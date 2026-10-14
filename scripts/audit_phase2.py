"""Independent raw-workbook KPI/statistical audit; no cleaning or analytics helpers."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from quantiva.config import Settings
from quantiva.database import database_content_digest
from quantiva.ingestion import load_raw, sha256
from quantiva.reconciliation import run_query


def independent_statistics(values: np.ndarray) -> dict:
    """NumPy summaries and bias-corrected Fisher sample skewness."""
    values = np.asarray(values, dtype=float)
    n = len(values)
    mean = values.mean()
    std = values.std(ddof=1)
    quantiles = np.quantile(values, [0.01, 0.25, 0.5, 0.75, 0.95, 0.99], method="linear")
    skew = n * np.sum((values - mean) ** 3) / ((n - 1) * (n - 2) * std**3)
    return {
        "count": n,
        "mean": mean,
        "median": np.median(values),
        "std": std,
        "variance": values.var(ddof=1),
        "p01": quantiles[0],
        "q1": quantiles[1],
        "q3": quantiles[3],
        "p95": quantiles[4],
        "p99": quantiles[5],
        "iqr": quantiles[3] - quantiles[1],
        "skewness": skew,
        "min": values.min(),
        "max": values.max(),
    }


def average_ranks(values: np.ndarray) -> np.ndarray:
    """Average ranks computed from sorted unique values and tie counts."""
    _, inverse, counts = np.unique(values, return_inverse=True, return_counts=True)
    return (np.cumsum(counts) - (counts - 1) / 2)[inverse]


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    """Normalized dot product of centered observations."""
    x = np.asarray(x, dtype=float) - np.mean(x)
    y = np.asarray(y, dtype=float) - np.mean(y)
    return float(np.dot(x, y) / np.sqrt(np.dot(x, x) * np.dot(y, y)))


def audit_raw_workbook() -> dict:
    """Independently validate published findings against raw eligible observations."""
    settings = Settings.from_environment()
    root = Path(__file__).resolve().parents[1]
    raw = load_raw(settings.raw_file)
    frame = raw.drop_duplicates().copy()
    q = pd.to_numeric(frame["Quantity"], errors="coerce")
    p = pd.to_numeric(frame["UnitPrice"], errors="coerce")
    dates = pd.to_datetime(frame["InvoiceDate"], errors="coerce")
    invoice = frame["InvoiceNo"].str.strip()
    eligible = (
        invoice.notna()
        & invoice.ne("")
        & ~invoice.str.upper().str.startswith("C", na=False)
        & frame["StockCode"].notna()
        & frame["StockCode"].str.strip().ne("")
        & q.gt(0)
        & q.mod(1).eq(0)
        & p.gt(0)
        & np.isfinite(q)
        & np.isfinite(p)
        & dates.notna()
    )
    sales = frame.loc[eligible].copy()
    sales["InvoiceNo"] = invoice[eligible]
    sales["amount_units"] = q[eligible].astype("int64") * np.rint(p[eligible] * 10000).astype(
        "int64"
    )
    sales["month"] = dates[eligible].dt.strftime("%Y-%m")
    known = sales.loc[sales["CustomerID"].notna()]
    known_ids = pd.to_numeric(known["CustomerID"], errors="coerce")
    if not (np.isfinite(known_ids) & known_ids.gt(0) & known_ids.mod(1).eq(0)).all():
        raise ValueError("Raw customer IDs require further validity treatment before this audit")
    orders = sales.groupby("InvoiceNo").agg(
        amount_units=("amount_units", "sum"), units=("Quantity", "sum")
    )
    customers = known.groupby("CustomerID").agg(
        amount_units=("amount_units", "sum"), frequency=("InvoiceNo", "nunique")
    )
    gross = int(sales["amount_units"].sum()) / 10000
    metrics = {
        "gross_revenue_gbp": gross,
        "completed_orders": len(orders),
        "aov_gbp": gross / len(orders),
        "units_sold": int(sales["Quantity"].sum()),
        "identifiable_customers": len(customers),
        "identifiable_revenue_gbp": int(known["amount_units"].sum()) / 10000,
        "repeat_customers": int((customers["frequency"] >= 2).sum()),
        "repeat_purchase_rate": float((customers["frequency"] >= 2).sum() / len(customers)),
    }
    metrics["revenue_per_identifiable_customer_gbp"] = metrics["identifiable_revenue_gbp"] / len(
        customers
    )
    published = json.loads((root / "reports" / "phase_2_metrics.json").read_text())
    checks = {
        f"raw_{key}": bool(np.isclose(value, published["kpis"][key], rtol=0, atol=1e-6))
        for key, value in metrics.items()
    }
    for query, column, sql_key in [
        ("monthly_revenue", "month", "month"),
        ("country_revenue", "Country", "country"),
        ("top_products", "StockCode", "stock_code"),
    ]:
        raw_groups = sales.groupby(column, dropna=False)["amount_units"].sum() / 10000
        sql = run_query(settings.database_file, query).set_index(sql_key)["revenue_gbp"]
        checks[f"raw_{query}"] = set(raw_groups.index) == set(sql.index) and bool(
            np.allclose(raw_groups.sort_index(), sql.sort_index(), rtol=0, atol=1e-6)
        )
    calendar = pd.date_range(dates.min().normalize(), dates.max().normalize())
    day_revenue = sales.groupby(sales["InvoiceDate"].dt.normalize())["amount_units"].sum() / 10000
    all_days = day_revenue.reindex(calendar, fill_value=0)
    observed = frame["InvoiceDate"].dt.normalize().unique()
    interior_observed = all_days.loc[
        all_days.index.isin(observed) & ~all_days.index.isin([calendar[0], calendar[-1]])
    ]
    statistical_arrays = {
        "order_value_gbp": orders["amount_units"].to_numpy() / 10000,
        "customer_spending_gbp": customers["amount_units"].to_numpy() / 10000,
        "line_amount_gbp": sales["amount_units"].to_numpy() / 10000,
        "daily_revenue_calendar_gbp": all_days.to_numpy(),
        "daily_revenue_observed_interior_gbp": interior_observed.to_numpy(),
    }
    differences = []
    for grain, values in statistical_arrays.items():
        statistics = independent_statistics(values)
        for measure, value in statistics.items():
            reported = published["statistics"][grain][measure]
            differences.append(abs(float(value) - reported))
            checks[f"stat_{grain}_{measure}"] = bool(
                np.isclose(value, reported, rtol=1e-10, atol=1e-8)
            )
    correlations = {
        "invoice_units_value_pearson": pearson(
            orders["units"].to_numpy(), statistical_arrays["order_value_gbp"]
        ),
        "invoice_units_value_rank": pearson(
            average_ranks(orders["units"].to_numpy()),
            average_ranks(statistical_arrays["order_value_gbp"]),
        ),
        "customer_frequency_spending_pearson": pearson(
            customers["frequency"].to_numpy(), statistical_arrays["customer_spending_gbp"]
        ),
        "customer_frequency_spending_rank": pearson(
            average_ranks(customers["frequency"].to_numpy()),
            average_ranks(statistical_arrays["customer_spending_gbp"]),
        ),
    }
    for name, value in correlations.items():
        checks[name] = bool(np.isclose(value, published["correlations"][name], rtol=0, atol=1e-12))
    # Duplicate sensitivity: independently retain all raw eligible lines.
    duplicate = raw.duplicated()
    extra = raw.loc[duplicate].copy()
    extra_sale = (
        ~extra["InvoiceNo"].str.upper().str.startswith("C", na=False)
        & extra["Quantity"].gt(0)
        & extra["UnitPrice"].gt(0)
    )
    extra = extra.loc[extra_sale]
    extra_amount = int((extra["Quantity"] * np.rint(extra["UnitPrice"] * 10000)).sum()) / 10000
    retained_revenue = gross + extra_amount
    retained_orders = pd.concat([sales["InvoiceNo"], extra["InvoiceNo"]]).nunique()
    sensitivity = pd.read_csv(root / "reports" / "duplicate_sensitivity.csv").set_index("metric")
    independently_retained = {
        "gross_revenue_gbp": retained_revenue,
        "completed_orders": retained_orders,
        "aov_gbp": retained_revenue / retained_orders,
        "units_sold": metrics["units_sold"] + int(extra["Quantity"].sum()),
    }
    for key, value in independently_retained.items():
        checks[f"duplicate_{key}"] = bool(
            np.isclose(value, sensitivity.loc[key, "duplicates_retained"], rtol=0, atol=1e-6)
        )
    original = Settings(root / "data")
    checks["raw_matches_original"] = sha256(settings.raw_file) == sha256(original.raw_file)
    original_manifest = json.loads((original.processed_dir / "manifest.json").read_text())
    checks["processed_artifacts_match_original"] = all(
        sha256(settings.processed_dir / name) == digest
        for name, digest in original_manifest["outputs"].items()
    )
    original_digest = database_content_digest(original.database_file)
    checks["database_matches_original"] = (
        database_content_digest(settings.database_file) == original_digest
    )
    if not all(checks.values()):
        raise ValueError(
            f"Independent audit failed: {[key for key, value in checks.items() if not value]}"
        )
    result = {
        "checks": checks,
        "passed": sum(checks.values()),
        "failed": 0,
        "raw_workbook_kpis": metrics,
        "correlations": correlations,
        "max_statistic_absolute_difference": max(differences),
        "statistic_tolerance": {"atol": 1e-8, "rtol": 1e-10},
        "database_content_digest": original_digest,
    }
    (root / "reports" / "phase_2_audit_results.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: value for key, value in result.items() if key != "checks"}, indent=2))
    return result


if __name__ == "__main__":
    audit_raw_workbook()
