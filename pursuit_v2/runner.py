from __future__ import annotations

from pursuit_v2.service import reject_service

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import time
import numpy as np

from .config import Config
from .environment import Environment, TimedEnvironment
from .policies import Policy
from .scenario import generate_scenario, save_scenario, scenario_hash
from .io import clean_json, dump_json, write_csv
from .physics import rollout_target
from .risk import risk_horizon
from .types import role_offset
from .timing import measured_decision


def run_episode(cfg, scenario, mode="event", solver="exact", output=None, trace=False, seed=None):
    reject_service(cfg)
    env = (TimedEnvironment(cfg, scenario) if cfg.turn_max_angle > 0 or
           cfg.speed_delta_max > 0 or cfg.motion_model == "continuous_turn"
           else Environment(cfg, scenario))
    if mode == "quality_event":
        from research.quality_allocation.policy import QualityEventPolicy
        policy = QualityEventPolicy(mode)
    else:
        policy = Policy(mode, solver)
    stages, frames, decisions, forecast_records = [], [], [], []
    wall_start = time.perf_counter()
    while not env.done:
        observation, decision, cpu = measured_decision(env, policy)
        decision.log.update(cpu)
        selected = decision.log.get("selected", [])
        if selected:
            estimates = [(row["target"], row["robots"], row["roles"],
                          row.get("on_time_probability")) for row in selected]
        else:
            estimates = [(row["target"],
                          tuple(k for k, a in enumerate(observation.assignment)
                                if a.target == row["target"]),
                          tuple(a.role for a in observation.assignment
                                if a.target == row["target"]),
                          row["estimate"]["on_time_probability"])
                         for row in decision.log.get("incumbent_risks", []) if row.get("estimate")]
        visible = {t.id: t for t in observation.targets}
        for target_id, robots, roles, probability in estimates:
            if probability is None:
                continue
            target = visible[target_id]
            forecast_records.append((target_id, tuple(robots), tuple(roles),
                                     float(probability), observation.time,
                                     risk_horizon(observation, target),
                                     observation.positions[list(robots)].copy(),
                                     np.array([role_offset(role, cfg) for role in roles])))
        result = env.step(decision.assignment, trace=trace)
        details = result.info
        new_frames = details.pop("frames", [])
        if new_frames:
            if frames and frames[-1]["time"] == new_frames[0]["time"]:
                frames.pop()
            frames.extend(new_frames)
        details["decision"] = decision.log
        stages.append(details)
        decisions.append(decision.log)
    metrics = env.metrics()
    double_ids = [t.id for t in scenario.targets if t.required_robots == 2]
    metrics["double_robot_completion_rate"] = (float(np.mean(np.isfinite(env.capture_times[double_ids])))
                                                 if double_ids else 0.0)
    audit_start = time.perf_counter()
    audit = []
    for target_id, robots, roles, probability, at, horizon, positions, offsets in forecast_records:
        result = rollout_target(cfg, scenario.targets[target_id], positions[None], offsets[None],
                                np.ones(1, dtype=bool), at, horizon)
        observed_success = bool(np.isfinite(result.capture_times[0]) and
                                result.capture_times[0] <= scenario.targets[target_id].deadline + 1e-10)
        audit.append({"target": target_id, "time": at, "robots": robots, "roles": roles,
                      "horizon": horizon, "deadline": scenario.targets[target_id].deadline,
                      "predicted_probability": probability,
                      "observed_on_time": int(observed_success),
                      "frozen_capture_time": (float(result.capture_times[0])
                                              if np.isfinite(result.capture_times[0]) else None),
                      "frozen_escape_time": (float(result.escape_times[0])
                                             if np.isfinite(result.escape_times[0]) else None),
                      "squared_error": (probability - observed_success) ** 2})
    metrics["forecast_audit_seconds"] = time.perf_counter() - audit_start
    metrics["risk_forecasts"] = len(audit)
    metrics["risk_brier"] = (float(np.mean([row["squared_error"] for row in audit]))
                             if audit else None)
    metrics["risk_false_positive_count"] = sum(
        row["predicted_probability"] >= cfg.risk_threshold and not row["observed_on_time"]
        for row in audit)
    metrics["local_repairs"] = sum("repair_scope" in row for row in decisions)
    metrics["global_fallbacks"] = sum(row.get("fallback_global", False) for row in decisions)
    metrics["certified_incumbent_checks"] = sum(
        report.get("certified", False) for row in decisions
        for report in row.get("incumbent_risks", []))
    latencies = np.array([d["decision_seconds"] for d in decisions])
    metrics.update({
        "policy": mode, "solver": "exact_dyadic" if mode == "quality_event" else solver, "seed": seed, "robots": cfg.robots,
        "task_count": cfg.task_count, "scenario_sha256": scenario_hash(scenario),
        "replans": sum(d["replanned"] for d in decisions),
        "candidate_evaluations": sum(d["candidate_count"] for d in decisions),
        "decision_seconds": float(latencies.sum()),
        "decision_mean_seconds": float(latencies.mean()),
        "decision_p95_seconds": float(np.percentile(latencies, 95)),
        "decision_max_seconds": float(latencies.max()),
        "prediction_seconds": (None if any(d["prediction_seconds"] is None for d in decisions) else sum(d["prediction_seconds"] for d in decisions)),
        "solver_seconds": (None if any(d["solver_seconds"] is None for d in decisions) else sum(d["solver_seconds"] for d in decisions)),
        "trigger_seconds": sum(d["trigger_seconds"] for d in decisions),
        "online_cpu_seconds": sum(d["online_cpu_seconds"] for d in decisions),
        "online_observation_cpu_seconds": sum(d["online_observation_cpu_seconds"] for d in decisions),
        "online_policy_cpu_seconds": sum(d["online_policy_cpu_seconds"] for d in decisions),
        "episode_wall_seconds": time.perf_counter() - wall_start,
    })
    if metrics["peak_speed"] > cfg.max_speed + 1e-7 or metrics["model_mismatches"]:
        raise RuntimeError("Execution violated the speed guard; inspect physics before using results")
    outcomes = [{"target": t.id, "status": env.status[t.id],
                 "capture_time": env.capture_times[t.id], "escape_time": env.escape_times[t.id]}
                for t in scenario.targets]
    record = clean_json({"config": cfg.to_dict(), "scenario": scenario.to_dict(),
                         "metrics": metrics, "outcomes": outcomes, "stages": stages,
                         "forecast_audit": audit, "frames": frames})
    if output is not None:
        directory = Path(output)
        directory.mkdir(parents=True, exist_ok=True)
        save_scenario(directory / "scenario.json", cfg, scenario)
        dump_json(directory / "metrics.json", metrics)
        dump_json(directory / "outcomes.json", outcomes)
        with (directory / "stages.jsonl").open("w", encoding="utf-8") as stream:
            for stage in stages:
                stream.write(json.dumps(clean_json(stage), ensure_ascii=False, allow_nan=False) + "\n")
        write_csv(directory / "stages.csv", stages)
        write_csv(directory / "forecast_audit.csv", audit)
        if trace:
            from .replay import write_replay
            dump_json(directory / "replay.json", record)
            write_replay(directory / "replay.html", record)
    return metrics, record


