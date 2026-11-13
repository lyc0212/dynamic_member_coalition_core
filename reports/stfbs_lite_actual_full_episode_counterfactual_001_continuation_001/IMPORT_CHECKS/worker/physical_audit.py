"""Read the frozen A2-S2 artifacts. This script does not run an episode."""
from fractions import Fraction
import json
import math
from pathlib import Path

from research.information_service_online.episode_audit import ANGLES, close, target_state
from research.information_service_online.quality_audit import audit_fusion
from scripts.gq_windows.a0_compare import admitted_pair, get_pointer, strict_pair
from scripts.gq_windows.a0_identity import IdentityMap, digest, exact_tree
from scripts.gq_windows.a0_plans import canonical_choice, catalogue, plans

RUN = Path("runs/a2_switch_episode_001")
PRE = Path("reports/a2_switch_preflight_001")
OUT = Path(__file__).parent
TICKS = range(0, 120, 20)
MODES = ("R", "S_NEW")


def read(path):
    return json.loads(path.read_bytes().decode("utf-8-sig"))


def save(name, value):
    (OUT / (name + ".json")).write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def prefix_step(old, new, mode, tick):
    context = {"pending": []}
    strict_pair(old, new, "step", f"", context)
    for kind, path, left, right in context["pending"]:
        if kind == "frame_digest":
            source = path.rsplit("/", 1)[0] + "/normalized_frame"
            assert left == digest(get_pointer(old, source)), (tick, path)
            assert right == digest(get_pointer(new, source)), (tick, path)
        elif kind in ("work", "environment"):
            assert (left, right) == ("A2_SWITCH_" + mode, "A2_" + mode), (tick, path)
        else:
            assert kind in ("stream", "frame", "packet"), (tick, path, kind)
            assert left.startswith("A2_SWITCH_" + mode + ":") and left == "A2_SWITCH" + right[2:], (tick, path)
    return len(context["pending"])


def table(record):
    view, choice = record["policy_input"], record["nominal_choice"]
    rows = choice["rows"]
    keys = catalogue(view)
    exact_tree(keys, [row["key"] for row in rows], "/candidate_catalogue")
    complete = plans(view, keys, rows)
    selected = canonical_choice(view, keys, rows, complete)
    ranked = sorted(complete, key=lambda plan: Fraction(plan["exact_value"]), reverse=True)
    idle = next(plan for plan in ranked if not plan["selected"])
    for plan in ranked:
        plan["margin"] = str(Fraction(plan["exact_value"]) - Fraction(idle["exact_value"]))
        plan["cost"] = str(plan["changes"] * Fraction.from_float(view["config"]["change_cost"]))
    best = next(plan for plan in ranked if plan["selected"] == selected)
    assert selected == choice["selected_indices"] and best["actions"] == choice["actions"]
    assert Fraction(ranked[0]["exact_value"]) == Fraction(choice["exact_value"])
    return ranked, best


def offset(role, cfg):
    return [cfg["observation_radius"] * fn(ANGLES[role]) for fn in (math.cos, math.sin)]


def prediction(belief, tick):
    age = (tick - belief["estimate_tick"]) * .05
    prior = belief["last_observation_tick"] is None
    span = age if prior else min(age, 1.)
    v = belief["velocity_estimate"]
    return ([x + span * u for x, u in zip(belief["position_estimate"], v)],
            v if prior or age <= 1. else [0., 0.])


def qualifies(e):
    return bool(e and e["has_accepted_estimate"] and e["optimizer_converged"]
                and not any(e[k] for k in ("numerical_ill_conditioned", "ambiguity_detected",
                                           "boundary_active", "numeric_contract_violation")))


