"""Parameterized SQLite aggregates and signature-aware read-only caching."""

import json
from dataclasses import dataclass
from datetime import date, timedelta
from importlib.resources import files
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import text

from quantiva.database import database_engine


@dataclass(frozen=True)
class Filters:
    """Inclusive calendar dates; empty country/product tuples mean all values."""

    start: date
    end: date
    countries: tuple[str, ...] = ()
    products: tuple[str, ...] = ()

    def validate(self) -> None:
        if not isinstance(self.start, date) or not isinstance(self.end, date):
            raise ValueError("Choose valid calendar dates")
        if self.start > self.end:
            raise ValueError("Start date must precede or equal end date")
        if any(not isinstance(v, str) or not v for v in (*self.countries, *self.products)):
            raise ValueError("Country/product filters must be nonempty strings")


def signature(path: Path) -> tuple:
    "Include SQLite WAL changes and nanosecond stat data; no object is shared mutable."
    paths = [path, Path(str(path) + "-wal")]
    return tuple(
        (str(p.resolve()), p.stat().st_mtime_ns, p.stat().st_size)
        if p.is_file()
        else (str(p.resolve()), None, None)
        for p in paths
    )


def scope(filters: Filters) -> tuple[str, dict]:
    "Build allowlisted predicates, binding all values rather than interpolating them."
    filters.validate()
    predicates = ["invoice_date >= :start", "invoice_date < :stop"]
    params = {
        "start": filters.start.isoformat(),
        "stop": (filters.end + timedelta(days=1)).isoformat(),
    }
    for column, values in [("country", filters.countries), ("stock_code", filters.products)]:
        if values:
            names = []
            for n, value in enumerate(values):
                key = f"{column}_{n}"
                names.append(f":{key}")
                params[key] = value
            column_sql = "COALESCE(country,'(Unknown)')" if column == "country" else column
            predicates.append(f"{column_sql} IN ({','.join(names)})")
    return " AND ".join(predicates), params


def query(path: Path, sql: str, params: dict | None = None) -> pd.DataFrame:
    """Execute aggregate SELECTs with the project's existing SQLAlchemy connection."""
    engine = database_engine(path)
    try:
        with engine.connect() as connection:
            return pd.read_sql_query(text(sql), connection, params=params or {})
    finally:
        engine.dispose()


@st.cache_data(show_spinner=False, max_entries=8)
def _catalog(path: str, version: tuple) -> dict:
    database = Path(path)
    bounds = query(
        database, "SELECT MIN(invoice_date) AS first, MAX(invoice_date) AS last FROM transactions"
    ).iloc[0]
    if pd.isna(bounds["first"]):
        raise ValueError("Database has no observations. Run quantiva database.")
    return {
        "start": pd.Timestamp(bounds["first"]).date(),
        "end": pd.Timestamp(bounds["last"]).date(),
        "countries": query(
            database,
            (
                "SELECT DISTINCT COALESCE(country,'(Unknown)') AS country FROM "
                "completed_sales ORDER BY country"
            ),
        )["country"].tolist(),
        "products": query(
            database,
            (
                "SELECT DISTINCT p.stock_code, p.display_description FROM products"
                " p JOIN completed_sales s ON s.stock_code=p.stock_code ORDER BY "
                "p.stock_code"
            ),
        ),
    }


def catalog(path: Path) -> dict:
    """Read coverage and identifier options; invalidate after database replacement."""
    if not path.is_file():
        raise FileNotFoundError(
            "SQLite database is missing. Run quantiva prepare, then quantiva database."
        )
    return _catalog(str(path.resolve()), signature(path))


