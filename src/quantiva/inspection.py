"""Inspect raw quality before deciding how to treat questionable records."""

import numpy as np
import pandas as pd


def inspect_data(frame: pd.DataFrame) -> dict:
    """Return JSON-safe quality counts; overlapping conditions are not additive."""
    quantity = pd.to_numeric(frame["Quantity"], errors="coerce")
    price = pd.to_numeric(frame["UnitPrice"], errors="coerce")
    dates = pd.to_datetime(frame["InvoiceDate"], errors="coerce", format="mixed")
    cancelled = frame["InvoiceNo"].astype("string").str.upper().str.startswith("C", na=False)
    negative = quantity.lt(0)
    customer = pd.to_numeric(frame["CustomerID"], errors="coerce")
    return {
        "original_records": len(frame),
        "column_types": {key: str(value) for key, value in frame.dtypes.items()},
        "missing_values": {key: int(value) for key, value in frame.isna().sum().items()},
        "duplicate_records": int(frame.duplicated().sum()),
        "duplicate_group_members": int(frame.duplicated(keep=False).sum()),
        "cancelled_records": int(cancelled.sum()),
        "negative_quantity_records": int(negative.sum()),
        "cancelled_negative_quantity_records": int((cancelled & negative).sum()),
        "noncancelled_negative_quantity_records": int((~cancelled & negative).sum()),
        "cancelled_nonnegative_quantity_records": int((cancelled & ~negative).sum()),
        "zero_quantity_records": int(quantity.eq(0).sum()),
        "zero_price_records": int(price.eq(0).sum()),
        "negative_price_records": int(price.lt(0).sum()),
        "invalid_quantity_records": int((~np.isfinite(quantity) | quantity.mod(1).ne(0)).sum()),
        "invalid_price_records": int((~np.isfinite(price)).sum()),
        "invalid_timestamp_records": int(dates.isna().sum()),
        "identifiable_customers": int(customer[customer.gt(0)].nunique()),
        "date_min": str(dates.min()),
        "date_max": str(dates.max()),
        "quantity_percentiles": {
            str(k): float(v)
            for k, v in quantity.quantile([0, 0.01, 0.25, 0.5, 0.75, 0.99, 1]).items()
        },
        "unit_price_percentiles": {
            str(k): float(v) for k, v in price.quantile([0, 0.01, 0.25, 0.5, 0.75, 0.99, 1]).items()
        },
        "negative_noncancelled_description_examples": frame.loc[
            ~cancelled & negative, "Description"
        ]
        .dropna()
        .astype(str)
        .value_counts()
        .head(15)
        .to_dict(),
    }
