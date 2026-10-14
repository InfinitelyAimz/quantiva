"""Deterministic baselines and genuine recursive seven-calendar-day forecasting."""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from quantiva.features import FEATURES, feature_frame, next_features
from quantiva.forecast_series import validate_history

MODELS = ("naive", "seasonal_naive", "linear_regression", "random_forest")
SEED = 42


@dataclass
class Forecaster:
    """Fitted model and immutable training/calendar configuration."""

    name: str
    training_start: pd.Timestamp
    training_cutoff: pd.Timestamp
    estimator: Pipeline | None = None
    inactive_weekdays: tuple[int, ...] = ()
    version: str = "3.0.0"


def fit_forecaster(
    history: pd.Series, name: str, *, inactive_weekdays: tuple[int, ...] = ()
) -> Forecaster:
    """Fit preprocessing/model only on the supplied historical window."""
    minimum = 1 if name == "naive" else 7 if name == "seasonal_naive" else 56
    history = validate_history(history, minimum=minimum)
    if name not in MODELS:
        raise ValueError(f"Unknown model: {name}")
    if any(day not in range(7) for day in inactive_weekdays):
        raise ValueError("Inactive weekdays must be 0 through 6")
    estimator = None
    if name in {"linear_regression", "random_forest"}:
        features = feature_frame(history).dropna()
        features = features.loc[~features.index.dayofweek.isin(inactive_weekdays)]
        if len(features) < 14:
            raise ValueError("Insufficient active feature rows for model training")
        transform = ColumnTransformer(
            [
                (
                    "weekday",
                    OneHotEncoder(
                        categories=[list(range(7))],
                        handle_unknown="ignore",
                        drop="first",
                        sparse_output=False,
                    ),
                    ["weekday"],
                ),
                ("numeric", StandardScaler(), [f for f in FEATURES if f != "weekday"]),
            ]
        )
        model = (
            LinearRegression()
            if name == "linear_regression"
            else RandomForestRegressor(
                n_estimators=120,
                max_depth=6,
                min_samples_leaf=5,
                max_features=1.0,
                random_state=SEED,
                n_jobs=1,
            )
        )
        estimator = Pipeline([("preprocessing", transform), ("regressor", model)])
        estimator.fit(features, history.loc[features.index])
    return Forecaster(name, history.index[0], history.index[-1], estimator, inactive_weekdays)


def forecast(model: Forecaster, history: pd.Series, *, horizon: int = 7) -> pd.DataFrame:
    """Predict the full horizon from one origin; append predictions, never future actuals."""
    if horizon != 7:
        raise ValueError("This verified experiment supports exactly seven calendar days")
    minimum = 1 if model.name == "naive" else 7 if model.name == "seasonal_naive" else 28
    context = validate_history(history, minimum=minimum)
    if context.index[-1] < model.training_cutoff:
        raise ValueError("Forecast origin precedes the model training cutoff")
    origin = context.index[-1]
    rows = []
    for step in range(1, horizon + 1):
        date = origin + pd.Timedelta(days=step)
        if date.dayofweek in model.inactive_weekdays:
            prediction = 0.0
        elif model.name == "naive":
            active = context.loc[~context.index.dayofweek.isin(model.inactive_weekdays)]
            if active.empty:
                raise ValueError("No active historical observation for naive prediction")
            prediction = float(active.iloc[-1])
        elif model.name == "seasonal_naive":
            prediction = float(context.loc[date - pd.Timedelta(days=7)])
        else:
            if model.estimator is None:
                raise ValueError("Regression estimator is missing")
            prediction = float(model.estimator.predict(next_features(context))[0])
        if not np.isfinite(prediction):
            raise ValueError("Model produced a nonfinite prediction")
        # Gross revenue cannot be negative. Same clipping policy in all evaluations/inference.
        prediction = max(0.0, prediction)
        rows.append(
            {
                "date": date,
                "horizon": step,
                "prediction_gbp": prediction,
                "forecast_origin": origin,
                "model": model.name,
                "model_version": model.version,
                "training_cutoff": model.training_cutoff,
                "interpretation": "retrospective historical demonstration",
            }
        )
        context = pd.concat([context, pd.Series([prediction], index=pd.DatetimeIndex([date]))])
    return pd.DataFrame(rows)
