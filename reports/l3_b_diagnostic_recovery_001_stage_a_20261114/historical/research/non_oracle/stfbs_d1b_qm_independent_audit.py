"""QM1BENG launch, static identity, public-graph and zero-science audit helpers."""
import ast,ctypes,hashlib,inspect,json,math,os,sys,time,traceback,subprocess
from pathlib import Path
from contextlib import contextmanager

HEAD='69c862f406fe155351ff1adb78be432131b01564'
TASK='D1-B-QM-1B-ENG';SUITE='eng_interface_v1';LABEL='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'
NEW_FILES=('research/non_oracle/stfbs_d1b_qm_execution.py','research/non_oracle/stfbs_d1b_qm_budget.py','research/non_oracle/stfbs_d1b_qm_independent_audit.py','tests/test_stfbs_d1b_qm1b_eng.py','scripts/stfbs_d1b_qm1b_eng_test_entry.py','scripts/stfbs_d1b_qm1b_eng_test_watchdog.py')
NAMES=('test_execution_branch_identity_isolation', 'test_old_probe_not_used_as_dynamic_right80', 'test_tick80_event_order_with_test_doubles', 'test_left80_feedback_not_consumed_at_freeze80', 'test_dynamic_public_authority_boundary', 'test_motion_rule_authority_static_contract', 'test_d1b_budget_categories_and_shared_cap', 'test_budget_failure_not_rolled_back', 'test_external_history_context_independence', 'test_real_execution_requires_run_authorization')
IDS=tuple('tests.test_stfbs_d1b_qm1b_eng.QM1BTests.'+n for n in NAMES)
_ACTIVE=None
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)

