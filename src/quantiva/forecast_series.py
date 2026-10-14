"""Traceable daily observed-sales target and explicit calendar boundaries."""

import json

import numpy as np
import pandas as pd

from quantiva.analytics import eligible_sales
from quantiva.config import Settings
from quantiva.database import SCALE, load_verified_ledger
from quantiva.ingestion import sha256
from quantiva.reconciliation import run_query

# M (Manual) remains: unlike these named charges, its meaning is ambiguous.
CHARGE_CODES = ("DOT", "POST", "AMAZONFEE", "BANK CHARGES")
TARGET_POLICY = "phase1_completed_sales_gross_including_eligible_charges"


def construct_series(ledger: pd.DataFrame, *, exclude_charges: bool = False) -> pd.DataFrame:
    """Aggregate in £0.0001 units; retain complete calendar dates and source coverage.

    Both boundary days are flagged/excluded. Missing dates retain zero OBSERVED
    revenue, not a claim about demand. Traceability remains in the source-row ledger.
    """
    if ledger.empty:
        raise ValueError("No ledger history available for forecasting")
    start, end = ledger["InvoiceDate"].min(), ledger["InvoiceDate"].max()
    dates = pd.date_range(start.normalize(), end.normalize(), freq="D")
    sales = eligible_sales(ledger)
    if exclude_charges:
        sales = sales.loc[~sales["StockCode"].isin(CHARGE_CODES)].copy()
    sales["date"] = sales["InvoiceDate"].dt.normalize()
    sales["revenue_units"] = sales["Quantity"].astype("int64") * np.rint(
        sales["UnitPrice"] * SCALE
    ).astype("int64")
    grouped = sales.groupby("date").agg(
        revenue_units=("revenue_units", "sum"), sale_lines=("source_row", "count")
    )
    table = grouped.reindex(dates, fill_value=0).rename_axis("date").reset_index()
    table["ledger_lines"] = (
        ledger.groupby(ledger["InvoiceDate"].dt.normalize())
        .size()
        .reindex(dates, fill_value=0)
        .to_numpy()
    )
    table["record_status"] = np.select(
        [table["sale_lines"].gt(0), table["ledger_lines"].gt(0)],
        ["eligible_sales", "other_ledger_only"],
        default="no_records",
    )
    table["boundary_excluded"] = table["date"].isin([dates[0], dates[-1]])
    table["revenue_gbp"] = table["revenue_units"] / SCALE
    return table


def validate_history(history: pd.Series, *, minimum: int = 1) -> pd.Series:
    """Require ordered daily, unique, finite, nonnegative historical context."""
    if not isinstance(history.index, pd.DatetimeIndex) or history.index.tz is not None:
        raise ValueError("History needs a timezone-naive DatetimeIndex")
    if len(history) < minimum:
        raise ValueError(f"Insufficient history: at least {minimum} calendar days required")
    expected = pd.date_range(history.index[0], periods=len(history), freq="D")
    if not history.index.equals(expected) or not history.index.equals(history.index.normalize()):
        raise ValueError("History must be unique, sorted, midnight-aligned, contiguous daily dates")
    values = history.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("History must contain finite nonnegative observed revenue")
    return history.astype(float).copy()


def modeled_history(table: pd.DataFrame) -> pd.Series:
    """Remove only declared boundary dates from the primary calendar series."""
    selected = table.loc[~table["boundary_excluded"]]
    return validate_history(selected.set_index("date")["revenue_gbp"], minimum=140)


def prepare_forecast_series(settings: Settings) -> dict:
    """Verify lineage, reconcile daily target with SQL, and save derived series."""
    ledger = load_verified_ledger(settings)
    table = construct_series(ledger)
    sql = run_query(settings.database_file, "daily_revenue")
    sql["date"] = pd.to_datetime(sql["date"])
    aligned = sql.set_index("date")["revenue_gbp"].reindex(table["date"], fill_value=0)
    if not np.allclose(aligned.to_numpy(), table["revenue_gbp"], rtol=0, atol=1e-6):
        raise ValueError("Forecast target does not reconcile with Phase 2 daily SQL")
    history = modeled_history(table)
    settings.forecast_dir.mkdir(parents=True, exist_ok=True)
    table.to_parquet(settings.forecast_dir / "daily_series.parquet", index=False)
    description = {
        "target_policy": TARGET_POLICY,
        "calendar_policy": "zero_observed_calendar",
        "first_source_timestamp": str(ledger["InvoiceDate"].min()),
        "last_source_timestamp": str(ledger["InvoiceDate"].max()),
        "modeling_start": str(history.index[0].date()),
        "modeling_end": str(history.index[-1].date()),
        "first_day_policy": "exclude_uncertain_boundary_not_proven_incomplete",
        "last_day_policy": "exclude_partial_midday_boundary",
        "full_revenue_gbp": float(table["revenue_gbp"].sum()),
        "modeled_revenue_gbp": float(history.sum()),
        "excluded_boundary_revenue_gbp": float(
            table.loc[table["boundary_excluded"], "revenue_gbp"].sum()
        ),
        "record_status_counts": table["record_status"]
        .value_counts()
        .reindex(["eligible_sales", "other_ledger_only", "no_records"], fill_value=0)
        .to_dict(),
        "missing_dates": table.loc[table["record_status"].eq("no_records"), "date"]
        .dt.strftime("%Y-%m-%d")
        .tolist(),
        "missing_weekdays": table.loc[table["record_status"].eq("no_records"), "date"]
        .dt.day_name()
        .value_counts()
        .to_dict(),
        "source_sha256": sha256(settings.raw_file),
        "ledger_sha256": sha256(settings.processed_dir / "transactions.parquet"),
        "series_sha256": sha256(settings.forecast_dir / "daily_series.parquet"),
        "daily_sql_reconciliation": "passed",
    }
    (settings.forecast_dir / "series_metadata.json").write_text(
        json.dumps(description, indent=2) + "\n", encoding="utf-8"
    )
    return description


def learn_inactive_weekdays(
    table: pd.DataFrame, start: pd.Timestamp, cutoff: pd.Timestamp
) -> tuple[int, ...]:
    """Freeze no-record weekdays using initial training only, never future flags."""
    initial = table.loc[table["date"].between(start, cutoff)]
    return tuple(
        day
        for day in range(7)
        if (
            len(initial.loc[initial["date"].dt.dayofweek.eq(day)]) >= 8
            and initial.loc[initial["date"].dt.dayofweek.eq(day), "ledger_lines"].eq(0).all()
        )
    )
