"""RUN-G0 release wiring. RUN-G1 cannot be authorized by this version."""
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from .stfbs_d1b_qm_model import SensorAuthority,initial_team
from .stfbs_d1a_replay import digest

SIGMAS=(.04,.08,.16,.32)
LABEL='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'

# The independent user channel is outside the experiment, policy and output tree.
AUTHORITY_PATH=Path(r'C:\Users\14738\.codex\authorizations\D1_B_QM_1B_RUN_G1_EXPECTED.json')
_ROOT_SEAL=object();_PERMIT_SEAL=object()
from contextvars import ContextVar
from contextlib import contextmanager
import json,hashlib
_RUNTIME=ContextVar('d1b_real_runtime',default=None)

@dataclass(frozen=True)
class ApprovalExpectation:
    expected_sha256: str
    source: str
    evidence_kind: str

class _IndependentRoot:
    def __init__(self,expected,seal):
        if seal is not _ROOT_SEAL:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED')
        self.expected=expected;self.seal=seal

class RunPermit:
    def __init__(self,bindings,root,seal):
        if seal is not _PERMIT_SEAL or type(root) is not _IndependentRoot:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED')
        self.bindings=json.loads(json.dumps(bindings));self.root=root;self.seal=seal

REQUIRED_BINDINGS=('task','batch_id','source_pins','fixture_digest','world_digest','motion_rule','special_protocol',
    'branch_ids','outer_limit','inner_limit','category_limits','cpu_limit','wall_limit','output_dir','attempt_id',
    'audit_version','stop_rule','main_script_sha256','watchdog_script_sha256','runtime_pins')

def validate_approval_bytes(raw,expectation,expected_bindings):
    if type(expectation) not in (ApprovalExpectation,_IndependentRoot):raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED')
    wanted=expectation.expected_sha256 if type(expectation) is ApprovalExpectation else expectation.expected
    if not isinstance(wanted,str) or len(wanted)!=64 or hashlib.sha256(raw).hexdigest()!=wanted:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: independent digest')
    value=json.loads(raw)
    if type(expectation) is _IndependentRoot and value.get('evidence_kind')==LABEL:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: test ticket cannot become real')
    if value.get('status')!='APPROVED_FOR_ONE_D1B_RUN_G1' or any(k not in value for k in REQUIRED_BINDINGS):raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: ticket schema')
    if any(value[k]!=expected_bindings[k] for k in REQUIRED_BINDINGS):raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: binding mismatch')
    if value['task']!='D1-B-QM-1B-RUN-G1' or not value['source_pins'] or value['outer_limit']!=292 or value['inner_limit']!=2628 or value['cpu_limit']!=480 or value['wall_limit']!=600:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: scope')
    return dict(status='PURE_VALIDATION_PASS',ticket=value,real_execution_permission=False)

def load_independent_root():
    if not AUTHORITY_PATH.is_file():raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: independent user channel absent')
    row=json.loads(AUTHORITY_PATH.read_bytes())
    if row.get('source')!='USER_INDEPENDENT_CONFIRMATION' or row.get('task')!='D1-B-QM-1B-RUN-G1' or row.get('evidence_kind')==LABEL or not row.get('user_confirmation_record'):raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: independent source')
    return _IndependentRoot(row['expected_sha256'],_ROOT_SEAL)

