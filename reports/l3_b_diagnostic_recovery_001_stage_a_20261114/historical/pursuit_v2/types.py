from __future__ import annotations

from dataclasses import dataclass
from bisect import bisect_right
from functools import lru_cache
import math
import numpy as np

from .config import Config


@dataclass(frozen=True)
class Assignment:
    target: int | None = None
    role: str = "none"

    def to_dict(self):
        return {"target": self.target, "role": self.role}


IDLE = Assignment()


def _arc_step(point, velocity, rate: float, duration: float):
    """Exact constant-speed, constant-turn-rate motion over one interval."""
    point = np.asarray(point, dtype=float)
    velocity = np.asarray(velocity, dtype=float)
    if abs(rate) <= 1e-12:
        return point + velocity * duration, velocity.copy()
    speed = float(np.linalg.norm(velocity))
    angle = math.atan2(velocity[1], velocity[0])
    next_angle = angle + rate * duration
    displacement = speed / rate * np.array((math.sin(next_angle) - math.sin(angle),
                                             math.cos(angle) - math.cos(next_angle)))
    return point + displacement, speed * np.array((math.cos(next_angle),
                                                   math.sin(next_angle)))


def _arc_crossing(point, velocity, rate: float, duration: float, side: float):
    """Earliest east-boundary crossing, including between integration ticks."""
    if point[0] >= side:
        return 0.0
    if abs(rate) <= 1e-12:
        return (side - point[0]) / velocity[0] if velocity[0] > 0 and \
            (side - point[0]) / velocity[0] <= duration + 1e-10 else None
    angle = math.atan2(velocity[1], velocity[0])
    end_angle = angle + rate * duration
    low, high = sorted((angle, end_angle))
    cuts = [0.0, duration]
    for k in range(math.floor((low - math.pi / 2) / math.pi),
                   math.ceil((high - math.pi / 2) / math.pi) + 1):
        crossing_angle = math.pi / 2 + k * math.pi
        at = (crossing_angle - angle) / rate
        if 1e-12 < at < duration - 1e-12:
            cuts.append(at)
    cuts.sort()
    def x_at(at):
        return _arc_step(point, velocity, rate, at)[0][0]
    for left, right in zip(cuts[:-1], cuts[1:]):
        if x_at(left) >= side - 1e-12:
            return left
        if x_at(right) < side - 1e-12:
            continue
        lo, hi = left, right
        for _ in range(56):
            mid = (lo + hi) / 2
            if x_at(mid) >= side:
                hi = mid
            else:
                lo = mid
        return hi
    return None


