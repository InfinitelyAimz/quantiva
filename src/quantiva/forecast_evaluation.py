"""Chronological folds, finite metrics, and held-out-safe evaluation."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from quantiva.forecast_series import validate_history
from quantiva.forecasting import MODELS, Forecaster, fit_forecaster, forecast


@dataclass(frozen=True)
class SplitPlan:
    """Eight disjoint weekly validation windows and eight disjoint test windows."""

    validation_days: int = 56
    test_days: int = 56
    horizon: int = 7
    minimum_training_days: int = 140

    def boundaries(self, history: pd.Series) -> dict:
        """Split by position/date only, never target values."""
        validate_history(history)
        if self.horizon != 7 or self.validation_days % 7 or self.test_days % 7:
            raise ValueError("Validation/test periods must be positive multiples of seven")
        if self.validation_days <= 0 or self.test_days <= 0:
            raise ValueError("Validation/test periods must be positive")
        test = len(history) - self.test_days
        validation = test - self.validation_days
        if validation < self.minimum_training_days:
            raise ValueError("Insufficient history for chronological training/validation/test")
        return {
            "validation_start": validation,
            "test_start": test,
            "training_start_date": str(history.index[0].date()),
            "initial_training_end_date": str(history.index[validation - 1].date()),
            "validation_start_date": str(history.index[validation].date()),
            "validation_end_date": str(history.index[test - 1].date()),
            "test_start_date": str(history.index[test].date()),
            "test_end_date": str(history.index[-1].date()),
        }


def score(actual, predicted) -> dict:
    """GBP MAE/RMSE and WAPE = sum absolute error / sum absolute actual ×100.

    WAPE is undefined when all actuals are zero; never divide by individual daily zeros.
    """
    actual, predicted = np.asarray(actual, dtype=float), np.asarray(predicted, dtype=float)
    if actual.shape != predicted.shape or actual.ndim != 1 or actual.size == 0:
        raise ValueError("Metrics require equal-length nonempty one-dimensional arrays")
    if not np.isfinite(actual).all() or not np.isfinite(predicted).all():
        raise ValueError("Metrics require finite inputs")
    error = predicted - actual
    denominator = np.abs(actual).sum()
    return {
        "mae_gbp": float(np.abs(error).mean()),
        "rmse_gbp": float(np.sqrt(np.mean(error**2))),
        "wape_pct": float(100 * np.abs(error).sum() / denominator) if denominator else None,
        "bias_gbp": float(error.mean()),
        "observations": len(actual),
    }


def summarize_predictions(predictions: pd.DataFrame, *, by: str | None = None) -> pd.DataFrame:
    """Aggregate equal forecast dates, keeping experiment labels distinct."""
    keys = ["experiment", "model"] + ([by] if by else [])
    rows = []
    for group, frame in predictions.groupby(keys, sort=True):
        rows.append(
            {
                **dict(zip(keys, group, strict=True)),
                **score(frame["actual_gbp"], frame["prediction_gbp"]),
            }
        )
    return pd.DataFrame(rows)


def rolling_validation(
    development: pd.Series, start: int, *, names=MODELS, inactive_weekdays=(), experiment="primary"
) -> pd.DataFrame:
    """Refit expanding history at each weekly origin, never accept held-out data."""
    development = validate_history(development)
    if start < 56 or (len(development) - start) % 7 or start >= len(development):
        raise ValueError("Invalid validation boundaries")
    rows = []
    for position in range(start, len(development), 7):
        training = development.iloc[:position]
        actual = development.iloc[position : position + 7]
        for name in names:
            model = fit_forecaster(training, name, inactive_weekdays=inactive_weekdays)
            predicted = forecast(model, training)
            predicted["actual_gbp"] = actual.to_numpy()
            predicted["fold"] = (position - start) // 7 + 1
            predicted["experiment"] = experiment
            rows.append(predicted)
    return pd.concat(rows, ignore_index=True)


def heldout_evaluation(
    history: pd.Series, start: int, selected: Forecaster, *, baselines=("naive", "seasonal_naive")
) -> pd.DataFrame:
    """Freeze learned weights before test; later origins may use already observed context.

    No estimator refits on test targets. Each seven-day block remains unavailable
    until after its predictions. This models scheduled weekly rolling forecasts.
    """
    history = validate_history(history)
    if start < 56 or (len(history) - start) % 7 or start >= len(history):
        raise ValueError("Invalid held-out boundary")
    if selected.training_cutoff >= history.index[start]:
        raise ValueError("Selected model was trained on held-out test dates")
    models = {selected.name: selected}
    for name in baselines:
        models.setdefault(name, fit_forecaster(history.iloc[:start], name))
    rows = []
    for position in range(start, len(history), 7):
        context = history.iloc[:position]
        for model in models.values():
            predicted = forecast(model, context)
            predicted["actual_gbp"] = history.iloc[position : position + 7].to_numpy()
            predicted["fold"] = (position - start) // 7 + 1
            predicted["experiment"] = "heldout_primary"
            rows.append(predicted)
    return pd.concat(rows, ignore_index=True)
