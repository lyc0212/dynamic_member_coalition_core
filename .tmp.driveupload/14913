"""Offline verification of saved VALUE-2E evidence, with no episode execution."""
from fractions import Fraction
import json
import math
from pathlib import Path
import runpy

from scripts.gq_windows.a0_compare import admitted_pair
from scripts.gq_windows.a0_identity import IdentityMap, exact_tree
from scripts.gq_windows.a0_plans import canonical_choice, catalogue, plans
from scripts.run_a2_value2_locked import compare_before_action, compare_prefork_step, load_open

OUT = Path("reports/a2_value2_episode_001_guard")
RUN = Path("runs/a2_value2_locked_001")
OPEN = Path("runs/a2_value2_open_001")
OPEN_AUDIT = Path("reports/a2_switch_episode_001_guard")
TICKS = tuple(range(0,120,20))
MODES = ("R","S_NEW")


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def save(name, value):
    (OUT / (name+".json")).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding="utf-8")


def audit_plan(row):
    view, choice, record = (row[k] for k in ("policy_input","choice","locked"))
    active = {a["id"]:a for a in view["targets"]}
    previous = view["assignment"]
    protected = {}
    for h in view["histories"]:
        j = h["target_id"]
        if j not in active:
            continue
        team = [{"robot_id":i,"role":a["role"]} for i,a in enumerate(previous) if a["target"]==j]
        if h["active_segment_id"] is None:
            assert not team
            continue
        segment, = [s for s in h["segments"] if s["segment_id"]==h["active_segment_id"]]
        clock = segment["latest_clock"]
        assert segment["closure"] is None and team==segment["team"]==clock["team"]
        assert len(team)==2 and {m["role"] for m in team}=={"dual_neg45","dual_pos45"}
        assert type(clock["intervals"]) is int and 0<=clock["intervals"]<=view["tick"]
        assert math.isfinite(clock["base"]) and clock["base"]>=0
        progress = clock["base"]+clock["intervals"]*.05
        assert progress < active[j]["service_duration"]
        if progress>0:
            protected[j] = dict(target=j,team=team,progress=progress,segment_id=segment["segment_id"])
    assert len(protected)<=1
    protection = next(iter(protected.values()),None)
    exact_tree(protection,record["protection"],"/lock/protection")
    rows = choice["rows"]
    keys = catalogue(view)
    exact_tree(keys,[r["key"] for r in rows],"/keys")
    original = plans(view,keys,rows)
    native = canonical_choice(view,keys,rows,original)
    native_plan = next(p for p in original if p["selected"]==native)
    exact_tree(choice["selected_indices"],native,"/choice/selected_indices")
    exact_tree(choice["actions"],native_plan["actions"],"/choice/actions")
    assert Fraction(choice["exact_value"])==Fraction(native_plan["exact_value"])
    feasible = []
    for p in original:
        admitted = all([{"robot_id":i,"role":a["role"]} for i,a in enumerate(p["actions"]) if a["target"]==j]
                       ==lock["team"] for j,lock in protected.items())
        p.update(original_legal=True,lock_feasible=admitted,
                 excluded_reason=None if admitted else "POSITIVE_PROGRESS_TEAM_NOT_PRESERVED",
                 change_cost=str(Fraction.from_float(view["config"]["change_cost"])*p["changes"]))
        if admitted:
            feasible.append(p)
    exact_tree(original,record["original_legal_plans"],"/lock/original_legal_plans")
    if protection:
        expected, = feasible
    else:
        expected = next(p for p in feasible if p["selected"]==native)
    rank = sorted(feasible,key=lambda p:Fraction(p["exact_value"]),reverse=True)
    assert Fraction(expected["exact_value"])==Fraction(rank[0]["exact_value"])
    exact_tree([p["selected"] for p in rank],record["feasible_ranking"],"/lock/feasible_ranking")
    selected = record["selected"]
    exact_tree(selected,dict(selected_indices=expected["selected"],actions=expected["actions"],
                             exact_value=expected["exact_value"]),"/lock/selected")
    exact_tree(selected["actions"],row["step"]["frames"][0]["assignment"],"/step/assignment")
    return dict(tick=view["tick"],protection=protection,original_selected=native,original_exact_value=choice["exact_value"],
                selected=selected,candidate_count=len(keys),plan_count=len(original),feasible_count=len(feasible),
                plans=original,beliefs=view["beliefs"],evidence=row["evidence"])


def load(root, mode):
    final = read(root/(mode+".json"))
    records = [read(root/f"{mode}_D{tick}.json") for tick in TICKS]
    exact_tree(records,final["records"],f"/{mode}/records")
    assert final["final"]["state"]["tick"]==120 and final["final"]["state"]["terminal_settled"]
    return records,final


