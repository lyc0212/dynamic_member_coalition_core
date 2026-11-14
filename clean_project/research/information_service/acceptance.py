"""Truth-side independent audits and shadow accounting; never called by sensing."""
import copy
import json
import math
from pathlib import Path

import numpy as np

from pursuit_v2.config import Config
from .common import DT, digest, save_json
from .oracle import quality_at, ray_intersection, truth_error
from .shadow_service import ShadowLedger, physical_valid


def read(path):
    return json.loads(Path(path).read_text())


def close(actual, expected, atol=1e-12, rtol=0):
    np.testing.assert_allclose(actual, expected, atol=atol, rtol=rtol)


def audit_quality(result, expected, truth, *, degenerate=False):
    quality, payload = result["quality"], result["payload"]
    record = dict(status=quality["status"], estimate=quality["estimate"],
                  actual_error=truth_error(quality["estimate"], truth),
                  radius_proxy=quality["radius_proxy"])
    assert digest(payload) == result["payload_sha256"]
    if degenerate:
        assert quality["status"] != "PASS", "Collinear input falsely passed"
    else:
        assert quality["status"] == expected["expected_Q"], (quality, expected)
    if quality["has_estimate"] and not degenerate:
        close(quality["estimate"], expected["ideal_estimate"], atol=1e-6)
        reference = quality_at(payload, quality["estimate"])
        close(quality["J"], reference["jacobian"], atol=1e-10, rtol=1e-10)
        close(quality["I"], reference["information"], atol=1e-9, rtol=1e-12)
        close(quality["radius_proxy"], reference["radius_proxy"], atol=1e-12, rtol=1e-12)
        ideal_radius = expected["scalar_quality_reference"]["radius_proxy"]
        close(quality["radius_proxy"], ideal_radius, atol=1e-6)
        record["independent_quality_at_same_estimate"] = reference
    return record


def replay(case, sense_rows):
    cfg = Config(**case["config"])
    ledgers = {mode: ShadowLedger(cfg, case["team"], case["duration"],
                                 stream_id=case["case_id"], end_time=case["end_time"],
                                 birth=case["birth"], deadline=case["deadline"], mode=mode)
               for mode in ("G", "GQ")}
    output = {mode: [] for mode in ledgers}
    errors = []
    assert len(sense_rows) == len(case["frames"])
    for index, (physical, sensed) in enumerate(zip(case["frames"], sense_rows)):
        tick = physical["public"]["tick"]
        assert sensed["tick"] == tick and sensed["repeat"] == 0
        result = sensed["result"]
        G = physical_valid(cfg, case["q"], case["team"], physical["truth"], physical["positions"])
        assert G == physical["expected_G"]
        expected = case["expected"]["endpoint_references"][index]
        errors.append(audit_quality(result, expected, physical["truth"]))
        if index:
            previous = case["frames"][index-1]
            velocity = (np.asarray(physical["positions"]) - previous["positions"]) / DT
            close(np.sum(velocity**2, axis=1), previous["powers"], atol=1e-12)
            assert float(np.max(np.linalg.norm(velocity, axis=1))) <= cfg.max_speed
        for mode, ledger in ledgers.items():
            frame = ledger.consume(tick, G, result["quality"]["status"],
                                   case["frames"][max(0, index-1)]["powers"])
            reference = case["expected"][mode + "_ledger"]["frames"][index]
            assert frame["status"] == reference["status"]
            close(frame["progress"], reference["progress"])
            close(frame["occupied_robot_seconds"], reference["occupied_robot_seconds"])
            close(frame["prefix_effort_by_robot"], reference["prefix_effort_by_robot"])
            assert frame["occupied_robot_ids"] == reference["occupied_robots"]
            assert len(frame["occupied_robot_ids"]) + len(frame["idle_robot_ids"]) == cfg.robots
            output[mode].append(frame)
    summaries = {}
    for mode, ledger in ledgers.items():
        expected = case["expected"][mode + "_ledger"]
        assert ledger.status == expected["final_status"]
        assert ledger.completion_tick == expected["completion_tick"]
        assert ledger.completion_time == expected["completion_time"]
        assert len(ledger.releases) == expected["release_count"]
        interruptions = [e for e in ledger.events if e["type"] == "interruption"]
        assert len(interruptions) == expected["interrupt_count"]
        for actual, ref in zip(interruptions, expected["events"]):
            close(actual["time"], ref["time"])
            assert actual["reason"] == ref["reason"]
            close(actual["progress_before"], ref["progress_before"])
        close(ledger.control_effort, expected["effort"])
        close(ledger.occupied_robot_seconds, expected["occupied_robot_seconds"])
        if expected["completion_window_ticks"] is not None:
            assert ledger.completion_window_ticks == expected["completion_window_ticks"]
        summaries[mode] = dict(status=ledger.status, completion_time=ledger.completion_time,
                               completion_tick=ledger.completion_tick, progress=ledger.progress,
                               occupied_robot_seconds=ledger.occupied_robot_seconds,
                               prefix_control_effort=ledger.control_effort,
                               effort_by_robot=ledger.effort_by_robot,
                               events=ledger.events, releases=ledger.releases,
                               snapshot=ledger.snapshot())
    return dict(passed=True, case_id=case["case_id"], frames=output, errors=errors,
                ledgers=summaries, expected=case["expected"],
                scope="deterministic mechanism and accounting; no accuracy probability claim")


