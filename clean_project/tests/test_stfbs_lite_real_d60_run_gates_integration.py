"""Unexecuted gate contracts. Artificial keys/files only; no scientific calls."""
import base64
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.non_oracle import stfbs_lite_real_d60_run_gates as gates
from research.non_oracle import stfbs_lite_real_d60_source as source

DISPOSITION = {'cpu_overshoot': 'REJECT_SUCCESS', 'wall_overshoot': 'REJECT_SUCCESS'}


def record(tmp_path):
    return dict(task_id='STFBS_LITE_REAL_D60', approved_source_identity='ARTIFICIAL_ONLY',
        run_id='run-test', attempt_id='attempt-test', physical_environment_id='environment-test',
        policy='R', target_cut_tick=60, maximum_completed_steps=3, source_manifest_digest='test',
        input_digests={}, runtime_identity={}, output_path=str(tmp_path / 'output'),
        policy_wls_limit=2, observation_wls_limit=2, solver_start_limit=36,
        cpu_limit={'semantics': 'TOTAL_CPU_SECONDS', 'seconds': 1}, wall_limit=2,
        storage_limit=100000, stop_rule='POST_FREEZE_PRE_ASSIGNMENT_D60')


@pytest.fixture
def signed(tmp_path):
    # Only future tests generate ephemeral TEST keys; never provisioned as trust.
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    r = record(tmp_path)
    envelope = dict(schema=gates.SCHEMA, key_id='TEST_ONLY', not_before=100, expires_at=200,
                    record=r, resource_disposition=DISPOSITION, signature='')
    envelope['signature'] = base64.b64encode(private.sign(gates.signed_bytes(envelope))).decode()
    authority = gates.Authority('TEST_ONLY', public, frozenset({source.content_digest(r)}), tmp_path)
    return envelope, authority


def verify(signed, **kwargs):
    envelope, authority = signed
    return gates.verify_signed_permit(envelope, authority, now=kwargs.pop('now', 150),
                                      expected_identity=kwargs.pop('identity', {'attempt_id': 'attempt-test'}))


def test_unprovisioned_fixed_root_rejects_without_reading_request(tmp_path):
    assert gates.TRUST_CONFIG_SHA256 is None
    with pytest.raises(source.AdmissionRejected, match='RUN_PERMIT_PROVIDER_NOT_READY'):
        gates.launch_protected_run(tmp_path / 'nonexistent-request.json')


def test_valid_test_signature_is_not_production_authority(signed):
    checked = verify(signed)
    assert checked['status'] == 'SIGNED_RECORD_VERIFIED_NOT_RUN_AUTHORITY'
    assert gates.gate_status()['status'] == 'RUN_ADMISSION_BLOCKED'


def test_tampering_rejected(signed):
    signed[0]['record']['wall_limit'] = 100
    with pytest.raises(source.AdmissionRejected, match='SIGNATURE'):
        verify(signed)


def test_permit_supplied_public_key_rejected(signed):
    signed[0]['public_key'] = 'SELF_SIGNED_KEY'
    with pytest.raises(source.AdmissionRejected, match='FIELDS'):
        verify(signed)


def test_untrusted_test_key_rejected(signed):
    envelope, authority = signed
    wrong = gates.Authority(authority.key_id, b'\0' * 32, authority.approved_record_digests,
                            authority.consumption_directory)
    with pytest.raises(source.AdmissionRejected, match='SIGNATURE'):
        gates.verify_signed_permit(envelope, wrong, now=150, expected_identity={})


@pytest.mark.parametrize('now', [99, 200, 1000])
def test_expiry_rejected(signed, now):
    with pytest.raises(source.AdmissionRejected, match='EXPIRED'):
        verify(signed, now=now)


def test_identity_mismatch_rejected(signed):
    with pytest.raises(source.AdmissionRejected, match='IDENTITY'):
        verify(signed, identity={'attempt_id': 'wrong'})


def test_valid_signature_without_user_record_approval_rejected(signed):
    env, a = signed
    root = gates.Authority(a.key_id, a.public_key, frozenset(), a.consumption_directory)
    with pytest.raises(source.AdmissionRejected, match='USER_APPROVED'):
        gates.verify_signed_permit(env, root, now=150, expected_identity={})


