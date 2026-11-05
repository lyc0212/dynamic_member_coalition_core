"""Bounded, one-process job dispatcher; no science imports before limits."""
import copy
import importlib.metadata
import json
import math
import os
from pathlib import Path
import resource
import subprocess
import sys
import time
import traceback
import unittest

from .common import save_json, sha_file

ROOT = Path(__file__).resolve().parents[2]


def guards(*, sense_only=False):
    def hook(event, args):
        if event in ("subprocess.Popen", "os.fork", "os.forkpty", "os.posix_spawn", "os.posix_spawnp"):
            raise RuntimeError("Worker subprocess creation prohibited")
        if event == "import" and sense_only:
            name = args[0]
            if name.startswith("pursuit_v2") or name in (
                    "research.cooperative_sensing.fixtures", "research.information_service.fixtures"):
                raise RuntimeError("Private import prohibited in public sensing worker")
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            path = os.fsdecode(args[0]).replace("\\", "/")
            parts = path.lower().split("/")
            if any(p in ("archive", "archieve", "dynamic_coalition_pursuit_core") for p in parts):
                raise RuntimeError("Old/external dependency prohibited")
            if sense_only and "/inputs/" in path and not path.endswith(".public.json"):
                raise RuntimeError("Sensing worker may only read public input files")
    sys.addaudithook(hook)


def json_safe(x):
    if isinstance(x, dict):
        return {str(k): json_safe(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [json_safe(v) for v in x]
    if hasattr(x, "tolist"):
        return json_safe(x.tolist())
    if isinstance(x, float) and not math.isfinite(x):
        return {"nonfinite": repr(x)}
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    return {"type": type(x).__name__, "repr": repr(x)}


def instrument_estimator(out):
    """Save every entry and returned start record, including expected test failures."""
    from research.cooperative_sensing import estimator as module
    native = module.least_squares
    original = module.estimate
    counts = dict(entries=0, real_estimates=0, native_start_attempts=0,
                  mocked_estimates=0, pre_solver_rejections=0)

    def counted_solver(*args, **kwargs):
        counts["native_start_attempts"] += 1
        return native(*args, **kwargs)

    module.least_squares = counted_solver

    def estimate(data):
        counts["entries"] += 1
        number = counts["entries"]
        before = counts["native_start_attempts"]
        mocked = module.least_squares is not counted_solver
        entry = dict(entry=number, input=json_safe(copy.deepcopy(data)),
                     solver_mocked=mocked)
        save_json(Path(out) / "estimates" / f"{number:04d}_started.json", entry)
        try:
            result = original(data)
            entry["result"] = json_safe(result)
            return result
        except BaseException as exc:
            entry["exception"] = dict(type=type(exc).__name__, message=str(exc))
            raise
        finally:
            attempts = counts["native_start_attempts"] - before
            entry["native_start_attempts"] = attempts
            if attempts:
                counts["real_estimates"] += 1
            elif mocked:
                counts["mocked_estimates"] += 1
            else:
                counts["pre_solver_rejections"] += 1
            save_json(Path(out) / "estimates" / f"{number:04d}_finished.json", entry)
            save_json(Path(out) / "estimate_counts.json", counts)
    module.estimate = estimate
    return counts


def run_job(job_path, out, cpu_limit):
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit + 1))
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    out = Path(out)
    job = json.loads(Path(job_path).read_text())
    kind = job["kind"]
    guards(sense_only=kind == "sense")
    started = time.process_time()
    environment = dict(python=sys.version, executable=sys.executable,
                       executable_sha256=sha_file(sys.executable),
                       pid=os.getpid(), pgid=os.getpgrp(), ppid=os.getppid(),
                       limits=dict(cpu=resource.getrlimit(resource.RLIMIT_CPU),
                                   address_space=resource.getrlimit(resource.RLIMIT_AS)),
                       threads={k: os.environ.get(k) for k in (
                           "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")},
                       job_sha256=sha_file(job_path))
    save_json(out / "worker_environment.json", environment)
    counts = None
    try:
        if kind == "environment":
            import numpy as np
            import scipy
            from scipy.optimize import least_squares
            expected = {"numpy": "2.3.5", "scipy": "1.16.3"}
            actual = {"numpy": np.__version__, "scipy": scipy.__version__}
            if actual != expected:
                raise RuntimeError(f"Frozen dependency versions differ: {actual}")
            result = dict(passed=True, versions=actual, numpy_file=np.__file__,
                          scipy_file=scipy.__file__,
                          module_file_sha256={np.__file__: sha_file(np.__file__),
                                              scipy.__file__: sha_file(scipy.__file__)},
                          least_squares_module=least_squares.__module__)
        elif kind == "cpu_probe":
            while True:
                pass
        elif kind in ("wall_probe", "hang_sleep"):
            time.sleep(2 if kind == "wall_probe" else 30)
            result = dict(passed=False, unexpected="sleep finished before watchdog")
        elif kind == "child_probe":
            try:
                subprocess.run([sys.executable, "-c", "pass"], check=True)
            except RuntimeError as exc:
                result = dict(passed=True, child_denied=True, message=str(exc))
            else:
                raise AssertionError("Child creation was not denied")
        elif kind == "nonzero_probe":
            raise RuntimeError("EXPECTED_NONZERO_PROBE")
        elif kind == "unittest":
            if job.get("instrument"):
                counts = instrument_estimator(out)
            sys.path.insert(0, str(ROOT / "tests"))
            suite = unittest.TestSuite()
            loader = unittest.TestLoader()
            for name in job["modules"]:
                suite.addTests(loader.loadTestsFromName(name))
            tested = unittest.TextTestRunner(stream=sys.stdout, verbosity=2).run(suite)
            result = dict(passed=tested.wasSuccessful(), tests=tested.testsRun,
                          failures=len(tested.failures), errors=len(tested.errors),
                          skipped=len(tested.skipped))
        elif kind == "sense":
            counts = instrument_estimator(out)
            from .sensing_runner import run_public_file
            pieces = {}
            for entry in job["inputs"]:
                dest = out / entry["case_id"]
                pieces[entry["case_id"]] = run_public_file(entry["file"], dest,
                                                          repeats=entry.get("repeats", 1))
            result = dict(passed=True, pieces=pieces)
        elif kind in ("audit_probes", "audit_case"):
            from .acceptance import audit_probes, audit_case
            result = (audit_probes(job, out) if kind == "audit_probes" else audit_case(job, out))
        else:
            raise ValueError(f"Unknown frozen job {kind}")
        result["worker_body_cpu"] = time.process_time() - started
        if counts is not None:
            result["estimate_counts"] = counts
        save_json(out / "result.json", result)
        return 0 if result.get("passed") else 1
    except BaseException as exc:
        save_json(out / "failure.json",
                  dict(type=type(exc).__name__, message=str(exc),
                       traceback=traceback.format_exc(),
                       worker_body_cpu=time.process_time() - started,
                       estimate_counts=counts))
        traceback.print_exc()
        return 7 if kind == "nonzero_probe" else 1
