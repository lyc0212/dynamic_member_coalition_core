"""Batch MODEL budget. No approved real estimator exists in this ENG release."""
from time import monotonic, process_time
from uuid import uuid4
from contextlib import contextmanager
from contextvars import ContextVar

CATEGORIES=('MODEL_OBSERVATION_WLS','MODEL_POLICY_EVALUATION_WLS','MODEL_SPECIAL_TEST_WLS','MODEL_INDEPENDENT_AUDIT_WLS','ACTUAL_WLS')
LABEL='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'

class D1BBudget:
    def __init__(self,*,test_cap=None,test_estimator=None):
        if test_estimator is not None and getattr(test_estimator,'evidence_kind',None)!=LABEL:
            raise ValueError('Only labelled test estimator permitted in ENG')
        if test_cap is not None and (type(test_cap) is not int or test_cap<0):raise ValueError('Invalid test cap')
        self.ledger_id='D1B:'+str(uuid4());self.counts=dict.fromkeys(CATEGORIES,0)
        self.records=[];self.rejections=[];self._cap=test_cap;self._double=test_estimator
        self.accounting=dict(outer_wls_started=0,outer_wls_returned=0,outer_wls_failed=0,budget_rejected=0,
                             least_squares_started=0,least_squares_returned=0,least_squares_failed=0)
        self.solver_records=[]
        self._cpu=process_time();self._wall=monotonic()
        self._branch=ContextVar('d1b_budget_branch_'+self.ledger_id,default=None)
    def __deepcopy__(self,memo):return self
    def check(self):
        if self.counts['ACTUAL_WLS']:raise RuntimeError('ACTUAL forbidden')
    def estimator(self,kind,*,branch_id=None):
        if kind not in CATEGORIES or kind=='ACTUAL_WLS':raise ValueError('Forbidden budget category')
        branch_id=self._branch.get() if branch_id is None else branch_id
        if not branch_id:raise ValueError('Budget callback requires full scientific branch identity')
        from .stfbs_d1b_qm_execution import IDENTITIES
        if branch_id not in IDENTITIES:raise ValueError('Unknown scientific budget branch')
        def call(payload):
            if self._double is None or self._cap is None:
                self.accounting['budget_rejected']+=1
                self.rejections.append(dict(kind=kind,branch_id=branch_id,reason='NO_APPROVED_REAL_BUDGET'))
                raise RuntimeError('NO_APPROVED_REAL_BUDGET')
            if sum(self.counts.values())>=self._cap:
                self.accounting['budget_rejected']+=1
                self.rejections.append(dict(kind=kind,branch_id=branch_id,reason='SHARED_CAP_EXCEEDED'))
                raise RuntimeError('SHARED_CAP_EXCEEDED')
            self.counts[kind]+=1
            self.accounting['outer_wls_started']+=1
            row=dict(kind=kind,branch_id=branch_id,index=sum(self.counts.values()),status='STARTED',evidence_kind=LABEL)
            self.records.append(row)
            try:
                result=self._double(payload);row['status']='RETURNED';self.accounting['outer_wls_returned']+=1;return result
            except BaseException as e:
                self.accounting['outer_wls_failed']+=1;row.update(status='FAILED',error=type(e).__name__);raise
        call.ledger_id=self.ledger_id;call.category=kind;call.branch_id=branch_id
        return call
    @contextmanager
    def for_branch(self,branch_id):
        from .stfbs_d1b_qm_execution import IDENTITIES
        if branch_id not in IDENTITIES:raise ValueError('Invalid budget branch')
        token=self._branch.set(branch_id)
        try:yield
        finally:self._branch.reset(token)
    def snapshot(self):
        return dict(ledger_id=self.ledger_id,counts=dict(self.counts),total=sum(self.counts.values()),
                    records=[dict(x) for x in self.records],rejections=[dict(x) for x in self.rejections],accounting=dict(self.accounting),solver_records=[dict(x) for x in self.solver_records],
                    cpu_seconds=process_time()-self._cpu,wall_seconds=monotonic()-self._wall,
                    scope='test-double calls only; real WLS zero; external Job remains resource authority',real_budget_approved=False)

    def record_solver(self,solver,*args,**kwargs):
        if getattr(solver,'evidence_kind',None)!=LABEL:
            from .stfbs_d1b_qm_run_release import require_run_g1
            require_run_g1()  # Real solver counting remains unavailable until RUN-G1 review.
        self.accounting['least_squares_started']+=1
        row=dict(index=self.accounting['least_squares_started'],status='STARTED',evidence_kind=LABEL)
        self.solver_records.append(row)
        try:
            result=solver(*args,**kwargs);row['status']='RETURNED';self.accounting['least_squares_returned']+=1;return result
        except BaseException as error:
            row.update(status='FAILED',error=type(error).__name__);self.accounting['least_squares_failed']+=1;raise

    def bind_real_estimator(self,approval=None):
        from .stfbs_d1b_qm_run_release import real_estimator_binding
        return real_estimator_binding(self,approval)

