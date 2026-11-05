"""Private actual GQ execution, persistent sampling, and public committed cuts.

Only this side reads the actual target/declaration schedules. Prediction outputs
are never accepted as positions, measurements, clocks, or terminal states.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import math

import numpy as np

from pursuit_v2.config import Config
from pursuit_v2.environment import Environment
from pursuit_v2.types import Scenario, Target
from pursuit_v2 import observation_geometry as geometry
from pursuit_v2.service import advance_clock, initial_state, TOL
from research.information_service.common import CONTRACT_ID as MEASUREMENT_ID
from research.information_service.public_quality import prepare_frame
from .common import CONTRACT_ID, DT, ContractError, digest
from . import public, measurements


def _point(when):
    tick = round(when / DT)
    return dict(time_seconds=float(when), event_tick=tick if abs(tick * DT - when) <= TOL else None)


def _zero(team=()):
    return dict(base=0.0, intervals=0, team=deepcopy(list(team)))


def _progress(clock):
    return math.fsum((clock["base"], clock["intervals"] * DT))


class ActualMeasurementCache:
    """First actual outcome per environment/target/Uk/tick; no retry sampling."""

    def __init__(self, physical_environment_id, restored=None):
        self.physical_environment_id = str(physical_environment_id)
        self.entries = {}
        self.attempts = []
        self.requests = 0
        self.reuses = 0
        # Runtime durability hook; excluded from snapshots and scientific identity.
        self.on_change = None
        if restored is not None:
            if restored["physical_environment_id"] != self.physical_environment_id:
                raise ContractError("Raw measurement cache belongs to another physical environment")
            for row in restored["entries"]:
                key = tuple(row["raw_key"])
                if len(key) != 4 or key[0] != self.physical_environment_id:
                    raise ContractError("Malformed or foreign restored raw key")
                self._key(key[1], key[2], key[3])
                if key in self.entries:
                    raise ContractError("Duplicate or foreign restored raw slot")
                if (row["slot"]["state"] not in ("VALID", "MISSING") or
                        row["slot"]["slot_key"] != dict(target_id=key[1], robot_id=key[2], tick=key[3])):
                    raise ContractError("A restored acquired outcome must match its raw key")
                if public.seal_slot(row["slot"]) != row["slot"]:
                    raise ContractError("Restored raw slot identity changed")
                self.entries[key] = deepcopy(row)
            self.attempts = deepcopy(restored["attempts"])
            self.requests, self.reuses = restored["requests"], restored["reuses"]

    def _emit(self):
        if self.on_change is not None:
            self.on_change(self.snapshot())

    def _key(self, target, robot, tick):
        if any(type(x) is not int or x < 0 for x in (target, robot, tick)):
            raise ContractError("Raw measurement indices must be nonnegative integers")
        return self.physical_environment_id, target, robot, tick

    def peek(self, target, robot, tick):
        key = self._key(target, robot, tick)
        if key in self.entries:
            return deepcopy(self.entries[key]["slot"])
        return public.seal_slot(dict(slot_key=dict(target_id=target, robot_id=robot, tick=tick),
                                     state="UNQUERIED", packet=None, slot_digest=None))

    def query(self, target, robot, tick, context, producer):
        """A private sampler calls producer only for a previously unqueried key.

        Context binds current physical position and declaration. A second query
        with conflicting context fails rather than drawing a replacement packet.
        """
        key = self._key(target, robot, tick)
        context_id = digest(context)
        self.requests += 1
        if key in self.entries:
            if self.entries[key]["context_digest"] != context_id:
                raise ContractError("Conflicting position/declaration for the same raw measurement key")
            self.reuses += 1
            self._emit()
            return deepcopy(self.entries[key]["slot"])
        attempt = dict(raw_key=list(key), context_digest=context_id, outcome="STARTED")
        self.attempts.append(attempt)
        self._emit()
        try:
            outcome = producer()
            slot = self.record_outcome(target, robot, tick, context, outcome)
            attempt["outcome"] = slot["state"]
            attempt["slot_digest"] = slot["slot_digest"]
        except BaseException as error:
            attempt.update(outcome="ERROR", error_type=type(error).__name__, error=str(error))
            self._emit()
            raise
        self._emit()
        return deepcopy(slot)

    def record_outcome(self, target, robot, tick, context, outcome):
        """Admit an already acquired result; identical keys cannot change value."""
        key = self._key(target, robot, tick)
        if not isinstance(outcome, dict) or set(outcome) != {"state", "packet"}:
            raise ContractError("Sampler must return a VALID packet or explicit MISSING")
        if outcome["state"] not in ("VALID", "MISSING"):
            raise ContractError("INVALID/transport errors are not accepted raw outcomes")
        slot = public.seal_slot(dict(slot_key=dict(target_id=target, robot_id=robot, tick=tick),
                                    state=outcome["state"], packet=deepcopy(outcome["packet"])))
        if slot["state"] == "VALID":
            p = slot["packet"]
            if (p["sensor_id"] != f"U{robot}" or p["measurement_tick"] != tick or
                    p["available_tick"] != tick or p["position"] != context["position"] or
                    p["sigma"] != context["sigma"] or context["health"] != "available"):
                raise ContractError("Actual packet conflicts with its physical key or declaration")
        row = dict(raw_key=list(key), context_digest=digest(context), slot=slot)
        if key in self.entries:
            if self.entries[key] != row:
                raise ContractError("A known actual slot cannot change bearing, availability, or context")
            return deepcopy(self.entries[key]["slot"])
        self.entries[key] = deepcopy(row)
        return deepcopy(slot)

    get = peek

    def snapshot(self):
        return dict(physical_environment_id=self.physical_environment_id,
                    entries=[deepcopy(self.entries[key]) for key in sorted(self.entries)],
                    attempts=deepcopy(self.attempts), requests=self.requests, reuses=self.reuses)


RawMeasurementCache = ActualMeasurementCache


class RequestJournal:
    """Successful replay precedes current-version checks; pending deadlines persist."""
    def __init__(self, restored=None):
        self.successful = {} if restored is None else deepcopy(restored["successful"])
        self.inflight = None if restored is None else deepcopy(restored["inflight"])

    def lookup(self, request_id, fingerprint):
        if request_id in self.successful:
            row = self.successful[request_id]
            return (dict(state="REPLAY", result=deepcopy(row["result"])) if row["fingerprint"] == fingerprint
                    else dict(state="REJECTED", reason="REQUEST_ID_CONFLICT"))
        if self.inflight is not None:
            if self.inflight["request_id"] != request_id:
                return dict(state="REJECTED", reason="BUSY")
            if self.inflight["fingerprint"] != fingerprint:
                return dict(state="REJECTED", reason="REQUEST_ID_CONFLICT")
            return dict(state="IN_PROGRESS", request_fingerprint=fingerprint,
                        deadline_wall=self.inflight["deadline_wall"], new_transaction_started=False, deadline_extended=False)
        return None

    def begin(self, request_id, fingerprint, now_wall=None, timeout_seconds=None):
        existing = self.lookup(request_id, fingerprint)
        if existing is not None:
            return existing
        if (now_wall is None) != (timeout_seconds is None):
            raise ContractError("Journal deadline needs both origin and duration")
        deadline = None if now_wall is None else float(now_wall) + float(timeout_seconds)
        if deadline is not None and (not math.isfinite(deadline) or timeout_seconds <= 0):
            raise ContractError("Invalid fixed request deadline")
        self.inflight = dict(request_id=request_id, fingerprint=fingerprint, deadline_wall=deadline)
        return dict(state="STARTED", deadline_wall=deadline)

    def check_deadline(self, now):
        if self.inflight is not None and self.inflight["deadline_wall"] is not None and now >= self.inflight["deadline_wall"]:
            raise TimeoutError("REQUEST_TIMEOUT")

    def commit(self, result):
        if self.inflight is None:
            raise ContractError("No pending request to commit")
        row = self.inflight
        self.successful[row["request_id"]] = dict(fingerprint=row["fingerprint"], result=deepcopy(result))
        self.inflight = None

    def abort(self):
        self.inflight = None

    def snapshot(self):
        return dict(successful=deepcopy(self.successful), inflight=deepcopy(self.inflight))


class BoundaryTransaction:
    """Prepare on a private copy; raw sampling outside that copy remains logged."""
    def __init__(self, state):
        self.source = state
        self.source_digest = digest(state)
        self.prepared = None
        self.failed = self.committed = False

    def prepare(self, mutator):
        if self.prepared is not None or self.failed or self.committed:
            raise ContractError("Boundary preparation cannot restart")
        draft = deepcopy(self.source)
        try:
            payload = mutator(draft)
            if digest(self.source) != self.source_digest:
                raise ContractError("Boundary preparation changed committed state")
            self.prepared = draft, deepcopy(payload)
            return deepcopy(payload)
        except BaseException:
            self.failed = True
            raise

    def commit(self):
        if self.failed or self.committed or self.prepared is None:
            raise ContractError("Only one successfully prepared boundary can commit")
        if digest(self.source) != self.source_digest:
            raise ContractError("Committed source changed during boundary preparation")
        self.committed = True
        return deepcopy(self.prepared)


def apply_assignment_boundary(state, actions, kappa):
    """One direct per-robot charge, used by the actual prepared transaction."""
    changes = sum(a != b for a, b in zip(state["assignment"], actions))
    cost = float(kappa * changes)
    state["assignment"] = deepcopy(actions)
    state["changes"] += changes
    state["change_cost"] += cost
    return dict(assignment_changes=changes, change_cost=cost)


def legal_decision_ticks(start, end_exclusive, period=20):
    if any(type(v) is not int for v in (start, end_exclusive, period)) or period <= 0 or start % period:
        raise ContractError("Legal decision range needs integer aligned endpoints")
    return list(range(start, end_exclusive, period))


def collect_interval_events(events, lo_exclusive, hi_inclusive):
    """Collect all births/ends in a decision interval, not merely its last frame."""
    ended, born = [], []
    for event in events:
        when = event["at"]["time_seconds"]
        if not lo_exclusive * DT < when <= hi_inclusive * DT + TOL:
            continue
        target = event["target_id"]
        if event["kind"] == "BIRTH" and target not in born:
            born.append(target)
        if event["kind"] in ("COMPLETED", "ESCAPED", "EPISODE_ENDED") and target not in ended:
            ended.append(target)
    return ended, born


def release_assignment(actions, target):
    robots = [i for i, action in enumerate(actions) if action["target"] == target]
    return ([dict(target=None, role="none") if a["target"] == target else deepcopy(a) for a in actions], robots)


def settle_terminal_once(state, cfg, weights):
    """Only the true episode-end caller invokes this idempotent ledger operation."""
    if state["terminal_settled"]:
        return 0.0
    tasks = cfg["task_count"] if isinstance(cfg, dict) else cfg.task_count
    penalty = cfg["unfinished_weight"] if isinstance(cfg, dict) else cfg.unfinished_weight
    if len(weights) != tasks or len(state["statuses"]) != tasks:
        raise ContractError("Terminal ledger must retain all original tasks")
    unfinished = math.fsum(weight for weight, status in zip(weights, state["statuses"]) if status != "completed")
    value = -penalty * unfinished / (4.0 * tasks)
    state["components"]["terminal"] += value
    state["terminal_settled"] = True
    return value


def validate_boundary_request(*, tick, end_tick, checkpoint_id, current_checkpoint_id,
                              expected_start_tick, boundary_committed_tick=None):
    """Return a frozen rejection reason, or None; perform no sampling/state write."""
    if tick >= end_tick:
        return "TERMINAL_ENVIRONMENT"
    if type(expected_start_tick) is not int or expected_start_tick != tick:
        return "WRONG_START_TICK"
    if tick not in legal_decision_ticks(0, end_tick):
        return "NONDECISION_BOUNDARY"
    if checkpoint_id != current_checkpoint_id:
        return "STALE_CHECKPOINT"
    if boundary_committed_tick == tick:
        return "BOUNDARY_ALREADY_COMMITTED"
    return None


class OnlineEnvironment:
    """Actual state persists across bounded jobs under one physical identity."""

    def __init__(self, case, sense_callback, physical_environment_id, restored=None, *, work_identity=None):
        source = case.get("private_execution_input", case)
        wanted = ("config", "positions_initial", "targets", "initial_assignment",
                  "sensor_declaration_schedule", "measurement_model")
        if not isinstance(source, dict) or any(key not in source for key in wanted):
            raise ContractError("Complete private actual execution input required")
        self._source = deepcopy({key: source[key] for key in wanted})
        self.source_identity = digest(self._source)
        if not isinstance(physical_environment_id, str) or not physical_environment_id:
            raise ContractError("A stable physical environment identity is required")
        self.physical_environment_id = physical_environment_id
        self.work_identity = work_identity or physical_environment_id
        self.sense_callback = sense_callback
        if not callable(sense_callback):
            raise ContractError("Actual sensing callback is required")
        self.cfg = Config(**deepcopy(source["config"]))
        cfg = self.cfg
        if (cfg.capture_mode != "stepwise_service" or cfg.geometry_mode != "angular_standoff_v1"
                or cfg.motion_model != "continuous_turn" or cfg.stage_dt != 3.
                or cfg.turn_interval != 1. or cfg.step_dt != DT or cfg.risk_prediction_dt != DT
                or cfg.observation_radius != .6 or cfg.observation_tolerance != .15):
            raise ContractError("Online execution requires the frozen angular/.05/one-second physical contract")
        self.targets = tuple(Target(**deepcopy(t)) for t in source["targets"])
        positions = np.asarray(source["positions_initial"], dtype=float)
        Environment(cfg, Scenario(positions, self.targets))  # Constructor guards only.
        if any(t.required_robots not in (2, 3) for t in self.targets):
            raise ContractError("Actual online GQ tasks require q2 or q3")
        idle = [dict(target=None, role="none") for _ in range(cfg.robots)]
        if source["initial_assignment"] != idle:
            raise ContractError("Main episodes begin unassigned; no hidden scripted prefix")
        self.end_tick = round(cfg.end_time / DT)
        self._escape = [float(t.escape_time(cfg.side)) for t in self.targets]
        self._schedule = deepcopy(source["sensor_declaration_schedule"])
        previous = -1
        for row in self._schedule:
            tick = row["effective_tick"]
            if type(tick) is not int or tick <= previous or tick > self.end_tick:
                raise ContractError("Declaration changes must have strictly increasing global ticks")
            previous = tick
            if [p["sensor_id"] for p in row["profiles"]] != [f"U{i}" for i in range(cfg.robots)]:
                raise ContractError("A declaration row needs every stable Uk in order")
            for profile in row["profiles"]:
                if (set(profile) != {"sensor_id", "sigma", "health"} or
                        type(profile["sigma"]) not in (int, float) or
                        not math.isfinite(profile["sigma"]) or profile["sigma"] <= 0 or
                        profile["health"] not in ("available", "missing")):
                    raise ContractError("Invalid actual sensor declaration")
        if not self._schedule or self._schedule[0]["effective_tick"] != 0:
            raise ContractError("An initial sensor declaration is required")
        if source["measurement_model"]["angle_perturbation"] != 0.0:
            raise ContractError("Actual main episode perturbation must remain the frozen zero value")
        self.sampler = ActualMeasurementCache(physical_environment_id)
        self._state = dict(tick=0, positions=positions.tolist(), assignment=idle,
            statuses=["hidden"] * cfg.task_count, histories={}, completion_times=[None] * cfg.task_count,
            escape_times=[None] * cfg.task_count, archives={}, total_effort=0.0,
            effort_by_robot=[0.0] * cfg.robots, occupied_by_robot=[0.0] * cfg.robots,
            flow=0.0, late=0.0, changes=0, change_cost=0.0, peak_speed=0.0,
            components={key: 0.0 for key in ("completion", "flow", "late", "effort", "terminal")},
            terminal_settled=False, events=[])
        self.frames, self.fusions, self.action_commits = [], [], []
        self.journal = RequestJournal()
        self._flows = {}
        self._last_checkpoint = None
        self._checkpoint_event_cursor = 0
        self._boundary_committed_tick = None
        self.failed, self.failure = False, None
        if restored is None:
            self._activate(self._state, 0)
            self._checkpoint()
        else:
            self._restore(restored)

    @property
    def tick(self):
        return self._state["tick"]

    @property
    def done(self):
        return self.tick >= self.end_tick

    @property
    def _successful(self):
        return self.journal.successful

    @_successful.setter
    def _successful(self, value):
        self.journal.successful = value

    @property
    def _inflight(self):
        return self.journal.inflight

    @_inflight.setter
    def _inflight(self, value):
        self.journal.inflight = value

    def _profiles(self, tick):
        row = max((r for r in self._schedule if r["effective_tick"] <= tick), key=lambda r: r["effective_tick"])
        return [dict(p, observed_tick=tick) for p in deepcopy(row["profiles"])]

    def _history(self, state, target):
        return state["histories"][str(target)]

    def _segment(self, state, target):
        history = self._history(state, target)
        return next((s for s in history["segments"] if s["segment_id"] == history["active_segment_id"]), None)

    def _event(self, state, target, kind, when, segment_id, before=0.0, after=0.0, reasons=()):
        event = dict(event_index=len(state["events"]), kind=kind, target_id=target, at=_point(when),
                     segment_id=segment_id, progress_before=float(before), progress_after=float(after), reasons=list(reasons))
        state["events"].append(event)
        history = self._history(state, target)
        history["events"].append(deepcopy(event))
        if segment_id is not None:
            segment = next((s for s in history["segments"] if s["segment_id"] == segment_id), None)
            if segment is not None:
                segment["events"].append(deepcopy(event))
        return event

    def _activate(self, state, tick):
        for t in self.targets:
            if state["statuses"][t.id] != "hidden" or t.birth > tick * DT + TOL:
                continue
            state["statuses"][t.id] = "active"
            history = dict(target_id=t.id, birth_tick=round(t.birth / DT), cutoff_tick=tick,
                active_segment_id=None, segments=[], unassigned_intervals=[], events=[])
            state["histories"][str(t.id)] = history
            event = self._event(state, t.id, "BIRTH", t.birth, None, reasons=["BIRTH"])
            history["unassigned_intervals"].append(dict(start_tick=round(t.birth / DT), end_at=None,
                opened_by="BIRTH", opening_event_index=event["event_index"], closing_event_index=None))

    def _seal_histories(self, state):
        for j, history in state["histories"].items():
            if state["statuses"][int(j)] == "active":
                history["cutoff_tick"] = state["tick"]
            history["segments"] = [public.seal_segment(s) for s in history["segments"]]
            state["histories"][j] = public.seal_history(history)

    def _checkpoint(self):
        state = self._state
        self._seal_histories(state)
        active = [t for t in self.targets if state["statuses"][t.id] == "active"]
        body = dict(previous_checkpoint_id=None if self._last_checkpoint is None else self._last_checkpoint["checkpoint_id"],
            phase="TERMINAL" if self.done else "DECISION_READY", tick=self.tick, episode_end_tick=self.end_tick,
            config=self.cfg.to_dict(), positions=deepcopy(state["positions"]), assignment=deepcopy(state["assignment"]),
            targets=[dict(id=t.id, birth=t.birth, position_now=t.position(self.tick * DT).tolist(),
                          velocity_now=t.velocity_at(self.tick * DT).tolist(), required_robots=t.required_robots,
                          weight=t.weight, deadline=t.deadline, service_duration=t.service_duration) for t in active],
            sensor_profiles=self._profiles(self.tick),
            task_histories=[deepcopy(self._history(state, t.id)) for t in active],
            current_slots=[self.sampler.peek(t.id, i, self.tick) for t in active for i in range(self.cfg.robots)],
            events_since_previous_checkpoint=deepcopy(state["events"][self._checkpoint_event_cursor:]))
        self._last_checkpoint = public.seal_checkpoint(body)
        public.validate_checkpoint(self._last_checkpoint, unit_only=True)  # Writer consistency, not authority issuance.
        self._checkpoint_event_cursor = len(state["events"])
        return deepcopy(self._last_checkpoint)

    def initialize(self):
        return self.observe_public()

    def observe_public(self):
        return deepcopy(self._last_checkpoint)

    def checkpoint(self):
        return self.observe_public()

    def public_binding(self):
        return public.binding_from_checkpoint(self._last_checkpoint)

    def _sample(self, state, target, robot, tick):
        profile = self._profiles(tick)[robot]
        position = deepcopy(state["positions"][robot])
        context = dict(position=position, sigma=profile["sigma"], health=profile["health"])

        def producer():
            if profile["health"] == "missing":
                return dict(state="MISSING", packet=None)
            point = self.targets[target].position(tick * DT)
            angle = math.atan2(float(point[1] - position[1]), float(point[0] - position[0]))
            bearing = (angle + math.pi) % (2 * math.pi) - math.pi
            return dict(state="VALID", packet=dict(sensor_id=f"U{robot}", position=position,
                bearing=bearing, sigma=profile["sigma"], measurement_tick=tick, available_tick=tick, status="ok"))

        return self.sampler.query(target, robot, tick, context, producer)

    def _fuse(self, state, target, team, tick):
        flow = self._flows[target]
        slots = [self._sample(state, target, member["robot_id"], tick) for member in team]
        all_slots = [self.sampler.peek(target, i, tick) for i in range(self.cfg.robots)]
        assembly = measurements.assemble_left_state(tick=tick, target_id=target,
            target_position=self.targets[target].position(tick * DT).tolist(), positions=state["positions"],
            sensor_profiles=self._profiles(tick), current_slots=all_slots, team=team, stream_id=flow["stream_id"], actual=True)
        frame, allowed = assembly["frame"], assembly["allowed_sensor_ids"]
        context = deepcopy(flow["context"])
        prepared = prepare_frame(frame, allowed)
        sent = deepcopy(frame)
        input_id = digest(sent)
        result = self.sense_callback(sent, allowed, flow["first_new_fusion_tick"], deepcopy(context))
        if digest(sent) != input_id:
            raise ContractError("Actual sensor callback mutated its frame")
        if not isinstance(result, dict) or result.get("flow_context") != context:
            raise ContractError("Actual fusion result has the wrong execution/segment context")
        for field in ("frame_id", "stream_id", "target_id", "tick"):
            if result.get(field) != frame[field]:
                raise ContractError("Actual fusion result belongs to a different endpoint")
        q = result.get("quality", {})
        if (q.get("status") not in ("PASS", "FAIL", "UNKNOWN") or
                result.get("payload_sha256") != prepared["payload_sha256"] or
                q.get("payload_sha256") != prepared["payload_sha256"]):
            raise ContractError("Actual quality/payload identity mismatch")
        endpoint = measurements.make_actual_endpoint(target_id=target, tick=tick, team=team,
            G=assembly["G"], assembly=assembly, quality_result=result)
        self.fusions.append(dict(frame=frame, allowed_sensor_ids=allowed, start_tick=flow["first_new_fusion_tick"],
                                 context=context, result=deepcopy(result), actual_endpoint=deepcopy(endpoint)))
        return endpoint, slots

    def _close_segment(self, state, target, reason, event):
        history = self._history(state, target)
        segment = self._segment(state, target)
        if segment is None or segment["closure"] is not None:
            raise ContractError("Missing live segment at closure")
        segment["closure"] = dict(reason=reason, at=deepcopy(event["at"]), closing_event_index=event["event_index"])
        history["active_segment_id"] = None

    def _prepare_boundary(self, metadata):
        transaction = BoundaryTransaction(self._state)
        transaction.prepare(lambda state: self._prepare_boundary_state(state, metadata))
        return transaction.commit()

    def _prepare_boundary_state(self, state, metadata):
        transitions, prepared_slots = [], {}
        self._flows = {m["target_id"]: deepcopy(m) for m in metadata["flows"]}
        for change in metadata["transitions"]:
            j, kind = change["target_id"], change["kind"]
            history = self._history(state, j)
            old = self._segment(state, j)
            before = 0.0 if old is None else _progress(old["latest_clock"])
            if kind in ("WITHDRAW", "MEMBER_CHANGE", "ROLE_CHANGE"):
                event_kind = "WITHDRAWN" if kind == "WITHDRAW" else "TEAM_CHANGED" if kind == "MEMBER_CHANGE" else "ROLE_CHANGED"
                reason = "WITHDRAWAL" if kind == "WITHDRAW" else kind
                event = self._event(state, j, event_kind, self.tick * DT, old["segment_id"], before, 0.0, [reason])
                self._close_segment(state, j, "WITHDRAWN" if kind == "WITHDRAW" else
                                    "TEAM_CHANGED" if kind == "MEMBER_CHANGE" else "ROLE_CHANGED", event)
                if kind == "WITHDRAW":
                    history["unassigned_intervals"].append(dict(start_tick=self.tick, end_at=None,
                        opened_by="WITHDRAWAL", opening_event_index=event["event_index"], closing_event_index=None))
            if kind not in ("KEEP", "WITHDRAW", "UNCHANGED_UNASSIGNED"):
                team = deepcopy(change["team"])
                segment = dict(target_id=j, segment_index=change["segment_index"],
                    segment_id=change["segment_id"], previous_segment_id=change["previous_segment_id"],
                    start_tick=self.tick, team=team, opened_by=change["opened_by"],
                    initial_clock=_zero(team), latest_clock=_zero(team), latest_endpoint=None, closure=None, events=[])
                history["segments"].append(segment)
                history["active_segment_id"] = segment["segment_id"]
                event = self._event(state, j, "ASSIGNED", self.tick * DT, segment["segment_id"],
                                    0.0, 0.0, [change["opened_by"]])
                for gap in history["unassigned_intervals"]:
                    if gap["end_at"] is None:
                        gap["end_at"] = deepcopy(event["at"])
                        gap["closing_event_index"] = event["event_index"]
                endpoint, slots = self._fuse(state, j, team, self.tick)
                segment["latest_endpoint"] = endpoint
                for slot in slots:
                    prepared_slots[(j, slot["slot_key"]["robot_id"])] = slot
            active = self._segment(state, j)
            transitions.append(dict(target_id=j, kind=kind, old_segment_id=change["old_segment_id"],
                new_segment_id=change["new_segment_id"], clock_after=_zero() if active is None else deepcopy(active["latest_clock"]),
                actual_left_endpoint=None if active is None else deepcopy(active["latest_endpoint"])))
        charged = apply_assignment_boundary(state, metadata["actions"], self.cfg.change_cost)
        if charged["assignment_changes"] != metadata["assignment_change_count"] or charged["change_cost"] != metadata["change_cost"]:
            raise ContractError("Prepared Assignment charge differs from its public boundary plan")
        self._seal_histories(state)
        committed = public.seal_action_commit(dict(checkpoint_id=self._last_checkpoint["checkpoint_id"],
            start_tick=self.tick, assignment=deepcopy(metadata["actions"]), transitions=transitions,
            assignment_change_count=metadata["assignment_change_count"], change_cost=metadata["change_cost"],
            simulated_time_advance=0.0, prepared_actual_slots=[prepared_slots[k] for k in sorted(prepared_slots)]))
        return committed

    def _finish(self, state, target, status, when, processed_tick):
        if state["statuses"][target] != "active":
            raise ContractError("Repeated actual terminal settlement")
        history, segment = self._history(state, target), self._segment(state, target)
        progress = 0.0 if segment is None else _progress(segment["latest_clock"])
        kind, reason = {"completed": ("COMPLETED", "SERVICE_COMPLETE"), "escaped": ("ESCAPED", "ESCAPE"),
                        "unfinished": ("EPISODE_ENDED", "EPISODE_END")}[status]
        event = self._event(state, target, kind, when, None if segment is None else segment["segment_id"],
                            progress, progress, [reason])
        if segment is not None:
            self._close_segment(state, target, "COMPLETED" if status == "completed" else
                                "ESCAPED" if status == "escaped" else "EPISODE_END", event)
        for gap in history["unassigned_intervals"]:
            if gap["end_at"] is None:
                gap["end_at"] = deepcopy(event["at"])
                gap["closing_event_index"] = event["event_index"]
        state["statuses"][target] = status
        history["cutoff_tick"] = processed_tick
        state["assignment"], robots = release_assignment(state["assignment"], target)
        if status == "completed":
            state["completion_times"][target] = when
            state["components"]["completion"] += self.targets[target].weight / self.cfg.weight_reference
        elif status == "escaped":
            state["escape_times"][target] = when
        state["archives"][str(target)] = dict(target_id=target, terminal_status=status, terminal_at=_point(when),
            released_robots=robots, release_change_cost=0.0, closing_event_index=event["event_index"])

    def _frame(self, state, phase, before, control, elapsed, new_events):
        progress, endpoints, segments = {}, {}, {}
        for j in state["histories"]:
            segment = self._segment(state, int(j))
            if segment is not None:
                progress[j] = _progress(segment["latest_clock"])
                segments[j] = segment["segment_id"]
                ep = segment["latest_endpoint"]
                if ep["tick"] == state["tick"]:
                    endpoints[j] = deepcopy(ep)
            else:
                history = state["histories"][j]
                archive = state["archives"].get(j)
                progress[j] = (state["events"][archive["closing_event_index"]]["progress_after"]
                               if archive is not None else 0.0)
                if history["segments"]:
                    last = history["segments"][-1]["latest_endpoint"]
                    if last["tick"] == state["tick"]:
                        endpoints[j] = deepcopy(last)
        return dict(tick=state["tick"], time=state["tick"] * DT, phase=phase,
            positions_start=before, positions=deepcopy(state["positions"]), control=control,
            control_elapsed_by_robot=elapsed, assignment=deepcopy(state["assignment"]),
            statuses=deepcopy(state["statuses"]), progress=progress, active_segment_ids=segments,
            actual_endpoints=endpoints, events=deepcopy(new_events), metrics=self._metrics(state))

    def _control_command(self, target_id, at, positions, offsets):
        """Oracle default; A1 overrides only this policy input seam."""
        target = self.targets[target_id]
        return target.velocity_at(at) + self.cfg.travel_gain * (target.position(at) + offsets - positions)

    def _advance_tick(self):
        if self.done:
            raise ContractError("No physical interval may run after the actual episode endpoint")
        state = deepcopy(self._state)
        n = state["tick"] + 1
        lo, hi = state["tick"] * DT, n * DT
        before = deepcopy(state["positions"])
        control = np.zeros((self.cfg.robots, 2), dtype=float)
        elapsed_by_robot = [0.0] * self.cfg.robots
        begin_events = len(state["events"])
        for t in self.targets:
            j = t.id
            if state["statuses"][j] != "active":
                continue
            segment = self._segment(state, j)
            escape = self._escape[j]
            stop = min(hi, escape)
            elapsed = max(0.0, stop - lo)
            if segment is not None:
                team = segment["team"]
                robots = [m["robot_id"] for m in team]
                if robots != [i for i, a in enumerate(state["assignment"]) if a["target"] == j]:
                    raise ContractError("Actual segment and occupied resources disagree")
                pos = np.asarray([state["positions"][i] for i in robots], dtype=float)
                offsets = np.asarray([geometry.offset(m["role"], self.cfg) for m in team])
                command = self._control_command(j, lo, pos, offsets)
                speed = np.linalg.norm(command, axis=1)
                command *= np.minimum(1.0, self.cfg.max_speed / np.maximum(speed, 1e-15))[:, None]
                pos += command * elapsed
                effort = float(np.sum(command ** 2)) * elapsed
                state["total_effort"] += effort
                state["components"]["effort"] -= self.cfg.control_weight * effort / self.cfg.effort_reference
                state["peak_speed"] = max(state["peak_speed"], float(np.linalg.norm(command, axis=1).max()))
                for local, robot in enumerate(robots):
                    state["positions"][robot] = pos[local].tolist()
                    state["effort_by_robot"][robot] += float(np.sum(command[local] ** 2)) * elapsed
                    state["occupied_by_robot"][robot] += elapsed
                    control[robot] = command[local]
                    elapsed_by_robot[robot] = elapsed
            if escape <= hi + TOL:
                self._finish(state, j, "escaped", escape, n)
                cost_stop = escape
            else:
                cost_stop = hi
                if segment is not None:
                    left = segment["latest_endpoint"]
                    if left["tick"] != n - 1:
                        raise ContractError("Actual service is missing its previous endpoint")
                    right, _ = self._fuse(state, j, segment["team"], n)
                    raw = segment["latest_clock"]
                    native = replace(initial_state(self.cfg), base=raw["base"], intervals=raw["intervals"],
                                     team=tuple((m["robot_id"], m["role"]) for m in raw["team"]))
                    valid = left["G"] and right["G"] and left["quality"]["status"] == right["quality"]["status"] == "PASS"
                    clock, done, interruptions = advance_clock(native, t.service_duration, native.team, valid, hi)
                    segment["latest_clock"] = dict(base=clock.base, intervals=clock.intervals, team=deepcopy(segment["team"]))
                    segment["latest_endpoint"] = right
                    for event in interruptions:
                        reasons = []
                        if not left["G"] or not right["G"]:
                            reasons.append("GEOMETRY_INVALID")
                        if "FAIL" in (left["quality"]["status"], right["quality"]["status"]):
                            reasons.append("QUALITY_FAIL")
                        if "UNKNOWN" in (left["quality"]["status"], right["quality"]["status"]):
                            reasons.append("QUALITY_UNKNOWN")
                        self._event(state, j, "INTERRUPTED", hi, segment["segment_id"],
                                    event["progress_before"], clock.progress, reasons)
                    if done:
                        self._finish(state, j, "completed", hi, n)
            flow = t.weight * max(0.0, cost_stop - max(lo, t.birth))
            late = t.weight * max(0.0, cost_stop - max(lo, t.birth, t.deadline))
            state["flow"] += flow
            state["late"] += late
            state["components"]["flow"] -= self.cfg.flow_weight * flow / (self.cfg.weight_reference * self.cfg.stage_dt)
            state["components"]["late"] -= self.cfg.late_weight * late / (self.cfg.weight_reference * self.cfg.stage_dt)
        state["tick"] = n
        self._activate(state, n)
        if n == self.end_tick:
            if state["terminal_settled"]:
                raise ContractError("Actual terminal cost was already settled")
            for t in self.targets:
                if state["statuses"][t.id] == "active":
                    self._finish(state, t.id, "unfinished", hi, n)
            settle_terminal_once(state, self.cfg, [t.weight for t in self.targets])
        self._seal_histories(state)
        frame = self._frame(state, "physical", before, control.tolist(), elapsed_by_robot, state["events"][begin_events:])
        self._state = state
        self.frames.append(frame)
        return deepcopy(frame)

    def _reject(self, reason):
        return dict(contract_id="gq_online_action_transaction_v1", status="REJECTED", reason=reason,
                    committed_assignment_or_fees_changed=False, new_sampling_attempts=0)

    def step(self, actions, checkpoint_id, expected_start_tick, request_id, *, work_identity=None, on_commit=None):
        if not isinstance(request_id, str) or not request_id:
            return self._reject("MALFORMED_INPUT")
        try:
            fingerprint = digest(dict(physical_environment_id=self.physical_environment_id,
                checkpoint_id=checkpoint_id, expected_start_tick=expected_start_tick, assignment=actions))
        except (TypeError, ValueError):
            return self._reject("MALFORMED_INPUT")
        previous = self.journal.lookup(request_id, fingerprint)
        if previous is not None and previous["state"] == "REPLAY":
            result = previous["result"]
            result["replayed"] = True
            return result
        if previous is not None and previous["state"] == "REJECTED":
            return self._reject(previous["reason"])
        if previous is not None and previous["state"] == "IN_PROGRESS":
            return dict(contract_id="gq_online_action_transaction_v1", status="IN_PROGRESS",
                        request_fingerprint=fingerprint, new_transaction_started=False, deadline_extended=False)
        if self.failed:
            raise ContractError("A failed actual environment cannot continue")
        rejection = validate_boundary_request(tick=self.tick, end_tick=self.end_tick,
            checkpoint_id=checkpoint_id, current_checkpoint_id=self._last_checkpoint["checkpoint_id"],
            expected_start_tick=expected_start_tick, boundary_committed_tick=self._boundary_committed_tick)
        if rejection is not None:
            return self._reject(rejection)
        if work_identity is not None:
            self.work_identity = str(work_identity)
        try:
            metadata = public.plan_action_metadata(self._last_checkpoint, actions, self.work_identity,
                                                  physical_environment_id=self.physical_environment_id)
        except (ContractError, ValueError, TypeError):
            return self._reject("MALFORMED_INPUT")
        start, first_frame, first_event, first_fusion = self.tick, len(self.frames), len(self._state["events"]), len(self.fusions)
        self.journal.begin(request_id, fingerprint)
        try:
            state, committed = self._prepare_boundary(metadata)
            self._state = state
            self._boundary_committed_tick = start
            self.action_commits.append(deepcopy(committed))
            boundary = self._frame(state, "decision", deepcopy(state["positions"]),
                [[0.0, 0.0] for _ in range(self.cfg.robots)], [0.0] * self.cfg.robots,
                state["events"][first_event:])
            self.frames.append(boundary)
            if on_commit is not None:
                on_commit(deepcopy(boundary))
            end = min(start + 20, self.end_tick)
            while self.tick < end:
                frame = self._advance_tick()
                if on_commit is not None:
                    on_commit(frame)
            checkpoint = self._checkpoint()
            ended, born = collect_interval_events(self._state["events"], start, end)
            result = dict(status="COMMITTED", replayed=False, action_commit=committed,
                action_commit_id=committed["action_commit_id"], start_tick=start, end_tick=end,
                checkpoint_after=checkpoint, public_binding=self.public_binding(),
                frames=deepcopy(self.frames[first_frame:]), events=deepcopy(self._state["events"][first_event:]),
                fusion_records=deepcopy(self.fusions[first_fusion:]), metrics=self.metrics(),
                ended_ids=ended, new_ids=born)
            self.journal.commit(result)
            return result
        except BaseException as error:
            self.failed = True
            self.failure = dict(error_type=type(error).__name__, error=str(error), request_id=request_id,
                last_committed_tick=self.tick, last_committed_checkpoint_id=self._last_checkpoint["checkpoint_id"],
                sample_attempts_retained=len(self.sampler.attempts), automatic_retry_allowed=False)
            error.gq_last_committed = deepcopy(self.frames[-1] if self.frames else self._last_checkpoint)
            raise
        finally:
            self.journal.abort()

    def _metrics(self, state):
        occupied = math.fsum(state["occupied_by_robot"])
        physical = math.fsum(state["components"].values())
        return dict(reward_components=deepcopy(state["components"]), return_without_changes=physical,
            return_with_changes=physical - state["change_cost"], change_cost=state["change_cost"],
            assignment_changes=state["changes"], control_integral=state["total_effort"],
            effort_by_robot=deepcopy(state["effort_by_robot"]), occupied_robot_seconds=occupied,
            idle_robot_seconds=self.cfg.robots * state["tick"] * DT - occupied,
            flow=state["flow"], late=state["late"], peak_speed=state["peak_speed"],
            completed_count=state["statuses"].count("completed"), escaped_count=state["statuses"].count("escaped"),
            actual_sampling_attempts=len(self.sampler.attempts), actual_cache_requests=self.sampler.requests,
            actual_cache_reuses=self.sampler.reuses, actual_fusions=len(self.fusions),
            reported_estimator_calls=sum(r["result"].get("estimator_called") is True for r in self.fusions))

    def metrics(self):
        return self._metrics(self._state)

    def private_snapshot(self):
        body = dict(contract_id=CONTRACT_ID, visibility="PRIVATE_EXECUTION_RECOVERY",
            physical_environment_id=self.physical_environment_id, source_identity=self.source_identity,
            case=deepcopy(self._source), state=deepcopy(self._state), sampler=self.sampler.snapshot(),
            successful_requests=deepcopy(self._successful), inflight=deepcopy(self._inflight),
            boundary_committed_tick=self._boundary_committed_tick, checkpoint=deepcopy(self._last_checkpoint),
            checkpoint_event_cursor=self._checkpoint_event_cursor, frames=deepcopy(self.frames),
            fusions=deepcopy(self.fusions), action_commits=deepcopy(self.action_commits),
            failed=self.failed, failure=deepcopy(self.failure))
        return dict(body, snapshot_digest=digest(body))

    def _restore(self, restored):
        data = deepcopy(restored)
        expected = data.pop("snapshot_digest", None)
        if expected != digest(data) or data.get("contract_id") != CONTRACT_ID:
            raise ContractError("Invalid actual resume artifact identity")
        if data["physical_environment_id"] != self.physical_environment_id or data["source_identity"] != self.source_identity:
            raise ContractError("Actual resume source/environment changed")
        if data["case"] != self._source or data["failed"] or data["inflight"] is not None:
            raise ContractError("Failed/inflight or modified actual state cannot resume")
        state, checkpoint = data["state"], data["checkpoint"]
        if state["tick"] % 20 or state["tick"] != checkpoint["tick"]:
            raise ContractError("Only a clean committed decision cut can resume")
        public.validate_checkpoint(checkpoint, unit_only=True)
        if state["positions"] != checkpoint["positions"] or state["assignment"] != checkpoint["assignment"]:
            raise ContractError("Private actual state and public committed cut disagree")
        active = [j for j, status in enumerate(state["statuses"]) if status == "active"]
        if (active != [t["id"] for t in checkpoint["targets"]] or
                [state["histories"][str(j)] for j in active] != checkpoint["task_histories"] or
                checkpoint["sensor_profiles"] != self._profiles(state["tick"]) or
                data["checkpoint_event_cursor"] != len(state["events"]) or
                state["terminal_settled"] != (state["tick"] == self.end_tick)):
            raise ContractError("Restored history/declarations/terminal ledger differ from the committed cut")
        recent = checkpoint["events_since_previous_checkpoint"]
        if recent and state["events"][-len(recent):] != recent:
            raise ContractError("Restored decision-interval events disagree with their public checkpoint")
        self.sampler = ActualMeasurementCache(self.physical_environment_id, data["sampler"])
        self._state = state
        self._successful = data["successful_requests"]
        self._boundary_committed_tick = data["boundary_committed_tick"]
        self._last_checkpoint = checkpoint
        self._checkpoint_event_cursor = data["checkpoint_event_cursor"]
        self.frames, self.fusions, self.action_commits = data["frames"], data["fusions"], data["action_commits"]
        self.failed, self.failure = False, None
        # Recheck all public current slots against the preserved physical cache.
        for slot in checkpoint["current_slots"]:
            key = slot["slot_key"]
            if self.sampler.peek(key["target_id"], key["robot_id"], key["tick"]) != slot:
                raise ContractError("Restored actual cache differs from the committed checkpoint")
