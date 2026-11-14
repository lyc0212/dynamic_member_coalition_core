"""SW3 private sampling with the versioned production-physics admission gate."""
from copy import deepcopy
import math

import numpy as np

from pursuit_v2.config import Config
from pursuit_v2.environment import Environment
from pursuit_v2.types import Scenario, Target
from .sw3_c1_private_worlds import CENTERS, draw_component, reject_motion


def construct(world):
    cfg = Config(**world["config"])
    targets = tuple(Target(**entry) for entry in deepcopy(world["targets"]))
    return Environment(cfg, Scenario(np.asarray(world["positions_initial"], dtype=float), targets))


def sample(template, split, n, w, previous, *, replaces=None):
    if type(w) is not int or not 0 <= w < 4 or len(previous) != w:
        raise ValueError("Supply previous accepted worlds in order")
    cfg = template["config"]
    t1 = template["targets"][1]
    if (cfg["motion_model"] != "continuous_turn" or cfg["turn_max_angle"] != .5
            or t1["turns"] or not t1["arc_rates"] or any(rate != 0 for _, rate in t1["arc_rates"])):
        raise ValueError("Unexpected fixed SW3 physics template")
    construct(template)
    seen = {(tuple(world["targets"][1]["position_at_birth"]),
             tuple(world["targets"][1]["velocity"])) for world in previous}
    attempts = []
    for a in range(32):
        draws = [draw_component(split, n, w, a, j, replaces=replaces) for j in range(4)]
        u0, u1, u2, u3 = (d[2] for d in draws)
        x, y = CENTERS[n]
        r, theta = .5 * math.sqrt(u0), 2 * math.pi * u1
        speed, angle = .8 * math.sqrt(u2), math.pi * (u3 - .5)
        p = (x + r * math.cos(theta), y + r * math.sin(theta))
        v = (speed * math.cos(angle), speed * math.sin(angle))
        heading = math.atan2(v[1], v[0])
        reason = reject_motion(p, v, cfg["side"], seen)
        if reason is None and abs(heading) > cfg["turn_max_angle"] + 1e-8:
            reason = "HEADING_OUT_OF_PHYSICAL_ENVELOPE"
        row = dict(a=a, draws=draws, position=p, velocity=v, heading=heading,
                   rejection=reason, constructor="NOT_RUN")
        attempts.append(row)
        if reason is not None:
            continue
        world = deepcopy(template)
        world["targets"][1].update(position_at_birth=list(p), velocity=list(v))
        # Any remaining exception is unclassified and must stop the run.
        construct(world)
        row["constructor"] = "PASS"
        return dict(status="ACCEPTED", world=world, attempts=attempts,
                    accepted_a=a, accepted_heading=heading)
    return dict(status="EXHAUSTED", world=None, attempts=attempts)
