from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np

from .config import Config
from .types import Assignment, IDLE, Observation, Scenario, complete_roles, role_offset
from .physics import rollout_target


@dataclass
class StepResult:
    reward: float
    done: bool
    info: dict


class Environment:
    """Atomic 3-second steps; actions can change only between step calls."""
    def __init__(self, cfg: Config, scenario: Scenario):
        self.cfg = cfg
        self.scenario = scenario
        from .observation_geometry import required_roles, identity
        self._geometry_identity = identity(cfg)
        if scenario.pursuers.shape != (cfg.robots, 2):
            raise ValueError("Pursuer shape must be [robots, xy]")
        if not np.isfinite(scenario.pursuers).all() or len(scenario.targets) != cfg.task_count:
            raise ValueError("Invalid scenario positions or task count")
        for i, target in enumerate(scenario.targets):
            required_roles(target.required_robots, cfg)
            if cfg.capture_mode == "stepwise_service" and target.service_duration is None:
                raise ValueError("stepwise_service requires explicit service_duration on every target")
            if target.id != i or target.birth >= cfg.end_time:
                raise ValueError("Target IDs must be contiguous; births must precede episode end")
            if not math.isclose(target.birth / cfg.stage_dt, round(target.birth / cfg.stage_dt),
                                abs_tol=1e-9):
                raise ValueError("Births must occur at stage boundaries")
            if not 0 <= target.position_at_birth[0] < cfg.side:
                raise ValueError("Targets must be born before the escape line")
            if (cfg.turn_max_angle > 0 or cfg.speed_delta_max > 0 or
                    cfg.motion_model == "continuous_turn"):
                velocities = (target.velocity,) + tuple((vx, vy) for _, vx, vy in target.turns)
                if any(np.linalg.norm(velocity) > cfg.target_speed_max + 1e-9
                       for velocity in velocities):
                    raise ValueError("Turning target exceeds configured speed bound")
                if any(not math.isclose(time / cfg.step_dt, round(time / cfg.step_dt), abs_tol=1e-9)
                       for time, _, _ in target.turns):
                    raise ValueError("Turn times must align with control step")
            if cfg.motion_model == "continuous_turn":
                if not target.arc_rates or target.turns:
                    raise ValueError("Continuous-turn targets need arc rates")
                if any(not math.isclose(time / cfg.step_dt, round(time / cfg.step_dt),
                                        abs_tol=1e-9) for time, _ in target.arc_rates):
                    raise ValueError("Arc rate changes must align with control step")
                if any(abs(rate) > cfg.turn_max_angle / cfg.turn_interval + 1e-9
                       for _, rate in target.arc_rates):
                    raise ValueError("Arc turn rate exceeds the configured bound")
                if any(abs(math.atan2(target.velocity_at(time)[1],
                                      target.velocity_at(time)[0])) > cfg.turn_max_angle + 1e-8
                       for time, _ in target.arc_rates):
                    raise ValueError("Arc heading leaves the eastward envelope")
        self.positions = scenario.pursuers.copy()
        self.stage = 0
        self.status = ["hidden"] * cfg.task_count
        self.capture_times = np.full(cfg.task_count, np.nan)
        if cfg.capture_mode == "stepwise_service":
            from .service import initial_state
            self.service_progress = np.zeros(cfg.task_count)
            self.service_team = [()] * cfg.task_count
            self._service_states = [initial_state(cfg) for _ in scenario.targets]
            self.completion_times = np.full(cfg.task_count, np.nan)
        self.escape_times = np.full(cfg.task_count, np.nan)
        self.last_assignment = (IDLE,) * cfg.robots
        self.ended_ids = ()
        self.new_ids = self._activate()
        self.total_reward = 0.0
        self.total_change_cost = 0.0
        self.total_changes = 0
        self.total_effort = 0.0
        self.total_partner_wait = 0.0
        self.peak_speed = 0.0
        self.mismatch_count = 0
        self._stepping = False

    @property
    def time(self):
        return self.stage * self.cfg.stage_dt

    @property
    def done(self):
        return self.stage >= self.cfg.max_stages

    @property
    def active_ids(self):
        return tuple(i for i, s in enumerate(self.status) if s == "active")

    def _activate(self):
        ids = []
        for task in self.scenario.targets:
            if self.status[task.id] == "hidden" and task.birth <= self.time + 1e-10:
                self.status[task.id] = "active"
                ids.append(task.id)
        return tuple(ids)

    def clean_assignment(self):
        active = set(self.active_ids)
        return tuple(a if a.target in active else IDLE for a in self.last_assignment)

    def observe(self) -> Observation:
        positions = self.positions.copy()
        positions.setflags(write=False)
        return Observation(self.cfg, self.stage, positions,
                           tuple(self.scenario.targets[i].observed(self.time) for i in self.active_ids),
                           self.clean_assignment(), self.new_ids, self.ended_ids,
                           self.time if (self.cfg.turn_max_angle > 0 or
                                         self.cfg.speed_delta_max > 0 or
                                         self.cfg.motion_model == "continuous_turn") else None,
                           tuple((j, self._service_states[j]) for j in self.active_ids)
                           if self.cfg.capture_mode == "stepwise_service" else ())

    def _validate(self, actions):
        from .observation_geometry import required_roles, identity, validate_roles
        if identity(self.cfg) != self._geometry_identity:
            raise ValueError('Runtime geometry change is forbidden')
        actions = tuple(actions)
        if len(actions) != self.cfg.robots or any(not isinstance(a, Assignment) for a in actions):
            raise ValueError("Supply one immutable Assignment per robot")
        counts = {}
        for action in actions:
            if action.target is None:
                if action.role != "none":
                    raise ValueError("Idle must use role=none")
                continue
            if isinstance(action.target, bool) or not isinstance(action.target, (int, np.integer)):
                raise ValueError("Target ID must be an integer")
            if action.target not in self.active_ids:
                raise ValueError("Cannot assign a hidden, captured, escaped or unknown target")
            task = self.scenario.targets[action.target]
            legal = required_roles(task.required_robots, self.cfg)
            if action.role not in legal:
                raise ValueError("Role is incompatible with task demand")
            counts[action.target] = counts.get(action.target, 0) + 1
            if counts[action.target] > task.required_robots:
                raise ValueError("Too many robots assigned to one task")
        if self.cfg.geometry_mode != 'legacy_anchor':
            for j in counts:
                validate_roles(self.scenario.targets[j].required_robots,
                               [a.role for a in actions if a.target == j], self.cfg)
        return actions

    @staticmethod
    def _coalition_log(old, new):
        targets = sorted({a.target for a in (*old, *new) if a.target is not None})
        events = []
        for target in targets:
            before = [k for k, a in enumerate(old) if a.target == target]
            after = [k for k, a in enumerate(new) if a.target == target]
            labels = []
            if before == after:
                labels.append("maintain")
            if set(after) - set(before):
                labels.append("join")
            if set(before) - set(after):
                labels.append("leave")
            destinations = {new[k].target for k in before if new[k].target is not None}
            origins = {old[k].target for k in after if old[k].target is not None}
            if len(destinations) > 1:
                labels.append("split")
            if len(origins) > 1:
                labels.append("merge")
            if any(old[k].target == new[k].target == target and old[k].role != new[k].role
                   for k in range(len(new))):
                labels.append("role_change")
            events.append({"target": target, "before": before, "after": after, "labels": labels})
        return events

    def step(self, actions, trace: bool = False) -> StepResult:
        if self.done or self._stepping:
            raise RuntimeError("Step requires a live environment at a stage boundary")
        actions = self._validate(actions)
        self._stepping = True
        try:
            return self._step(actions, trace)
        finally:
            self._stepping = False

    def _release_events(self, info, actions):
        """One release per ended target, at its numerical event time."""
        if self.cfg.capture_mode != "stepwise_instant":
            return
        events = [(kind, event) for kind in ("escape", "capture")
                  for event in info[kind + "_events"]]
        info["release_events"] = [
            {"target": event["target"], "time": event["time"], "reason": kind,
             "robots": [k for k, action in enumerate(actions)
                          if action.target == event["target"]]}
            for kind, event in sorted(events, key=lambda row: (
                row[1]["time"], row[0] != "escape", row[1]["target"]))
            if any(action.target == event["target"] for action in actions)]

    def _step(self, actions, trace):
        if self.cfg.capture_mode == "stepwise_service":
            from .service_environment import step_service
            return step_service(self, actions, trace)
        cfg, start = self.cfg, self.time
        end = start + cfg.stage_dt
        old = self.clean_assignment()
        changes = sum(a != b for a, b in zip(actions, old))
        forced_release = [k for k, a in enumerate(self.last_assignment)
                          if a.target is not None and old[k] == IDLE]
        active = self.active_ids
        before = self.positions.copy()
        captured, escaped = [], []
        effort = partner_wait = peak = 0.0
        mismatch = 0
        modes = ["IDLE"] * cfg.robots
        guards = [None] * cfg.robots
        frame_times = [start + i * cfg.step_dt for i in range(round(cfg.stage_dt / cfg.step_dt) + 1)]
        frame_positions = [before.copy() for _ in frame_times] if trace else []
        frame_indices = {round(t, 9): i for i, t in enumerate(frame_times)}
        for target_id in active:
            target = self.scenario.targets[target_id]
            robots = [k for k, a in enumerate(actions) if a.target == target_id]
            if robots:
                roles = [actions[k].role for k in robots]
                result = rollout_target(
                    cfg, target, self.positions[robots][None],
                    np.array([role_offset(r, cfg) for r in roles])[None],
                    np.array([complete_roles(target, roles)]), start, trace=trace)
                self.positions[robots] = result.positions[0]
                effort += float(result.effort[0])
                partner_wait += float(result.partner_wait[0])
                peak = max(peak, float(result.peak_speed[0]))
                mismatch += int(result.mismatch_count[0])
                for local, k in enumerate(robots):
                    modes[k] = str(result.stages[0]["modes"][0])
                    guards[k] = float(result.stages[0]["guard_peaks"][0, local])
                if np.isfinite(result.capture_times[0]):
                    self.capture_times[target_id] = result.capture_times[0]
                    self.status[target_id] = "captured"
                    captured.append(target_id)
                elif np.isfinite(result.escape_times[0]):
                    self.escape_times[target_id] = result.escape_times[0]
                    self.status[target_id] = "escaped"
                    escaped.append(target_id)
                if trace:
                    for time, positions in result.frames:
                        index = frame_indices.get(round(time, 9))
                        if index is not None:
                            frame_positions[index][robots] = positions[0]
            elif target.escape_time(cfg.side) <= end + 1e-10:
                self.escape_times[target_id] = target.escape_time(cfg.side)
                self.status[target_id] = "escaped"
                escaped.append(target_id)

        flow = late = 0.0
        for i in active:
            target = self.scenario.targets[i]
            stop = (self.capture_times[i] if i in captured else
                    self.escape_times[i] if i in escaped else end)
            flow += target.weight * max(0.0, stop - max(start, target.birth))
            late += target.weight * max(0.0, stop - max(start, target.birth, target.deadline))
        capture_gain = sum(self.scenario.targets[i].weight for i in captured) / cfg.weight_reference
        flow_penalty = cfg.flow_weight * flow / (cfg.weight_reference * cfg.stage_dt)
        late_penalty = cfg.late_weight * late / (cfg.weight_reference * cfg.stage_dt)
        effort_penalty = cfg.control_weight * effort / cfg.effort_reference
        terminal_penalty = 0.0
        if self.stage + 1 == cfg.max_stages:
            terminal_penalty = cfg.unfinished_weight * sum(
                t.weight for t in self.scenario.targets if self.status[t.id] != "captured"
            ) / cfg.weight_reference
        reward = capture_gain - flow_penalty - late_penalty - effort_penalty - terminal_penalty
        cost = cfg.change_cost * changes
        self.total_reward += reward
        self.total_change_cost += cost
        self.total_changes += changes
        self.total_effort += effort
        self.total_partner_wait += partner_wait
        self.peak_speed = max(self.peak_speed, peak)
        self.mismatch_count += mismatch

        info = {
            "stage": self.stage, "start": start, "end": end, "visible_ids": list(active),
            "new_ids": list(self.new_ids), "assignment": [a.to_dict() for a in actions],
            "coalition_changes": self._coalition_log(old, actions),
            "forced_release_robots": forced_release, "changed_robots": changes,
            "modes": modes, "guard_peaks": guards, "positions_start": before.tolist(),
            "positions_end": self.positions.tolist(), "captured": captured, "escaped": escaped,
            "capture_events": [{"target": i, "time": float(self.capture_times[i])} for i in captured],
            "escape_events": [{"target": i, "time": float(self.escape_times[i])} for i in escaped],
            "flow": flow, "late": late, "effort": effort, "peak_speed": peak,
            "partner_wait": partner_wait, "model_mismatches": mismatch,
            "reward": reward, "change_cost": cost, "reward_with_changes": reward - cost,
            "reward_components": {"capture": capture_gain, "flow": -flow_penalty,
                                  "late": -late_penalty, "effort": -effort_penalty,
                                  "terminal": -terminal_penalty},
            "overdue_ids": [i for i in active if self.scenario.targets[i].deadline < end],
        }
        self._release_events(info, actions)
        if trace:
            frames = []
            for time, positions in zip(frame_times, frame_positions):
                actual_modes = modes.copy()
                for k, a in enumerate(actions):
                    if a.target is None:
                        continue
                    stopped = ((np.isfinite(self.capture_times[a.target]) and
                                time >= self.capture_times[a.target] - 1e-10) or
                               (np.isfinite(self.escape_times[a.target]) and
                                time >= self.escape_times[a.target] - 1e-10))
                    if stopped:
                        actual_modes[k] = "HOLD"
                frames.append({"time": round(time, 10), "positions": positions.tolist(),
                               "modes": actual_modes, "assignment": info["assignment"]})
            info["frames"] = frames
        self.last_assignment = actions
        if cfg.capture_mode == "stepwise_instant":
            self.last_assignment = self.clean_assignment()
        self.ended_ids = tuple(captured + escaped)
        self.stage += 1
        self.new_ids = self._activate()
        return StepResult(float(reward), self.done, info)

    def metrics(self):
        if self.cfg.capture_mode == "stepwise_service":
            from .service_environment import service_metrics
            return service_metrics(self)
        weights = np.array([t.weight for t in self.scenario.targets])
        deadlines = np.array([t.deadline for t in self.scenario.targets])
        captured = np.isfinite(self.capture_times)
        escaped = np.isfinite(self.escape_times)
        on_time = captured & (self.capture_times <= deadlines + 1e-9)
        stop = np.where(captured, self.capture_times, np.where(escaped, self.escape_times, self.time))
        elapsed = np.maximum(0, stop - np.array([t.birth for t in self.scenario.targets]))
        return {
            "return": float(self.total_reward),
            "return_with_changes": float(self.total_reward - self.total_change_cost),
            "completion_rate": float(np.mean(captured)),
            "weighted_on_time_rate": float(weights @ on_time / weights.sum()),
            "captured_count": int(captured.sum()), "escaped_count": int(escaped.sum()),
            "escaped_weight_fraction": float(weights @ escaped / weights.sum()),
            "unfinished_weight_fraction": float(weights @ (~captured) / weights.sum()),
            "assignment_changes": self.total_changes, "control_effort": self.total_effort,
            "partner_wait_robot_seconds": self.total_partner_wait,
            "max_task_sojourn": float(elapsed.max()), "peak_speed": self.peak_speed,
            "model_mismatches": self.mismatch_count, "stages": self.stage,
            "capture_mode": self.cfg.capture_mode,
        }


