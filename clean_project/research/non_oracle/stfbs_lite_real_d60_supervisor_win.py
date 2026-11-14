"""Non-scientific Windows supervision; never grants production admission.

CPU thresholds are engineering inputs, not approved production budgets. Polling
and OS user-time limits do not guarantee zero overshoot or bounded latency.
"""
import ctypes
import json
import math
import os
import time
from collections import deque
from decimal import Decimal
from pathlib import Path


_MAX_TICKS = (1 << 63) - 1


def _seconds(value, *, cpu=False):
    """Validate before creating a Job; floor exact decimal seconds to ticks."""
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise ValueError('INVALID_SUPERVISOR_LIMITS')
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number <= 0:
            raise ValueError('INVALID_SUPERVISOR_LIMITS')
        if cpu:
            if number < Decimal('0.0000001') or number >= Decimal('922337203685.4775808'):
                raise ValueError('INVALID_SUPERVISOR_LIMITS')
            # Integer ratio avoids Decimal context rounding at large magnitudes.
            numerator, denominator = number.as_integer_ratio()
            ticks = numerator * 10_000_000 // denominator
            if not 1 <= ticks <= _MAX_TICKS:
                raise ValueError('INVALID_SUPERVISOR_LIMITS')
            return ticks
        result = float(number)
        if not math.isfinite(result) or result <= 0:
            raise ValueError('INVALID_SUPERVISOR_LIMITS')
        return result
    except (OverflowError, ArithmeticError) as exc:
        raise ValueError('INVALID_SUPERVISOR_LIMITS') from exc


def _process_cpu_ticks():
    """Current process user+kernel; callers use a window delta, not lifetime."""
    from ctypes import wintypes as W
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.argtypes = []
    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.GetProcessTimes.argtypes = [W.HANDLE] + [ctypes.POINTER(W.FILETIME)] * 4
    kernel.GetProcessTimes.restype = W.BOOL
    values = [W.FILETIME() for _ in range(4)]
    if not kernel.GetProcessTimes(kernel.GetCurrentProcess(), *(ctypes.byref(v) for v in values)):
        raise ctypes.WinError(ctypes.get_last_error())
    return sum((v.dwHighDateTime << 32) | v.dwLowDateTime for v in values[2:])


