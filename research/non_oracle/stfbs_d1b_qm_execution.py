"""Thin dynamic schedule; no RUN approval can be minted by this ENG release."""
from copy import deepcopy
from .stfbs_d1b_qm_model import QMBranch,preset_action
from .stfbs_d1b_qm_scenario import validate_fixture
from .stfbs_d1b_qm_budget import D1BBudget

SELECTORS={'QM_B0_KEEP':'B0','QM_B1_MEMBER_CHANGE':'B1','QM_B3_UNKNOWN':'B0'}
PROBES=('QM_PROBE_OLD',)+tuple('QM_PROBE_DEGRADED_'+str(i) for i in range(1,5))
IDENTITIES=tuple(SELECTORS)+PROBES

def selector(branch_id,claimed=None):
    if branch_id not in SELECTORS:raise ValueError('Probe is not a dynamic branch')
    result=SELECTORS[branch_id]
    if claimed is not None and claimed!=result:raise ValueError('Scientific identity/selector mismatch')
    return result

def require_run_authorization(approval=None):
    from .stfbs_d1b_qm_run_release import require_run_g1
    require_run_g1(approval)

def bind_shared_budget(branch,budget):
    if type(budget) is not D1BBudget:raise ValueError('D1-B shared budget required; no D1-A fallback')
    if (branch.tick!=60 or branch.fusions or branch.streams or branch.feedback or branch.cache.rows
        or branch.cache.counts['requests'] or branch.boundaries or branch.consumer.pending
        or branch.consumer.model_measurements or any(a['target'] is not None for a in branch.actions)
        or any(h['segments'] for h in branch.histories.values())
        or any(branch.budget.counts.values())):raise ValueError('Unsafe late budget takeover')
    branch.budget=budget
    if branch.budget is not budget:raise RuntimeError('Budget identity lost')

class DynamicSchedule:
    """Also exercised with explicitly labelled nonphysical ports; no science reimplementation."""
    def __init__(self,branch,branch_id):
        if branch_id not in SELECTORS or branch.name!=branch_id:raise ValueError('Wrong dynamic identity')
        if type(branch.budget) is not D1BBudget:raise ValueError('Budget not bound before schedule')
        self.branch=branch;self.branch_id=branch_id;self.events=[];self._started=False;self._cuts=set()
    def _execution_gate(self):
        if isinstance(self.branch,QMBranch):require_run_authorization()
        cls=type(self.branch)
        if (cls.__module__ not in ('tests.test_stfbs_d1b_qm1b_eng','tests.test_stfbs_d1b_qm_run_g0') or cls.__name__!='SyntheticPort'
            or getattr(self.branch,'evidence_kind',None)!='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'):
            raise PermissionError('Unregistered engineering port')
    def start(self):
        self._execution_gate()
        b=self.branch
        if self._started or b.tick!=60:raise ValueError('Duplicate/late initial assignment')
        view=b.policy_view();choice=preset_action(view,selector(self.branch_id))
        with b.budget.for_branch(self.branch_id):
            b.assign(choice['actions'])  # Fuse is owned exclusively by assignment transaction.
        self._started=True;self._cuts.add(60);self.events.append(dict(tick=60,kind='INITIAL_ASSIGNMENT',branch=self.branch_id))
    def advance_one(self):
        self._execution_gate()
        b=self.branch
        if not self._started or b.tick>=120 or b.tick in (80,100) and b.tick not in self._cuts:
            raise ValueError('Decision barrier not satisfied')
        with b.budget.for_branch(self.branch_id):
            b.advance()  # Owns old-team movement, right endpoint and service settlement.
        if b.tick in (80,100):self.decision_cut()
    def decision_cut(self):
        self._execution_gate()
        b=self.branch
        if not self._started or b.tick not in (80,100) or b.tick in self._cuts:raise ValueError('Duplicate/illegal decision freeze')
        b._sensor_authority.publish_from_executor(b.tick)
        view=b.policy_view()  # Freeze once, before any new left endpoint is produced.
        choice=preset_action(view,selector(self.branch_id))
        # Even KEEP goes through the original transaction (which resets its stream
        # window marker but does not fuse/create a segment when the team is unchanged).
        with b.budget.for_branch(self.branch_id):b.assign(choice['actions'])
        self._cuts.add(b.tick);self.events.append(dict(tick=b.tick,kind='PUBLIC_FREEZE_AND_PRESET',branch=self.branch_id))
    def run_to_end(self):
        self.start()
        while self.branch.tick<120 and any(s=='active' for s in self.branch.status.values()):self.advance_one()
        return self.events

def prepare_branch(fixture,branch_id,budget,registration,*,degraded_sigma=.08):
    from .stfbs_d1b_qm_independent_audit import verify_registration
    validate_fixture(fixture);verify_registration(registration,fixture,branch_id)
    if branch_id not in IDENTITIES:raise ValueError('Unregistered science identity')
    if fixture.world['motion_rule']!='constant_velocity_from_public_D60_v1':raise ValueError('Unsupported MODEL motion authority')
    if branch_id=='QM_PROBE_OLD':degraded_sigma=.02
    elif branch_id in PROBES:degraded_sigma=(.04,.08,.16,.32)[int(branch_id.rsplit('_',1)[1])-1]
    branch=QMBranch(fixture,name=branch_id,degraded_sigma=degraded_sigma)
    bind_shared_budget(branch,budget)
    return branch

def execute_run(fixture,branch_id,budget,registration,*,approval=None):
    require_run_authorization(approval)  # Before construction, assign, raw, fuse or advance.
    branch=prepare_branch(fixture,branch_id,budget,registration)
    schedule=DynamicSchedule(branch,branch_id);schedule.run_to_end()
    return branch

def validate_dynamic_endpoint(endpoint,branch_id,tick):
    if endpoint.get('branch')!=branch_id or endpoint.get('tick')!=tick or endpoint.get('observation_origin')!='MODEL':
        raise ValueError('Foreign endpoint: OLD probe cannot replace dynamic endpoint')
    return True

class ProbeSchedule:
    """Independent fixed-team prefix, never a B0/B1 preset selector."""
    def __init__(self,branch,branch_id):
        if branch_id not in PROBES or branch.name!=branch_id or type(branch.budget) is not D1BBudget:raise ValueError('Probe identity/budget mismatch')
        self.branch=branch;self.branch_id=branch_id;self.started=False
    def _gate(self):
        if isinstance(self.branch,QMBranch):require_run_authorization()
        cls=type(self.branch)
        if cls.__module__!='tests.test_stfbs_d1b_qm_run_g0' or cls.__name__!='SyntheticPort' or getattr(self.branch,'evidence_kind',None)!='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE':raise PermissionError('Unregistered probe port')
    def start(self):
        from .stfbs_d1b_qm_model import initial_team
        self._gate()
        if self.started or self.branch.tick!=60:raise ValueError('Invalid probe start')
        with self.branch.budget.for_branch(self.branch_id):self.branch.assign(initial_team())
        self.started=True
    def run_to_80(self):
        self._gate();self.start()
        while self.branch.tick<80 and any(s=='active' for s in self.branch.status.values()):
            with self.branch.budget.for_branch(self.branch_id):self.branch.advance()
        if self.branch.tick!=80 or not any(s=='active' for s in self.branch.status.values()):raise ValueError('Probe admission terminated before 80')
        return dict(branch=self.branch_id,tick=self.branch.tick,terminal_penalty_applied=False)
