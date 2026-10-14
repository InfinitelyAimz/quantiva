"""Historical-only features shared by training and recursive inference."""

import numpy as np
import pandas as pd

from quantiva.forecast_series import validate_history

LAGS = (1, 7, 14, 28)
WINDOWS = (7, 14, 28)
FEATURES = (
    "weekday",
    "month_sin",
    "month_cos",
    "day_of_month",
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "mean_7",
    "mean_14",
    "mean_28",
    "std_7",
    "trend_7_28",
)


def feature_frame(history: pd.Series) -> pd.DataFrame:
    """Training row t uses calendar t and revenue no later than t−1."""
    history = validate_history(history)
    frame = pd.DataFrame(index=history.index)
    frame["weekday"] = history.index.dayofweek
    frame["month_sin"] = np.sin(2 * np.pi * history.index.month / 12)
    frame["month_cos"] = np.cos(2 * np.pi * history.index.month / 12)
    frame["day_of_month"] = history.index.day
    for lag in LAGS:
        frame[f"lag_{lag}"] = history.shift(lag)
    previous = history.shift(1)
    for window in WINDOWS:
        frame[f"mean_{window}"] = previous.rolling(window, min_periods=window).mean()
    frame["std_7"] = previous.rolling(7, min_periods=7).std(ddof=1)
    frame["trend_7_28"] = frame["mean_7"] - frame["mean_28"]
    return frame[list(FEATURES)]


def next_features(history: pd.Series) -> pd.DataFrame:
    """Construct tomorrow's row from a validated history, with no future actuals."""
    history = validate_history(history, minimum=28)
    date = history.index[-1] + pd.Timedelta(days=1)
    # Placeholder is not read by any shifted feature; training and inference agree.
    extended = pd.concat([history, pd.Series([0.0], index=pd.DatetimeIndex([date]))])
    return feature_frame(extended).iloc[[-1]]
