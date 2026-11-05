"""Independent saved-episode physics, clock, accounting and coverage audit.

This module never imports the actual executor, candidate evaluator, measurement
assembler, production motion/geometry/service functions, or a WLS estimator.
"""
from collections import Counter
from fractions import Fraction
import math
from pathlib import Path

from .common import digest, read_json, save_json
from .quality_audit import audit_fusion


DT = Fraction(1, 20)
TOL = 1e-10
ANGLES = {"dual_neg45": -math.pi / 4, "dual_pos45": math.pi / 4,
          "tri_0": 0.0, "tri_120": 2 * math.pi / 3, "tri_240": 4 * math.pi / 3}
ROLES = {2: {"dual_neg45", "dual_pos45"}, 3: {"tri_0", "tri_120", "tri_240"}}


def close(a, b, atol=1e-12, label=""):
    if isinstance(b, dict):
        assert set(a) == set(b), (label, set(a), set(b))
        for key in b:
            close(a[key], b[key], atol, label + "/" + str(key))
    elif isinstance(b, (list, tuple)):
        assert len(a) == len(b), (label, len(a), len(b))
        for n, (x, y) in enumerate(zip(a, b)):
            close(x, y, atol, label + "/" + str(n))
    elif b is None or isinstance(b, (str, bool)):
        assert a == b, (label, a, b)
    else:
        assert math.isfinite(a) and math.isfinite(b) and abs(a - b) <= atol, (label, a, b)


def _arc(p, v, omega, duration):
    if abs(omega) <= 1e-12:
        return [p[i] + v[i] * duration for i in (0, 1)], list(v)
    speed, theta = math.hypot(*v), math.atan2(v[1], v[0])
    end = theta + omega * duration
    return ([p[0] + speed / omega * (math.sin(end) - math.sin(theta)),
             p[1] + speed / omega * (math.cos(theta) - math.cos(end))],
            [speed * math.cos(end), speed * math.sin(end)])


def target_state(target, when):
    p, v = list(target["position_at_birth"]), list(target["velocity"])
    previous, rate = target["birth"], 0.0
    assert not target.get("turns"), "This audit's frozen actual targets use continuous arc rates"
    for at, next_rate in target["arc_rates"]:
        if at > when:
            break
        p, v = _arc(p, v, rate, at - previous)
        previous, rate = at, next_rate
    return _arc(p, v, rate, when - previous)


def _escape(target, side, end):
    """Independent scalar crossing search on monotone portions of actual arcs."""
    boundaries = [target["birth"]] + [at for at, _ in target["arc_rates"] if target["birth"] < at < end] + [end]
    for lo, hi in zip(boundaries[:-1], boundaries[1:]):
        p, v = target_state(target, lo)
        if p[0] >= side:
            return lo
        rate = next((omega for at, omega in reversed(target["arc_rates"]) if at <= lo), 0.0)
        cuts = [lo, hi]
        if abs(rate) > 1e-12:
            theta = math.atan2(v[1], v[0]); finish = theta + rate * (hi - lo)
            for k in range(math.floor((min(theta, finish) - math.pi / 2) / math.pi) - 1,
                           math.ceil((max(theta, finish) - math.pi / 2) / math.pi) + 2):
                at = lo + (math.pi / 2 + k * math.pi - theta) / rate
                if lo < at < hi:
                    cuts.append(at)
        for left, right in zip(sorted(cuts)[:-1], sorted(cuts)[1:]):
            if target_state(target, left)[0][0] >= side:
                return left
            if target_state(target, right)[0][0] < side:
                continue
            a, b = left, right
            for _ in range(64):
                middle = (a + b) / 2
                if target_state(target, middle)[0][0] >= side:
                    b = middle
                else:
                    a = middle
            return b
    return math.inf


def _team(actions, target):
    return [(i, a["role"]) for i, a in enumerate(actions) if a["target"] == target]


def _geometry(positions, team, point, cfg):
    return bool(team) and all(math.hypot(positions[i][0] - point[0] - cfg["observation_radius"] * math.cos(ANGLES[role]),
                                          positions[i][1] - point[1] - cfg["observation_radius"] * math.sin(ANGLES[role]))
                              <= cfg["observation_tolerance"] + TOL for i, role in team)


