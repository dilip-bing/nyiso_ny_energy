"""
tests/test_data.py
Data pipeline tests: validate that the synthetic NYISO demand and NREL ATB
outputs meet calibration targets and have no data quality issues.
"""

import sys
from pathlib import Path

import pytest
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.generate_data import generate_nyiso_demand, generate_nrel_atb, generate_price_projections
from config import NY_ANNUAL_DEMAND_TWH, NY_PEAK_DEMAND_GW, ALL_TECHS


class TestNYISODemand:

    @pytest.fixture(scope="class")
    def demand_df(self) -> pd.DataFrame:
        return generate_nyiso_demand()

    def test_row_count(self, demand_df):
        """Exactly 8,760 hourly rows for one year."""
        assert len(demand_df) == 8760

    def test_annual_energy_calibration(self, demand_df):
        """Annual energy within ±5% of 154 TWh (NYISO 2023 Gold Book)."""
        twh = demand_df["demand_mw"].sum() / 1e6
        assert abs(twh - NY_ANNUAL_DEMAND_TWH) / NY_ANNUAL_DEMAND_TWH < 0.05, (
            f"Annual energy {twh:.1f} TWh deviates >5% from {NY_ANNUAL_DEMAND_TWH} TWh target"
        )

    def test_peak_demand_calibration(self, demand_df):
        """Peak demand within ±10% of 28 GW summer peak target."""
        peak = demand_df["demand_gw"].max()
        assert abs(peak - NY_PEAK_DEMAND_GW) / NY_PEAK_DEMAND_GW < 0.10, (
            f"Peak {peak:.1f} GW deviates >10% from {NY_PEAK_DEMAND_GW} GW target"
        )

    def test_minimum_demand_positive(self, demand_df):
        """Demand never goes below 10 GW (overnight minimum floor)."""
        assert demand_df["demand_gw"].min() > 10.0

    def test_no_missing_values(self, demand_df):
        assert demand_df.isnull().sum().sum() == 0

    def test_required_columns(self, demand_df):
        required = {"timestamp", "hour", "month", "hour_of_day", "demand_gw", "demand_mw"}
        assert required.issubset(set(demand_df.columns))

    def test_demand_mw_consistency(self, demand_df):
        """demand_mw == demand_gw * 1000."""
        assert np.allclose(demand_df["demand_mw"], demand_df["demand_gw"] * 1000, rtol=1e-6)

    def test_month_range(self, demand_df):
        assert demand_df["month"].min() == 1
        assert demand_df["month"].max() == 12

    def test_hour_of_day_range(self, demand_df):
        assert demand_df["hour_of_day"].min() == 0
        assert demand_df["hour_of_day"].max() == 23


class TestNRELATB:

    @pytest.fixture(scope="class")
    def atb_df(self) -> pd.DataFrame:
        return generate_nrel_atb()

    def test_technology_count(self, atb_df):
        """Exactly 7 technologies modeled."""
        assert len(atb_df) == 7

    def test_all_technologies_present(self, atb_df):
        techs = set(atb_df["technology"])
        for t in ALL_TECHS:
            assert t in techs, f"Technology '{t}' missing from ATB"

    def test_all_costs_positive(self, atb_df):
        """Capital costs, LCOE, and capacity factors must all be positive."""
        assert (atb_df["capital_cost_per_kw"] > 0).all()
        assert (atb_df["lcoe_per_mwh"] > 0).all()
        assert (atb_df["capacity_factor"] > 0).all()
        assert (atb_df["annual_capital_per_kw_yr"] > 0).all()

    def test_capacity_factors_in_range(self, atb_df):
        """Capacity factors must be between 0 and 1."""
        assert (atb_df["capacity_factor"] > 0).all()
        assert (atb_df["capacity_factor"] < 1).all()

    def test_wacc_crf(self, atb_df):
        """CRF must be between 0 and 1."""
        assert (atb_df["crf"] > 0).all()
        assert (atb_df["crf"] < 1).all()

    def test_no_negative_costs(self, atb_df):
        cost_cols = ["capital_cost_per_kw", "fixed_om_per_kw_yr",
                     "var_om_per_mwh", "fuel_cost_per_mwh"]
        for col in cost_cols:
            assert (atb_df[col] >= 0).all(), f"Negative values in {col}"

    def test_zero_carbon_emissions(self, atb_df):
        """Solar, wind, and battery storage have zero CO₂."""
        zero_co2_techs = {"Solar PV (Utility)", "Onshore Wind", "Offshore Wind", "Battery Storage (4h)"}
        for _, row in atb_df.iterrows():
            if row["technology"] in zero_co2_techs:
                assert row["co2_kg_per_mwh"] == 0, (
                    f"{row['technology']} should have zero CO₂"
                )


class TestPriceProjections:

    @pytest.fixture(scope="class")
    def proj_df(self) -> pd.DataFrame:
        return generate_price_projections()

    def test_year_range(self, proj_df):
        assert proj_df["year"].min() == 2023
        assert proj_df["year"].max() == 2040

    def test_declining_costs(self, proj_df):
        """Solar and battery costs must decline over the projection period."""
        assert proj_df["solar_capital_per_kw"].iloc[0] > proj_df["solar_capital_per_kw"].iloc[-1]
        assert proj_df["battery_capital_per_kw"].iloc[0] > proj_df["battery_capital_per_kw"].iloc[-1]

    def test_no_negative_projections(self, proj_df):
        numeric_cols = proj_df.select_dtypes("number").columns.tolist()
        assert (proj_df[numeric_cols] > 0).all().all()
