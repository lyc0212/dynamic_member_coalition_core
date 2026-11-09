"""RUN-G0 release wiring. RUN-G1 cannot be authorized by this version."""
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from .stfbs_d1b_qm_model import SensorAuthority,initial_team
from .stfbs_d1a_replay import digest

SIGMAS=(.04,.08,.16,.32)
LABEL='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'

def require_run_g1(approval=None):
    raise PermissionError('RUN_G1_NOT_AUTHORIZED: G0 release is fail-closed')

class MissingSensorAuthority(SensorAuthority):
    def __init__(self):
        super().__init__(.02)
        self._schedule[1]['profiles'][1]['health']='missing'

def missing_slot_structure(authority,tick,robot=1):
    """Pure missing representation; no raw producer or sensor is invoked."""
    from research.information_service_online.public import seal_slot
    if authority.physical_profile_at(tick)[robot]['health']!='missing':raise ValueError('Not missing')
    return seal_slot(dict(slot_key=dict(target_id=0,robot_id=robot,tick=tick),state='MISSING',packet=None,slot_digest=None))

@dataclass(frozen=True)
class Admission:
    selected_sigma: float
    selected_factor: int
    selected_probe_id: str
    selection_rule: str
    selection_evidence_digest: str
    admission_status: str
    source_run_identity: str
    evidence_json: str

def freeze_admission(rows,source_run_identity):
    import json
    if not source_run_identity or not rows:raise ValueError('Admission evidence required')
    selected=None
    for index,row in enumerate(rows):
        if index>=4 or row['probe_id']!='QM_PROBE_DEGRADED_'+str(index+1) or row['sigma']!=SIGMAS[index]:raise ValueError('Probe selection order changed')
        if row['old_G'] is not True or row['new_G'] is not True or row['old_Q']!='PASS':raise ValueError('Scenario admission failed')
        if row['new_Q'] not in ('PASS','FAIL','UNKNOWN'):raise ValueError('Invalid quality category')
        if row['new_Q']=='FAIL':
            selected=(index,row);break
    if selected is None:raise ValueError('NO_Q_ONLY_FAIL_FOUND')
    index,row=selected
    if len(rows)!=index+1:raise ValueError('Post-selection probe results forbidden')
    frozen=json.dumps(rows,sort_keys=True)
    return Admission(row['sigma'],(2,4,8,16)[index],row['probe_id'],'FIRST_EXPLICIT_Q_ONLY_FAIL',digest(rows),'ADMITTED',source_run_identity,frozen)

def verify_admission(admission,selected_sigma):
    import json
    if type(admission) is not Admission:raise ValueError('Frozen admission required')
    expected=freeze_admission(json.loads(admission.evidence_json),admission.source_run_identity)
    if expected!=admission or selected_sigma!=admission.selected_sigma:raise ValueError('Selected sigma/admission mismatch')
    return True

def prepare_dynamic_branch(fixture,branch_id,budget,registration,*,selected_sigma,admission):
    from .stfbs_d1b_qm_execution import prepare_branch
    from .stfbs_d1b_qm_run_audit import verify_verified_registration
    if branch_id not in ('QM_B0_KEEP','QM_B1_MEMBER_CHANGE'):raise ValueError('Not B0/B1')
    verify_admission(admission,selected_sigma)
    registered=verify_verified_registration(Path(__file__).resolve().parents[2],fixture,branch_id,registration)
    branch=prepare_branch(fixture,branch_id,budget,registered,degraded_sigma=selected_sigma)
    if branch._sensor_authority.physical_profile_at(80)[1]['sigma']!=selected_sigma:raise ValueError('Physical sigma mismatch')
    return branch

def prepare_b3_branch(fixture,budget,registration):
    from .stfbs_d1b_qm_execution import prepare_branch,bind_shared_budget
    from .stfbs_d1b_qm_run_audit import verify_verified_registration
    registered=verify_verified_registration(Path(__file__).resolve().parents[2],fixture,'QM_B3_UNKNOWN',registration)
    branch=prepare_branch(fixture,'QM_B3_UNKNOWN',budget,registered,degraded_sigma=.02)
    bind_shared_budget(branch,budget)  # Recheck the untouched pre-sampling takeover window.
    branch._sensor_authority=MissingSensorAuthority()
    return branch

def prepare_probe_branch(fixture,branch_id,budget,registration):
    from .stfbs_d1b_qm_execution import prepare_branch,PROBES
    from .stfbs_d1b_qm_run_audit import verify_verified_registration
    if branch_id not in PROBES:raise ValueError('Not a probe identity')
    registered=verify_verified_registration(Path(__file__).resolve().parents[2],fixture,branch_id,registration)
    return prepare_branch(fixture,branch_id,budget,registered)

def real_estimator_binding(budget,approval=None):
    """Candidate call graph only. The first line rejects throughout RUN-G0."""
    require_run_g1(approval)
    from research.cooperative_sensing import estimator
    from unittest.mock import patch
    def call(payload):
        original=estimator.least_squares
        def measured(*args,**kwargs):return budget.record_solver(original,*args,**kwargs)
        with patch.object(estimator,'least_squares',measured):return estimator.estimate(payload)
    return call

def execute_probe(fixture,branch_id,budget,registration,*,approval=None):
    require_run_g1(approval)
    from .stfbs_d1b_qm_execution import prepare_branch,ProbeSchedule
    branch=prepare_probe_branch(fixture,branch_id,budget,registration)
    ProbeSchedule(branch,branch_id).run_to_80()
    return branch

def execute_dynamic(fixture,branch_id,budget,registration,*,selected_sigma,admission,approval=None):
    require_run_g1(approval)
    from .stfbs_d1b_qm_execution import DynamicSchedule
    branch=prepare_dynamic_branch(fixture,branch_id,budget,registration,selected_sigma=selected_sigma,admission=admission)
    DynamicSchedule(branch,branch_id).run_to_end()
    return branch
