"""Local trust, exact reload predictions, integrity failures, and deployment schema."""

import numpy as np
import pandas as pd
import pytest

from quantiva.forecasting import fit_forecaster, forecast
from quantiva.model_artifacts import forecast_saved, load_artifact, save_artifact, verify_artifact


@pytest.mark.parametrize("name", ["naive", "seasonal_naive", "linear_regression", "random_forest"])
def test_saved_models_reload_and_forecast_same_values(tmp_path, name):
    history = pd.Series(
        np.arange(1, 101, dtype=float), index=pd.date_range("2011-01-01", periods=100)
    )
    model = fit_forecaster(history, name)
    metadata = save_artifact(model, history, tmp_path, {"forecast_horizon": 7})
    assert metadata["training_end"] == "2011-04-10"
    expected = forecast(model, history)
    loaded = forecast_saved(tmp_path, trusted=True)
    np.testing.assert_allclose(
        expected["prediction_gbp"], loaded["prediction_gbp"], atol=1e-10, rtol=0
    )
    assert set(loaded.columns) == {
        "date",
        "horizon",
        "prediction_gbp",
        "forecast_origin",
        "model",
        "model_version",
        "training_cutoff",
        "interpretation",
    }
    assert verify_artifact(tmp_path)["horizon"] == 7
    with pytest.raises(ValueError, match="explicit trust"):
        load_artifact(tmp_path)
    with (tmp_path / "selected.joblib").open("ab") as stream:
        stream.write(b"modified")
    with pytest.raises(ValueError, match="checksum mismatch"):
        load_artifact(tmp_path, trusted=True)


def test_missing_artifacts_and_no_context_are_actionable(tmp_path):
    with pytest.raises(FileNotFoundError, match="forecast-train"):
        forecast_saved(tmp_path, trusted=True)