def static_preflight(root):
    root=Path(root).resolve();report=root/'reports/stfbs_lite_d1b_qm1b_eng_001';base=read(report/'BASELINE.json')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!=HEAD:raise ValueError('QM1BENG_HEAD_MISMATCH')
    for p,s in {**base['existing_source_pins'],**base['protected_archives'],**base['protected_manifests']}.items():
        if sha(root/p)!=s:raise ValueError('FROZEN_FILE_CHANGED: '+p)
    changed=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=root,text=True).splitlines()
    if changed:raise ValueError('EXISTING_TRACKED_FILE_CHANGED: '+repr(changed))
    others=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=root,text=True).splitlines()
    if any(p not in NEW_FILES and not p.startswith('reports/stfbs_lite_d1b_qm1b_eng_001/') for p in others):raise ValueError('UNAPPROVED_NEW_PATH')
    for p in NEW_FILES:
        text=(root/p).read_text(encoding='utf-8-sig');compile(text,str(root/p),'exec')
    tree=ast.parse((root/NEW_FILES[3]).read_text(encoding='utf-8-sig'))
    names=[n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    if sorted(names)!=sorted(NAMES) or len(names)!=10:raise ValueError('TEST_AST_WHITELIST_MISMATCH')
    for n in ast.walk(tree):
        if isinstance(n,(ast.Assign,ast.AnnAssign)):
            targets=n.targets if isinstance(n,ast.Assign) else [n.target]
            if any(isinstance(t,ast.Attribute) and t.attr in ('estimate','least_squares','run','advance','step','process','fuse') for t in targets):raise ValueError('TEST_RESTORES_SCIENTIFIC_ENTRY')
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('eval','exec','__import__'):raise ValueError('DYNAMIC_TEST_IMPORT_OR_EXEC')
    return dict(source_pins={**base['existing_source_pins'],**{p:sha(root/p) for p in NEW_FILES}},new_source_pins={p:sha(root/p) for p in NEW_FILES},baseline_sha256=sha(report/'BASELINE.json'))

def verify_launch(root,args):
    """Called before importing any test or scientific module."""
    import psutil
    from ctypes import wintypes as W
    root=Path(root).resolve();policy_path=Path(args.run_policy).resolve()
    if not sys.flags.isolated or not sys.dont_write_bytecode:raise ValueError('ISOLATED_NO_BYTECODE_REQUIRED')
    if sha(policy_path)!=args.policy_sha256:raise ValueError('RUN_POLICY_DIGEST_MISMATCH')
    p=read(policy_path);launch_path=Path(args.launch_ticket).resolve();launch=read(launch_path)
    if p['task']!=TASK or p['suite']!=SUITE or args.suite!=SUITE or p['test_ids']!=list(IDS):raise ValueError('QM1BENG_SUITE_IDENTITY')
    if Path(p['root']).resolve()!=root or Path.cwd().resolve()!=root:raise ValueError('QM1BENG_ROOT_OR_CWD')
    if Path(sys.argv[0]).resolve()!=Path(p['entry_script']).resolve() or Path(sys.executable).resolve()!=Path(p['python']).resolve():raise ValueError('QM1BENG_SCRIPT_OR_PYTHON')
    expected=[args.policy_sha256 if s=='<RUN_POLICY_SHA256>' else s for s in p['allowed_child_command']]
    me=psutil.Process();parent=psutil.Process(os.getppid())
    if me.cmdline()!=expected or parent.cmdline()!=p['watchdog_command']:raise ValueError('QM1BENG_COMMAND_MISMATCH')
    if launch['child_pid']!=os.getpid() or launch['watchdog_pid']!=parent.pid or p['watchdog_pid']!=parent.pid:raise ValueError('QM1BENG_PID_BINDING')
    if parent.create_time()!=p['watchdog_create_time'] or not parent.create_time()<=me.create_time()<=time.time()+1:raise ValueError('QM1BENG_PROCESS_CREATION_BINDING')
    if Path(p['watchdog_script']).resolve() not in [Path(a).resolve() for a in parent.cmdline() if a.endswith('.py')]:raise ValueError('QM1BENG_PARENT_SCRIPT')
    if (p['wall_limit'],p['cpu_limit'],p['attempts'])!=(180,120,1) or launch['wall_limit']!=180 or launch['assigned_before_resume'] is not True or launch.get('approval_sha256') is not None:raise ValueError('QM1BENG_LIMIT_OR_JOB_TICKET')
    if launch_path!=Path(p['evidence_dir'])/'LAUNCH.json':raise ValueError('QM1BENG_LAUNCH_PATH')
    api=ctypes.WinDLL('kernel32',use_last_error=True);api.GetCurrentProcess.restype=W.HANDLE
    api.IsProcessInJob.argtypes=[W.HANDLE,W.HANDLE,ctypes.POINTER(W.BOOL)];api.IsProcessInJob.restype=W.BOOL
    member=W.BOOL()
    if not api.IsProcessInJob(api.GetCurrentProcess(),None,ctypes.byref(member)):raise ctypes.WinError(ctypes.get_last_error())
    if not member.value:raise ValueError('QM1BENG_NOT_IN_WINDOWS_JOB')
    for name,s in p['source_pins'].items():
        if sha(root/name)!=s:raise ValueError('QM1BENG_SOURCE_IDENTITY: '+name)
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!=p['head']:raise ValueError('QM1BENG_HEAD_CHANGED')
    if sha(sys.executable)!=p['python_sha256']:raise ValueError('QM1BENG_PYTHON_IDENTITY')
    attempt=read(policy_path.parent/'TEST_ATTEMPT.json')
    if attempt['policy_sha256']!=args.policy_sha256 or attempt['attempt']!=1 or attempt['watchdog_pid']!=parent.pid:raise ValueError('QM1BENG_ATTEMPT_BINDING')
    return p,dict(status='PASS',child_pid=me.pid,parent_pid=parent.pid,parent_create_time=parent.create_time(),child_create_time=me.create_time(),actual_command=me.cmdline(),watchdog_command=parent.cmdline(),cwd=str(Path.cwd()),in_windows_job=True,policy_sha256=args.policy_sha256,launch_sha256=sha(launch_path),isolated=True,no_bytecode=True)

class ForbiddenScienceCall(RuntimeError):pass
class GuardRegistry:
    def __init__(self):
        self.entries=[];self.calls=[];self.checks=[];self.scopes=[];self.current_test=None;self.allowed_fake=None;self.overwritten=False
    def add(self,owner,attribute,category):
        original=getattr(owner,attribute)
        if getattr(original,'_qm1a_guard',False):guard=original
        else:
            label=getattr(owner,'__name__',repr(owner))+'.'+attribute
            def guard(*args,**kwargs):
                self.calls.append(dict(category=category,entry=label,test=self.current_test,stack=traceback.format_stack(limit=8)))
                raise ForbiddenScienceCall('FORBIDDEN_SCIENTIFIC_CALL: '+label)
            guard._qm1a_guard=True
        setattr(owner,attribute,guard);self.entries.append((owner,attribute,guard,category))
        return original,guard
    def integrity(self,phase):
        broken=[]
        for owner,attr,guard,category in self.entries:
            expected=self.allowed_fake if self.allowed_fake is not None and getattr(owner,'__name__','')=='Branch' and attr=='fuse' else guard
            if getattr(owner,attr) is not expected:broken.append(getattr(owner,'__name__','')+'.'+attr)
        self.checks.append(dict(phase=phase,broken=broken,forbidden_attempts=len(self.calls),fake_scope=self.allowed_fake is not None))
        if broken:self.overwritten=True;raise RuntimeError('GUARD_OVERWRITTEN: '+repr(broken))
    def note_double(self,description):
        self.scopes.append(dict(test=self.current_test,label=LABEL,description=description,kind='pure synthetic data',physical_evidence=False))
    @contextmanager
    def fake_scope(self,description,fn):
        from .stfbs_d1a_model import Branch
        if getattr(fn,'evidence_kind',None)!=LABEL or self.allowed_fake is not None:raise ValueError('Unregistered/nested fake fusion')
        self.integrity('before fake: '+description)
        previous=Branch.fuse;record=dict(test=self.current_test,label=LABEL,description=description,kind='fusion substitute',closed=False,physical_evidence=False)
        self.scopes.append(record);self.allowed_fake=fn;Branch.fuse=fn
        try:
            self.integrity('entered fake: '+description);yield
        finally:
            Branch.fuse=previous;self.allowed_fake=None;record['closed']=True
            self.integrity('after fake: '+description)
    def ledger(self):
        categories=('WLS','FUSION','MODEL_ADVANCE','ACTUAL_STEP','SAMPLING','QUALITY','POLICY_SEARCH')
        return dict(installed_entries=[dict(owner=getattr(o,'__name__',repr(o)),attribute=a,category=c,guard_installed=getattr(o,a) is g) for o,a,g,c in self.entries],
            forbidden_attempts={c:sum(x['category']==c for x in self.calls) for c in categories},attempt_details=self.calls,actual_scientific_execution={k:None if self.overwritten else 0 for k in ('WLS','MODEL_advance','ACTUAL_STEP')},
            guard_checks=self.checks,fake_fuse_scopes=self.scopes,ever_overwritten=self.overwritten,scope='Known reachable whitelist call graph; no intentional guard calls; substitutes are not physical evidence')

def install_guards():
    """No original solver reference is exposed to the tests; aliases are patched too."""
    global _ACTIVE
    import scipy.optimize as opt
    from research.cooperative_sensing import estimator
    registry=GuardRegistry();_ACTIVE=registry;originals=[]
    for owner,attr in ((estimator,'estimate'),(estimator,'least_squares'),(opt,'least_squares')):
        originals.append(registry.add(owner,attr,'WLS'))
    from research.non_oracle import stfbs_d1a_model as m,policy
    from research.non_oracle import stfbs_d1b_qm_model as qm
    from research.non_oracle import stfbs_d1b_qm_execution as execution
    from research.information_service_bridge import public_stream as bridge
    from research.information_service import public_quality as quality
    from research.information_service_online.execution import OnlineEnvironment
    from pursuit_v2.environment import Environment,TimedEnvironment
    from pursuit_v2 import service
    targets=[(m,'estimate','WLS'),(policy,'estimate','WLS'),(m.Budget,'estimator','WLS'),
        (bridge,'_estimate','WLS'),(quality,'_estimate','WLS'),(quality,'assess_quality','QUALITY'),(bridge,'assess_quality','QUALITY'),(policy,'assess_quality','QUALITY'),
        (execution.DynamicSchedule,'run_to_end','MODEL_ADVANCE'),(m.Branch,'fuse','FUSION'),(bridge.BridgeFrameProcessor,'process','FUSION'),(quality.FrameProcessor,'process','FUSION'),
        (m.Branch,'raw','SAMPLING'),(qm.QMBranch,'raw','SAMPLING'),(m.Branch,'advance','MODEL_ADVANCE'),(m.Branch,'run','MODEL_ADVANCE'),(m.Branch,'finish','MODEL_ADVANCE'),(qm.QMBranch,'run','MODEL_ADVANCE'),
        (OnlineEnvironment,'step','ACTUAL_STEP'),(OnlineEnvironment,'_advance_tick','ACTUAL_STEP'),(OnlineEnvironment,'_sample','SAMPLING'),(OnlineEnvironment,'_fuse','FUSION'),(Environment,'step','ACTUAL_STEP'),(TimedEnvironment,'step','ACTUAL_STEP'),
        (service,'rollout_fixed_service','MODEL_ADVANCE'),(service,'advance_clock','MODEL_ADVANCE'),(m,'advance_clock','MODEL_ADVANCE'),(policy,'advance_clock','MODEL_ADVANCE'),(policy,'decide','POLICY_SEARCH'),(policy,'evaluate','POLICY_SEARCH')]
    for owner,attr,category in targets:originals.append(registry.add(owner,attr,category))
    # Catch already-imported estimate/solver/processor aliases, including SciPy exports.
    for module in list(sys.modules.values()):
        if module is None:continue
        for attr,value in list(vars(module).items()):
            for original,guard in originals:
                if value is original and original is not guard:
                    setattr(module,attr,guard);registry.entries.append((module,attr,guard,'ALIAS'));break
    originals.clear();registry.integrity('installed before test import')
    return registry

def active_registry():
    if _ACTIVE is None:raise RuntimeError('Protected test runner required')
    return _ACTIVE

def assert_public_surface(value):
    """Inspect actual reachable objects, not just JSON key spellings."""
    from .stfbs_d1b_qm_model import PublicProfiles,SensorAuthority,QMBranch
    seen=set()
    def visit(obj):
        if id(obj) in seen:return
        seen.add(id(obj))
        if obj is None or type(obj) in (str,int,float,bool):return
        if isinstance(obj,(SensorAuthority,QMBranch)):raise ValueError('PRIVATE_EXECUTOR_REACHABLE')
        if type(obj) is PublicProfiles:
            if obj.public_profile_at.__func__.__closure__:raise ValueError('PUBLIC_CLOSURE_REACHABLE')
            visit(obj.to_public_dict());return
        if isinstance(obj,dict):
            if any(k in obj for k in ('_schedule','private_schedule','sensor_declaration_schedule','private_environment')):raise ValueError('PRIVATE_SCHEDULE_FIELD')
            for k,v in obj.items():visit(k);visit(v)
            return
        if isinstance(obj,(list,tuple,set)):
            for child in obj:visit(child)
            return
        if callable(obj):raise ValueError('PUBLIC_CALLABLE_OR_CLOSURE_REACHABLE')
        raise ValueError('UNAPPROVED_PUBLIC_OBJECT: '+type(obj).__name__)
    visit(value)
    return dict(status='PASS',scope='Detached public data/snapshot reachable graph, no private instance or captured callbacks; not a malicious-Python sandbox')

def verify_receipts(report):
    report=Path(report);p=read(report/'RUN_POLICY.json');attempt=read(report/'TEST_ATTEMPT.json')
    w=read(Path(p['evidence_dir'])/'WATCHDOG_RECEIPT.json');launch=read(Path(p['evidence_dir'])/'LAUNCH.json')
    bind=read(report/'LAUNCH_BINDING.json');tests=read(report/'DETERMINISTIC_TEST_RESULTS.json');ledger=read(report/'FORBIDDEN_CALL_LEDGER.json')
    if p['task']!=TASK or p['suite']!=SUITE or p['test_ids']!=list(IDS) or attempt['policy_sha256']!=sha(report/'RUN_POLICY.json'):raise ValueError('POLICY_NOT_VERIFIED')
    if (w['wall_limit'],w['cpu_limit'],w['attempts'],w['status'],w['exit_code'])!=(180,120,1,'EXITED',0):raise ValueError('SUPERVISION_NOT_VERIFIED')
    if not w['cpu_complete'] or w['active_processes']!=0 or w.get('descendant_cleanup'):raise ValueError('JOB_ACCOUNTING_NOT_VERIFIED')
    for key,limit in (('tree_cpu_seconds',120),('process_cpu_seconds',120),('wall_seconds',180)):
        v=w.get(key)
        if type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=limit:raise ValueError('RESOURCE_NOT_VERIFIED: '+key)
    if launch['wall_limit']!=180 or not launch['assigned_before_resume'] or not bind['in_windows_job']:raise ValueError('JOB_BINDING_NOT_VERIFIED')
    if launch['child_pid']!=w['child_pid'] or bind['child_pid']!=w['child_pid'] or launch['watchdog_pid']!=w['watchdog_pid'] or bind['parent_pid']!=w['watchdog_pid']:raise ValueError('PID_NOT_VERIFIED')
    if bind['policy_sha256']!=sha(report/'RUN_POLICY.json') or bind['actual_command']!=w['command']:raise ValueError('COMMAND_NOT_VERIFIED')
    if tests['executed_ids']!=list(IDS) or len(set(tests['executed_ids']))!=10 or not tests['all_passed'] or tests['skips'] or tests['unexpected_successes']:raise ValueError('TWELVE_TESTS_NOT_VERIFIED')
    if ledger['ever_overwritten'] or any(ledger['forbidden_attempts'].values()) or any(ledger['actual_scientific_execution'].values()):raise ValueError('ZERO_SCIENCE_NOT_VERIFIED')
    if any(c['broken'] for c in ledger['guard_checks']) or any(not x['guard_installed'] for x in ledger['installed_entries']):raise ValueError('GUARDS_NOT_VERIFIED')
    if any(s.get('kind')=='fusion substitute' and not s['closed'] for s in ledger['fake_fuse_scopes']):raise ValueError('FAKE_SCOPE_NOT_CLOSED')
    for name,s in p['source_pins'].items():
        if sha(Path(p['root'])/name)!=s:raise ValueError('POSTRUN_SOURCE_CHANGED')
    return dict(status='PASS',task=TASK,suite=SUITE,policy_sha256=sha(report/'RUN_POLICY.json'),production_launch_marker=w.get('production_launch'),production_marker_note='None approval is correct for this engineering suite; no H1 validator used',test_count=10,zero_science=True)

# External fixture registrations are frozen BEFORE branch construction.
from dataclasses import dataclass

@dataclass(frozen=True)
class ExternalRegistration:
    branch_id: str
    fixture_digest: str
    prefix_json: str
    source_pins_json: str
    registration_digest: str

def register_fixture(fixture,branch_id,source_pins):
    from .stfbs_d1b_qm_scenario import validate_fixture
    from .stfbs_d1b_qm_execution import IDENTITIES
    from .stfbs_d1a_replay import digest
    validate_fixture(fixture)
    if branch_id not in IDENTITIES or not source_pins:raise ValueError('External registration identity/pins required')
    prefix=json.dumps({h['target_id']:h for h in fixture.view['histories']},sort_keys=True)
    payload=dict(branch_id=branch_id,fixture_digest=digest(dict(view=fixture.view,seed=fixture.seed,world=fixture.world,identity=fixture.identity)),prefix_json=prefix,source_pins_json=json.dumps(source_pins,sort_keys=True))
    return ExternalRegistration(**payload,registration_digest=digest(payload))

def verify_registration(registration,fixture,branch_id):
    if type(registration) is not ExternalRegistration:raise ValueError('External registration required')
    expected=register_fixture(fixture,branch_id,json.loads(registration.source_pins_json))
    if expected!=registration:raise ValueError('Fixture/prefix/branch registration mismatch')
    return True

def audit_registered(branch,registration):
    from .stfbs_d1a_history_audit import AuditContext,audit_branch_independent
    from .stfbs_d1a_replay import digest
    if type(registration) is not ExternalRegistration:raise ValueError('External registration required')
    payload={k:getattr(registration,k) for k in ('branch_id','fixture_digest','prefix_json','source_pins_json')}
    if digest(payload)!=registration.registration_digest or branch.name!=registration.branch_id:raise ValueError('External identity mismatch')
    # Never reads branch._audit_context; frozen prefix supplied by external registration.
    return audit_branch_independent(branch,context=AuditContext(registration.branch_id,registration.prefix_json))
