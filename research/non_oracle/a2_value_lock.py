"""Positive-progress protection for the frozen three-robot q2 comparison."""
from fractions import Fraction
import math

from research.non_oracle.a2_analysis import decision_evidence
from scripts.gq_windows.a0_plans import ROLES, canonical_choice, plans


def protected_team(view):
    if view["tick"] not in range(0, 120, 20) or view["end_tick"] != 120:
        raise ValueError("Unsupported decision cut")
    actions = view["assignment"]
    targets = {target["id"]: target for target in view["targets"]}
    if len(actions) != 3 or len(view["positions"]) != 3 or any(
        target["required_robots"] != 2 for target in targets.values()
    ):
        raise ValueError("A2-VALUE-1 requires three robots and q2 tasks")
    if any(a["target"] not in targets and a != {"target": None, "role": "none"} for a in actions):
        raise ValueError("Assignment refers to inactive target")
    protection = None
    for target in targets:
        histories = [h for h in view["histories"] if h["target_id"] == target]
        if len(histories) != 1:
            raise ValueError("Missing or duplicate active task history")
        history = histories[0]
        segment_id = history["active_segment_id"]
        team = [{"robot_id": i, "role": a["role"]} for i, a in enumerate(actions) if a["target"] == target]
        if segment_id is None:
            if team:
                raise ValueError("Assignment without active service segment")
            continue
        segments = [s for s in history["segments"] if s["segment_id"] == segment_id]
        if len(segments) != 1 or segments[0]["closure"] is not None:
            raise ValueError("Invalid active service segment")
        segment = segments[0]
        clock = segment["latest_clock"]
        if len(team) != 2 or {m["role"] for m in team} != set(ROLES) or team != segment["team"] or team != clock["team"]:
            raise ValueError("Assignment, segment and clock teams differ")
        base, intervals = clock["base"], clock["intervals"]
        if type(base) not in (int, float) or not math.isfinite(base) or base < 0 or type(intervals) is not int or not 0 <= intervals <= view["tick"]:
            raise ValueError("Invalid settled service clock")
        progress = base + intervals * .05
        if progress >= targets[target]["service_duration"]:
            raise ValueError("Completed clock in active service segment")
        if progress > 0:
            protection = dict(target=target, team=team, progress=progress, segment_id=segment_id)
    return protection


def select(view, choice, protection):
    """With one anchored q2 team only one robot remains, so KEEP is unique."""
    if protection is None:
        return {key: choice[key] for key in ("selected_indices", "actions", "exact_value")}
    indices = [
        i for i, row in enumerate(choice["rows"])
        if row["key"]["target"] == protection["target"]
        and list(zip(row["key"]["robots"], row["key"]["roles"])) ==
        [(member["robot_id"], member["role"]) for member in protection["team"]]
    ]
    if len(indices) != 1:
        raise ValueError("Missing or duplicate protected candidate")
    index = indices[0]
    base = 0.
    baselines = {}
    for row in choice["rows"]:
        baselines.setdefault(row["key"]["target"], row["baseline"])
    for target in sorted(baselines):
        base += baselines[target]
    value = Fraction.from_float(base) + Fraction.from_float(choice["rows"][index]["v"])
    return dict(selected_indices=[index], actions=view["assignment"], exact_value=str(value))


def audit_selection(view, choice, protection, selected):
    """Independent complete enumeration, including plans excluded by protection."""
    rows = choice["rows"]
    table = plans(view, [row["key"] for row in rows], rows)
    anchor = [] if protection is None else [
        (m["robot_id"], {"target": protection["target"], "role": m["role"]})
        for m in protection["team"]
    ]
    cost = Fraction.from_float(view["config"]["change_cost"])
    for plan in table:
        allowed = all(plan["actions"][i] == action for i, action in anchor)
        plan.update(original_legal=True, lock_feasible=allowed,
                    excluded_reason=None if allowed else "POSITIVE_PROGRESS_TEAM_NOT_PRESERVED",
                    change_cost=str(cost * plan["changes"]))
    feasible = [p for p in table if p["lock_feasible"]]
    if protection is None:
        expected = canonical_choice(view, [row["key"] for row in rows], rows, table)
    else:
        if len(feasible) != 1:
            raise ValueError("Frozen q2 protection must have exactly one feasible plan")
        expected = feasible[0]["selected"]
    plan = next(p for p in feasible if p["selected"] == expected)
    if (selected["selected_indices"] != expected or selected["actions"] != plan["actions"]
            or Fraction(selected["exact_value"]) != Fraction(plan["exact_value"])
            or Fraction(plan["exact_value"]) != max(Fraction(p["exact_value"]) for p in feasible)):
        raise ValueError("Selection differs from independent feasible optimum")
    return dict(protection=protection, selected=selected, original_legal_plans=table,
                feasible_ranking=[p["selected"] for p in sorted(
                    feasible, key=lambda p: Fraction(p["exact_value"]), reverse=True)])


def locked_decision(view, choice, accepted_receipts):
    unrestricted = decision_evidence(view, choice, accepted_receipts)
    protection = protected_team(view)
    selected = select(view, choice, protection)
    return unrestricted, audit_selection(view, choice, protection, selected)
