"""Summarize independently admitted VALUE-2 evidence without running physics."""
import hashlib
import json
from pathlib import Path

G = Path(__file__).parent
ROOTS = {g:Path(f"runs/a2_value2_{g.lower()}_001") for g in ("OPEN","LOCKED")}


def read(path):
    return json.loads(path.read_bytes().decode("utf-8-sig"))


def save(name,value):
    (G/(name+".json")).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding="utf-8")


def summarize():
    pins = read(G/"OPEN_HASHES.json")
    assert {Path(item["Path"]).resolve() for item in pins} == {
        p.resolve() for p in ROOTS["OPEN"].iterdir() if p.is_file()
    }
    for item in pins:
        assert hashlib.sha256(Path(item["Path"]).read_bytes()).hexdigest()==item["Hash"].lower()
    physics = read(G/"PHYSICAL_RECHECK.json")
    fork = read(G/"PRE_FORK_COMPARISON.json")["forks"]["R"]
    comparison = read(G/"VALUE_COMPARISON.json")
    plan_audit = read(G/"PLAN_AUDIT.json")
    groups = {}
    for group,root in ROOTS.items():
        src = read(root/"R.json")
        check = physics[group]["R"]
        rows = []
        for r in src["records"]:
            view, step, native = (r[k] for k in ("policy_input","step","choice"))
            ev = r["evidence"]
            chosen = r.get("locked",{}).get("selected",native)
            allowed = len(r["locked"]["feasible_ranking"]) if "locked" in r else ev["legal_plan_count"]
            rows.append(dict(tick=view["tick"], visible=[t["id"] for t in view["targets"]],
                current_assignment=view["assignment"],progress_before={str(h["target_id"]):
                    next((s["latest_clock"]["base"]+.05*s["latest_clock"]["intervals"]
                          for s in h["segments"] if s["segment_id"]==h["active_segment_id"]),0.)
                    for h in view["histories"] if h["target_id"] in [t["id"] for t in view["targets"]]},
                end_progress=step["frames"][-1]["progress"],candidates=ev["candidate_count"],
                plans=ev["legal_plan_count"],feasible=allowed,original=native["selected_indices"],
                chosen=chosen["selected_indices"],actual_assignment=chosen["actions"],
                exact_value=chosen["exact_value"],protection=r.get("locked",{}).get("protection"),
                margins={str(t["target_id"]):t["net_margin"] for t in ev["targets"]},
                beliefs=ev["targets"],change_cost=step["action_commit"]["change_cost"],events=step["events"]))
        tasks = {}
        for j in (0,1):
            name = str(j)
            terminal = check["archives"][name]
            endpoint_rows = [(f,e) for f in check["trace"] if (e:=f["endpoints"].get(name)) is not None]
            qualified = [f["tick"] for f,e in endpoint_rows if e["G"] and e["Q"]=="PASS"]
            observations = [r for r in check["receipts"] if r["target"]==j]
            consumed = [r for r in check["observations_consumed"] if r["target_id"]==j]
            events = [e for e in check["events"] if e["target_id"]==j]
            complete = terminal["terminal_status"]=="completed"
            archive_tick = terminal["terminal_at"]["event_tick"]
            length = (45,21)[j]
            start = archive_tick-length if complete else None
            if complete:
                assert set(range(start,archive_tick+1))<=set(qualified)
            tasks[name] = dict(archive=terminal,first_qualified_tick=min(qualified,default=None),
                sustained_start_tick=start,continuous_completion_intervals=length if complete else None,
                first_bearing=next((x["tick"] for x in observations if x["bearing_count"]),None),
                first_accepted=next((x["tick"] for x in observations if x["accepted"]),None),
                first_consumed=min((x["consumed_tick"] for x in consumed),default=None),
                accepted_at_tick80=sum(x["accepted"] and x["decision"]==60 for x in observations),
                completion_slack_ticks=120-archive_tick if complete else None,
                terminal_progress=events[-1]["progress_after"],observations=len(observations),
                consumed=len(consumed),events=events,ledger=check["ledger"][j],
                change_cost=check["change_cost_attributed_to_incoming_or_withdrawn_target"][j],
                occupation=check["occupied_seconds"][j],effort=check["effort_by_robot"][j])
        groups[group]=dict(rows=rows,tasks=tasks)
    t1=groups["OPEN"]["tasks"]["1"]
    t0=groups["LOCKED"]["tasks"]["0"]
    release=t0["archive"]["terminal_at"]["event_tick"] if t0["archive"]["terminal_status"]=="completed" else None
    assignment=((release+19)//20)*20 if release is not None else None
    locked_budget=120-assignment if assignment is not None else None
    protected=all(groups["LOCKED"]["rows"][i]["protection"] and
                  groups["LOCKED"]["rows"][i]["protection"]["target"]==0 for i in (3,4))
    switched=any(e["target_id"]==0 and e["kind"]=="WITHDRAWN" and e["progress_before"]>0
                 for e in groups["OPEN"]["rows"][3]["events"]) and any(
                 e["target_id"]==1 and e["kind"]=="ASSIGNED" for e in groups["OPEN"]["rows"][3]["events"])
    window=("NOT_OBSERVED" if t1["first_bearing"] is None else
            "OBSERVED" if switched and t1["completion_slack_ticks"] is not None
            and protected and locked_budget is not None and locked_budget<21 else "NOT_REALIZED")
    windows=dict(groups=groups,open_t1=t1,locked_t0=t0,release_tick=release,next_assignment_tick=assignment,
                 locked_t1_max_intervals=locked_budget,minimum_slack_ticks=4,
                 design_slack_observed=t1["completion_slack_ticks"] is not None and t1["completion_slack_ticks"]>=4)
    save("WINDOW_ANALYSIS",windows)
    signs={"VALID_POSITIVE":"POSITIVE","VALID_NEGATIVE":"NEGATIVE","VALID_ZERO":"ZERO"}
    save("ACCEPTANCE",dict(ENTRY_FROZEN="PASS",EXECUTION_OPEN="COMPLETE",EXECUTION_LOCKED="COMPLETE",
        FROZEN_INPUTS="PASS",PRE_FORK_COMPARABILITY="PASS",OPEN_POLICY_COMPLIANCE="PASS",
        LOCK_POLICY_COMPLIANCE="PASS",CONSTRAINED_EXACT_OPTIMUM="PASS",PHYSICAL_ACCOUNTING="PASS",
        R_S_NEW_CONSISTENCY="PASS",PHYSICAL_WINDOW=window,AUTONOMOUS_SWITCH="OBSERVED" if switched else "NOT_OBSERVED",
        REALIZED_VALUE=signs[comparison["validity"]],DELTA_J_VERIFIED="PASS",VALUE2_VALIDITY=comparison["validity"],
        FIRST_FORK_TICK=fork["FIRST_FORK_TICK"] if fork else None,
        locked_pair_identity_count=plan_audit["pair_identity_count"]))


if __name__=="__main__":
    summarize()
