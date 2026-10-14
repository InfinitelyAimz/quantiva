"""Actual saved-evidence validation remains available without a model binary."""

import json

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from quantiva.dashboard.evidence import load_evidence
from quantiva.forecast_evaluation import summarize_predictions


@pytest.fixture
def evidence_folder(tmp_path):
    folder = tmp_path / "reports"
    folder.mkdir()
    summary = {
        "selected_model": "random_forest",
        "series": {"modeling_start": "2011-01-01", "modeling_end": "2011-03-01"},
        "sensitivities": [],
        "artifact_metadata_sha256": "no-model",
    }
    for name, start, names in [
        (
            "validation",
            "2011-01-08",
            ["naive", "seasonal_naive", "linear_regression", "random_forest"],
        ),
        ("test", "2011-01-15", ["naive", "seasonal_naive", "random_forest"]),
    ]:
        dates = pd.date_range(start, periods=7)
        frame = pd.concat(
            [
                pd.DataFrame(
                    {
                        "date": dates,
                        "forecast_origin": dates[0] - pd.Timedelta(days=1),
                        "training_cutoff": pd.Timestamp("2011-01-07"),
                        "horizon": range(1, 8),
                        "model": model,
                        "prediction_gbp": 10.0,
                        "actual_gbp": 12.0,
                        "fold": 1,
                        "experiment": "primary" if name == "validation" else "heldout_primary",
                    }
                )
                for model in names
            ],
            ignore_index=True,
        )
        frame.to_csv(folder / f"forecast_{name}_predictions.csv", index=False)
        summary["validation" if name == "validation" else "heldout_test"] = summarize_predictions(
            frame
        ).to_dict("records")
    (folder / "forecast_results.json").write_text(json.dumps(summary))
    return folder


def test_evidence_separates_validation_and_test(evidence_folder):
    evidence = load_evidence(evidence_folder)
    assert "linear_regression" in evidence["validation_metrics"]["model"].tolist()
    assert "linear_regression" not in evidence["test_metrics"]["model"].tolist()
    assert evidence["validation"]["date"].max() < evidence["test"]["date"].min()


def test_evidence_rejects_tampered_predictions(evidence_folder):
    path = evidence_folder / "forecast_test_predictions.csv"
    frame = pd.read_csv(path)
    frame.loc[0, "prediction_gbp"] = 1000
    frame.to_csv(path, index=False)
    with pytest.raises(ValueError, match="disagree"):
        load_evidence(evidence_folder)


def test_predictive_page_without_model_preserves_evaluation(evidence_folder):
    root = evidence_folder.parent
    source = f"""from pathlib import Path
import streamlit as st
from quantiva.config import Settings
from quantiva.dashboard.pages import predictive
st.session_state['quantiva_theme']='light'
predictive(Settings(Path({str(root / "missing_data")!r})),Path({str(root)!r}))
"""
    app = AppTest.from_string(source).run(timeout=30)
    assert not app.exception
    assert any("artifacts unavailable" in warning.value for warning in app.warning)
    assert any("Retrospective" in h.value for h in app.subheader)
    app.radio[0].set_value("test").run()
    assert not app.exception
    assert app.selectbox[0].value == "random_forest"


def test_missing_evaluation_has_setup_message(tmp_path):
    source = f"""from pathlib import Path
import streamlit as st
from quantiva.config import Settings
from quantiva.dashboard.pages import predictive
st.session_state['quantiva_theme']='dark'
predictive(Settings(Path({str(tmp_path)!r})),Path({str(tmp_path)!r}))
"""
    app = AppTest.from_string(source).run(timeout=30)
    assert not app.exception and app.warning
    assert "forecast-train" in app.warning[0].value
