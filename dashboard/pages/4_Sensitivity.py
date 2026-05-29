"""
dashboard/pages/4_Sensitivity.py
Sensitivity Analysis — heatmaps of total cost and LCOE vs solar × wind capital costs,
plus capacity response line charts and sliders for interactive exploration.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config import SCENARIOS, TECH_COLORS
from dashboard.components.metrics import run_sensitivity, insight_box
from dashboard.components.charts import (
    sensitivity_heatmap, capacity_response_line,
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Sensitivity Analysis — Solar & Wind Capital Cost Uncertainty")
st.markdown(
    "How does total system cost and LCOE change as solar and wind capital costs decline "
    "along NREL ATB learning curves? This grid search jointly varies both, modeling "
    "technology cost trajectories from 2023 through the CLCPA 2030–2040 horizon."
)

# ── Controls ──────────────────────────────────────────────────────────────────
ctrl1, ctrl2, ctrl3 = st.columns(3)
with ctrl1:
    sens_scenario = st.selectbox("Scenario", list(SCENARIOS), index=1)
with ctrl2:
    solar_range = st.slider(
        "Solar capital cost range ($/kW)", 400, 1300, (500, 1150), step=50
    )
with ctrl3:
    wind_range = st.slider(
        "Onshore wind capital cost range ($/kW)", 700, 1800, (800, 1500), step=50
    )

steps = st.slider("Grid resolution (steps per axis)", 4, 10, 6, help="Higher = more detail, slower")

# ── Run sensitivity ────────────────────────────────────────────────────────────
sens_df = run_sensitivity(
    sens_scenario,
    solar_range[0], solar_range[1],
    wind_range[0], wind_range[1],
    steps,
)

# ── Heatmaps ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Total System Cost ($B/yr)")
    st.plotly_chart(
        sensitivity_heatmap(sens_df, "total_cost_b_yr", "$B/yr", ".1f"),
        use_container_width=True,
    )

with col2:
    st.subheader("System LCOE ($/MWh)")
    st.plotly_chart(
        sensitivity_heatmap(sens_df, "lcoe_system", "$/MWh", ".0f"),
        use_container_width=True,
    )

# ── Capacity response curves ───────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Optimal Solar Capacity vs Solar Price")
    st.plotly_chart(
        capacity_response_line(
            sens_df,
            x_col="solar_capital_per_kw",
            y_col="solar_gw",
            x_label="Solar Capital Cost ($/kW)",
            y_label="Optimal Solar Capacity (GW)",
            color=TECH_COLORS["Solar PV (Utility)"],
        ),
        use_container_width=True,
    )

with col2:
    st.subheader("Optimal Wind Capacity vs Wind Price")
    st.plotly_chart(
        capacity_response_line(
            sens_df,
            x_col="wind_capital_per_kw",
            y_col="wind_gw",
            x_label="Onshore Wind Capital Cost ($/kW)",
            y_label="Optimal Wind Capacity (GW)",
            color=TECH_COLORS["Onshore Wind"],
        ),
        use_container_width=True,
    )

# ── Insight ───────────────────────────────────────────────────────────────────
insight_box(
    "<b>Interpretation:</b> Total system cost drops by approximately "
    "<b>15%</b> if solar capital falls from $1,150 to $600/kW — consistent with "
    "NREL's Advanced scenario by 2035. Wind cost declines have a smaller "
    "but compounding effect when combined with solar reductions."
)

# ── Raw data ──────────────────────────────────────────────────────────────────
with st.expander("Raw sensitivity data table"):
    st.dataframe(
        sens_df.round(3).sort_values(["solar_capital_per_kw", "wind_capital_per_kw"]),
        use_container_width=True,
        hide_index=True,
    )
