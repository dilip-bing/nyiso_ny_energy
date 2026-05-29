"""
dashboard/app.py
Entry point — injects global CSS and wires up the six analysis pages.

Run:
    streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from dashboard.components.metrics import apply_css

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NY Renewable Pathway Analyzer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_css()

# ── Navigation ────────────────────────────────────────────────────────────────
# NOTE: st.navigation() always renders at the TOP of the sidebar.
# The brand header is injected via CSS ::before — see DASHBOARD_CSS.
pg = st.navigation([
    st.Page("pages/1_Overview.py",       title="Scenario Overview"),
    st.Page("pages/2_Capacity_Mix.py",   title="Capacity & Generation Mix"),
    st.Page("pages/3_Cost_Analysis.py",  title="Cost Analysis"),
    st.Page("pages/4_Sensitivity.py",    title="Sensitivity Analysis"),
    st.Page("pages/5_Demand_Profile.py", title="Demand Profile"),
    st.Page("pages/6_Methodology.py",    title="Methodology"),
])

# ── Sidebar footer (appears below nav links — Streamlit behavior) ─────────────
with st.sidebar:
    st.markdown("<hr class='sidebar-divider'>", unsafe_allow_html=True)
    st.markdown("<p class='sidebar-section-label'>Model</p>", unsafe_allow_html=True)
    st.markdown(
        "<p class='sidebar-meta'>"
        "Linear programming · PuLP / CBC<br>"
        "7% WACC &nbsp;·&nbsp; CBC solver<br>"
        "7 technologies · 3 scenarios<br>"
        "8,760-hour demand profile"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown("<p class='sidebar-section-label'>Data Sources</p>", unsafe_allow_html=True)
    st.markdown(
        "<p class='sidebar-meta'>"
        "NYISO 2023 Gold Book<br>"
        "NREL ATB 2023 Moderate<br>"
        "CLCPA 2019 targets<br>"
        "NYISO Reliability Plan 2022"
        "</p>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p class='sidebar-footer'>"
        "Dilip &nbsp;·&nbsp; "
        "<a href='https://github.com/dilip-bing' style='color:#6FA8DC;text-decoration:none'>"
        "github.com/dilip-bing</a><br>"
        "MS CS (AI Track) · Binghamton University"
        "</p>",
        unsafe_allow_html=True,
    )

pg.run()
