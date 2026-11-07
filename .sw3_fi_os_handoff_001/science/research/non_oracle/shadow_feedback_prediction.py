"""SW2 offline, fixed C6, zero-noise conditional feedback simulation."""
from copy import deepcopy
from dataclasses import dataclass
import math

import numpy as np

from pursuit_v2.config import Config
from pursuit_v2.service import ServiceState, advance_clock
from research.information_service_bridge.public_stream import BridgeFrameProcessor
from research.information_service_online.measurements import assemble_left_state
from research.information_service_online.public import IDS, segment_identity
from .policy import command

DT = .05
TEAM = ((0,"dual_neg45"),(1,"dual_pos45"))


@dataclass(frozen=True)
class WorldHypothesis:
    label: str
    position: tuple
    velocity: tuple
    offline_diagnostic: bool = False


def consume_model(queue, prior, speed_limit):
    """Mirror the production freeze at tick80, on a private MODEL-only queue."""
    belief = deepcopy(prior)
    history, decisions = [], []
    for observation in queue:
        if set(observation) != {"provenance","observation_origin","receipt_id","tick","available_tick","wls"}:
            raise ValueError("Unexpected shadow observation fields")
        if (observation["provenance"],observation["observation_origin"]) != ("SIMULATED","MODEL"):
            raise ValueError("Shadow queue accepts only simulated MODEL observations")
        t, available, e = (observation[k] for k in ("tick","available_tick","wls"))
        if available<t:
            raise ValueError("Negative model observation latency")
        reason = None
        if available>80:
            reason = "NOT_YET_AVAILABLE"
        elif e is None or not e.get("has_accepted_estimate") or not e.get("optimizer_converged") or any(
            e.get(k,True) for k in ("numerical_ill_conditioned","ambiguity_detected","boundary_active","numeric_contract_violation")
        ):
            reason = "ESTIMATOR_NOT_ADMISSIBLE"
        elif len(e["estimate"])!=2 or not all(math.isfinite(x) for x in e["estimate"]):
            reason = "INVALID_POSITION"
        elif history and t<=history[-1][0]:
            reason = "NONINCREASING_TICK"
        decisions.append(dict(receipt_id=observation["receipt_id"],measurement_tick=t,
                              available_tick=available,consumed=available<=80,accepted=reason is None,
                              rejection=reason))
        if reason is not None:
            continue
        p = list(e["estimate"])
        previous = next(((s,q) for s,q in reversed(history) if t-s>=5),None)
        velocity = list(belief["velocity_estimate"])
        if previous:
            s,q = previous
            velocity = [(x-y)/((t-s)*DT) for x,y in zip(p,q)]
            speed = math.hypot(*velocity)
            if speed>speed_limit:
                velocity = [v*speed_limit/speed for v in velocity]
        history.append((t,p))
        belief.update(estimate_tick=t,available_tick=available,position_estimate=p,velocity_estimate=velocity,
                      velocity_source="ACTUAL_POSITION_DIFFERENCE" if previous else belief["velocity_source"],
                      last_observation_tick=t,source="ACTUAL_WLS",status="OBSERVED",diagnostics=deepcopy(e))
    if belief["last_observation_tick"] is not None and 80-belief["last_observation_tick"]>20:
        belief["status"]="DEGRADED"
    return deepcopy(belief),history,decisions