@st.cache_data(show_spinner=False, max_entries=16)
def _bundle(path: str, version: tuple, filters: Filters) -> dict:
    database = Path(path)
    where, params = scope(filters)
    prefix = f"WITH filtered AS (SELECT * FROM completed_sales WHERE {where}) "

    def read(sql):
        return query(database, prefix + sql, params)

    # Reuse the authoritative packaged KPI query rather than reproducing its definitions.
    kpi_sql = files("quantiva").joinpath("sql/kpis.sql").read_text(encoding="utf-8")
    kpis = read(kpi_sql.replace("FROM completed_sales", "FROM filtered")).iloc[0].to_dict()
    for name in ["completed_orders", "units_sold", "identifiable_customers"]:
        kpis[name] = int(kpis[name])
    customers = read(
        "SELECT customer_id, MAX(invoice_date) AS last_purchase,\n        "
        "COUNT(DISTINCT invoice_no) AS frequency, "
        "SUM(revenue_units)/10000.0 AS monetary_gbp\n        FROM filtered "
        "WHERE customer_id IS NOT NULL GROUP BY customer_id"
    )
    count = len(customers)
    kpis["repeat_customers"] = int(customers["frequency"].ge(2).sum())
    kpis["repeat_purchase_rate"] = float(customers["frequency"].ge(2).mean()) if count else None
    aggregates = {}
    for period, expr in [
        ("daily", "date(invoice_date)"),
        ("weekly", "date(invoice_date,'-6 days','weekday 1')"),
        ("monthly", "strftime('%Y-%m',invoice_date)"),
    ]:
        aggregates[period] = read(f"""SELECT {expr} AS period,
            SUM(revenue_units)/10000.0 AS revenue_gbp, COUNT(DISTINCT invoice_no) AS orders,
            SUM(quantity) AS units, SUM(revenue_units)/10000.0/COUNT(DISTINCT invoice_no) AS aov_gbp
            FROM filtered GROUP BY {expr} ORDER BY period""")
    days = pd.date_range(filters.start, filters.end)
    daily = aggregates["daily"].set_index("period")
    daily.index = pd.to_datetime(daily.index)
    daily = daily.reindex(days)
    for column in ["revenue_gbp", "orders", "units"]:
        daily[column] = pd.to_numeric(daily[column]).astype(float).fillna(0)
    aggregates["daily"] = daily.rename_axis("period").reset_index()
    week_start = pd.Timestamp(filters.start) - pd.Timedelta(days=filters.start.weekday())
    weeks = pd.date_range(week_start, filters.end, freq="W-MON")
    weekly = aggregates["weekly"].set_index("period")
    weekly.index = pd.to_datetime(weekly.index)
    weekly = weekly.reindex(weeks)
    for column in ["revenue_gbp", "orders", "units"]:
        weekly[column] = pd.to_numeric(weekly[column]).astype(float).fillna(0)
    aggregates["weekly"] = weekly.rename_axis("period").reset_index()
    bounds = catalog(database)
    monthly = aggregates["monthly"]
    periods = pd.period_range(filters.start, filters.end, freq="M")
    monthly = (
        monthly.set_index("period").reindex(periods.astype(str)).rename_axis("period").reset_index()
    )
    for column in ["revenue_gbp", "orders", "units"]:
        monthly[column] = pd.to_numeric(monthly[column]).astype(float).fillna(0)
    monthly["complete_month"] = [
        max(bounds["start"], filters.start) <= p.start_time.date()
        and min(bounds["end"], filters.end) >= p.end_time.date()
        for p in periods
    ]
    previous = monthly["revenue_gbp"].shift()
    valid = (
        monthly["complete_month"]
        & monthly["complete_month"].shift(fill_value=False)
        & previous.gt(0)
    )
    monthly["growth_pct"] = (100 * (monthly["revenue_gbp"] / previous - 1)).where(valid)
    aggregates["monthly"] = monthly
    result = {
        "kpis": kpis,
        "customers": customers,
        **aggregates,
        "products": read(
            "SELECT f.stock_code, MAX(p.display_description) AS description,"
            "\n            SUM(f.revenue_units)/10000.0 AS revenue_gbp, "
            "SUM(f.quantity) AS units,\n            COUNT(DISTINCT "
            "f.invoice_no) AS orders FROM filtered f\n            JOIN products"
            " p ON p.stock_code=f.stock_code GROUP BY f.stock_code ORDER BY "
            "revenue_gbp DESC"
        ),
        "countries": read(
            "SELECT COALESCE(country,'(Unknown)') AS country,\n            "
            "SUM(revenue_units)/10000.0 AS revenue_gbp, COUNT(DISTINCT "
            "invoice_no) AS orders\n            FROM filtered GROUP BY country "
            "ORDER BY revenue_gbp DESC"
        ),
        "orders": read(
            "SELECT invoice_no, SUM(revenue_units)/10000.0 AS order_value_gbp "
            "FROM filtered GROUP BY invoice_no"
        ),
    }
    if signature(database) != version:
        raise ValueError("Database changed while reading. Wait for rebuild to finish and refresh.")
    return result


def bundle(path: Path, filters: Filters) -> dict:
    """Return filtered SQL aggregates with safe caching and no raw workbook reads."""
    filters.validate()
    bounds = catalog(path)
    if filters.start < bounds["start"] or filters.end > bounds["end"]:
        raise ValueError("Date filters must be inside the recorded dataset coverage")
    return _bundle(str(path.resolve()), signature(path), filters)


def read_json(path: Path) -> dict:
    """Read metadata without masking corrupted or missing prerequisites."""
    if not path.is_file():
        raise FileNotFoundError(f"{path.name} is missing. See README setup commands.")
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise ValueError(f"Invalid metadata object: {path.name}")
    return result