def verify_physics(records, final, world):
    cfg, targets = world["config"], world["targets"]
    reference = 4 * cfg["task_count"]
    effort_ref = cfg["robots"] * cfg["stage_dt"] * cfg["control_reference"] ** 2
    ledger = [dict(completion=0., flow=0., late=0., effort=0., terminal=0.) for t in targets]
    costs = [0. for t in targets]
    busy = [[0.] * cfg["robots"] for t in targets]
    energy = [[0.] * cfg["robots"] for t in targets]
    trace, receipts, all_events = [], [], []
    previous = None
    for row in records:
        view, step = row["policy_input"], row["step"]
        tick = view["tick"]
        assert step["status"] == "COMMITTED" and (step["start_tick"], step["end_tick"]) == (tick, tick+20)
        boundary, *frames = step["frames"]
        assert [f["tick"] for f in frames] == list(range(tick+1, tick+21))
        close(boundary["positions"], view["positions"])
        assignments = row["submitted_assignment"]
        assert step["checkpoint_after"]["tick"] == tick+20
        assert step["checkpoint_after"]["phase"] == ("TERMINAL" if tick==100 else "DECISION_READY")
        exact_tree(boundary["assignment"], assignments, "/assignment")
        changes = 0
        for before, after in zip(view["assignment"], assignments):
            if before != after:
                changes += 1
                responsible = after["target"] if after["target"] is not None else before["target"]
                costs[responsible] += cfg["change_cost"]
        close(step["action_commit"]["change_cost"], changes * cfg["change_cost"])
        close(boundary["metrics"]["change_cost"], sum(costs))
        if previous:
            close(previous["positions"], boundary["positions"])
            close(boundary["metrics"]["reward_components"], previous["metrics"]["reward_components"])
            close(boundary["metrics"]["assignment_changes"] - previous["metrics"]["assignment_changes"], changes)
        for event in boundary["events"]:
            if event["kind"] in ("WITHDRAWN", "MEMBER_CHANGE", "ROLE_CHANGE", "TEAM_CHANGED", "ROLE_CHANGED"):
                close(event["progress_before"], previous["progress"][str(event["target_id"])])
                close(event["progress_after"], 0.)
        fusion = {}
        by_tick = {frame["tick"]: frame for frame in [boundary, *frames]}
        for entry in step["fusion_records"]:
            audit_fusion(entry)
            f = entry["frame"]
            j, n = f["target_id"], f["tick"]
            assert (j,n) not in fusion
            fusion[j,n] = entry
            point, velocity = target_state(targets[j], n*.05)
            for packet in f["records"]:
                i = int(packet["sensor_id"][1:])
                close(packet["position"], by_tick[n]["positions"][i])
                delta = math.atan2(point[1]-packet["position"][1], point[0]-packet["position"][0]) - packet["bearing"]
                close(math.atan2(math.sin(delta), math.cos(delta)), 0.)
            estimate = entry["result"]["estimate_result"]
            receipts.append(dict(target=j, tick=n, decision=tick, available_tick=n, bearing_count=len(f["records"]),
                                 accepted=qualifies(estimate), estimate=estimate["estimate"] if qualifies(estimate) else None,
                                 quality=entry["result"]["quality"]["status"]))
        for frame in [boundary, *frames]:
            n = frame["tick"]
            endpoint_data = {}
            for key, ep in frame["actual_endpoints"].items():
                j = int(key)
                point, velocity = target_state(targets[j], n*.05)
                errors = [math.dist(frame["positions"][member["robot_id"]],
                           [x+o for x,o in zip(point,offset(member["role"],cfg))]) for member in ep["team"]]
                assert ep["G"] == (max(errors) <= cfg["observation_tolerance"] + 1e-10), (n,j,errors)
                entry = fusion.get((j,n))
                if entry:
                    assert ep["quality"]["status"] == entry["result"]["quality"]["status"]
                endpoint_data[key] = dict(G=ep["G"], Q=ep["quality"]["status"], target_position=point,
                                          target_velocity=velocity, role_errors=errors)
            trace.append(dict(decision=tick,tick=n,phase=frame["phase"],progress=frame["progress"],
                              positions=frame["positions"],control=frame["control"],endpoints=endpoint_data))
        last = boundary
        for frame in frames:
            n = frame["tick"]
            close(frame["positions_start"], last["positions"])
            for i, action in enumerate(last["assignment"]):
                j = action["target"]
                p = last["positions"][i]
                elapsed = frame["control_elapsed_by_robot"][i]
                command = [0.,0.]
                if j is not None:
                    goal, v = prediction(view["beliefs"][str(j)], n-1)
                    command = [u + cfg["travel_gain"]*(x+o-y) for u,x,o,y in zip(v,goal,offset(action["role"],cfg),p)]
                    scale = min(1., cfg["max_speed"]/max(math.hypot(*command),1e-15))
                    command = [u*scale for u in command]
                    close(elapsed,.05)
                    work = math.fsum(u*u for u in command)*elapsed
                    energy[j][i] += work
                    busy[j][i] += elapsed
                    ledger[j]["effort"] -= cfg["control_weight"]*work/effort_ref
                else:
                    close(elapsed,0.)
                close(frame["control"][i], command, 1e-11, f"control/{n}/{i}")
                close(frame["positions"][i], [x+u*elapsed for x,u in zip(p,command)], 1e-11)
            for t in targets:
                j = t["id"]
                key = str(j)
                assert frame["statuses"][j] != "escaped", "Partial escape interval outside this fixed-scene audit"
                if last["statuses"][j] == "active":
                    lo,hi = (n-1)*.05,n*.05
                    ledger[j]["flow"] -= cfg["flow_weight"]*t["weight"]*max(0.,hi-max(lo,t["birth"]))/(reference*cfg["stage_dt"])
                    ledger[j]["late"] -= cfg["late_weight"]*t["weight"]*max(0.,hi-max(lo,t["birth"],t["deadline"]))/(reference*cfg["stage_dt"])
                left,right = last["actual_endpoints"].get(key),frame["actual_endpoints"].get(key)
                if key in last["active_segment_ids"]:
                    assert left and right, (n,j)
                    before = last["progress"][key]
                    valid = all(ep["G"] and ep["quality"]["status"]=="PASS" for ep in (left,right))
                    advanced = before+.05 if valid else 0.
                    completed = advanced >= t["service_duration"] - 1e-10
                    close(frame["progress"][key],t["service_duration"] if completed else advanced)
                    assert completed == (frame["statuses"][j]=="completed"), (n,j)
                    resets = [e for e in frame["events"] if e["target_id"]==j and e["kind"]=="INTERRUPTED"]
                    assert len(resets)==int(not valid and before>0.), (n,j)
                    if resets:
                        close(resets[0]["progress_before"],before)
                        close(resets[0]["progress_after"],0.)
                    if completed:
                        ledger[j]["completion"] += t["weight"]/reference
                if n==120 and frame["statuses"][j]!="completed":
                    ledger[j]["terminal"] -= cfg["unfinished_weight"]*t["weight"]/reference
            last = frame
        previous = last
        all_events.extend(step["events"])
    total = {k:sum(row[k] for row in ledger) for k in ledger[0]}
    close(total, final["metrics"]["reward_components"])
    close(sum(costs),final["metrics"]["change_cost"])
    close(sum(total.values())-sum(costs),final["metrics"]["return_with_changes"])
    close([sum(x) for x in zip(*energy)],final["metrics"]["effort_by_robot"])
    close(sum(map(sum,busy)),final["metrics"]["occupied_robot_seconds"])
    return dict(ledger=ledger,change_cost_attributed_to_incoming_or_withdrawn_target=costs,
                occupied_seconds=busy,effort_by_robot=energy,trace=trace,receipts=receipts,events=all_events)