def test_atomic_attempt_consumption_concurrent_and_replay(signed, tmp_path):
    checked = verify(signed)
    def consume():
        try:
            return str(gates.consume_attempt(checked, tmp_path))
        except source.AdmissionRejected:
            return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: consume(), range(2)))
    assert sum(value is not None for value in outcomes) == 1
    with pytest.raises(source.AdmissionRejected, match='ALREADY_CONSUMED'):
        gates.consume_attempt(checked, tmp_path)


def test_fsync_failure_keeps_consumed_tombstone(signed, tmp_path, monkeypatch):
    checked = verify(signed)
    def fail(fd):
        raise OSError('injected fsync failure')
    monkeypatch.setattr(gates.os, 'fsync', fail)
    with pytest.raises(OSError):
        gates.consume_attempt(checked, tmp_path)
    with pytest.raises(source.AdmissionRejected, match='ALREADY_CONSUMED'):
        gates.consume_attempt(checked, tmp_path)


@pytest.mark.parametrize('key,value', [('cpu_limit', None), ('wall_limit', float('nan')),
                                    ('policy_wls_limit', True), ('solver_start_limit', 0)])
def test_missing_invalid_budget_rejected(tmp_path, key, value):
    r = record(tmp_path)
    r[key] = value
    with pytest.raises(source.AdmissionRejected):
        gates.validate_budget(r, DISPOSITION)


def test_disposition_and_user_mode_not_defaulted(tmp_path):
    r = record(tmp_path)
    with pytest.raises(source.AdmissionRejected, match='DISPOSITION'):
        gates.validate_budget(r, None)
    r['cpu_limit']['semantics'] = 'JOB_USER_SECONDS'
    with pytest.raises(source.AdmissionRejected, match='TOTAL_CPU'):
        gates.validate_budget(r, DISPOSITION)


def test_loaded_module_conflicting_path_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(gates, 'sys', SimpleNamespace(modules={
        'research.unexpected': SimpleNamespace(__file__=str(tmp_path.parent / 'outside.py'))}))
    with pytest.raises(source.AdmissionRejected, match='UNEXPECTED_LOADED'):
        gates.audit_loaded_paths(tmp_path, {})


def test_loaded_module_changed_bytes_rejected(tmp_path, monkeypatch):
    p = tmp_path / 'module.py'
    p.write_text('changed')
    monkeypatch.setattr(gates, 'sys', SimpleNamespace(modules={
        'research.artificial': SimpleNamespace(__file__=str(p))}))
    with pytest.raises(source.AdmissionRejected, match='BYTES_CHANGED'):
        gates.audit_loaded_paths(tmp_path, {'module.py': '0' * 64})


def test_source_check_never_promotes_bytes_to_isolation(tmp_path, monkeypatch):
    python = str(Path(gates.sys.executable).resolve())
    monkeypatch.setattr(gates, 'verify_source_manifest', lambda *a, **k: {'status': 'BYTES_ONLY'})
    monkeypatch.setattr(gates, 'audit_loaded_paths', lambda *a: 'CHECKED')
    result = gates.source_execution_preflight({}, repository=tmp_path, input_paths=['a', 'b'],
                                             runtime_paths=[python])
    assert result['source_bytes'] == 'SOURCE_BYTES_VERIFIED'
    assert result['source_preflight'] == 'SOURCE_PREFLIGHT_NOT_READY'
    assert result['source_execution'] != 'SOURCE_EXECUTION_ISOLATED'


def test_unprotected_worker_wiring_seam_rejects(tmp_path):
    def forbidden(**kwargs):
        pytest.fail('No production supervisor may be constructed')
    with pytest.raises(source.AdmissionRejected, match='BOOTSTRAP_NOT_READY'):
        gates.supervised_worker_call({}, argv=[], repository=tmp_path, log=tmp_path/'log',
                                     supervisor_factory=forbidden)


