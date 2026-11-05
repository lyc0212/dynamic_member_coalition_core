"""Linux serial-worker accounting with an independent launcher fallback.

This is deliberately not an arbitrary process-tree accounting facility.
Scientific workers cannot create children; supervisor/launcher CPU is separate.
"""
import ctypes
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from .common import save_json

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "examples/validate_stage2a5b_a.py"
THREADS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")


def process_stat(pid):
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return dict(pid=pid, ppid=int(fields[1]), pgid=int(fields[2]),
                    start_ticks=int(fields[19]),
                    cpu=(int(fields[11]) + int(fields[12])) / os.sysconf("SC_CLK_TCK"))
    except (FileNotFoundError, ProcessLookupError):
        return None


def live_identity(row):
    actual = process_stat(row["pid"])
    return actual is not None and actual["start_ticks"] == row["start_ticks"]


def kill_registered(row):
    if live_identity(row):
        if row["pgid"] != row["pid"]:
            raise RuntimeError("Worker is not its own process-group leader")
        try:
            os.killpg(row["pid"], signal.SIGKILL)
        except ProcessLookupError:
            pass


def environment(folder):
    env = dict(os.environ)
    env.update({k: "1" for k in THREADS})
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0",
               PYTHONUTF8="1", TMPDIR=str(folder), TEMP=str(folder), TMP=str(folder))
    return env


def enable_subreaper():
    # Orphaned workers of a timed-out controller are reaped by this launcher.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), "Cannot enable launcher subreaper")


def reap(pid, deadline):
    while True:
        got, status, usage = os.wait4(pid, os.WNOHANG)
        if got:
            return dict(pid=pid, returncode=os.waitstatus_to_exitcode(status),
                        user_cpu=usage.ru_utime, system_cpu=usage.ru_stime,
                        cpu=usage.ru_utime + usage.ru_stime, reaped=True)
        if time.monotonic() >= deadline:
            raise RuntimeError(f"Failed to reap registered process {pid}")
        time.sleep(0.01)


