"""Run with streamlit run app/Home.py from the repository root."""

from pathlib import Path

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from quantiva.config import Settings
from quantiva.dashboard import pages
from quantiva.dashboard.data import catalog
from quantiva.dashboard.theme import css, theme_state

st.set_page_config(page_title="Quantiva | Retail intelligence", page_icon="◈", layout="wide")
settings = Settings.from_environment()
root = Path(__file__).resolve().parents[1]
initial = st.context.theme.type
theme = theme_state(st.session_state, initial)


def guarded(renderer):
    """Keep navigation available even if a page's artifacts are missing or corrupt."""

    def render():
        try:
            renderer(settings, root)
        except (OSError, ValueError, KeyError, TypeError, SQLAlchemyError) as exc:
            st.warning(f"This view needs valid local artifacts: {exc}")
            st.info(
                "From the checkout: quantiva download → quantiva prepare → "
                "quantiva database → quantiva analyze → quantiva forecast-train. "
                "See README for exact commands."
            )

    render.__name__ = renderer.__name__
    return render


page_list = [
    st.Page(guarded(pages.overview), title="Overview", icon=":material/dashboard:", default=True),
    st.Page(guarded(pages.sales), title="Sales Analytics", icon=":material/monitoring:"),
    st.Page(guarded(pages.customers), title="Customer Intelligence", icon=":material/groups:"),
    st.Page(guarded(pages.predictive), title="Predictive Analytics", icon=":material/query_stats:"),
    st.Page(guarded(pages.quality), title="Data Quality", icon=":material/verified_user:"),
]
navigation = st.navigation(page_list, position="hidden")

with st.sidebar:
    st.html('<div class="q-brand"><b>Q</b>UANTIVA</div>')
    st.caption("RETAIL INTELLIGENCE / 2010–2011")
    for page in page_list:
        st.page_link(page)
    st.divider()
    chosen = st.radio(
        "Appearance",
        ["light", "dark"],
        index=["light", "dark"].index(theme),
        horizontal=True,
        format_func=str.title,
        key="appearance",
    )
    st.session_state["quantiva_theme"] = chosen
    st.divider()
st.html(css(chosen))

with st.sidebar:
    st.divider()
    st.caption("SOURCE / UCI Online Retail")
    try:
        coverage = catalog(settings.database_file)
        st.caption(f"Recorded coverage\n\n{coverage['start']} — {coverage['end']}")
        st.caption("SQLite available · December 2011 partial")
    except (OSError, ValueError, SQLAlchemyError):
        st.caption("SQLite not available · setup required")
    st.caption("Local application · gross sales · GBP")
navigation.run()
