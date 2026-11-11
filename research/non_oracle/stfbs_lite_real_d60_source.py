"""D60 orchestration and durable audits; unresolved RUN gates fail closed.

Signed-permit software and protected supervision are separate from actual trust
provisioning, source execution isolation and formal production approvals.
"""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import threading
import os

CATEGORIES = ('ACTUAL_POLICY_WLS', 'ACTUAL_OBSERVATION_WLS', 'ACTUAL_SOLVER_START')
_ACTIVE = threading.Lock()


class AdmissionRejected(RuntimeError):
    pass


def _require(condition, code):
    if not condition:
        raise AdmissionRejected(code)


def content_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def check_run_admission(permit=None, *, expectations=None, supervisor=None):
    """Legacy in-process calls cannot grant production authority."""
    from research.non_oracle.stfbs_lite_real_d60_run_gates import gate_status
    return gate_status()


@dataclass(frozen=True)
class SessionExpectations:
    """Pre-run external expectations; not a real authentication capability."""
    manifest_json: str
    file_pins: tuple


def verify_session_expectations(expected, *, repository, observed):
    _require(type(expected) is SessionExpectations, 'EXTERNAL_EXPECTATIONS_REQUIRED')
    wanted = json.loads(expected.manifest_json)
    fields = {'git_head', 'run_id', 'attempt_id', 'physical_environment_id', 'output_directory',
              'target_tick', 'cut_phase', 'python_identity', 'runtime_dependencies', 'budget',
              'permit_identity', 'supervisor_identity'}
    _require(set(wanted) == fields and observed == wanted, 'SESSION_IDENTITY_CONFLICT')
    _require(wanted['target_tick'] == 60 and wanted['cut_phase'] == 'POST_FREEZE_PRE_ASSIGNMENT', 'SESSION_CUT_CONFLICT')
    roles = set()
    seen = set()
    root = Path(repository).resolve()
    for relative, sha, role in expected.file_pins:
        path = (root/relative).resolve()
        _require(path not in seen, 'DUPLICATE_SOURCE_PIN_PATH')
        seen.add(path)
        _require(path.is_relative_to(root), 'SOURCE_PATH_OUTSIDE_REPOSITORY')
        _require(hashlib.sha256(path.read_bytes()).hexdigest() == sha, 'PREDECLARED_SOURCE_BYTES_CONFLICT')
        roles.add(role)
    _require({'PRODUCTION', 'ENG', 'INPUT', 'DEPENDENCY'} <= roles, 'SOURCE_PIN_COVERAGE_INCOMPLETE')
    _require(all(wanted[k] for k in ('budget', 'python_identity', 'runtime_dependencies', 'permit_identity', 'supervisor_identity')),
             'SESSION_EXPECTATIONS_INCOMPLETE')
    return dict(status='TEST_DOUBLE_SESSION_EXPECTATIONS_MATCH', real_source_authentication='NOT_VERIFIED')


class ResourceLedger:
    """Pre-count irreversible STARTED charges; test quotas are not RUN quotas."""
    def __init__(self, limits):
        _require(set(limits) == set(CATEGORIES) and all(type(v) is int and v >= 0 for v in limits.values()),
                 'INCOMPLETE_WLS_BUDGET')
        self.limits = dict(limits)
        self.counts = {k: 0 for k in CATEGORIES}
        self.events = []
        self.outer = None
        self.integrity_check = lambda: None

    def invoke(self, category, fn, *args, **kwargs):
        self.integrity_check()
        is_solver = category == 'ACTUAL_SOLVER_START'
        _require(category in self.counts, 'UNCLASSIFIED_CALL')
        if (is_solver and self.outer is None) or (not is_solver and self.outer is not None):
            self.events.append(dict(category=category, status='REJECTED', reason='INVALID_CALL_NESTING'))
            raise AdmissionRejected('INVALID_CALL_NESTING')
        if self.counts[category] >= self.limits[category]:
            self.events.append(dict(category=category, status='REJECTED', reason='BUDGET_EXHAUSTED'))
            raise AdmissionRejected('BUDGET_EXHAUSTED')
        self.counts[category] += 1
        self.events.append(dict(category=category, status='STARTED', ordinal=self.counts[category]))
        if not is_solver:
            self.outer = category
        try:
            result = fn(*args, **kwargs)
            self.integrity_check()
        except BaseException:
            self.events.append(dict(category=category, status='FAILED'))
            raise
        else:
            self.events.append(dict(category=category, status='RETURNED'))
            return result
        finally:
            if not is_solver:
                self.outer = None


