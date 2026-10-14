"""Verify actual UCI dashboard calculations against independent Parquet aggregates."""

import hashlib
import json
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from quantiva.analytics import eligible_sales, monthly_calendar, pandas_kpis
from quantiva.config import Settings
from quantiva.dashboard.data import Filters, _bundle, bundle, catalog
from quantiva.database import load_verified_ledger
from quantiva.segmentation import build_rfm

# SHA-256 of the accepted Phase 3 report after CRLF-to-LF normalization.
# Verified against the archived original; independent of rewritten Git commit IDs.
PHASE3_FORECAST_SHA256 = "ff74f39a953b4d40097d165047c391bf3bbd7075c1ba7f4efcde1116ddd25e2d"


def verify_dashboard() -> dict:
    """Reconcile full/filtered scopes and raw customer aggregates; report actual timings."""
    settings = Settings.from_environment()
    root = Path(__file__).resolve().parents[1]
    ledger = load_verified_ledger(settings)
    info = catalog(settings.database_file)
    full = Filters(info["start"], info["end"])
    scopes = {
        "full": full,
        "country": Filters(info["start"], info["end"], ("Germany",)),
        "date": Filters(date(2011, 6, 1), date(2011, 8, 31)),
        "product": Filters(info["start"], info["end"], (), ("DOT",)),
        "empty": Filters(date(2011, 1, 1), date(2011, 1, 1)),
    }
    _bundle.clear()
    start = time.perf_counter()
    data = bundle(settings.database_file, full)
    cold = time.perf_counter() - start
    start = time.perf_counter()
    bundle(settings.database_file, full)
    warm = time.perf_counter() - start
    checks = {}
    for name, selected in scopes.items():
        subset = ledger.loc[ledger["InvoiceDate"].dt.date.between(selected.start, selected.end)]
        if selected.countries:
            subset = subset.loc[subset["Country"].fillna("(Unknown)").isin(selected.countries)]
        if selected.products:
            subset = subset.loc[subset["StockCode"].isin(selected.products)]
        actual = bundle(settings.database_file, selected)
        expected = pandas_kpis(subset)
        for metric, value in expected.items():
            got = actual["kpis"][metric]
            checks[f"{name}_{metric}"] = bool(
                pd.isna(got) if value is None else np.isclose(got, value, atol=1e-6, rtol=0)
            )
        checks[f"{name}_product_revenue"] = bool(
            np.isclose(
                actual["products"]["revenue_gbp"].sum(),
                expected["gross_revenue_gbp"],
                atol=1e-6,
                rtol=0,
            )
        )
        checks[f"{name}_country_revenue"] = bool(
            np.isclose(
                actual["countries"]["revenue_gbp"].sum(),
                expected["gross_revenue_gbp"],
                atol=1e-6,
                rtol=0,
            )
        )
    monthly = monthly_calendar(ledger)
    checks["monthly_completeness_unchanged"] = (
        data["monthly"]["complete_month"].tolist() == monthly["complete_month"].tolist()
    )
    checks["monthly_growth_unchanged"] = bool(
        np.allclose(
            data["monthly"]["growth_pct"], monthly["growth_pct"], atol=1e-6, rtol=0, equal_nan=True
        )
    )
    reference = pd.Timestamp(info["end"]) + pd.Timedelta(days=1)
    rfm = build_rfm(data["customers"], reference).set_index("customer_id").sort_index()
    known = eligible_sales(ledger).dropna(subset=["CustomerID"])
    expected = (
        known.groupby("CustomerID")
        .agg(
            last=("InvoiceDate", "max"),
            frequency=("InvoiceNo", "nunique"),
            monetary=("line_revenue_gbp", "sum"),
        )
        .sort_index()
    )
    checks["rfm_customer_keys"] = rfm.index.tolist() == expected.index.tolist()
    checks["rfm_recency"] = (
        rfm["recency_days"].tolist()
        == (reference - expected["last"].dt.normalize()).dt.days.tolist()
    )
    checks["rfm_distinct_invoice_frequency"] = (
        rfm["frequency"].tolist() == expected["frequency"].tolist()
    )
    checks["rfm_monetary"] = bool(
        np.allclose(rfm["monetary_gbp"], expected["monetary"], atol=1e-6, rtol=0)
    )
    checks["rfm_exhaustive"] = (
        not rfm["segment"].isna().any() and len(rfm) == data["kpis"]["identifiable_customers"]
    )
    evidence = (root / "reports/forecast_results.json").read_bytes().replace(b"\r\n", b"\n")
    checks["phase3_evidence_unchanged"] = (
        hashlib.sha256(evidence).hexdigest() == PHASE3_FORECAST_SHA256
    )
    checks = {k: bool(v) for k, v in checks.items()}
    if not all(checks.values()):
        raise ValueError(
            f"Dashboard reconciliation failed: {[k for k, v in checks.items() if not v]}"
        )
    summary = {
        "checks": checks,
        "passed": sum(checks.values()),
        "failed": 0,
        "full_kpis": data["kpis"],
        "rfm_reference_date": str(reference.date()),
        "rfm_segment_counts": rfm.groupby("segment").size().to_dict(),
        "cold_bundle_seconds": cold,
        "cached_bundle_seconds": warm,
        "source": "Actual verified UCI ledger and SQLite; synthetic fixtures are tests only",
    }
    (root / "reports/phase_4_verification.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    verify_dashboard()