def receipt():
    return dict(attempt_identity='attempt-test', execution_entry='RUN_MONITORED',
        cpu_semantics='TOTAL_CPU_SECONDS', cpu_scope='WHOLE_JOB', job_cleanup_status='PASS',
        process_tree_status='PROCESS_TREE_EXIT_CONFIRMED', active_processes_final=0,
        accounting_status='FINAL_VALID', evidence_completeness_status='COMPLETE_IN_MEMORY', errors=[],
        total_user_ticks=10, total_kernel_ticks=5, final_cpu_ticks=15, total_cpu_ticks=15,
        accounting={'TotalUserTime': 10, 'TotalKernelTime': 5, 'ActiveProcesses': 0},
        cpu_limit_ticks=10_000_000, wall_limit_seconds=2., cpu_overshoot_ticks=0,
        stop_reason='NATURAL_EXIT', termination_requested=False,
        wall_elapsed_at_tree_exit=1., supervisor_cpu_ticks=1, worker_exit_status=0,
        supervisor_cpu_scope='CURRENT_PROCESS_WINDOW_EXCLUDED_FROM_JOB',
        supervisor_cpu_window_start='BEFORE_WORKER_CREATION',
        supervisor_cpu_window_end='RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE')


@pytest.mark.parametrize('key,value', [('execution_entry','LEGACY_SPLIT_UNPROTECTED'),
    ('attempt_identity','other'), ('final_cpu_ticks',None), ('job_cleanup_status','FAIL'),
    ('evidence_completeness_status','INCOMPLETE'), ('supervisor_cpu_ticks',None),
    ('wall_elapsed_at_tree_exit',float('nan'))])
def test_success_receipt_rejects_incomplete_or_conflicting_resources(tmp_path, key, value):
    result = receipt()
    result[key] = value
    with pytest.raises(source.AdmissionRejected):
        gates.validate_success_receipt(result, record(tmp_path), DISPOSITION, attempt_id='attempt-test')


def test_success_receipt_needs_explicit_disposition(tmp_path):
    with pytest.raises(source.AdmissionRejected, match='DISPOSITION'):
        gates.validate_success_receipt(receipt(), record(tmp_path), None, attempt_id='attempt-test')


def test_overshoot_is_audited_but_not_automatically_success(tmp_path):
    result = receipt()
    result.update(total_user_ticks=10_000_001, total_kernel_ticks=0,
                  final_cpu_ticks=10_000_001, total_cpu_ticks=10_000_001, cpu_overshoot_ticks=1,
                  accounting={'TotalUserTime':10_000_001,'TotalKernelTime':0,'ActiveProcesses':0})
    with pytest.raises(source.AdmissionRejected, match='DISPOSITION_REJECTED'):
        gates.validate_success_receipt(result, record(tmp_path), DISPOSITION, attempt_id='attempt-test')


def test_failed_success_audit_uses_independent_failure_path(tmp_path):
    calls = []
    class FailedSupervisor:
        closed = True
        result = {'job_cleanup_status':'FAIL'}
        def save_failure_evidence(self, path):
            calls.append(path)
            return {'saved':False,'status':'INCOMPLETE'}
    verified = {'record':record(tmp_path), 'budget':gates.validate_budget(record(tmp_path), DISPOSITION)}
    result = gates.finalize_run_evidence(FailedSupervisor(), worker_journal=tmp_path/'missing',
        receipt_path=tmp_path/'success', failure_path=tmp_path/'failure', verified=verified)
    assert result['status'] == 'FAIL_OR_INCOMPLETE'
    assert calls == [tmp_path/'failure']
    assert not (tmp_path/'success').exists()


def test_direct_production_entry_still_rejects_before_science():
    with pytest.raises(source.AdmissionRejected, match='RUN_ADMISSION_BLOCKED'):
        source.production_dispatcher(permit={'test':True})


