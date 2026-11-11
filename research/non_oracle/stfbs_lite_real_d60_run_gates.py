"""REAL D60 gate contracts. No keys, permits or production budgets are issued.

Production remains closed until externally provisioned trust AND a verified
Windows execution-isolation backend exist. A digest is never authorization.
"""
import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from research.non_oracle.stfbs_lite_real_d60_source import (
    AdmissionRejected, CATEGORIES, content_digest, verify_permit_record,
    verify_source_manifest, _require,
)
from research.non_oracle.stfbs_lite_real_d60_supervisor_win import _seconds

TRUST_CONFIG_PATH = Path(r'C:\ProgramData\STFBSLite\real_d60_authority.json')
# Must be approved out of band. No CLI/environment/permit-supplied override.
TRUST_CONFIG_SHA256 = None
SCHEMA = 'STFBS_REAL_D60_SIGNED_PERMIT_V1'


@dataclass(frozen=True)
class Authority:
    """Verifier input only; constructing this object grants no launch rights."""
    key_id: str
    public_key: bytes
    approved_record_digests: frozenset
    consumption_directory: Path
    execution_context: dict = None


def read_json(path):
    def unique(pairs):
        out = {}
        for key, value in pairs:
            _require(key not in out, 'DUPLICATE_JSON_KEY')
            out[key] = value
        return out
    def invalid(value):
        raise AdmissionRejected('NONFINITE_JSON_NUMBER')
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      object_pairs_hook=unique, parse_constant=invalid)


def load_production_authority():
    _require(TRUST_CONFIG_SHA256 is not None, 'RUN_PERMIT_PROVIDER_NOT_READY')
    path = TRUST_CONFIG_PATH
    _require(path.is_absolute() and not path.is_symlink(), 'UNTRUSTED_AUTHORITY_PATH')
    raw = path.read_bytes()
    _require(hashlib.sha256(raw).hexdigest() == TRUST_CONFIG_SHA256,
             'TRUST_ROOT_CONFIGURATION_DRIFT')
    # Parse exactly the checked bytes, not a second filesystem read.
    config = json.loads(raw.decode('utf-8-sig'))
    _require(set(config) == {'key_id', 'ed25519_public_key', 'approved_record_digests',
                            'consumption_directory', 'execution_context'}, 'TRUST_ROOT_FIELDS_INVALID')
    key = base64.b64decode(config['ed25519_public_key'], validate=True)
    _require(len(key) == 32 and bool(config['key_id']), 'INVALID_TRUST_ROOT')
    digests = config['approved_record_digests']
    _require(type(digests) is list and all(type(d) is str and len(d) == 64 for d in digests),
             'APPROVED_RECORDS_REQUIRED')
    directory = Path(config['consumption_directory'])
    _require(directory.is_absolute(), 'CONSUMPTION_DIRECTORY_INVALID')
    context = config['execution_context']
    _require(type(context) is dict and set(context) >= {'consumer_sid', 'worker_sid',
             'snapshot_root', 'snapshot_layout'}
             and set(context) <= {'consumer_sid', 'worker_sid', 'snapshot_root',
                                  'snapshot_layout', 'token_source'}, 'TRUSTED_WINDOWS_CONTEXT_REQUIRED')
    from research.non_oracle.stfbs_lite_real_d60_windows_boundary import inspect_acl, inspect_current_identity
    inspect_current_identity(consumer_sid=context['consumer_sid'], worker_sid=context['worker_sid'])
    inspect_acl(path, consumer_sid=context['consumer_sid'], worker_sid=context['worker_sid'], source=False)
    return Authority(config['key_id'], key, frozenset(digests), directory, context)


def signed_bytes(envelope):
    body = {k: v for k, v in envelope.items() if k != 'signature'}
    return (SCHEMA + '\n' + json.dumps(body, sort_keys=True, separators=(',', ':'),
                                      allow_nan=False)).encode('utf-8')


