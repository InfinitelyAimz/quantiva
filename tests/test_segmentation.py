"""RFM recency, tie safety, sparse scores and exhaustive ordered segment rules."""

import numpy as np
import pandas as pd
import pytest

from quantiva.dashboard.data import Filters, bundle, catalog
from quantiva.segmentation import SEGMENTS, build_rfm, score_values


def test_identifiable_rfm_uses_distinct_invoices(analytical_database):
    c = catalog(analytical_database)
    r = build_rfm(
        bundle(analytical_database, Filters(c["start"], c["end"]))["customers"],
        pd.Timestamp("2011-03-04"),
    )
    assert r["customer_id"].tolist() == ["10"]
    assert r.iloc[0]["frequency"] == 2
    assert r.iloc[0]["monetary_gbp"] == 11
    assert r.iloc[0]["recency_days"] == 60
    assert r.iloc[0]["rfm_score"] == 333


def test_score_direction_and_ties():
    values = pd.Series([1, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    f = score_values(values)
    r = score_values(values, reverse=True)
    assert f.iloc[0] == f.iloc[1] and f.iloc[-1] > f.iloc[0]
    assert r.iloc[-1] < r.iloc[0]
    assert score_values(pd.Series([7, 7, 7])).tolist() == [3, 3, 3]
    assert score_values(pd.Series([1, 2, 3])).tolist() == [1, 3, 5]


def test_segments_exhaustive_and_exclusive():
    customers = pd.DataFrame(
        {
            "customer_id": np.arange(125).astype(str),
            "last_purchase": pd.date_range("2011-01-01", periods=125),
            "frequency": np.tile(np.arange(1, 26), 5),
            "monetary_gbp": np.arange(1, 126) * 10,
        }
    )
    r = build_rfm(customers, pd.Timestamp("2011-05-06"))
    assert len(r) == len(customers) and not r["segment"].isna().any()
    assert set(r["segment"]) == set(SEGMENTS)
    for row in r.itertuples():
        conditions = [
            row.r_score >= 4 and row.f_score >= 4 and row.m_score >= 4,
            row.r_score <= 2 and (row.f_score >= 3 or row.m_score >= 4),
            row.r_score <= 2,
            row.f_score >= 4,
            row.r_score >= 4 and row.f_score <= 2,
            True,
        ]
        assert row.segment == SEGMENTS[conditions.index(True)]


def test_rfm_empty_invalid_reference_and_nonfinite():
    assert build_rfm(
        pd.DataFrame(columns=["customer_id", "last_purchase", "frequency", "monetary_gbp"]),
        pd.Timestamp("2011-01-01"),
    ).empty
    with pytest.raises(ValueError):
        score_values(pd.Series([np.inf]))
    with pytest.raises(ValueError):
        build_rfm(pd.DataFrame({"last_purchase": ["2011-01-01"]}), pd.Timestamp("2011-01-01"))
