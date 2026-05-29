"""
dashboard/components/metrics.py
Global CSS design system, cached data loaders, and KPI renderers.

Design language: Apple-inspired modern clean
  Font      : -apple-system / SF Pro (renders natively on macOS)
  Palette   : #F5F5F7 page bg, #1D1D1F text, #0066CC accent
  Cards     : 12px radius, hairline shadow, no heavy borders
  No emojis anywhere in the UI
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from models.optimizer import NYEnergyOptimizer
from models.scenarios import ScenarioResult
from data.generate_data import generate_price_projections, generate_nyiso_demand


# ── Cached data loaders ────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Initializing optimization model…")
def load_optimizer() -> NYEnergyOptimizer:
    return NYEnergyOptimizer()


@st.cache_data(show_spinner="Solving LP scenarios…")
def get_scenario_results() -> list[ScenarioResult]:
    opt = load_optimizer()
    return opt.run_all_scenarios()


@st.cache_data(show_spinner="Running sensitivity grid…")
def run_sensitivity(
    scenario_name: str,
    solar_min: int, solar_max: int,
    wind_min: int, wind_max: int,
    steps: int,
):
    opt = load_optimizer()
    solar_range = list(np.linspace(solar_min, solar_max, steps, dtype=int))
    wind_range  = list(np.linspace(wind_min,  wind_max,  steps, dtype=int))
    return opt.run_sensitivity(scenario_name, solar_range, wind_range)


@st.cache_data
def get_demand_data():
    return generate_nyiso_demand()


@st.cache_data
def get_price_projections():
    return generate_price_projections()


# ── Apple-inspired font stack ─────────────────────────────────────────────────
# On macOS this renders SF Pro Display/Text natively.
# On Windows: Segoe UI. On Linux: Ubuntu/Noto Sans.
_APPLE_FONT = (
    "-apple-system, BlinkMacSystemFont, 'SF Pro Display', "
    "'Helvetica Neue', Helvetica, Arial, sans-serif"
)

# ── Global CSS ─────────────────────────────────────────────────────────────────

DASHBOARD_CSS = f"""
<style>

/* ── Font across entire application ──────────────────────────── */
html, body, * {{
    font-family: {_APPLE_FONT} !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}}

/* ── Page background (Apple #F5F5F7) ────────────────────────── */
.stApp,
section.main,
section.main > div.block-container {{
    background-color: #F5F5F7 !important;
}}
section.main > div.block-container {{
    padding-top: 2.25rem !important;
    padding-bottom: 3rem !important;
    max-width: 1280px;
}}

/* ── Headings ────────────────────────────────────────────────── */
h1 {{
    font-size: 2.4rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    color: #1D1D1F !important;
    line-height: 1.1 !important;
    margin-bottom: 0.5rem !important;
    border: none !important;
    padding: 0 !important;
}}
h2 {{
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.01em !important;
    color: #1D1D1F !important;
    border: none !important;
    padding: 0 !important;
    margin-top: 1.6rem !important;
    margin-bottom: 0.6rem !important;
    text-transform: none !important;
}}
h3 {{
    font-size: 1.05rem !important;
    font-weight: 600 !important;
    color: #1D1D1F !important;
}}

/* Body text */
p, li, td, th, div.stMarkdown p {{
    font-size: 1.0625rem !important;   /* 17px — Apple's body size */
    color: #1D1D1F !important;
    line-height: 1.6 !important;
}}

/* ── Sidebar shell ───────────────────────────────────────────── */
[data-testid="stSidebar"] {{
    background-color: #1D1D1F !important;
    border-right: none !important;
}}
[data-testid="stSidebar"] > div:first-child {{
    padding-top: 0 !important;
}}

/* ── Brand header injected via CSS — appears above nav links ─── *
 * st.navigation() forces nav to the top of the sidebar DOM, so   *
 * we use ::before on the sidebar's inner wrapper div to prepend  *
 * the brand above nav. stSidebarHeader (which shows "keyboard"   *
 * broken Material icon text) is hidden entirely.                 *
 * ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebarHeader"] {{
    display: none !important;
}}
[data-testid="stSidebar"] > div:first-child::before {{
    content: "Energy Pathway Analyzer";
    display: block;
    font-family: {_APPLE_FONT};
    font-size: 1.08rem;
    font-weight: 700;
    color: #F5F5F7;
    letter-spacing: -0.01em;
    line-height: 1.3;
    padding: 18px 18px 14px 16px;
    border-bottom: 0.5px solid #2C2C2E;
    border-left: 3px solid #4A7FB5;
    white-space: normal;
    overflow-wrap: break-word;
}}
/* Clear ::after — no absolute-positioned eyebrow */
[data-testid="stSidebar"] > div:first-child::after {{
    content: none !important;
    display: none !important;
}}

