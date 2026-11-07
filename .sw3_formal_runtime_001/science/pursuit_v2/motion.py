"""Shared discrete target-motion update for scenario truth and online forecasts."""
from __future__ import annotations

import math

import numpy as np


def motion_step(cfg, angle: float, speed: float, turn_increment: float,
                event_index: int, turn_rng, speed_rng):
    """Advance one motion tick; a sampled heading increment can persist for several ticks."""
    if cfg.turn_max_angle > 0:
        innovation = float(turn_rng.uniform(-cfg.turn_max_angle, cfg.turn_max_angle))
        if (event_index - 1) % cfg.turn_hold_ticks == 0:
            turn_increment = innovation
        angle = float(np.clip(angle + turn_increment,
                              -cfg.turn_max_angle, cfg.turn_max_angle))
    if cfg.speed_delta_max > 0:
        speed = float(np.clip(speed + speed_rng.uniform(-cfg.speed_delta_max,
                                                       cfg.speed_delta_max),
                              cfg.target_speed_min, cfg.target_speed_max))
    return angle, speed, turn_increment, (speed * math.cos(angle), speed * math.sin(angle))