def inspect_production_aliases(*, processors=()):
    """Read production bindings without invoking any estimator or processor.

    Covers the known production call graph and explicitly supplied instances;
    not an assertion about arbitrary external closures holding old callables.
    """
    from research.non_oracle import policy
    from research.information_service_bridge import public_stream
    from research.cooperative_sensing import estimator
    from scipy import optimize
    _require(policy.estimate is estimator.estimate, 'UNKNOWN_POLICY_ESTIMATOR_ALIAS')
    _require(estimator.least_squares is optimize.least_squares, 'UNKNOWN_SOLVER_ALIAS')
    _require(all(p.estimator_fn is public_stream._estimate for p in processors), 'UNKNOWN_PROCESSOR_ESTIMATOR_ALIAS')
    return dict(status='KNOWN_PRODUCTION_ALIAS_LAYOUT_MATCH',
                instance_scope='EXPLICITLY_SUPPLIED_PROCESSORS_ONLY', real_run_admission='BLOCKED')


@contextmanager
def guard_wls_bindings(ledger, *, policy, bridge, estimator, processors=(), aliases=()):
    """Scoped hooks for the three specified slots and declared bound aliases.

    ENG exercises these with test doubles only. Arbitrary undeclared Python
    aliases cannot be proven absent: real RUN admission remains closed.
    """
    _require(_ACTIVE.acquire(blocking=False), 'CONCURRENT_GUARD_CONFLICT')
    original, installed = [], []
    try:
        slots = [(policy, 'estimate', 'ACTUAL_POLICY_WLS'),
                 (bridge, '_estimate', 'ACTUAL_OBSERVATION_WLS'),
                 (estimator, 'least_squares', 'ACTUAL_SOLVER_START')]
        policy_original, observation_original = policy.estimate, bridge._estimate
        for processor in processors:
            _require(processor.estimator_fn is observation_original, 'UNKNOWN_PROCESSOR_ESTIMATOR_ALIAS')
            slots.append((processor, 'estimator_fn', 'ACTUAL_OBSERVATION_WLS'))
        for owner, name, expected, category in aliases:
            _require(category in CATEGORIES and getattr(owner, name) is expected, 'UNKNOWN_ESTIMATOR_ALIAS')
            canonical = {'ACTUAL_POLICY_WLS': policy_original, 'ACTUAL_OBSERVATION_WLS': observation_original,
                         'ACTUAL_SOLVER_START': estimator.least_squares}[category]
            _require(expected is canonical, 'UNKNOWN_ESTIMATOR_ALIAS')
            slots.append((owner, name, category))
        _require(len({(id(o), n) for o, n, _ in slots}) == len(slots), 'DUPLICATE_HOOK_SLOT')

        def intact():
            _require(all(getattr(o, n) is wrapper for o, n, wrapper in installed), 'WLS_BINDING_TAMPERED')

        for owner, name, category in slots:
            fn = getattr(owner, name)
            original.append((owner, name, fn))
            def wrapped(*args, _fn=fn, _category=category, **kwargs):
                return ledger.invoke(_category, _fn, *args, **kwargs)
            setattr(owner, name, wrapped)
            installed.append((owner, name, wrapped))
        ledger.integrity_check = intact
        yield ledger
        intact()
    finally:
        for owner, name, fn in reversed(original):
            setattr(owner, name, fn)
        ledger.integrity_check = lambda: None
        _ACTIVE.release()


class StorageContract:
    """Pre-write reservation and durable-record contract, not a disk quota."""
    def __init__(self, max_bytes):
        _require(type(max_bytes) is int and max_bytes >= 0, 'INVALID_STORAGE_LIMIT')
        self.limit, self.reserved = max_bytes, 0

    def reserve(self, size):
        _require(type(size) is int and 0 <= size <= self.limit-self.reserved, 'OUTPUT_STORAGE_LIMIT')
        self.reserved += size


def verify_bound_output(record, *, expected_digest):
    _require(content_digest(record) == expected_digest, 'OUTPUT_IDENTITY_CONFLICT')
    return 'TEST_DOUBLE_OUTPUT_BINDING_MATCH'