def authorize_policy(policy_path):
    root=load_independent_root();raw=Path(policy_path).read_bytes();value=json.loads(raw)
    from .stfbs_d1b_qm_run_audit import SourceAnchor,verify_source_pins
    from .stfbs_d1b_qm_run_audit import NEW_FILES
    validate_approval_bytes(raw,root,value)
    required_sources=NEW_FILES+('research/non_oracle/stfbs_d1a_model.py','research/non_oracle/stfbs_d1a_history.py','research/non_oracle/stfbs_d1a_history_audit.py','research/non_oracle/stfbs_d1a_audit.py','research/non_oracle/stfbs_d1a_state.py','research/non_oracle/belief.py','research/non_oracle/policy.py','research/non_oracle/stfbs_d1b_qm_scenario.py','research/non_oracle/stfbs_d1b_qm_model.py','research/non_oracle/stfbs_d1b_qm_independent_audit.py','research/cooperative_sensing/estimator.py','research/information_service_bridge/public_stream.py','research/information_service/public_quality.py','pursuit_v2/config.py','pursuit_v2/observation_geometry.py','pursuit_v2/service.py')
    if any(path not in value['source_pins'] for path in required_sources):raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: incomplete scientific source pins')
    verify_source_pins(Path(__file__).resolve().parents[2],value['source_pins'],SourceAnchor('USER_APPROVED_RUN_G1',json.dumps(value['source_pins'],sort_keys=True)))
    from .stfbs_d1b_qm_scenario import build_fixture
    f=build_fixture()
    if value['fixture_digest']!=digest(dict(view=f.view,seed=f.seed,identity=f.identity)) or value['world_digest']!=f.world['world_digest'] or value['motion_rule']!=f.world['motion_rule']:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: fixture/world')
    paths=('scripts/stfbs_d1b_qm_run_g1.py','scripts/stfbs_d1b_qm_run_g1_watchdog.py')
    for path,field in zip(paths,('main_script_sha256','watchdog_script_sha256')):
        if value['source_pins'].get(path)!=value[field]:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: entry pins')
    if value['branch_ids']!=['QM_PROBE_OLD']+['QM_PROBE_DEGRADED_'+str(i) for i in range(1,5)]+['QM_B0_KEEP','QM_B1_MEMBER_CHANGE','QM_B3_UNKNOWN','QM_F2_VALID_HISTORY','QM_F3_STREAM_A','QM_F3_STREAM_B']:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: identities')
    if value['special_protocol']!='F2_B1_LEFT80_U0_U2__F3_B0_RIGHT80_B1_LEFT80_V1' or value['category_limits']!=dict(MODEL_OBSERVATION_WLS=289,MODEL_SPECIAL_TEST_WLS=3,MODEL_POLICY_EVALUATION_WLS=0,MODEL_INDEPENDENT_AUDIT_WLS=0,ACTUAL_WLS=0):raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: specialty/caps')
    output=Path(value['output_dir']).resolve();repo=Path(__file__).resolve().parents[2]
    if not output.is_relative_to(repo/'runs') or not value['attempt_id'] or not value['batch_id']:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: output/attempt')
    import sys
    if not value['runtime_pins'] or str(Path(sys.executable).resolve()) not in value['runtime_pins']:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: runtime pins')
    reference=json.loads((Path(__file__).resolve().parents[2]/'reports/stfbs_lite_d1a_h1_preflight_lock_001/RUNTIME_IDENTITY.json').read_bytes())['runtime']
    required_runtime=[reference[k]['module_file'] for k in ('numpy','scipy','psutil')]+list(reference['python']['DLLs'])+list(reference['psutil_native'])
    if any(name not in value['runtime_pins'] for name in required_runtime):raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: incomplete runtime pins')
    for name,wanted in value['runtime_pins'].items():
        target=Path(name).resolve()
        if not target.is_relative_to(Path(sys.executable).resolve().parent) or not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest()!=wanted:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: runtime changed')
    if value['audit_version']!='D1B_RELEASE_AUDIT_V1' or value['stop_rule']!='ONE_ATTEMPT_STOP_ON_ANY_CONTRACT_FAILURE':raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: audit/stop rule')
    return RunPermit(value,root,_PERMIT_SEAL)

@contextmanager
def runtime_scope(permit,launch_evidence):
    if type(permit) is not RunPermit or permit.seal is not _PERMIT_SEAL or launch_evidence.get('actual_windows_job') is not True or launch_evidence.get('attempt_id')!=permit.bindings['attempt_id']:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: real scope')
    if _RUNTIME.get() is not None:raise PermissionError('Nested runtime forbidden')
    token=_RUNTIME.set(permit)
    try:yield permit
    finally:_RUNTIME.reset(token)

def require_run_g1(approval=None):
    permit=_RUNTIME.get()
    if type(permit) is not RunPermit or permit.seal is not _PERMIT_SEAL or type(permit.root) is not _IndependentRoot or permit.root.seal is not _ROOT_SEAL:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED')
    if approval is not None and approval is not permit:raise PermissionError('RUN_G1_APPROVAL_NOT_VERIFIED: foreign context')
    return permit

def execute_test_plan(pure_validation,port):
    """Separate simulation channel: never installs _RUNTIME or returns RunPermit."""
    cls=type(port)
    if pure_validation.get('status')!='PURE_VALIDATION_PASS' or pure_validation.get('real_execution_permission') is not False or cls.__module__!='tests.test_stfbs_d1b_qm_run_release' or cls.__name__!='SyntheticOps' or getattr(port,'evidence_kind',None)!=LABEL:raise PermissionError('Only registered synthetic operation port')
    from .stfbs_d1b_qm_run_evidence import coordinate_batch
    return coordinate_batch(port)


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

def _freeze_rows(rows,source_run_identity):
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