def main():
    before, after = (read(OUT/(p+".json")) for p in ("BEFORE","AFTER"))
    exact_tree(before,after,"/frozen")
    timing = read(OUT/"TIMING.json")
    assert all(r["finished"] and r["exit_code"]==0 for r in timing.values()) and set(timing)=={"OPEN","LOCKED"}
    for root in (RUN,OPEN):
        assert read(root/"PAIR_CHECK.json")["status"]=="PASS"
    for name in ("WORLD_INPUT","PUBLIC_INPUT"):
        exact_tree(read(OPEN/(name+".json")),read(RUN/(name+".json")),"/"+name)
    world = read(RUN/"WORLD_INPUT.json")
    announcements = read(RUN/"PUBLIC_INPUT.json")["announcements"]
    legacy = runpy.run_path(str(OPEN_AUDIT/"recheck.py"))
    physics, finals = {"OPEN":{},"LOCKED":{}},{"OPEN":{},"LOCKED":{}}
    locked_records, audited, prefork, forks = {},{},{},{}
    for mode in MODES:
        a, a_final = load(OPEN,mode)
        b, b_final = load(RUN,mode)
        locked_records[mode] = b
        fork = None
        for i,tick in enumerate(TICKS):
            fork = compare_before_action(a[i],b[i],a_final["observations_consumed"],
                       [x for x in b_final["observations_consumed"] if x["consumed_tick"]<=tick],mode,tick)
            count = None if fork else compare_prefork_step(a[i]["step"],b[i]["step"],mode,tick)
            prefork[f"{mode}/D{tick}"] = dict(status="PASS",step_identity_count=count)
            if fork:
                break
        forks[mode] = fork
        for x in a:
            legacy["table"](x)
        audited[mode] = [audit_plan(x) for x in b]
        for group,records,final in (("OPEN",a,a_final),("LOCKED",b,b_final)):
            # The independent physics verifier needs the actions actually committed.
            executed = [dict(row,choice=row["locked"]["selected"]) for row in records] if group=="LOCKED" else records
            result = legacy["verify_physics"](executed,final,world)
            legacy["verify_observation_feedback"](records,final,result["receipts"],announcements)
            result["observations_consumed"] = final["observations_consumed"]
            result["archives"] = final["final"]["state"]["archives"]
            result["histories"] = final["final"]["state"]["histories"]
            physics[group][mode] = result
            finals[group][mode] = final["metrics"]
    mapping = IdentityMap()
    for tick,a,b in zip(TICKS,locked_records["R"],locked_records["S_NEW"]):
        for key in ("policy_input","choice","evidence","locked"):
            exact_tree(a[key],b[key],f"/LOCKED/D{tick}/{key}")
        admitted_pair(a["step"],b["step"],"step","A2_VALUE2_LOCKED",tick,
                      (a["policy_input"],b["policy_input"]),mapping)
    for group in ("OPEN","LOCKED"):
        exact_tree(physics[group]["R"],physics[group]["S_NEW"],"/"+group+"/physics")
        exact_tree(finals[group]["R"],finals[group]["S_NEW"],"/"+group+"/metrics")
    ledgers = {}
    for group in finals:
        metrics = finals[group]["R"]
        ledgers[group] = dict(metrics["reward_components"],change_cost=-metrics["change_cost"],
                              net=metrics["return_with_changes"])
    native = read(RUN/"PRE_FORK_CHECK.json")
    exact_tree(forks,native["forks"],"/native/forks")
    exact_tree(forks["R"],forks["S_NEW"],"/forks")
    exact = {k:Fraction.from_float(v)-Fraction.from_float(ledgers["LOCKED"][k])
             for k,v in ledgers["OPEN"].items()}
    delta = exact["net"]
    residual = delta-sum(v for k,v in exact.items() if k!="net")
    assert abs(residual)<=Fraction.from_float(1e-12)
    validity = "VALID_POSITIVE" if delta>0 else "VALID_NEGATIVE" if delta<0 else "VALID_ZERO"
    save("PRE_FORK_COMPARISON",dict(status="PASS",cuts=prefork,forks=forks))
    save("PLAN_AUDIT",dict(status="PASS",modes=audited,pair_identity_count=len(mapping.records)))
    save("PHYSICAL_RECHECK",physics)
    save("VALUE_COMPARISON",dict(validity=validity,ledgers=ledgers,
        delta={k:float(v) for k,v in exact.items()},exact_delta={k:str(v) for k,v in exact.items()},
        exact_rounding_residual=str(residual),timing=timing))


def open_gate():
    """Validate the first official call before allowing the second."""
    world = read(Path("configs/a2_value2_two_target_v1.json"))
    ann = read(Path("configs/a2_value2_public_announcements_v1.json"))
    records = load_open(OPEN,world,ann)
    legacy = runpy.run_path(str(OPEN_AUDIT/"recheck.py"))
    mapping = IdentityMap()
    checked = {}
    for mode in MODES:
        final = read(OPEN/(mode+".json"))
        for row in records[mode]:
            legacy["table"](row)
        result = legacy["verify_physics"](records[mode],final,world)
        legacy["verify_observation_feedback"](records[mode],final,result["receipts"],ann["announcements"])
        checked[mode] = dict(physical=result,metrics=final["metrics"],consumed=final["observations_consumed"])
    exact_tree(checked["R"],checked["S_NEW"],"/OPEN/physical")
    for tick,a,b in zip(TICKS,records["R"],records["S_NEW"]):
        for key in ("policy_input","choice","evidence"):
            exact_tree(a[key],b[key],f"/OPEN/D{tick}/{key}")
        admitted_pair(a["step"],b["step"],"step","A2",tick,
                      (a["policy_input"],b["policy_input"]),mapping)
    save("OPEN_GATE",dict(status="PASS",decisions=6,pair_identity_paths=len(mapping.records)))


if __name__=="__main__":
    import sys
    if sys.argv[1:]==["--open-gate"]:
        open_gate()
    else:
        main()
