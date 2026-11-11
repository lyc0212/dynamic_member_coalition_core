"""ENG-only D60 orchestration, session expectations and budget guard contracts.

No real permit issuer or hard process-tree supervisor is implemented here.
Production admission always fails before environment creation/imported science.
"""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import threading

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
    """No Boolean/string/dict/legacy permit can launch production in ENG V1."""
    return dict(status='RUN_ADMISSION_BLOCKED', hard_time_guard='RUN_HARD_TIME_GUARD_NOT_READY',
                reason='INDEPENDENT_RUN_ISSUER_AND_VERIFIED_PROCESS_TREE_SUPERVISOR_NOT_CONFIGURED')


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
    root = Path(repository).resolve()
    for relative, sha, role in expected.file_pins:
        path = (root/relative).resolve()
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

    A production dispatcher is deliberately not connected while hard supervisor
    and independent permit issuance remain unimplemented.
    """
    admission = check_run_admission(permit, expectations=expectations, supervisor=supervisor)
    raise AdmissionRejected(admission['reason'])