_ISSUED_ADMISSIONS={}

def freeze_admission(candidates,source_run_identity):
    from .stfbs_d1b_qm_run_evidence import TrustedCandidate,_CANDIDATE_SEAL
    permit=require_run_g1()
    if source_run_identity!=permit.bindings['batch_id'] or not candidates or any(type(c) is not TrustedCandidate or c.seal is not _CANDIDATE_SEAL or c.evidence_kind!='MODEL' for c in candidates):raise PermissionError('Admission requires real independently audited candidates')
    result=_freeze_rows([json.loads(c.row_json) for c in candidates],source_run_identity)
    _ISSUED_ADMISSIONS[id(result)]=result
    return result

def verify_admission(admission,selected_sigma):
    require_run_g1()
    if type(admission) is not Admission or _ISSUED_ADMISSIONS.get(id(admission)) is not admission:raise PermissionError('Unissued admission rejected')
    expected=_freeze_rows(json.loads(admission.evidence_json),admission.source_run_identity)
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
    from .stfbs_d1b_qm_execution import prepare_branch
    from .stfbs_d1b_qm_run_audit import verify_verified_registration
    registered=verify_verified_registration(Path(__file__).resolve().parents[2],fixture,'QM_B3_UNKNOWN',registration)
    branch=prepare_branch(fixture,'QM_B3_UNKNOWN',budget,registered,degraded_sigma=.02)
    branch._sensor_authority=MissingSensorAuthority()
    return branch

def prepare_probe_branch(fixture,branch_id,budget,registration):
    from .stfbs_d1b_qm_execution import prepare_branch,PROBES
    from .stfbs_d1b_qm_run_audit import verify_verified_registration
    if branch_id not in PROBES:raise ValueError('Not a probe identity')
    registered=verify_verified_registration(Path(__file__).resolve().parents[2],fixture,branch_id,registration)
    return prepare_branch(fixture,branch_id,budget,registered)

def real_estimator_binding(budget,approval=None):
    permit=require_run_g1(approval)
    return budget.install_real_backend(permit)

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


def verify_g1_launch(permit,approval_path,launch_path):
    import os,sys,ctypes,psutil
    from ctypes import wintypes as W
    repo=Path(__file__).resolve().parents[2];v=permit.bindings
    if not sys.flags.isolated or not sys.dont_write_bytecode:raise PermissionError('RUN_G1 requires isolated child')
    launch_path=Path(launch_path).resolve();output=Path(v['output_dir']).resolve()
    if launch_path!=output/'WATCHDOG'/'LAUNCH.json':raise PermissionError('RUN_G1 launch path mismatch')
    launch=json.loads(launch_path.read_bytes());attempt=json.loads((output/'ATTEMPT.json').read_bytes())
    me=psutil.Process();parent=me.parent()
    expected=[str(Path(sys.executable).resolve()),'-I','-B',str(repo/'scripts/stfbs_d1b_qm_run_g1.py'),'--approval-file',str(Path(approval_path).resolve()),'--launch-ticket',str(launch_path)]
    if me.cmdline()!=expected or parent is None or parent.pid!=launch['watchdog_pid'] or me.pid!=launch['child_pid']:raise PermissionError('RUN_G1 process identity mismatch')
    if str(repo/'scripts/stfbs_d1b_qm_run_g1_watchdog.py') not in parent.cmdline() or attempt['watchdog_pid']!=parent.pid or attempt['watchdog_create_time']!=parent.create_time():raise PermissionError('RUN_G1 parent mismatch')
    if attempt['attempt_id']!=v['attempt_id'] or attempt['batch_id']!=v['batch_id'] or attempt['approval_sha256']!=permit.root.expected or launch['approval_sha256']!=permit.root.expected or not launch['assigned_before_resume'] or launch['wall_limit']!=v['wall_limit']:raise PermissionError('RUN_G1 approval/Job ticket mismatch')
    api=ctypes.WinDLL('kernel32',use_last_error=True);api.GetCurrentProcess.restype=W.HANDLE
    api.IsProcessInJob.argtypes=[W.HANDLE,W.HANDLE,ctypes.POINTER(W.BOOL)];api.IsProcessInJob.restype=W.BOOL;member=W.BOOL()
    if not api.IsProcessInJob(api.GetCurrentProcess(),None,ctypes.byref(member)) or not member.value:raise PermissionError('RUN_G1 not in Windows Job')
    return dict(actual_windows_job=True,attempt_id=v['attempt_id'],child_pid=me.pid,parent_pid=parent.pid,command=me.cmdline(),approval_sha256=permit.root.expected)
