"""Auditable cleaning that separates sales from cancellations and adjustments."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from quantiva.config import COLUMNS

POLICY_VERSION = "1.0.0"


@dataclass
class CleaningResult:
    """Partition of raw records plus an explicit cleaning summary."""

    ledger: pd.DataFrame
    exclusions: pd.DataFrame
    report: dict


def clean_transactions(raw: pd.DataFrame) -> CleaningResult:
    """Keep valid adjustments, quarantine invalid rows, and audit exact duplicates.

    Completed sales are noncancelled, positive-quantity, positive-price lines.
    This is an analytical eligibility rule, not proof of payment or delivery.
    Every original row occurs once in either the ledger or exclusions.
    """
    missing = set(COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Required columns missing: {sorted(missing)}")
    frame = raw[COLUMNS].copy().reset_index(drop=True)
    frame.insert(0, "source_row", np.arange(2, len(frame) + 2))
    duplicate = frame.duplicated(subset=COLUMNS, keep="first")
    duplicates = frame.loc[duplicate].copy()
    duplicates["exclusion_reason"] = "exact_duplicate"
    duplicates["exclusion_reason"] = duplicates["exclusion_reason"].astype("string")
    frame = frame.loc[~duplicate].copy()
    for column in ["InvoiceNo", "StockCode", "Description", "Country"]:
        frame[column] = frame[column].astype("string").str.strip().replace("", pd.NA)
    quantity = pd.to_numeric(frame["Quantity"], errors="coerce")
    price = pd.to_numeric(frame["UnitPrice"], errors="coerce")
    dates = pd.to_datetime(frame["InvoiceDate"], errors="coerce", format="mixed")
    cancelled = frame["InvoiceNo"].str.upper().str.startswith("C", na=False)
    reasons = pd.Series("", index=frame.index, dtype="string")
    checks = {
        "missing_invoice": frame["InvoiceNo"].isna(),
        "missing_stock_code": frame["StockCode"].isna(),
        "invalid_timestamp": dates.isna(),
        "invalid_quantity": ~np.isfinite(quantity) | quantity.mod(1).ne(0),
        "zero_quantity": quantity.eq(0),
        "invalid_price": ~np.isfinite(price) | price.lt(0),
        "inconsistent_cancellation": cancelled & quantity.ge(0),
    }
    for reason, mask in checks.items():
        reasons.loc[mask] = reasons.loc[mask] + reason + ";"
    rejected = frame.loc[reasons.ne("")].copy()
    rejected["exclusion_reason"] = reasons.loc[reasons.ne("")].str.rstrip(";")
    frame = frame.loc[reasons.eq("")].copy()
    frame["Quantity"] = quantity.loc[frame.index].astype("int64")
    frame["UnitPrice"] = price.loc[frame.index].astype("float64")
    frame["InvoiceDate"] = dates.loc[frame.index]
    customer = pd.to_numeric(frame["CustomerID"], errors="coerce")
    valid_customer = np.isfinite(customer) & customer.gt(0) & customer.mod(1).eq(0)
    frame["has_valid_customer"] = valid_customer
    frame["CustomerID"] = customer.where(valid_customer).astype("Int64").astype("string")
    frame["description_missing"] = frame["Description"].isna()
    frame["country_missing"] = frame["Country"].isna()
    frame["is_cancelled"] = cancelled.loc[frame.index]
    frame["transaction_type"] = "completed_sale"
    frame.loc[frame["UnitPrice"].eq(0), "transaction_type"] = "zero_value"
    frame.loc[frame["Quantity"].lt(0), "transaction_type"] = "unlinked_negative"
    frame.loc[frame["Quantity"].lt(0) & frame["UnitPrice"].eq(0), "transaction_type"] = (
        "stock_adjustment_candidate"
    )
    frame.loc[frame["is_cancelled"], "transaction_type"] = "cancellation"
    frame["is_completed_sale"] = frame["transaction_type"].eq("completed_sale")
    frame["line_revenue_gbp"] = (frame["Quantity"] * frame["UnitPrice"]).round(4)
    ledger = frame.sort_values("source_row").reset_index(drop=True)
    exclusions = pd.concat(
        [
            duplicates[["source_row", "exclusion_reason"]],
            rejected[["source_row", "exclusion_reason"]],
        ],
        ignore_index=True,
    ).sort_values("source_row")
    # Audit records retain original source values rather than lossy inferred types.
    audit = raw[COLUMNS].copy().reset_index(drop=True)
    audit.insert(0, "source_row", np.arange(2, len(audit) + 2))
    exclusions = audit.merge(
        exclusions[["source_row", "exclusion_reason"]], on="source_row", validate="one_to_one"
    )
    # String conversion stabilizes Parquet schemas even with malformed mixed-type input.
    for column in COLUMNS:
        exclusions[column] = exclusions[column].astype("string")
    report = {
        "policy_version": POLICY_VERSION,
        "original_records": len(raw),
        "cleaned_records": len(ledger),
        "duplicate_records_removed": len(duplicates),
        "quarantined_records": len(rejected),
        "excluded_records": len(exclusions),
        "transaction_types": {
            str(key): int(value) for key, value in ledger["transaction_type"].value_counts().items()
        },
        "missing_or_invalid_customer_records": int((~ledger["has_valid_customer"]).sum()),
        "completed_sales_without_customer": int(
            (ledger["is_completed_sale"] & ~ledger["has_valid_customer"]).sum()
        ),
        "missing_description_records": int(ledger["description_missing"].sum()),
        "exclusion_reasons": {
            str(key): int(value)
            for key, value in exclusions["exclusion_reason"].value_counts().items()
        },
    }
    if len(ledger) + len(exclusions) != len(raw):
        raise RuntimeError("Cleaning row accounting failed")
    return CleaningResult(ledger, exclusions, report)
