"""Display conversion must not alter analytical values, ranking, or source artifacts."""

import io
from decimal import Decimal

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from quantiva.dashboard import components
from quantiva.dashboard.currency import (
    FX_DATE,
    GBP_TO_ZAR,
    Currency,
    currency_state,
    display_values,
    table_values,
)


def test_fixed_rate_provenance_and_default_persistence():
    assert (Decimal("10.8374") / Decimal("0.8528")).quantize(Decimal("0.000001")) == GBP_TO_ZAR
    assert FX_DATE == "2011-12-08"
    state = {}
    assert currency_state(state).code == "ZAR"
    state["display_currency"] = "GBP"
    assert currency_state(state).code == "GBP"
    state["display_currency"] = "invalid"
    assert currency_state(state).code == "ZAR"
    with pytest.raises(ValueError):
        Currency("USD")


@pytest.mark.parametrize("code", ["GBP", "ZAR"])
def test_formatting_missing_zero_negative_and_rounding(code):
    unit = Currency(code)
    assert unit.money(None) == unit.money(np.nan) == "—"
    assert unit.money(0) == unit.symbol + "0.00"
    assert unit.money(-100) == unit.symbol + ("-100.00" if code == "GBP" else "-1,270.80")
    assert unit.money(100) == unit.symbol + ("100.00" if code == "GBP" else "1,270.80")
    assert Currency("GBP").money(1.005) == "£1.01"


@pytest.mark.parametrize("code", ["GBP", "ZAR"])
def test_evaluation_rfm_values_exports_and_sources_stay_independent(code):
    source = pd.DataFrame(
        {
            "model": ["seasonal_naive", "random_forest"],
            "mae_gbp": [11250.17, 12344.71],
            "rmse_gbp": [15.0, 20.0],
            "bias_gbp": [-2.0, 3.0],
            "monetary_gbp": [10.0, 30.0],
            "wape_pct": [24.31, 26.68],
            "frequency": [2, 3],
            "rfm_score": [345, 444],
        }
    )
    original = source.copy(deep=True)
    unit = Currency(code)
    shown = display_values(source, unit)
    factor = float(unit.factor)
    for name in ["mae_gbp", "rmse_gbp", "bias_gbp", "monetary_gbp"]:
        np.testing.assert_allclose(shown[name], source[name] * factor)
    for name in ["wape_pct", "frequency", "rfm_score"]:
        pd.testing.assert_series_equal(shown[name], source[name])
    assert shown.loc[shown.mae_gbp.idxmin(), "model"] == "seasonal_naive"
    exported = pd.read_csv(io.StringIO(table_values(source, unit, export=True).to_csv(index=False)))
    assert f"mae_{code.lower()}" in exported
    assert exported.source_currency.eq("GBP").all()
    assert exported.display_currency.eq(code).all()
    assert exported.fx_reference_date.eq(FX_DATE).all()
    assert exported.illustrative_conversion.eq(code == "ZAR").all()
    pd.testing.assert_frame_equal(source, original)


def test_mixed_duplicate_sensitivity_converts_only_monetary_rows():
    source = pd.DataFrame(
        {
            "metric": ["gross_revenue_gbp", "completed_orders", "aov_gbp", "units_sold"],
            "deduplicated": [100, 2, 50, 8],
            "duplicates_retained": [110, 2, 55, 9],
            "difference": [10, 0, 5, 1],
            "change_pct": [10, 0, 10, 12.5],
        }
    )
    shown = table_values(source, Currency("ZAR"))
    np.testing.assert_allclose(shown.difference, [127.08021, 0, 63.540105, 1])
    assert shown.unit.tolist() == ["ZAR", "count", "ZAR", "count"]
    assert shown.metric.tolist() == [
        "gross_revenue_zar",
        "completed_orders",
        "aov_zar",
        "units_sold",
    ]
    pd.testing.assert_series_equal(shown.change_pct, source.change_pct)
    assert source.deduplicated.tolist() == [100, 2, 50, 8]


def test_chart_table_and_csv_share_selected_currency(monkeypatch):
    source = pd.DataFrame({"country": ["A", "B"], "revenue_gbp": [100.0, 50.0], "orders": [2, 1]})
    captured = {}
    monkeypatch.setattr(
        components.st, "session_state", {"display_currency": "ZAR", "quantiva_theme": "light"}
    )
    monkeypatch.setattr(components.st, "plotly_chart", lambda fig, **kw: captured.update(fig=fig))
    monkeypatch.setattr(components.st, "markdown", lambda *args, **kw: None)
    monkeypatch.setattr(components.st, "html", lambda html: captured.update(html=html))
    monkeypatch.setattr(components.st, "caption", lambda *args, **kw: None)
    monkeypatch.setattr(
        components.st, "download_button", lambda label, data, name: captured.update(csv=data)
    )
    components.chart(source, "country", "revenue_gbp", "Revenue", currency=True)
    components.table(source, limit=1)
    fig = captured["fig"]
    np.testing.assert_allclose(fig.data[0].y, [1270.8021, 635.40105])
    assert fig.layout.yaxis.tickprefix == "R "
    assert "ZAR" in fig.data[0].hovertemplate and "GBP" not in fig.data[0].hovertemplate
    assert "Revenue ZAR" in captured["html"] and "1,270.80" in captured["html"]
    exported = pd.read_csv(io.StringIO(captured["csv"]))
    np.testing.assert_allclose(exported.revenue_zar, fig.data[0].y)
    assert exported.orders.tolist() == [2, 1]
    assert source.revenue_gbp.tolist() == [100, 50]


def test_currency_toggle_and_page_reruns(analytical_database):
    source = f"""from pathlib import Path
from types import SimpleNamespace
import streamlit as st
from quantiva.dashboard.components import currency_selector
from quantiva.dashboard import pages
st.session_state['quantiva_theme']='light'
currency_selector()
page=st.selectbox('Page',['overview','sales','customers'])
settings=SimpleNamespace(database_file=Path({str(analytical_database)!r}))
getattr(pages,page)(settings,Path('.'))
"""
    app = AppTest.from_string(source).run(timeout=30)
    assert not app.exception and app.radio[0].value == "ZAR"
    assert app.metric[0].value == "R 266.87"
    app.radio[0].set_value("GBP").run()
    assert not app.exception and app.metric[0].value == "£21.00"
    app.selectbox[0].set_value("sales").run()
    assert not app.exception and app.metric[0].value == "£21.00"
    app.radio[0].set_value("ZAR").run()
    assert not app.exception and app.metric[0].value == "R 266.87"
    app.selectbox[0].set_value("customers").run()
    assert not app.exception and app.metric[0].value == "1"
    assert app.metric[1].value == "R 139.79"
    assert app.session_state["display_currency"] == "ZAR"
