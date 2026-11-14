from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path


@dataclass(frozen=True)
class Config:
    robots: int = 6
    task_count: int = 4
    side: float | None = None
    stage_dt: float = 3.0
    capture_check: float = 2.8
    step_dt: float = 0.05
    max_stages: int = 10
    prediction_stages: int = 3
    max_plan_age: int = 3
    max_speed: float = 3.0
    travel_gain: float = 1.0
    capture_radius: float = 0.3
    anchor_offset: float = 0.6
    time_gain: float = 2.0
    singularity_epsilon: float = 0.02
    hold_gain: float = 2.0
    target_speed_min: float = 0.4
    target_speed_max: float = 0.8
    turn_interval: float = 1.0
    turn_max_angle: float = 0.5
    turn_hold_ticks: int = 1
    speed_delta_max: float = 0.0
    motion_model: str = "continuous_turn"
    risk_samples: int = 8
    risk_trigger_samples: int = 2
    risk_prediction_dt: float | None = None
    risk_threshold: float = 0.65
    local_substitutes: int = 2
    initial_fraction: float = 0.6
    two_robot_probability: float = 0.4
    flow_weight: float = 0.1
    late_weight: float = 0.3
    control_weight: float = 0.02
    unfinished_weight: float = 2.0
    control_reference: float = 10.0
    change_cost: float = 0.01
    capture_mode: str = "stepwise_instant"
    geometry_mode: str = "legacy_anchor"
    observation_radius: float = 0.6
    observation_tolerance: float = 0.15

    def __post_init__(self):
        if self.task_count is None:
            object.__setattr__(self, "task_count", math.ceil(1.5 * self.robots))
        if self.side is None:
            object.__setattr__(self, "side", 20.0 * math.sqrt(self.robots / 3))
        if self.risk_prediction_dt is None:
            object.__setattr__(self, "risk_prediction_dt", self.step_dt)
        if self.motion_model not in ("piecewise_velocity", "continuous_turn"):
            raise ValueError("Unknown target motion model")
        if self.capture_mode not in ("fixed_check_legacy", "stepwise_instant", "stepwise_service"):
            raise ValueError("Unknown capture mode")
        for key, value in asdict(self).items():
            if key in ("motion_model", "capture_mode", "geometry_mode"):
                continue
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError(f"{key} must be finite numeric data")
        if self.geometry_mode not in ('legacy_anchor', 'angular_standoff_v1'):
            raise ValueError('Unknown geometry mode')
        if self.geometry_mode == 'angular_standoff_v1':
            rho = self.observation_tolerance + 1e-10
            if (self.capture_mode != 'stepwise_service' or self.observation_tolerance <= 0
                    or not 0 < rho < self.observation_radius
                    or rho / self.observation_radius >= math.sin(math.pi/4)):
                raise ValueError('Invalid angular service geometry parameters')
        elif self.observation_radius != .6 or self.observation_tolerance != .15:
            raise ValueError('Observation parameters require angular geometry')
        for key in ("robots", "task_count", "max_stages", "prediction_stages", "max_plan_age",
                    "risk_samples", "risk_trigger_samples", "turn_hold_ticks"):
            value = getattr(self, key)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{key} must be a positive integer")
        if not 2 <= self.robots <= 16:
            raise ValueError("This exact small-scale benchmark supports 2..16 robots")
        if not 0 < self.singularity_epsilon < self.capture_check < self.stage_dt:
            raise ValueError("Require 0 < epsilon < capture_check < stage_dt")
        for key in ("side", "step_dt", "max_speed", "travel_gain", "capture_radius",
                    "hold_gain", "control_reference"):
            if getattr(self, key) <= 0:
                raise ValueError(f"{key} must be positive")
        if self.time_gain <= 1 or self.anchor_offset <= self.capture_radius:
            raise ValueError("Require time_gain > 1 and disjoint upper/lower capture disks")
        for duration in (self.stage_dt, self.capture_check):
            if not math.isclose(duration / self.step_dt, round(duration / self.step_dt),
                                abs_tol=1e-9):
                raise ValueError("stage_dt and capture_check must be multiples of step_dt")
        if not 0 <= self.target_speed_min <= self.target_speed_max:
            raise ValueError("Invalid target speed range")
        if self.turn_interval < 0 or not 0 <= self.turn_max_angle < math.pi / 2:
            raise ValueError("Invalid turn model")
        if self.turn_max_angle > 0 and self.turn_interval <= 0:
            raise ValueError("Positive turn_max_angle requires turn_interval")
        if self.speed_delta_max < 0 or (self.speed_delta_max > 0 and self.turn_interval <= 0):
            raise ValueError("Speed changes require a nonnegative bound and turn_interval")
        if self.turn_hold_ticks > 1 and self.turn_max_angle <= 0:
            raise ValueError("Persistent turns require positive turn_max_angle")
        if (self.motion_model == "continuous_turn" and
                (self.turn_interval <= 0 or self.speed_delta_max != 0 or
                 self.turn_hold_ticks != 1)):
            raise ValueError("Continuous turns currently require fixed speed and one-tick rates")
        if self.turn_interval and not math.isclose(self.turn_interval / self.step_dt,
                                                   round(self.turn_interval / self.step_dt), abs_tol=1e-9):
            raise ValueError("turn_interval must be a multiple of step_dt")
        if self.risk_prediction_dt < self.step_dt:
            raise ValueError("risk_prediction_dt must be at least step_dt")
        if self.capture_mode in ("stepwise_instant", "stepwise_service") and any(
                not math.isclose(dt, 0.05, rel_tol=0.0, abs_tol=1e-12)
                for dt in (self.step_dt, self.risk_prediction_dt)):
            raise ValueError(f"{self.capture_mode} requires step_dt and risk_prediction_dt = 0.05")
        for duration in (self.stage_dt, self.capture_check, self.turn_interval):
            if duration and not math.isclose(duration / self.risk_prediction_dt,
                                             round(duration / self.risk_prediction_dt), abs_tol=1e-9):
                raise ValueError("risk_prediction_dt must divide stage, check and turn times")
        if (self.turn_max_angle or self.speed_delta_max or
                self.motion_model == "continuous_turn") and not math.isclose(
                                                    self.stage_dt / self.turn_interval,
                                                    round(self.stage_dt / self.turn_interval), abs_tol=1e-9):
            raise ValueError("turn_interval must divide stage_dt for online decisions")
        if not 0 <= self.risk_threshold <= 1 or self.local_substitutes < 0:
            raise ValueError("Invalid risk policy settings")
        if not 0 < self.initial_fraction <= 1 or not 0 <= self.two_robot_probability <= 1:
            raise ValueError("Invalid generation probabilities")
        for key in ("flow_weight", "late_weight", "control_weight",
                    "unfinished_weight", "change_cost"):
            if getattr(self, key) < 0:
                raise ValueError(f"{key} must be nonnegative")

    @property
    def weight_reference(self) -> float:
        return 4.0 * self.task_count

    @property
    def effort_reference(self) -> float:
        return self.robots * self.stage_dt * self.control_reference ** 2

    @property
    def end_time(self) -> float:
        return self.stage_dt * self.max_stages

    def to_dict(self):
        result = asdict(self)
        if self.geometry_mode == 'legacy_anchor':
            for key in ('geometry_mode', 'observation_radius', 'observation_tolerance'):
                result.pop(key)
        return result

    @classmethod
    def load(cls, path: str | Path):
        return cls(**json.loads(Path(path).read_text(encoding="utf-8-sig")))
