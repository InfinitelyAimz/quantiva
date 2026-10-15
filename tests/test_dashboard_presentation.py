"""UI labels, semantic colors and plot scales preserve analytical/export values."""

import numpy as np
import pandas as pd
import pytest

from quantiva.dashboard import components
from quantiva.dashboard.currency import Currency, table_values
from quantiva.dashboard.presentation import (
    friendly_frame,
    label,
    log_monetary_available,
    table_html,
)
from quantiva.dashboard.theme import MODEL_COLORS, SEGMENT_COLORS


def test_readable_escaped_tables_and_technical_exports():
    source = pd.DataFrame(
        {
            "model": ["random_forest", "seasonal_naive"],
            "rfm_score": [345, 444],
            "orders": [1000, 2],
            "wape_pct": [24.31, 26.68],
            "mae_gbp": [10.0, 20.0],
            "complete_month": [True, False],
            "description": ['<script>alert("x")</script>', "Safe"],
        }
    )
    original = source.copy(deep=True)
    html = table_html(table_values(source, Currency("ZAR")))
    assert "Random Forest" in html and "Weekly Seasonal Naive" in html
    assert "Complete month" in html and "Partial month" in html
    assert "RFM Score" in html and "MAE (ZAR/day)" in html
    assert "1,000" in html and "1,000.00" not in html and "24.31%" in html
    assert 'scope="col"' in html and 'tabindex="0"' in html and 'class="q-number"' in html
    assert "<script>" not in html and "&lt;script&gt;" in html
    exported = table_values(source, Currency("ZAR"), export=True)
    assert exported.model.tolist() == source.model.tolist()
    assert exported.complete_month.tolist() == [True, False]
    pd.testing.assert_frame_equal(source, original)
    assert label("recency_days") == "Recency (days)"


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_semantic_colors_and_log_axes_keep_original_values(monkeypatch, theme):
    captured = []
    monkeypatch.setattr(
        components.st, "session_state", {"display_currency": "ZAR", "quantiva_theme": theme}
    )
    monkeypatch.setattr(components.st, "plotly_chart", lambda fig, **kw: captured.append(fig))
    monkeypatch.setattr(components.st, "markdown", lambda *args, **kw: None)
    source = pd.DataFrame(
        {
            "segment": ["At Risk", "Champions"],
            "recency_days": [100, 1],
            "monetary_gbp": [10.0, 100000.0],
        }
    )
    components.chart(
        source,
        "recency_days",
        "monetary_gbp",
        "Recorded spend",
        kind="scatter",
        color="segment",
        log_y=True,
        currency=True,
    )
    components.chart(
        source.iloc[::-1],
        "recency_days",
        "monetary_gbp",
        "Recorded spend",
        kind="scatter",
        color="segment",
        log_y=True,
        currency=True,
    )
    for figure in captured:
        assert figure.layout.yaxis.type == "log"
        assert {t.name: t.marker.color for t in figure.data} == {
            name: SEGMENT_COLORS[name] for name in source.segment
        }
        for trace in figure.data:
            expected = source.loc[source.segment.eq(trace.name), "monetary_gbp"] * 12.708021
            np.testing.assert_allclose(trace.y, expected)
    models = pd.DataFrame({"model": ["seasonal_naive", "random_forest"], "mae_gbp": [1.0, 2.0]})
    components.chart(models, "mae_gbp", "model", "Mean absolute error (MAE)", color="model")
    assert {t.name: t.marker.color for t in captured[-1].data} == {
        "Weekly Seasonal Naive": MODEL_COLORS["Weekly Seasonal Naive"],
        "Random Forest": MODEL_COLORS["Random Forest"],
    }
    assert models.model.tolist() == ["seasonal_naive", "random_forest"]
    assert source.monetary_gbp.tolist() == [10, 100000]


@pytest.mark.parametrize(
    "values,available",
    [
        ([0, 1], False),
        ([-1, 1], False),
        ([None, 1], False),
        ([], False),
        ([1, 100000], True),
    ],
)
def test_log_scale_fallback_never_discards_nonpositive_rows(values, available):
    source = pd.Series(values, dtype=float)
    assert log_monetary_available(source) is available
    assert len(source) == len(values)


def test_month_coverage_labels_preserve_source_boolean_policy():
    source = pd.DataFrame({"complete_month": [True, False, True]})
    assert friendly_frame(source).complete_month.tolist() == [
        "Complete month",
        "Partial month",
        "Complete month",
    ]
    assert source.complete_month.tolist() == [True, False, True]
