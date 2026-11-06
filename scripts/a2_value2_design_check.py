"""Static A2-VALUE-2 budget. No policy, estimator, environment or episode calls."""
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/a2_value2_preflight_001"
DT = Fraction(1, 20)
END = 120
SWITCH = 60
UPDATE = 80


def read(path):
    return json.loads((ROOT / path).read_bytes().decode("utf-8-sig"))


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def f(x):
    return Fraction(str(x))


def first_service(valid, length):
    count = 0
    for end in range(1, len(valid)):
        count = count + 1 if valid[end-1] and valid[end] else 0
        if count == length:
            return end-length, end
    return None


def next_cut(release, period):
    return ((release+period-1)//period)*period


def conditional_ledger(cfg, targets, finished, effort, changes):
    ref = 4 * cfg["task_count"]
    flow_scale = f(cfg["flow_weight"])/(ref*f(cfg["stage_dt"]))
    late_scale = f(cfg["late_weight"])/(ref*f(cfg["stage_dt"]))
    values = dict.fromkeys(("completion","flow","late","terminal","change"), Fraction())
    for t in targets:
        j = t["id"]
        stop = finished.get(j, END*DT)
        weight = f(t["weight"])
        values["completion"] += weight/ref if j in finished else 0
        values["terminal"] -= f(cfg["unfinished_weight"])*weight/ref if j not in finished else 0
        values["flow"] -= flow_scale*weight*(stop-f(t["birth"]))
        values["late"] -= late_scale*weight*max(Fraction(),stop-f(t["deadline"]))
    values["change"] = -changes*f(cfg["change_cost"])
    values = {k:float(v) for k,v in values.items()}
    effort_ref = cfg["robots"]*cfg["stage_dt"]*cfg["control_reference"]**2
    values["effort"] = -cfg["control_weight"]*effort/effort_ref
    values["net"] = math.fsum(values.values())
    return values


def tracking_budget(cfg, robots, target, prior, sigma):
    """Closed-form Euler tracking, conditional on fixed U0/U1 and exact tick80 WLS.

    A local radius proxy at the true representative is a Q feasibility check.
    It does not certify WLS convergence, uniqueness or future policy choices.
    """
    dt = float(DT)
    roles = np.array([[1.,-1.],[1.,1.]])*cfg["observation_radius"]/math.sqrt(2)
    initial = np.array(robots)
    point0 = np.array(target["position_at_birth"])
    v = np.array(target["velocity"])
    anchor0 = np.array(prior["coarse_position"])+roles
    gain = cfg["travel_gain"]
    decay = 1-gain*dt
    at_update = anchor0 + (initial-anchor0)*decay**(UPDATE-SWITCH)
    residual = at_update - (point0+(UPDATE-SWITCH)*dt*v+roles)
    trace = []
    for tick in range(SWITCH,END+1):
        point = point0+(tick-SWITCH)*dt*v
        if tick < UPDATE:
            positions = anchor0+(initial-anchor0)*decay**(tick-SWITCH)
            control = gain*(anchor0-positions)
        else:
            positions = point+roles+residual*decay**(tick-UPDATE)
            control = v-gain*residual*decay**(tick-UPDATE)
        delta = point-positions
        ranges2 = np.sum(delta**2,axis=1)
        jacobian = np.column_stack((delta[:,1],-delta[:,0]))/(sigma*ranges2[:,None])
        smax,smin = np.linalg.svd(jacobian,compute_uv=False)
        radius = math.sqrt(-2*math.log(.05))/smin
        error = max(np.linalg.norm(positions-point-roles,axis=1))
        speed = max(np.linalg.norm(control,axis=1))
        assert speed < cfg["max_speed"] and point[0] < cfg["side"]
        trace.append(dict(tick=tick,error=float(error),radius_proxy=radius,
                          valid_if_wls_accepted=bool(error<=cfg["observation_tolerance"] and radius<=.06 and smin/smax>=1e-4),
                          control_speed=float(speed), effort_next_interval=float(np.sum(control**2)*dt)))
    return trace


def analyse():
    world = read("configs/a2_value2_two_target_v1.json")
    original = read("configs/a2_switch_two_target_v1.json")
    announcement = read("configs/a2_value2_public_announcements_v1.json")
    assert announcement == read("configs/a2_switch_public_announcements_v1.json")
    cfg, targets = world["config"], world["targets"]
    assert world == dict(original,targets=[original["targets"][0],dict(
        original["targets"][1],position_at_birth=[9.03,10.29],velocity=[.02,0.])])
    t0,t1 = targets
    a0,a1 = announcement["announcements"]
    for t,a in zip(targets,(a0,a1)):
        assert all(t[k]==a[k] for k in ("id","birth","weight","deadline","required_robots","service_duration"))
        assert f(t["birth"])/DT==a["announcement_tick"]
    assert cfg["robots"]==3 and f(cfg["step_dt"])==DT
    assert f(cfg["stage_dt"])*cfg["max_stages"]/DT==END
    assert world["measurement_model"]["angle_perturbation"]==0
    for n in (0,20,40):
        row = read(f"runs/a2_switch_episode_001/R_D{n}.json")
        assert [t["id"] for t in row["policy_input"]["targets"]]==[0]
        assert all(x["frame"]["target_id"]==0 for x in row["step"]["fusion_records"])
    old_cut = read("runs/a2_switch_episode_001/R_D60.json")
    before = read("runs/a2_switch_episode_001/R_D40.json")["step"]["frames"][-1]
    assert before["tick"]==SWITCH and before["statuses"]==["active","active"]
    assert before["positions"]==old_cut["policy_input"]["positions"]
    assert [a["target"] for a in before["assignment"]]==[0,0,None]
    progress = Fraction(round(before["progress"]["0"]/float(DT)))*DT
    assert progress==Fraction(3,5)
    length = int(f(t1["service_duration"])/DT)
    assert length*DT==f(t1["service_duration"])
    trace = tracking_budget(cfg,before["positions"][:2],t1,a1,.02)
    start, finish = first_service([r["valid_if_wls_accepted"] for r in trace],length)
    start, finish = start+SWITCH,finish+SWITCH
    slack = (END-finish)*DT
    assert slack>=Fraction(1,5)
    release = SWITCH+int((f(t0["service_duration"])-progress)/DT)
    assignment = next_cut(release,20)
    lock_slack = (END-assignment-length)*DT
    assert lock_slack<0
    old_locked = read("runs/a2_value1_locked_001/R.json")
    assert old_locked["final"]["state"]["archives"]["0"]["terminal_at"]["event_tick"]==release
    old_effort = read("runs/a2_switch_episode_001/R_D40.json")["step"]["metrics"]["control_integral"]
    open_effort = old_effort+sum(r["effort_next_interval"] for r in trace if r["tick"]<finish)
    locked_effort = old_locked["metrics"]["control_integral"]
    open_ledger = conditional_ledger(cfg,targets,{1:finish*DT},open_effort,4)
    locked_ledger = conditional_ledger(cfg,targets,{0:release*DT},locked_effort,2)
    delta = {key:open_ledger[key]-locked_ledger[key] for key in open_ledger}
    assert math.isclose(delta["completion"]+delta["terminal"],.1875)
    return dict(status="CONDITIONAL_ESTIMATE",scenario_count=1,episode_calls=0,
        changed_fields={"targets/1/position_at_birth":[original["targets"][1]["position_at_birth"],t1["position_at_birth"]],
                        "targets/1/velocity":[original["targets"][1]["velocity"],t1["velocity"]]},
        switch_positions=before["positions"],position_error=math.dist(a1["coarse_position"],t1["position_at_birth"]),
        velocity_error=math.dist(a1["velocity_prior"],t1["velocity"]),
        service_intervals=length,first_sustainable_tick=start,conditional_complete_tick=finish,
        zero_slack_tick=END-length,minimum_slack_ticks=4,slack_ticks=END-finish,slack=float(slack),
        assumed_observation_consumption_tick=UPDATE,locked_t0_progress=float(progress),
        locked_t0_remaining=float(f(t0["service_duration"])-progress),
        locked_release_tick=release,locked_next_assignment_tick=assignment,
        locked_t1_slack_best_case=float(lock_slack),legacy_c6_selected=old_cut["choice"]["selected_indices"],
        legacy_c6_value=old_cut["choice"]["exact_value"],trace=trace,
        ledger=dict(OPEN=open_ledger,LOCKED=locked_ledger,delta=delta),
        history_unchanged=all(sha(path)==value for path,value in read(
            "reports/a2_value2_preflight_001/HISTORICAL_PINS.json").items()))


if __name__=="__main__":
    result = analyse()
    assert result["history_unchanged"]
    (REPORT / "DESIGN_ANALYSIS.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
