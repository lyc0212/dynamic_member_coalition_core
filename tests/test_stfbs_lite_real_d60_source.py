"""ENG test doubles only. No real WLS, ACTUAL or MODEL invocation."""
from types import SimpleNamespace
import json
import hashlib
from pathlib import Path

import pytest

from research.non_oracle import stfbs_lite_real_d60_source as eng
from scripts import run_stfbs_lite_real_d60 as entry


def test_real_entry_always_rejects_before_science():
    for permit in (None, True, 'RUN-G1', {'authorized': True}, object()):
        assert eng.check_run_admission(permit)['status'] == 'RUN_ADMISSION_BLOCKED'
        with pytest.raises(eng.AdmissionRejected): eng.run_real_d60(permit=permit)
    assert entry.main() == 2


class Port:
    evidence_kind = 'TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'
    def __init__(self): self.tick, self.calls = 0, []
    def prepare_decision(self):
        self.calls.append(('freeze', self.tick)); return dict(tick=self.tick)
    def decide(self, view, mode):
        self.calls.append(('decide', self.tick, mode)); return dict(actions=[])
    def step(self, actions, tick):
        self.calls.append(('step', tick)); self.tick += 20; return dict(status='COMMITTED')
    def capture(self, view):
        self.calls.append(('capture', self.tick)); return dict(status='LIVE_CUT_STRUCTURAL_CAPTURE_PASS')
    def map_candidate(self, cut):
        self.calls.append(('map', self.tick)); return dict(candidate_status='MODEL_INITIALIZATION_CANDIDATE_READY',
                                                        execution_admission='MODEL_EXECUTION_ADMISSION_DENIED')


def test_d60_order_and_stop_without_current_assignment():
    port = Port()
    out = eng.exercise_d60_sequence(port)
    assert port.calls == [(name, tick, 'R') if name == 'decide' else (name, tick)
        for tick in (0,20,40) for name in ('freeze','decide','step')]+[('freeze',60),('capture',60),('map',60)]
    assert port.tick == 60 and out['real_actual_capture'] == 'NOT_RUN'
    assert out['source_session_binding'] == 'NOT_VERIFIED'
    with pytest.raises(eng.AdmissionRejected): eng.exercise_d60_sequence(port)


def hooks():
    solver = SimpleNamespace(least_squares=lambda: 7)
    policy = SimpleNamespace(estimate=lambda: solver.least_squares())
    bridge = SimpleNamespace(_estimate=lambda: solver.least_squares())
    processor = SimpleNamespace(estimator_fn=bridge._estimate)
    alias = SimpleNamespace(estimate=policy.estimate)
    return policy, bridge, solver, processor, alias


def test_three_entries_bound_aliases_and_restore():
    p,b,s,processor,alias = hooks()
    originals = (p.estimate,b._estimate,s.least_squares,processor.estimator_fn,alias.estimate)
    ledger = eng.ResourceLedger(dict(zip(eng.CATEGORIES, (2,2,4))))
    with eng.guard_wls_bindings(ledger, policy=p, bridge=b, estimator=s, processors=[processor],
                               aliases=[(alias,'estimate',alias.estimate,'ACTUAL_POLICY_WLS')]):
        assert p.estimate() == processor.estimator_fn() == alias.estimate() == b._estimate() == 7
        assert ledger.counts == dict(zip(eng.CATEGORIES,(2,2,4)))
    assert (p.estimate,b._estimate,s.least_squares,processor.estimator_fn,alias.estimate) == originals
    assert sum(e['status']=='STARTED' for e in ledger.events) == 8


@pytest.mark.parametrize('bad', ['solver_without_outer','budget','failure','tamper','unknown_alias','concurrent'])
def test_guard_failure_closed_and_charges_not_rolled_back(bad):
    p,b,s,processor,alias = hooks()
    if bad == 'failure':
        def failed(): raise ValueError('test failure')
        s.least_squares = failed
    if bad == 'unknown_alias': processor.estimator_fn = lambda: 8
    originals = (p.estimate,b._estimate,s.least_squares)
    ledger = eng.ResourceLedger(dict(zip(eng.CATEGORIES,(1,1,0 if bad=='budget' else 1))))
    with pytest.raises((eng.AdmissionRejected,ValueError)):
        with eng.guard_wls_bindings(ledger, policy=p, bridge=b, estimator=s, processors=[processor]):
            if bad == 'solver_without_outer': s.least_squares()
            elif bad == 'tamper': p.estimate = lambda: 0
            elif bad == 'concurrent':
                with eng.guard_wls_bindings(ledger,policy=p,bridge=b,estimator=s): pass
            else: p.estimate()
    assert (p.estimate,b._estimate,s.least_squares) == originals
    if bad in ('budget','failure'):
        assert ledger.counts['ACTUAL_POLICY_WLS'] == 1
        assert any(e['status']=='FAILED' for e in ledger.events)