def _profiles(source, tick):
    row = max((r for r in source["sensor_declaration_schedule"] if r["effective_tick"] <= tick), key=lambda r: r["effective_tick"])
    return [dict(p, observed_tick=tick) for p in row["profiles"]]


def audit_episode(job, out):
    index = read_json(job["episode_index_file"])
    design = read_json(index["design_file"])
    declared = next(e for e in design["episodes"] if e["episode_id"] == index["episode_id"])
    raw = read_json(index["private_input_file"])
    source = raw.get("private_execution_input", raw)
    assert source == declared["private_execution_input"], "Actual episode input changed from its declared design"
    cfg, targets = source["config"], source["targets"]
    X, Y, end_tick = cfg["robots"], cfg["task_count"], round(cfg["stage_dt"] * cfg["max_stages"] / .05)
    assert len(targets) == Y and [t["id"] for t in targets] == list(range(Y))
    positions = [list(p) for p in source["positions_initial"]]
    actions = [dict(target=None, role="none") for _ in range(X)]
    statuses = ["active" if t["birth"] == 0 else "hidden" for t in targets]
    clocks = [Fraction() for _ in targets]
    left = {}
    escapes = [_escape(t, cfg["side"], end_tick * .05) for t in targets]
    flow = late = completion = Fraction()
    energy = 0.0
    energy_by_robot = [0.0] * X
    busy = [Fraction() for _ in range(X)]
    changes = 0
    completions, ended, birth_events, resets, keeps, reused = [], [], [], [], [], []
    eligible_release = {}
    all_fusions, quality_counts, positions_at = [], Counter(), {0: [list(p) for p in positions]}
    recorded_positions_at = {0: [list(p) for p in positions]}
    segment_ids = [None] * Y
    segment_counts = [0] * Y
    previous_segments = [None] * Y
    expected_events = []
    multi_history = []
    selected_at = {}
    terminal_charged = False

    def event(kind, j, when, before=0.0, after=0.0, segment=None, reasons=()):
        n = round(when / .05)
        row = dict(event_index=len(expected_events), kind=kind, target_id=j,
            at=dict(time_seconds=when, event_tick=n if abs(n * .05 - when) <= TOL else None),
            segment_id=segment, progress_before=float(before), progress_after=float(after), reasons=list(reasons))
        expected_events.append(row)
        return row

    for target in targets:
        if target["birth"] == 0:
            birth_events.append((target["id"], 0))
            event("BIRTH", target["id"], 0.0, reasons=["BIRTH"])

    def metrics(tick):
        components = dict(completion=float(completion / (4 * Y)),
            flow=float(-Fraction(str(cfg["flow_weight"])) * flow / (4 * Y * Fraction(str(cfg["stage_dt"])))),
            late=float(-Fraction(str(cfg["late_weight"])) * late / (4 * Y * Fraction(str(cfg["stage_dt"])))),
            effort=-cfg["control_weight"] * energy / (X * cfg["stage_dt"] * cfg["control_reference"] ** 2),
            terminal=-cfg["unfinished_weight"] * sum(t["weight"] for t in targets if statuses[t["id"]] != "completed") / (4 * Y)
            if terminal_charged else 0.0)
        cost = cfg["change_cost"] * changes
        physical = math.fsum(components.values())
        return dict(reward_components=components, return_without_changes=physical, return_with_changes=physical - cost,
            assignment_changes=changes, change_cost=cost, control_integral=energy, effort_by_robot=energy_by_robot,
            occupied_robot_seconds=float(sum(busy)), idle_robot_seconds=float(X * tick * DT - sum(busy)),
            flow=float(flow), late=float(late))

    def compare_frame(frame, tick, control):
        assert frame["tick"] == tick
        close(frame["positions"], positions, label="actual independent positions")
        close(frame["control"], control, label="actual independent control")
        assert frame["assignment"] == actions and frame["statuses"] == statuses
        for j, target in enumerate(targets):
            if target["birth"] <= tick * .05 + TOL:
                close(frame["progress"][str(j)], float(clocks[j]), label="independent Fraction GQ clock")
        for key, value in metrics(tick).items():
            close(frame["metrics"][key], value, label="real ledger/" + key)

    for decision in index["decisions"]:
        k = decision["tick"]
        assert k == len(selected_at) * 20 and k < end_tick
        selection = read_json(decision["selection_file"])
        assert selection["passed"] and selection["optimality_checked"] and selection["tie_rule_checked"]
        assert read_json(decision["selection_audit_file"])["passed"], "Decision audit must precede episode acceptance"
        step = read_json(decision["step_result_file"])
        assert step["status"] == "COMMITTED" and not step["replayed"]
        assert step["start_tick"] == k and step["end_tick"] == min(k + 20, end_tick)
        chosen = selection["actions"]
        selected_at[k] = chosen
        cp_before = (read_json(index["initial_artifacts"]["public_checkpoint"]) if k == 0 else
                     prior_checkpoint)
        assert selection["checkpoint_id"] == cp_before["checkpoint_id"] == step["action_commit"]["checkpoint_id"]
        assert cp_before["assignment"] == actions
        close(cp_before["positions"], positions)
        assert cp_before["sensor_profiles"] == _profiles(source, k)
        live_histories = [h for h in cp_before["task_histories"] if h["active_segment_id"] is not None]
        if len(live_histories) >= 2:
            multi_history.append(dict(tick=k, targets=[h["target_id"] for h in live_histories]))
        for j in range(Y):
            team = _team(chosen, j)
            assert not team or (statuses[j] == "active" and len(team) == targets[j]["required_robots"] and
                                {r for _, r in team} == ROLES[targets[j]["required_robots"]])
        assert len(chosen) == X
        transition_map = {r["target_id"]: r for r in step["action_commit"]["transitions"]}
        assert set(transition_map) == {j for j in range(Y) if statuses[j] == "active"}
        fusion_map = {}
        for row in step["fusion_records"]:
            key = row["frame"]["target_id"], row["frame"]["tick"]
            assert key not in fusion_map, "Repeated actual fusion in one committed segment/step"
            fusion_map[key] = row
            q = audit_fusion(row)
            quality_counts.update(q["counts"])
            all_fusions.append(row)

        def endpoint(j, tick, team):
            row = fusion_map.pop((j, tick))
            actual = row["actual_endpoint"]
            assert row["context"]["purpose"] == "ACTUAL_EXECUTION"
            assert row["context"]["segment_id"] == segment_ids[j]
            assert row["context"]["checkpoint_id"] == cp_before["checkpoint_id"]
            assert actual["team"] == [dict(robot_id=i, role=r) for i, r in team]
            g = _geometry(positions, team, target_state(targets[j], tick * .05)[0], cfg)
            assert actual["G"] == g and actual["quality"]["status"] == row["result"]["quality"]["status"]
            close([r["position"] for r in row["frame"]["records"]],
                  [positions[int(r["sensor_id"][1:])] for r in row["frame"]["records"]])
            return actual

        for j in sorted(transition_map):
            old_team, team = _team(actions, j), _team(chosen, j)
            old_segment = segment_ids[j]
            transition = transition_map[j]
            if team and team == old_team:
                kind = "KEEP"
                assert transition["actual_left_endpoint"] == left[j]
                if clocks[j] > 0:
                    keeps.append(dict(target_id=j, tick=k, progress_before=float(clocks[j]), segment_id=old_segment))
            elif not team:
                kind = "WITHDRAW" if old_team else "UNCHANGED_UNASSIGNED"
                if old_team:
                    event("WITHDRAWN", j, k * .05, clocks[j], 0.0, old_segment, ["WITHDRAWAL"])
                clocks[j] = Fraction();segment_ids[j] = None;left.pop(j, None)
            else:
                if not old_team:
                    kind = "REASSIGN" if segment_counts[j] else "FIRST_ASSIGNMENT"
                    opened = "REASSIGNMENT" if segment_counts[j] else "INITIAL_ASSIGNMENT"
                else:
                    kind = "ROLE_CHANGE" if [i for i, _ in old_team] == [i for i, _ in team] else "MEMBER_CHANGE"
                    opened = kind
                    event("ROLE_CHANGED" if kind == "ROLE_CHANGE" else "TEAM_CHANGED", j, k * .05,
                          clocks[j], 0.0, old_segment, [kind])
                clocks[j] = Fraction()
                segment_ids[j] = digest(dict(contract_id="gq_online_service_segment_v1", target_id=j,
                    segment_index=segment_counts[j], previous_segment_id=previous_segments[j], start_tick=k,
                    team=[dict(robot_id=i, role=r) for i, r in team], opened_by=opened))
                previous_segments[j] = segment_ids[j];segment_counts[j] += 1
                event("ASSIGNED", j, k * .05, segment=segment_ids[j], reasons=[opened])
                left[j] = endpoint(j, k, team)
            assert transition["kind"] == kind and transition["new_segment_id"] == segment_ids[j]
            clock_after = transition["clock_after"]
            close(math.fsum((clock_after["base"], clock_after["intervals"] * .05)), float(clocks[j]))
        delta_changes = sum(a != b for a, b in zip(actions, chosen))
        assert delta_changes == step["action_commit"]["assignment_change_count"]
        close(step["action_commit"]["change_cost"], cfg["change_cost"] * delta_changes)
        for i, (old_action, action) in enumerate(zip(actions, chosen)):
            if old_action["target"] is None and action["target"] is not None and i in eligible_release:
                origin = eligible_release[i]
                if origin["target_id"] != action["target"]:
                    reused.append(dict(robot_id=i, old_target=origin["target_id"], completion_time=origin["time"],
                                       new_target=action["target"], decision_tick=k, autonomous_selection_verified=True))
                del eligible_release[i]
        changes += delta_changes
        actions = [dict(a) for a in chosen]
        assert len(step["frames"]) == 21
        compare_frame(step["frames"][0], k, [[0.0, 0.0] for _ in range(X)])
        for offset, n in enumerate(range(k + 1, k + 21), 1):
            lo, hi = Fraction(n - 1, 20), Fraction(n, 20)
            controls = [[0.0, 0.0] for _ in range(X)]
            for j, target in enumerate(targets):
                if statuses[j] != "active":
                    continue
                team = _team(actions, j)
                escape = escapes[j]
                stop = Fraction(str(escape)) if escape <= float(hi) else hi
                elapsed = max(Fraction(), stop - lo)
                accounting_stop = Fraction(str(escape)) if escape <= float(hi) + TOL else hi
                flow += Fraction(str(target["weight"])) * max(Fraction(), accounting_stop - max(lo, Fraction(str(target["birth"]))))
                late += Fraction(str(target["weight"])) * max(Fraction(), accounting_stop - max(lo, Fraction(str(target["birth"])), Fraction(str(target["deadline"]))))
                p, velocity = target_state(target, float(lo))
                for robot, role in team:
                    theta = ANGLES[role]
                    anchor = [p[0] + cfg["observation_radius"] * math.cos(theta), p[1] + cfg["observation_radius"] * math.sin(theta)]
                    u = [velocity[a] + cfg["travel_gain"] * (anchor[a] - positions[robot][a]) for a in (0, 1)]
                    scale = min(1.0, cfg["max_speed"] / max(math.hypot(*u), 1e-15))
                    u = [v * scale for v in u];controls[robot] = u
                    positions[robot] = [positions[robot][a] + u[a] * float(elapsed) for a in (0, 1)]
                    cost = math.fsum(v * v for v in u) * float(elapsed)
                    energy += cost;energy_by_robot[robot] += cost;busy[robot] += elapsed
                terminal = None
                if escape <= float(hi) + TOL:
                    terminal, when = "escaped", escape
                elif team:
                    right = endpoint(j, n, team)
                    valid = left[j]["G"] and right["G"] and left[j]["quality"]["status"] == right["quality"]["status"] == "PASS"
                    before = clocks[j]
                    clocks[j] = clocks[j] + DT if valid else Fraction()
                    if not valid and before > 0:
                        reasons = []
                        if not left[j]["G"] or not right["G"]: reasons.append("GEOMETRY_INVALID")
                        if "FAIL" in (left[j]["quality"]["status"], right["quality"]["status"]): reasons.append("QUALITY_FAIL")
                        if "UNKNOWN" in (left[j]["quality"]["status"], right["quality"]["status"]): reasons.append("QUALITY_UNKNOWN")
                        event("INTERRUPTED", j, n * .05, before, 0.0, segment_ids[j], reasons)
                        resets.append(dict(target_id=j, tick=n, progress_before=float(before), reasons=reasons))
                    left[j] = right
                    if float(clocks[j]) >= target["service_duration"] - TOL:
                        clocks[j] = Fraction(str(target["service_duration"]))
                        terminal, when = "completed", n * .05
                if terminal is not None:
                    statuses[j] = terminal
                    event("COMPLETED" if terminal == "completed" else "ESCAPED", j, when, clocks[j], clocks[j],
                          segment_ids[j], ["SERVICE_COMPLETE" if terminal == "completed" else "ESCAPE"])
                    record = dict(target_id=j, time=when, tick=n, robots=[i for i, _ in team])
                    ended.append(record)
                    if terminal == "completed":
                        completion += Fraction(str(target["weight"]))
                        completions.append(record)
                        for i, _ in team: eligible_release[i] = record
                    for i, _ in team: actions[i] = dict(target=None, role="none")
                    segment_ids[j] = None
            for j, target in enumerate(targets):
                if statuses[j] == "hidden" and target["birth"] <= n * .05 + TOL:
                    statuses[j] = "active";birth_events.append((j, n))
                    event("BIRTH", j, target["birth"], reasons=["BIRTH"])
            if n == end_tick:
                for j in range(Y):
                    if statuses[j] == "active":
                        event("EPISODE_ENDED", j, n * .05, clocks[j], clocks[j], segment_ids[j], ["EPISODE_END"])
                        statuses[j] = "unfinished";segment_ids[j] = None
                actions = [dict(target=None, role="none") for _ in range(X)]
                terminal_charged = True
            compare_frame(step["frames"][offset], n, controls)
            positions_at[n] = [list(p) for p in positions]
            recorded_positions_at[n] = step["frames"][offset]["positions"]
        assert not fusion_map, "Unused actual fusion suggests extra sampling or same-boundary reselection"
        prior_checkpoint = step["checkpoint_after"]
        assert prior_checkpoint["tick"] == k + 20
        close(prior_checkpoint["positions"], positions)
        assert prior_checkpoint["assignment"] == actions
        assert prior_checkpoint["sensor_profiles"] == _profiles(source, k + 20)
    assert sorted(selected_at) == list(range(0, end_tick, 20))
    final = read_json(index["final_artifacts"]["private_snapshot"])
    state, cache = final["state"], final["sampler"]
    assert state["tick"] == end_tick and state["statuses"] == statuses and not final["failed"] and final["inflight"] is None
    close(state["events"], expected_events, 1e-10, "independent event chronology")
    assert final["fusions"] == all_fusions
    for record in completions:
        archive = state["archives"][str(record["target_id"])]
        assert archive["released_robots"] == record["robots"] and archive["release_change_cost"] == 0.0
    metric = metrics(end_tick)
    last_step = read_json(index["decisions"][-1]["step_result_file"])
    for key, value in metric.items(): close(last_step["metrics"][key], value, label="final independent O/" + key)
    entries = {tuple(row["raw_key"]): row for row in cache["entries"]}
    assert len(entries) == len(cache["entries"]) == len(cache["attempts"])
    assert len({tuple(row["raw_key"]) for row in cache["attempts"]}) == len(cache["attempts"])
    used = set();query_count = 0
    for row in all_fusions:
        frame, endpoint_value = row["frame"], row["actual_endpoint"]
        j, n = frame["target_id"], frame["tick"]
        records = {int(r["sensor_id"][1:]): r for r in frame["records"]}
        for reference in endpoint_value["slots"]:
            i = reference["slot_key"]["robot_id"]
            key = (final["physical_environment_id"], j, i, n)
            used.add(key);query_count += 1
            slot = entries[key]["slot"]
            assert slot["state"] == reference["state"] and slot["slot_digest"] == reference["slot_digest"]
            profile = _profiles(source, n)[i]
            assert entries[key]["context_digest"] == digest(dict(position=recorded_positions_at[n][i],
                sigma=profile["sigma"], health=profile["health"]))
            if profile["health"] == "missing":
                assert slot["state"] == "MISSING" and i not in records
            else:
                assert slot["state"] == "VALID"
                packet = slot["packet"]
                assert packet == {k: v for k, v in records[i].items() if k != "packet_id"}
                close(packet["position"], positions_at[n][i])
                p = target_state(targets[j], n * .05)[0]
                bearing = math.atan2(p[1] - positions_at[n][i][1], p[0] - positions_at[n][i][0])
                close((packet["bearing"] - bearing + math.pi) % (2 * math.pi) - math.pi, 0.0)
                assert packet["sigma"] == profile["sigma"] and packet["measurement_tick"] == packet["available_tick"] == n
    assert used == set(entries), "Actual cache contains a value not produced for an actual selected team"
    assert cache["requests"] == query_count and cache["reuses"] == query_count - len(entries)
    for attempt in cache["attempts"]:
        assert attempt["outcome"] in ("VALID", "MISSING")
    coverage = dict(numerical_contract_passed=True, research_coverage_required=index["episode_id"] in ("N1", "N2"),
        positive_actual_KEEP_boundaries=keeps, actual_completion_releases=completions,
        multi_active_verified_history_checkpoints=multi_history, completed_resource_reuses=reused,
        actual_quality_resets=resets, birth_events=[dict(target_id=j, tick=n) for j, n in birth_events])
    if index["episode_id"] == "N1":
        coverage["research_coverage_passed"] = any(any(c["target_id"] == keep["target_id"] and c["time"] >= keep["tick"] * .05 for c in completions) for keep in keeps)
    elif index["episode_id"] == "N2":
        coverage["research_coverage_passed"] = bool(multi_history and (2, 60) in birth_events and reused)
    else:
        coverage["research_coverage_passed"] = None
    coverage["stage_all_objectives_validated"] = coverage["research_coverage_passed"] is not False
    coverage["classification"] = ("LEGAL_PATH_BUT_REQUIRED_RESEARCH_WITNESS_NOT_OBTAINED"
                                  if coverage["research_coverage_passed"] is False else "NUMERICAL_CONTRACT_AND_APPLICABLE_COVERAGE_PASSED")
    conditional = dict(applied=False, reason="actual action/GQ antecedent did not establish the predeclared conditional path")
    pair = lambda target, robots: [dict(target=target if i in robots else None,
        role="dual_neg45" if i == robots[0] else "dual_pos45" if i == robots[1] else "none") for i in range(X)]
    eid = index["episode_id"]
    canonical = eid in ("N1", "N4A") and selected_at[0] == pair(0, [0, 1]) and selected_at[20] == pair(0, [0, 1])
    if eid == "N3":
        canonical = selected_at[0] == pair(0, [0, 1]) and selected_at[20] == pair(0, [0, 2]) and selected_at[40] == pair(0, [0, 2])
    if eid == "N2":
        both = [dict(target=0 if i < 2 else 1, role="dual_neg45" if i % 2 == 0 else "dual_pos45") for i in range(4)]
        canonical = selected_at[0] == both and selected_at[20] == both and selected_at[60] == pair(2, [0, 1])
    expected = declared["expected_only"].get("conditional_ledger")
    expected_ticks = ({0: 27} if eid in ("N1", "N4A") else {0: 41} if eid == "N3" else {0: 27, 1: 31, 2: 64})
    quality_condition = canonical and all(any(c["target_id"] == j and c["tick"] == tick for c in completions) for j, tick in expected_ticks.items())
    if expected is not None and quality_condition:
        fields = {"net_O": "return_with_changes", "physical_O": "return_without_changes",
                  "control_integral": "control_integral", "occupied_robot_seconds": "occupied_robot_seconds",
                  "idle_robot_seconds": "idle_robot_seconds", "change_cost": "change_cost", "flow_raw": "flow", "late_raw": "late"}
        for key, actual_key in fields.items(): close(metric[actual_key], expected[key]["float64_display"], label="conditional closed form/" + key)
        for key, value in expected["reward_components"].items(): close(metric["reward_components"][key], value["float64_display"])
        assert changes == expected["assignment_changes"]
        conditional = dict(applied=True, reason="actual prescribed actions and actual GQ completion trace matched; no action was forced")
    report = dict(passed=True, episode_id=eid, numerical_contract_passed=True,
        all_episode_objectives_passed=coverage["stage_all_objectives_validated"], metrics=metric,
        coverage=coverage, conditional_expected_only_check=conditional, quality_counts=dict(quality_counts),
        decisions=len(selected_at), actual_fusions=len(all_fusions), unique_raw_measurements=len(entries),
        cache_reuses=cache["reuses"], independent_motion="scalar continuous-arc target and per-robot norm-clipped controller",
        independent_clock="Fraction(1,20) complete intervals with real endpoint Q, actual team resets and escape precedence",
        scope="Saved actual decisions and traces only; no controller, estimator or scientific rerun")
    save_json(Path(out) / "episode_audit.json", report)
    return report
