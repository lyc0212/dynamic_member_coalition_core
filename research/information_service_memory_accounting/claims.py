"""Pure metadata decisions for the frozen memory-accounting protocol.

No cache, oracle, scientific evaluator, file reader or worker is invoked here.
Actual source, live-object, process and read evidence belongs to the producers
and auditors; a numeric result is never a replacement for those observations.
"""
from copy import deepcopy
import math
from statistics import median


RUNS = ("OLD_a", "NEW_a", "NEW_b", "OLD_b")
C_IDS = tuple(f"C{i:02d}" for i in range(1, 11))
P_IDS = ("P01", "P_ENV", "P_WORKER", "P_VARIATION")
RUNTIME_IDS = C_IDS + P_IDS
ITEM_STATUSES = {"NOT_EVALUATED", "UNAVAILABLE", "FAILED", "VERIFIED",
                 "TARGET_MET", "TARGET_NOT_MET"}
RESULT_FIELDS = ['id', 'status', 'owner', 'evidence_refs', 'checks_completed',
                 'actual_work_counters', 'unknown_or_missing_evidence']
OWNERS = {key: 'gate_auditor' for key in C_IDS[:7]}
OWNERS.update(C08='saved_result_auditor', C09='final_launcher',
              C10='saved_result_auditor', P01='saved_result_auditor')
OWNERS.update({key: 'final_launcher' for key in P_IDS[1:]})


class MemoryClaimsError(ValueError):
    def __init__(self, code, **details):
        self.code = code
        self.details = details
        super().__init__(code)


def _finite(value):
    if type(value) not in (int, float):
        return False
    try:
        return math.isfinite(value)
    except (OverflowError, ValueError):
        return False


def _require(condition, code, **details):
    if not condition:
        raise MemoryClaimsError(code, **details)


def evaluate_cpu(costs_by_run):
    """Evaluate the four fresh final-wait4 records; grant no source authority."""
    _require(type(costs_by_run) is dict and set(costs_by_run) == set(RUNS),
             "CPU_RUN_COVERAGE")
    costs = {}
    for run in RUNS:
        row = costs_by_run[run]
        _require(type(row) is dict, "CPU_RECORD_TYPE", run=run)
        for field in ("env_CPU", "sense_CPU", "worker_CPU"):
            value = row.get(field)
            _require(type(value) is float and math.isfinite(value),
                     "CPU_INPUT_UNAVAILABLE_OR_INVALID", run=run, field=field)
            _require(value > 0 if field == "env_CPU" else value >= 0,
                     "CPU_INPUT_UNAVAILABLE_OR_INVALID", run=run, field=field)
        expected_worker = math.fsum((row["env_CPU"], row["sense_CPU"]))
        _require(math.isfinite(expected_worker) and row["worker_CPU"] == expected_worker,
                 "WORKER_CPU_ROLE_RECONCILIATION", run=run)
        costs[run] = {field: row[field] for field in ("env_CPU", "sense_CPU", "worker_CPU")}
    old = [costs[run]["env_CPU"] for run in ("OLD_a", "OLD_b")]
    new = [costs[run]["env_CPU"] for run in ("NEW_a", "NEW_b")]
    med_old, med_new = median(old), median(new)
    _require(_finite(med_old) and med_old > 0 and _finite(med_new) and med_new > 0,
             "CPU_DERIVED_DENOMINATOR_INVALID")
    metrics = dict(
        r_a=costs["NEW_a"]["env_CPU"] / costs["OLD_a"]["env_CPU"],
        r_b=costs["NEW_b"]["env_CPU"] / costs["OLD_b"]["env_CPU"],
        median_ratio=med_new / med_old,
        relative_reduction=1.0 - med_new / med_old,
        v_OLD_env=(max(old) - min(old)) / med_old,
        v_NEW_env=(max(new) - min(new)) / med_new,
    )
    _require(all(_finite(value) for value in metrics.values()), "CPU_DERIVED_NONFINITE")
    worker_pairs = {
        "a": costs["NEW_a"]["worker_CPU"] <= costs["OLD_a"]["worker_CPU"],
        "b": costs["NEW_b"]["worker_CPU"] <= costs["OLD_b"]["worker_CPU"],
    }
    targets = dict(
        P_ENV=metrics["r_a"] < 1.0 and metrics["r_b"] < 1.0,
        P_WORKER=all(worker_pairs.values()),
        P_VARIATION=metrics["v_OLD_env"] <= .15 and metrics["v_NEW_env"] <= .15,
    )
    return dict(cpu_evidence_complete=True, raw_costs=costs, metrics=metrics,
                worker_pair_comparisons=worker_pairs, targets=targets,
                criteria_all_met=all(targets.values()),
                variation_scope="ENV_FINAL_WAIT4_CPU_ONLY",
                controller_guardian_launcher_in_worker=False,
                scope="pure fixed-batch metadata arithmetic; no source admission")


