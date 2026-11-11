"""D1 deterministic contracts only: written, NOT executed under D1 authority.

No native process, Job or scientific estimator is started by these fixtures.
D2 native validation needs separate authorization and finite resource parameters;
no automatically collected native workload is included here.
"""
from decimal import Decimal
from types import SimpleNamespace

import pytest

from research.non_oracle import stfbs_lite_real_d60_supervisor_win as mod
from research.quality_allocation.service_m3_benchmarks.windows_job_monitor import api as native


class Clock:
    def __init__(self):
        self.now = 0.

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def account(user=0, kernel=0, active=1):
    return dict(TotalUserTime=user, TotalKernelTime=kernel, ActiveProcesses=active)


class FakeAPI:
    def __init__(self):
        self.calls = []
        self.queue = []
        self.last = account()
        self.kill_error = None
        self.create_error = None
        self.resume_error = None
        self.close_error = None
        self.exit = 0
        self.k = SimpleNamespace(SetInformationJobObject=lambda *args: 1)

    def job(self, name):
        self.calls.append('job')
        return 1

    def check(self, value, name):
        assert value

    def create(self, *args):
        self.calls.append('create')
        if self.create_error:
            raise self.create_error
        return SimpleNamespace(hProcess=2, hThread=3, dwProcessId=42)

    def member(self, *args):
        return True

    def resume(self, *args):
        self.calls.append('resume')
        if self.resume_error:
            raise self.resume_error

    def accounting(self, job):
        self.calls.append('query')
        if self.queue:
            item = self.queue.pop(0)
            if isinstance(item, BaseException):
                raise item
            self.last = item
        return dict(self.last)

    def terminate(self, job):
        self.calls.append('terminate')
        if self.kill_error:
            raise self.kill_error
        self.last = dict(self.last, ActiveProcesses=0)

    def exit_code(self, handle):
        return self.exit

    def close(self, handle):
        self.calls.append(('close', handle))
        if self.close_error:
            raise self.close_error


@pytest.fixture
def rig(monkeypatch):
    api, clock = FakeAPI(), Clock()
    monkeypatch.setattr(native, 'API', lambda: api)
    monkeypatch.setattr(mod, 'os', SimpleNamespace(name='nt', environ={}, fsync=lambda fd: None))
    monkeypatch.setattr(mod, 'time', clock)
    cpu = iter([1000, 1200, 1400, 1600])
    monkeypatch.setattr(mod, '_process_cpu_ticks', lambda: next(cpu))
    return api, clock


def start(rig, **kwargs):
    supervisor = mod.WindowsSupervisor(wall_seconds=kwargs.pop('wall_seconds', 1),
                                      attempt_identity='ARTIFICIAL_D1', **kwargs)
    supervisor.start(['ARTIFICIAL_ONLY'], cwd='.', log='unused.log')
    return supervisor


@pytest.mark.parametrize('value', [True, False, float('nan'), float('inf'), -float('inf'),
                                 0, -1, '1', object(), Decimal('NaN')])
@pytest.mark.parametrize('parameter', ['wall_seconds', 'user_cpu_seconds', 'total_cpu_seconds'])
def test_invalid_parameters_before_job(rig, parameter, value):
    api, _ = rig
    args = dict(wall_seconds=1)
    args[parameter] = value
    with pytest.raises(ValueError):
        mod.WindowsSupervisor(**args)
    assert api.calls == []


@pytest.mark.parametrize('value', [1e-8, Decimal('0.000000099999'), 10**20,
                                 Decimal('1e999999'), Decimal('1e-999999')])
def test_cpu_tick_range_rejected_before_job(rig, value):
    with pytest.raises(ValueError):
        mod.WindowsSupervisor(wall_seconds=1, total_cpu_seconds=value)
    assert rig[0].calls == []


def test_floor_tick_conversion(rig):
    s = mod.WindowsSupervisor(wall_seconds=1, total_cpu_seconds=Decimal('0.000000199999'))
    assert s.total_limit_ticks == 1
    assert mod._seconds(Decimal('922337203685.4775807'), cpu=True) == (1 << 63) - 1
    s.close()


def test_optional_cpu_guards_and_invalid_none_wall(rig):
    with pytest.raises(ValueError):
        mod.WindowsSupervisor(wall_seconds=None)
    assert rig[0].calls == []
    s = mod.WindowsSupervisor(wall_seconds=1, user_cpu_seconds=None, total_cpu_seconds=None)
    assert s.user_limit_ticks is None and s.total_limit_ticks is None
    s.close()


def test_final_overshoot_uses_final_accounting(rig):
    api, _ = rig
    s = start(rig, total_cpu_seconds=0.000001)
    api.queue = [account(8, 2), account(12, 3, 0), account(12, 3, 0)]
    r = s.wait()
    assert r['cpu_ticks_at_trigger'] == 10
    assert r['final_cpu_ticks'] == 15
    assert r['cpu_overshoot_ticks'] == 5
    assert r['strict_zero_overshoot'] == 'NOT_CLAIMED'
    s.close()


