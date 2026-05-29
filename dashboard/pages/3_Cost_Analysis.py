"""
dashboard/pages/3_Cost_Analysis.py
Cost Analysis — per-technology waterfall, LCOE comparison, stacked cost breakdown.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from config import SCENARIO_COLORS, TECH_COLORS, SCENARIOS, US_AVG_RETAIL_PRICE_MWH
from dashboard.components.metrics import get_scenario_results, load_optimizer, kpi_card
from dashboard.components.charts import (
    cost_by_tech_bar, lcoe_comparison_bar, cost_stack_scenarios,
)

# ── Data ──────────────────────────────────────────────────────────────────────
results = get_scenario_results()
opt = load_optimizer()
scenario_map = {r.scenario_name: r for r in results}
colors = [SCENARIO_COLORS[s] for s in SCENARIOS]

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Cost Breakdown Analysis")

# ── Per-scenario detail ────────────────────────────────────────────────────────
selected = st.selectbox("Select scenario", SCENARIOS)
r = scenario_map[selected]

col1, col2, col3 = st.columns(3)
col1.metric("Total System Cost", f"${r.total_cost_b_yr:.2f}B/yr")
col2.metric("System LCOE", f"${r.lcoe_system:.0f}/MWh")
col3.metric(
    "vs US Avg Retail",
    f"{'−' if r.lcoe_system < US_AVG_RETAIL_PRICE_MWH else '+'}"
    f"${abs(r.lcoe_system - US_AVG_RETAIL_PRICE_MWH):.0f}/MWh",
)

st.subheader(f"Annualized Cost by Technology — {selected}")
st.plotly_chart(cost_by_tech_bar(r, TECH_COLORS), use_container_width=True)

st.divider()

# ── System LCOE comparison ────────────────────────────────────────────────────
st.subheader("System LCOE — All Scenarios")
col1, col2 = st.columns([2, 1])

with col1:
    st.plotly_chart(
        lcoe_comparison_bar(scenario_map, list(SCENARIOS), colors, US_AVG_RETAIL_PRICE_MWH),
        use_container_width=True,
    )

with col2:
    st.markdown("**Individual Technology LCOEs**")
    atb = opt.atb_df.reset_index()[["technology", "lcoe_per_mwh", "capacity_factor", "type"]]
    atb = atb.sort_values("lcoe_per_mwh").copy()
    atb.columns = ["Technology", "LCOE ($/MWh)", "Cap. Factor", "Type"]
    st.dataframe(atb, hide_index=True, use_container_width=True)

# ── Stacked cost across scenarios ─────────────────────────────────────────────
st.subheader("Total System Cost by Technology — All Scenarios")
st.plotly_chart(
    cost_stack_scenarios(scenario_map, list(SCENARIOS), TECH_COLORS),
    use_container_width=True,
)

# ── Full cost table ───────────────────────────────────────────────────────────
with st.expander("Full cost data table"):
    rows = []
    for s in SCENARIOS:
        rv = scenario_map[s]
        for tech in TECH_COLORS:
            cm = rv.cost_breakdown_m.get(tech, 0)
            gw = rv.capacity_gw.get(tech, 0)
            rows.append({
                "Scenario": s,
                "Technology": tech,
                "Capacity (GW)": round(gw, 2),
                "Annual Cost ($M)": round(cm, 1),
                "Annual Cost ($B)": round(cm / 1e3, 3),
                "Cost Share": f"{cm / (rv.total_cost_b_yr * 1e3) * 100:.1f}%" if rv.total_cost_b_yr > 0 else "—",
            })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
