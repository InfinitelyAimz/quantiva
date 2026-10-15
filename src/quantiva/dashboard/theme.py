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
        "hover": "#1c304d",
        "selected": "#223e61",
    },
    "light": {
        "background": "#f5f7fb",
        "surface": "#ffffff",
        "text": "#12243c",
        "muted": "#50627a",
        "border": "#c5d0e0",
        "accent": "#1861b5",
        "hover": "#edf3fb",
        "selected": "#e1edfc",
    },
}
PALETTE = ["#378ce7", "#eea64c", "#2ba68d", "#9a7cdd", "#df708a", "#708aaf"]
SEGMENT_COLORS = dict(
    zip(
        [
            "Champions",
            "Loyal Customers",
            "Potential Loyalists",
            "New Customers",
            "At Risk",
            "Hibernating",
        ],
        PALETTE,
        strict=True,
    )
)
MODEL_COLORS = dict(
    zip(
        ["Random Forest", "Naive", "Weekly Seasonal Naive", "Linear Regression"],
        PALETTE[:4],
        strict=True,
    )
)
COVERAGE_COLORS = {"Complete month": PALETTE[0], "Partial month": PALETTE[1]}
LAYOUT = {"radius": "12px", "gap": "1.25rem", "focus_width": "3px"}


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
        font={"color": t["text"], "family": "Segoe UI, Arial, sans-serif", "size": 12},
        colorway=PALETTE,
        margin={"l": 12, "r": 20, "t": 20, "b": 85},
        height=340,
        legend={"orientation": "h", "y": -0.25, "x": 0, "title_text": "", "font_size": 12},
        hoverlabel={"bgcolor": t["surface"], "font_color": t["text"]},
    )
    fig.update_xaxes(
        gridcolor=t["border"], title_font_color=t["muted"], automargin=True, zeroline=False
    )
    fig.update_yaxes(
        gridcolor=t["border"], title_font_color=t["muted"], automargin=True, zeroline=False
    )
    return fig


def css(theme: str, active_path: str = "") -> str:
    """Controlled Streamlit 1.66 DOM overrides;
    tables avoid unthemeable canvas grids."""
    if theme not in THEMES:
        raise ValueError("Theme must be dark or light")
    if active_path not in {"", "overview", "sales", "customers", "predictive", "quality"}:
        raise ValueError("Unknown navigation path")
    t = THEMES[theme]
    return f"""<style>
    :root {{ color-scheme: {theme};
     --q-bg: {t["background"]};
     --q-surface: {t["surface"]};

      --q-text: {t["text"]};
     --q-muted: {t["muted"]};
     --q-border: {t["border"]};
     --q-accent: {t["accent"]}; --q-hover: {t["hover"]}; --q-selected: {t["selected"]};
     --q-radius: {LAYOUT["radius"]}; --q-gap: {LAYOUT["gap"]};
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
    [data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] h1 {{
      font-size:clamp(1.8rem, 2.4vw, 2.3rem); letter-spacing:-.025em;}}
    [data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] h3 {{
      font-size:1.25rem; margin-top:1rem;}}
    [data-testid="stMainBlockContainer"] [data-testid="stMarkdownContainer"] h4 {{
      font-size:1.05rem; font-weight:600;}}
    [data-testid="stVerticalBlock"] {{gap:var(--q-gap);}}
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {{gap:.75rem;}}
    [data-testid="stPlotlyChart"] {{background:var(--q-surface); border:1px solid var(--q-border);
      border-radius:var(--q-radius);}}
    a:focus-visible, button:focus-visible, input:focus-visible, [tabindex="0"]:focus-visible {{
      outline:{LAYOUT["focus_width"]} solid var(--q-accent)!important; outline-offset:3px;}}
    [data-testid="stPageLink-NavLink"] {{padding:.65rem .75rem; border-radius:8px;}}
    [data-testid="stPageLink-NavLink"] [data-testid="stIconMaterial"] {{
      color:var(--q-muted)!important;}}
    [data-testid="stPageLink-NavLink"]:hover {{background:var(--q-hover);}}
    [data-testid="stPageLink-NavLink"][href="{active_path}"] {{background:var(--q-selected);
      box-shadow:inset 3px 0 var(--q-accent);}}
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
    [data-testid="stMultiSelect"] [role="group"] {{background:var(--q-surface)!important;
      border-color:var(--q-border)!important; color:var(--q-text)!important;}}
    [data-testid="stMultiSelect"] [role="group"]:focus-within {{
      outline:2px solid var(--q-accent); outline-offset:2px;}}
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
    border-radius:var(--q-radius);
    }}
    [data-testid="stAlert"] p {{color:var(--q-text);
    }}
    [data-testid="stMetric"] {{padding:16px 18px;
     min-height:102px; box-shadow:none;
    }}
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {{color:var(--q-text);
    }}
    [data-testid="stMetric"] {{container-type:inline-size;}}
    [data-testid="stMetricValue"] > div {{
      font-size:clamp(1.25rem, 10cqi, 2rem);
      white-space:normal; overflow-wrap:anywhere;
      overflow:visible; text-overflow:clip; line-height:1.25;
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
    .q-table .q-number {{text-align:right; font-variant-numeric:tabular-nums;}}
    .q-table .q-text {{text-align:left;}}
    .q-table tbody tr:hover {{background:var(--q-hover);}}
    @media(max-width:1100px) {{[data-testid="stMainBlockContainer"] {{padding:1rem;
    }}
      [data-testid="stHorizontalBlock"] {{flex-direction:column;
    }} [data-testid="stColumn"] {{width:100%!important;
    min-width:100%!important;}} h1 {{font-size:26px;
    }}}}
    </style>"""