def test_user_plus_kernel_threshold_and_termination_before_final_query(rig):
    api, _ = rig
    s = start(rig, total_cpu_seconds=0.000001)
    api.queue = [account(6, 4)]
    r = s.wait()
    assert api.calls[api.calls.index('query') + 1] == 'terminate'
    assert r['stop_reason'] == 'CPU_LIMIT_REACHED'
    assert r['cpu_ticks_at_trigger'] == r['final_cpu_ticks'] == 10
    assert r['cpu_overshoot_ticks'] == 0
    assert r['supervisor_cpu_ticks'] == 200
    assert r['total_cpu_ticks'] == 10  # Supervisor is excluded.
    assert r['production_run_admission'] == 'BLOCKED'
    s.close()


def test_wall_precedes_any_accounting(rig):
    api, clock = rig
    s = start(rig)
    clock.now = 1
    api.queue = [OSError('query unavailable')]
    r = s.wait()
    assert api.calls.index('terminate') < api.calls.index('query')
    assert r['stop_reason'] == 'WALL_LIMIT_REACHED'
    assert r['cpu_ticks_at_trigger'] is None
    s.close()


def test_accounting_failure_is_preserved_through_secondary_failure(rig):
    api, _ = rig
    s = start(rig, total_cpu_seconds=1)
    api.queue = [OSError('original query'), OSError('cleanup query'), OSError('final query')]
    api.kill_error = OSError('secondary kill')
    r = s.wait()
    assert r['errors'][0]['message'] == 'original query'
    assert r['termination_result'] == 'FAILED'
    assert r['job_cleanup_status'] == 'FAIL'
    assert r['final_cpu_ticks'] is None and r['cpu_overshoot_ticks'] is None
    assert r['evidence_completeness_status'] == 'INCOMPLETE'
    s.close()


def test_internal_sleep_failure_protectively_terminates(rig):
    api, clock = rig
    s = start(rig)
    def fail_sleep(seconds):
        raise RuntimeError('internal wait')
    clock.sleep = fail_sleep
    r = s.wait()
    assert r['stop_reason'] == 'SUPERVISOR_INTERNAL_FAILURE'
    assert 'terminate' in api.calls
    assert r['errors'][0]['message'] == 'internal wait'
    s.close()


def test_worker_exit_does_not_end_job_monitoring(rig):
    api, _ = rig
    s = start(rig, total_cpu_seconds=0.000002)
    api.exit = 0  # Worker alone has already exited.
    api.queue = [account(1, 0, 1), account(20, 0, 1)]
    r = s.wait()
    assert r['stop_reason'] == 'CPU_LIMIT_REACHED'
    assert r['last_valid_cpu_ticks'] == 20
    s.close()


@pytest.mark.parametrize('phase', ['create', 'resume'])
def test_start_failure_closes_all_handles_and_preserves_original(rig, phase):
    api, _ = rig
    s = mod.WindowsSupervisor(wall_seconds=1)
    original = RuntimeError('original start')
    setattr(api, phase + '_error', original)
    api.kill_error = RuntimeError('secondary kill')
    api.queue = [account(active=0)]
    with pytest.raises(RuntimeError) as caught:
        s.start(['unused'], cwd='.', log='unused')
    assert caught.value is original
    assert s.closed and ('close', 1) in api.calls
    if phase == 'resume':
        assert ('close', 2) in api.calls and ('close', 3) in api.calls
    assert s.result['evidence_completeness_status'] == 'INCOMPLETE'


def test_close_is_idempotent_and_does_not_skip_later_handles(rig):
    api, _ = rig
    s = start(rig)
    api.close_error = OSError('close failed')
    s.close()
    calls = list(api.calls)
    s.close()
    assert api.calls == calls
    assert all(('close', h) in calls for h in (1, 2, 3))
    assert s.result['job_cleanup_status'] == 'FAIL'


def test_kill_failure_cannot_produce_complete_receipt(rig):
    api, _ = rig
    s = start(rig, total_cpu_seconds=0.000001)
    api.queue = [account(10), account(10, active=0)]
    api.kill_error = OSError('kill failed')
    r = s.wait()
    assert r['termination_result'] == 'FAILED'
    assert r['evidence_completeness_status'] == 'INCOMPLETE'
    s.close()


def test_final_query_failure_does_not_substitute_last_sample(rig):
    api, _ = rig
    s = start(rig, total_cpu_seconds=0.000001)
    api.queue = [account(12), account(12, active=0), OSError('final unavailable')]
    r = s.wait()
    assert r['last_valid_cpu_ticks'] == 12
    assert r['final_cpu_ticks'] is None
    assert r['cpu_overshoot_ticks'] is None
    s.close()


