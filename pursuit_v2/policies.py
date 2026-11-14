from __future__ import annotations

from pursuit_v2.service import reject_service

from dataclasses import dataclass
from time import perf_counter
import numpy as np

from .allocation import allocate
from .types import IDLE, Observation, complete_roles, role_offset
from .physics import rollout_target
from .risk import assess_options, risk_horizon, travel_certificate


@dataclass(frozen=True)
class Decision:
    assignment: tuple
    log: dict


def forecast_risk(obs: Observation):
    reject_service(obs.config)
    reasons = []
    horizon = min(obs.config.prediction_stages, obs.config.max_stages - obs.stage)
    for target in obs.targets:
        robots = [k for k, a in enumerate(obs.assignment) if a.target == target.id]
        if not robots:
            continue
        roles = [obs.assignment[k].role for k in robots]
        if not complete_roles(target, roles):
            reasons.append(f"incomplete_coalition:{target.id}")
            continue
        result = rollout_target(
            obs.config, target, obs.positions[robots][None],
            np.array([role_offset(r, obs.config) for r in roles])[None],
            np.ones(1, dtype=bool), obs.time, horizon)
        if np.isfinite(result.escape_times[0]) and not np.isfinite(result.capture_times[0]):
            reasons.append(f"predicted_escape:{target.id}")
    return reasons


def incumbent_risks(obs: Observation):
    reject_service(obs.config)
    reports, risky = [], []
    for target in obs.targets:
        group = tuple(k for k, a in enumerate(obs.assignment) if a.target == target.id)
        if not group:
            continue
        roles = tuple(obs.assignment[k].role for k in group)
        if not complete_roles(target, roles):
            reports.append({"target": target.id, "probability": 0.0, "complete": False})
            risky.append(target.id)
            continue
        certificate = travel_certificate(obs, target, group, roles)
        if certificate["certified_on_time"] or (target.deadline < obs.time and
                                                 certificate["certified_next_check"]):
            reports.append({"target": target.id, "probability": 1.0,
                            "complete": True, "certified": True,
                            "estimate": {"on_time_probability": float(
                                certificate["certified_on_time"])}})
            continue
        estimate = assess_options(obs, target, [(group, roles)], risk_horizon(obs, target),
                                  samples=obs.config.risk_trigger_samples)[0]
        probability = (estimate["on_time_probability"] if target.deadline >= obs.time
                       else estimate["completion_probability"])
        reports.append({"target": target.id, "probability": probability,
                        "complete": True, "estimate": estimate})
        if probability < obs.config.risk_threshold:
            risky.append(target.id)
    return reports, tuple(risky)


def local_scope(obs: Observation, risky_targets):
    """One-hop closure: replacement robots bring their incumbent task and partners."""
    ids = set(risky_targets)
    available = {k for k, a in enumerate(obs.assignment) if a.target in ids}
    for target in obs.targets:
        if target.id not in ids:
            continue
        point = target.position(obs.time)
        ranked = sorted((float(np.linalg.norm(obs.positions[k] - point)), k)
                        for k in range(obs.config.robots) if k not in available)
        for _, k in ranked[:obs.config.local_substitutes]:
            available.add(k)
            original = obs.assignment[k].target
            if original is not None:
                ids.add(original)
                available.update(j for j, a in enumerate(obs.assignment) if a.target == original)
    excluded = tuple(t.id for t in obs.targets if t.id not in ids)
    return tuple(sorted(available)), excluded


