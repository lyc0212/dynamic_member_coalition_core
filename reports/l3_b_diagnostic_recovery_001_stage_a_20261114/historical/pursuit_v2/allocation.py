from __future__ import annotations

from pursuit_v2.service import reject_service

from dataclasses import dataclass
from itertools import combinations
from time import perf_counter
import math
import numpy as np

from .config import Config
from .types import Assignment, IDLE, Observation, role_offset
from .physics import candidate_benefit, rollout_target
from .risk import assess_options, risk_horizon


@dataclass(frozen=True)
class Candidate:
    target: int
    robots: tuple[int, ...]
    roles: tuple[str, ...]
    benefit: float
    capture_time: float | None = None
    first_commit_time: float | None = None
    effort: float = 0.0
    guard_peaks: tuple[float, ...] = ()
    on_time_probability: float | None = None
    completion_probability: float | None = None
    partner_wait: float = 0.0
    certified_next_check: bool = False
    certified_on_time: bool = False
    speed_margin: float | None = None
    endpoint_margin: float | None = None
    escape_margin: float | None = None
    capture_time_upper_bound: float | None = None

    @property
    def mask(self):
        return sum(1 << k for k in self.robots)

    def to_dict(self):
        result = {"target": self.target, "robots": self.robots, "roles": self.roles,
                "benefit": self.benefit, "capture_time": self.capture_time,
                "first_commit_time": self.first_commit_time, "effort": self.effort,
                "guard_peaks": self.guard_peaks, "on_time_probability": self.on_time_probability,
                "completion_probability": self.completion_probability,
                "partner_wait": self.partner_wait,
                "certified_next_check": self.certified_next_check,
                "certified_on_time": self.certified_on_time,
                "speed_margin": self.speed_margin,
                "endpoint_margin": self.endpoint_margin,
                 "escape_margin": self.escape_margin}
        if self.capture_time_upper_bound is not None:
            result["capture_time_upper_bound"] = self.capture_time_upper_bound
        return result


def _nullable(value):
    return float(value) if math.isfinite(value) else None


def enumerate_candidates(obs: Observation, available=None, excluded_targets=()):
    reject_service(obs.config)
    cfg = obs.config
    available = tuple(range(cfg.robots) if available is None else available)
    horizon = min(cfg.prediction_stages, cfg.max_stages - obs.stage)
    if horizon <= 0:
        return []
    candidates = []
    for target in obs.targets:
        if target.id in excluded_targets:
            continue
        options = []
        for group in combinations(available, target.required_robots):
            for roles in ((("center",),) if target.required_robots == 1
                          else (("upper", "lower"), ("lower", "upper"))):
                options.append((group, roles))
        if not options:
            continue
        positions = np.array([obs.positions[list(group)] for group, _ in options])
        offsets = np.array([[role_offset(role, cfg) for role in roles] for _, roles in options])
        prediction = rollout_target(cfg, target, positions, offsets,
                                    np.ones(len(options), dtype=bool), obs.time, horizon)
        benefits = candidate_benefit(cfg, target, prediction, obs.time, horizon)
        for i, (group, roles) in enumerate(options):
            candidates.append(Candidate(
                target.id, tuple(group), tuple(roles), float(benefits[i]),
                _nullable(prediction.capture_times[i]), _nullable(prediction.first_commit_times[i]),
                float(prediction.effort[i]), tuple(map(float, prediction.stages[0]["guard_peaks"][i]))))
    return candidates


def enumerate_risk_candidates(obs: Observation, available=None, excluded_targets=()):
    reject_service(obs.config)
    cfg = obs.config
    available = tuple(range(cfg.robots) if available is None else available)
    candidates = []
    for target in obs.targets:
        if target.id in excluded_targets:
            continue
        options = []
        for group in combinations(available, target.required_robots):
            rolesets = (("center",),) if target.required_robots == 1 else (
                ("upper", "lower"), ("lower", "upper"))
            options.extend((tuple(group), roles) for roles in rolesets)
        horizon = risk_horizon(obs, target)
        for (group, roles), estimate in zip(options, assess_options(obs, target, options, horizon)):
            candidates.append(Candidate(target.id, group, roles, estimate["benefit"],
                                        estimate["capture_time"], None, estimate["effort"], (),
                                        estimate["on_time_probability"],
                                        estimate["completion_probability"],
                                        estimate["partner_wait"],
                                        estimate["certified_next_check"],
                                        estimate["certified_on_time"],
                                        estimate["speed_margin"],
                                        estimate["endpoint_margin"],
                                        estimate["escape_margin"],
                                        capture_time_upper_bound=estimate.get(
                                            "capture_time_upper_bound")))
    return candidates