def verify_observation_feedback(rr, final, receipts, announcements):
    """Match consumption to actual frames, then rederive the admissible position and velocity."""
    expected = [dict(target_id=f["target"],measurement_tick=f["tick"],available_tick=f["available_tick"],
                     consumed_tick=f["decision"]+20) for f in receipts if f["decision"]<100]
    exact_tree(expected,final["observations_consumed"],"/observations_consumed")
    for row in rr:
        view = row["policy_input"]
        tick = view["tick"]
        for key, belief in view["beliefs"].items():
            j = int(key)
            a = announcements[j]
            admitted = [f for f in receipts if f["target"]==j and f["accepted"] and f["decision"]<tick]
            velocity = a["velocity_prior"]
            if not admitted:
                assert belief["status"]=="PRIOR_ONLY" and belief["last_observation_tick"] is None
                close(belief["position_estimate"],a["coarse_position"])
            else:
                newest = admitted[-1]
                assert belief["last_observation_tick"]==newest["tick"]
                assert belief["available_tick"]==newest["available_tick"]
                assert belief["status"]==("DEGRADED" if tick-newest["tick"]>20 else "OBSERVED")
                close(belief["position_estimate"],newest["estimate"])
                for f in reversed(admitted):
                    if newest["tick"]-f["tick"]>=5:
                        velocity = [(x-y)/((newest["tick"]-f["tick"])*.05)
                                    for x,y in zip(newest["estimate"],f["estimate"])]
                        speed=math.hypot(*velocity)
                        if speed>a["speed_limit"]:
                            velocity=[v*a["speed_limit"]/speed for v in velocity]
                        break
            close(belief["velocity_estimate"],velocity)

