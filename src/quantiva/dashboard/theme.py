"""Central dashboard tokens;
session-local styling without global config mutation."""

from collections.abc import MutableMapping

import plotly.graph_objects as go

THEMES = {
    "dark": {
        "background": "#0b1424",
        "surface": "#142239",
        "text": "#edf3fc",
        "muted": "#a6b7d0",
        "border": "#31455f",
        "accent": "#65aaff",
    },
    "light": {
        "background": "#f5f7fb",
        "surface": "#ffffff",
        "text": "#12243c",
        "muted": "#50627a",
        "border": "#c5d0e0",
        "accent": "#1861b5",
    },
}
PALETTE = ["#378ce7", "#eea64c", "#2ba68d", "#9a7cdd", "#df708a", "#708aaf"]


def theme_state(state: MutableMapping, initial: str = "light") -> str:
    """Keep the chosen theme independent of page widget cleanup;
    reset invalid values."""
    if state.get("quantiva_theme") not in THEMES:
        state["quantiva_theme"] = initial if initial in THEMES else "light"
    return state["quantiva_theme"]


def chart_theme(fig: go.Figure, theme: str) -> go.Figure:
    """Apply explicit colors to chart canvas, axes, legend and hover labels."""
    if theme not in THEMES:
        raise ValueError("Theme must be dark or light")
    t = THEMES[theme]
    fig.update_layout(
        template="plotly_dark" if theme == "dark" else "plotly_white",
        paper_bgcolor=t["surface"],
        plot_bgcolor=t["surface"],
        font={"color": t["text"], "family": "Arial, sans-serif"},
        colorway=PALETTE,
        margin={"l": 12, "r": 12, "t": 55, "b": 25},
        height=340,
        legend={"orientation": "h", "y": -0.2},
        hoverlabel={"bgcolor": t["surface"], "font_color": t["text"]},
    )
    fig.update_xaxes(gridcolor=t["border"], title_font_color=t["muted"])
    fig.update_yaxes(gridcolor=t["border"], title_font_color=t["muted"])
    return fig


def css(theme: str) -> str:
    """Controlled Streamlit 1.66 DOM overrides;
    tables avoid unthemeable canvas grids."""
    if theme not in THEMES:
        raise ValueError("Theme must be dark or light")
    t = THEMES[theme]
    return f"""<style>
    :root {{ color-scheme: {theme};
     --q-bg: {t["background"]};
     --q-surface: {t["surface"]};

      --q-text: {t["text"]};
     --q-muted: {t["muted"]};
     --q-border: {t["border"]};
     }}
    .stApp, [data-testid="stHeader"] {{background:var(--q-bg);
     color:var(--q-text);
    }}
    [data-testid="stSidebar"] {{background:var(--q-surface);
     color:var(--q-text);
    }}
    [data-testid="stMainBlockContainer"] {{padding-top:2rem;
     max-width:1550px;
    }}
    h1,h2,h3,p,label,strong,small,li, [data-testid="stMarkdownContainer"],
    [data-testid="stWidgetLabel"]
      {{color:var(--q-text);
    }}
    th, abbr, [role="columnheader"] {{color:var(--q-text)!important;}}
    button[aria-label="Collapse sidebar"], button[aria-label="Expand sidebar"],
    button[aria-label="Collapse sidebar"] span, button[aria-label="Expand sidebar"] span
      {{color:var(--q-text)!important; opacity:1!important; visibility:visible!important;}}
    [data-testid="stCaptionContainer"] {{color:var(--q-muted);
    }}
    [data-testid="stDateInputField"], [data-testid="stDateInputFieldsScroller"]
      {{background:var(--q-surface)!important; color:var(--q-text)!important;}}
    [data-testid="stDateInput"] span, [data-testid="stDateInput"] [role="group"],
    [data-testid="stDateInput"] button {{color:var(--q-text)!important;}}
    input::placeholder {{color:var(--q-muted)!important; opacity:1;}}
    [data-testid="stSidebarNav"] a {{color:var(--q-text);
    }}
    [data-testid="stSidebarNav"] a[aria-current="page"] {{background:var(--q-border);
    }}
    button, input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"],
    [data-baseweb="popover"], [role="listbox"], [role="option"], [role="dialog"]
      {{background:var(--q-surface)!important;
    color:var(--q-text)!important;
    border-color:var(--q-border)!important;
    }}
    [data-baseweb="select"] span, [data-baseweb="select"] div, [data-baseweb="tag"],
    [data-baseweb="calendar"] {{color:var(--q-text)!important;
    }}
    [data-testid="stMetric"], [data-testid="stAlert"], [data-testid="stExpander"]
      {{background:var(--q-surface);
    border:1px solid var(--q-border);
    border-radius:12px;
    }}
    [data-testid="stAlert"] p {{color:var(--q-text);
    }}
    [data-testid="stMetric"] {{padding:16px 18px;
     box-shadow:0 4px 15px #00000008;
    }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{color:var(--q-text);
    }}
    .q-brand {{font-size:25px;
    font-weight:800;
    letter-spacing:3px;
    }}
    .q-brand b {{color:{t["accent"]};
    }} .q-eyebrow {{color:{t["accent"]};
    font-size:12px;
    letter-spacing:2px;
    }}
    .q-table {{overflow:auto;
    border:1px solid var(--q-border);
    border-radius:10px;
    max-height:420px;
    }}
    .q-table table {{width:100%;
    border-collapse:collapse;
    background:var(--q-surface);
    color:var(--q-text);
    font-size:13px;
    }}
    .q-table th {{position:sticky;
    top:0;
    background:var(--q-surface);
    text-align:left;
    }}
    .q-table th,.q-table td {{padding:10px 12px;
    border-bottom:1px solid var(--q-border);
    white-space:nowrap;
    }}
    @media(max-width:1100px) {{[data-testid="stMainBlockContainer"] {{padding:1rem;
    }}
      [data-testid="stHorizontalBlock"] {{flex-direction:column;
    }} [data-testid="stColumn"] {{width:100%!important;
    min-width:100%!important;}} h1 {{font-size:26px;
    }}}}
    </style>"""
