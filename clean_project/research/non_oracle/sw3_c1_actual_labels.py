"""Independent fixed-action labels from production physical execution."""
from copy import deepcopy
from time import perf_counter, process_time

from scripts.run_a1 import Sensing
from .environment import StaggeredEnvironment


def actions(target):
    return [dict(target=target,role="dual_neg45"),dict(target=target,role="dual_pos45"),
            dict(target=None,role="none")]


def extract_label(step, state):
    if step["status"]!="COMMITTED" or step["end_tick"]!=100 or state["tick"]!=100:
        raise ValueError("Incomplete actual label horizon")
    status = state["statuses"][1]
    archive = state["archives"].get("1")
    events = [e for e in state["events"] if e["target_id"]==1 and e["kind"]=="COMPLETED"]
    if status=="completed" and len(events)==1 and archive:
        event = events[0]
        tick = event["at"]["event_tick"]
        if (type(tick) is not int or not 60<=tick<=100 or archive["terminal_status"]!="completed"
                or archive["terminal_at"]!=event["at"] or archive["closing_event_index"]!=event["event_index"]
                or event not in step["events"] or archive["released_robots"]!=[0,1]
                or any(a["target"]==1 for a in state["assignment"])):
            raise ValueError("Inconsistent actual completion archive")
        return dict(source="ACTUAL",completed_by_H=True,completion_tick=tick,
                    observation_end_tick=100,terminal_status="COMPLETED")
    if status=="active" and archive is None and not events:
        return dict(source="ACTUAL",completed_by_H=False,completion_tick=None,
                    observation_end_tick=100,terminal_status="ACTIVE_AT_H")
    raise ValueError("Invalid actual label; not ordinary noncompletion")


def run_reference(world, announcements, instance, *, public_gate, record):
    """Callbacks receive copies; only the D60 gate is exposed to the public lane."""
    wall,cpu = perf_counter(),process_time()
    env = StaggeredEnvironment(world,Sensing(),instance,announcements["announcements"])
    counts = []
    for tick in (0,20,40,60,80):
        if env.tick!=tick:
            raise ValueError("Unexpected decision cut")
        view = env.prepare_decision()
        if tick<60 and ([t["id"] for t in view["targets"]]!=[0] or 1 in view["beliefs"]):
            raise ValueError("T1 visible before its legal cut")
        if tick==60:
            public_gate(deepcopy(view))
        before = env.metrics()
        chosen = actions(0 if tick<60 else 1)
        result = env.step(chosen,env.observe_public()["checkpoint_id"],tick,f"fixed-D{tick}")
        record(tick,dict(policy_input=deepcopy(view),step=result,consumed=deepcopy(env.beliefs.consumed)))
        if result["status"]!="COMMITTED" or result["end_tick"]!=tick+20:
            raise ValueError(f"Fixed action failed at {tick}")
        after=env.metrics()
        counts.append(dict(tick=tick,wls=after["reported_estimator_calls"]-before["reported_estimator_calls"],
            fusions=len(result["fusion_records"]),sampling=after["actual_sampling_attempts"]-before["actual_sampling_attempts"]))
        if tick<60 and any(x["frame"]["target_id"]==1 for x in result["fusion_records"]):
            raise ValueError("T1 sampled before allocation")
    prefix=sum(x["wls"] for x in counts[:3])
    window=sum(x["wls"] for x in counts[3:])
    if prefix>61 or window>41:
        raise ValueError("Reference WLS budget exceeded")
    state=env.private_snapshot()["state"]
    return dict(label=extract_label(result,state),private_state=state,counts=counts,prefix_wls=prefix,window_wls=window,
                wall=perf_counter()-wall,cpu=process_time()-cpu)
