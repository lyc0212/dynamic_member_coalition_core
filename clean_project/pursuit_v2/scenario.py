from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import numpy as np

from .config import Config
from .motion import motion_step
from .types import Scenario, Target


def generate_scenario(cfg: Config, seed: int) -> Scenario:
    rng = np.random.default_rng(seed)
    pursuers = rng.uniform([0.05 * cfg.side, 0.1 * cfg.side],
                           [0.30 * cfg.side, 0.9 * cfg.side], size=(cfg.robots, 2))
    initial = math.ceil(cfg.initial_fraction * cfg.task_count)
    arrival_times = np.array([3.0, 6.0, 9.0])
    arrival_times = arrival_times[arrival_times < cfg.end_time]
    # For custom stage lengths, retain boundary-only births.
    arrival_times = np.unique(np.ceil(arrival_times / cfg.stage_dt) * cfg.stage_dt)
    arrival_times = arrival_times[arrival_times < cfg.end_time]
    if not len(arrival_times):
        initial = cfg.task_count
    births = [0.0] * initial + sorted(rng.choice(arrival_times, cfg.task_count - initial).tolist())
    targets = []
    for i, birth in enumerate(births):
        xy = rng.uniform([0.45 * cfg.side, 0.1 * cfg.side],
                         [0.70 * cfg.side, 0.9 * cfg.side])
        speed = float(rng.uniform(cfg.target_speed_min, cfg.target_speed_max))
        demand = 2 if rng.random() < cfg.two_robot_probability else 1
        weight = float(rng.choice([1, 2, 4]))
        deadline = birth + float(rng.choice([6, 9, 12]))
        targets.append(Target(i, birth, tuple(xy), (speed, 0.0), demand, weight, deadline))
    if cfg.motion_model == "continuous_turn":
        turn_rng = np.random.default_rng(np.random.SeedSequence([seed, 112358]))
        speed_rng = np.random.default_rng(np.random.SeedSequence([seed, 112359]))
        moving = []
        for target in targets:
            speed = float(np.linalg.norm(target.velocity))
            angle = 0.0
            rates = []
            event_count = round((cfg.end_time - target.birth) / cfg.turn_interval)
            for index in range(1, event_count):
                next_angle, speed, _, _ = motion_step(
                    cfg, angle, speed, 0.0, index, turn_rng, speed_rng)
                rates.append((float(target.birth + index * cfg.turn_interval),
                              (next_angle - angle) / cfg.turn_interval))
                angle = next_angle
            rates.append((cfg.end_time, 0.0))
            moving.append(Target(target.id, target.birth, target.position_at_birth,
                                 target.velocity, target.required_robots, target.weight,
                                 target.deadline, arc_rates=tuple(rates)))
        targets = moving
    elif cfg.turn_max_angle > 0 or cfg.speed_delta_max > 0:
        turn_rng = np.random.default_rng(np.random.SeedSequence([seed, 112358]))
        speed_rng = np.random.default_rng(np.random.SeedSequence([seed, 112359]))
        moving = []
        for target in targets:
            speed = float(np.linalg.norm(target.velocity))
            angle = 0.0
            increment = 0.0
            turns = []
            event_count = round((cfg.end_time - target.birth) / cfg.turn_interval)
            for index in range(1, event_count):
                angle, speed, increment, velocity = motion_step(
                    cfg, angle, speed, increment, index, turn_rng, speed_rng)
                turns.append((float(target.birth + index * cfg.turn_interval), *velocity))
            moving.append(Target(target.id, target.birth, target.position_at_birth,
                                 target.velocity, target.required_robots, target.weight,
                                 target.deadline, tuple(turns)))
        targets = moving
    return Scenario(pursuers, tuple(targets))


def scenario_hash(scenario: Scenario) -> str:
    raw = json.dumps(scenario.to_dict(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def save_scenario(path: str | Path, cfg: Config, scenario: Scenario):
    Path(path).write_text(json.dumps({"config": cfg.to_dict(), "scenario": scenario.to_dict()},
                                    ensure_ascii=False, indent=2), encoding="utf-8")


def load_scenario(path: str | Path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if "clusters" in data["config"] or any("required_clusters" in t for t in data["scenario"]["targets"]):
        raise ValueError("Legacy fixed-pair scene rejected: physical demand has changed; construct a new robot scene")
    cfg = Config(**data["config"])
    raw = data["scenario"]
    from .observation_geometry import required_roles
    for task in raw['targets']:
        required_roles(task['required_robots'], cfg)
    return cfg, Scenario(raw["pursuers"], tuple(Target(**t) for t in raw["targets"]))
