"""Multi-step causality, baselines, chronological isolation, and metric edge cases."""

import numpy as np
import pandas as pd
import pytest

from quantiva.forecast_evaluation import SplitPlan, heldout_evaluation, rolling_validation, score
from quantiva.forecast_experiment import select_candidate
from quantiva.forecasting import Forecaster, fit_forecaster, forecast


def history(length=210):
    dates = pd.date_range("2011-01-01", periods=length)
    return pd.Series(20 + dates.dayofweek.to_numpy() * 5, index=dates, dtype=float)


def test_naive_and_weekly_baselines_use_only_available_history():
    values = history()
    naive = forecast(fit_forecaster(values, "naive"), values)
    assert naive["prediction_gbp"].tolist() == [values.iloc[-1]] * 7
    seasonal = forecast(fit_forecaster(values, "seasonal_naive"), values)
    assert seasonal["prediction_gbp"].tolist() == values.iloc[-7:].tolist()
    assert seasonal["horizon"].tolist() == list(range(1, 8))
    assert seasonal["date"].tolist() == list(
        pd.date_range(values.index[-1] + pd.Timedelta(days=1), periods=7)
    )


def test_recursive_forecasting_uses_previous_predictions():
    values = history()
    rows = []

    class Estimator:
        def predict(self, features):
            rows.append(features.iloc[0].to_dict())
            return np.array([features.iloc[0]["lag_1"] + 1])

    model = Forecaster("linear_regression", values.index[0], values.index[-1], Estimator())
    result = forecast(model, values)
    assert result["prediction_gbp"].tolist() == [values.iloc[-1] + step for step in range(1, 8)]
    assert rows[1]["lag_1"] == result.iloc[0]["prediction_gbp"]
    assert rows[6]["lag_7"] == values.iloc[-1]


def test_zero_revenue_and_metrics():
    assert score([0, 10], [5, 5]) == {
        "mae_gbp": 5,
        "rmse_gbp": 5,
        "wape_pct": 100,
        "bias_gbp": 0,
        "observations": 2,
    }
    assert score([0, 0], [1, 2])["wape_pct"] is None
    with pytest.raises(ValueError):
        score([], [])
    with pytest.raises(ValueError):
        score([1], [np.inf])


def test_chronological_split_and_holdout_separation():
    values = history(280)
    plan = SplitPlan()
    split = plan.boundaries(values)
    assert split["validation_start"] == 168
    assert split["test_start"] == 224
    development = values.iloc[: split["test_start"]]
    validation = rolling_validation(
        development, split["validation_start"], names=("seasonal_naive",)
    )
    assert len(validation) == 56
    assert (validation["date"] > validation["training_cutoff"]).all()
    assert validation["date"].max() < values.index[split["test_start"]]
    fitted = fit_forecaster(development, "linear_regression")
    test = heldout_evaluation(values, split["test_start"], fitted)
    assert len(test) == 56 * 3
    assert test.loc[test["model"].eq("linear_regression"), "training_cutoff"].nunique() == 1
    # Targets within the FIRST seven-day block may alter errors, never predictions.
    changed = values.copy()
    changed.iloc[split["test_start"] : split["test_start"] + 7] = 1e8
    altered = heldout_evaluation(changed, split["test_start"], fitted)
    pd.testing.assert_series_equal(
        test.loc[test["fold"].eq(1), "prediction_gbp"],
        altered.loc[altered["fold"].eq(1), "prediction_gbp"],
    )
    with pytest.raises(ValueError, match="trained on held-out"):
        heldout_evaluation(values, split["test_start"], fit_forecaster(values, "linear_regression"))


@pytest.mark.parametrize("name", ["linear_regression", "random_forest"])
def test_regression_predictions_are_deterministic(name):
    values = history()
    one = forecast(fit_forecaster(values, name), values)
    two = forecast(fit_forecaster(values, name), values)
    pd.testing.assert_frame_equal(one, two)
    assert one["prediction_gbp"].ge(0).all()


def test_insufficient_history_and_invalid_horizon():
    with pytest.raises(ValueError, match="Insufficient history"):
        fit_forecaster(history(6), "seasonal_naive")
    with pytest.raises(ValueError, match="Insufficient history"):
        fit_forecaster(history(55), "random_forest")
    with pytest.raises(ValueError):
        SplitPlan().boundaries(history(200))
    with pytest.raises(ValueError, match="exactly seven"):
        forecast(fit_forecaster(history(), "naive"), history(), horizon=30)


def test_selection_refuses_heldout_or_sensitivity_rows():
    for experiment in ["heldout_primary", "excluding_named_charges"]:
        with pytest.raises(ValueError, match="primary validation only"):
            select_candidate(pd.DataFrame({"experiment": [experiment]}))
