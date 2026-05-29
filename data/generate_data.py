"""
data/generate_data.py
Generates synthetic but realistic NYISO demand and NREL ATB cost data.
Sources modeled after:
  - NYISO 2023 Gold Book (hourly load ~155 TWh annual, peak ~28 GW)
  - NREL Annual Technology Baseline 2023 (capital/O&M costs, Moderate scenario)
"""

import numpy as np
import pandas as pd

np.random.seed(42)


def generate_nyiso_demand(year: int = 2023) -> pd.DataFrame:
    """
    Synthetic NYISO hourly demand for one year (8760 hours).
    Calibrated to ~155 TWh annual energy, ~28 GW summer peak.
    """
    hours = np.arange(8760)
    day_of_year = hours // 24
    hour_of_day = hours % 24

    seasonal = (
        5.0 * np.sin(2 * np.pi * (day_of_year - 172) / 365)
        - 1.5 * np.cos(4 * np.pi * day_of_year / 365)
    )
    diurnal = (
        3.5 * np.sin(np.pi * (hour_of_day - 6) / 14) * (hour_of_day >= 6) * (hour_of_day <= 22)
        - 1.0 * (hour_of_day < 6).astype(float)
    )
    day_of_week = (day_of_year + 3) % 7
    weekend_factor = np.where(day_of_week >= 5, -1.5, 0.0)

    base = 17.0   # GW — calibrated to ~155 TWh annual
    noise = np.random.normal(0, 0.4, 8760)
    demand_gw = np.clip(base + seasonal + diurnal + weekend_factor + noise, 12.0, 30.0)

    timestamps = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return pd.DataFrame({
        "timestamp": timestamps,
        "hour": hours,
        "month": timestamps.month,
        "hour_of_day": hour_of_day,
        "demand_gw": demand_gw,
        "demand_mw": demand_gw * 1000,
    })


def generate_nrel_atb() -> pd.DataFrame:
    """NREL ATB 2023 Moderate scenario costs for NY State."""
    technologies = {
        "Solar PV (Utility)": {
            "capital_cost_per_kw": 1150, "fixed_om_per_kw_yr": 17,
            "var_om_per_mwh": 0, "fuel_cost_per_mwh": 0,
            "capacity_factor": 0.19, "lifetime_yr": 30,
            "co2_kg_per_mwh": 0, "color": "#FFB703", "type": "renewable",
        },
        "Onshore Wind": {
            "capital_cost_per_kw": 1500, "fixed_om_per_kw_yr": 43,
            "var_om_per_mwh": 0, "fuel_cost_per_mwh": 0,
            "capacity_factor": 0.35, "lifetime_yr": 25,
            "co2_kg_per_mwh": 0, "color": "#219EBC", "type": "renewable",
        },
        "Offshore Wind": {
            "capital_cost_per_kw": 3200, "fixed_om_per_kw_yr": 110,
            "var_om_per_mwh": 0, "fuel_cost_per_mwh": 0,
            "capacity_factor": 0.44, "lifetime_yr": 25,
            "co2_kg_per_mwh": 0, "color": "#0077B6", "type": "renewable",
        },
        "Battery Storage (4h)": {
            "capital_cost_per_kw": 1400, "fixed_om_per_kw_yr": 28,
            "var_om_per_mwh": 2, "fuel_cost_per_mwh": 0,
            "capacity_factor": 0.20, "lifetime_yr": 15,
            "co2_kg_per_mwh": 0, "color": "#8338EC", "type": "storage",
        },
        "Natural Gas (CCGT)": {
            "capital_cost_per_kw": 1050, "fixed_om_per_kw_yr": 12,
            "var_om_per_mwh": 3.5, "fuel_cost_per_mwh": 28,
            "capacity_factor": 0.55, "lifetime_yr": 30,
            "co2_kg_per_mwh": 370, "color": "#E76F51", "type": "fossil",
        },
        "Nuclear": {
            "capital_cost_per_kw": 7200, "fixed_om_per_kw_yr": 145,
            "var_om_per_mwh": 2.5, "fuel_cost_per_mwh": 8,
            "capacity_factor": 0.93, "lifetime_yr": 60,
            "co2_kg_per_mwh": 12, "color": "#6D6875", "type": "low_carbon",
        },
        "Hydropower": {
            "capital_cost_per_kw": 2800, "fixed_om_per_kw_yr": 45,
            "var_om_per_mwh": 1, "fuel_cost_per_mwh": 0,
            "capacity_factor": 0.52, "lifetime_yr": 50,
            "co2_kg_per_mwh": 4, "color": "#2EC4B6", "type": "renewable",
        },
    }

    records = []
    r = 0.07
    for tech, p in technologies.items():
        n = p["lifetime_yr"]
        crf = (r * (1 + r)**n) / ((1 + r)**n - 1)
        annual_cap = p["capital_cost_per_kw"] * crf
        lcoe = (annual_cap + p["fixed_om_per_kw_yr"]) / (p["capacity_factor"] * 8.76) + p["var_om_per_mwh"] + p["fuel_cost_per_mwh"]
        records.append({**p, "technology": tech,
                        "annual_capital_per_kw_yr": round(annual_cap, 1),
                        "lcoe_per_mwh": round(lcoe, 1), "crf": round(crf, 4)})
    return pd.DataFrame(records)


def generate_price_projections() -> pd.DataFrame:
    years = list(range(2023, 2041))
    records = []
    for yr in years:
        d = yr - 2023
        records.append({
            "year": yr,
            "solar_capital_per_kw":        round(1150 * (0.94**d), 0),
            "solar_lcoe_per_mwh":          round(42   * (0.94**d), 1),
            "onshore_wind_capital_per_kw":  round(1500 * (0.97**d), 0),
            "onshore_wind_lcoe_per_mwh":    round(38   * (0.97**d), 1),
            "offshore_wind_capital_per_kw": round(3200 * (0.955**d), 0),
            "offshore_wind_lcoe_per_mwh":   round(82   * (0.955**d), 1),
            "battery_capital_per_kw":       round(1400 * (0.92**d), 0),
        })
    return pd.DataFrame(records)


def get_ny_capacity_limits() -> dict:
    """
    Technical upper/lower bounds (GW) for NY State.
    Offshore wind cap raised to 30 GW to enable 100% RPS feasibility
    (consistent with long-term CLCPA planning studies).
    """
    return {
        "Solar PV (Utility)":   {"min_gw": 0,   "max_gw": 25.0},
        "Onshore Wind":         {"min_gw": 0,   "max_gw": 10.0},
        "Offshore Wind":        {"min_gw": 0,   "max_gw": 30.0},
        "Battery Storage (4h)": {"min_gw": 0,   "max_gw": 20.0},
        "Natural Gas (CCGT)":   {"min_gw": 2.0, "max_gw": 15.0},
        "Nuclear":              {"min_gw": 3.0, "max_gw": 5.0},
        "Hydropower":           {"min_gw": 4.0, "max_gw": 6.5},
    }


if __name__ == "__main__":
    d = generate_nyiso_demand()
    a = generate_nrel_atb()
    p = generate_price_projections()
    d.to_csv("nyiso_demand_2023.csv", index=False)
    a.to_csv("nrel_atb_2023.csv", index=False)
    p.to_csv("price_projections.csv", index=False)
    print(f"Demand: {len(d)} hrs, peak={d.demand_gw.max():.1f} GW, annual={d.demand_mw.sum()/1e6:.1f} TWh")
    print(f"ATB: {len(a)} technologies")
    print("\nLCOEs ($/MWh):")
    print(a[["technology","lcoe_per_mwh","capacity_factor"]].to_string(index=False))
