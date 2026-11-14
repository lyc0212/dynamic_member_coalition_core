"""Independent joint execution reference for one public, fixed-action window.

This module does not import the candidate evaluator. It advances the full robot
array, keeps separate per-task ledgers, and charges one global boundary change.
The supplied trajectory is the declared public CV model, never private future.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, replace
import math

import numpy as np

from pursuit_v2.config import Config
from pursuit_v2 import observation_geometry as geometry
from pursuit_v2.service import DT, TOL, advance_clock, initial_state
from research.information_service.common import CONTRACT_ID as MEASUREMENT_CONTRACT
from research.information_service.public_quality import prepare_frame
from .common import ContractError, digest
from . import public
from .adapter import validate_flat_request, legacy_manifest, joint_identity


CONTRACT_ID = "STAGE2A5B-GQ-ONLINE-v1.0"


def _actions(raw, count, targets, cfg):
    if not isinstance(raw, (list, tuple)) or len(raw) != count:
        raise ContractError("Reference requires one Assignment per stable robot")
    result, teams = [], {j: [] for j in targets}
    for robot, action in enumerate(raw):
        if hasattr(action, "to_dict"):
            action = action.to_dict()
        if not isinstance(action, dict) or set(action) != {"target", "role"}:
            raise ContractError("Exact reference Assignment fields required")
        target, role = action["target"], action["role"]
        if target is None:
            if role != "none":
                raise ContractError("IDLE role must be none")
        else:
            if isinstance(target, bool) or not isinstance(target, int) or target not in targets:
                raise ContractError("Assignment target must be currently visible and active")
            if not isinstance(role, str):
                raise ContractError("Role must be a string")
            teams[target].append((robot, role))
        result.append(dict(target=target, role=role))
    for j, team in teams.items():
        if team and not geometry.validate_roles(targets[j]["required_robots"], [r for _, r in team], cfg):
            raise ContractError("A selected target needs its complete role-unique team")
    return result, {j: tuple(team) for j, team in teams.items()}


def _fold_components(c):
    return float((((c["completion"] + c["flow"]) + c["late"]) + c["effort"]) + c["terminal"])


def execute_joint(public_request, full_actions, sense_callback, mode="GQ", work_identity=None,
                  *, history_authority=None, unit_only=False, on_commit=None):
    """Public entry preserving the last fully committed frame on any failure."""
    cp=public_request['checkpoint']
    last = dict(tick=cp['tick'], phase="initial_uncommitted",positions=copy.deepcopy(cp['positions']),
                assignment=copy.deepcopy(cp['assignment']))

    def committed(frame):
        nonlocal last
        last = copy.deepcopy(frame)
        if on_commit is not None:
            on_commit(copy.deepcopy(frame))

    try:
        return _execute_joint(public_request, full_actions, sense_callback, mode, work_identity,
                              history_authority=history_authority, unit_only=unit_only, on_commit=committed)
    except BaseException as error:
        error.gq_last_committed = copy.deepcopy(last)
        raise


def _execute_joint(public_request, full_actions, sense_callback, mode="GQ", work_identity=None,
                   *, history_authority=None, unit_only=False, on_commit=None):
    """Execute one joint assignment under a previously admitted public request.

    ``sense_callback(frame, allowed_sensor_ids, start_tick)`` has the frozen
    public processor result contract. A KEEP branch reuses its current endpoint;
    its independent new stream starts at the next tick, not at the clock origin.
    Synthetic histories require the caller's explicit ``unit_only=True``.
    """
    source_digest = digest(public_request)
    request = validate_flat_request(public_request, history_authority=history_authority, unit_only=unit_only)
    current_slots={(s['slot_key']['target_id'],s['slot_key']['robot_id']):s for s in public_request['checkpoint']['current_slots']}
    if mode not in ("GQ", "G_ONLY"):
        raise ContractError("Unknown reference service mode")
    if mode == "GQ" and not callable(sense_callback):
        raise ContractError("GQ reference requires an explicit public sensing callback")
    cfg = Config(**request["config"])
    first, last = request["start_tick"], request["prediction_end_tick"]
    start, until = first * DT, last * DT
    episode_tick = round(cfg.end_time / DT)
    if not first < last <= episode_tick:
        raise ContractError("Invalid reference prediction window")
    positions = np.array(request["positions"], dtype=float, copy=True)
    targets = {t["id"]: copy.deepcopy(t) for t in request["targets"]}
    order = sorted(targets)
    histories = {h["target_id"]: h for h in request["gq_histories"]}
    profiles = {p["sensor_id"]: p for p in request["sensor_profiles"]}
    actions, teams = _actions(full_actions, cfg.robots, targets, cfg)
    initial_actions = copy.deepcopy(actions)
    old = request["assignment"]
    changes = sum(a != b for a, b in zip(actions, old))
    change_cost = cfg.change_cost * changes
    identity = "reference" if work_identity is None else str(work_identity)
    events, frames, sensed = [], [], []
    states = {}

    def point(target, when):
        return np.asarray(target["position_now"], dtype=float) + np.asarray(target["velocity_now"], dtype=float) * (when - start)

    def geometry_valid(j, when):
        team = teams[j]
        if not team:
            return False
        offsets = np.asarray([geometry.offset(role, cfg) for _, role in team])
        return bool(np.all(np.linalg.norm(positions[[i for i, _ in team]] - point(targets[j], when) - offsets,
                                          axis=1) <= geometry.radius(cfg)))

    for j in order:
        t, h, team = targets[j], histories[j], teams[j]
        old_clock = h["clock_state"]
        history_team = tuple((int(i), r) for i, r in old_clock["team"])
        old_team = tuple((i, a["role"]) for i, a in enumerate(old) if a["target"] == j)
        keep = bool(team and team == history_team == old_team and h["last_endpoint"] is not None)
        clock = replace(initial_state(cfg), base=old_clock["base"], intervals=old_clock["intervals"],
                        team=history_team)
        if not keep:
            if clock.progress > 0:
                events.append(dict(type="interruption", target=j, time=start, event_tick=first,
                                   reason="team_changed" if team else "withdrawn", progress_before=clock.progress))
            clock = replace(clock, base=0.0, intervals=0, team=team)
        vx = float(t["velocity_now"][0])
        distance = cfg.side - float(t["position_now"][0])
        escape = start + distance / vx if vx > 0 else math.inf
        if distance <= 0:
            escape = start
        bar = min(until, escape)
        base_flow = -cfg.flow_weight * t["weight"] * max(0.0, bar - max(start, t["birth"])) / (cfg.weight_reference * cfg.stage_dt)
        base_late = -cfg.late_weight * t["weight"] * max(0.0, bar - max(start, t["birth"], t["deadline"])) / (cfg.weight_reference * cfg.stage_dt)
        base_terminal = -cfg.unfinished_weight * t["weight"] / cfg.weight_reference if last == episode_tick else 0.0
        baseline_components = dict(completion=0.0, flow=base_flow, late=base_late, effort=0.0, terminal=base_terminal)
        first_sense_tick = first + int(keep)
        states[j] = dict(clock=clock, keep=keep, status="active", completion_time=None, completion_tick=None,
                         escape_time=None, predicted_escape=escape, escape_tick=None, effort=0.0,
                         effort_by_robot=[0.0] * cfg.robots, occupied=0.0, flow=0.0, late=0.0,
                         last_endpoint=copy.deepcopy(h["last_endpoint"]) if keep else None,
                         first_sense_tick=first_sense_tick, stream_id=f"{identity}:T{j}:first{first_sense_tick}",
                         baseline_components=baseline_components, baseline=_fold_components(baseline_components))
    if changes:
        events.append(dict(type="assignment", time=start, event_tick=first, before=copy.deepcopy(old),
                           after=copy.deepcopy(actions), changes=changes, change_cost=change_cost))

    def endpoint(j, tick):
        state, t = states[j], targets[j]
        g = geometry_valid(j, tick * DT)
        if mode == "G_ONLY":
            return dict(tick=tick, G=g, Q=None, public_payload_sha256=None)
        records = [];source_slots=[]
        target_point = point(t, tick * DT)
        allowed = [f"U{i}" for i, _ in teams[j]]
        for robot, _ in teams[j]:
            sensor = f"U{robot}"
            profile = profiles[sensor]
            slot=current_slots[(j,robot)] if tick==first else None
            observed=slot is not None and slot['state']!='UNQUERIED'
            if observed:
                outcome=slot['state'];packet=copy.deepcopy(slot['packet'])
            elif profile['health']=='missing':
                outcome='MISSING';packet=None
            else:
                outcome='VALID';p=positions[robot]
                angle=math.atan2(float(target_point[1]-p[1]),float(target_point[0]-p[0]))
                packet=dict(sensor_id=sensor,position=p.tolist(),bearing=(angle+math.pi)%(2*math.pi)-math.pi,
                    sigma=profile['sigma'],measurement_tick=tick,available_tick=tick,status='ok')
            source_slots.append(dict(slot_key=dict(target_id=j,robot_id=robot,tick=tick),
                source='OBSERVED' if observed else 'MODEL',outcome=outcome,packet=copy.deepcopy(packet),
                observed_slot_digest=slot['slot_digest'] if observed else None))
            if packet is not None:
                records.append(dict(packet,packet_id=f"{state['stream_id']}:tick{tick}:{sensor}"))
        frame = dict(contract_id=MEASUREMENT_CONTRACT, stream_id=state["stream_id"],
                     frame_id=f"{state['stream_id']}:tick{tick}", tick=tick, target_id=j,
                     measurement_time=tick * DT, available_time=tick * DT, records=records)
        prepared = prepare_frame(frame, allowed)
        sent = copy.deepcopy(frame)
        before = digest(sent)
        result = sense_callback(sent, allowed, state["first_sense_tick"])
        if digest(sent) != before:
            raise ContractError("Reference callback mutated its public frame")
        if not isinstance(result, dict):
            raise ContractError("Sensing result must be a mapping")
        for key in ("frame_id", "stream_id", "target_id", "tick"):
            if result.get(key) != frame[key]:
                raise ContractError("Reference received a mismatched endpoint identity")
        quality = result.get("quality", {})
        if (quality.get("status") not in ("PASS", "FAIL", "UNKNOWN") or
                result.get("payload_sha256") != prepared["payload_sha256"] or
                quality.get("payload_sha256") != prepared["payload_sha256"]):
            raise ContractError("Reference received invalid public quality/payload identity")
        sensed.append(dict(frame=frame, allowed_sensor_ids=allowed, start_tick=state["first_sense_tick"],
                           result=copy.deepcopy(result),source_slots=source_slots))
        return dict(tick=tick, G=g, Q=quality["status"], public_payload_sha256=prepared["payload_sha256"])

    def finish(j, kind, when, tick):
        state = states[j]
        if state["status"] != "active":
            raise ContractError("Repeated reference task termination")
        state["status"] = kind
        if kind == "completed":
            state["completion_time"], state["completion_tick"] = when, tick
        elif kind == "escaped":
            state["escape_time"], state["escape_tick"] = when, tick
        event_kind = "completion" if kind == "completed" else "escape" if kind == "escaped" else kind
        events.append(dict(type=event_kind, target=j,
                           time=when, event_tick=tick, progress=state["clock"].progress))
        occupied = [i for i, a in enumerate(actions) if a["target"] == j]
        if occupied:
            for i in occupied:
                actions[i] = dict(target=None, role="none")
            events.append(dict(type="release", target=j, time=when, event_tick=tick,
                               robots=occupied, reason=kind, virtual=False, change_cost=0.0))

    def record(tick, phase, controls, elapsed, before_positions):
        frames.append(dict(tick=tick, time=tick * DT, phase=phase,
            positions_start=before_positions.tolist(), positions=positions.tolist(),
            control=controls.tolist(), control_elapsed_by_robot=list(elapsed), assignment=copy.deepcopy(actions),
            progress={str(j): states[j]["clock"].progress for j in order},
            clock_states={str(j): asdict(states[j]["clock"]) for j in order},
            status={str(j): states[j]["status"] for j in order},
            G={str(j): states[j]["last_endpoint"]["G"] for j in order if states[j]["last_endpoint"] is not None
               and states[j]["last_endpoint"]["tick"] == tick},
            Q={str(j): states[j]["last_endpoint"]["Q"] for j in order if states[j]["last_endpoint"] is not None
               and states[j]["last_endpoint"]["tick"] == tick},
            ledger={str(j): dict(flow=states[j]["flow"], late=states[j]["late"], effort=states[j]["effort"],
                                occupied_robot_seconds=states[j]["occupied"]) for j in order}))
        if on_commit is not None:
            on_commit(copy.deepcopy(frames[-1]))

    for j in order:
        state = states[j]
        if state["predicted_escape"] <= start + TOL:
            finish(j, "escaped", state["predicted_escape"], first)
        elif teams[j]:
            if not state["keep"]:
                state["last_endpoint"] = endpoint(j, first)
            else:
                if state["last_endpoint"]["G"] != geometry_valid(j, start):
                    raise ContractError("Admitted KEEP endpoint disagrees with the current geometry")
                if mode == "G_ONLY":
                    state["last_endpoint"]["Q"] = None
    record(first, "boundary", np.zeros_like(positions), [0.0] * cfg.robots, positions.copy())

    for tick in range(first + 1, last + 1):
        lo, hi = (tick - 1) * DT, tick * DT
        before_positions = positions.copy()
        controls = np.zeros_like(positions)
        elapsed_by_robot = [0.0] * cfg.robots
        for j in order:
            state, t, team = states[j], targets[j], teams[j]
            if state["status"] != "active":
                continue
            stop = min(hi, state["predicted_escape"])
            elapsed = max(0.0, stop - lo)
            state["flow"] += max(0.0, stop - max(lo, t["birth"]))
            state["late"] += max(0.0, stop - max(lo, t["birth"], t["deadline"]))
            if team:
                robot_ids = [i for i, _ in team]
                offsets = np.asarray([geometry.offset(role, cfg) for _, role in team])
                command = np.asarray(t["velocity_now"]) + cfg.travel_gain * (point(t, lo) + offsets - positions[robot_ids])
                speeds = np.linalg.norm(command, axis=1)
                command *= np.minimum(1.0, cfg.max_speed / np.maximum(speeds, 1e-15))[:, None]
                positions[robot_ids] += command * elapsed
                controls[robot_ids] = command
                state["effort"] += float(np.sum(command ** 2)) * elapsed
                state["occupied"] += len(team) * elapsed
                for k, robot in enumerate(robot_ids):
                    state["effort_by_robot"][robot] += float(np.sum(command[k] ** 2)) * elapsed
                    elapsed_by_robot[robot] = elapsed
            if state["predicted_escape"] <= hi + TOL:
                at = state["predicted_escape"]
                event_tick = round(at / DT) if math.isclose(at, round(at / DT) * DT, rel_tol=0.0, abs_tol=TOL) else None
                finish(j, "escaped", at, event_tick)
                continue
            if team:
                left = state["last_endpoint"]
                right = endpoint(j, tick)
                valid = left["G"] and right["G"] and (mode == "G_ONLY" or (left["Q"] == right["Q"] == "PASS"))
                state["clock"], done, interruptions = advance_clock(state["clock"], t["service_duration"], team, valid, hi)
                events.extend(dict(event, type="interruption", target=j) for event in interruptions)
                state["last_endpoint"] = right
                if done:
                    finish(j, "completed", hi, tick)
        if tick == episode_tick:
            for j in order:
                if states[j]["status"] == "active":
                    finish(j, "unfinished", hi, tick)
        record(tick, "physical", controls, elapsed_by_robot, before_positions)

    per_target, components = {}, {k: 0.0 for k in ("completion", "flow", "late", "effort", "terminal")}
    B64 = 0.0
    for j in order:
        state, t = states[j], targets[j]
        c = dict(completion=t["weight"] / cfg.weight_reference if state["status"] == "completed" else 0.0,
                 flow=-cfg.flow_weight * t["weight"] * state["flow"] / (cfg.weight_reference * cfg.stage_dt),
                 late=-cfg.late_weight * t["weight"] * state["late"] / (cfg.weight_reference * cfg.stage_dt),
                 effort=-cfg.control_weight * state["effort"] / cfg.effort_reference,
                 terminal=-cfg.unfinished_weight * t["weight"] / cfg.weight_reference
                 if last == episode_tick and state["status"] != "completed" else 0.0)
        absolute = _fold_components(c)
        per_target[str(j)] = dict(target=j, status=state["status"],
            termination_reason="horizon_truncated" if state["status"] == "active" else
                        "episode_end" if state["status"] == "unfinished" else state["status"],
            completion_time=state["completion_time"], completion_tick=state["completion_tick"],
            escape_time=state["escape_time"], escape_tick=state["escape_tick"],
            clock_state=asdict(state["clock"]), final_progress=state["clock"].progress,
            selected_team=[list(pair) for pair in teams[j]], kept_history=state["keep"],
            last_endpoint=state["last_endpoint"], components=c, absolute_O=absolute,
            baseline_components=state["baseline_components"], baseline=state["baseline"],
            v=float(absolute - state["baseline"]), control_integral=state["effort"],
            effort_by_robot=state["effort_by_robot"], occupied_robot_seconds=state["occupied"],
            flow_raw=state["flow"], late_raw=state["late"])
        B64 += state["baseline"]
        for key in components:
            components[key] += c[key]
    physical = sum(per_target[str(j)]["absolute_O"] for j in order)
    occupied = sum(states[j]["occupied"] for j in order)
    metrics = dict(components=components, physical_O=physical, B64=B64, change_cost=change_cost,
                   assignment_changes=changes, net_O=physical - change_cost,
                   control_integral=sum(states[j]["effort"] for j in order), occupied_robot_seconds=occupied,
                   idle_robot_seconds=cfg.robots * (until - start) - occupied,
                   measurement_requests=len(sensed),
                   reported_estimator_calls=sum(row["result"].get("estimator_called") is True for row in sensed))
    if digest(public_request) != source_digest:
        raise ContractError("Reference execution mutated its source request")
    manifest = legacy_manifest(public_request, history_authority=history_authority, unit_only=unit_only)
    selected_keys = [dict(target=j, robots=[i for i, _ in teams[j]], roles=[r for _, r in teams[j]])
                     for j in order if teams[j]]
    candidate_id = None
    if len(selected_keys) == 1:
        candidate_id = next(c["candidate_identity"] for c in manifest["candidates"]
                            if c["structural_key"] == selected_keys[0])
    return dict(contract_id=CONTRACT_ID, implementation="independent_joint_reference_v1", mode=mode,
                request_identity=manifest["request_identity"], world_identity=manifest["world_identity"],
                candidate_identity=candidate_id,
                joint_identity=joint_identity(public_request, initial_actions, history_authority=history_authority,
                                              unit_only=unit_only),
                start_tick=first, end_tick=last, initial_actions=initial_actions,
                assignment_changes=changes, change_cost=change_cost, frames=frames, events=events,
                per_target=per_target, metrics=metrics, final_positions=positions.tolist(),
                final_assignment=copy.deepcopy(actions), sensing_results=sensed,
                scope="public nominal frozen window; no mid-window reassignment or post-completion reuse")
