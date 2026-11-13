"""External resource-contract restoration; engineering validation is pending."""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from research.non_oracle.stfbs_lite_real_d60_source import ResourceLedger, AdmissionRejected
from .diagnostics import emit, persist
from .journal import LocalJournal, NestedJournal, ModelJournal, MODEL_MAP, require

LIMITS = {'ACTUAL_POLICY_WLS': 744, 'ACTUAL_OBSERVATION_WLS': 63,
          'ACTUAL_SOLVER_START': 7263}
INVERSE_MAP = {v: k for k, v in MODEL_MAP.items()}
CALL_TYPES = {'ACTUAL_POLICY_WLS': 'POLICY_WLS',
              'ACTUAL_OBSERVATION_WLS': 'OBSERVATION_WLS',
              'ACTUAL_SOLVER_START': 'SOLVER'}


class SolverFatal(BaseException):
    """Retain the historical conservative barrier to swallowed solver errors."""


class AuditedDurableResourceLedger(ResourceLedger):
    """Direct ResourceLedger adapter, not a second DurableResourceLedger layer."""
    def __init__(self, model, integrity_check):
        super().__init__(dict(LIMITS))
        self.model = model
        self.integrity_fault = False
        def checked():
            try:
                integrity_check()
            except BaseException:
                self.integrity_fault = True
                raise
        self.integrity_check = checked

    def invoke(self, category, fn, *args, **kwargs):
        self.model.nested.require_open()
        self.integrity_check()
        require(category in CALL_TYPES, 'UNKNOWN_RESOURCE_CATEGORY')
        call = self.model.nested.allocate(CALL_TYPES[category], category, MODEL_MAP[category])
        before = dict(self.counts)
        entered = False
        started_committed = False
        self.integrity_fault = False
        def expensive():
            nonlocal entered, started_committed
            entered = True
            # Core already charged; if persistence fails fn is never called.
            self.model.event(call, 'STARTED', before, dict(self.counts))
            started_committed = True
            return fn(*args, **kwargs)
        try:
            # RETURNED must follow the core's post-execution integrity_check.
            result = super().invoke(category, expensive)
        except BaseException as exc:
            if started_committed and not self.model.nested.local.invalid:
                self.model.event(call, 'FAILED', before, dict(self.counts),
                                 exception_type=type(exc).__name__, exception_message=str(exc))
            elif (not entered and not self.integrity_fault and
                  isinstance(exc, AdmissionRejected) and str(exc) in
                  {'INVALID_CALL_NESTING', 'BUDGET_EXHAUSTED'} and self.counts == before):
                self.model.event(call, 'REJECTED', before, dict(self.counts), reason=str(exc))
            # No FAILED/REJECTED fabrication when STARTED never committed.
            raise
        self.model.event(call, 'RETURNED', before, dict(self.counts))
        return result


class IndependentRecorder:
    def __init__(self, nested, call_type, integrity_check, limit=2):
        require(call_type in {'R', 'ASSIGNMENT'} and limit == 2, 'INDEPENDENT_CONTRACT')
        self.nested, self.call_type = nested, call_type
        self.integrity_check, self.limit = integrity_check, limit
        self.runtime_counter = 0

    def usage(self):
        return self.nested.incremental_usage(self.call_type)

    def reconcile(self):
        usage = self.usage()
        require(usage == self.runtime_counter, 'RUNTIME_COUNTER_RECONCILIATION')
        return usage

    def invoke(self, fn, *args, logical_allowed=True, prepare=None, **kwargs):
        self.nested.require_open()
        self.integrity_check()
        usage = self.reconcile()
        call = self.nested.allocate(self.call_type)
        before = {self.call_type: usage}
        if not logical_allowed or usage >= self.limit:
            self.nested.event(call, 'REJECTED', before, before,
                              reason='LOGICAL_BOUNDARY' if not logical_allowed else 'BUDGET_EXHAUSTED')
            raise AdmissionRejected('INDEPENDENT_CALL_REJECTED')
        metadata = prepare() if prepare else {}
        # Provenance save is preparation, not resource consumption.
        self.nested.event(call, 'STARTED', before, {self.call_type: usage + 1}, **metadata)
        try:
            committed = self.usage()
            self.runtime_counter += 1
            require(committed == self.runtime_counter == usage + 1,
                    'RUNTIME_COUNTER_RECONCILIATION')
            result = fn(*args, **kwargs)
            self.integrity_check()
            self.reconcile()
        except BaseException as exc:
            if not self.nested.local.invalid:
                self.nested.event(call, 'FAILED', before, {self.call_type: self.usage()},
                                  exception_type=type(exc).__name__, exception_message=str(exc))
            raise
        self.nested.event(call, 'RETURNED', before, {self.call_type: self.usage()})
        return result