class Policy:
    def __init__(self, mode: str, solver: str = "exact"):
        if mode not in ("fixed", "periodic", "event", "risk_periodic", "risk_event",
                        "risk_local"):
            raise ValueError("Unknown policy mode")
        self.mode = mode
        self.solver = solver
        self.local_mode = mode == "risk_local"
        self.last_replan_stage = -10**9
        self.last_global_fallback_stage = -10**9

    def decide(self, obs: Observation) -> Decision:
        reject_service(obs.config)
        start = perf_counter()
        reasons = []
        available = None
        excluded = ()
        risk_checked = False
        risk_mode = self.mode.startswith("risk_")
        reports, risky = [], ()
        if not obs.targets:
            return Decision((IDLE,) * obs.config.robots,
                            {"replanned": False, "reasons": ["no_active_tasks"],
                             "candidate_count": 0, "selected": [], "prediction_seconds": 0.0,
                             "solver_seconds": 0.0, "trigger_seconds": 0.0,
                             "decision_seconds": perf_counter() - start, "risk_checked": False})
        if self.mode == "fixed":
            # Nonpreemptive: retain all live jobs; dispatch only idle/released robots.
            available = tuple(k for k, a in enumerate(obs.assignment) if a == IDLE)
            excluded = tuple({a.target for a in obs.assignment if a.target is not None})
            if available and any(t.id not in excluded for t in obs.targets):
                reasons.append("dispatch_free_robots")
        elif self.mode in ("periodic", "risk_periodic"):
            reasons.append("periodic_boundary")
        else:
            if obs.stage == 0 and obs.time == 0:
                reasons.append("initial")
            if obs.new_ids:
                reasons.append("birth")
            if obs.ended_ids:
                reasons.append("task_ended")
            if obs.stage - self.last_replan_stage >= obs.config.max_plan_age:
                reasons.append("max_plan_age")
            if not reasons:
                risk_checked = True
                if risk_mode:
                    reports, risky = incumbent_risks(obs)
                    reasons.extend(f"low_joint_success:{i}" for i in risky)
                else:
                    reasons.extend(forecast_risk(obs))
        triggered = perf_counter()
        log = {"replanned": bool(reasons), "reasons": reasons or ["maintain"],
               "trigger_seconds": triggered - start, "risk_checked": risk_checked,
               "incumbent_risks": reports}
        if reasons:
            if self.local_mode and risky and all(r.startswith("low_joint_success:")
                                                 for r in reasons):
                available, excluded = local_scope(obs, risky)
                actions, allocation_log = allocate(obs, self.solver, available, excluded,
                                                   risk=True)
                log["repair_scope"] = {"robots": available,
                                       "targets": [t.id for t in obs.targets
                                                   if t.id not in excluded]}
                selected = {c["target"]: c for c in allocation_log["selected"]}
                missing_risky = any(i not in selected for i in risky)
                legacy_fallback = (self.last_global_fallback_stage != obs.stage and
                                   len(available) < obs.config.robots and missing_risky)
                if legacy_fallback:
                    local_log = allocation_log
                    global_actions, global_log = allocate(obs, self.solver, risk=True)
                    gain = (global_log["candidate_objective"] -
                            local_log["candidate_objective"])
                    accept = legacy_fallback or gain > obs.config.change_cost + 1e-12
                    log["scope_screen_gain"] = gain
                    log["scope_screen_margin"] = obs.config.change_cost
                    log["scope_screen_accepted"] = bool(accept)
                    if accept:
                        actions, allocation_log = global_actions, global_log
                        log["fallback_global"] = True
                        log["fallback_reason"] = ("legacy_missing_risky" if legacy_fallback
                                                  else "excluded_target_value")
                        self.last_global_fallback_stage = obs.stage
                    other_log = local_log if accept else global_log
                    allocation_log["candidate_count"] += other_log["candidate_count"]
                    allocation_log["prediction_seconds"] += other_log["prediction_seconds"]
                    allocation_log["solver_seconds"] += other_log["solver_seconds"]
            else:
                actions, allocation_log = allocate(obs, self.solver, available, excluded,
                                                   risk=risk_mode)
            log.update(allocation_log)
            self.last_replan_stage = obs.stage
        else:
            actions = obs.assignment
            log.update({"candidate_count": 0, "selected": [], "prediction_seconds": 0.0,
                        "solver_seconds": 0.0, "solver": self.solver})
        log["decision_seconds"] = perf_counter() - start
        return Decision(actions, log)