def cpu_claims(costs_by_run, evidence_refs, *, actual_work_counters):
    """Build the three evaluated numeric claims, not P01 source admission."""
    evaluation = evaluate_cpu(costs_by_run)
    refs = list(evidence_refs)
    rows = []
    metrics = evaluation["metrics"]
    values = {
        "P_ENV": {key: metrics[key] for key in ("r_a", "r_b")},
        "P_WORKER": dict(evaluation["worker_pair_comparisons"]),
        "P_VARIATION": {key: metrics[key] for key in ("v_OLD_env", "v_NEW_env")},
    }
    for identifier in P_IDS[1:]:
        target = evaluation["targets"][identifier]
        rows.append(dict(
            id=identifier, status="TARGET_MET" if target else "TARGET_NOT_MET",
            owner="final_launcher", evidence_refs=deepcopy(refs),
            checks_completed=["FROZEN_FOUR_RUN_FORMULA", "NO_EPSILON", "VALID_FINITE_INPUTS"],
            actual_work_counters=deepcopy(actual_work_counters), unknown_or_missing_evidence=[],
            numeric_evaluation_complete=True, observed_values=deepcopy(values[identifier]),
            target_met=target, cpu_inputs=deepcopy(evaluation["raw_costs"])))
    return rows


def _same(value, expected):
    if type(expected) is bool:
        return type(value) is bool and value is expected
    if type(expected) in (int, float):
        return type(value) is type(expected) and _finite(value) and value == expected
    if type(expected) is dict:
        return type(value) is dict and set(value) == set(expected) and all(
            _same(value[key], expected[key]) for key in expected)
    if type(expected) is list:
        return type(value) is list and len(value) == len(expected) and all(
            _same(a, b) for a, b in zip(value, expected))
    return type(value) is type(expected) and value == expected


