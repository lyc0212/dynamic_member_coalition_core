"""Offline SW1 service prediction for the unassigned T1 at tick60."""
from dataclasses import dataclass
import math

import numpy as np

from pursuit_v2.config import Config
from pursuit_v2.service import ServiceState, advance_clock
from .policy import command, endpoint

START, END, DT = 60, 80, .05


@dataclass(frozen=True)
class Hypothesis:
    position: tuple[float, float]
    velocity: tuple[float, float]


def predict_windows(view, candidate, hypotheses, *, share_control=True):
    """Evaluate hypotheses without changing the public control state."""
    j = candidate["target"]
    target = next(t for t in view["targets"] if t["id"] == j)
    robots, roles = candidate["robots"], candidate["roles"]
    if (view["tick"] != START or view["end_tick"] < END or j != 1
            or view["beliefs"][j]["status"] != "PRIOR_ONLY"
            or target["service_duration"] <= (END-START)*DT
            or any(a["target"] == j for a in view["assignment"])
            or any(s["slot_key"]["target_id"] == j and s["state"] != "UNQUERIED"
                   for s in view["current_slots"])
            or len(robots) != 2 or len(set(robots)) != 2
            or set(roles) != {"dual_neg45", "dual_pos45"} or len(roles) != 2):
        raise ValueError("Outside SW1: expected fresh q2 T1 with no existing service or measurements")
    cfg = Config(**view["config"])
    for hypothesis in hypotheses:
        p, v = hypothesis.position, hypothesis.velocity
        if (len(p) != 2 or len(v) != 2 or not all(math.isfinite(x) for x in (*p,*v))
                or max(p[0],p[0]+v[0]*(END-START)*DT) >= cfg.side):
            raise ValueError("Unsupported physical hypothesis or window escape")

    def control_path():
        positions = np.asarray(view["positions"],dtype=float)
        frames = [(START,positions.copy(),np.zeros_like(positions))]
        for tick in range(START+1,END+1):
            controls = np.zeros_like(positions)
            for robot,role in zip(robots,roles):
                controls[robot] = command(view["beliefs"][j],tick-1,[positions[robot]],[role],cfg)[0]
            positions = positions + DT*controls
            frames.append((tick,positions,controls))
        return frames

    def service(hypothesis, path):
        # Only endpoint() sees this trajectory. Its bearing/WLS/Q path is the
        # original zero-noise contract. No synthetic observation updates belief.
        physical = dict(view,beliefs={j:dict(estimate_tick=START,last_observation_tick=None,
            position_estimate=hypothesis.position,velocity_estimate=hypothesis.velocity)})
        team = tuple(zip(robots,roles))
        clock = ServiceState(team=team)
        left = None
        frames, resets = [], []
        longest = streak = 0
        for tick,positions,controls in path:
            g,q = endpoint(physical,j,candidate,tick,positions,cfg)
            if left is not None:
                valid = left == (True,"PASS") and (g,q) == (True,"PASS")
                streak = streak+1 if valid else 0
                longest = max(longest,streak)
                clock, done, events = advance_clock(clock,target["service_duration"],team,valid,tick*DT)
                if done:
                    raise ValueError("Completion is outside the shared SW1 window")
                reasons = []
                if not g or not left[0]:
                    reasons.append("GEOMETRY_INVALID")
                if "FAIL" in (q,left[1]):
                    reasons.append("QUALITY_FAIL")
                if "UNKNOWN" in (q,left[1]):
                    reasons.append("QUALITY_UNKNOWN")
                resets.extend(dict(tick=tick,reasons=reasons,**event) for event in events)
            left = (g,q)
            frames.append(dict(tick=tick,G=g,Q=q,progress=clock.progress,
                               positions=positions.tolist(),control=controls.tolist()))
        return dict(frames=frames,resets=resets,longest_intervals=longest,
                    first_qualified_tick=next((f["tick"] for f in frames if f["G"] and f["Q"]=="PASS"),None),
                    final_progress=clock.progress,
                    control_effort=sum(float(np.sum(controls**2))*DT for _,_,controls in path[1:]))

    shared = control_path() if share_control else None
    return [service(h,shared if shared is not None else control_path()) for h in hypotheses]