class RRecorder(IndependentRecorder):
    def __init__(self, nested, integrity_check):
        super().__init__(nested, 'R', integrity_check)


class AssignmentRecorder(IndependentRecorder):
    def __init__(self, nested, integrity_check):
        super().__init__(nested, 'ASSIGNMENT', integrity_check)


class Budget:
    def __init__(self, local, nested, model, ledger, r, assignment, provenance, directory):
        require(nested.local is local and model.nested is nested and ledger.model is model
                and r.nested is nested and assignment.nested is nested, 'MULTIPLE_JOURNALS')
        self.local, self.nested, self.model = local, nested, model
        self.ledger, self.r, self.assignment = ledger, r, assignment
        self.provenance, self.directory, self.branch = provenance, Path(directory), None
        self.halted = False
        self.state = 'OPEN'
        self.finalization_report = None
        from research.cooperative_sensing import estimator
        from research.non_oracle import policy, stfbs_d1a_model
        from scipy import optimize
        require(stfbs_d1a_model.estimate is estimator.estimate and
                policy.estimate is estimator.estimate and
                estimator.least_squares is optimize.least_squares, 'UNKNOWN_ESTIMATOR_ALIAS')
        self.est, self.solver, self.exact = estimator.estimate, estimator.least_squares, policy.solve

    def check(self):
        require(self.state == 'OPEN', 'BUDGET_FINALIZED_OR_FINALIZING')
        self.nested.require_open()
        require(not self.halted, 'BUDGET_FAIL_STOP')
        committed = self.local.committed_counts()
        for category, call_type in CALL_TYPES.items():
            require(self.ledger.counts[category] == committed[call_type],
                    'WLS_RUNTIME_COUNTER_RECONCILIATION')
        self.r.reconcile()
        self.assignment.reconcile()
        require(sum(p.stat().st_size for p in self.directory.rglob('*') if p.is_file())
                <= 268435456, 'BRANCH_STORAGE_EXHAUSTED')

    def _invoke(self, fn, *args, **kwargs):
        try:
            self.check()
            return fn(*args, **kwargs)
        except BaseException:
            self.halted = True
            raise

    @property
    def r_calls(self):
        return self.r.reconcile()

    @property
    def counts(self):
        return dict({MODEL_MAP[k]: v for k, v in self.ledger.counts.items()},
                    R_CALLS=self.r.reconcile(),
                    ASSIGNMENT_EXACT_SOLVER=self.assignment.reconcile(),
                    ACTUAL_WLS=0, ACTUAL_STEP=0)

    def estimator(self, kind):
        require(kind in {'MODEL_POLICY_EVALUATION_WLS', 'MODEL_OBSERVATION_WLS'},
                'UNKNOWN_MODEL_ESTIMATOR_KIND')
        return lambda payload: self._invoke(self.ledger.invoke, INVERSE_MAP[kind], self.est, payload)

    def solve(self, *args, **kwargs):
        return self._invoke(self.assignment.invoke, self.exact, *args, **kwargs)

    def choose(self, view):
        from research.non_oracle import policy
        def prepare():
            from hashlib import sha256
            path = self.directory / ('BELIEF_PROVENANCE_D%d.json' % view['tick'])
            persist(path, self.provenance(self.branch, view['tick']))
            return dict(provenance_id=str(path), provenance_sha256=sha256(path.read_bytes()).hexdigest(),
                        provenance_tick=view['tick'])
        def real():
            with (patch.object(policy, 'estimate', self.estimator('MODEL_POLICY_EVALUATION_WLS')),
                  patch.object(policy, 'solve', self.solve)):
                return policy.decide(view, method='R')
        return self._invoke(self.r.invoke, real, logical_allowed=view['tick'] in (80, 100),
                            prepare=prepare)

    @contextmanager
    def solver_guard(self):
        from research.cooperative_sensing import estimator
        def real(*args, **kwargs):
            try:
                return self._invoke(self.ledger.invoke, 'ACTUAL_SOLVER_START',
                                    self.solver, *args, **kwargs)
            except BaseException as exc:
                raise SolverFatal(str(exc)) from exc
        with patch.object(estimator, 'least_squares', real):
            yield

    def reconcile_final(self):
        """L3: independently recount disk, then compare commits and runtime."""
        committed = self.local.committed_counts()
        disk = dict.fromkeys(committed, 0)
        for row in self.local.records():
            event = row['event']
            if (event.get('event_kind') == 'RESOURCE_CALL' and
                    event.get('status') == 'STARTED' and event.get('call_type') in disk):
                disk[event['call_type']] += 1
        runtime = {call_type: self.ledger.counts[category]
                   for category, call_type in CALL_TYPES.items()}
        runtime.update(R=self.r.runtime_counter, ASSIGNMENT=self.assignment.runtime_counter)
        require(disk == committed == runtime, 'FINAL_RESOURCE_COUNTER_RECONCILIATION')
        return dict(disk=disk, committed=committed, runtime=runtime)

    def finalize(self, *, success=True):
        """Irreversible, best-effort failure enclosure independent of file health."""
        require(self.state not in {'FINALIZED_PASS', 'FINALIZED_FAILED', 'FINALIZING'},
                'BUDGET_FINALIZATION_IRREVERSIBLE')
        self.local.freeze_writes()
        self.state = 'FINALIZING'
        if self.nested.state not in {'FINALIZED_PASS', 'FINALIZED_FAILED'}:
            self.nested.state = 'FINALIZING'
        failures = []
        if not success or self.halted or self.nested.poisoned:
            failures.append(dict(check='EXECUTION_OUTCOME', error='FAILED_OR_POISONED'))
        def perform(name, operation):
            try:
                return operation()
            except BaseException as exc:
                failures.append(dict(check=name, error=type(exc).__name__, message=str(exc)))
                return None
        resource_audit = perform('FINAL_RESOURCE_RECONCILIATION', self.reconcile_final)
        # Do not skip sealing a healthy Journal because resource checks failed.
        perform('LOCAL_JOURNAL_SEAL', self.local.seal)
        perform('NESTED_IDENTITY_AND_LIFECYCLE_AUDIT', self.nested.audit)
        perform('LOCAL_JOURNAL_CLOSE', self.local.close)
        terminal = 'FINALIZED_FAILED' if failures else 'FINALIZED_PASS'
        self.state = self.nested.state = terminal
        self.halted = terminal == 'FINALIZED_FAILED'
        self.finalization_report = dict(state=terminal, failures=failures,
                                        local_invalid=self.local.invalid,
                                        local_sealed=self.local.sealed,
                                        resource_audit=resource_audit)
        if failures:
            raise RuntimeError('BUDGET_FINALIZED_FAILED: ' + repr(failures))
        return self.finalization_report


