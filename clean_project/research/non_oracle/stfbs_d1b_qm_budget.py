"""Shared two-level budget with append-only pre-call journals; no scientific formula."""
import json,os,time,threading
from pathlib import Path
from contextlib import contextmanager
from contextvars import ContextVar
from uuid import uuid4
CATEGORIES=('MODEL_OBSERVATION_WLS','MODEL_POLICY_EVALUATION_WLS','MODEL_SPECIAL_TEST_WLS','MODEL_INDEPENDENT_AUDIT_WLS','ACTUAL_WLS')
LABEL='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'
_ALIAS_LOCK=threading.Lock()

class BudgetRejected(RuntimeError):pass

class CallJournal:
    def __init__(self,path,batch_id):
        self.path=Path(path);self.batch_id=batch_id;self.sequence=0
        self.handle=self.path.open('x',encoding='utf-8');self.closed=False
    def append(self,**entry):
        if self.closed:raise RuntimeError('Journal closed')
        self.sequence+=1
        row=dict(batch_id=self.batch_id,sequence=self.sequence,timestamp=time.time(),branch_id=None,category=None,
                 outer_call_id=None,inner_call_id=None,frame_id=None,reason=None,**{})
        row.update(entry);self.handle.write(json.dumps(row,sort_keys=True)+'\n');self.handle.flush();os.fsync(self.handle.fileno())
        return row
    def close(self):
        if not self.closed:self.handle.close();self.closed=True

def inspect_journal(path):
    pending={};sequence=0;rows=[]
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        try:row=json.loads(line)
        except json.JSONDecodeError:return dict(status='RESOURCE_LEDGER_INCOMPLETE',pending=list(pending.values()),records=rows,reason='Partial or corrupt JSONL record')
        sequence+=1
        if row['sequence']!=sequence:raise ValueError('Journal sequence mismatch')
        rows.append(row);key=(row['level'],row['outer_call_id'],row['inner_call_id'])
        if row['status']=='STARTED':
            if key in pending:raise ValueError('Duplicate STARTED')
            pending[key]=row
        elif row['status'] in ('RETURNED','FAILED'):
            if key not in pending:raise ValueError('Terminal without STARTED')
            pending.pop(key)
    return dict(status='RESOURCE_LEDGER_INCOMPLETE' if pending else 'COMPLETE',pending=list(pending.values()),records=rows)

