"""Exact dyadic set-packing DP; the binary64 input table defines the objective."""
from __future__ import annotations

import math
from pursuit_v2.types import Assignment, IDLE

EXPONENT = 1074
SCALE = 1 << EXPONENT


def units(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Non-finite numerical objective')
    numerator, denominator = value.as_integer_ratio()
    return numerator << (EXPONENT-(denominator.bit_length()-1))


def display(value, direction=0):
    result = value/SCALE
    if direction < 0 and units(result) > value:
        result = math.nextafter(result, -math.inf)
    if direction > 0 and units(result) < value:
        result = math.nextafter(result, math.inf)
    return result


def baseline(obs):
    return -units(obs.config.change_cost)*sum(a != IDLE for a in obs.assignment)


def profit(obs, spec, value):
    delta = sum(int(obs.assignment[k] != IDLE)-
                int(obs.assignment[k] != Assignment(spec.target, role))
                for k, role in zip(spec.robots, spec.roles))
    return units(value)+units(obs.config.change_cost)*delta


def objective(obs, specs, values, selected):
    return baseline(obs)+sum(profit(obs, specs[i], values[i]) for i in selected)


def solve(obs, specs, values):
    """None means unavailable to the feasible lower-bound solver, not deletion."""
    groups = {}
    for spec in specs:
        groups.setdefault(spec.target, []).append(spec)
    dp = {0: (baseline(obs), ())}
    for target in sorted(groups):
        previous = dp
        dp = previous.copy()
        for spec in groups[target]:
            value = values[spec.index]
            if value is None:
                continue
            p = profit(obs, spec, value)
            if p <= 0:
                continue
            for mask, (score, selected) in previous.items():
                if mask & spec.mask:
                    continue
                destination = mask | spec.mask
                new = score+p
                if destination not in dp or new > dp[destination][0]:
                    dp[destination] = new, selected+(spec.index,)
    best_mask = min(dp, key=lambda mask: (-dp[mask][0], mask))
    return dp[best_mask][1], dp[best_mask][0]

