"""Shared headings, scope controls, accessible tables and chart rendering."""

import pandas as pd
import plotly.express as px
import streamlit as st

from quantiva.dashboard.currency import (
    currency_state,
    display_values,
    monetary_columns,
    table_values,
)
from quantiva.dashboard.data import Filters, catalog
from quantiva.dashboard.theme import PALETTE, chart_theme


def heading(title: str, description: str) -> None:
    st.html('<div class="q-eyebrow">QUANTIVA / RETAIL INTELLIGENCE</div>')
    st.title(title)
    st.caption(description)
    st.caption(currency_state(st.session_state).notice)


def currency_selector() -> None:
    """Shared application-shell widget; its selection survives all page navigation."""
    selected = currency_state(st.session_state)
    code = st.radio(
        "Display currency",
        ["ZAR", "GBP"],
        index=["ZAR", "GBP"].index(selected.code),
        horizontal=True,
        key="display_currency_choice",
    )
    st.session_state["display_currency"] = code
    st.caption("Source currency: GBP · ZAR is illustrative")


def table(frame: pd.DataFrame, limit: int = 50) -> None:
    """Escape source values; bounded HTML tables honor session colors on both themes."""
    if frame.empty:
        st.info("No records match this selection.")
        return
    currency = currency_state(st.session_state)
    display = table_values(frame, currency).head(limit)
    display.columns = [
        str(c)
        .replace("_", " ")
        .title()
        .replace("Gbp", "GBP")
        .replace("Zar", "ZAR")
        .replace("Rfm", "RFM")
        .replace(" Id", " ID")
        for c in display.columns
    ]
    st.html(
        '<div class="q-table">'
        + display.to_html(
            index=False,
            escape=True,
            float_format=lambda value: f"{value:,.2f}",
            na_rep="Not available",
            border=0,
        )
        + "</div>"
    )
    if len(frame) > limit:
        st.caption(f"Showing {limit:,} of {len(frame):,} rows. Export the table for all rows.")
        st.download_button(
            "Export table as CSV",
            table_values(frame, currency, export=True).to_csv(index=False),
            f"quantiva_table_{currency.code.lower()}.csv",
        )


def chart(
    frame: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    *,
    kind: str = "bar",
    color: str | None = None,
    currency: bool = False,
    **kwargs,
) -> None:
    if frame.empty:
        st.info("No chart observations in this scope.")
        return
    factory = {"bar": px.bar, "line": px.line, "scatter": px.scatter, "histogram": px.histogram}[
        kind
    ]
    unit = currency_state(st.session_state)
    shown = display_values(frame, unit)
    if "series" in shown:
        shown["series"] = shown["series"].str.replace("_gbp", "_" + unit.code.lower(), regex=False)
    labels = {c: unit.label(str(c).replace("_", " ").title()) for c in frame.columns}
    labels.update({c: unit.label(v) for c, v in kwargs.pop("labels", {}).items()})
    kwargs["labels"] = labels
    hover = kwargs.pop("hover_data", [])
    kwargs["hover_data"] = {**dict.fromkeys(hover), **{c: ":,.2f" for c in monetary_columns(frame)}}
    fig = factory(
        shown, x=x, y=y, title=title, color=color, color_discrete_sequence=PALETTE, **kwargs
    )
    chart_theme(fig, st.session_state["quantiva_theme"])
    st.markdown(f"**{title}**")
    fig.update_layout(title_text="", margin={"l": 12, "r": 12, "t": 15, "b": 25})
    if x.endswith("gbp"):
        fig.update_xaxes(tickprefix=unit.symbol, separatethousands=True)
    if currency:
        fig.update_yaxes(tickprefix=unit.symbol, separatethousands=True)
    st.plotly_chart(fig, width="stretch", theme=None, config={"displaylogo": False})


def filters(path, *, product: bool = False) -> Filters:
    """Shared shell widgets retain scope across Overview/Sales/Customer navigation."""
    info = catalog(path)
    state = st.session_state
    saved = state.get("scope_dates", (info["start"], info["end"]))
    if len(saved) != 2 or saved[0] < info["start"] or saved[1] > info["end"]:
        saved = (info["start"], info["end"])
    state.setdefault("scope_countries", [])
    state["scope_countries"] = [x for x in state["scope_countries"] if x in info["countries"]]
    state.setdefault("scope_products", [])
    options = info["products"].set_index("stock_code")["display_description"].to_dict()
    state["scope_products"] = [x for x in state["scope_products"] if x in options]
    a, b, c = st.columns([2, 2, 2])
    dates = a.date_input(
        "Observation dates",
        value=saved,
        min_value=info["start"],
        max_value=info["end"],
        key="scope_dates_widget",
    )
    country = b.multiselect(
        "Countries · empty means all",
        info["countries"],
        default=state["scope_countries"],
        key="scope_countries_widget",
    )
    products = (
        c.multiselect(
            "Products · stock code",
            list(options),
            default=state["scope_products"],
            key="scope_products_widget",
            format_func=lambda code: f"{code} · {options[code] or 'Unnamed'}",
        )
        if product
        else []
    )
    if len(dates) != 2:
        st.info("Choose both a start and an end date.")
        st.stop()
    state["scope_dates"], state["scope_countries"] = dates, country
    if product:
        state["scope_products"] = products
    else:
        # A hidden product filter is never applied to a page that does not show it.
        products = []
    st.caption(
        "All displayed sales/customer metrics use these dates and countries. "
        + (
            (
                "Product selection restricts eligible lines and counts affected "
                "invoices; AOV is not full-basket value. "
            )
            if product
            else ""
        )
        + "Gross completed sales include eligible charges; cancellations are separate."
    )
    return Filters(dates[0], dates[1], tuple(country), tuple(products))


def kpi_cards(kpis: dict, names: dict[str, tuple[str, str]]) -> None:
    for start in range(0, len(names), 3):
        for column, (key, (label, unit)) in zip(
            st.columns(3), list(names.items())[start : start + 3], strict=False
        ):
            value = kpis.get(key)
            missing = value is None or pd.isna(value)
            formatted = (
                "—"
                if missing
                else (
                    currency_state(st.session_state).money(value)
                    if unit == "gbp"
                    else f"{value:.2%}"
                    if unit == "pct"
                    else f"{value:,.0f}"
                )
            )
            column.metric(label, formatted)
