"""Streamlit app tests exercise actual widgets/renderers without browser dependence."""

import json
from pathlib import Path

import plotly.graph_objects as go
import pytest
from streamlit.testing.v1 import AppTest

from quantiva.dashboard.theme import THEMES, chart_theme, css, theme_state


def test_theme_switching_and_persistence():
    state = {}
    assert theme_state(state, "dark") == "dark"
    state["quantiva_theme"] = "light"
    assert theme_state(state, "dark") == "light"
    state["quantiva_theme"] = "bad"
    assert theme_state(state, "dark") == "dark"
    for name in THEMES:
        assert THEMES[name]["background"] in css(name)
        fig = chart_theme(go.Figure(), name)
        assert fig.layout.paper_bgcolor == THEMES[name]["surface"]
        assert fig.layout.hoverlabel.font.color == THEMES[name]["text"]
    with pytest.raises(ValueError):
        chart_theme(go.Figure(), "bad")


@pytest.mark.parametrize("page", ["overview", "sales", "customers"])
@pytest.mark.parametrize("theme", ["dark", "light"])
def test_business_pages_filters_and_themes(analytical_database, tmp_path, page, theme):
    # Settings resolve a synthetic SQLite fixture only; published findings never use it.
    import shutil

    data = tmp_path / "data"
    (data / "processed").mkdir(parents=True)
    shutil.copyfile(analytical_database, data / "processed/quantiva.db")
    source = f"""from pathlib import Path
import streamlit as st
from quantiva.config import Settings
from quantiva.dashboard.pages import {page}
from quantiva.dashboard.theme import css
st.session_state['quantiva_theme']={theme!r}
st.html(css({theme!r}))
{page}(Settings(Path({str(data)!r})),Path({str(tmp_path)!r}))
"""
    app = AppTest.from_string(source).run(timeout=30)
    assert not app.exception
    assert app.metric
    app.multiselect[0].set_value(["(Unknown)"]).run()
    assert not app.exception
    assert app.metric[0].value == ("0" if page == "customers" else "£10.00")


def test_entrypoint_missing_artifacts_keeps_navigation(monkeypatch, tmp_path):
    monkeypatch.setenv("QUANTIVA_DATA_DIR", str(tmp_path / "empty"))
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app/Home.py")).run(
        timeout=30
    )
    assert not app.exception and app.warning
    app.radio[0].set_value("dark").run()
    assert not app.exception and app.session_state["quantiva_theme"] == "dark"


def test_quality_counts_and_corrupt_metadata(tmp_path):
    data = tmp_path / "data/processed"
    data.mkdir(parents=True)
    report = {
        "cleaned_records": 8,
        "transaction_types": {"completed_sale": 4, "cancellation": 1},
        "duplicate_records_removed": 1,
        "quarantined_records": 0,
        "exclusion_reasons": {"exact_duplicate": 1},
        "source_sha256": "fixture",
        "policy_version": "test",
    }
    inspect = {
        "original_records": 9,
        "missing_values": {"CustomerID": 2, "Description": 1},
        "date_min": "2011-01-01",
        "date_max": "2011-03-03",
    }
    for name, value in [("cleaning_report", report), ("initial_inspection", inspect)]:
        (data / f"{name}.json").write_text(json.dumps(value))
    source = f"""from pathlib import Path
import streamlit as st
from quantiva.config import Settings
from quantiva.dashboard.pages import quality
st.session_state['quantiva_theme']='dark'
quality(Settings(Path({str(data.parent)!r})),Path({str(tmp_path)!r}))
"""
    app = AppTest.from_string(source).run(timeout=30)
    assert not app.exception and app.metric[0].value == "9"
    assert app.info
