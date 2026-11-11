"""D2-B native preparation; separate explicit native authorization required."""
import argparse
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import sys
import time

REPO = Path(r'D:\1st\dynamic_member_coalition_core')
PARAMETERS = {'B1': (.10, 2., 1.5), 'B2': (3., .5, 2.), 'B3': (3., .5, 2.)}


def write_new(path, record):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(record, f, ensure_ascii=False, allow_nan=False, indent=2)
        f.flush()
        os.fsync(f.fileno())


def identity(api, handle, pid, job):
    k = api.k
    k.GetProcessTimes.argtypes = [W.HANDLE] + [C.POINTER(W.FILETIME)] * 4
    k.GetProcessTimes.restype = W.BOOL
    k.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD)]
    k.QueryFullProcessImageNameW.restype = W.BOOL
    times = [W.FILETIME() for _ in range(4)]
    api.check(k.GetProcessTimes(handle, *(C.byref(t) for t in times)), 'GetProcessTimes')
    image, length = C.create_unicode_buffer(32768), W.DWORD(32768)
    api.check(k.QueryFullProcessImageNameW(handle, 0, image, C.byref(length)), 'QueryFullProcessImageNameW')
    return dict(pid=pid, creation_ticks=(times[0].dwHighDateTime << 32) | times[0].dwLowDateTime,
                image=image.value, member=api.member(handle, job),
                wait_status=int(k.WaitForSingleObject(handle, 0)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--scenario', choices=PARAMETERS, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--native-authorized', action='store_true')
    args = p.parse_args()
    if not args.native_authorized or os.name != 'nt':
        raise RuntimeError('SEPARATE_NATIVE_AUTHORIZATION_REQUIRED')
    sys.path.insert(0, str(REPO))
    from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor
    cpu, wall, lifetime = PARAMETERS[args.scenario]
    root = args.output
    child_file = root / 'child_pid.txt'
    busy = "import time\nend=time.monotonic()+1.5\nwhile time.monotonic()<end: pass\n"
    sleeper = 'import time; time.sleep(2.0)'
    family = ('import subprocess,sys,time\nend=time.monotonic()+2.0\n'
              'child=subprocess.Popen([sys.executable,"-B","-c",' + repr(sleeper) + '],creationflags=0x08000000)\n'
              'with open(' + repr(str(child_file)) + ',"x") as f: f.write(str(child.pid))\n'
              'time.sleep(max(0.0,end-time.monotonic()))\n')
    s = WindowsSupervisor(wall_seconds=wall, total_cpu_seconds=cpu,
                          attempt_identity='D2B_' + args.scenario)
    observed, retained = [], []
    original_accounting, original_create = s.api.accounting, s.api.create
    worker_pid = [None]
    def create(*a, **kw):
        pi = original_create(*a, **kw)
        worker_pid[0] = int(pi.dwProcessId)
        observed.append(dict(kind='WORKER_CONTAINED_SUSPENDED',
                             identity=identity(s.api, pi.hProcess, worker_pid[0], s.job)))
        return pi
    s.api.create = create
    def accounting(job):
        value = original_accounting(job)
        if args.scenario in ('B2', 'B3') and child_file.exists() and not retained:
            try:
                pid = int(child_file.read_text())
            except (ValueError, OSError):
                return value  # An incomplete publication never counts as proof.
            h = s.api.k.OpenProcess(0x100000 | 0x1000, False, pid)
            s.api.check(h, 'OpenProcess/DESCENDANT')
            retained.append(h)
            record = identity(s.api, h, pid, job)
            observed.append(dict(kind='DESCENDANT_BEFORE_STOP', identity=record,
                                 wall_elapsed=s._elapsed()))
            if not record['member'] or record['wait_status'] != 258 or pid == worker_pid[0]:
                raise RuntimeError('DESCENDANT_NOT_LIVE_AND_CONTAINED')
        return value
    s.api.accounting = accounting
    if args.scenario == 'B3':
        def injected_terminate(job):
            raise OSError('D2B_INSTANCE_ONLY_INJECTED_TERMINATION_FAILURE')
        s.api.terminate = injected_terminate
    receipt, error = None, None
    try:
        receipt = s.run_monitored([sys.executable, '-B', '-c', busy if args.scenario == 'B1' else family],
                                  cwd=REPO, log=root / 'worker.log')
    except BaseException as exc:
        error = dict(type=type(exc).__name__, message=str(exc))
        receipt = s.result
    finally:
        s.close()
        child_exits = []
        for h in retained:
            child_exits.append(int(s.api.k.WaitForSingleObject(h, 100)))
            s.api.close(h)
    common = error is None and receipt is not None
    if args.scenario == 'B1':
        ok = (common and receipt['stop_reason'] == 'CPU_LIMIT_REACHED'
              and receipt['termination_result'] == 'SUCCEEDED'
              and receipt['final_cpu_ticks'] is not None
              and receipt['final_cpu_ticks'] >= 1_000_000
              and receipt['accounting_status'] == 'FINAL_VALID'
              and receipt['job_cleanup_status'] == 'PASS'
              and receipt['evidence_completeness_status'] == 'COMPLETE_IN_MEMORY')
    else:
        proof = [r for r in observed if r['kind'] == 'DESCENDANT_BEFORE_STOP']
        ok = common and bool(proof) and child_exits == [0]
        if args.scenario == 'B2':
            ok = (ok and receipt['stop_reason'] == 'WALL_LIMIT_REACHED'
                  and receipt['job_cleanup_status'] == 'PASS'
                  and receipt['final_cpu_ticks'] is not None
                  and receipt['evidence_completeness_status'] == 'COMPLETE_IN_MEMORY')
        else:
            ok = (ok and receipt['termination_result'] == 'FAILED'
                  and receipt['fallback_close_result'] == 'SUCCEEDED_TREE_EXIT_UNVERIFIED'
                  and receipt['final_cpu_ticks'] is None
                  and receipt['cpu_overshoot_ticks'] is None
                  and receipt['job_cleanup_status'] == 'FAIL')
    write_new(root / 'driver_evidence.json', dict(scenario=args.scenario,
              candidate_valid=bool(ok), final_status='PENDING_INDEPENDENT_OUTER_CLEANUP',
              parameters=dict(cpu=cpu, wall=wall, worker_lifetime=lifetime),
              receipt=receipt, processes=observed, descendant_wait_results=child_exits, error=error))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
