"""Execute packaged SQL and independently reconcile pandas metrics."""

import math
from importlib.resources import files
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from quantiva.analytics import pandas_groups, pandas_kpis
from quantiva.database import database_engine

MONEY_ATOL = 0.000001  # £0.000001: numerical summation error, below source price precision.


def query_names() -> list[str]:
    """List packaged, reproducible analytical queries."""
    return sorted(
        path.name.removesuffix(".sql")
        for path in files("quantiva").joinpath("sql").iterdir()
        if path.name.endswith(".sql")
    )


def run_query(path: Path, name: str) -> pd.DataFrame:
    """Execute a named read-only SQL query; names are restricted to packaged files."""
    if name not in query_names():
        raise ValueError(f"Unknown query {name!r}. Available: {query_names()}")
    sql = files("quantiva").joinpath("sql", f"{name}.sql").read_text(encoding="utf-8")
    engine = database_engine(path)
    try:
        with engine.connect() as connection:
            return pd.read_sql_query(text(sql), connection)
    finally:
        engine.dispose()


def reconcile(ledger: pd.DataFrame, path: Path, *, fail_on_difference: bool = True) -> pd.DataFrame:
    """Compare actual SQL and pandas results at scalar and every grouped key.

    Counts compare exactly; money uses absolute tolerance only. Missing/extra group
    keys always fail even if the group's revenue is zero. Null ratios match nulls.
    """
    rows = []

    def add(metric, sql_value, pandas_value, *, count=False, missing=False):
        sql_null = sql_value is None or pd.isna(sql_value)
        pd_null = pandas_value is None or pd.isna(pandas_value)
        if sql_null or pd_null:
            difference, relative = None, None
            passed = sql_null and pd_null and not missing
        else:
            sql_value, pandas_value = float(sql_value), float(pandas_value)
            difference = abs(sql_value - pandas_value)
            relative = difference / abs(pandas_value) if pandas_value else None
            passed = (
                difference == 0
                if count
                else math.isclose(sql_value, pandas_value, rel_tol=0, abs_tol=MONEY_ATOL)
            ) and not missing
        rows.append(
            {
                "metric": metric,
                "sql_result": sql_value,
                "pandas_result": pandas_value,
                "absolute_difference": difference,
                "relative_difference": relative,
                "passed": bool(passed),
            }
        )

    sql_kpis = run_query(path, "kpis").iloc[0].to_dict()
    pd_kpis = pandas_kpis(ledger)
    for metric, value in sql_kpis.items():
        add(
            metric,
            value,
            pd_kpis[metric],
            count=metric in {"completed_orders", "units_sold", "identifiable_customers"},
        )
    repeat = run_query(path, "repeat_customers").iloc[0]
    for metric in ["repeat_customers", "repeat_purchase_rate"]:
        add(metric, repeat[metric], pd_kpis[metric], count=metric == "repeat_customers")
    for name, pandas_table in pandas_groups(ledger).items():
        sql_table = run_query(path, name)
        key = {
            "monthly_revenue": "month",
            "country_revenue": "country",
            "top_products": "stock_code",
        }[name]

        def key_value(value):
            return (0, "") if pd.isna(value) else (1, str(value))

        sql_map = {key_value(r[key]): r["revenue_gbp"] for r in sql_table.to_dict("records")}
        pd_map = {key_value(r[key]): r["revenue_gbp"] for r in pandas_table.to_dict("records")}
        for group in sorted(set(sql_map) | set(pd_map)):
            add(
                f"{name}:{'<missing>' if group[0] == 0 else group[1]}",
                sql_map.get(group),
                pd_map.get(group),
                missing=group not in sql_map or group not in pd_map,
            )
    result = pd.DataFrame(rows)
    if fail_on_difference and not result["passed"].all():
        failures = result.loc[~result["passed"]].to_string(index=False)
        raise ValueError(f"SQL/pandas reconciliation failed:\n{failures}")
    return result