def validate_budget(record, disposition):
    _require(type(record.get('cpu_limit')) is dict
             and set(record['cpu_limit']) == {'semantics', 'seconds'}
             and record['cpu_limit']['semantics'] == 'TOTAL_CPU_SECONDS',
             'WHOLE_JOB_TOTAL_CPU_REQUIRED')
    try:
        ticks = _seconds(record['cpu_limit']['seconds'], cpu=True)
        wall = _seconds(record['wall_limit'])
    except (ValueError, TypeError, KeyError) as exc:
        raise AdmissionRejected('PRODUCTION_TIME_BUDGET_INVALID') from exc
    for name in ('policy_wls_limit', 'observation_wls_limit', 'solver_start_limit', 'storage_limit'):
        _require(type(record.get(name)) is int and record[name] > 0, 'PRODUCTION_BUDGET_MISSING')
    # No default disposition; this software supports rejection, not a newly
    # approved allowance. The signed envelope must explicitly carry this rule.
    _require(disposition == {'cpu_overshoot': 'REJECT_SUCCESS', 'wall_overshoot': 'REJECT_SUCCESS'},
             'APPROVED_RESOURCE_DISPOSITION_REQUIRED')
    return dict(total_cpu_ticks=ticks, wall_seconds=wall,
                wls_limits=dict(zip(CATEGORIES, (record['policy_wls_limit'],
                    record['observation_wls_limit'], record['solver_start_limit']))),
                storage_limit=record['storage_limit'], disposition=dict(disposition))


def verify_signed_permit(envelope, authority, *, now, expected_identity):
    """Pure verifier; only the fixed-root loader is used by production launch."""
    _require(type(authority) is Authority, 'TRUSTED_AUTHORITY_REQUIRED')
    fields = {'schema', 'key_id', 'not_before', 'expires_at', 'record', 'resource_disposition', 'signature'}
    _require(type(envelope) is dict and set(envelope) == fields, 'SIGNED_PERMIT_FIELDS_INVALID')
    _require(envelope['schema'] == SCHEMA and envelope['key_id'] == authority.key_id,
             'PERMIT_AUTHORITY_CONFLICT')
    _require(type(now) is int and type(envelope['not_before']) is int
             and type(envelope['expires_at']) is int
             and envelope['not_before'] <= now < envelope['expires_at'], 'PERMIT_EXPIRED_OR_NOT_YET_VALID')
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        signature = base64.b64decode(envelope['signature'], validate=True)
        Ed25519PublicKey.from_public_bytes(authority.public_key).verify(signature, signed_bytes(envelope))
    except Exception as exc:
        raise AdmissionRejected('PERMIT_SIGNATURE_INVALID_OR_BACKEND_UNAVAILABLE') from exc
    record = envelope['record']
    digest = content_digest(record)
    _require(digest in authority.approved_record_digests, 'USER_APPROVED_RECORD_REQUIRED')
    # Existing field/scope verifier is reused only AFTER signature verification.
    verify_permit_record(record, independent_expected_digest=digest, expected_identity=expected_identity)
    _require(all(type(record[k]) is str and record[k].strip() for k in
                 ('run_id', 'attempt_id', 'physical_environment_id', 'output_path')),
             'PERMIT_IDENTITY_INVALID')
    _require(Path(record['output_path']).is_absolute(), 'ABSOLUTE_OUTPUT_REQUIRED')
    budget = validate_budget(record, envelope['resource_disposition'])
    return dict(record=record, record_digest=digest, budget=budget,
                signed_envelope_digest=content_digest(envelope), status='SIGNED_RECORD_VERIFIED_NOT_RUN_AUTHORITY')


def consume_attempt(verified, directory):
    """Exclusive-create tombstone; never unlink/refund, including on fsync failure.

    Concurrency is enforced by O_EXCL on a local store. Store ACLs, directory
    metadata durability and protection against deletion still require external
    provisioning/Windows validation; production cannot reach this while blocked.
    """
    directory = Path(directory)
    _require(directory.is_dir() and not directory.is_symlink(), 'ATTEMPT_STORE_NOT_PROVISIONED')
    attempt = verified['record']['attempt_id']
    marker = directory / (hashlib.sha256(attempt.encode()).hexdigest() + '.consumed')
    payload = json.dumps(dict(attempt_id=attempt, run_id=verified['record']['run_id'],
                             permit_digest=verified['signed_envelope_digest'],
                             status='CONSUMED_NO_REFUND'), sort_keys=True).encode() + b'\n'
    try:
        fd = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise AdmissionRejected('ATTEMPT_ALREADY_CONSUMED') from exc
    with os.fdopen(fd, 'wb') as stream:
        _require(stream.write(payload) == len(payload), 'CONSUMPTION_SHORT_WRITE')
        stream.flush()
        os.fsync(stream.fileno())
    return marker


