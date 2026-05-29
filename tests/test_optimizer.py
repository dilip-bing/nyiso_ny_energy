"""
tests/test_optimizer.py
Optimizer correctness tests: verify all three scenarios solve optimally,
constraints are satisfied, and results are economically consistent.
"""

import sys
from pathlib import Path

import pytest
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models.optimizer import NYEnergyOptimizer
from models.scenarios import ScenarioResult
from config import (
    RENEWABLE_TECHS, ZERO_CARBON_TECHS, CAPACITY_CREDIT,
    RESERVE_MARGIN, NY_BASELINE_CO2_MT,
)


@pytest.fixture(scope="module")
def optimizer() -> NYEnergyOptimizer:
    return NYEnergyOptimizer()


@pytest.fixture(scope="module")
def all_results(optimizer) -> dict[str, ScenarioResult]:
    results = optimizer.run_all_scenarios()
    return {r.scenario_name: r for r in results}


class TestSolverStatus:

    def test_50pct_rps_optimal(self, all_results):
        assert all_results["50% Renewable"].status == "Optimal"

    def test_80pct_rps_optimal(self, all_results):
        assert all_results["80% Renewable"].status == "Optimal"

    def test_100pct_zce_optimal(self, all_results):
        assert all_results["100% Zero-Carbon"].status == "Optimal"


class TestEnergyBalance:

    def test_50pct_energy_balance(self, optimizer, all_results):
        r = all_results["50% Renewable"]
        total_gen = sum(r.generation_twh.values())
        assert total_gen >= optimizer.annual_demand_twh - 0.01, (
            f"Energy balance violated: gen={total_gen:.2f} < demand={optimizer.annual_demand_twh:.2f}"
        )

    def test_80pct_energy_balance(self, optimizer, all_results):
        r = all_results["80% Renewable"]
        total_gen = sum(r.generation_twh.values())
        assert total_gen >= optimizer.annual_demand_twh - 0.01

    def test_100pct_energy_balance(self, optimizer, all_results):
        r = all_results["100% Zero-Carbon"]
        total_gen = sum(r.generation_twh.values())
        assert total_gen >= optimizer.annual_demand_twh - 0.01


class TestRPSConstraint:

    def test_50pct_rps_satisfied(self, all_results):
        r = all_results["50% Renewable"]
        ren_gen = sum(r.generation_twh[t] for t in r.generation_twh if t in RENEWABLE_TECHS)
        total_gen = sum(r.generation_twh.values())
        actual_rps = ren_gen / total_gen if total_gen > 0 else 0
        assert actual_rps >= 0.50 - 1e-4, (
            f"50% RPS violated: actual={actual_rps:.2%}"
        )

    def test_80pct_rps_satisfied(self, all_results):
        r = all_results["80% Renewable"]
        ren_gen = sum(r.generation_twh[t] for t in r.generation_twh if t in RENEWABLE_TECHS)
        total_gen = sum(r.generation_twh.values())
        actual_rps = ren_gen / total_gen if total_gen > 0 else 0
        assert actual_rps >= 0.80 - 1e-4, (
            f"80% RPS violated: actual={actual_rps:.2%}"
        )

    def test_100pct_zce_no_fossil(self, all_results):
        r = all_results["100% Zero-Carbon"]
        fossil_gen = sum(
            r.generation_twh[t] for t in r.generation_twh
            if t not in ZERO_CARBON_TECHS
        )
        assert fossil_gen < 0.01, (
            f"100% ZCE has fossil generation: {fossil_gen:.3f} TWh"
        )

    def test_100pct_zero_carbon_fraction(self, all_results):
        r = all_results["100% Zero-Carbon"]
        assert r.zero_carbon_fraction >= 0.999, (
            f"ZCE scenario zero-carbon fraction: {r.zero_carbon_fraction:.3%}"
        )


class TestPeakAdequacy:

    def test_50pct_peak_adequacy(self, optimizer, all_results):
        r = all_results["50% Renewable"]
        firm_gw = sum(CAPACITY_CREDIT.get(t, 0.9) * r.capacity_gw[t] for t in r.capacity_gw)
        required = optimizer.peak_demand_gw * RESERVE_MARGIN["50% Renewable"]
        assert firm_gw >= required - 0.01, (
            f"Peak adequacy violated: firm={firm_gw:.2f} < required={required:.2f}"
        )

    def test_80pct_peak_adequacy(self, optimizer, all_results):
        r = all_results["80% Renewable"]
        firm_gw = sum(CAPACITY_CREDIT.get(t, 0.9) * r.capacity_gw[t] for t in r.capacity_gw)
        required = optimizer.peak_demand_gw * RESERVE_MARGIN["80% Renewable"]
        assert firm_gw >= required - 0.01

    def test_100pct_peak_adequacy(self, optimizer, all_results):
        r = all_results["100% Zero-Carbon"]
        firm_gw = sum(CAPACITY_CREDIT.get(t, 0.9) * r.capacity_gw[t] for t in r.capacity_gw)
        required = optimizer.peak_demand_gw * RESERVE_MARGIN["100% Zero-Carbon"]
        assert firm_gw >= required - 0.01


