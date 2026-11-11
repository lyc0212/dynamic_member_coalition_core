"""Native non-scientific supervisor primitives; no RUN permit is issued here.

Reuses the existing audited x64 ABI/job-list creation utility. Job membership is
atomic at suspended process creation; only the explicitly listed std handles
are inherited. No breakaway flags are enabled.
"""
import ctypes
import os
import time
from pathlib import Path


class WindowsSupervisor:
    def __init__(self, *, wall_seconds, user_cpu_seconds=None):
        if os.name != 'nt':
            raise RuntimeError('WINDOWS_REQUIRED')
        if not wall_seconds > 0 or user_cpu_seconds is not None and not user_cpu_seconds > 0:
            raise ValueError('INVALID_SUPERVISOR_LIMITS')
        from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API, ExtendedLimit
        self.api = API()
        self.job = self.api.job(None)
        self.wall = wall_seconds
        self.pi = None
        self.closed = False
        try:
            if user_cpu_seconds is not None:
                limits = ExtendedLimit()
                limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x4
                limits.BasicLimitInformation.PerJobUserTimeLimit = int(user_cpu_seconds*10_000_000)
                self.api.check(self.api.k.SetInformationJobObject(self.job, 9, ctypes.byref(limits), ctypes.sizeof(limits)),
                               'SetInformationJobObject/USER_CPU')
        except BaseException:
            self.close()
            raise

    def start(self, argv, *, cwd, log):
        if self.pi is not None or self.closed:
            raise RuntimeError('SUPERVISOR_SINGLE_USE')
        self.started = time.monotonic()
        self.pi = self.api.create(self.job, argv, Path(cwd), dict(os.environ), Path(log))
        try:
            if not self.api.member(self.pi.hProcess, self.job):
                raise RuntimeError('WORKER_NOT_CONTAINED')
            self.api.resume(self.pi.hThread)
        except BaseException:
            self.api.terminate(self.job)
            raise
        return int(self.pi.dwProcessId)

    def wait(self):
        if self.pi is None:
            raise RuntimeError('WORKER_NOT_STARTED')
        reason = 'WORKER_EXITED'
        while self.api.accounting(self.job)['ActiveProcesses']:
            if time.monotonic()-self.started >= self.wall:
                reason = 'WALL_LIMIT'
                self.api.terminate(self.job)
                break
            time.sleep(.01)
        deadline = time.monotonic()+3.
        while self.api.accounting(self.job)['ActiveProcesses'] and time.monotonic() < deadline:
            time.sleep(.01)
        accounting = self.api.accounting(self.job)
        clean = accounting['ActiveProcesses'] == 0
        return dict(termination_reason=reason, worker_exit_status=self.api.exit_code(self.pi.hProcess),
                    job_cleanup_status='PASS' if clean else 'FAIL', accounting=accounting,
                    wall_elapsed=time.monotonic()-self.started,
                    cpu_semantics='JOB_ACCUMULATED_USER_TIME_OS_ENFORCED_NOT_EXACT_BOUNDARY',
                    total_cpu_hard_limit='RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY')

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            if self.pi is not None:
                self.api.terminate(self.job)
                self.api.k.WaitForSingleObject(self.pi.hProcess, 3000)
        finally:
            if self.pi is not None:
                self.api.close(self.pi.hThread)
                self.api.close(self.pi.hProcess)
            self.api.close(self.job)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
