"""Independent pandas metrics, descriptive summaries, and coverage-aware aggregates."""

import pandas as pd

from quantiva.cleaning import clean_transactions
from quantiva.config import COLUMNS


def eligible_sales(ledger: pd.DataFrame) -> pd.DataFrame:
    """Select the authoritative Phase 1 sales eligibility flag."""
    return ledger.loc[ledger["is_completed_sale"]].copy()


def pandas_kpis(ledger: pd.DataFrame) -> dict:
    """Calculate KPIs at line, invoice, and identifiable-customer grain."""
    sales = eligible_sales(ledger)
    known = sales.loc[sales["CustomerID"].notna()]
    revenue = float(sales["line_revenue_gbp"].sum())
    orders = int(sales["InvoiceNo"].nunique())
    customers = int(known["CustomerID"].nunique())
    known_revenue = float(known["line_revenue_gbp"].sum())
    frequency = known.groupby("CustomerID")["InvoiceNo"].nunique()
    return {
        "gross_revenue_gbp": revenue,
        "completed_orders": orders,
        "aov_gbp": revenue / orders if orders else None,
        "units_sold": int(sales["Quantity"].sum()),
        "identifiable_customers": customers,
        "identifiable_revenue_gbp": known_revenue,
        "revenue_per_identifiable_customer_gbp": known_revenue / customers if customers else None,
        "repeat_customers": int(frequency.ge(2).sum()),
        "repeat_purchase_rate": float(frequency.ge(2).mean()) if customers else None,
    }


def pandas_groups(ledger: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Independently group the Parquet ledger without reading database results."""
    sales = eligible_sales(ledger)
    sales["month"] = sales["InvoiceDate"].dt.strftime("%Y-%m")
    result = {}
    for name, column, key in [
        ("monthly_revenue", "month", "month"),
        ("country_revenue", "Country", "country"),
        ("top_products", "StockCode", "stock_code"),
    ]:
        table = sales.groupby(column, dropna=False)["line_revenue_gbp"].sum().reset_index()
        result[name] = table.rename(columns={column: key, "line_revenue_gbp": "revenue_gbp"})
    return result


def daily_calendar(ledger: pd.DataFrame) -> pd.DataFrame:
    """Fill observed-span dates, flag no-record dates and observation boundaries.

    Zero observed revenue on a missing date does not prove zero business demand.
    """
    columns = ["date", "revenue_gbp", "orders", "has_transactions", "boundary_day", "weekday"]
    if ledger.empty:
        return pd.DataFrame(columns=columns)
    dates = pd.date_range(
        ledger["InvoiceDate"].min().normalize(), ledger["InvoiceDate"].max().normalize(), freq="D"
    )
    sales = eligible_sales(ledger)
    sales["date"] = sales["InvoiceDate"].dt.normalize()
    grouped = sales.groupby("date").agg(
        revenue_gbp=("line_revenue_gbp", "sum"), orders=("InvoiceNo", "nunique")
    )
    table = grouped.reindex(dates, fill_value=0).rename_axis("date").reset_index()
    observed = ledger["InvoiceDate"].dt.normalize().unique()
    table["has_transactions"] = table["date"].isin(observed)
    table["boundary_day"] = table["date"].isin([dates[0], dates[-1]])
    table["weekday"] = table["date"].dt.day_name()
    return table[columns]


def monthly_calendar(ledger: pd.DataFrame) -> pd.DataFrame:
    """Revenue growth only between adjacent complete calendar months."""
    if ledger.empty:
        return pd.DataFrame(columns=["month", "revenue_gbp", "complete_month", "growth_pct"])
    start = ledger["InvoiceDate"].min().normalize()
    end = ledger["InvoiceDate"].max().normalize()
    periods = pd.period_range(start, end, freq="M")
    sales = eligible_sales(ledger)
    totals = sales.groupby(sales["InvoiceDate"].dt.to_period("M"))["line_revenue_gbp"].sum()
    table = totals.reindex(periods, fill_value=0).rename("revenue_gbp").reset_index()
    table = table.rename(columns={"index": "period"})
    table["complete_month"] = [
        start <= p.start_time and end >= p.end_time.normalize() for p in periods
    ]
    previous = table["revenue_gbp"].shift()
    comparable = table["complete_month"] & table["complete_month"].shift(fill_value=False)
    table["growth_pct"] = ((table["revenue_gbp"] / previous - 1) * 100).where(
        comparable & previous.gt(0)
    )
    table["month"] = [str(p) for p in periods]
    return table[["month", "revenue_gbp", "complete_month", "growth_pct"]]


def describe_values(values: pd.Series) -> dict:
    """Sample variance/std (ddof=1), distribution shape, and robust spread."""
    values = values.dropna().astype(float)
    if values.empty:
        return {"count": 0}
    q = values.quantile([0.01, 0.25, 0.5, 0.75, 0.95, 0.99])

    def finite_or_none(value):
        return None if pd.isna(value) else float(value)

    return {
        "count": len(values),
        "mean": float(values.mean()),
        "median": float(values.median()),
        "std": finite_or_none(values.std(ddof=1)),
        "variance": finite_or_none(values.var(ddof=1)),
        "q1": float(q.loc[0.25]),
        "q3": float(q.loc[0.75]),
        "p01": float(q.loc[0.01]),
        "p95": float(q.loc[0.95]),
        "p99": float(q.loc[0.99]),
        "iqr": float(q.loc[0.75] - q.loc[0.25]),
        "skewness": finite_or_none(values.skew()),
        "min": float(values.min()),
        "max": float(values.max()),
    }


def duplicate_sensitivity(ledger: pd.DataFrame, exclusions: pd.DataFrame) -> pd.DataFrame:
    """Restore eligible duplicate lines without changing the Phase 1 cleaning policy."""
    duplicates = exclusions.loc[exclusions["exclusion_reason"].eq("exact_duplicate")].copy()
    # Reuse all Phase 1 validity rules. Restoring repeats must not reinstate invalid
    # positive lines (e.g. absent invoice/product or fractional quantity).
    classified = clean_transactions(duplicates[COLUMNS])
    positions = (
        classified.ledger.loc[classified.ledger["is_completed_sale"], "source_row"].to_numpy() - 2
    )
    eligible_keys = duplicates.iloc[positions][COLUMNS].drop_duplicates()
    # Preserve the multiplicity of each eligible original row, including third+ copies.
    duplicates = duplicates.merge(eligible_keys, on=COLUMNS, how="inner", validate="many_to_one")
    quantity = pd.to_numeric(duplicates["Quantity"], errors="raise")
    price = pd.to_numeric(duplicates["UnitPrice"], errors="raise")
    baseline = pandas_kpis(ledger)
    sales = eligible_sales(ledger)
    revenue = baseline["gross_revenue_gbp"] + float((quantity * price).round(4).sum())
    orders = pd.concat([sales["InvoiceNo"], duplicates["InvoiceNo"].str.strip()]).nunique()
    retained = {
        "gross_revenue_gbp": revenue,
        "completed_orders": int(orders),
        "aov_gbp": revenue / orders if orders else None,
        "units_sold": baseline["units_sold"] + int(quantity.sum()),
    }
    rows = []
    for key, value in retained.items():
        base = baseline[key]
        delta = None if value is None else value - base
        rows.append(
            {
                "metric": key,
                "deduplicated": base,
                "duplicates_retained": value,
                "difference": delta,
                "change_pct": 100 * delta / base if base else None,
            }
        )
    return pd.DataFrame(rows)
