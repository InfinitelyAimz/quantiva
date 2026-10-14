"""Verify full-data database integrity and independent SQL/pandas calculations."""

import json

import numpy as np
import pandas as pd
from sqlalchemy import text

from quantiva.analytics import monthly_calendar
from quantiva.config import Settings
from quantiva.database import database_engine, load_verified_ledger
from quantiva.ingestion import sha256
from quantiva.reconciliation import query_names, reconcile, run_query


def verify_analytics() -> dict:
    """Fail on relational, provenance, KPI, query, or calendar discrepancies."""
    settings = Settings.from_environment()
    ledger = load_verified_ledger(settings)
    engine = database_engine(settings.database_file)
    try:
        with engine.connect() as connection:
            expected_counts = {
                "transactions": len(ledger),
                "invoices": ledger["InvoiceNo"].nunique(),
                "products": ledger["StockCode"].nunique(),
                "customers": ledger["CustomerID"].nunique(),
                "countries": ledger["Country"].nunique(),
            }
            counts = {
                table: connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar_one()
                for table in expected_counts
            }
            provenance = json.loads(
                connection.execute(
                    text("SELECT value FROM dataset_metadata WHERE key='ledger_sha256'")
                ).scalar_one()
            )
            checks = {
                "database_counts_match": all(counts[t] == n for t, n in expected_counts.items()),
                "foreign_keys_pass": not connection.execute(
                    text("PRAGMA foreign_key_check")
                ).fetchall(),
                "sqlite_integrity_pass": connection.execute(
                    text("PRAGMA integrity_check")
                ).scalar_one()
                == "ok",
                "ledger_provenance_matches": provenance
                == sha256(settings.processed_dir / "transactions.parquet"),
            }
    finally:
        engine.dispose()
    reconciliation = reconcile(ledger, settings.database_file)
    queries = {name: run_query(settings.database_file, name) for name in query_names()}
    sql_monthly = queries["monthly_growth"]
    pandas_monthly = monthly_calendar(ledger)
    checks["monthly_coverage_matches"] = (
        sql_monthly["month"].tolist() == pandas_monthly["month"].tolist()
        and sql_monthly["complete_month"].astype(bool).tolist()
        == pandas_monthly["complete_month"].tolist()
        and np.allclose(
            pd.to_numeric(sql_monthly["growth_pct"]),
            pd.to_numeric(pandas_monthly["growth_pct"]),
            atol=1e-6,
            rtol=0,
            equal_nan=True,
        )
    )
    if not all(checks.values()):
        raise ValueError(f"Full-data analytics verification failed: {checks}")
    summary = {
        "checks": checks,
        "database_counts": counts,
        "queries_executed": len(queries),
        "reconciliation_rows": len(reconciliation),
        "all_reconciled": bool(reconciliation["passed"].all()),
        "max_absolute_difference": float(reconciliation["absolute_difference"].max()),
    }
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    verify_analytics()