/* ── Sidebar expand button (collapsed → open) ───────────────── */
[data-testid="stSidebarCollapsedControl"] {{
    background: #1D1D1F !important;
    border-right: 0.5px solid #2C2C2E !important;
}}
[data-testid="stSidebarCollapsedControl"] button {{
    background: transparent !important;
    border: none !important;
    color: #48484A !important;
    width: 32px !important;
    height: 52px !important;
    border-radius: 0 8px 8px 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.15s ease !important;
    font-size: 1.1rem !important;
}}
[data-testid="stSidebarCollapsedControl"] button:hover {{
    color: #6FA8DC !important;
    background: rgba(111,168,220,0.08) !important;
}}
[data-testid="stSidebarCollapsedControl"] button svg {{
    display: none !important;
}}
[data-testid="stSidebarCollapsedControl"] button::after {{
    content: "›" !important;
    font-size: 1.3rem !important;
    font-weight: 300 !important;
    line-height: 1 !important;
}}

/* ── Sidebar text ────────────────────────────────────────────── */
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] small,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] li {{
    color: #636366 !important;
    font-size: 0.875rem !important;
    line-height: 1.6 !important;
}}
[data-testid="stSidebar"] strong,
[data-testid="stSidebar"] b {{
    color: #EBEBF0 !important;
}}
[data-testid="stSidebar"] hr,
hr.sidebar-divider {{
    border-color: #2C2C2E !important;
    border-top-width: 0.5px !important;
    margin: 12px 0 8px !important;
}}

