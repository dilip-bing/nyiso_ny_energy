# ⚡ NY State Least-Cost Renewable Energy Pathway Analyzer

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Built%20with-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: 42 passing](https://img.shields.io/badge/tests-42%20passing-brightgreen.svg)]()

**Individual Project · February 2026**

A Python linear programming tool that models the **minimum-cost electricity generation mix** for New York State under three Clean Energy Standard policy scenarios. Built with PuLP, Streamlit, and Plotly — integrating NYISO 2023 hourly demand and NREL Annual Technology Baseline cost datasets across 7 technologies.

---

## Live Results

| Scenario | Annual Cost | System LCOE | Renewable % | Zero-Carbon % | CO₂ (Mt/yr) | CO₂ Reduction |
|----------|------------|-------------|-------------|---------------|-------------|---------------|
| 50% Renewable | $9.75B/yr | $63/MWh | 50% | 84% | 9.7 | 82% |
| 80% Renewable | $19.77B/yr | $79/MWh | 80% | 96% | 4.0 | 93% |
| **100% Zero-Carbon** | **$11.00B/yr** | **$72/MWh** | **65%** | **100%** | **0.4** | **99%** |

> **Counterintuitive result:** The 100% Zero-Carbon scenario costs **44% less than 80% Renewable** because eliminating gas avoids the $9.9B/yr offshore wind overbuild (26 GW) that dominates the 80% RPS case. Nuclear baseload (3 GW) anchors firm capacity cheaply.

---

## Key Findings

1. **100% zero-carbon is surprisingly affordable** — at $11.0B/yr it is only 13% more expensive than the 50% RPS baseline, because the nuclear fleet (existing 3 GW, low marginal cost) and aggressive solar + battery buildout replace gas more cheaply than large-scale offshore wind.

2. **80% RPS is the most expensive scenario** — hitting 80% with some residual gas requires 25.6 GW of offshore wind (the highest-CAPEX technology), making it $8B/yr more expensive than going all the way to 100% ZCE.

3. **Battery storage scales with solar** — 15–17 GW of 4-hour storage is needed at high RPS levels to time-shift midday solar and maintain firm capacity for the evening peak.

4. **Solar price trajectory matters most** — sensitivity analysis shows a 15% total cost reduction if solar capital costs fall from $1,150 to $600/kW (consistent with NREL Advanced scenario by 2035).

5. **NY's existing hydro is a critical anchor** — 6.5 GW of must-run hydropower (4.0 GW minimum) provides baseload renewable generation in all scenarios, reducing the required variable capacity.

---

## Architecture

```
ny_energy/
├── config.py                   # All constants: paths, colors, parameters, WACC
├── data/
│   ├── generate_data.py        # NYISO demand (8,760-hr) + NREL ATB cost pipeline
│   ├── raw/                    # Placeholder for real NYISO/NREL downloads
│   └── processed/              # Cleaned outputs
├── models/
│   ├── optimizer.py            # NYEnergyOptimizer class (PuLP/CBC LP solver)
│   ├── constraints.py          # Modular constraint builders (energy, RPS, peak)
│   └── scenarios.py            # ScenarioConfig + ScenarioResult dataclasses
├── dashboard/
│   ├── app.py                  # Streamlit entry point (st.navigation controller)
│   ├── pages/
│   │   ├── 1_Overview.py       # KPI cards, cost/CO₂ charts, summary table
│   │   ├── 2_Capacity_Mix.py   # Donut charts, stacked scenario comparisons
│   │   ├── 3_Cost_Analysis.py  # Per-tech cost bars, LCOE comparison, breakdown
│   │   ├── 4_Sensitivity.py    # Solar×wind heatmaps, capacity response curves
│   │   ├── 5_Demand_Profile.py # 8,760-hr timeseries, seasonal curves, heatmap
│   │   └── 6_Methodology.py    # LP formulation in LaTeX, data sources, limits
│   └── components/
│       ├── charts.py           # All Plotly chart factory functions
│       └── metrics.py          # Cached data loaders + KPI card renderers
├── notebooks/
│   ├── 01_data_exploration.ipynb   # Demand profile + ATB cost visualization
│   ├── 02_model_validation.ipynb   # Constraint verification + shadow prices
│   └── 03_results_analysis.ipynb  # Scenario comparison + policy implications
├── tests/
│   ├── test_data.py            # 19 tests: demand calibration, ATB quality
│   └── test_optimizer.py       # 23 tests: solver status, constraints, sanity
├── requirements.txt
└── .gitignore
```

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Optimization | Python, PuLP, CBC solver (open-source LP) |
| Numerical | NumPy, SciPy, Pandas |
| Visualization | Plotly, Streamlit 1.36+ multi-page |
| Data | NYISO 2023 Gold Book (demand), NREL ATB 2023 Moderate (costs) |
| Dev | Jupyter, pytest, pathlib, dataclasses |

---

## Installation & Running

```bash
# Clone the repository
git clone https://github.com/dilip-bing/ny-energy-optimizer
cd ny-energy-optimizer

# Install dependencies
pip install -r requirements.txt

# Run the optimizer (console output for all 3 scenarios)
python models/optimizer.py

# Launch the interactive Streamlit dashboard
streamlit run dashboard/app.py

# Run the test suite
pytest tests/ -v
```

---

## Optimization Model

**Objective:** Minimize total annualized system cost (capital + fixed O&M + variable + fuel):

```
min  Σ_t [ (CRF_t × CAPEX_t + FOM_t) × cap[t]  +  (VOM_t + Fuel_t) × gen[t] ]
```

**Decision variables:**
- `cap[t]` — Installed capacity (GW) per technology
- `gen[t]` — Annual energy generation (TWh) per technology

**Constraints:**

| Constraint | Equation |
|------------|----------|
| Energy balance | Σ gen[t] ≥ annual demand (153.9 TWh) |
| Capacity factor link | gen[t] = cap[t] × CF[t] × 8,760h |
| RPS (50%/80%) | Σ_{t∈R} gen[t] ≥ RPS × Σ gen[t] |
| ZCE (100%) | gen[t] = 0 ∀ t ∉ zero-carbon set |
| Peak adequacy | Σ δ_t × cap[t] ≥ peak × reserve margin |
| Capacity bounds | cap_min[t] ≤ cap[t] ≤ cap_max[t] |

**Financial assumptions:** 7% WACC, technology-specific lifetimes (15–60 yr), Capital Recovery Factor annualization.

---

## Data Sources

| Dataset | Source | Notes |
|---------|--------|-------|
| NYISO 2023 Gold Book | NYISO | Hourly demand; synthetic ~154 TWh, ~28 GW peak |
| NREL ATB 2023 | NREL (atb.nrel.gov) | Moderate scenario; 7 technologies |
| CLCPA (2019) | NYSERDA / DPS | 70% RPS by 2030; 100% ZCE by 2040 |
| NYISO Reliability Plan | NYISO (2022) | Reserve margins; capacity credit assumptions |
| EIA Electric Power Monthly | EIA (2023) | US average retail price benchmark |

---

## Capacity Credit (Derate) Factors

| Technology | Credit | Basis |
|------------|--------|-------|
| Solar PV | 15% | Low coincidence with summer afternoon peak |
| Onshore Wind | 20% | Coastal resource correlation with peak |
| Offshore Wind | 25% | Higher offshore wind at peak hours |
| Hydropower | 80% | Largely dispatchable |
| Battery (4h) | 100% | Full rated discharge for 4-hour peak window |
| Nuclear | 95% | Regulated baseload |
| Natural Gas CCGT | 95% | Fully dispatchable thermal |

---

## Limitations

- **Static single-year model** — no intra-hour dispatch, unit commitment, or seasonal storage cycling
- **Copper plate** — no transmission zones, congestion, or NY's 11-zone grid topology
- **No demand growth** — CLCPA electrification (EVs, heat pumps) could add 20–40% load by 2040
- **Battery simplified** — modeled on energy basis; intra-day cycling and round-trip losses not captured
- **No carbon pricing** — NY RGGI allowance costs (~$15/tonne) would shift results toward clean resources

---

## Author

**Dilip**
MS Computer Science (AI Track) · Binghamton University
5 years SWE/automation experience at Zoho Corporation

- GitHub: [github.com/dilip-bing](https://github.com/dilip-bing)

---

## License

MIT