class TimedEnvironment(Environment):
    """Decisions each turn_interval; capture follows Config.capture_mode."""

    def __init__(self, cfg: Config, scenario: Scenario):
        if (cfg.turn_max_angle <= 0 and cfg.speed_delta_max <= 0 and
                cfg.motion_model != "continuous_turn"):
            raise ValueError("TimedEnvironment requires a changing target motion")
        self._time = 0.0
        super().__init__(cfg, scenario)

    @property
    def time(self):
        return self._time

    def step(self, actions, trace: bool = False) -> StepResult:
        if self.done or self._stepping:
            raise RuntimeError("Step requires a live observation tick")
        actions = self._validate(actions)
        self._stepping = True
        try:
            return self._step_tick(actions, trace)
        finally:
            self._stepping = False

    def _step_tick(self, actions, trace):
        if self.cfg.capture_mode == "stepwise_service":
            from .service_environment import step_service
            return step_service(self, actions, trace)
        cfg, start = self.cfg, self.time
        end = min(cfg.end_time, start + cfg.turn_interval)
        old = self.clean_assignment()
        changes = sum(a != b for a, b in zip(actions, old))
        active = self.active_ids
        before = self.positions.copy()
        captured, escaped = [], []
        effort = partner_wait = peak = 0.0
        modes = ["IDLE"] * cfg.robots
        guards = [None] * cfg.robots
        frame_times = [round(start + i * cfg.step_dt, 10)
                       for i in range(round((end - start) / cfg.step_dt) + 1)]
        frame_positions = {time: before.copy() for time in frame_times} if trace else {}
        for target_id in active:
            target = self.scenario.targets[target_id]
            robots = [k for k, a in enumerate(actions) if a.target == target_id]
            if robots:
                roles = [actions[k].role for k in robots]
                result = rollout_target(cfg, target, self.positions[robots][None],
                                        np.array([role_offset(r, cfg) for r in roles])[None],
                                        np.array([complete_roles(target, roles)]),
                                        start, trace=trace, until=end)
                self.positions[robots] = result.positions[0]
                effort += float(result.effort[0])
                partner_wait += float(result.partner_wait[0])
                peak = max(peak, float(result.peak_speed[0]))
                for k in robots:
                    modes[k] = "TRAVEL"
                    guards[k] = 0.0
                if np.isfinite(result.capture_times[0]):
                    self.capture_times[target_id] = result.capture_times[0]
                    self.status[target_id] = "captured"
                    captured.append(target_id)
                elif np.isfinite(result.escape_times[0]):
                    self.escape_times[target_id] = result.escape_times[0]
                    self.status[target_id] = "escaped"
                    escaped.append(target_id)
                if trace:
                    for time, positions in result.frames:
                        key = round(time, 10)
                        if key in frame_positions:
                            frame_positions[key][robots] = positions[0]
            elif target.escape_time(cfg.side) <= end + 1e-10:
                self.escape_times[target_id] = target.escape_time(cfg.side)
                self.status[target_id] = "escaped"
                escaped.append(target_id)
        flow = late = 0.0
        for i in active:
            target = self.scenario.targets[i]
            stop = (self.capture_times[i] if i in captured else
                    self.escape_times[i] if i in escaped else end)
            flow += target.weight * max(0.0, stop - max(start, target.birth))
            late += target.weight * max(0.0, stop - max(start, target.birth, target.deadline))
        capture_gain = sum(self.scenario.targets[i].weight for i in captured) / cfg.weight_reference
        flow_penalty = cfg.flow_weight * flow / (cfg.weight_reference * cfg.stage_dt)
        late_penalty = cfg.late_weight * late / (cfg.weight_reference * cfg.stage_dt)
        effort_penalty = cfg.control_weight * effort / cfg.effort_reference
        terminal_penalty = (cfg.unfinished_weight * sum(
            t.weight for t in self.scenario.targets if self.status[t.id] != "captured")
            / cfg.weight_reference if end >= cfg.end_time - 1e-10 else 0.0)
        reward = capture_gain - flow_penalty - late_penalty - effort_penalty - terminal_penalty
        cost = cfg.change_cost * changes
        self.total_reward += reward
        self.total_change_cost += cost
        self.total_changes += changes
        self.total_effort += effort
        self.total_partner_wait += partner_wait
        self.peak_speed = max(self.peak_speed, peak)
        info = {
            "stage": self.stage, "start": start, "end": end, "visible_ids": list(active),
            "new_ids": list(self.new_ids), "assignment": [a.to_dict() for a in actions],
            "coalition_changes": self._coalition_log(old, actions),
            "changed_robots": changes, "modes": modes, "guard_peaks": guards,
            "positions_start": before.tolist(), "positions_end": self.positions.tolist(),
            "captured": captured, "escaped": escaped,
            "capture_events": [{"target": i, "time": float(self.capture_times[i])} for i in captured],
            "escape_events": [{"target": i, "time": float(self.escape_times[i])} for i in escaped],
            "flow": flow, "late": late, "effort": effort, "peak_speed": peak,
            "partner_wait": partner_wait, "model_mismatches": 0,
            "reward": reward, "change_cost": cost, "reward_with_changes": reward - cost,
            "reward_components": {"capture": capture_gain, "flow": -flow_penalty,
                                  "late": -late_penalty, "effort": -effort_penalty,
                                  "terminal": -terminal_penalty},
            "overdue_ids": [i for i in active if self.scenario.targets[i].deadline < end],
        }
        self._release_events(info, actions)
        if trace:
            frames = []
            for time in frame_times:
                actual_modes = modes.copy()
                if cfg.capture_mode == "stepwise_instant":
                    for k, action in enumerate(actions):
                        if action.target in captured + escaped:
                            stop = (self.capture_times[action.target] if action.target in captured
                                    else self.escape_times[action.target])
                            if time >= stop - 1e-10:
                                actual_modes[k] = "HOLD"
                frames.append({"time": time, "positions": frame_positions[time].tolist(),
                               "modes": actual_modes, "assignment": info["assignment"]})
            info["frames"] = frames
        self.last_assignment = actions
        if cfg.capture_mode == "stepwise_instant":
            self.last_assignment = self.clean_assignment()
        self.ended_ids = tuple(captured + escaped)
        self._time = end
        self.stage = min(cfg.max_stages, int(round(end / cfg.stage_dt))
                         if math.isclose(end / cfg.stage_dt, round(end / cfg.stage_dt), abs_tol=1e-9)
                         else math.floor(end / cfg.stage_dt))
        self.new_ids = self._activate()
        return StepResult(float(reward), self.done, info)