/* ── Sidebar nav links ───────────────────────────────────────── */
[data-testid="stSidebar"] [data-testid="stPageLink"] {{
    border-radius: 6px !important;
    margin: 1px 10px 1px 0 !important;
    padding: 2px 8px !important;
    border-left: 3px solid transparent !important;
    transition: background 0.12s ease !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"]:hover {{
    background: rgba(255,255,255,0.05) !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"] span,
[data-testid="stSidebar"] [data-testid="stPageLink"] p {{
    color: #8E8E93 !important;
    font-size: 0.9rem !important;
    font-weight: 400 !important;
    letter-spacing: 0 !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] {{
    background: rgba(74,127,181,0.12) !important;
    border-left: 3px solid #4A7FB5 !important;
}}
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] span,
[data-testid="stSidebar"] [data-testid="stPageLink"][aria-current="page"] p {{
    color: #90B8D8 !important;
    font-weight: 500 !important;
}}

/* ── st.metric cards ─────────────────────────────────────────── */
[data-testid="stMetric"] {{
    background: #FFFFFF !important;
    border-radius: 12px !important;
    border: none !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 0 0 0.5px rgba(0,0,0,0.06) !important;
    padding: 20px 22px 18px !important;
}}
[data-testid="stMetricLabel"] p {{
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #86868B !important;
}}
[data-testid="stMetricValue"] {{
    font-size: 2rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #1D1D1F !important;
}}
[data-testid="stMetricDelta"] {{
    font-size: 0.8125rem !important;
    color: #6E6E73 !important;
}}

/* ── DataFrames ──────────────────────────────────────────────── */
[data-testid="stDataFrame"] {{
    border-radius: 12px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 0 0 0.5px rgba(0,0,0,0.06) !important;
    border: none !important;
}}
[data-testid="stDataFrame"] th {{
    background: #F5F5F7 !important;
    color: #86868B !important;
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
    border-bottom: 1px solid #D2D2D7 !important;
}}
[data-testid="stDataFrame"] td {{
    font-size: 0.875rem !important;
    color: #1D1D1F !important;
}}

/* ── Selectbox / slider labels ───────────────────────────────── */
[data-testid="stSelectbox"] label p,
[data-testid="stSlider"] label p {{
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    color: #86868B !important;
}}

/* ── Expander ────────────────────────────────────────────────── */
[data-testid="stExpander"] {{
    background: #FFFFFF !important;
    border: none !important;
    border-radius: 12px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06), 0 0 0 0.5px rgba(0,0,0,0.06) !important;
    overflow: hidden !important;
}}
[data-testid="stExpander"] summary p {{
    font-size: 0.9375rem !important;
    font-weight: 600 !important;
    color: #1D1D1F !important;
}}

/* ── Divider ─────────────────────────────────────────────────── */
hr {{
    border-color: #D2D2D7 !important;
    border-top-width: 0.5px !important;
    margin: 1.25rem 0 !important;
}}

/* ── Streamlit alerts ────────────────────────────────────────── */
[data-testid="stAlert"] {{
    border-radius: 12px !important;
    border-left-width: 0 !important;
    font-size: 0.9375rem !important;
}}

/* ── Remove Streamlit top padding gaps ───────────────────────── */
.element-container {{ margin-bottom: 0.2rem !important; }}
div[data-testid="column"] > div > div > div > div.element-container {{
    margin-bottom: 0 !important;
}}

/* ── Sidebar custom components ───────────────────────────────────
   Prefix with [data-testid="stSidebar"] p.class to beat the
   general sidebar p rule in specificity (both have !important;
   same element+attribute+class specificity → last defined wins).
───────────────────────────────────────────────────────────────── */
/* sidebar-eyebrow / sidebar-title / sidebar-sub removed —
   brand header is now injected via CSS ::before pseudo-element
   on [data-testid="stSidebar"] > div:first-child               */
[data-testid="stSidebar"] p.sidebar-section-label {{
    font-size: 0.63rem !important;
    font-weight: 700 !important;
    letter-spacing: .16em !important;
    text-transform: uppercase !important;
    color: #48484A !important;
    margin: 16px 0 4px !important;
    padding: 0 !important;
    line-height: 1.2 !important;
}}
[data-testid="stSidebar"] p.sidebar-meta {{
    font-size: 0.8125rem !important;
    color: #636366 !important;
    line-height: 1.9 !important;
    margin: 0 !important;
    padding: 0 !important;
}}
[data-testid="stSidebar"] p.sidebar-footer {{
    font-size: 0.775rem !important;
    color: #3A3A3C !important;
    line-height: 1.8 !important;
    margin: 16px 0 0 !important;
    padding: 12px 0 0 !important;
    border-top: 0.5px solid #2C2C2E !important;
}}

</style>
"""


def apply_css() -> None:
    """Inject Apple-inspired CSS. Call once at the top of app.py — it persists across all pages."""
    st.markdown(DASHBOARD_CSS, unsafe_allow_html=True)


# ── KPI card ───────────────────────────────────────────────────────────────────

def kpi_card(label: str, value: str, sub: str = "", color: str = "#0066CC") -> None:
    """
    Apple-style KPI card: white, 12px radius, hairline shadow.
    A thin color bar at the top is the only accent — no left-border, no heavy frame.
    """
    sub_html = (
        f"<div style='"
        f"font-family:{_APPLE_FONT};"
        f"font-size:0.8125rem;"
        f"color:#6E6E73;"
        f"margin-top:10px;"
        f"padding-top:10px;"
        f"border-top:0.5px solid #E5E5EA'>{sub}</div>"
        if sub else ""
    )
    st.markdown(f"""
    <div style="
        background:#FFFFFF;
        border-radius:12px;
        box-shadow:0 1px 4px rgba(0,0,0,0.07),0 0 0 0.5px rgba(0,0,0,0.05);
        padding:20px 22px 16px;
        border-top:3px solid {color};
        margin-bottom:4px;
    ">
        <div style="
            font-family:{_APPLE_FONT};
            font-size:0.6875rem;
            font-weight:600;
            color:#86868B;
            text-transform:uppercase;
            letter-spacing:.08em;
            margin-bottom:7px">{label}</div>
        <div style="
            font-family:{_APPLE_FONT};
            font-size:2rem;
            font-weight:700;
            letter-spacing:-0.025em;
            color:#1D1D1F;
            line-height:1.05">{value}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def insight_box(text: str, color: str = "#0066CC") -> None:
    """
    Apple-style informational callout.
    Rounded card, tinted background — no left-rule, no emoji prefix.
    """
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    st.markdown(f"""
    <div style="
        background:rgba({r},{g},{b},0.07);
        border-radius:12px;
        border:0.5px solid rgba({r},{g},{b},0.2);
        padding:16px 20px;
        margin:16px 0 8px;
        font-family:{_APPLE_FONT};
        font-size:0.9375rem;
        color:#1D1D1F;
        line-height:1.55;
    ">
        {text}
    </div>
    """, unsafe_allow_html=True)


def label_tag(text: str) -> None:
    """Small uppercase label tag — used as a section intro label (Apple 'eyebrow' text)."""
    st.markdown(f"""
    <div style="
        font-family:{_APPLE_FONT};
        font-size:0.6875rem;
        font-weight:600;
        letter-spacing:.08em;
        text-transform:uppercase;
        color:#86868B;
        margin-bottom:4px;
    ">{text}</div>
    """, unsafe_allow_html=True)
