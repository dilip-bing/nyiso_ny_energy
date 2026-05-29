"""
dashboard/pages/2_Capacity_Mix.py
Capacity & Generation Mix — donut charts, stacked comparisons, per-scenario KPIs.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

from config import SCENARIO_COLORS, TECH_COLORS, SCENARIOS
from dashboard.components.metrics import get_scenario_results, load_optimizer
from dashboard.components.charts import (
    capacity_donut, generation_donut,
    capacity_stack_bar, generation_stack_bar,
)

# ── Data ──────────────────────────────────────────────────────────────────────
results = get_scenario_results()
opt = load_optimizer()
scenario_map = {r.scenario_name: r for r in results}

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Capacity & Generation Mix by Scenario")

# ── Scenario selector ─────────────────────────────────────────────────────────
selected = st.selectbox("Select scenario for detailed view", SCENARIOS, index=0)
r = scenario_map[selected]

# ── KPI row ───────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Installed Capacity", f"{r.total_capacity_gw:.1f} GW")
k2.metric("Annual Generation", f"{r.total_generation_twh:.1f} TWh")
k3.metric("Renewable Share", f"{r.renewable_fraction:.0%}")
k4.metric("System LCOE", f"${r.lcoe_system:.0f}/MWh")

st.divider()

# ── Donut charts ──────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("Installed Capacity Mix (GW)")
    st.plotly_chart(capacity_donut(r, TECH_COLORS), use_container_width=True)
with col2:
    st.subheader("Annual Generation Mix (TWh)")
    st.plotly_chart(generation_donut(r, TECH_COLORS), use_container_width=True)

# ── Cross-scenario comparisons ────────────────────────────────────────────────
st.subheader("Capacity Mix — All Scenarios")
st.plotly_chart(
    capacity_stack_bar(scenario_map, list(SCENARIOS), TECH_COLORS),
    use_container_width=True,
)

st.subheader("Generation Mix — All Scenarios")
st.plotly_chart(
    generation_stack_bar(
        scenario_map, list(SCENARIOS), TECH_COLORS, opt.annual_demand_twh
    ),
    use_container_width=True,
)

# ── Capacity detail table ─────────────────────────────────────────────────────
st.subheader("Technology Detail Table")
import pandas as pd

detail_rows = []
for tech in TECH_COLORS:
    gw = r.capacity_gw.get(tech, 0)
    twh = r.generation_twh.get(tech, 0)
    cost = r.cost_breakdown_m.get(tech, 0)
    cf_actual = twh * 1e3 / (gw * 8760) if gw > 0 else 0
    detail_rows.append({
        "Technology": tech,
        "Capacity (GW)": f"{gw:.2f}",
        "Generation (TWh)": f"{twh:.1f}",
        "Annual Cost ($B)": f"${cost/1e3:.2f}",
        "Utilization": f"{cf_actual:.0%}",
    })
st.dataframe(pd.DataFrame(detail_rows), use_container_width=True, hide_index=True)