def decide(claims, matrix, *, executed=True, final=False):
    """Fail closed; keep algorithm, records, science and CPU conclusions apart."""
    answer = dict(status="INCOMPLETE_EVIDENCE", correctness_passed=False,
                  cpu_evaluation_complete=False, observed_cpu_improvement=None,
                  phase="FINAL" if final else "PRELIMINARY", issues=[],
                  same_live_graph_algorithm_passed=False,
                  record_consistency_passed=False, scientific_equivalence_passed=False,
                  historical_status_unchanged=True)

    def fail(code, **details):
        answer.update(status="FAILED", failure_code=code)
        answer["issues"].append(dict(code=code, **details))
        return answer

    if type(executed) is not bool or type(final) is not bool:
        return fail("DECISION_MODE_TYPE")
    if not executed:
        answer["status"] = "PREPARED_NOT_IMPLEMENTED_NOT_EXECUTED"
        return answer
    if not (type(matrix) is dict and matrix.get("exact_runtime_result_id_set") == list(RUNTIME_IDS)
            and matrix.get("required_correctness_ids") == list(C_IDS)
            and matrix.get("required_cpu_evidence_ids") == ["P01"]
            and matrix.get("required_cpu_evaluation_ids") == list(P_IDS[1:])
            and matrix.get('required_result_fields') == RESULT_FIELDS):
        return fail("MATRIX_IDENTITY_OR_SCOPE")
    definitions = matrix.get("claims")
    if type(definitions) is not list or any(type(row) is not dict for row in definitions):
        return fail("MATRIX_DEFINITIONS")
    if any(type(row.get('id')) is not str for row in definitions):
        return fail('MATRIX_DEFINITIONS')
    rules = {row.get("id"): row for row in definitions}
    if len(rules) != len(definitions) or set(rules) != set(RUNTIME_IDS):
        return fail("MATRIX_DEFINITIONS")
    for key,rule in rules.items():
        accepted=['TARGET_MET','TARGET_NOT_MET'] if key in P_IDS[1:] else ['VERIFIED']
        if rule.get('owner')!=OWNERS[key] or rule.get('accepted_statuses')!=accepted:
            return fail('MATRIX_OWNER_OR_STATUS_SCOPE',claim_id=key)
    if type(claims) is dict:
        if any(type(row) is not dict or row.get("id") != key for key, row in claims.items()):
            return fail("CLAIM_MAP_IDENTITY")
        entries = list(claims.values())
    elif type(claims) is list:
        entries = claims
    else:
        return fail("CLAIM_COLLECTION")
    found = {}
    for row in entries:
        if type(row) is not dict or row.get("id") not in RUNTIME_IDS:
            return fail("UNKNOWN_RUNTIME_CLAIM")
        identifier = row["id"]
        if identifier in found:
            return fail("DUPLICATE_RUNTIME_CLAIM", claim_id=identifier)
        found[identifier] = row
    missing = []
    failures = []
    for identifier in RUNTIME_IDS:
        row = found.get(identifier)
        if row is None:
            missing.append(identifier)
            continue
        status = row.get("status")
        if type(status) is not str or status not in ITEM_STATUSES:
            return fail("UNKNOWN_ITEM_STATUS", claim_id=identifier)
        if row.get("owner") != rules[identifier].get("owner"):
            return fail("CLAIM_OWNER", claim_id=identifier)
        if identifier == "C09" and not final and status == "VERIFIED":
            return fail("WORKER_POST_REAP_PREFILL", claim_id=identifier)
        if status == "FAILED":
            failures.append(identifier)
            continue
        if status in ("UNAVAILABLE", "NOT_EVALUATED"):
            missing.append(identifier)
            continue
        if status not in rules[identifier].get("accepted_statuses", []):
            return fail("CLAIM_STATUS_SCOPE", claim_id=identifier)
        fields = matrix.get("required_result_fields", [])
        if any(key not in row for key in fields):
            missing.append(identifier)
            continue
        if (type(row["evidence_refs"]) is not list or not row["evidence_refs"]
                or any(not ((type(ref) is str and bool(ref)) or
                            (type(ref) is dict and type(ref.get('path')) is str and bool(ref['path'])))
                       for ref in row['evidence_refs'])
                or type(row["checks_completed"]) is not list or not row["checks_completed"]
                or any(type(key) is not str or not key for key in row["checks_completed"])
                or type(row["actual_work_counters"]) is not dict or not row["actual_work_counters"]
                or any(not _finite(value) or value < 0 for value in row["actual_work_counters"].values())
                or row["unknown_or_missing_evidence"] != []):
            missing.append(identifier)
    answer["claim_statuses"] = {key: row.get("status") for key, row in found.items()}
    answer["missing_or_incomplete_ids"] = list(dict.fromkeys(missing))
    valid_c = lambda identifier: identifier not in missing and found.get(identifier, {}).get("status") == "VERIFIED"
    answer["same_live_graph_algorithm_passed"] = final and all(valid_c(key) for key in C_IDS[:7] + ("C09",))
    answer["record_consistency_passed"] = final and valid_c("C10") and valid_c("C09")
    answer["scientific_equivalence_passed"] = final and valid_c("C08") and valid_c("C09")
    answer["correctness_passed"] = final and all(valid_c(key) for key in C_IDS)
    if failures:
        answer.update(status="STOPPED_RESOURCE_OR_ACCOUNTING_FAILURE" if "C09" in failures else "FAILED",
                      failed_ids=failures)
        return answer
    if not answer["correctness_passed"]:
        answer["status"] = "INCOMPLETE_EVIDENCE" if missing or not final else "FAILED"
        return answer
    if any(key in missing for key in P_IDS):
        answer["status"] = "CORRECTNESS_PASSED_CPU_EVIDENCE_INCOMPLETE"
        return answer
    p01 = found["P01"]
    try:
        evaluated = evaluate_cpu(p01.get("cpu_inputs"))
        expected_values = {
            "P_ENV": {key: evaluated["metrics"][key] for key in ("r_a", "r_b")},
            "P_WORKER": evaluated["worker_pair_comparisons"],
            "P_VARIATION": {key: evaluated["metrics"][key] for key in ("v_OLD_env", "v_NEW_env")},
        }
        for key in P_IDS[1:]:
            row = found[key]
            _require(row.get("numeric_evaluation_complete") is True,
                     "CPU_EVALUATION_NOT_COMPLETED", claim_id=key)
            _require(_same(row.get("cpu_inputs"), evaluated["raw_costs"]),
                     "CPU_INPUT_SCOPE_CHANGED", claim_id=key)
            _require(_same(row.get("observed_values"), expected_values[key]),
                     "CPU_FORMULA_RECORD_CHANGED", claim_id=key)
            target = evaluated["targets"][key]
            _require(row.get("target_met") is target and row["status"] ==
                     ("TARGET_MET" if target else "TARGET_NOT_MET"),
                     "CPU_TARGET_RECORD_CHANGED", claim_id=key)
    except MemoryClaimsError as error:
        answer.update(status="CORRECTNESS_PASSED_CPU_EVIDENCE_INCOMPLETE",
                      cpu_failure_code=error.code, cpu_failure_details=error.details)
        return answer
    answer.update(cpu_evaluation_complete=True, cpu_evaluation=evaluated,
                  observed_cpu_improvement=evaluated["criteria_all_met"],
                  status="FIXED_BATCH_CPU_REDUCTION_OBSERVED" if evaluated["criteria_all_met"]
                  else "CORRECTNESS_PASSED_CPU_TARGET_NOT_MET")
    return answer
