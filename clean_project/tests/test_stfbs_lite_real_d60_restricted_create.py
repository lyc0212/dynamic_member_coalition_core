"""Restricted-create tests: CODE ONLY, not executed by implementation release.

Native case is separately opt-in, one bounded harmless worker, no science.
The fixture describes an independently approved existing worker-token provider;
this test never creates accounts, changes ACLs or requests credentials.
"""
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from research.non_oracle.stfbs_lite_real_d60_source import AdmissionRejected
from research.non_oracle import stfbs_lite_real_d60_restricted_create as restricted
from research.non_oracle import stfbs_lite_real_d60_windows_boundary as boundary


def fake_security(monkeypatch, *, user='worker', groups=(), restricted_sids=(('worker', 4),), elevation=0):
    values = {'user':(user,0), 'groups':groups, 'restricted':restricted_sids,
              'privileges':[('SeChangeNotifyPrivilege',2)], 'elevated':elevation, 'type':1}
    module = SimpleNamespace(TokenUser='user', TokenGroups='groups', TokenRestrictedSids='restricted',
        TokenPrivileges='privileges', TokenElevation='elevated', TokenType='type',
        GetTokenInformation=lambda token, key: values[key], ConvertSidToStringSid=str,
        LookupPrivilegeName=lambda server, name: name)
    monkeypatch.setitem(sys.modules, 'win32security', module)


def test_consumer_token_cannot_masquerade_as_worker(monkeypatch):
    fake_security(monkeypatch, user='consumer')
    with pytest.raises(AdmissionRejected, match='INDEPENDENT_WORKER'):
        restricted.inspect_token(1, consumer_sid='consumer', worker_sid='worker')


@pytest.mark.parametrize('groups,elevation,restrictions', [
    ([('S-1-5-32-544',0x10)],0,[('worker',4)]),
    ([],1,[('worker',4)]), ([],0,[])])
def test_privileged_or_unrestricted_token_rejected(monkeypatch, groups, elevation, restrictions):
    fake_security(monkeypatch, groups=groups, elevation=elevation, restricted_sids=restrictions)
    with pytest.raises(AdmissionRejected):
        restricted.inspect_token(1, consumer_sid='consumer', worker_sid='worker')


def test_token_evidence_preserves_group_attributes(monkeypatch):
    fake_security(monkeypatch, groups=[('ordinary-group',0x10)])
    evidence = restricted.inspect_token(1, consumer_sid='consumer', worker_sid='worker')
    assert evidence['groups'] == [('ordinary-group',0x10)]
    assert evidence['restricted_sids'] == [('worker',4)]


def test_system_ancestors_do_not_require_project_dacl(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(boundary, 'effective_access', lambda path, token: calls.append(path) or 4)
    monkeypatch.setattr(boundary, 'inspect_acl', lambda *a, **k: pytest.fail('no project DACL on ancestor'))
    evidence = boundary.inspect_ancestor_access(tmp_path/'snapshot', 1)
    assert evidence and calls


def test_ancestor_delete_child_and_replacement_denied(monkeypatch, tmp_path):
    for rights in (0x40, 0x10000, 0x40000, 0x80000, 0x100):
        monkeypatch.setattr(boundary, 'effective_access', lambda path, token: rights)
        with pytest.raises(AdmissionRejected, match='REPLACE_OR_REDIRECT'):
            boundary.inspect_ancestor_access(tmp_path/'snapshot', 1)


def test_effective_access_failure_is_not_treated_as_safe_denial(monkeypatch, tmp_path):
    def unavailable(*args):
        raise OSError('AccessCheck unavailable')
    monkeypatch.setattr(boundary, 'effective_access', unavailable)
    with pytest.raises(OSError):
        boundary.inspect_worker_no_write(tmp_path, 1)


def test_source_and_store_effective_write_rejected(monkeypatch, tmp_path):
    for rights in (2, 4, 0x10, 0x40, 0x10000, 0x40000):
        monkeypatch.setattr(boundary, 'effective_access', lambda path, token: rights)
        with pytest.raises(AdmissionRejected):
            boundary.inspect_worker_no_write(tmp_path, 1)


@pytest.mark.skipif(os.environ.get('STFBS_RESTRICTED_NATIVE_TEST_AUTHORIZED') != 'YES'
                    or os.name != 'nt', reason='Separate bounded native-test authorization required')
def test_native_independent_token_worker_before_resume(tmp_path):
    from research.non_oracle.stfbs_lite_real_d60_run_gates import read_json
    from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor
    from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API
    fixture_path = os.environ.get('STFBS_RESTRICTED_NATIVE_FIXTURE')
    assert fixture_path, 'Approved independent token fixture required; no automatic account/credentials'
    fixture = read_json(fixture_path)
    context, executable = fixture['context'], fixture['controlled_python']
    token, token_evidence = restricted.acquire_worker_token(context)
    try:
        assert token_evidence['user_sid'] != context['consumer_sid']
        boundary.inspect_worker_no_write(fixture['protected_source_probe'], token)
        boundary.inspect_worker_no_write(fixture['protected_consume_probe'], token, store=True)
        adapter = restricted.restricted_create_adapter(token, context, executable=executable,
                   environment=fixture['controlled_environment'])
        with WindowsSupervisor(wall_seconds=3., total_cpu_seconds=1.,
                               attempt_identity='ARTIFICIAL_RESTRICTED_NATIVE_ONLY') as supervisor:
            supervisor.api = adapter  # Instance-only; no frozen/global changes.
            result = supervisor.run_monitored([executable, '-I', '-S', '-B', '-c',
                       'import time; time.sleep(.1)'], cwd=Path(executable).parent, log=tmp_path/'worker.log')
        assert result['execution_entry'] == 'RUN_MONITORED'
        assert result['job_cleanup_status'] == 'PASS'
        assert len(adapter.restricted_creation_evidence) == 1
        assert adapter.restricted_creation_evidence[0]['state'] == 'CONTAINED_BEFORE_RESUME'
        assert not adapter.restricted_creation_failures
    finally:
        API().close(token)