class WindowsSupervisor:
    def __init__(self, *, wall_seconds, user_cpu_seconds=None, total_cpu_seconds=None,
                 attempt_identity=None):
        wall = _seconds(wall_seconds)
        user = None if user_cpu_seconds is None else _seconds(user_cpu_seconds, cpu=True)
        total = None if total_cpu_seconds is None else _seconds(total_cpu_seconds, cpu=True)
        if os.name != 'nt':
            raise RuntimeError('WINDOWS_REQUIRED')
        from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API, ExtendedLimit
        self.wall, self.user_limit_ticks, self.total_limit_ticks = wall, user, total
        self.attempt_identity = attempt_identity
        self.api = API()
        self.job = None
        self.job_handle_state = 'JOB_HANDLE_NOT_CREATED'
        self.fallback_close_attempted = False
        self.fallback_close_result = None
        self.fallback_close_error = None
        self.protected_entry = False
        self.pi = None
        self.closed = False
        self.started = None
        self.result = None
        self.errors = []
        self.samples = deque(maxlen=64)
        self.events = deque(maxlen=64)
        self.last_sample = None
        self.stop_reason = None
        self.stop_elapsed = None
        self.trigger_cpu = None
        self.termination_requested = False
        self.termination_result = None
        self.termination_error = None
        self.tree_exit_elapsed = None
        self.supervisor_cpu_start = None
        self.supervisor_cpu_error = None
        try:
            self.job = self.api.job(None)
            self.job_handle_state = 'JOB_HANDLE_OPEN'
            if user is not None:
                limits = ExtendedLimit()
                limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x4
                limits.BasicLimitInformation.PerJobUserTimeLimit = user
                self.api.check(self.api.k.SetInformationJobObject(
                    self.job, 9, ctypes.byref(limits), ctypes.sizeof(limits)),
                    'SetInformationJobObject/USER_CPU')
            self.events.append('GUARD_CONFIGURED')
        except BaseException as exc:
            self._error('CONFIGURATION_FAILURE', exc)
            self.close()
            raise

    def _error(self, stage, exc):
        self.errors.append(dict(stage=stage, type=type(exc).__name__, message=str(exc)))

    def _elapsed(self):
        return None if self.started is None else time.monotonic() - self.started

    def _query(self):
        if self.job_handle_state != 'JOB_HANDLE_OPEN':
            raise RuntimeError('JOB_HANDLE_NOT_USABLE')
        accounting = self.api.accounting(self.job)
        for name in ('TotalUserTime', 'TotalKernelTime', 'ActiveProcesses'):
            value = accounting[name]
            if type(value) is not int or value < 0:
                raise ValueError('INVALID_JOB_ACCOUNTING/' + name)
        ticks = accounting['TotalUserTime'] + accounting['TotalKernelTime']
        sample = dict(wall_elapsed=self._elapsed(), cpu_ticks=ticks,
                      active_processes=accounting['ActiveProcesses'], accounting=dict(accounting))
        if self.last_sample is not None and ticks < self.last_sample['cpu_ticks']:
            raise ValueError('NONMONOTONIC_JOB_CPU')
        self.last_sample = sample
        self.samples.append(sample)
        return sample

    def _terminate(self, reason):
        """No persistence or CPU query may precede this stop request."""
        if self.job_handle_state != 'JOB_HANDLE_OPEN':
            return  # Closed or uncertain handles must never be reused.
        if self.stop_reason is None:
            self.stop_reason = reason
            self.stop_elapsed = self._elapsed()
            self.trigger_cpu = (self.last_sample['cpu_ticks'] if self.last_sample is not None
                                and reason in ('CPU_LIMIT_REACHED', 'MULTIPLE_LIMITS_OBSERVED')
                                else None)
        self.termination_requested = True
        self.events.append('STOP_REQUESTED')
        try:
            self.api.terminate(self.job)
            self.termination_result = 'SUCCEEDED'
            self.events.append('TERMINATE_JOB_RESULT')
        except BaseException as exc:
            self.termination_result = 'FAILED'
            if self.termination_error is None:
                self.termination_error = dict(type=type(exc).__name__, message=str(exc))
            self._error('TERMINATE_JOB_FAILURE', exc)
            self._close_job(fallback=True)  # Before any drain/query/persistence.

    def _close_job(self, *, fallback=False):
        if self.job_handle_state != 'JOB_HANDLE_OPEN':
            return
        self.job_handle_state = 'JOB_HANDLE_CLOSE_ATTEMPTED'
        if fallback:
            self.fallback_close_attempted = True
        try:
            self.api.close(self.job)
        except BaseException as exc:
            # Retain the value for diagnostics, but never assume it is usable
            # or retry it blindly after an uncertain CloseHandle outcome.
            self.job_handle_state = 'JOB_HANDLE_CLOSE_FAILED_OR_UNCERTAIN'
            self._error('FALLBACK_JOB_CLOSE_FAILURE' if fallback else 'HANDLE_CLOSE_FAILURE', exc)
            if fallback:
                self.fallback_close_result = 'FAILED_OR_UNCERTAIN'
                self.fallback_close_error = dict(type=type(exc).__name__, message=str(exc))
        else:
            self.job = None
            self.job_handle_state = 'JOB_HANDLE_CLOSED'
            if fallback:
                self.fallback_close_result = 'SUCCEEDED_TREE_EXIT_UNVERIFIED'

    def _drain(self):
        """Bounded best effort; successful kill is not evidence of tree exit."""
        if self.job_handle_state != 'JOB_HANDLE_OPEN':
            return False
        deadline = time.monotonic() + 3.
        while True:
            try:
                sample = self._query()
                if sample['active_processes'] == 0:
                    self.tree_exit_elapsed = sample['wall_elapsed']
                    self.events.append('PROCESS_TREE_EXIT_CONFIRMED')
                    return True
            except BaseException as exc:
                self._error('CLEANUP_ACCOUNTING_FAILURE', exc)
                return False
            if time.monotonic() >= deadline:
                return False
            try:
                time.sleep(.01)
            except BaseException as exc:
                self._error('CLEANUP_WAIT_FAILURE', exc)
                return False

    def start(self, argv, *, cwd, log):
        if self.started is not None or self.closed:
            raise RuntimeError('SUPERVISOR_SINGLE_USE')
        self.started = time.monotonic()  # Includes creation and containment.
        try:
            self.supervisor_cpu_start = _process_cpu_ticks()
        except BaseException as exc:
            self.supervisor_cpu_error = str(exc)
            self._error('SUPERVISOR_CPU_START_FAILURE', exc)
        try:
            self.pi = self.api.create(self.job, argv, Path(cwd), dict(os.environ), Path(log))
            if not self.api.member(self.pi.hProcess, self.job):
                raise RuntimeError('WORKER_NOT_CONTAINED')
            self.events.append('WORKER_CONTAINED')
            self.api.resume(self.pi.hThread)
            self.events.append('WORKER_RESUMED')
        except BaseException as exc:
            self._error('START_FAILURE', exc)
            self._terminate('SUPERVISOR_INTERNAL_FAILURE')
            self._drain()
            self._finish()
            self.close()
            raise  # Preserve the original create/member/resume exception.
        return int(self.pi.dwProcessId)

    def run_monitored(self, argv, *, cwd, log):
        """Protected synchronous entry; no caller work between start and wait.

        Does not eliminate OS scheduling delay or grant production admission.
        Legacy split calls remain available, but are not this protected entry.
        """
        self.protected_entry = True
        primary_error = None
        try:
            self.start(argv, cwd=cwd, log=log)
            return self.wait()
        except BaseException as exc:
            primary_error = exc
            self._error('RUN_MONITORED_FAILURE', exc)
            raise
        finally:
            try:
                self.close()
            except BaseException as exc:
                self._error('RUN_MONITORED_CLOSE_FAILURE', exc)
                if self.result is not None:
                    self.result.update(errors=list(self.errors), job_cleanup_status='FAIL',
                                       evidence_completeness_status='INCOMPLETE')
                if primary_error is None:
                    raise

    def wait(self):
        if self.result is not None:
            return self.result
        if self.pi is None or self.closed:
            raise RuntimeError('WORKER_NOT_STARTED')
        self.events.append('RUNNING_MONITORED')
        try:
            while True:
                if self._elapsed() >= self.wall:
                    # Do not query accounting before a due wall termination.
                    self._terminate('WALL_LIMIT_REACHED')
                    break
                try:
                    sample = self._query()
                except BaseException as exc:
                    self._error('CPU_ACCOUNTING_FAILURE', exc)
                    self._terminate('CPU_ACCOUNTING_FAILURE')
                    break
                cpu_due = (self.total_limit_ticks is not None
                           and sample['cpu_ticks'] >= self.total_limit_ticks)
                wall_due = sample['wall_elapsed'] >= self.wall
                if cpu_due or wall_due:
                    reason = ('MULTIPLE_LIMITS_OBSERVED' if cpu_due and wall_due else
                              'CPU_LIMIT_REACHED' if cpu_due else 'WALL_LIMIT_REACHED')
                    self._terminate(reason)
                    break
                if sample['active_processes'] == 0:
                    self.stop_reason = 'NATURAL_EXIT'
                    self.tree_exit_elapsed = sample['wall_elapsed']
                    self.events.append('PROCESS_TREE_EXIT_CONFIRMED')
                    break
                time.sleep(.01)
        except BaseException as exc:
            self._error('SUPERVISOR_INTERNAL_FAILURE', exc)
            self._terminate('SUPERVISOR_INTERNAL_FAILURE')
        if self.tree_exit_elapsed is None:
            self._drain()
        return self._finish()

    def _finish(self):
        final = None
        try:
            candidate = self._query() if self.job_handle_state == 'JOB_HANDLE_OPEN' else None
            if candidate is not None and candidate['active_processes'] == 0 and self.tree_exit_elapsed is not None:
                final = candidate
                self.events.append('FINAL_ACCOUNTING')
        except BaseException as exc:
            self._error('FINAL_ACCOUNTING_UNAVAILABLE', exc)
        exit_code = None
        if self.pi is not None:
            try:
                exit_code = self.api.exit_code(self.pi.hProcess)
            except BaseException as exc:
                self._error('WORKER_EXIT_STATUS_FAILURE', exc)
        supervisor_cpu = None
        try:
            end = _process_cpu_ticks()
            if self.supervisor_cpu_start is not None:
                supervisor_cpu = end - self.supervisor_cpu_start
                if supervisor_cpu < 0:
                    raise ValueError('NONMONOTONIC_SUPERVISOR_CPU')
        except BaseException as exc:
            supervisor_cpu = None
            self._error('SUPERVISOR_CPU_END_FAILURE', exc)
        ticks = None if final is None else final['cpu_ticks']
        clean = self.tree_exit_elapsed is not None
        if not clean:
            self.events.append('PROCESS_TREE_CLEANUP_FAILED')
        complete = clean and final is not None and exit_code is not None and not self.errors
        reason = self.stop_reason
        legacy_reason = {'NATURAL_EXIT': 'WORKER_EXITED', 'WALL_LIMIT_REACHED': 'WALL_LIMIT'}.get(reason, reason)
        self.result = dict(
            attempt_identity=self.attempt_identity,
            termination_reason=legacy_reason, stop_reason=reason,
            worker_exit_status=exit_code, worker_exit_code=exit_code,
            job_cleanup_status='PASS' if clean else 'FAIL',
            process_tree_status=('PROCESS_TREE_EXIT_CONFIRMED' if clean else
                                 'PROCESS_TREE_CLEANUP_UNVERIFIED' if self.fallback_close_attempted else
                                 'PROCESS_TREE_CLEANUP_FAILED'),
            execution_entry='RUN_MONITORED' if self.protected_entry else 'LEGACY_SPLIT_UNPROTECTED',
            job_handle_state=self.job_handle_state,
            fallback_close_attempted=self.fallback_close_attempted,
            fallback_close_result=self.fallback_close_result,
            fallback_close_error_if_any=self.fallback_close_error,
            original_termination_error=self.termination_error,
            accounting=None if final is None else final['accounting'],
            cpu_semantics=('TOTAL_CPU_SECONDS' if self.total_limit_ticks is not None else
                           'JOB_ACCUMULATED_USER_TIME_OS_ENFORCED_NOT_EXACT_BOUNDARY'),
            cpu_scope='WHOLE_JOB', cpu_limit_ticks=self.total_limit_ticks,
            user_cpu_limit_ticks=self.user_limit_ticks, wall_limit_seconds=self.wall,
            total_user_ticks=None if final is None else final['accounting']['TotalUserTime'],
            total_kernel_ticks=None if final is None else final['accounting']['TotalKernelTime'],
            total_cpu_ticks=ticks, final_cpu_ticks=ticks,
            cpu_ticks_at_trigger=self.trigger_cpu,
            last_valid_cpu_ticks=None if self.last_sample is None else self.last_sample['cpu_ticks'],
            last_valid_cpu_sample=self.last_sample,
            cpu_overshoot_ticks=(None if ticks is None or self.total_limit_ticks is None else
                                 max(0, ticks - self.total_limit_ticks)),
            wall_elapsed=self._elapsed(), last_valid_wall_sample=self._elapsed(),
            wall_elapsed_at_stop_request=self.stop_elapsed,
            wall_elapsed_at_tree_exit=self.tree_exit_elapsed,
            termination_latency=(None if self.stop_elapsed is None or self.tree_exit_elapsed is None else
                                 self.tree_exit_elapsed - self.stop_elapsed),
            termination_requested=self.termination_requested,
            termination_attempted=self.termination_requested,
            termination_result=self.termination_result, termination_error=self.termination_error,
            remaining_active_processes_if_known=(None if self.last_sample is None else
                                                self.last_sample['active_processes']),
            active_processes_final=None if final is None else final['active_processes'],
            supervisor_cpu_ticks=supervisor_cpu,
            supervisor_cpu_scope='CURRENT_PROCESS_USER_PLUS_KERNEL_WINDOW_EXCLUDED_FROM_JOB; '
                                 'MAY_INCLUDE_OTHER_CONCURRENT_WORK',
            supervisor_cpu_window_start='BEFORE_WORKER_CREATION',
            supervisor_cpu_window_end='RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE',
            accounting_status='FINAL_VALID' if final is not None else 'FINAL_ACCOUNTING_UNAVAILABLE',
            receipt_integrity_status='NOT_PERSISTED',
            evidence_completeness_status='COMPLETE_IN_MEMORY' if complete else 'INCOMPLETE',
            os_termination_cause='OS_TERMINATION_CAUSE_UNVERIFIED',
            samples=list(self.samples), events=list(self.events), errors=list(self.errors),
            strict_zero_overshoot='NOT_CLAIMED', overshoot_bound='NOT_PROVEN',
            total_cpu_hard_limit='RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY',
            production_run_admission='BLOCKED')
        return self.result

    def save_failure_evidence(self, path):
        """Explicit caller-selected, exclusive-create failure record; never a PASS.

        Call after wait/start failure/close. No implicit production directory and
        no IO on the live monitoring path. A partial failed write is retained.
        """
        if self.result is None or (self.started is not None and self.tree_exit_elapsed is None
                                   and not self.termination_requested):
            raise RuntimeError('STOP_OR_CLEANUP_REQUIRED_BEFORE_PERSISTENCE')
        record = dict(self.result, evidence_kind='SUPERVISOR_FAILURE_EVIDENCE',
                      evidence_completeness_status='INCOMPLETE',
                      receipt_integrity_status='FAILURE_RECORD_WRITTEN_NOT_SUCCESS_RECEIPT')
        try:
            payload = json.dumps(record, ensure_ascii=False, allow_nan=False).encode('utf-8') + b'\n'
            with Path(path).open('xb') as stream:
                if stream.write(payload) != len(payload):
                    raise OSError('SHORT_RECEIPT_WRITE')
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException as exc:
            self._error('RECEIPT_WRITE_FAILED', exc)
            self.result.update(receipt_integrity_status='RECEIPT_WRITE_FAILED',
                               evidence_completeness_status='INCOMPLETE', errors=list(self.errors))
            return dict(saved=False, status='INCOMPLETE', error=str(exc), path=str(path))
        self.result['receipt_integrity_status'] = 'FAILURE_EVIDENCE_SAVED'
        return dict(saved=True, status='FAILURE_EVIDENCE_ONLY', path=str(path))

    def close(self):
        if self.closed:
            return
        try:
            if self.job_handle_state == 'JOB_HANDLE_OPEN' and self.started is not None and self.tree_exit_elapsed is None:
                self._terminate(self.stop_reason or 'SUPERVISOR_CLOSED')
                self._drain()
            if self.started is not None and self.result is None:
                self._finish()
        finally:
            # Try every handle even if an earlier close fails. Never mask the
            # original start/context exception with a secondary cleanup error.
            handles = [] if self.pi is None else [self.pi.hThread, self.pi.hProcess]
            for handle in handles:
                if handle is not None:
                    try:
                        self.api.close(handle)
                    except BaseException as exc:
                        self._error('HANDLE_CLOSE_FAILURE', exc)
            self._close_job()
            self.closed = True
            if self.result is not None:
                self.result.update(job_handle_state=self.job_handle_state,
                                   fallback_close_attempted=self.fallback_close_attempted,
                                   fallback_close_result=self.fallback_close_result,
                                   fallback_close_error_if_any=self.fallback_close_error,
                                   original_termination_error=self.termination_error)
            if self.result is not None and self.errors:
                self.result.update(errors=list(self.errors), evidence_completeness_status='INCOMPLETE')
                if any(e['stage'] == 'HANDLE_CLOSE_FAILURE' for e in self.errors):
                    self.result['job_cleanup_status'] = 'FAIL'

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
