"""Hand calculations and adversarial future perturbations detect leakage."""

import numpy as np
import pandas as pd
import pytest

from quantiva.features import feature_frame, next_features
from quantiva.forecast_series import construct_series, learn_inactive_weekdays, validate_history


def history(length=100):
    return pd.Series(
        np.arange(1, length + 1, dtype=float), index=pd.date_range("2011-01-01", periods=length)
    )


def test_target_eligibility_calendar_and_boundaries(cleaning_result):
    table = construct_series(cleaning_result.ledger).set_index("date")
    assert table["revenue_gbp"].sum() == 21
    assert table.loc["2011-01-01", "revenue_gbp"] == 20  # Anonymous purchase included.
    assert table.loc["2011-01-02", "record_status"] == "no_records"
    assert table.loc["2011-03-03", "record_status"] == "other_ledger_only"
    assert table["boundary_excluded"].sum() == 2
    changed = cleaning_result.ledger.copy()
    changed.loc[changed["StockCode"].eq("A"), "StockCode"] = "DOT"
    assert construct_series(changed, exclude_charges=True)["revenue_gbp"].sum() == 4


def test_lag_rolling_features_and_inference_row_agree():
    values = history()
    frame = feature_frame(values)
    row = frame.iloc[28]
    assert row["lag_1"] == 28
    assert row["lag_7"] == 22
    assert row["lag_28"] == 1
    assert row["mean_7"] == np.mean(np.arange(22, 29))
    assert row["mean_28"] == 14.5
    assert row["std_7"] == np.std(np.arange(22, 29), ddof=1)
    pd.testing.assert_frame_equal(
        next_features(values.iloc[:28]), frame.iloc[[28]], check_freq=False
    )


def test_future_targets_cannot_change_current_features():
    values = history()
    before = feature_frame(values).iloc[28].copy()
    values.iloc[28:] = 1e9
    pd.testing.assert_series_equal(before, feature_frame(values).iloc[28])


@pytest.mark.parametrize(
    "bad",
    [
        pd.Series([1, 2]),
        history(10).iloc[[0, 2, 3]],
        pd.Series([1, np.nan], index=pd.date_range("2011-01-01", periods=2)),
        pd.Series([1, -1], index=pd.date_range("2011-01-01", periods=2)),
    ],
)
def test_history_validation_rejects_bad_inputs(bad):
    with pytest.raises(ValueError):
        validate_history(bad)


def test_insufficient_context_is_actionable():
    with pytest.raises(ValueError, match="Insufficient history"):
        next_features(history(27))


def test_weekday_schedule_ignores_future_activity_flags():
    dates = pd.date_range("2011-01-01", periods=140)
    coverage = pd.DataFrame({"date": dates, "ledger_lines": (dates.dayofweek != 5).astype(int)})
    cutoff = dates[69]
    assert learn_inactive_weekdays(coverage, dates[0], cutoff) == (5,)
    coverage.loc[coverage["date"] > cutoff, "ledger_lines"] = 999
    assert learn_inactive_weekdays(coverage, dates[0], cutoff) == (5,)
