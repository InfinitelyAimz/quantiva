"""Constant histories have undefined correlations but JSON-safe diagnostics."""

import json

import pandas as pd
import pytest

from quantiva.forecast_experiment import series_diagnostics


@pytest.mark.parametrize("revenue", [0.0, 125.5], ids=["constant_zero", "constant_positive"])
def test_constant_history_diagnostics_serialize_undefined_autocorrelations(revenue):
    history = pd.Series(revenue, index=pd.date_range("2011-01-01", periods=140))
    diagnostics = series_diagnostics(history)
    assert diagnostics["autocorrelation"] == {"1": None, "7": None, "14": None, "28": None}
    assert diagnostics["mean_gbp"] == revenue
    assert diagnostics["median_gbp"] == revenue
    assert diagnostics["std_gbp"] == 0.0
    assert diagnostics["max_gbp"] == revenue
    serialized = json.dumps(diagnostics, allow_nan=False)
    assert json.loads(serialized)["autocorrelation"] == {
        "1": None,
        "7": None,
        "14": None,
        "28": None,
    }