def audit_loaded_paths(repository, manifest):
    """Check currently loaded project modules; not a dependency-closure proof."""
    root = Path(repository).resolve()
    expected = {}
    for name, sha in manifest.items():
        path = Path(name) if Path(name).is_absolute() else root / name
        expected[path.resolve()] = sha
    for name, module in tuple(sys.modules.items()):
        if name.split('.')[0] not in {'research', 'pursuit_v2', 'scripts'}:
            continue
        filename = getattr(module, '__file__', None)
        if filename is None:
            continue
        path = Path(filename).resolve()
        _require(path.is_relative_to(root) and path in expected, 'UNEXPECTED_LOADED_PROJECT_MODULE')
        _require(hashlib.sha256(path.read_bytes()).hexdigest() == expected[path], 'LOADED_SOURCE_BYTES_CHANGED')
    return 'LOADED_PROJECT_PATHS_CHECKED_NOT_ISOLATED'


def source_execution_preflight(manifest, *, repository, input_paths, runtime_paths):
    root = Path(repository).resolve()
    for name in manifest:
        path = Path(name) if Path(name).is_absolute() else root / name
        _require(path.exists() and not path.is_symlink(), 'SOURCE_MISSING_OR_LINKED')
        if not Path(name).is_absolute():
            _require(path.resolve().is_relative_to(root), 'SOURCE_PATH_ESCAPE')
    _require(str(Path(sys.executable).resolve()) in {str(Path(p).resolve()) for p in runtime_paths},
             'PYTHON_EXECUTABLE_NOT_PINNED')
    verify_source_manifest(manifest, repository=root, input_paths=input_paths, runtime_paths=runtime_paths)
    audit_loaded_paths(root, manifest)
    # No Windows restricted-worker ACL/token + immutable runtime closure is
    # provisioned. Never accept caller booleans as an isolation attestation.
    return dict(source_bytes='SOURCE_BYTES_VERIFIED', source_execution='NOT_ISOLATED',
                source_preflight='SOURCE_PREFLIGHT_NOT_READY',
                reason='WINDOWS_READ_ONLY_RUNTIME_DEPENDENCY_CLOSURE_AND_LOAD_ENFORCEMENT_NOT_PROVISIONED')


def gate_status():
    return dict(status='RUN_ADMISSION_BLOCKED', hard_time_guard='RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY',
                blockers=['RUN_PERMIT_PROVIDER_NOT_READY', 'SOURCE_PREFLIGHT_NOT_READY',
                          'ATTEMPT_STORE_PROTECTION_AND_DURABILITY_NOT_VERIFIED',
                          'PRODUCTION_BUDGET_AND_DISPOSITION_NOT_APPROVED'],
                reason='REAL_D60_RESTRICTED_WORKER_FINAL_CLOSURE_PARTIAL_BLOCKED')


def verify_trusted_request(request, authority, *, now):
    """Identity comes from signed + independently approved bytes, not hints."""
    _require(type(request) is dict and set(request) == {'envelope', 'repository', 'source_manifest',
             'input_paths', 'runtime_paths', 'expected_identity'}, 'RUN_REQUEST_FIELDS_INVALID')
    verified = verify_signed_permit(request['envelope'], authority, now=now, expected_identity={})
    record = verified['record']
    hint = request['expected_identity']
    _require(type(hint) is dict and all(k in record and record[k] == v for k, v in hint.items()),
             'REQUEST_IDENTITY_HINT_CONFLICT')
    verified['trusted_identity'] = {k: record[k] for k in ('run_id', 'attempt_id',
        'physical_environment_id', 'policy', 'target_cut_tick', 'maximum_completed_steps',
        'output_path', 'source_manifest_digest', 'runtime_identity', 'stop_rule')}
    return verified


class RestrictedWorkerBackend:
    """Token/permission preflight; authenticated science bootstrap is NOT ready.

    The instance-only restricted-create adapter exists separately. A trusted
    parent/child channel and enforced Python/DLL closure are still missing and
    cannot be substituted by CLI/environment credentials or this class's label.
    """
    def __init__(self, authority, request):
        self.authority, self.request = authority, request
        self.worker_token = None
        self.token_evidence = None

    def preflight(self):
        from research.non_oracle.stfbs_lite_real_d60_windows_boundary import (
            inspect_snapshot, inspect_protected_store)
        context = self.authority.execution_context
        _require(type(context) is dict, 'TRUSTED_WINDOWS_CONTEXT_REQUIRED')
        from research.non_oracle.stfbs_lite_real_d60_restricted_create import acquire_worker_token
        self.worker_token, self.token_evidence = acquire_worker_token(context)
        inspect_protected_store(self.authority.consumption_directory, context, worker_token=self.worker_token)
        evidence = inspect_snapshot(context['snapshot_root'], context['snapshot_layout'],
                                    self.request['source_manifest'], context, worker_token=self.worker_token)
        _require(evidence['source_execution'] == 'SOURCE_EXECUTION_ISOLATED', 'SOURCE_PREFLIGHT_NOT_READY')
        raise AdmissionRejected('RESTRICTED_WORKER_TOKEN_AND_AUTHENTICATED_JOB_BOOTSTRAP_NOT_READY')

    def run_monitored(self, verified, consumption):
        raise AdmissionRejected('RESTRICTED_WORKER_TOKEN_AND_AUTHENTICATED_JOB_BOOTSTRAP_NOT_READY')

    def close(self):
        if self.worker_token is not None:
            from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API
            handle, self.worker_token = self.worker_token, None
            API().close(handle)