class TestResultSanity:

    def test_all_costs_positive(self, all_results):
        for scenario, r in all_results.items():
            assert r.total_cost_b_yr > 0, f"Non-positive cost in {scenario}"

    def test_all_lcoe_positive(self, all_results):
        for scenario, r in all_results.items():
            assert r.lcoe_system > 0, f"Non-positive LCOE in {scenario}"

    def test_no_negative_capacity(self, all_results):
        for scenario, r in all_results.items():
            for tech, gw in r.capacity_gw.items():
                assert gw >= -1e-6, f"Negative capacity {gw:.4f} GW for {tech} in {scenario}"

    def test_no_negative_generation(self, all_results):
        for scenario, r in all_results.items():
            for tech, twh in r.generation_twh.items():
                assert twh >= -1e-6, f"Negative generation {twh:.4f} TWh for {tech} in {scenario}"

    def test_co2_reduction_ordering(self, all_results):
        """More stringent RPS → lower or equal CO₂."""
        co2_50 = all_results["50% Renewable"].co2_mt_yr
        co2_80 = all_results["80% Renewable"].co2_mt_yr
        co2_100 = all_results["100% Zero-Carbon"].co2_mt_yr
        assert co2_80 <= co2_50 + 0.1, "80% RPS should emit ≤ 50% RPS"
        assert co2_100 <= co2_80 + 0.1, "100% ZCE should emit ≤ 80% RPS"

    def test_100pct_near_zero_co2(self, all_results):
        """100% ZCE scenario should have near-zero CO₂ emissions."""
        r = all_results["100% Zero-Carbon"]
        assert r.co2_mt_yr < 5.0, f"100% ZCE CO₂ too high: {r.co2_mt_yr} Mt/yr"

    def test_generation_link_consistency(self, optimizer, all_results):
        """gen[t] ≈ cap[t] × CF[t] × 8760 (within numerical tolerance)."""
        atb = optimizer.atb_df
        for scenario, r in all_results.items():
            for tech in optimizer.techs:
                gw = r.capacity_gw.get(tech, 0)
                twh = r.generation_twh.get(tech, 0)
                cf = float(atb.loc[tech, "capacity_factor"])
                expected_twh = gw * cf * 8.76
                assert abs(twh - expected_twh) < 0.01, (
                    f"CF link violated for {tech} in {scenario}: "
                    f"gen={twh:.3f} ≠ cap×CF×8760={expected_twh:.3f}"
                )

    def test_renewable_fraction_ordering(self, all_results):
        """Stricter RPS scenarios should have higher renewable fractions."""
        rf_50 = all_results["50% Renewable"].renewable_fraction
        rf_80 = all_results["80% Renewable"].renewable_fraction
        assert rf_80 >= rf_50 - 0.01, (
            f"80% RPS renewable fraction ({rf_80:.2%}) should be ≥ 50% RPS ({rf_50:.2%})"
        )


class TestSensitivityAnalysis:

    def test_sensitivity_runs_without_error(self, optimizer):
        df = optimizer.run_sensitivity(
            "80% Renewable",
            solar_range=[800, 1000, 1150],
            wind_range=[1000, 1500],
        )
        assert len(df) == 6  # 3 × 2 grid

    def test_sensitivity_lower_cost_at_lower_price(self, optimizer):
        """Lower solar price should give lower or equal total system cost."""
        df = optimizer.run_sensitivity(
            "80% Renewable",
            solar_range=[500, 1150],
            wind_range=[1500],
        )
        low_cost = df[df["solar_capital_per_kw"] == 500]["total_cost_b_yr"].values[0]
        high_cost = df[df["solar_capital_per_kw"] == 1150]["total_cost_b_yr"].values[0]
        assert low_cost <= high_cost + 0.5, (
            f"Lower solar price should reduce cost: {low_cost:.2f} vs {high_cost:.2f}"
        )
