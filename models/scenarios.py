"""
models/scenarios.py
Scenario configuration dataclasses for the NY State energy optimizer.
Separates policy scenario definitions from the solver logic.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScenarioConfig:
    """Immutable policy scenario specification."""

    name: str
    rps_target: float | None   # fraction (0–1); None when zce_mode=True
    zce_mode: bool             # True = 100% Zero-Carbon Electricity
    reserve_margin: float      # e.g. 1.15 = 115% of peak demand
    gas_allowed: bool = True   # False forces gas capacity to 0

    @classmethod
    def rps_50(cls) -> "ScenarioConfig":
        return cls(
            name="50% Renewable",
            rps_target=0.50,
            zce_mode=False,
            reserve_margin=1.15,
            gas_allowed=True,
        )

    @classmethod
    def rps_80(cls) -> "ScenarioConfig":
        return cls(
            name="80% Renewable",
            rps_target=0.80,
            zce_mode=False,
            reserve_margin=1.12,
            gas_allowed=True,
        )

    @classmethod
    def zce_100(cls) -> "ScenarioConfig":
        return cls(
            name="100% Zero-Carbon",
            rps_target=None,
            zce_mode=True,
            reserve_margin=1.10,
            gas_allowed=False,
        )

    @classmethod
    def all_scenarios(cls) -> list["ScenarioConfig"]:
        return [cls.rps_50(), cls.rps_80(), cls.zce_100()]

    @property
    def effective_rps(self) -> float:
        """Effective RPS fraction for reporting (1.0 for ZCE)."""
        return self.rps_target if self.rps_target is not None else 1.0


@dataclass
class ScenarioResult:
    """Output of the LP optimizer for a single scenario."""

    scenario_name: str
    rps_target: float
    status: str
    total_cost_b_yr: float
    lcoe_system: float
    capacity_gw: dict = field(default_factory=dict)
    generation_twh: dict = field(default_factory=dict)
    cost_breakdown_m: dict = field(default_factory=dict)
    renewable_fraction: float = 0.0
    zero_carbon_fraction: float = 0.0
    co2_mt_yr: float = 0.0
    annual_demand_twh: float = 0.0
    peak_demand_gw: float = 0.0

    @property
    def total_capacity_gw(self) -> float:
        return sum(self.capacity_gw.values())

    @property
    def total_generation_twh(self) -> float:
        return sum(self.generation_twh.values())

    @property
    def co2_reduction_pct(self) -> float:
        """CO₂ reduction vs. 2019 NY baseline (~55 Mt)."""
        from config import NY_BASELINE_CO2_MT
        return 1.0 - self.co2_mt_yr / NY_BASELINE_CO2_MT
