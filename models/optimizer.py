"""
models/optimizer.py
Least-cost electricity generation mix optimizer for New York State.
Uses PuLP linear programming with the open-source CBC solver.

Scenarios
---------
  50% RPS   — 50% of generation from renewables (wind, solar, hydro)
  80% RPS   — 80% renewable
  100% ZCE  — 100% zero-carbon electricity (CLCPA definition)
              Renewables + nuclear qualify; natural gas phased out.

Objective
---------
  Minimize total annualized system cost (capital + fixed O&M + variable + fuel)

Run directly:
  python models/optimizer.py
"""

from __future__ import annotations

import sys
import time
import logging
from pathlib import Path
from typing import Optional

import pulp
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import (
    WACC, ANNUAL_HOURS, NY_BASELINE_CO2_MT,
    RENEWABLE_TECHS, ZERO_CARBON_TECHS, CAPACITY_CREDIT,
    NY_CAPACITY_LIMITS, RESERVE_MARGIN,
)
from models.constraints import (
    energy_balance, generation_link, rps_constraint,
    zce_constraint, peak_adequacy, capacity_bounds, apply_constraints,
)
from models.scenarios import ScenarioConfig, ScenarioResult
from data.generate_data import generate_nyiso_demand, generate_nrel_atb

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class NYEnergyOptimizer:
    """
    LP-based least-cost capacity expansion model for New York State.
    Covers a static single-year planning horizon with 7 technology options.
    """

    def __init__(self) -> None:
        self.demand_df = generate_nyiso_demand()
        self.atb_df = generate_nrel_atb().set_index("technology")
        self.base_limits = NY_CAPACITY_LIMITS

        self.annual_demand_twh = self.demand_df["demand_mw"].sum() / 1e6
        self.peak_demand_gw = self.demand_df["demand_gw"].max()
        self.techs: list[str] = list(self.atb_df.index)

    # ── Core solver ──────────────────────────────────────────────────────────

    def optimize(
        self,
        scenario: str | ScenarioConfig,
        price_overrides: Optional[dict[str, float]] = None,
    ) -> ScenarioResult:
        """
        Solve the LP for a single scenario.

        Parameters
        ----------
        scenario:
            Scenario name string or ScenarioConfig dataclass.
        price_overrides:
            {technology: new_capital_cost_per_kw} for sensitivity sweeps.

        Returns
        -------
        ScenarioResult with capacity, generation, costs, and emissions.
        """
        if isinstance(scenario, str):
            cfg = self._config_from_name(scenario)
        else:
            cfg = scenario

        atb = self.atb_df.copy()
        limits = {k: dict(v) for k, v in self.base_limits.items()}

        if not cfg.gas_allowed:
            limits["Natural Gas (CCGT)"]["min_gw"] = 0.0
            limits["Natural Gas (CCGT)"]["max_gw"] = 0.0

        if price_overrides:
            atb = self._apply_price_overrides(atb, price_overrides)

        required_peak_gw = self.peak_demand_gw * cfg.reserve_margin

        # ── Decision variables ────────────────────────────────────────────────
        prob = pulp.LpProblem(f"NY_{cfg.name.replace(' ', '_')}", pulp.LpMinimize)
        cap = {t: pulp.LpVariable(f"cap_{i}", lowBound=0) for i, t in enumerate(self.techs)}
        gen = {t: pulp.LpVariable(f"gen_{i}", lowBound=0) for i, t in enumerate(self.techs)}

        # ── Objective: minimize annualized cost ($M/yr) ───────────────────────
        prob += pulp.lpSum(
            (atb.loc[t, "annual_capital_per_kw_yr"] + atb.loc[t, "fixed_om_per_kw_yr"])
            * cap[t]
            + (atb.loc[t, "var_om_per_mwh"] + atb.loc[t, "fuel_cost_per_mwh"])
            * gen[t] * 1e-3
            for t in self.techs
        ), "minimize_total_cost"

        # ── Constraints ───────────────────────────────────────────────────────
        apply_constraints(prob, energy_balance(gen, self.annual_demand_twh))
        apply_constraints(prob, generation_link(cap, gen, atb, ANNUAL_HOURS))
        apply_constraints(prob, peak_adequacy(cap, required_peak_gw, CAPACITY_CREDIT))
        apply_constraints(prob, capacity_bounds(cap, limits))

        if cfg.rps_target is not None:
            apply_constraints(prob, rps_constraint(gen, RENEWABLE_TECHS, cfg.rps_target))
        if cfg.zce_mode:
            apply_constraints(prob, zce_constraint(gen, ZERO_CARBON_TECHS))

        # ── Solve ─────────────────────────────────────────────────────────────
        t0 = time.perf_counter()
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        elapsed = time.perf_counter() - t0
        status = pulp.LpStatus[prob.status]
        logger.debug("Scenario %s solved in %.2fs — %s", cfg.name, elapsed, status)

        if status != "Optimal":
            logger.warning("Non-optimal status for %s: %s", cfg.name, status)
            return ScenarioResult(
                scenario_name=cfg.name,
                rps_target=cfg.effective_rps,
                status=status,
                total_cost_b_yr=0.0,
                lcoe_system=0.0,
                annual_demand_twh=round(self.annual_demand_twh, 1),
                peak_demand_gw=round(self.peak_demand_gw, 1),
            )

        return self._extract_result(cfg, cap, gen, atb)

    # ── Batch runs ────────────────────────────────────────────────────────────

    def run_all_scenarios(self) -> list[ScenarioResult]:
        """Solve all three policy scenarios and return results list."""
        results = []
        for cfg in ScenarioConfig.all_scenarios():
            print(f"  → {cfg.name}...", end=" ", flush=True)
            r = self.optimize(cfg)
            print(
                f"{r.status} | ${r.total_cost_b_yr:.2f}B/yr | "
                f"${r.lcoe_system:.1f}/MWh | RPS {r.renewable_fraction:.0%} | "
                f"ZC {r.zero_carbon_fraction:.0%} | CO₂ {r.co2_mt_yr:.1f} Mt/yr"
            )
            results.append(r)
        return results

    def run_sensitivity(
        self,
        scenario: str,
        solar_range: list[float],
        wind_range: list[float],
    ) -> pd.DataFrame:
        """
        Grid search over solar × onshore-wind capital costs for one scenario.
        Offshore wind is scaled proportionally (2.1× onshore).
        Returns a DataFrame with costs, LCOE, and optimal capacities.
        """
        records = []
        for sc in solar_range:
            for wc in wind_range:
                overrides = {
                    "Solar PV (Utility)": float(sc),
                    "Onshore Wind": float(wc),
                    "Offshore Wind": float(wc) * 2.1,
                }
                r = self.optimize(scenario, price_overrides=overrides)
                records.append({
                    "solar_capital_per_kw":  int(sc),
                    "wind_capital_per_kw":   int(wc),
                    "total_cost_b_yr":       r.total_cost_b_yr,
                    "lcoe_system":           r.lcoe_system,
                    "renewable_fraction":    r.renewable_fraction,
                    "co2_mt_yr":             r.co2_mt_yr,
                    "solar_gw":              r.capacity_gw.get("Solar PV (Utility)", 0),
                    "wind_gw": (
                        r.capacity_gw.get("Onshore Wind", 0)
                        + r.capacity_gw.get("Offshore Wind", 0)
                    ),
                })
        return pd.DataFrame(records)

    # ── Private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _config_from_name(name: str) -> ScenarioConfig:
        mapping = {
            "50% Renewable":    ScenarioConfig.rps_50(),
            "80% Renewable":    ScenarioConfig.rps_80(),
            "100% Zero-Carbon": ScenarioConfig.zce_100(),
        }
        if name not in mapping:
            raise ValueError(f"Unknown scenario '{name}'. Choose from: {list(mapping)}")
        return mapping[name]

    @staticmethod
    def _apply_price_overrides(atb: pd.DataFrame, overrides: dict) -> pd.DataFrame:
        """Recompute annual capital cost and LCOE for overridden technologies."""
        for tech, new_cap_kw in overrides.items():
            if tech not in atb.index:
                continue
            crf = atb.loc[tech, "crf"]
            new_annual = new_cap_kw * crf
            cf = atb.loc[tech, "capacity_factor"]
            fo = atb.loc[tech, "fixed_om_per_kw_yr"]
            vo = atb.loc[tech, "var_om_per_mwh"]
            fu = atb.loc[tech, "fuel_cost_per_mwh"]
            atb.loc[tech, "capital_cost_per_kw"] = new_cap_kw
            atb.loc[tech, "annual_capital_per_kw_yr"] = new_annual
            atb.loc[tech, "lcoe_per_mwh"] = (new_annual + fo) / (cf * 8.76) + vo + fu
        return atb

    def _extract_result(
        self,
        cfg: ScenarioConfig,
        cap: dict,
        gen: dict,
        atb: pd.DataFrame,
    ) -> ScenarioResult:
        """Extract and compute all output metrics from solved LP variables."""
        capacity_gw = {t: round(float(pulp.value(cap[t]) or 0), 3) for t in self.techs}
        generation_twh = {t: round(float(pulp.value(gen[t]) or 0), 3) for t in self.techs}

        cost_m: dict[str, float] = {}
        for t in self.techs:
            cc = (
                (atb.loc[t, "annual_capital_per_kw_yr"] + atb.loc[t, "fixed_om_per_kw_yr"])
                * capacity_gw[t]
            )
            vc = (
                (atb.loc[t, "var_om_per_mwh"] + atb.loc[t, "fuel_cost_per_mwh"])
                * generation_twh[t] * 1e3 / 1e6
            )
            cost_m[t] = round(cc + vc, 1)

        total_cost_m = sum(cost_m.values())
        total_gen = sum(generation_twh.values())
        ren_gen = sum(generation_twh[t] for t in self.techs if t in RENEWABLE_TECHS)
        zc_gen = sum(generation_twh[t] for t in self.techs if t in ZERO_CARBON_TECHS)
        co2_mt = sum(
            float(atb.loc[t, "co2_kg_per_mwh"]) * generation_twh[t] * 1e6 / 1e9
            for t in self.techs
        )
        lcoe = (total_cost_m * 1e6) / (total_gen * 1e6) if total_gen > 0 else 0.0

        return ScenarioResult(
            scenario_name=cfg.name,
            rps_target=cfg.effective_rps,
            status="Optimal",
            total_cost_b_yr=round(total_cost_m / 1e3, 2),
            lcoe_system=round(lcoe, 1),
            capacity_gw=capacity_gw,
            generation_twh=generation_twh,
            cost_breakdown_m=cost_m,
            renewable_fraction=round(ren_gen / total_gen, 3) if total_gen else 0.0,
            zero_carbon_fraction=round(zc_gen / total_gen, 3) if total_gen else 0.0,
            co2_mt_yr=round(co2_mt, 2),
            annual_demand_twh=round(self.annual_demand_twh, 1),
            peak_demand_gw=round(self.peak_demand_gw, 1),
        )


# ── CLI entry point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("NY State Least-Cost Renewable Energy Pathway Optimizer")
    print("=" * 60)
    opt = NYEnergyOptimizer()
    print(
        f"  Annual demand : {opt.annual_demand_twh:.1f} TWh\n"
        f"  Peak demand   : {opt.peak_demand_gw:.1f} GW\n"
        f"  Technologies  : {len(opt.techs)}\n"
    )
    results = opt.run_all_scenarios()

    print("\nCapacity mix (GW) — non-zero only:")
    for r in results:
        print(f"\n  ── {r.scenario_name} ──")
        for t, gw in r.capacity_gw.items():
            if gw > 0.05:
                twh = r.generation_twh.get(t, 0)
                cost = r.cost_breakdown_m.get(t, 0)
                print(f"    {t:<30s} {gw:6.1f} GW  {twh:6.1f} TWh  ${cost/1e3:.2f}B")
        print(
            f"  Total: ${r.total_cost_b_yr:.2f}B/yr  LCOE=${r.lcoe_system:.0f}/MWh  "
            f"CO₂={r.co2_mt_yr:.1f} Mt/yr"
        )
