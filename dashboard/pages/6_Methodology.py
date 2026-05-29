"""
dashboard/pages/6_Methodology.py
Methodology documentation — LP formulation in LaTeX, constraint table,
data sources, technology assumptions, and limitations.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from config import CAPACITY_CREDIT
from dashboard.components.metrics import load_optimizer

opt = load_optimizer()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Methodology & Model Documentation")

# ── LP Formulation ────────────────────────────────────────────────────────────
st.header("Optimization Formulation")

st.markdown("""
This tool solves a **static, single-year least-cost capacity expansion** linear program
using [PuLP](https://coin-or.github.io/pulp/) with the open-source **CBC solver**.
The model determines the minimum-cost generation mix for New York State
that satisfies annual energy demand, peak reliability, and renewable portfolio standards.
""")

st.subheader("Decision Variables")
st.markdown("""
| Variable | Description | Units |
|----------|-------------|-------|
| `cap[t]` | Installed capacity for technology *t* | GW |
| `gen[t]` | Annual energy generation for technology *t* | TWh |
""")

st.subheader("Objective Function")
st.markdown("Minimize total annualized system cost (capital + fixed O&M + variable + fuel):")
st.latex(r"""
\min \sum_{t \in T} \left[
  \underbrace{\left( \text{CRF}_t \cdot \text{CAPEX}_t + \text{FOM}_t \right) \cdot \text{cap}_t}_{\text{annualized capital + fixed O\&M}}
  +
  \underbrace{\left( \text{VOM}_t + \text{Fuel}_t \right) \cdot \text{gen}_t}_{\text{variable + fuel cost}}
\right]
""")

st.markdown("""
Where:
- **CRF** = Capital Recovery Factor = $\\frac{r(1+r)^n}{(1+r)^n - 1}$ at WACC $r = 7\\%$, lifetime $n$
- **CAPEX** = overnight capital cost (\\$/kW)
- **FOM** = fixed operations & maintenance (\\$/kW-yr)
- **VOM** = variable O&M (\\$/MWh)
- **Fuel** = fuel cost (\\$/MWh)
""")

st.subheader("Constraints")
st.latex(r"""
\begin{aligned}
&\textbf{Energy balance:} & \sum_t \text{gen}[t] &\geq D_{\text{annual}} \\
&\textbf{Capacity factor link:} & \text{gen}[t] &= \text{cap}[t] \cdot \text{CF}_t \cdot 8{,}760\ \forall t \\
&\textbf{RPS (50\%/80\%):} & \sum_{t \in R} \text{gen}[t] &\geq \text{RPS} \cdot \sum_t \text{gen}[t] \\
&\textbf{ZCE (100\%):} & \text{gen}[t] &= 0\ \forall t \notin Z \\
&\textbf{Peak adequacy:} & \sum_t \delta_t \cdot \text{cap}[t] &\geq D_{\text{peak}} \cdot (1 + r_{\text{reserve}}) \\
&\textbf{Capacity bounds:} & \text{cap}_t^{\min} &\leq \text{cap}[t] \leq \text{cap}_t^{\max}\ \forall t \\
&\textbf{Non-negativity:} & \text{cap}[t],\ \text{gen}[t] &\geq 0
\end{aligned}
""")

st.markdown("""
Where **R** = renewable technology set, **Z** = zero-carbon technology set,
**δ** = capacity credit (derate factor), and $r_\\text{reserve}$ = reserve margin.
""")

# ── Capacity credit table ─────────────────────────────────────────────────────
st.subheader("Capacity Credit (Derate Factors)")
cc_df = pd.DataFrame([
    {"Technology": t, "Capacity Credit": f"{v:.0%}", "Rationale": r}
    for (t, v), r in zip(
        CAPACITY_CREDIT.items(),
        [
            "Coincident peak probability (summer afternoon)",
            "Coastal wind resource at peak hours",
            "Offshore wind higher coincidence with summer peak",
            "Dispatchable; operates at rated capacity when needed",
            "4-hour discharge provides full rated capacity for peak window",
            "Fully dispatchable thermal plant",
            "Regulated baseload; consistently available",
        ]
    )
])
st.dataframe(cc_df, use_container_width=True, hide_index=True)

# ── Data sources ──────────────────────────────────────────────────────────────
st.subheader("Data Sources")
sources = pd.DataFrame([
    {
        "Dataset": "NYISO 2023 Gold Book",
        "Source": "NYISO (nyiso.com/engineering/resource_adequacy)",
        "Used For": "Hourly demand profile calibration (~154 TWh, ~28 GW peak)",
    },
    {
        "Dataset": "NREL Annual Technology Baseline 2023",
        "Source": "NREL (atb.nrel.gov) — Moderate scenario",
        "Used For": "Overnight CAPEX, O&M costs, capacity factors, lifetimes",
    },
    {
        "Dataset": "NY Climate Leadership & Community Protection Act",
        "Source": "NYSERDA / DPS (2019)",
        "Used For": "70% RPS by 2030, 100% ZCE by 2040, technology capacity targets",
    },
    {
        "Dataset": "NYISO Comprehensive Reliability Plan",
        "Source": "NYISO (2022)",
        "Used For": "Reserve margin requirements, capacity credit assumptions",
    },
    {
        "Dataset": "EIA Electric Power Monthly",
        "Source": "US Energy Information Administration (2023)",
        "Used For": "US average retail electricity price benchmark ($76/MWh)",
    },
])
st.dataframe(sources, use_container_width=True, hide_index=True)

# ── Technology assumptions ────────────────────────────────────────────────────
st.subheader("Technology Assumptions (NREL ATB 2023 Moderate)")
atb_display = opt.atb_df.reset_index()[[
    "technology", "capital_cost_per_kw", "fixed_om_per_kw_yr",
    "var_om_per_mwh", "fuel_cost_per_mwh", "capacity_factor",
    "lcoe_per_mwh", "lifetime_yr", "co2_kg_per_mwh",
]].copy()
atb_display.columns = [
    "Technology", "CAPEX ($/kW)", "Fixed O&M ($/kW-yr)",
    "Var O&M ($/MWh)", "Fuel ($/MWh)", "Cap. Factor",
    "LCOE ($/MWh)", "Lifetime (yr)", "CO₂ (kg/MWh)",
]
st.dataframe(atb_display, use_container_width=True, hide_index=True)

# ── Limitations ───────────────────────────────────────────────────────────────
st.subheader("Model Limitations")
st.markdown("""
1. **Static annual model** — does not capture sub-hourly dispatch, seasonal storage cycling,
   or intra-day solar ramping (no unit commitment or economic dispatch).

2. **Copper plate transmission** — no geographic zones, congestion, or transmission capacity
   limits. NY's 11 load zones and interface constraints are not modeled.

3. **No demand growth** — uses 2023 baseline demand. CLCPA electrification (EVs, heat pumps)
   could increase NY peak demand 20–40% by 2040.

4. **Battery modeled on energy basis** — capacity credit is applied at rated power;
   actual 4-hour storage duration and round-trip efficiency losses are simplified.

5. **Single-year planning horizon** — investment timing, construction lead times,
   and multi-year capital deployment are not captured.

6. **No carbon price** — does not include NY RGGI allowance costs (~$15/tonne CO₂),
   which would shift the objective further toward clean resources.
""")

# ── References ────────────────────────────────────────────────────────────────
st.subheader("References")
st.markdown("""
- NYISO (2023). *2023 Comprehensive Reliability Plan*. New York Independent System Operator.
- NREL (2023). *Annual Technology Baseline*. National Renewable Energy Laboratory.
- NYSERDA (2019). *Climate Leadership and Community Protection Act*. NY State.
- Brown & Botterud (2021). *The Role of Long-Duration Energy Storage in Deep Decarbonization*.
  *Joule*, 5(1), 3–4.
- Sepulveda et al. (2021). *The Design Space for Long-Duration Energy Storage in
  Decarbonized Power Systems*. *Nature Energy*, 6, 506–516.
""")