def exercise_d60_sequence(port):
    """Engineering port only. Never promotes a port label to real admission."""
    _require(getattr(port, 'evidence_kind', None) == 'TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE', 'TEST_DOUBLE_REQUIRED')
    events = []
    for tick in (0, 20, 40):
        _require(port.tick == tick, 'DRIVER_CUT_ORDER_CONFLICT')
        view = port.prepare_decision()
        _require(view['tick'] == tick, 'DRIVER_VIEW_TICK_CONFLICT')
        choice = port.decide(view, 'R')
        result = port.step(choice['actions'], tick)
        _require(result['status'] == 'COMMITTED' and port.tick == tick+20, 'DRIVER_STEP_CONFLICT')
        events.append(dict(tick=tick, completed_tick=port.tick))
    view = port.prepare_decision()
    _require(port.tick == view['tick'] == 60, 'DRIVER_D60_CONFLICT')
    cut = port.capture(view)
    _require(cut['status'] == 'LIVE_CUT_STRUCTURAL_CAPTURE_PASS', 'DRIVER_CAPTURE_FAILED')
    candidate = port.map_candidate(cut)
    _require(candidate['candidate_status'] == 'MODEL_INITIALIZATION_CANDIDATE_READY'
             and candidate['execution_admission'] == 'MODEL_EXECUTION_ADMISSION_DENIED', 'DRIVER_CANDIDATE_CONFLICT')
    return dict(status='REAL_D60_CAPTURE_DRIVER_ENG_PASS', evidence_kind='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE',
                events=events, candidate=candidate, real_actual_capture='NOT_RUN',
                source_session_binding='NOT_VERIFIED', real_source_authentication='NOT_VERIFIED')


def run_real_d60(*, permit=None, expectations=None, supervisor=None):
    """Gate before constructing StaggeredEnvironment or invoking any science.

    In-process dispatch is not a protected worker admission capability.
    """
    admission = check_run_admission(permit, expectations=expectations, supervisor=supervisor)
    raise AdmissionRejected(admission['reason'])


# Explicit path coverage replaces role-label counting for new RUN admission.
REQUIRED_SOURCE_PATHS = frozenset((
    'research/non_oracle/environment.py', 'research/non_oracle/belief.py', 'research/non_oracle/policy.py',
    'research/information_service_online/execution.py', 'research/cooperative_sensing/estimator.py',
    'research/information_service_bridge/public_stream.py', 'research/information_service/public_quality.py',
    'research/information_service/common.py', 'research/information_service_online/public.py',
    'research/information_service_online/common.py', 'research/information_service_online/evaluator.py',
    'research/quality_allocation/certified_solver.py', 'pursuit_v2/observation_geometry.py',
    'pursuit_v2/service.py', 'pursuit_v2/types.py', 'pursuit_v2/config.py',
    'scripts/gq_windows/a0_plans.py', 'scripts/run_a1.py',
    'research/non_oracle/stfbs_lite_real_d60_source.py',
    'research/non_oracle/stfbs_lite_real_d60_run_gates.py',
    'research/non_oracle/stfbs_lite_real_d60_windows_boundary.py',
    'research/non_oracle/stfbs_lite_real_d60_restricted_create.py',
    'research/non_oracle/stfbs_lite_real_d60_consume_store.py',
    'scripts/check_stfbs_lite_real_d60_deployment.py',
    'research/non_oracle/stfbs_lite_real_d60_supervisor_win.py', 'scripts/run_stfbs_lite_real_d60.py',
    'research/non_oracle/stfbs_lite_live_cut.py', 'research/non_oracle/stfbs_lite_real_cut_to_model.py',
    'research/quality_allocation/service_m3_benchmarks/windows_job_monitor/api.py'))


def verify_source_manifest(manifest, *, repository, input_paths, runtime_paths):
    """Verify exact expected paths/bytes, without claiming post-check isolation."""
    _require(len(input_paths) == 2 and len(set(input_paths)) == 2, 'WORLD_AND_PUBLIC_INPUT_REQUIRED')
    required = REQUIRED_SOURCE_PATHS | set(input_paths) | set(runtime_paths)
    _require(set(manifest) == required and len(runtime_paths) >= 3, 'REQUIRED_SOURCE_PATHS_MISSING')
    root = Path(repository).resolve()
    for name, sha in manifest.items():
        path = Path(name) if Path(name).is_absolute() else root/name
        _require(hashlib.sha256(path.read_bytes()).hexdigest() == sha, 'SOURCE_BYTES_CHANGED')
    return dict(status='SOURCE_EXPECTATION_BYTES_MATCH', source_preflight='SOURCE_PREFLIGHT_NOT_READY',
                reason='NO_VERIFIED_READ_ONLY_RUNTIME_AND_LOADED_MODULE_TOCTOU_ISOLATION')