def artificial_d60_journal(path, *, unfinished=False):
    journal = source.DurableJournal(path, attempt_id='attempt-test', max_bytes=100000)
    try:
        for tick in (0, 20, 40):
            journal.append({'kind':'STEP_REQUEST','tick':tick})
            journal.append({'kind':'STEP_RESULT','result':{'status':'COMMITTED',
                'start_tick':tick,'end_tick':tick+20,
                'checkpoint_after':{'tick':tick+20,'checkpoint_id':str(tick+20)}}})
            journal.append({'kind':'STEP_COMPLETE','start_tick':tick,'end_tick':tick+20,
                            'checkpoint_id':str(tick+20)})
        journal.append({'kind':'D60_CANDIDATE','candidate':{
                        'execution_admission':'MODEL_EXECUTION_ADMISSION_DENIED'}})
        if unfinished:
            journal.append({'kind':'WLS','status':'STARTED','call_id':'pending',
                            'category':'ACTUAL_POLICY_WLS'})
    finally:
        journal.close()


def test_complete_artificial_resource_audit_persists_success_receipt(tmp_path):
    worker, parent = tmp_path/'worker.jsonl', tmp_path/'parent.jsonl'
    artificial_d60_journal(worker)
    audited = source.persist_supervisor_receipt(worker, parent, attempt_id='attempt-test',
        result=receipt(), max_bytes=100000, permit_record=record(tmp_path),
        resource_disposition=DISPOSITION)
    assert audited['journal_status'] == 'VERIFIED'
    assert audited['last_complete_step'] == 60
    assert not audited['retry_authorized']


def test_unfinished_wls_cannot_persist_success_receipt(tmp_path):
    worker, parent = tmp_path/'worker.jsonl', tmp_path/'parent.jsonl'
    artificial_d60_journal(worker, unfinished=True)
    with pytest.raises(source.AdmissionRejected, match='COMPLETE_D60_AUDIT'):
        source.persist_supervisor_receipt(worker, parent, attempt_id='attempt-test',
            result=receipt(), max_bytes=100000, permit_record=record(tmp_path),
            resource_disposition=DISPOSITION)
    assert not parent.exists()


# V1.2 additions: deterministic contracts, not Windows access/launch evidence.
def test_request_identity_is_only_a_hint_not_authority(signed):
    env, authority = signed
    request = dict(envelope=env, repository='unused', source_manifest={},
                   input_paths=[], runtime_paths=[], expected_identity={'attempt_id':'forged'})
    with pytest.raises(source.AdmissionRejected, match='HINT_CONFLICT'):
        gates.verify_trusted_request(request, authority, now=150)
    request['expected_identity'] = {}
    verified = gates.verify_trusted_request(request, authority, now=150)
    assert verified['trusted_identity']['attempt_id'] == env['record']['attempt_id']
    assert verified['trusted_identity']['physical_environment_id'] == 'environment-test'


def test_acl_rejects_worker_delete_and_delete_child():
    from research.non_oracle.stfbs_lite_real_d60_windows_boundary import validate_acl, READ_EXECUTE
    consumer, worker = 'S-1-5-21-100', 'S-1-5-21-200'
    for mask in (READ_EXECUTE | 0x10000, READ_EXECUTE | 0x40):
        with pytest.raises(source.AdmissionRejected, match='WRITE_OR_DELETE'):
            validate_acl(consumer, True, [(0,0,0x1F01FF,consumer),(0,0,mask,worker)],
                         consumer_sid=consumer, worker_sid=worker, source=True)
    with pytest.raises(source.AdmissionRejected):
        validate_acl(worker, True, [(0,0,0x1F01FF,consumer)],
                     consumer_sid=consumer, worker_sid=worker, source=False)


def test_acl_store_does_not_grant_worker_even_read_access():
    from research.non_oracle.stfbs_lite_real_d60_windows_boundary import validate_acl, READ_EXECUTE
    with pytest.raises(source.AdmissionRejected):
        validate_acl('consumer', True, [(0,0,0x1F01FF,'consumer'),(0,0,READ_EXECUTE,'worker')],
                     consumer_sid='consumer', worker_sid='worker', source=False)


def test_snapshot_layout_escape_rejected_before_copy(tmp_path):
    from research.non_oracle.stfbs_lite_real_d60_windows_boundary import prepare_snapshot
    with pytest.raises(source.AdmissionRejected, match='PATH_ESCAPE'):
        prepare_snapshot({'source':'unused'}, {'source':'../escape'},
                         repository=tmp_path, destination=tmp_path/'snapshot')
    assert not (tmp_path/'snapshot').exists()


