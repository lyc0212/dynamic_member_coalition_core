"""SW3-B single-branch conditional simulator; never runs the SW2 F0 branch."""
from copy import deepcopy
from time import perf_counter, process_time

import numpy as np

from pursuit_v2.service import ServiceState, advance_clock
from research.information_service_bridge.public_stream import BridgeFrameProcessor
from research.information_service_online.measurements import assemble_left_state
from research.information_service_online.public import IDS, segment_identity
from .policy import command
from .shadow_feedback_prediction import DT, TEAM, WorldHypothesis, consume_model
from .sw3_public_hypotheses import legal, library, public_fingerprint, public_input, select_hypotheses


def outcome(last, horizon=100):
    if last["tick"]>horizon or not last["completed"] and last["tick"]!=horizon:
        raise ValueError("Incomplete or out-of-horizon simulation")
    return dict(completed_by_H=last["completed"],completion_tick=last["tick"] if last["completed"] else None,
                observation_end_tick=horizon,terminal_status="COMPLETED" if last["completed"] else "ACTIVE_AT_H")


def predict_f1(public_d60, public_hypothesis, horizon_tick=100):
    wall,cpu = perf_counter(),process_time()
    view,cfg,target = public_input(public_d60)
    hypothesis = public_hypothesis
    if horizon_tick!=100 or type(hypothesis) is not WorldHypothesis or not legal(hypothesis,cfg,target):
        raise ValueError("Unsupported horizon or hypothesis")
    if not hypothesis.offline_diagnostic and hypothesis not in library(target,cfg)[1]:
        raise ValueError("Online hypothesis is outside the public library")
    history = next(h for h in view["histories"] if h["target_id"]==1)
    prior = deepcopy(view["beliefs"][1])
    team = [dict(robot_id=i,role=r) for i,r in TEAM]
    segment = dict(target_id=1,start_tick=60,segment_index=len(history["segments"]),
                   previous_segment_id=None,opened_by="INITIAL_ASSIGNMENT",team=team,
                   contract_id=IDS["service_segment"])
    segment["segment_id"] = segment_identity(segment)
    allowed = ["U0","U1"]

    def evolve(label, start, end, position, clock, left, belief):
        stream = f"SW3:MODEL:{hypothesis.label}:{label}:first{start if left is None else start+1}"
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
                    stream_id=stream,input_source="offline reference" if hypothesis.offline_diagnostic else "public hypothesis",
                    offline_diagnostic=hypothesis.offline_diagnostic,receipt_id=receipt["receipt_id"])))
            if done:
                break
        return dict(rows=rows,estimator_calls=bridge.estimator_calls,first_new_fusion_tick=first),queue,positions,clock,left

    prefix,queue,positions,clock,left = evolve("prefix",60,80,np.array(view["positions"]),ServiceState(team=TEAM),None,prior)

    feedback,accepted,consumed = consume_model(queue,prior,target["speed_limit"])
    f1,*_ = evolve("F1",80,100,positions,clock,left,feedback)
    frames = prefix["rows"]+f1["rows"]
    longest = streak = 0
    for a,b in zip(frames,frames[1:]):
        streak = streak+1 if a["G"] and b["G"] and a["Q"]==b["Q"]=="PASS" else 0
        longest = max(longest,streak)
    last = frames[-1]
    count = prefix["estimator_calls"]+f1["estimator_calls"]
    if count>41:
        raise AssertionError("F1-only WLS budget exceeded")
    return dict(kind="PREDICTION_ONLY",provenance="SIMULATED",observation_origin="MODEL",
        public_sha256=public_fingerprint(view),hypothesis=hypothesis.label,offline_diagnostic=hypothesis.offline_diagnostic,
        Y_H=outcome(last),actual_simulation_end_tick=last["tick"],progress=last["progress"],
        longest_intervals=longest,remaining_service=max(0.,target["service_duration"]-last["progress"]),
        segment=segment,prefix=prefix,F1=f1,
        feedback=dict(provenance="SIMULATED",observation_origin="MODEL",hypothesis=hypothesis.label,
                      offline_diagnostic=hypothesis.offline_diagnostic,
                      mirror_id=prefix["rows"][-1]["result"]["frame_id"]+":freeze80",
                      internal_science_mirror=feedback,accepted_history=accepted,consumption=consumed),
        resets=[dict(tick=f["tick"],**r) for f in frames for r in f["resets"]],released=last["released"],
        cost=dict(wls=count,frames=len(frames),intervals=len(frames)-1,
                  wall=perf_counter()-wall,cpu=process_time()-cpu))


def aggregate(results):
    if not results or len({r["public_sha256"] for r in results})!=1:
        raise ValueError("A nonempty same-cut result list is required")
    if any(r["offline_diagnostic"] for r in results):
        raise ValueError("Offline diagnostic results cannot enter public aggregation")
    statuses = sorted({r["Y_H"]["completed_by_H"] for r in results})
    ticks = sorted({r["Y_H"]["completion_tick"] for r in results if r["Y_H"]["completed_by_H"]})
    return dict(predicted_completion_status_set=statuses,predicted_completion_ticks=ticks,
                completion_time_envelope=[ticks[0],ticks[-1]] if ticks else None,
                noncompletion_possible=False in statuses,results=deepcopy(results),
                cost={k:sum(r["cost"][k] for r in results) for k in ("wls","frames","intervals","wall","cpu")})


def predict_method(view,method):
    wall,cpu = perf_counter(),process_time()
    selection = select_hypotheses(view,method)
    prediction = aggregate([predict_f1(view,h) for h in selection["selected"]])
    return dict(method=method,selection=selection,prediction=prediction,
                end_to_end=dict(wall=perf_counter()-wall,cpu=process_time()-cpu))