PERMIT_FIELDS = frozenset(('task_id', 'approved_source_identity', 'run_id', 'attempt_id',
    'physical_environment_id', 'policy', 'target_cut_tick', 'maximum_completed_steps',
    'source_manifest_digest', 'input_digests', 'runtime_identity', 'output_path',
    'policy_wls_limit', 'observation_wls_limit', 'solver_start_limit', 'cpu_limit', 'wall_limit',
    'storage_limit', 'stop_rule'))


def verify_permit_record(record, *, independent_expected_digest, expected_identity):
    """Verifier contract only. Caller expectations are not a permit issuer."""
    _require(type(record) is dict and set(record) == PERMIT_FIELDS, 'PERMIT_FIELDS_INVALID')
    _require(content_digest(record) == independent_expected_digest, 'PERMIT_DIGEST_CONFLICT')
    _require(all(record[k] == v for k, v in expected_identity.items()), 'PERMIT_IDENTITY_CONFLICT')
    _require(record['task_id'] == 'STFBS_LITE_REAL_D60' and record['policy'] == 'R'
             and record['target_cut_tick'] == 60 and record['maximum_completed_steps'] == 3
             and record['stop_rule'] == 'POST_FREEZE_PRE_ASSIGNMENT_D60', 'PERMIT_SCOPE_INVALID')
    _require(all(type(record[k]) is int and record[k] > 0 for k in
                 ('policy_wls_limit','observation_wls_limit','solver_start_limit','storage_limit')), 'PERMIT_BUDGET_INVALID')
    _require(record['cpu_limit']['semantics'] in ('JOB_USER_SECONDS','TOTAL_CPU_SECONDS')
             and record['cpu_limit']['seconds'] > 0 and record['wall_limit'] > 0, 'PERMIT_TIME_BUDGET_INVALID')
    return dict(status='PERMIT_RECORD_INTERFACE_VERIFIED', provider='RUN_PERMIT_PROVIDER_NOT_READY',
                admission='RUN_ADMISSION_BLOCKED')


class DurableJournal:
    """Single-writer exclusive file, chained JSONL, flush/fsync before return.

    Failed writes stop the attempt; incomplete last lines are never repaired.
    This journal is not an independent authenticity or OS storage quota service.
    """
    def __init__(self, path, *, attempt_id, max_bytes):
        self.path = Path(path)
        self.file = self.path.open('x+b')
        self.identity = (os.fstat(self.file.fileno()).st_dev, os.fstat(self.file.fileno()).st_ino)
        self.attempt_id, self.limit, self.sequence, self.previous = attempt_id, max_bytes, 0, None
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.bytes_digest = hashlib.sha256(b'').digest()

    def append(self, event):
        _require(os.getpid() == self.pid and threading.get_ident() == self.thread, 'JOURNAL_WRITER_CONFLICT')
        stat = self.path.stat()
        _require((stat.st_dev, stat.st_ino) == self.identity and stat.st_size == self.file.tell(), 'JOURNAL_FILE_REPLACED_OR_MODIFIED')
        self.file.seek(0)
        old = self.file.read()
        self.file.seek(0,os.SEEK_END)
        _require(hashlib.sha256(old).digest() == self.bytes_digest, 'JOURNAL_EXISTING_BYTES_CHANGED')
        row = dict(attempt_id=self.attempt_id, sequence=self.sequence+1, previous=self.previous, event=deepcopy(event))
        row['digest'] = content_digest(row)
        encoded = (json.dumps(row,sort_keys=True,separators=(',',':'))+'\n').encode()
        _require(stat.st_size+len(encoded) <= self.limit, 'OUTPUT_STORAGE_LIMIT')
        self.file.write(encoded)
        self.file.flush()
        os.fsync(self.file.fileno())
        self.bytes_digest = hashlib.sha256(old+encoded).digest()
        self.sequence, self.previous = row['sequence'], row['digest']
        return row

    def close(self):
        self.file.close()


def read_durable_journal(path, *, attempt_id):
    raw = Path(path).read_bytes()
    _require(raw and raw.endswith(b'\n'), 'JOURNAL_MISSING_OR_TRUNCATED')
    rows, previous = [], None
    for index, line in enumerate(raw.splitlines(),1):
        row = json.loads(line)
        _require(row['attempt_id'] == attempt_id and row['sequence'] == index and row['previous'] == previous
                 and row['digest'] == content_digest({k:v for k,v in row.items() if k!='digest'}), 'JOURNAL_INTEGRITY_CONFLICT')
        previous = row['digest']; rows.append(row)
    return rows