def _execute_verified_attempt(verified, authority, backend):
    """Ordering contract; production constructs its backend, not the request.

    Preflight must fail BEFORE consumption on the current deployment backend.
    Tests may supply an artificial backend; that is no production capability.
    Any error after consume leaves the tombstone and index intact.
    """
    from research.non_oracle.stfbs_lite_real_d60_consume_store import protected_consume
    primary = None
    try:
        backend.preflight()
        token = getattr(backend, 'worker_token', None)
        consumption = (protected_consume(verified, authority) if token is None else
                       protected_consume(verified, authority, worker_token=token))
        return backend.run_monitored(verified, consumption)
    except BaseException as exc:
        primary = exc
        raise
    finally:
        close = getattr(backend, 'close', None)
        if close is not None:
            try:
                close()
            except BaseException as cleanup:
                if primary is None:
                    raise
                backend.token_cleanup_error = str(cleanup)
                note = getattr(primary, 'add_note', None)
                if note is not None:
                    note('Worker-token cleanup failed: ' + str(cleanup))


def launch_protected_run(request_path):
    """Parent-only chain. The unfinished isolation gate prevents worker launch."""
    authority = load_production_authority()  # Fixed root; never request-supplied.
    request = read_json(request_path)
    verified = verify_trusted_request(request, authority,
                                     now=int(datetime.now(timezone.utc).timestamp()))
    record = verified['record']
    root = Path(request['repository']).resolve()
    _require(root == Path(__file__).resolve().parents[2], 'EXECUTING_REPOSITORY_CONFLICT')
    actual_head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    _require(record['approved_source_identity'] == {'git_head': actual_head, 'repository': str(root)},
             'APPROVED_EXECUTION_SOURCE_IDENTITY_CONFLICT')
    _require(record['source_manifest_digest'] == content_digest(request['source_manifest']), 'PERMIT_SOURCE_CONFLICT')
    _require(record['input_digests'] == {p: request['source_manifest'][p] for p in request['input_paths']},
             'PERMIT_INPUT_CONFLICT')
    _require(record['runtime_identity'] == {p: request['source_manifest'][p] for p in request['runtime_paths']},
             'PERMIT_RUNTIME_CONFLICT')
    isolation = source_execution_preflight(request['source_manifest'], repository=request['repository'],
                                          input_paths=request['input_paths'], runtime_paths=request['runtime_paths'])
    _require(isolation['source_bytes'] == 'SOURCE_BYTES_VERIFIED', 'SOURCE_PREFLIGHT_NOT_READY')
    # No request-supplied backend, token, worker command or approval flag.
    return _execute_verified_attempt(verified, authority, RestrictedWorkerBackend(authority, request))


def supervised_worker_call(verified, *, argv, repository, log, supervisor_factory=None):
    """Wiring seam only; no public caller can turn a verified dict into authority.

    Actual worker launch remains denied until the isolation/store contract is
    implemented. Retain the precise protected call below for that integration.
    """
    _require(False, 'PROTECTED_WORKER_BOOTSTRAP_NOT_READY')
    from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor
    factory = WindowsSupervisor if supervisor_factory is None else supervisor_factory
    with factory(wall_seconds=verified['budget']['wall_seconds'],
                 total_cpu_seconds=verified['record']['cpu_limit']['seconds'],
                 attempt_identity=verified['record']['attempt_id']) as supervisor:
        return supervisor.run_monitored(argv, cwd=repository, log=log)


