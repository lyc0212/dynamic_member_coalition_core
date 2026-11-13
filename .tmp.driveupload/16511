"""Independent six-second outer Job guard; preparation never runs this file."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

REPO = Path(r'D:\1st\dynamic_member_coalition_core')
HEAD = '72fda26ffe1a1049a4de30bda52586587106e387'
PYTHON = r'D:\anaconda3\python.exe'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', choices=['B1', 'B2', 'B3'], required=True)
    parser.add_argument('--native-authorized-once', action='store_true')
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    if not args.native_authorized_once:
        raise RuntimeError('NEW_EXPLICIT_NATIVE_AUTHORIZATION_REQUIRED')
    if (base / 'HALT').exists():
        raise RuntimeError('PREVIOUS_SCENARIO_FAILED_NO_CONTINUATION')
    manifest = json.loads((base / 'DRIVER_MANIFEST.json').read_text(encoding='utf-8-sig'))
    for filename, digest in manifest['code_sha256'].items():
        if hashlib.sha256((base / filename).read_bytes()).hexdigest().upper() != digest:
            raise RuntimeError('FROZEN_DRIVER_DRIFT')
    def git(*args):
        return subprocess.check_output(['git', *args], cwd=REPO, text=True).strip()
    if git('rev-parse', 'HEAD') != HEAD or git('branch', '--show-current') != 'main' or git('status', '--porcelain', '--untracked-files=all'):
        raise RuntimeError('SOURCE_PREFLIGHT_REJECTED')
    if args.scenario != 'B1':
        previous = 'B1' if args.scenario == 'B2' else 'B2'
        prior = json.loads((base / ('native_' + previous) / 'outer_receipt.json').read_text())
        if prior['status'] != previous + '_NATIVE_VALIDATED':
            raise RuntimeError('PRIOR_SCENARIO_NOT_VALIDATED')
    out = base / ('native_' + args.scenario)
    out.mkdir(exist_ok=False)  # Per-scenario single attempt, never overwrite.
    sys.path.insert(0, str(REPO))
    from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API
    from m3_d2b_native_driver import identity, write_new
    api, job, pi = API(), None, None
    retained, records, errors = {}, [], []
    timed_out, exit_code, final = False, None, None
    start = time.monotonic()
    job_state = dict(state='JOB_HANDLE_NOT_CREATED', diagnostic_handle=None,
                     first_termination_error=None, fallback_close_attempted=False,
                     fallback_close_result=None, fallback_close_error=None)
    worker_wait = None

    def close_job(*, fallback=False):
        nonlocal final
        if job_state['state'] != 'JOB_HANDLE_OPEN':
            return
        job_state['state'] = 'JOB_HANDLE_CLOSE_ATTEMPTED'
        if fallback:
            job_state['fallback_close_attempted'] = True
            final = None  # Stale accounting is not a final post-cleanup result.
        try:
            api.close(job)
        except BaseException as exc:
            job_state['state'] = 'JOB_HANDLE_CLOSE_FAILED_OR_UNCERTAIN'
            error = dict(type=type(exc).__name__, message=str(exc))
            errors.append(dict(stage='OUTER_FALLBACK_CLOSE' if fallback else 'OUTER_JOB_CLOSE', **error))
            if fallback:
                job_state['fallback_close_result'] = 'FAILED_OR_UNCERTAIN'
                job_state['fallback_close_error'] = error
        else:
            job_state['state'] = 'JOB_HANDLE_CLOSED'
            if fallback:
                job_state['fallback_close_result'] = 'SUCCEEDED_TREE_EXIT_UNVERIFIED'

    def terminate_job(stage):
        if job_state['state'] != 'JOB_HANDLE_OPEN':
            return False
        try:
            api.terminate(job)
        except BaseException as exc:
            error = dict(type=type(exc).__name__, message=str(exc))
            if job_state['first_termination_error'] is None:
                job_state['first_termination_error'] = error
            errors.append(dict(stage=stage, **error))
            close_job(fallback=True)  # Immediate: no query, wait, IO or retry.
            return False
        return True

    try:
        job = api.job(None)
        job_state.update(state='JOB_HANDLE_OPEN', diagnostic_handle=int(job))
        pi = api.create(job, [PYTHON, '-B', str(base / 'm3_d2b_native_driver.py'),
                       '--scenario', args.scenario, '--output', str(out), '--native-authorized'],
                       REPO, dict(os.environ, PYTHONDONTWRITEBYTECODE='1'), out / 'driver.log')
        if not api.member(pi.hProcess, job):
            raise RuntimeError('OUTER_CONTAINMENT_FAILED')
        records.append(identity(api, pi.hProcess, int(pi.dwProcessId), job))
        api.resume(pi.hThread)
        while True:
            if time.monotonic() - start >= 6.:
                timed_out = True
                terminate_job('OUTER_TIMEOUT_TERMINATE')
                break
            accounting = api.accounting(job)
            if accounting['ActiveProcesses'] == 0:
                break
            for pid in api.pids(job):
                if pid in retained:
                    continue
                h = api.k.OpenProcess(0x100000 | 0x1000 | 1, False, pid)
                api.check(h, 'OpenProcess/OUTER_RETAIN')
                try:
                    rec = identity(api, h, pid, job)
                    if not rec['member']:
                        raise RuntimeError('IDENTITY_MEMBERSHIP_REJECTED')
                except BaseException:
                    api.close(h)
                    raise
                retained[pid] = h
                records.append(rec)
            time.sleep(.01)
    except BaseException as exc:
        errors.append(dict(stage='OUTER_SUPERVISION', type=type(exc).__name__, message=str(exc)))
        terminate_job('OUTER_EXCEPTION_TERMINATE')
    finally:
        if job_state['state'] == 'JOB_HANDLE_OPEN':
            deadline = time.monotonic() + 1.
            try:
                while time.monotonic() < deadline:
                    final = api.accounting(job)
                    if final['ActiveProcesses'] == 0:
                        break
                    time.sleep(.01)
                if final is None or final['ActiveProcesses'] != 0:
                    terminate_job('OUTER_FINAL_CLEANUP_TERMINATE')
            except BaseException as exc:
                errors.append(dict(stage='OUTER_CLEANUP', message=str(exc)))
        waits = []
        for pid, h in retained.items():
            status = int(api.k.WaitForSingleObject(h, 0))
            if status != 0:
                try:
                    api.check(api.k.TerminateProcess(h, 98), 'REMEDIAL_VERIFIED_HANDLE_TERMINATE')
                except BaseException as exc:
                    errors.append(dict(stage='HANDLE_TERMINATE', pid=pid, message=str(exc)))
                status = int(api.k.WaitForSingleObject(h, 100))
            waits.append(dict(pid=pid, wait_status=status))
        if pi is not None:
            worker_wait = int(api.k.WaitForSingleObject(pi.hProcess, 100))
            if worker_wait == 0:
                exit_code = api.exit_code(pi.hProcess)
            else:
                errors.append(dict(stage='DRIVER_EXIT_UNCONFIRMED'))
        driver = None
        try:
            driver = json.loads((out / 'driver_evidence.json').read_text(encoding='utf-8'))
        except BaseException as exc:
            errors.append(dict(stage='DRIVER_EVIDENCE', message=str(exc)))
        clean = (not job_state['fallback_close_attempted'] and final is not None
                 and final['ActiveProcesses'] == 0 and all(w['wait_status'] == 0 for w in waits))
        for h in list(retained.values()) + ([] if pi is None else [pi.hThread, pi.hProcess]):
            try:
                api.close(h)
            except BaseException as exc:
                errors.append(dict(stage='OUTER_HANDLE_CLOSE', message=str(exc)))
        close_job()  # Closed/uncertain fallback handles are never retried.
        ok = clean and not timed_out and not errors and exit_code == 0 and driver is not None and driver['candidate_valid']
        label = ('INJECTED_TERMINATION_FAILURE_FALLBACK_NATIVE_VALIDATED' if args.scenario == 'B3' else
                 args.scenario + '_NATIVE_VALIDATED') if ok else 'FAIL_OR_INCOMPLETE'
        record = dict(scenario=args.scenario, status=label, wall_limit_seconds=6,
                      request_deadline_scope='BEFORE_DRIVER_CREATION', timed_out=timed_out,
                      elapsed_seconds=time.monotonic()-start, final_outer_accounting=final,
                      driver_exit_code=exit_code, driver_wait_status=worker_wait,
                      process_identities=records, handle_waits=waits,
                      job_handle_state=job_state['state'], job_handle_diagnostic=job_state['diagnostic_handle'],
                      first_termination_error=job_state['first_termination_error'],
                      fallback_close_attempted=job_state['fallback_close_attempted'],
                      fallback_close_result=job_state['fallback_close_result'],
                      fallback_close_error=job_state['fallback_close_error'],
                      final_accounting_status='AVAILABLE' if final is not None else 'UNAVAILABLE',
                      cleanup_complete=clean and not errors,
                      process_tree_exit_confirmed=clean, errors=errors,
                      production_admission='BLOCKED')
        try:
            write_new(out / 'outer_receipt.json', record)
        except BaseException:
            (base / 'HALT').touch(exist_ok=True)
            raise
        if not ok:
            (base / 'HALT').touch(exist_ok=True)
    return 0 if ok else 1


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except BaseException as exc:
        if not isinstance(exc, SystemExit) or exc.code not in (0, None):
            (Path(__file__).resolve().parent / 'HALT').touch(exist_ok=True)
        raise