class DurableResourceLedger(ResourceLedger):
    def __init__(self, limits, journal):
        super().__init__(limits)
        self.journal = journal

    def invoke(self, category, fn, *args, **kwargs):
        before = dict(self.counts)
        call_id = f'{os.getpid()}:{self.journal.sequence+1}'
        def expensive():
            self.journal.append(dict(kind='WLS', status='STARTED', category=category, call_id=call_id,
                                     budget_before=before, budget_after=dict(self.counts)))
            try:
                result = fn(*args, **kwargs)
            except BaseException:
                self.journal.append(dict(kind='WLS',status='FAILED',category=category,call_id=call_id,
                                         budget_before=before,budget_after=dict(self.counts)))
                raise
            self.journal.append(dict(kind='WLS',status='RETURNED',category=category,call_id=call_id,
                                     budget_before=before,budget_after=dict(self.counts)))
            return result
        try:
            return super().invoke(category, expensive)
        except AdmissionRejected:
            self.journal.append(dict(kind='WLS',status='REJECTED',category=category,call_id=call_id,
                                     budget_before=before,budget_after=dict(self.counts)))
            raise


def inspect_attempt_journal(rows):
    started, finished, complete, checkpoint, transaction = {}, set(), None, None, None
    durable_result = None
    for row in rows:
        e = row['event']
        if e['kind'] == 'WLS':
            if e['status'] == 'STARTED': started[e['call_id']] = e
            elif e['status'] in ('RETURNED','FAILED'): finished.add(e['call_id'])
        elif e['kind'] == 'STEP_REQUEST':
            _require(transaction is None, 'OVERLAPPING_STEP_REQUEST')
            transaction = e['tick']; durable_result = None
        elif e['kind'] == 'STEP_RESULT':
            r = e['result']
            _require(transaction == r['start_tick'] and r['status'] == 'COMMITTED'
                     and r['end_tick'] == transaction+20 and r['checkpoint_after']['tick'] == r['end_tick'], 'INVALID_DURABLE_STEP_RESULT')
            durable_result = r
        elif e['kind'] == 'STEP_COMPLETE':
            _require(transaction == e['start_tick'] and durable_result is not None
                     and e['end_tick'] == durable_result['end_tick']
                     and e['checkpoint_id'] == durable_result['checkpoint_after']['checkpoint_id'], 'STEP_COMPLETION_WITHOUT_DURABLE_RESULT')
            complete, checkpoint, transaction = e['end_tick'], e['checkpoint_id'], None
    return dict(last_complete_step=complete,last_durable_checkpoint=checkpoint,
                incomplete_transaction=transaction, started_calls=len(started),
                unfinished_calls=sorted(set(started)-finished))


def _dispatch_d60(env, *, decide, capture, map_candidate, journal):
    """Production four-argument STEP contract; caller must pass full RUN gates."""
    for tick in (0,20,40):
        _require(env.tick == tick, 'DISPATCH_TICK_CONFLICT')
        view = env.prepare_decision()
        choice = decide(view, 'R')
        checkpoint_id = env.observe_public()['checkpoint_id']
        request_id = f'{journal.attempt_id}:D{tick}'
        journal.append(dict(kind='STEP_REQUEST',tick=tick,checkpoint_id=checkpoint_id,request_id=request_id))
        def on_commit(frame): journal.append(dict(kind='STEP_FRAME',frame=frame))
        result = env.step(choice['actions'], checkpoint_id, tick, request_id, on_commit=on_commit)
        _require(result['status'] == 'COMMITTED' and result['start_tick'] == tick
                 and result['end_tick'] == tick+20 and result['checkpoint_after']['tick'] == tick+20, 'STEP_NOT_COMPLETE')
        journal.append(dict(kind='STEP_RESULT',result=result))
        # Independently re-read durable bytes before issuing the completion mark.
        inspect_attempt_journal(read_durable_journal(journal.path,attempt_id=journal.attempt_id))
        journal.append(dict(kind='STEP_COMPLETE',start_tick=tick,end_tick=tick+20,
                            checkpoint_id=result['checkpoint_after']['checkpoint_id']))
    _require(env.tick == 60, 'DISPATCH_D60_CONFLICT')
    view = env.prepare_decision()
    cut = capture(env,view)
    _require(cut['status'] == 'LIVE_CUT_STRUCTURAL_CAPTURE_PASS','CAPTURE_FAILED')
    candidate = map_candidate(cut)
    _require(candidate['execution_admission'] == 'MODEL_EXECUTION_ADMISSION_DENIED','MODEL_ADMISSION_CONFLICT')
    journal.append(dict(kind='D60_CANDIDATE',cut=cut,candidate=candidate))
    return candidate