def predict_feedback(view, hypothesis, *, prefix_check=None):
    if type(hypothesis) is not WorldHypothesis:
        raise TypeError("Explicit WorldHypothesis required")
    target = next(t for t in view["targets"] if t["id"]==1)
    history = next(h for h in view["histories"] if h["target_id"]==1)
    prior = deepcopy(view["beliefs"][1])
    cfg = Config(**view["config"])
    if (view["tick"]!=60 or view["end_tick"]<100 or history["segments"]
            or prior["status"]!="PRIOR_ONLY" or any(a["target"]==1 for a in view["assignment"])):
        raise ValueError("SW2 requires a fresh T1 at D60")
    if (len(hypothesis.position)!=2 or len(hypothesis.velocity)!=2
            or not all(math.isfinite(x) for x in (*hypothesis.position,*hypothesis.velocity))
            or max(hypothesis.position[0],hypothesis.position[0]+2*hypothesis.velocity[0])>=cfg.side):
        raise ValueError("SW2 hypotheses must remain in the non-escape window")
    team = [dict(robot_id=i,role=r) for i,r in TEAM]
    segment = dict(target_id=1,start_tick=60,segment_index=len(history["segments"]),
                   previous_segment_id=None,opened_by="INITIAL_ASSIGNMENT",team=team,
                   contract_id=IDS["service_segment"])
    segment["segment_id"] = segment_identity(segment)
    allowed = ["U0","U1"]

    def evolve(label, start, end, position, clock, left, belief):
        stream = f"SW2:MODEL:{hypothesis.label}:{label}:first{start if left is None else start+1}"
        bridge = BridgeFrameProcessor(allowed,start if left is None else start+1,stream,1)
        rows, queue = [], []
        positions = position.copy()
        first = start if left is None else start+1
        for tick in range(first,end+1):
            control = np.zeros_like(positions)
            if tick>start:
                control[:2] = command(belief,tick-1,positions[:2],[r for _,r in TEAM],cfg)
                positions = positions + DT*control
            point = [x+v*(tick*DT-3.) for x,v in zip(hypothesis.position,hypothesis.velocity)]
            profiles = [dict(p,observed_tick=tick) for p in view["sensor_profiles"]]
            slots = [dict(slot_key=dict(target_id=1,robot_id=i,tick=tick),state="UNQUERIED",packet=None,
                          contract_id=IDS["measurement_slot"],slot_digest=None) for i in range(len(profiles))]
            assembly = assemble_left_state(tick=tick,target_id=1,target_position=point,positions=positions.tolist(),
                sensor_profiles=profiles,current_slots=slots,team=team,stream_id=stream,actual=False)
            result = bridge.process(assembly["frame"])
            endpoint = (assembly["G"],result["quality"]["status"])
            resets, done = [], False
            if left is not None:
                clock,done,resets = advance_clock(clock,target["service_duration"],TEAM,
                                                  left==endpoint==(True,"PASS"),tick*DT)
            left = endpoint
            receipt = dict(provenance="SIMULATED",observation_origin="MODEL",receipt_id=result["frame_id"],
                           tick=tick,available_tick=tick,wls=deepcopy(result["estimate_result"]))
            queue.append(receipt)
            rows.append(dict(tick=tick,positions=positions.tolist(),control=control.tolist(),G=left[0],Q=left[1],
                progress=clock.progress,resets=resets,completed=done,released=[0,1] if done else [],
                segment_id=segment["segment_id"],assembly=assembly,result=result,
                provenance=dict(provenance="SIMULATED",observation_origin="MODEL",hypothesis=hypothesis.label,
                    stream_id=stream,input_source="offline reference" if hypothesis.offline_diagnostic else "public nominal",
                    offline_diagnostic=hypothesis.offline_diagnostic,receipt_id=receipt["receipt_id"])))
            if done:
                break
        return dict(rows=rows,estimator_calls=bridge.estimator_calls,first_new_fusion_tick=first),queue,positions,clock,left

    prefix,queue,positions,clock,left = evolve("prefix",60,80,np.array(view["positions"]),ServiceState(team=TEAM),None,prior)
    if prefix_check is not None:
        prefix_check(deepcopy(prefix))
    feedback, accepted, consumed = consume_model(queue,prior,target["speed_limit"])
    f0,*_ = evolve("F0",80,100,positions,clock,left,deepcopy(prior))
    f1,*_ = evolve("F1",80,100,positions,clock,left,deepcopy(feedback))
    return dict(segment=segment,prefix=prefix,F0=f0,F1=f1,
        feedback=dict(provenance="SIMULATED",observation_origin="MODEL",hypothesis=hypothesis.label,
                      offline_diagnostic=hypothesis.offline_diagnostic,mirror_id=prefix["rows"][-1]["result"]["frame_id"]+":freeze80",
                      internal_science_mirror=feedback,accepted_history=accepted,consumption=consumed))