def solve_candidates(cfg: Config, candidates: list[Candidate], old: tuple[Assignment, ...],
                     available=None, solver="exact"):
    """Exact bitmask DP for the candidate set-packing problem, or a greedy baseline.

    This is optimal only for the supplied finite-horizon candidate table.
    It is not an episode-level upper bound or a clairvoyant scheduler.
    """
    reject_service(cfg)
    available = tuple(range(cfg.robots) if available is None else available)
    available_set = set(available)
    baseline = -cfg.change_cost * sum(old[k] != IDLE for k in available)
    profits = []
    for candidate in candidates:
        if not set(candidate.robots) <= available_set:
            raise ValueError("Candidate consumes a locked robot")
        delta = sum(int(old[k] != IDLE) - int(old[k] != Assignment(candidate.target, role))
                    for k, role in zip(candidate.robots, candidate.roles))
        profits.append(candidate.benefit + cfg.change_cost * delta)

    if solver == "greedy":
        used_mask, used_targets, chosen = 0, set(), []
        for i in sorted(range(len(candidates)), key=lambda i: (-profits[i], i)):
            c = candidates[i]
            if profits[i] > 1e-12 and not c.mask & used_mask and c.target not in used_targets:
                chosen.append(i)
                used_mask |= c.mask
                used_targets.add(c.target)
        return chosen, float(baseline + sum(profits[i] for i in chosen))
    if solver != "exact":
        raise ValueError("solver must be exact or greedy")

    masks = np.arange(1 << cfg.robots, dtype=np.int64)
    dp = np.full(len(masks), -np.inf)
    dp[0] = baseline
    groups = {}
    for i, candidate in enumerate(candidates):
        groups.setdefault(candidate.target, []).append(i)
    parents = []
    for target in sorted(groups):
        previous = dp
        dp = previous.copy()
        parent_mask = masks.copy()
        choices = np.full(len(masks), -1, dtype=int)
        for i in groups[target]:
            if profits[i] <= 1e-12:
                continue
            bitmask = candidates[i].mask
            source = masks[((masks & bitmask) == 0) & np.isfinite(previous)]
            destination = source | bitmask
            values = previous[source] + profits[i]
            improve = values > dp[destination] + 1e-12
            dst = destination[improve]
            dp[dst] = values[improve]
            parent_mask[dst] = source[improve]
            choices[dst] = i
        parents.append((parent_mask, choices))
    current = int(np.argmax(dp))
    objective = float(dp[current])
    selected = []
    for parent_mask, choices in reversed(parents):
        choice = int(choices[current])
        if choice >= 0:
            selected.append(choice)
        current = int(parent_mask[current])
    return list(reversed(selected)), objective


def allocate(obs: Observation, solver="exact", available=None, excluded_targets=(), risk=False):
    reject_service(obs.config)
    cfg = obs.config
    available = tuple(range(cfg.robots) if available is None else available)
    start = perf_counter()
    candidates = (enumerate_risk_candidates if risk else enumerate_candidates)(
        obs, available, excluded_targets)
    predicted = perf_counter()
    chosen, objective = solve_candidates(cfg, candidates, obs.assignment, available, solver)
    solved = perf_counter()
    actions = list(obs.assignment)
    for k in available:
        actions[k] = IDLE
    for i in chosen:
        candidate = candidates[i]
        for k, role in zip(candidate.robots, candidate.roles):
            actions[k] = Assignment(candidate.target, role)
    return tuple(actions), {
        "candidate_count": len(candidates), "selected": [candidates[i].to_dict() for i in chosen],
        "prediction_seconds": predicted - start, "solver_seconds": solved - predicted,
        "candidate_objective": objective, "solver": solver,
    }
