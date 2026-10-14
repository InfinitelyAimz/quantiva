"""Validate full-data artifacts without publishing invented business metrics."""

import json

import numpy as np
import pandas as pd

from quantiva.config import Settings
from quantiva.ingestion import sha256


def verify() -> dict:
    """Check report reconciliation, row coverage, eligibility, and file hashes."""
    settings = Settings.from_environment()
    folder = settings.processed_dir
    report = json.loads((folder / "cleaning_report.json").read_text(encoding="utf-8"))
    inspection = json.loads((folder / "initial_inspection.json").read_text(encoding="utf-8"))
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    ledger = pd.read_parquet(folder / "transactions.parquet")
    audit = pd.read_parquet(folder / "exclusions.parquet")
    source_hash = sha256(settings.raw_file)
    checks = {
        "source_hash_matches": source_hash
        == report["source_sha256"]
        == inspection["source_sha256"]
        == manifest["source_sha256"],
        "output_hashes_match": all(
            sha256(folder / name) == digest for name, digest in manifest["outputs"].items()
        ),
        "row_counts_reconcile": len(ledger) == report["cleaned_records"]
        and len(audit) == report["excluded_records"]
        and len(ledger) + len(audit)
        == report["original_records"]
        == inspection["original_records"],
        "source_rows_partition_raw": np.array_equal(
            np.sort(pd.concat([ledger["source_row"], audit["source_row"]]).to_numpy()),
            np.arange(2, report["original_records"] + 2),
        ),
        "completed_sales_rule_matches": np.array_equal(
            ledger["is_completed_sale"].to_numpy(),
            (
                ~ledger["is_cancelled"] & ledger["Quantity"].gt(0) & ledger["UnitPrice"].gt(0)
            ).to_numpy(),
        ),
        "signed_line_revenue_matches": np.allclose(
            ledger["line_revenue_gbp"],
            (ledger["Quantity"] * ledger["UnitPrice"]).round(4),
            rtol=0,
            atol=1e-8,
        ),
        "category_counts_reconcile": sum(report["transaction_types"].values()) == len(ledger),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Data verification failed: {checks}")
    print(json.dumps(checks, indent=2))
    return checks


if __name__ == "__main__":
    verify()