def validate_success_receipt(result, record, disposition, *, attempt_id):
    """Resource success contract, not permit authentication or RUN admission."""
    _require(type(record) is dict and record.get('attempt_id') == attempt_id
             and result.get('attempt_identity') == attempt_id, 'RESOURCE_ATTEMPT_IDENTITY_CONFLICT')
    budget = validate_budget(record, disposition)
    _require(result.get('execution_entry') == 'RUN_MONITORED'
             and result.get('cpu_semantics') == 'TOTAL_CPU_SECONDS'
             and result.get('cpu_scope') == 'WHOLE_JOB', 'PROTECTED_TOTAL_CPU_ENTRY_REQUIRED')
    _require(result.get('job_cleanup_status') == 'PASS'
             and result.get('process_tree_status') == 'PROCESS_TREE_EXIT_CONFIRMED'
             and type(result.get('active_processes_final')) is int
             and result['active_processes_final'] == 0, 'PROCESS_TREE_CLEANUP_NOT_CONFIRMED')
    _require(result.get('accounting_status') == 'FINAL_VALID'
             and result.get('evidence_completeness_status') == 'COMPLETE_IN_MEMORY'
             and result.get('errors') == [], 'RESOURCE_AUDIT_INCOMPLETE')
    _require(type(result.get('worker_exit_status')) is int and result['worker_exit_status'] == 0,
             'WORKER_SUCCESS_EXIT_REQUIRED')
    values = [result.get(k) for k in ('total_user_ticks', 'total_kernel_ticks', 'final_cpu_ticks')]
    _require(all(type(v) is int and v >= 0 for v in values), 'FINAL_CPU_ACCOUNTING_MISSING')
    _require(type(result.get('total_cpu_ticks')) is int
             and values[0] + values[1] == values[2] == result['total_cpu_ticks'], 'FINAL_CPU_ACCOUNTING_CONFLICT')
    accounting = result.get('accounting')
    _require(type(accounting) is dict and accounting.get('TotalUserTime') == values[0]
             and accounting.get('TotalKernelTime') == values[1] and accounting.get('ActiveProcesses') == 0,
             'JOB_ACCOUNTING_CONFLICT')
    _require(result.get('cpu_limit_ticks') == budget['total_cpu_ticks']
             and result.get('wall_limit_seconds') == budget['wall_seconds'], 'RESOURCE_LIMIT_IDENTITY_CONFLICT')
    _require(result.get('cpu_overshoot_ticks') == max(0, values[2] - budget['total_cpu_ticks']),
             'CPU_OVERSHOOT_AUDIT_CONFLICT')
    _require(values[2] <= budget['total_cpu_ticks'] and result.get('stop_reason') == 'NATURAL_EXIT'
             and result.get('termination_requested') is False, 'PRODUCTION_RESOURCE_DISPOSITION_REJECTED')
    try:
        wall = _seconds(result.get('wall_elapsed_at_tree_exit'))
    except ValueError as exc:
        raise AdmissionRejected('FINAL_WALL_ACCOUNTING_MISSING') from exc
    _require(wall <= budget['wall_seconds'], 'PRODUCTION_WALL_DISPOSITION_REJECTED')
    _require(type(result.get('supervisor_cpu_ticks')) is int and result['supervisor_cpu_ticks'] >= 0,
             'SUPERVISOR_CPU_AUDIT_MISSING')
    _require('EXCLUDED_FROM_JOB' in result.get('supervisor_cpu_scope', '')
             and result.get('supervisor_cpu_window_start') == 'BEFORE_WORKER_CREATION'
             and result.get('supervisor_cpu_window_end') == 'RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE',
             'SUPERVISOR_CPU_SCOPE_CONFLICT')
    return budget


def finalize_run_evidence(supervisor, *, worker_journal, receipt_path, failure_path, verified):
    """Parent success/failure split. Failure evidence never restores an attempt."""
    from research.non_oracle.stfbs_lite_real_d60_source import persist_supervisor_receipt
    _require(supervisor.result is not None and supervisor.closed, 'SUPERVISOR_FINAL_CLEANUP_REQUIRED')
    try:
        receipt = persist_supervisor_receipt(worker_journal, receipt_path,
                    attempt_id=verified['record']['attempt_id'], result=supervisor.result,
                    max_bytes=verified['budget']['storage_limit'], permit_record=verified['record'],
                    resource_disposition=verified['budget']['disposition'])
    except Exception as exc:
        try:
            saved = supervisor.save_failure_evidence(failure_path)
        except Exception as failure:
            saved = dict(saved=False, status='INCOMPLETE', error=str(failure))
        return dict(status='FAIL_OR_INCOMPLETE', success_error=str(exc), failure_evidence=saved,
                    retry_authorized=False, production_admission='BLOCKED')
    return dict(status='RESOURCE_RECEIPT_PERSISTED_NOT_RUN_ADMISSION', receipt=receipt,
                retry_authorized=False, production_admission='BLOCKED')
