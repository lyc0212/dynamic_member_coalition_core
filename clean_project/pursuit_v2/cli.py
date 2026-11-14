from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path

from .config import Config
from .runner import evaluate, run_episode
from .scenario import generate_scenario, load_scenario


def output_directory(path):
    directory = Path(path)
    if directory.exists() and any(directory.iterdir()):
        raise ValueError(f"Output directory is not empty: {directory}. Choose a new --out.")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def main(argv=None):
    parser = argparse.ArgumentParser(description="动态联盟追逃 v0.1 — independent classical benchmark")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="Run one episode and generate offline replay")
    source = run.add_mutually_exclusive_group()
    source.add_argument("--config")
    source.add_argument("--scenario", help="Replay an exported scenario with another policy")
    run.add_argument("--robots", type=int, choices=range(2, 17))
    run.add_argument("--task-count", type=int)
    run.add_argument("--seed", type=int, default=0)
    modes = ("quality_event", "fixed", "periodic", "event", "risk_periodic", "risk_event", "risk_local",
             )
    run.add_argument("--policy", choices=modes, default="quality_event")
    run.add_argument("--solver", choices=("exact", "greedy"), default="exact")
    capture_modes = ("fixed_check_legacy", "stepwise_instant")
    run.add_argument("--capture-mode", choices=capture_modes)
    run.add_argument("--no-replay", action="store_true")
    run.add_argument("--out", default=None)

    batch = commands.add_parser("evaluate", help="Paired multi-seed, multi-scale comparison")
    batch.add_argument("--config")
    batch.add_argument("--robots", type=int, nargs="+", choices=range(2, 17), default=[6])
    batch.add_argument("--episodes", type=int, default=10)
    batch.add_argument("--seed-start", type=int, default=0)
    batch.add_argument("--policies", nargs="+", choices=modes,
                       default=["fixed", "periodic", "event"])
    batch.add_argument("--solver", choices=("exact", "greedy"), default="exact")
    batch.add_argument("--capture-mode", choices=capture_modes)
    batch.add_argument("--replay-first", action="store_true")
    batch.add_argument("--out", default=None)
    args = parser.parse_args(argv)
    try:
        base = Config.load(args.config) if getattr(args, "config", None) else Config()
        if args.capture_mode is not None:
            base = replace(base, capture_mode=args.capture_mode)
        default_out = "runs/" + args.command + "_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        output = output_directory(args.out or default_out)
        if args.command == "run":
            if args.scenario:
                if args.robots is not None:
                    raise ValueError("--robots cannot override an exported scenario")
                cfg, scenario = load_scenario(args.scenario)
                if args.capture_mode is not None:
                    cfg = replace(cfg, capture_mode=args.capture_mode)
                seed = None
            else:
                cfg = (replace(base, robots=args.robots, task_count=None, side=None)
                       if args.robots is not None and args.robots != base.robots else base)
                scenario, seed = generate_scenario(cfg, args.seed), args.seed
            if args.task_count is not None:
                if args.scenario:
                    raise ValueError("--task-count cannot override an exported scenario")
                cfg = replace(cfg, task_count=args.task_count)
                scenario = generate_scenario(cfg, args.seed)
            metrics, _ = run_episode(cfg, scenario, args.policy, args.solver, output,
                                     trace=not args.no_replay, seed=seed)
            print(json.dumps(metrics, indent=2, ensure_ascii=False))
            if not args.no_replay:
                print(f"Replay: {(output / 'replay.html').resolve()}")
        else:
            if args.episodes < 1:
                raise ValueError("--episodes must be positive")
            if len(set(args.policies)) != len(args.policies) or len(set(args.robots)) != len(args.robots):
                raise ValueError("Duplicate policy or robot entries are not allowed")
            evaluate(base, args.robots, range(args.seed_start, args.seed_start + args.episodes),
                     args.policies, args.solver, output, args.replay_first)
            print(f"Summary: {(output / 'summary.md').resolve()}")
    except (ValueError, OSError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