def audit_case(job, out):
    case = read(job["case_file"])
    sensed = read(job["sensing_file"])
    result = replay(case, sensed["rows"])
    if case["case_id"] == "C4":
        assert all(row["result"]["quality"]["status"] == "PASS" for row in sensed["rows"])
        assert any(row["result"]["quality"]["estimator_diagnostics"]["branch_guard_triggered"]
                   for row in sensed["rows"]), "Expected discarded-start branch probe not exercised"
    save_json(Path(out) / "audit.json", result)
    return result


def audit_probes(job, out):
    results = {}
    for item in job["inputs"]:
        case, sensed = read(item["case_file"]), read(item["sensing_file"])
        name = case["case_id"]
        rows = sensed["rows"]
        if name == "G_FALSE":
            results[name] = replay(case, rows)
        elif name in ("P1", "P2"):
            value = rows[0]["result"]
            audit = audit_quality(value, case["expected"]["endpoint_references"][0],
                                  case["frames"][0]["truth"])
            intersection = ray_intersection(value["payload"])
            assert intersection["usable_ray_intersection"]
            close(value["quality"]["estimate"], intersection["intersection"], atol=1e-6)
            assert truth_error(value["quality"]["estimate"], case["frames"][0]["truth"]) > 1e-4
            results[name] = dict(passed=True, audit=audit, ray=intersection)
        elif name == "D08":
            results[name] = dict(passed=True, audit=audit_quality(
                rows[0]["result"], case["expected"]["endpoint_references"][0],
                case["frames"][0]["truth"], degenerate=True))
        elif name == "D06":
            assert len(rows) == 2
            assert rows[0]["result"] == rows[1]["result"]
            # These private values are held only by the evaluation worker.
            hidden = case["expected"]["hidden_truth_variants"]
            assert hidden[0] != hidden[1]
            native = rows[0]["result"]
            audit_quality(native, case["expected"]["endpoint_references"][0],
                          case["frames"][0]["truth"])
            # Native result reused for explicit quality-layer fault injections.
            from .public_quality import FrameProcessor, assess_quality
            payload = native["payload"]
            injections = []
            base = native["estimate_result"]
            for flag in ("numerical_ill_conditioned", "ambiguity_detected", "boundary_active"):
                modified = copy.deepcopy(base)
                modified[flag] = True
                quality = assess_quality(payload, modified)
                assert quality["status"] == "UNKNOWN"
                injections.append(dict(flag=flag, quality=quality))
            no_solution = copy.deepcopy(base)
            no_solution.update(has_accepted_estimate=False, estimate=None)
            assert assess_quality(payload, no_solution)["status"] == "UNKNOWN"
            # D02 full adapter-to-clock check, using an explicitly fake estimator.
            full = read(job["c1_file"])
            calls = []
            def fake(data):
                calls.append(digest(data))
                return copy.deepcopy(base)
            processor = FrameProcessor(["U0", "U1"], fake)
            ledger = ShadowLedger(Config(**full["config"]), full["team"], .10)
            for index in (0, 1, 1, 2):
                frame = full["frames"][index]
                processed = processor.process(frame["public"])
                if not processed["duplicate"]:
                    ledger.consume(index, True, processed["quality"]["status"], frame["powers"])
            assert len(calls) == 3 and ledger.completion_tick == 2 and len(ledger.releases) == 1
            results[name] = dict(passed=True, identical_public_results=True,
                                 hidden_truth_not_sent=hidden, injections=injections,
                                 D02_adapter_clock=dict(fake_calls=len(calls), snapshot=ledger.snapshot()))
        else:
            raise AssertionError(name)
        save_json(Path(out) / f"{name}_audit.json", results[name])
    return dict(passed=True, probes=results, real_wls_calls_in_this_audit=0)
