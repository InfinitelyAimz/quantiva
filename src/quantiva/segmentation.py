"""Descriptive RFM scoring; ties are never broken using customer identifiers."""

import numpy as np
import pandas as pd

SEGMENTS = (
    "Champions",
    "At Risk",
    "Hibernating",
    "Loyal Customers",
    "New Customers",
    "Potential Loyalists",
)


def score_values(values: pd.Series, *, reverse: bool = False) -> pd.Series:
    """Five-point empirical quantiles; constant=3 and sparse values use spaced ranks."""
    if values.empty:
        return pd.Series(index=values.index, dtype="int64")
    if not np.isfinite(values).all():
        raise ValueError("RFM values must be finite")
    unique = values.nunique()
    if unique == 1:
        scores = pd.Series(3, index=values.index)
    elif unique < 5:
        scores = (1 + 4 * (values.rank(method="dense") - 1) / (unique - 1)).round().astype(int)
    else:
        thresholds = values.quantile([0.2, 0.4, 0.6, 0.8]).to_numpy()
        scores = pd.Series(np.searchsorted(thresholds, values, side="left") + 1, index=values.index)
    return (6 - scores if reverse else scores).astype("int64")


def build_rfm(customers: pd.DataFrame, reference_date: pd.Timestamp) -> pd.DataFrame:
    """Score SQL customer aggregates relative to the day AFTER the filter end date."""
    frame = customers.copy()
    if frame.empty:
        for name in ["recency_days", "r_score", "f_score", "m_score", "rfm_score"]:
            frame[name] = pd.Series(dtype="int64")
        frame["segment"] = pd.Series(dtype="string")
        return frame
    frame["last_purchase"] = pd.to_datetime(frame["last_purchase"])
    reference = pd.Timestamp(reference_date).normalize()
    if reference <= frame["last_purchase"].max().normalize():
        raise ValueError("RFM reference must be after every eligible purchase date")
    frame["recency_days"] = (reference - frame["last_purchase"].dt.normalize()).dt.days
    frame["r_score"] = score_values(frame["recency_days"], reverse=True)
    frame["f_score"] = score_values(frame["frequency"])
    frame["m_score"] = score_values(frame["monetary_gbp"])
    r, f, m = frame["r_score"], frame["f_score"], frame["m_score"]
    frame["segment"] = np.select(
        [
            r.ge(4) & f.ge(4) & m.ge(4),
            r.le(2) & (f.ge(3) | m.ge(4)),
            r.le(2),
            f.ge(4),
            r.ge(4) & f.le(2),
        ],
        list(SEGMENTS[:-1]),
        default=SEGMENTS[-1],
    )
    frame["rfm_score"] = 100 * r + 10 * f + m
    return frame