class D1BBudget:
    def __init__(self,*,test_cap=None,test_estimator=None,test_inner_cap=None,journal_path=None,batch_id='ENGINEERING_TEST',category_limits=None):
        if test_estimator is not None and getattr(test_estimator,'evidence_kind',None)!=LABEL:raise ValueError('Labelled test estimator required')
        for n in (test_cap,test_inner_cap):
            if n is not None and (type(n) is not int or n<0):raise ValueError('Invalid cap')
        self.ledger_id='D1B:'+str(uuid4());self.counts=dict.fromkeys(CATEGORIES,0);self.records=[];self.rejections=[];self.solver_records=[]
        self.accounting=dict(outer_wls_started=0,outer_wls_returned=0,outer_wls_failed=0,budget_rejected=0,least_squares_started=0,least_squares_returned=0,least_squares_failed=0)
        self._cap=test_cap;self._inner_cap=test_inner_cap if test_inner_cap is not None else (test_cap*9 if test_cap is not None else None)
        self._double=test_estimator;self._real=None;self._permit=None;self._alias_active=False
        self._limits=category_limits or {k:(0 if k in ('MODEL_POLICY_EVALUATION_WLS','ACTUAL_WLS') else test_cap) for k in CATEGORIES}
        self._branch=ContextVar('d1b_branch_'+self.ledger_id,default=None);self._frame=ContextVar('d1b_frame_'+self.ledger_id,default=None);self._outer=ContextVar('d1b_outer_'+self.ledger_id,default=None)
        self._cpu=time.process_time();self._wall=time.monotonic();self.journal=CallJournal(journal_path,batch_id) if journal_path is not None else None
    def __deepcopy__(self,memo):return self
    @classmethod
    def from_release(cls,permit,journal_path):
        from .stfbs_d1b_qm_run_release import require_run_g1
        if require_run_g1(permit) is not permit:raise PermissionError('Wrong permit')
        v=permit.bindings;b=cls(journal_path=journal_path,batch_id=v['batch_id']);b._permit=permit;b._cap=v['outer_limit'];b._inner_cap=v['inner_limit'];b._limits=dict(v['category_limits']);b.install_real_backend(permit);return b
    def install_real_backend(self,permit):
        from .stfbs_d1b_qm_run_release import require_run_g1
        require_run_g1(permit)
        if self._permit is not permit or self.journal is None or self._double is not None or sum(self.counts.values()):raise PermissionError('Real backend must bind before first call')
        from research.cooperative_sensing import estimator
        self._real=(estimator,estimator.estimate,estimator.least_squares)
        return self._real[1]
    @property
    def real_ready(self):return self._real is not None and self._double is None and self._permit is not None and self.journal is not None
    def check(self):
        if self.counts['ACTUAL_WLS']:raise RuntimeError('ACTUAL forbidden')
        if self._permit is not None:
            from .stfbs_d1b_qm_run_release import require_run_g1
            require_run_g1(self._permit)
    def _write(self,level,status,kind,branch,outer=None,inner=None,reason=None,payload=None):
        row=dict(level=level,status=status,category=kind,branch_id=branch,outer_call_id=outer,inner_call_id=inner,frame_id=self._frame.get(),reason=reason,payload=payload,evidence_kind='MODEL' if self._permit else LABEL)
        if self.journal:row=self.journal.append(**row)
        return row
    def _reject(self,level,kind,branch,reason):
        outer=self._outer.get()
        self.accounting['budget_rejected']+=1;self.rejections.append(self._write(level,'REJECTED',kind,branch,outer[0] if outer else None,reason=reason));raise BudgetRejected(reason)
    @contextmanager
    def for_branch(self,branch_id):
        from .stfbs_d1b_qm_execution import IDENTITIES,SPECIAL_IDS
        if branch_id not in IDENTITIES+SPECIAL_IDS:raise ValueError('Invalid full scientific identity')
        token=self._branch.set(branch_id)
        try:yield
        finally:self._branch.reset(token)
    @contextmanager
    def for_frame(self,frame_id):
        if not isinstance(frame_id,str) or not frame_id:raise ValueError('Frame identity required')
        token=self._frame.set(frame_id)
        try:yield
        finally:self._frame.reset(token)
    def estimator(self,kind,*,branch_id=None):
        from .stfbs_d1b_qm_execution import IDENTITIES,SPECIAL_IDS
        branch=branch_id or self._branch.get()
        if branch not in IDENTITIES+SPECIAL_IDS or kind not in CATEGORIES or kind in ('ACTUAL_WLS','MODEL_POLICY_EVALUATION_WLS'):raise ValueError('Forbidden branch/category')
        if branch in SPECIAL_IDS and kind!='MODEL_SPECIAL_TEST_WLS':raise ValueError('Special identity requires special category')
        if self._permit is not None and kind=='MODEL_SPECIAL_TEST_WLS' and branch not in SPECIAL_IDS:raise ValueError('Real special WLS requires special identity')
        def call(payload):
            self.check()
            if self._outer.get() is not None:raise RuntimeError('Nested outer WLS forbidden')
            if (self._double is None and not self.real_ready) or self._cap is None:self._reject('OUTER',kind,branch,'NO_APPROVED_REAL_BUDGET')
            if self.real_ready:
                module,estimate,original=self._real
                if module.estimate is not estimate or module.least_squares is not original or self._alias_active or _ALIAS_LOCK.locked():self._reject('OUTER',kind,branch,'SOLVER_ALIAS_NOT_READY')
            if self._frame.get() is None:self._reject('OUTER',kind,branch,'FRAME_ID_REQUIRED')
            if sum(self.counts.values())>=self._cap or self._limits.get(kind) is None or self.counts[kind]>=self._limits[kind]:self._reject('OUTER',kind,branch,'OUTER_CAP_EXCEEDED')
            outer='O'+str(sum(self.counts.values())+1)
            row=self._write('OUTER','STARTED',kind,branch,outer,payload=payload);self.counts[kind]+=1;self.accounting['outer_wls_started']+=1;self.records.append(row)
            token=self._outer.set((outer,kind,branch));inner_before=self.accounting['least_squares_started']
            try:
                if self.real_ready:
                    module,estimate,original=self._real
                    if module.estimate is not estimate or module.least_squares is not original:raise RuntimeError('Real solver alias changed before call')
                    value=self.invoke_alias(module,estimate,payload,real=True)
                else:value=self._double(payload)
                self._write('OUTER','RETURNED',kind,branch,outer);self.accounting['outer_wls_returned']+=1;row['status']='RETURNED';return value
            except BaseException as e:
                self._write('OUTER','FAILED',kind,branch,outer,reason=repr(e));self.accounting['outer_wls_failed']+=1;row['status']='FAILED';raise
            finally:
                row['inner_started']=self.accounting['least_squares_started']-inner_before;self._outer.reset(token)
        call.ledger_id=self.ledger_id;call.category=kind;call.branch_id=branch
        return call
    def record_solver(self,solver,*args,**kwargs):
        self.check();outer=self._outer.get()
        if outer is None:raise RuntimeError('Solver without active outer WLS')
        oid,kind,branch=outer
        if self._permit is None and getattr(solver,'evidence_kind',None)!=LABEL:raise PermissionError('Test context cannot enter real solver')
        if self._inner_cap is None or self.accounting['least_squares_started']>=self._inner_cap:self._reject('INNER',kind,branch,'INNER_CAP_EXCEEDED')
        active=sum(x['outer_call_id']==oid for x in self.solver_records)
        if active>=9:self._reject('INNER',kind,branch,'PER_OUTER_NINE_STARTS_EXCEEDED')
        inner='I'+str(self.accounting['least_squares_started']+1)
        row=self._write('INNER','STARTED',kind,branch,oid,inner);self.accounting['least_squares_started']+=1;self.solver_records.append(row)
        try:
            value=solver(*args,**kwargs);self._write('INNER','RETURNED',kind,branch,oid,inner);self.accounting['least_squares_returned']+=1;row['status']='RETURNED';return value
        except BaseException as e:
            self._write('INNER','FAILED',kind,branch,oid,inner,repr(e));self.accounting['least_squares_failed']+=1;row['status']='FAILED';raise
    def invoke_alias(self,module,estimate,payload,*,real=False):
        if real:
            from .stfbs_d1b_qm_run_release import require_run_g1
            require_run_g1(self._permit)
            if not self.real_ready or self._real[:2]!=(module,estimate):raise PermissionError('Unregistered real alias backend')
        if self._outer.get() is None or self._alias_active or not _ALIAS_LOCK.acquire(blocking=False):raise RuntimeError('Serial alias scope/reentry violation')
        original=module.least_squares;self._alias_active=True
        if not real and (getattr(original,'evidence_kind',None)!=LABEL or getattr(estimate,'evidence_kind',None)!=LABEL):
            self._alias_active=False;_ALIAS_LOCK.release();raise PermissionError('Alias test cannot bind real functions')
        def measured(*args,**kwargs):return self.record_solver(original,*args,**kwargs)
        module.least_squares=measured
        try:
            if module.least_squares is not measured:raise RuntimeError('Alias installation failed')
            return estimate(payload)
        finally:
            bad=module.least_squares is not measured
            module.least_squares=original;self._alias_active=False;_ALIAS_LOCK.release()
            if module.least_squares is not original or bad:raise RuntimeError('Alias scope was altered')
    def snapshot(self):
        return dict(ledger_id=self.ledger_id,counts=dict(self.counts),total=sum(self.counts.values()),accounting=dict(self.accounting),records=self.records,rejections=self.rejections,solver_records=self.solver_records,real_budget_approved=self.real_ready,scope='REAL_MODEL' if self._permit else LABEL,cpu_seconds=time.process_time()-self._cpu,wall_seconds=time.monotonic()-self._wall)
    def bind_real_estimator(self,approval=None):
        from .stfbs_d1b_qm_run_release import real_estimator_binding
        return real_estimator_binding(self,approval)