@dataclass(frozen=True)
class Target:
    id: int
    birth: float
    position_at_birth: tuple[float, float]
    velocity: tuple[float, float]
    required_robots: int
    weight: float
    deadline: float
    turns: tuple[tuple[float, float, float], ...] = ()
    turn_increment: float = 0.0
    arc_rates: tuple[tuple[float, float], ...] = ()
    service_duration: float | None = None

    def __post_init__(self):
        if self.service_duration is not None and (
                isinstance(self.service_duration, bool) or
                not isinstance(self.service_duration, (int, float)) or
                not math.isfinite(self.service_duration) or self.service_duration <= 0):
            raise ValueError("service_duration must be a finite positive number")
        object.__setattr__(self, "position_at_birth", tuple(self.position_at_birth))
        object.__setattr__(self, "velocity", tuple(self.velocity))
        object.__setattr__(self, "turns", tuple(tuple(turn) for turn in self.turns))
        object.__setattr__(self, "arc_rates", tuple(tuple(event) for event in self.arc_rates))
        if isinstance(self.id, bool) or not isinstance(self.id, int) or self.id < 0:
            raise ValueError("Target ID must be a nonnegative integer")
        if len(self.position_at_birth) != 2 or len(self.velocity) != 2:
            raise ValueError("Target vectors must have two coordinates")
        values = (*self.position_at_birth, *self.velocity, self.birth, self.weight,
                  self.deadline, self.turn_increment)
        if not all(math.isfinite(v) for v in values):
            raise ValueError("Target data must be finite")
        if (isinstance(self.required_robots, bool) or not isinstance(self.required_robots, int)
                or self.required_robots not in (1, 2, 3) or self.weight <= 0 or self.birth < 0
                or self.deadline < self.birth or self.velocity[0] < 0):
            raise ValueError("Require q=1/2/3, positive weight, valid times and eastward velocity")
        previous = self.birth
        for time, vx, vy in self.turns:
            if not all(math.isfinite(x) for x in (time, vx, vy)) or time <= previous or vx < 0:
                raise ValueError("Turns must have increasing times and eastward finite velocities")
            previous = time
        if self.turns and self.arc_rates:
            raise ValueError("Use either velocity jumps or continuous turn rates")
        previous = self.birth
        for time, rate in self.arc_rates:
            if not math.isfinite(time) or not math.isfinite(rate) or time <= previous:
                raise ValueError("Arc rates need finite, increasing start times")
            previous = time

    @lru_cache(maxsize=8192)
    def _arc_segments(self):
        point = np.asarray(self.position_at_birth, dtype=float)
        velocity = np.asarray(self.velocity, dtype=float)
        previous, rate = self.birth, 0.0
        times = [previous]
        points = [tuple(point)]
        velocities = [tuple(velocity)]
        rates = [rate]
        for change_time, next_rate in self.arc_rates:
            point, velocity = _arc_step(point, velocity, rate, change_time - previous)
            previous, rate = change_time, next_rate
            times.append(previous)
            points.append(tuple(point))
            velocities.append(tuple(velocity))
            rates.append(rate)
        return tuple(times), tuple(points), tuple(velocities), tuple(rates)

    def _arc_state(self, time: float):
        times, points, velocities, rates = self._arc_segments()
        index = max(0, bisect_right(times, time) - 1)
        return _arc_step(points[index], velocities[index], rates[index],
                         time - times[index])

    def position(self, time: float) -> np.ndarray:
        if self.arc_rates:
            return self._arc_state(time)[0]
        point = np.asarray(self.position_at_birth, dtype=float).copy()
        velocity = np.asarray(self.velocity, dtype=float)
        previous = self.birth
        for turn_time, vx, vy in self.turns:
            if time <= turn_time:
                break
            point += velocity * (turn_time - previous)
            previous = turn_time
            velocity = np.array([vx, vy])
        return point + velocity * (time - previous)

    def velocity_at(self, time: float) -> np.ndarray:
        if self.arc_rates:
            return self._arc_state(time)[1]
        velocity = self.velocity
        for turn_time, vx, vy in self.turns:
            if time < turn_time - 1e-10:
                break
            velocity = (vx, vy)
        return np.asarray(velocity, dtype=float)

    @lru_cache(maxsize=8192)
    def escape_time(self, side: float) -> float:
        if self.arc_rates:
            times, points, velocities, rates = self._arc_segments()
            for index in range(len(times) - 1):
                duration = times[index + 1] - times[index]
                hit = _arc_crossing(points[index], velocities[index],
                                    rates[index], duration, side)
                if hit is not None:
                    return times[index] + hit
            rate = rates[-1]
            duration = 2 * math.pi / abs(rate) if abs(rate) > 1e-12 else math.inf
            hit = _arc_crossing(points[-1], velocities[-1], rate, duration, side)
            return times[-1] + hit if hit is not None else math.inf
        if self.position_at_birth[0] >= side:
            return self.birth
        x, previous, vx = self.position_at_birth[0], self.birth, self.velocity[0]
        for turn_time, next_vx, _ in self.turns:
            if vx > 0 and x + vx * (turn_time - previous) >= side:
                return previous + (side - x) / vx
            x += vx * (turn_time - previous)
            previous, vx = turn_time, next_vx
        return previous + (side - x) / vx if vx > 0 else math.inf

    def to_dict(self):
        result = {"id": self.id, "birth": self.birth, "position_at_birth": self.position_at_birth,
                "velocity": self.velocity, "required_robots": self.required_robots,
                "weight": self.weight, "deadline": self.deadline}
        if self.turns:
            result["turns"] = self.turns
        if self.arc_rates:
            result["arc_rates"] = self.arc_rates
        if self.service_duration is not None:
            result["service_duration"] = self.service_duration
        return result

    def observed(self, now: float) -> "Target":
        """Current state with a constant-velocity extrapolation; future turns stay hidden."""
        velocity = self.velocity_at(now)
        origin = self.position(now) - velocity * (now - self.birth)
        if self.arc_rates:
            return Target(self.id, self.birth, tuple(origin), tuple(velocity),
                          self.required_robots, self.weight, self.deadline,
                          service_duration=self.service_duration)
        previous_velocity = self.velocity
        increment = 0.0
        for turn_time, vx, vy in self.turns:
            if turn_time > now + 1e-10:
                break
            increment = math.atan2(vy, vx) - math.atan2(previous_velocity[1],
                                                        previous_velocity[0])
            previous_velocity = (vx, vy)
        return Target(self.id, self.birth, tuple(origin), tuple(velocity),
                      self.required_robots, self.weight, self.deadline,
                      turn_increment=increment, service_duration=self.service_duration)


@dataclass(frozen=True)
class Scenario:
    pursuers: np.ndarray
    targets: tuple[Target, ...]

    def __post_init__(self):
        positions = np.array(self.pursuers, dtype=float, copy=True)
        if positions.ndim != 2 or positions.shape[1] != 2 or not np.isfinite(positions).all():
            raise ValueError("Stage-one scenarios require independent positions[robot, xy]; legacy paired scenes are rejected")
        positions.setflags(write=False)
        object.__setattr__(self, "pursuers", positions)
        object.__setattr__(self, "targets", tuple(self.targets))

    def to_dict(self):
        return {"pursuers": self.pursuers.tolist(), "targets": [t.to_dict() for t in self.targets]}


@dataclass(frozen=True)
class Observation:
    """The entire scheduler interface. It contains no future targets or RNG state."""
    config: Config
    stage: int
    positions: np.ndarray
    targets: tuple[Target, ...]
    assignment: tuple[Assignment, ...]
    new_ids: tuple[int, ...]
    ended_ids: tuple[int, ...]
    time_override: float | None = None
    service_states: tuple = ()

    @property
    def time(self):
        return self.stage * self.config.stage_dt if self.time_override is None else self.time_override


def role_offset(role: str, cfg: Config) -> np.ndarray:
    if role not in ("center", "upper", "lower"):
        raise ValueError(f"Unknown active role: {role}")
    return np.array([0.0, {"center": 0.0, "upper": cfg.anchor_offset,
                           "lower": -cfg.anchor_offset}[role]])


def complete_roles(target: Target, roles) -> bool:
    if target.required_robots not in (1, 2):
        raise ValueError('Legacy role helper requires q=1/2')
    return (tuple(roles) == ("center",) if target.required_robots == 1
            else len(roles) == 2 and set(roles) == {"upper", "lower"})