def production_dispatcher(*, permit=None, expectations=None, supervisor=None, journal=None, world=None, announcements=None):
    # Independent permit provider and source TOCTOU isolation are still absent.
    admission = check_run_admission(permit,expectations=expectations,supervisor=supervisor)
    _require(admission['status'] == 'RUN_ADMISSION_GRANTED', 'RUN_ADMISSION_BLOCKED')
    from research.non_oracle.environment import StaggeredEnvironment
    from scripts.run_a1 import Sensing
    from research.non_oracle.policy import decide
    from research.non_oracle.stfbs_lite_live_cut import capture_live_cut
    from research.non_oracle.stfbs_lite_real_cut_to_model import prepare_real_cut_model_input
    from research.non_oracle import policy
    from research.information_service_bridge import public_stream
    from research.cooperative_sensing import estimator
    # Unreachable until separately authorized provider/source gates are completed.
    inspect_production_aliases()
    ledger = DurableResourceLedger(dict(zip(CATEGORIES,(permit['policy_wls_limit'],permit['observation_wls_limit'],permit['solver_start_limit']))),journal)
    with guard_wls_bindings(ledger,policy=policy,bridge=public_stream,estimator=estimator):
        env = StaggeredEnvironment(world,Sensing(),permit['physical_environment_id'],announcements)
        return _dispatch_d60(env,decide=decide,capture=capture_live_cut,map_candidate=prepare_real_cut_model_input,journal=journal)


def persist_supervisor_receipt(worker_journal, receipt_path, *, attempt_id, result, max_bytes,
                               permit_record=None, resource_disposition=None):
    """Parent-side audit after Job cleanup; never authorizes retry/resume."""
    _require(result['job_cleanup_status'] == 'PASS', 'PROCESS_TREE_CLEANUP_NOT_CONFIRMED')
    from research.non_oracle.stfbs_lite_real_d60_run_gates import validate_success_receipt
    budget = validate_success_receipt(result, permit_record, resource_disposition, attempt_id=attempt_id)
    _require(type(max_bytes) is int and 0 < max_bytes <= budget['storage_limit'], 'RECEIPT_STORAGE_LIMIT_CONFLICT')
    rows = read_durable_journal(worker_journal,attempt_id=attempt_id)
    boundary = inspect_attempt_journal(rows)
    _require(boundary['last_complete_step'] == 60 and boundary['incomplete_transaction'] is None
             and not boundary['unfinished_calls'], 'SUCCESS_REQUIRES_COMPLETE_D60_AUDIT')
    _require(any(r['event']['kind'] == 'D60_CANDIDATE'
                 and r['event'].get('candidate', {}).get('execution_admission') == 'MODEL_EXECUTION_ADMISSION_DENIED'
                 for r in rows), 'D60_CAPTURE_EVIDENCE_MISSING')
    counts, started, finished = {k: 0 for k in CATEGORIES}, {}, set()
    for row in rows:
        event = row['event']
        if event['kind'] != 'WLS':
            continue
        category, call = event['category'], event['call_id']
        _require(category in counts, 'UNKNOWN_DURABLE_RESOURCE_CATEGORY')
        if event['status'] == 'STARTED':
            _require(call not in started, 'DUPLICATE_DURABLE_CALL')
            counts[category] += 1
            _require(counts[category] <= budget['wls_limits'][category], 'DURABLE_BUDGET_EXCEEDED')
            started[call] = category
        else:
            _require(event['status'] == 'RETURNED' and call in started and call not in finished
                     and started[call] == category, 'FAILED_OR_CONFLICTING_DURABLE_CALL')
            finished.add(call)
    _require(set(started) == finished, 'UNFINISHED_DURABLE_CALLS')
    boundary['journal_status'] = 'VERIFIED'
    receipt = dict(result,**boundary, retry_authorized=False, attempt_id=attempt_id)
    journal=DurableJournal(receipt_path,attempt_id=attempt_id,max_bytes=max_bytes)
    try: journal.append(dict(kind='SUPERVISOR_RECEIPT',receipt=receipt))
    finally: journal.close()
    return receipt