def test_bounded_sampling_and_no_monitoring_persistence(rig, monkeypatch):
    api, _ = rig
    s = start(rig)
    monkeypatch.setattr(mod.Path, 'open', lambda *a, **k: pytest.fail('monitoring must not write'))
    api.queue = [account(n) for n in range(80)] + [account(80, active=0)]
    r = s.wait()
    assert len(r['samples']) == 64
    assert r['stop_reason'] == 'NATURAL_EXIT'
    s.close()


def test_failed_cleanup_evidence_exclusive_write_and_failure_status(rig, tmp_path):
    api, clock = rig
    s = start(rig)
    clock.now = 1
    api.kill_error = OSError('kill unavailable')
    r = s.wait()
    assert r['job_cleanup_status'] == 'FAIL'
    path = tmp_path / 'failure.json'
    saved = s.save_failure_evidence(path)
    assert saved['saved'] is True
    before = path.read_bytes()
    again = s.save_failure_evidence(path)
    assert again['saved'] is False
    assert path.read_bytes() == before
    assert r['receipt_integrity_status'] == 'RECEIPT_WRITE_FAILED'
    assert r['evidence_completeness_status'] == 'INCOMPLETE'
    s.close()


def test_log_failure_cannot_prevent_prior_termination(rig, tmp_path, monkeypatch):
    api, _ = rig
    s = start(rig, total_cpu_seconds=0.000001)
    api.queue = [account(10)]
    r = s.wait()
    def cannot_write(*args, **kwargs):
        assert 'terminate' in api.calls
        raise OSError('disk unavailable')
    monkeypatch.setattr(mod.Path, 'open', cannot_write)
    saved = s.save_failure_evidence(tmp_path / 'failure.json')
    assert not saved['saved']
    assert r['receipt_integrity_status'] == 'RECEIPT_WRITE_FAILED'
    s.close()


def test_failure_persistence_rejected_before_stop(rig, tmp_path):
    s = start(rig)
    with pytest.raises(RuntimeError, match='STOP_OR_CLEANUP_REQUIRED'):
        s.save_failure_evidence(tmp_path / 'must-not-exist.json')
    assert not (tmp_path / 'must-not-exist.json').exists()
    s.close()


def test_context_cleanup_does_not_mask_original_exception(rig):
    api, _ = rig
    s = start(rig)
    api.close_error = OSError('secondary close')
    original = RuntimeError('context failure')
    with pytest.raises(RuntimeError) as caught:
        with s:
            raise original
    assert caught.value is original
    assert s.result['job_cleanup_status'] == 'FAIL'


def test_legacy_fields_and_no_exit_code_cpu_attribution(rig):
    api, _ = rig
    s = start(rig, user_cpu_seconds=0.15)
    api.exit = 0xC0000044
    api.queue = [account(100, active=0)]
    r = s.wait()
    assert {'termination_reason', 'worker_exit_status', 'job_cleanup_status', 'accounting'} <= r.keys()
    assert r['termination_reason'] == 'WORKER_EXITED'
    assert not r['termination_requested']
    assert r['os_termination_cause'] == 'OS_TERMINATION_CAUSE_UNVERIFIED'
    assert r['total_cpu_hard_limit'] == 'RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY'
    assert r['user_cpu_limit_ticks'] == 1_500_000
    assert r['cpu_limit_ticks'] is None
    s.close()


def test_multiple_limits_observed_without_fabricated_order(rig):
    api, clock = rig
    s = start(rig, total_cpu_seconds=0.000001, user_cpu_seconds=0.1)
    observations = iter([account(6, 4), account(6, 4, 0), account(6, 4, 0)])
    def query(job):
        clock.now = 1
        return next(observations)
    api.accounting = query
    r = s.wait()
    assert r['stop_reason'] == 'MULTIPLE_LIMITS_OBSERVED'
    assert r['user_cpu_limit_ticks'] == 1_000_000
    assert r['cpu_limit_ticks'] == 10
    s.close()


def test_supervisor_cpu_failure_is_missing_not_zero(rig, monkeypatch):
    def unavailable():
        raise OSError('process times unavailable')
    monkeypatch.setattr(mod, '_process_cpu_ticks', unavailable)
    s = start(rig)
    rig[0].queue = [account(active=0)]
    r = s.wait()
    assert r['supervisor_cpu_ticks'] is None
    assert r['evidence_completeness_status'] == 'INCOMPLETE'
    s.close()


def test_production_admission_remains_blocked():
    from research.non_oracle.stfbs_lite_real_d60_source import check_run_admission
    assert check_run_admission()['status'] == 'RUN_ADMISSION_BLOCKED'
