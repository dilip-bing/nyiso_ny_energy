"""
models/constraints.py
Modular PuLP constraint builders for the NY State least-cost energy optimizer.
Each function returns a list of (pulp_expression, constraint_name) tuples
so the caller can add them to the problem in a single loop.
"""

from __future__ import annotations
import pulp


def energy_balance(
    gen: dict[str, pulp.LpVariable],
    demand_twh: float,
) -> list[tuple]:
    """Total annual generation must meet or exceed annual demand."""
    expr = pulp.lpSum(gen[t] for t in gen)
    return [(expr >= demand_twh, "energy_balance")]


def generation_link(
    cap: dict[str, pulp.LpVariable],
    gen: dict[str, pulp.LpVariable],
    atb,
    annual_hours: int = 8760,
) -> list[tuple]:
    """
    Link installed capacity to annual generation via capacity factor.
    gen[t] = cap[t] × CF[t] × hours  (GW × fraction × h = GWh, then /1000 = TWh)
    """
    h = annual_hours / 1000  # GW × h → TWh
    return [
        (gen[t] == cap[t] * float(atb.loc[t, "capacity_factor"]) * h, f"cf_link_{i}")
        for i, t in enumerate(cap)
    ]


def rps_constraint(
    gen: dict[str, pulp.LpVariable],
    renewable_techs: frozenset,
    rps_target: float,
) -> list[tuple]:
    """
    Renewable generation share ≥ rps_target.
    Equivalent: ren_gen ≥ rps_target × total_gen
    Linearized: ren × (1 - rps) ≥ rps × non_ren
    """
    ren = pulp.lpSum(gen[t] for t in gen if t in renewable_techs)
    non_ren = pulp.lpSum(gen[t] for t in gen if t not in renewable_techs)
    return [(ren * (1 - rps_target) >= rps_target * non_ren, "rps_target")]


def zce_constraint(
    gen: dict[str, pulp.LpVariable],
    zero_carbon_techs: frozenset,
) -> list[tuple]:
    """100% ZCE: all generation must come from zero-carbon sources."""
    fossil = [t for t in gen if t not in zero_carbon_techs]
    if not fossil:
        return []
    expr = pulp.lpSum(gen[t] for t in fossil)
    return [(expr == 0, "zce_no_fossil")]


def peak_adequacy(
    cap: dict[str, pulp.LpVariable],
    required_peak_gw: float,
    capacity_credit: dict[str, float],
) -> list[tuple]:
    """
    Derated firm capacity must cover peak demand × reserve margin.
    Capacity credit reflects each technology's contribution at the system peak.
    """
    firm = pulp.lpSum(capacity_credit.get(t, 0.9) * cap[t] for t in cap)
    return [(firm >= required_peak_gw, "peak_adequacy")]


def capacity_bounds(
    cap: dict[str, pulp.LpVariable],
    limits: dict[str, dict],
) -> list[tuple]:
    """Physical and policy capacity bounds per technology (GW)."""
    constraints = []
    for t in cap:
        lims = limits.get(t, {})
        min_gw = lims.get("min_gw", 0.0)
        if min_gw > 0:
            constraints.append((cap[t] >= min_gw, f"cap_min_{t}"))
        if "max_gw" in lims:
            constraints.append((cap[t] <= lims["max_gw"], f"cap_max_{t}"))
    return constraints


def apply_constraints(prob: pulp.LpProblem, constraint_list: list[tuple]) -> None:
    """Convenience: add a list of (expression, name) tuples to a PuLP problem."""
    for expr, name in constraint_list:
        prob += expr, name