def supervise(job_path, out, *, cpu_limit, wall_limit, cumulative, cpu_budget, deadline):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    work_deadline = deadline - 5.0  # reserve cleanup inside the shared wall budget
    cpu_limit = min(float(cpu_limit), cpu_budget - cumulative)
    wall_limit = min(float(wall_limit), work_deadline - time.monotonic())
    if cpu_limit <= 0 or wall_limit <= 0:
        raise RuntimeError("No remaining worker budget")
    command = [sys.executable, "-B", str(ENTRY), "worker", "--job", str(job_path),
               "--out", str(out), "--cpu-limit", str(max(1, math.ceil(cpu_limit)))]
    started = time.monotonic()
    samples, termination, monitor_error = [], None, None
    registry = out.parent / "active_worker.json"
    child, identity, collected = None, None, None
    with (out / "stdout_stderr.log").open("x", encoding="utf-8") as log:
        try:
            child = subprocess.Popen(command, cwd=ROOT, env=environment(out), stdout=log,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            identity = process_stat(child.pid)
            if identity is None:
                raise RuntimeError("Worker identity disappeared before registration")
            save_json(registry, dict(active=True, **identity, out=str(out), command=command))
            while True:
                got, status, usage = os.wait4(child.pid, os.WNOHANG)
                if got:
                    collected = dict(returncode=os.waitstatus_to_exitcode(status),
                                     user_cpu=usage.ru_utime, system_cpu=usage.ru_stime,
                                     cpu=usage.ru_utime + usage.ru_stime)
                    child.returncode = collected["returncode"]
                    break
                at = time.monotonic()
                live = process_stat(child.pid)
                cpu = None if live is None else live["cpu"]
                samples.append(dict(wall=at-started, cpu=cpu,
                                    cumulative_cpu=None if cpu is None else cumulative+cpu))
                if termination is None:
                    if at >= work_deadline:
                        termination = "total_wall_cleanup_reserve"
                    elif at-started >= wall_limit:
                        termination = "worker_wall"
                    elif cpu is not None and cumulative+cpu >= cpu_budget:
                        termination = "total_cpu"
                    elif cpu is not None and cpu >= cpu_limit:
                        termination = "worker_cpu"
                    try:
                        children = Path(f"/proc/{child.pid}/task/{child.pid}/children").read_text().split()
                    except FileNotFoundError:
                        children = []
                    if children:
                        termination = "unexpected_child"
                    if termination:
                        kill_registered(identity)
                time.sleep(0.05)
        except BaseException as exc:
            termination = termination or "supervision_exception"
            monitor_error = dict(type=type(exc).__name__, message=str(exc))
        finally:
            if child is not None and collected is None:
                if identity is None:
                    identity = process_stat(child.pid)
                if identity is not None:
                    kill_registered(identity)
                collected = reap(child.pid, deadline)
                child.returncode = collected["returncode"]
    if child is None or collected is None:
        raise RuntimeError(f"Worker creation failed: {monitor_error}")
    if termination is None and collected["returncode"] in (-signal.SIGXCPU, -signal.SIGKILL):
        termination = "kernel_cpu_or_signal"
    record = dict(command=command, **identity, returncode=collected["returncode"],
                  user_cpu=collected["user_cpu"], system_cpu=collected["system_cpu"],
                  process_lifecycle_cpu=collected["cpu"], cumulative_before=cumulative,
                  cumulative_after=cumulative+collected["cpu"], wall=time.monotonic()-started,
                  cpu_limit=cpu_limit, wall_limit=wall_limit, termination=termination,
                  monitor_error=monitor_error, samples=samples, reaped=True,
                  live_after_reap=live_identity(identity),
                  accounting="single worker incl startup/imports; not arbitrary process-tree CPU")
    save_json(out / "process.json", record)
    save_json(registry, dict(active=False, last_pid=child.pid))
    return record


def cleanup_adopted(deadline):
    records = []
    path = Path(f"/proc/{os.getpid()}/task/{os.getpid()}/children")
    for value in path.read_text().split():
        row = process_stat(int(value))
        if row is None:
            continue
        if row["pgid"] == row["pid"]:
            kill_registered(row)
        elif live_identity(row):
            try:
                os.kill(row["pid"], signal.SIGKILL)
            except ProcessLookupError:
                pass
        records.append(reap(row["pid"], deadline))
    return records


def external_watchdog_probe(attempt, overall_deadline):
    """Actually kill an unresponsive controller and recover its registered worker."""
    folder = Path(attempt) / "logs" / "external_watchdog"
    folder.mkdir(parents=True, exist_ok=False)
    command = [sys.executable, "-B", str(ENTRY), "hang-controller", "--out", str(folder)]
    with (folder / "controller.log").open("x", encoding="utf-8") as log:
        controller = subprocess.Popen(command, cwd=ROOT, env=environment(folder),
                                      stdout=log, stderr=subprocess.STDOUT,
                                      start_new_session=True)
        identity = process_stat(controller.pid)
        registry = folder / "active_worker.json"
        ready_deadline = min(overall_deadline, time.monotonic() + 5)
        while not registry.exists():
            if time.monotonic() >= ready_deadline:
                kill_registered(identity)
                reap(controller.pid, overall_deadline)
                cleanup_adopted(overall_deadline)
                raise RuntimeError("External watchdog probe did not register worker")
            time.sleep(0.01)
        worker = json.loads(registry.read_text())
        until = min(overall_deadline, time.monotonic() + 0.5)
        while time.monotonic() < until:
            time.sleep(0.01)
        kill_registered(identity)
        controller_record = reap(controller.pid, overall_deadline)
        controller.returncode = controller_record["returncode"]
        kill_registered(worker)
        worker_record = reap(worker["pid"], overall_deadline)
    passed = (controller_record["returncode"] == -signal.SIGKILL
              and worker_record["returncode"] == -signal.SIGKILL
              and not live_identity(identity) and not live_identity(worker))
    result = dict(passed=passed, expected="external_timeout", controller=controller_record,
                  worker=worker_record, worker_identity=worker,
                  worker_cpu=worker_record["cpu"], survivors=False)
    save_json(folder / "result.json", result)
    if not passed:
        raise RuntimeError("External watchdog cleanup failed")
    return result


def launch_controller(attempt, deadline, starting_cpu):
    folder = Path(attempt)
    command = [sys.executable, "-B", str(ENTRY), "controller", "--attempt", str(folder),
               "--deadline", str(deadline), "--starting-cpu", str(starting_cpu)]
    with (folder / "logs/controller.log").open("x", encoding="utf-8") as log:
        child = subprocess.Popen(command, cwd=ROOT, env=environment(folder),
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        identity = process_stat(child.pid)
        timed_out = False
        while True:
            got, status, usage = os.wait4(child.pid, os.WNOHANG)
            if got:
                child.returncode = os.waitstatus_to_exitcode(status)
                break
            if time.monotonic() >= deadline - 3.0:
                timed_out = True
                kill_registered(identity)
            time.sleep(0.05)
    orphans = []
    # The controller might die before unregistering its current worker.
    registry = folder / "logs/active_worker.json"
    if registry.exists():
        registered = json.loads(registry.read_text())
        if registered.get("active") and live_identity(registered):
            kill_registered(registered)
    orphans = cleanup_adopted(deadline)
    result = dict(command=command, returncode=child.returncode, timed_out=timed_out,
                  orphan_records=orphans, controller_reaped=True,
                  controller_wait4_cpu_including_any_reaped_descendants=usage.ru_utime + usage.ru_stime,
                  note="controller own CPU is reported separately by controller process_time")
    save_json(folder / "logs/launcher_controller.json", result)
    return result