@contextmanager
def initialized_budget(path, task_id, attempt_id, provenance):
    """Caller constructs Branch only inside this protected context; never an attempt factory."""
    local = None
    budget = None
    try:
        local = LocalJournal(path, task_id, attempt_id, 268435456)
        nested = NestedJournal(local)
        model = ModelJournal(nested)
        # Binding a late Budget reference avoids circular constructors.
        owner = []
        def integrity():
            if owner:
                owner[0].check()
            else:
                local.check()
        ledger = AuditedDurableResourceLedger(model, integrity)
        r, assignment = RRecorder(nested, integrity), AssignmentRecorder(nested, integrity)
        budget = Budget(local, nested, model, ledger, r, assignment, provenance, Path(path).parent)
        owner.append(budget)
        yield budget
        budget.finalize()
    except BaseException as exc:
        if budget is not None and budget.state not in {'FINALIZED_PASS', 'FINALIZED_FAILED'}:
            try:
                budget.finalize(success=False)
            except BaseException as final_exc:
                emit(task_id, attempt_id, 'FAILED_FINALIZATION', final_exc,
                     resource_state='UNRECONCILED' if local and local.invalid else 'UNKNOWN')
        elif local is not None and not local.invalid and not local.sealed:
            try:
                local.seal()
            except BaseException as seal_exc:
                emit(task_id, attempt_id, 'FAILED_INITIALIZATION_SEAL', seal_exc,
                     resource_state='UNRECONCILED')
        emit(task_id, attempt_id, 'INITIALIZATION_OR_EXECUTION', exc,
             resource_state='UNRECONCILED' if local and local.invalid else 'UNKNOWN')
        raise
    finally:
        if local is not None:
            local.close()