def evaluate(base: Config, robot_counts, seeds, policies, solver, output, replay_first=False):
    directory = Path(output)
    directory.mkdir(parents=True, exist_ok=True)
    rows, all_forecasts = [], []
    seeds = list(seeds)
    for robots in robot_counts:
        cfg = (base if robots == base.robots else
               replace(base, robots=robots, task_count=None, side=None))
        for seed in seeds:
            scenario = generate_scenario(cfg, seed)
            expected_hash = scenario_hash(scenario)
            for mode in policies:
                path = directory / f"C{robots}" / f"seed_{seed}" / mode
                metrics, record = run_episode(cfg, scenario, mode, solver, path,
                                              trace=replay_first and seed == seeds[0], seed=seed)
                assert metrics["scenario_sha256"] == expected_hash
                rows.append(metrics)
                all_forecasts.extend({"robot_count": robots, "seed": seed, "policy": mode,
                                      "scenario_sha256": expected_hash, **audit}
                                     for audit in record["forecast_audit"])
                print(f"C={robots:2d} seed={seed:4d} {mode:8s} "
                      f"capture={metrics['completion_rate']:.3f} "
                      f"on_time={metrics['weighted_on_time_rate']:.3f} "
                      f"replans={metrics['replans']:2d}", flush=True)
    write_csv(directory / "episodes.csv", rows)
    write_csv(directory / "forecast_audit.csv", all_forecasts)
    calibration = []
    for policy_name in policies:
        group = [row for row in all_forecasts if row["policy"] == policy_name]
        if not group:
            continue
        for probability in sorted({row["predicted_probability"] for row in group}):
            bucket = [row for row in group if row["predicted_probability"] == probability]
            observed = float(np.mean([row["observed_on_time"] for row in bucket]))
            calibration.append({"policy": policy_name, "predicted_probability": probability,
                                "forecasts": len(bucket), "observed_on_time_rate": observed,
                                "calibration_gap": observed - probability,
                                "brier": float(np.mean([row["squared_error"] for row in bucket]))})
    write_csv(directory / "calibration.csv", calibration)
    calibration_summary = []
    for policy_name in policies:
        group = [row for row in all_forecasts if row["policy"] == policy_name]
        if not group:
            continue
        bins = [row for row in calibration if row["policy"] == policy_name]
        confident = [row for row in group if row["predicted_probability"] >= base.risk_threshold]
        calibration_summary.append({
            "policy": policy_name, "forecasts": len(group),
            "brier": float(np.mean([row["squared_error"] for row in group])),
            "expected_calibration_error": sum(
                row["forecasts"] * abs(row["calibration_gap"]) for row in bins) / len(group),
            "high_probability_forecasts": len(confident),
            "high_probability_failures": sum(not row["observed_on_time"] for row in confident),
        })
    write_csv(directory / "calibration_summary.csv", calibration_summary)
    fields = ["return", "return_with_changes", "completion_rate", "weighted_on_time_rate",
              "double_robot_completion_rate", "risk_false_positive_count",
              "escaped_weight_fraction", "replans", "assignment_changes", "decision_seconds",
              "decision_p95_seconds", "partner_wait_robot_seconds", "control_effort",
              "candidate_evaluations"]
    summary = []
    for robots in robot_counts:
        for mode in policies:
            group = [r for r in rows if r["robots"] == robots and r["policy"] == mode]
            row = {"robots": robots, "policy": mode, "episodes": len(group), "solver": solver}
            for field in fields:
                values = np.array([r[field] for r in group])
                row[field + "_mean"] = float(values.mean())
                row[field + "_std"] = float(values.std(ddof=1)) if len(values) > 1 else 0.0
            summary.append(row)
    write_csv(directory / "summary.csv", summary)
    paired = []
    intervals = []
    lookup = {(r["robots"], r["seed"], r["policy"]): r for r in rows}
    for row in rows:
        references = []
        if "periodic" in policies and row["policy"] != "periodic":
            references.append("periodic")
        if ("risk_periodic" in policies and row["policy"] in ("risk_event", "risk_local")):
            references.append("risk_periodic")
        for reference_mode in references:
            reference = lookup[(row["robots"], row["seed"], reference_mode)]
            paired.append({"robots": row["robots"], "seed": row["seed"],
                           "policy": row["policy"], "reference": reference_mode,
                           "comparison": row["policy"] + "_minus_" + reference_mode,
                           **{field: row[field] - reference[field] for field in fields}})
    write_csv(directory / "paired_deltas.csv", paired)
    comparisons = sorted({(r["robots"], r["policy"], r["reference"]) for r in paired})
    for robots, policy_name, reference_name in comparisons:
        group = [r for r in paired if r["robots"] == robots and
                 r["policy"] == policy_name and r["reference"] == reference_name]
        n = len(group)
        # A stable seed makes the interval file reproducible. Intervals are descriptive,
        # not a substitute for an adequately powered, frozen confirmatory experiment.
        seed_value = 20261004 + robots + sum(map(ord, policy_name + reference_name))
        rng = np.random.default_rng(seed_value)
        draws = rng.integers(0, n, size=(2000, n))
        for field in fields:
            values = np.array([r[field] for r in group], dtype=float)
            sampled = values[draws].mean(axis=1)
            low, high = np.percentile(sampled, [2.5, 97.5])
            intervals.append({"robots": robots, "policy": policy_name,
                              "reference": reference_name,
                              "comparison": policy_name + "_minus_" + reference_name,
                              "metric": field, "episodes": n,
                              "mean_delta": float(values.mean()),
                              "ci_low": float(low), "ci_high": float(high),
                              "bootstrap_resamples": 2000, "bootstrap_seed": seed_value})
    write_csv(directory / "paired_intervals.csv", intervals)
    dump_json(directory / "manifest.json", {
        "created_utc": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
        "numpy": np.__version__, "base_config": base.to_dict(), "robots": list(robot_counts),
        "seeds": seeds, "policies": list(policies), "solver": solver,
        "note": "Paired external scenarios; separate closed-loop state per policy. No parameter tuning.",
    })
    lines = ["# 评测结果", "", "各策略使用同一个外生场景，分别闭环推进。以下为均值；样本标准差见 summary.csv。",
             "小样本只用于运行验证，不能据此认定方法优劣。", "",
             "| 簇数 | 策略 | 回合数 | 捕获率 | 加权按时率 | 重规划次数 | 改派次数 | 决策总秒数 |",
             "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for row in summary:
        lines.append(f"| {row['robots']} | {row['policy']} | {row['episodes']} | "
                     f"{row['completion_rate_mean']:.3f} | {row['weighted_on_time_rate_mean']:.3f} | "
                     f"{row['replans_mean']:.2f} | {row['assignment_changes_mean']:.2f} | "
                     f"{row['decision_seconds_mean']:.3f} |")
    (directory / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rows, summary
