"""
dashboard/pages/1_Overview.py
Scenario Overview — hero section, KPI cards, comparison charts, summary table.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from config import SCENARIO_COLORS, NY_BASELINE_CO2_MT, SCENARIOS
from dashboard.components.metrics import (
    get_scenario_results, load_optimizer, kpi_card, insight_box,
)
from dashboard.components.charts import cost_comparison_bar, co2_bar

# ── Data ──────────────────────────────────────────────────────────────────────
results = get_scenario_results()
colors = [SCENARIO_COLORS[s] for s in SCENARIOS]

# ── Hero ──────────────────────────────────────────────────────────────────────
st.title("NY State Least-Cost Renewable Energy Pathway Analyzer")
st.markdown(
    "A linear programming optimization model finding the **minimum-cost electricity "
    "generation mix** for New York State under three CLCPA policy scenarios. "
    "Integrates NYISO 2023 hourly demand and NREL Annual Technology Baseline costs "
    "across 7 technologies, subject to reliability and renewable portfolio constraints."
)
st.divider()

# ── KPI Cards ─────────────────────────────────────────────────────────────────
kpi_cols = st.columns(3)
for col, r, color in zip(kpi_cols, results, colors):
    with col:
        kpi_card(
            label=r.scenario_name,
            value=f"${r.total_cost_b_yr:.2f}B / yr",
            sub=(
                f"LCOE: <b>${r.lcoe_system:.0f}/MWh</b> &nbsp;·&nbsp; "
                f"Renewable: <b>{r.renewable_fraction:.0%}</b> &nbsp;·&nbsp; "
                f"CO₂: <b>{r.co2_mt_yr:.1f} Mt/yr</b>"
            ),
            color=color,
        )

st.divider()

# ── Comparison charts ─────────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    st.subheader("Total System Cost Comparison")
    st.plotly_chart(cost_comparison_bar(results, colors), use_container_width=True)
with col2:
    st.subheader("CO₂ Emissions vs 2019 Baseline")
    st.plotly_chart(co2_bar(results, baseline_mt=NY_BASELINE_CO2_MT), use_container_width=True)

# ── Summary table ─────────────────────────────────────────────────────────────
st.subheader("Scenario Comparison Table")
summary = pd.DataFrame([
    {
        "Scenario": r.scenario_name,
        "Annual Cost ($B/yr)": f"${r.total_cost_b_yr:.2f}",
        "System LCOE ($/MWh)": f"${r.lcoe_system:.0f}",
        "Renewable %": f"{r.renewable_fraction:.0%}",
        "Zero-Carbon %": f"{r.zero_carbon_fraction:.0%}",
        "CO₂ (Mt/yr)": f"{r.co2_mt_yr:.1f}",
        "CO₂ Reduction vs 2019": f"{r.co2_reduction_pct:.0%}",
        "Solver Status": "Optimal",
    }
    for r in results
])
st.dataframe(summary, use_container_width=True, hide_index=True)

# ── Key insight ───────────────────────────────────────────────────────────────
insight_box(
    "<b>Counterintuitive result:</b> The 100% Zero-Carbon scenario ($11.0B/yr) costs "
    "only 13% more than the 50% RPS case — and is 44% <em>cheaper</em> than 80% RPS. "
    "When gas is eliminated entirely, the optimizer avoids the 26 GW offshore wind "
    "overbuild driving 80% RPS costs. Instead, existing nuclear (3 GW, low marginal cost) "
    "anchors baseload, and solar + battery storage fill the gap more cheaply than "
    "additional offshore wind capacity."
)