def test_snapshot_dependency_drift_rejected(tmp_path, monkeypatch):
    from research.non_oracle import stfbs_lite_real_d60_windows_boundary as boundary
    module = tmp_path/'dependency.pyd'
    module.write_bytes(b'artificial changed dependency')
    monkeypatch.setattr(boundary, 'reject_reparse_chain', lambda p: Path(p))
    with pytest.raises(source.AdmissionRejected, match='SNAPSHOT_BYTES_CHANGED'):
        boundary.inspect_snapshot(tmp_path, {'dependency':'dependency.pyd'},
                                  {'dependency':'0'*64}, {})


def test_consume_index_detects_deleted_marker_and_orphan(signed, tmp_path):
    from research.non_oracle.stfbs_lite_real_d60_consume_store import inspect_consume_index
    checked = verify(signed)
    marker = gates.consume_attempt(checked, tmp_path)
    with pytest.raises(source.AdmissionRejected, match='ORPHAN'):
        inspect_consume_index(tmp_path)
    row = dict(sequence=1, previous=None, attempt_id='attempt-test',
               permit_digest=checked['signed_envelope_digest'],
               marker_sha256=gates.hashlib.sha256(marker.read_bytes()).hexdigest())
    row['digest'] = source.content_digest(row)
    (tmp_path/'consumed.jsonl').write_text(gates.json.dumps(row)+'\n')
    assert len(inspect_consume_index(tmp_path)) == 1
    marker.unlink()  # Artificial tampering only; no production cleanup API.
    with pytest.raises(source.AdmissionRejected, match='DELETED_OR_CHANGED'):
        inspect_consume_index(tmp_path)


def test_consume_index_rejects_truncated_log(tmp_path):
    from research.non_oracle.stfbs_lite_real_d60_consume_store import inspect_consume_index
    (tmp_path/'consumed.jsonl').write_bytes(b'{"partial":')
    with pytest.raises(source.AdmissionRejected, match='TRUNCATED'):
        inspect_consume_index(tmp_path)


def test_verified_order_consumes_before_artificial_worker(signed, monkeypatch):
    from research.non_oracle import stfbs_lite_real_d60_consume_store as store
    checked, calls = verify(signed), []
    def consume(v, a):
        calls.append('CONSUMED')
        return {'irreversible':True}
    monkeypatch.setattr(store, 'protected_consume', consume)
    class ArtificialBackend:
        def preflight(self):
            calls.append('PREFLIGHT')
        def run_monitored(self, v, consumption):
            assert consumption['irreversible']
            calls.append('ARTIFICIAL_WORKER')
            return 'ARTIFICIAL_ONLY'
    assert gates._execute_verified_attempt(checked, signed[1], ArtificialBackend()) == 'ARTIFICIAL_ONLY'
    assert calls == ['PREFLIGHT','CONSUMED','ARTIFICIAL_WORKER']


def test_launch_failure_never_refunds_consumed_attempt(signed, tmp_path, monkeypatch):
    from research.non_oracle import stfbs_lite_real_d60_consume_store as store
    checked = verify(signed)
    monkeypatch.setattr(store, 'protected_consume', lambda v,a: gates.consume_attempt(v,tmp_path))
    class FailedBackend:
        def preflight(self):
            pass
        def run_monitored(self, *args):
            raise OSError('artificial worker launch failed')
    with pytest.raises(OSError, match='launch failed'):
        gates._execute_verified_attempt(checked, signed[1], FailedBackend())
    with pytest.raises(source.AdmissionRejected, match='ALREADY_CONSUMED'):
        gates.consume_attempt(checked, tmp_path)


def test_real_backend_blocks_before_consumption_without_trusted_windows_context(signed, monkeypatch):
    from research.non_oracle import stfbs_lite_real_d60_consume_store as store
    monkeypatch.setattr(store, 'protected_consume', lambda *a: pytest.fail('must not consume'))
    backend = gates.RestrictedWorkerBackend(signed[1], {})
    with pytest.raises(source.AdmissionRejected, match='TRUSTED_WINDOWS_CONTEXT'):
        gates._execute_verified_attempt(verify(signed), signed[1], backend)