def test_storage_and_output_replacement():
    storage = eng.StorageContract(10)
    storage.reserve(8)
    with pytest.raises(eng.AdmissionRejected): storage.reserve(3)
    assert storage.reserved == 8
    original = {'evidence_kind':'TEST_DOUBLE','cut_tick':60}
    expected = eng.content_digest(original)
    assert eng.verify_bound_output(original,expected_digest=expected).endswith('MATCH')
    with pytest.raises(eng.AdmissionRejected): eng.verify_bound_output(dict(original,cut_tick=80),expected_digest=expected)


def test_session_expectations_external_pins_and_no_real_authentication():
    root = Path(__file__).resolve().parents[1]
    source = 'research/non_oracle/stfbs_lite_real_d60_source.py'
    sha = hashlib.sha256((root/source).read_bytes()).hexdigest()
    manifest = dict(git_head='test-head',run_id='test-run',attempt_id='test-attempt',physical_environment_id='TEST_DOUBLE',
        output_directory='test-only',target_tick=60,cut_phase='POST_FREEZE_PRE_ASSIGNMENT',python_identity='test-python',
        runtime_dependencies={'test':'identity'},budget={'test':1},permit_identity='test-permit',supervisor_identity='test-supervisor')
    # Fixture identity expectations are artificial and never grant real RUN.
    pins = tuple((source,sha,role) for role in ('PRODUCTION','ENG','INPUT','DEPENDENCY'))
    expected = eng.SessionExpectations(json.dumps(manifest),pins)
    out = eng.verify_session_expectations(expected,repository=root,observed=manifest)
    assert out['real_source_authentication'] == 'NOT_VERIFIED'
    for altered in (dict(manifest,attempt_id='changed'),dict(manifest,supervisor_identity=None)):
        with pytest.raises(eng.AdmissionRejected): eng.verify_session_expectations(expected,repository=root,observed=altered)
    with pytest.raises(eng.AdmissionRejected):
        eng.verify_session_expectations(eng.SessionExpectations(json.dumps(manifest),()),repository=root,observed=manifest)
    assert eng.check_run_admission(expected,expectations=expected,supervisor={'pid':1})['hard_time_guard'].endswith('NOT_READY')


def test_actual_production_alias_layout_inspected_without_calling_science(monkeypatch):
    from research.non_oracle import policy
    from research.information_service_bridge import public_stream
    from research.cooperative_sensing import estimator
    import scipy.optimize
    def no_science(*args, **kwargs): raise AssertionError('Science must not execute')
    assert eng.inspect_production_aliases()['real_run_admission'] == 'BLOCKED'
    with monkeypatch.context() as patch:
        patch.setattr(policy, 'estimate', no_science)
        with pytest.raises(eng.AdmissionRejected): eng.inspect_production_aliases()
    with pytest.raises(eng.AdmissionRejected):
        eng.inspect_production_aliases(processors=[SimpleNamespace(estimator_fn=no_science)])
    assert eng.inspect_production_aliases(processors=[SimpleNamespace(estimator_fn=public_stream._estimate)])['status'].endswith('MATCH')


def test_invalid_budget_and_nested_outer_rejected():
    with pytest.raises(eng.AdmissionRejected): eng.ResourceLedger({})
    ledger = eng.ResourceLedger(dict(zip(eng.CATEGORIES,(2,2,2))))
    with pytest.raises(eng.AdmissionRejected):
        ledger.invoke('ACTUAL_POLICY_WLS',lambda:ledger.invoke('ACTUAL_OBSERVATION_WLS',lambda:None))
    assert ledger.counts == dict(zip(eng.CATEGORIES,(1,0,0)))
    assert [r['status'] for r in ledger.events] == ['STARTED','REJECTED','FAILED']
