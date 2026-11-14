"""One isolated eight-method patch suite and its independent launch checks."""
import argparse,ast,ctypes,hashlib,io,json,math,os,subprocess,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HEAD='a175734551a9e259b62d3c93c41f94b463108d02'
TASK='D1-B-QM-1B-RUN-RELEASE-PATCH';SUITE='release_patch_v1';LABEL='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'
REPORT=ROOT/'reports/stfbs_lite_d1b_qm_run_release_patch_001'
PATCH_FILES=('scripts/stfbs_d1b_qm_run_g1_watchdog.py','research/non_oracle/stfbs_d1b_qm_run_evidence.py','tests/test_stfbs_d1b_qm_run_release_patch.py','scripts/stfbs_d1b_qm_run_release_patch_test_entry.py','scripts/stfbs_d1b_qm_run_release_patch_watchdog.py')
_REGISTRY=None
NAMES=('test_resource_receipt_accepts_valid_and_exact_limit', 'test_resource_receipt_rejects_cpu_and_wall_excess', 'test_resource_receipt_rejects_nonfinite_negative_missing_and_bool', 'test_resource_receipt_rejects_approved_limit_mismatch', 'test_scenario_admission_early_stop_has_complete_science', 'test_no_q_only_fail_early_stop_has_complete_science', 'test_dynamic_not_realized_preserves_executed_b0_b1', 'test_early_stop_science_semantics_and_no_scientific_execution')
IDS=tuple('tests.test_stfbs_d1b_qm_run_release_patch.PatchTests.'+n for n in NAMES)

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_bytes())
def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
def active_registry():
    if _REGISTRY is None:raise RuntimeError('Protected patch runner required')
    return _REGISTRY

def static_preflight():
    base=read(REPORT/'BASELINE.json')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!=HEAD:raise ValueError('PATCH_HEAD_MISMATCH')
    for name,wanted in base['source_pins'].items():
        if name not in base['allowed_modifications'] and sha(ROOT/name)!=wanted:raise ValueError('PROTECTED_FILE_CHANGED: '+name)
    for name,wanted in base['runtime_pins'].items():
        if sha(name)!=wanted:raise ValueError('RUNTIME_CHANGED: '+name)
    changed=subprocess.check_output(['git','diff','HEAD','--name-only'],cwd=ROOT,text=True).splitlines()
    if any(n not in base['allowed_modifications'] for n in changed):raise ValueError('UNAPPROVED_SOURCE_MODIFICATION')
    others=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    if any(n not in base['new_files'] and not n.startswith('reports/stfbs_lite_d1b_qm_run_release_patch_001/') for n in others):raise ValueError('UNAPPROVED_NEW_FILE')
    for path in PATCH_FILES:compile((ROOT/path).read_text(encoding='utf-8-sig'),str(ROOT/path),'exec')
    tree=ast.parse((ROOT/PATCH_FILES[2]).read_text(encoding='utf-8-sig'))
    found=[n.name for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    if len(found)!=8 or sorted(found)!=sorted(NAMES):raise ValueError('PATCH_EIGHT_METHOD_WHITELIST_MISMATCH')
    return dict(source_pins={**base['source_pins'],**{n:sha(ROOT/n) for n in PATCH_FILES}},patch_source_pins={n:sha(ROOT/n) for n in PATCH_FILES})
def verify_launch(root,args):
    """Called before importing any test or scientific module."""
    import psutil
    from ctypes import wintypes as W
    root=Path(root).resolve();policy_path=Path(args.run_policy).resolve()
    if not sys.flags.isolated or not sys.dont_write_bytecode:raise ValueError('ISOLATED_NO_BYTECODE_REQUIRED')
    if sha(policy_path)!=args.policy_sha256:raise ValueError('RUN_POLICY_DIGEST_MISMATCH')
    p=read(policy_path);launch_path=Path(args.launch_ticket).resolve();launch=read(launch_path)
    if p['task']!=TASK or p['suite']!=SUITE or args.suite!=SUITE or p['test_ids']!=list(IDS):raise ValueError('RUN_G0_SUITE_IDENTITY')
    if Path(p['root']).resolve()!=root or Path.cwd().resolve()!=root:raise ValueError('RUN_G0_ROOT_OR_CWD')
    if Path(sys.argv[0]).resolve()!=Path(p['entry_script']).resolve() or Path(sys.executable).resolve()!=Path(p['python']).resolve():raise ValueError('RUN_G0_SCRIPT_OR_PYTHON')
    expected=[args.policy_sha256 if s=='<RUN_POLICY_SHA256>' else s for s in p['allowed_child_command']]
    me=psutil.Process();parent=psutil.Process(os.getppid())
    if me.cmdline()!=expected or parent.cmdline()!=p['watchdog_command']:raise ValueError('RUN_G0_COMMAND_MISMATCH')
    if launch['child_pid']!=os.getpid() or launch['watchdog_pid']!=parent.pid or p['watchdog_pid']!=parent.pid:raise ValueError('RUN_G0_PID_BINDING')
    if parent.create_time()!=p['watchdog_create_time'] or not parent.create_time()<=me.create_time()<=time.time()+1:raise ValueError('RUN_G0_PROCESS_CREATION_BINDING')
    if Path(p['watchdog_script']).resolve() not in [Path(a).resolve() for a in parent.cmdline() if a.endswith('.py')]:raise ValueError('RUN_G0_PARENT_SCRIPT')
    if (p['wall_limit'],p['cpu_limit'],p['attempts'])!=(180,120,1) or launch['wall_limit']!=180 or launch['assigned_before_resume'] is not True or launch.get('approval_sha256') is not None:raise ValueError('RUN_G0_LIMIT_OR_JOB_TICKET')
    if launch_path!=Path(p['evidence_dir'])/'LAUNCH.json':raise ValueError('RUN_G0_LAUNCH_PATH')
    api=ctypes.WinDLL('kernel32',use_last_error=True);api.GetCurrentProcess.restype=W.HANDLE
    api.IsProcessInJob.argtypes=[W.HANDLE,W.HANDLE,ctypes.POINTER(W.BOOL)];api.IsProcessInJob.restype=W.BOOL
    member=W.BOOL()
    if not api.IsProcessInJob(api.GetCurrentProcess(),None,ctypes.byref(member)):raise ctypes.WinError(ctypes.get_last_error())
    if not member.value:raise ValueError('RUN_G0_NOT_IN_WINDOWS_JOB')
    for name,s in p['source_pins'].items():
        if sha(root/name)!=s:raise ValueError('RUN_G0_SOURCE_IDENTITY: '+name)
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()!=p['head']:raise ValueError('RUN_G0_HEAD_CHANGED')
    if sha(sys.executable)!=p['python_sha256']:raise ValueError('RUN_G0_PYTHON_IDENTITY')
    attempt=read(policy_path.parent/'TEST_ATTEMPT.json')
    if attempt['policy_sha256']!=args.policy_sha256 or attempt['attempt']!=1 or attempt['watchdog_pid']!=parent.pid:raise ValueError('RUN_G0_ATTEMPT_BINDING')
    return p,dict(status='PASS',child_pid=me.pid,parent_pid=parent.pid,parent_create_time=parent.create_time(),child_create_time=me.create_time(),actual_command=me.cmdline(),watchdog_command=parent.cmdline(),cwd=str(Path.cwd()),in_windows_job=True,policy_sha256=args.policy_sha256,launch_sha256=sha(launch_path),isolated=True,no_bytecode=True)

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
    if tests['executed_ids']!=list(IDS) or len(set(tests['executed_ids']))!=8 or not tests['all_passed'] or tests['skips'] or tests['unexpected_successes']:raise ValueError('TWELVE_TESTS_NOT_VERIFIED')
    if ledger['ever_overwritten'] or any(ledger['forbidden_attempts'].values()) or any(ledger['actual_scientific_execution'].values()):raise ValueError('ZERO_SCIENCE_NOT_VERIFIED')
    if any(c['broken'] for c in ledger['guard_checks']) or any(not x['guard_installed'] for x in ledger['installed_entries']):raise ValueError('GUARDS_NOT_VERIFIED')
    if any(s.get('kind')=='fusion substitute' and not s['closed'] for s in ledger['fake_fuse_scopes']):raise ValueError('FAKE_SCOPE_NOT_CLOSED')
    for name,s in p['source_pins'].items():
        if sha(Path(p['root'])/name)!=s:raise ValueError('POSTRUN_SOURCE_CHANGED')
    return dict(status='PASS',task=TASK,suite=SUITE,policy_sha256=sha(report/'RUN_POLICY.json'),production_launch_marker=w.get('production_launch'),production_marker_note='None approval is correct for this engineering suite; no H1 validator used',test_count=8,zero_science=True)


def main():
    global _REGISTRY
    parser=argparse.ArgumentParser();parser.add_argument('--suite',required=True);parser.add_argument('--launch-ticket',required=True)
    parser.add_argument('--run-policy',required=True);parser.add_argument('--policy-sha256',required=True)
    args=parser.parse_args();raw=Path(args.run_policy).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=args.policy_sha256:raise ValueError('Policy SHA mismatch')
    initial=json.loads(raw)
    if Path(initial['root']).resolve()!=ROOT or Path(initial['entry_script']).resolve()!=Path(__file__).resolve():raise ValueError('Untrusted patch root/entry')
    sys.path.insert(0,str(ROOT))
    canonical='scripts.stfbs_d1b_qm_run_release_patch_test_entry'
    if canonical in sys.modules and sys.modules[canonical] is not sys.modules[__name__]:raise ValueError('Unexpected entry alias')
    sys.modules[canonical]=sys.modules[__name__]
    policy,binding=verify_launch(ROOT,args);save(REPORT/'LAUNCH_BINDING.json',binding)
    from research.non_oracle.stfbs_d1b_qm_run_audit import install_guards
    reg=install_guards();_REGISTRY=reg
    from scripts import stfbs_d1b_qm_run_g1 as g1,stfbs_d1b_qm_run_g1_watchdog as g1wd
    from research.non_oracle import stfbs_d1b_qm_run_release as release,stfbs_d1b_qm_execution as execution
    for owner,name in ((g1,'main'),(g1wd,'main'),(release,'authorize_policy'),(execution.ProbeSchedule,'start'),(execution.ProbeSchedule,'run_to_80'),(execution.DynamicSchedule,'start'),(execution.DynamicSchedule,'advance_one')):
        reg.add(owner,name,'FORMAL_ENTRY')
    reg.integrity('patch guards before tests')
    import unittest,importlib
    stream=io.StringIO();result=None;fatal=None;start=time.time()
    try:
        module=importlib.import_module('tests.test_stfbs_d1b_qm_run_release_patch')
        if Path(module.__file__).resolve()!=ROOT/PATCH_FILES[2]:raise ValueError('Wrong patch test module')
        if sorted(n for n in vars(module.PatchTests) if n.startswith('test_'))!=sorted(NAMES):raise ValueError('Runtime whitelist mismatch')
        class Result(unittest.TextTestResult):
            def __init__(self,*a,**kw):super().__init__(*a,**kw);self.executed=[];self.records=[];self.started={}
            def startTest(self,t):
                if t.id() not in IDS or t.id() in self.executed:raise ValueError('Unexpected/duplicate test')
                reg.current_test=t.id();reg.integrity('before '+t.id());reg.note_double('Patch synthetic receipt/operation port only')
                self.executed.append(t.id());self.started[t.id()]=time.time();super().startTest(t)
            def stopTest(self,t):
                try:reg.integrity('after '+t.id())
                except Exception:self.addError(t,sys.exc_info())
                failed=any(x.id()==t.id() for x,_ in self.errors+self.failures)
                self.records.append(dict(id=t.id(),execution_count=1,status='FAIL' if failed else 'PASS',started=self.started[t.id()],ended=time.time(),evidence_kind=LABEL))
                super().stopTest(t)
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(unittest.TestSuite([module.PatchTests(name) for name in NAMES]))
    except BaseException as error:fatal=dict(error=repr(error),traceback=traceback.format_exc())
    finally:
        try:reg.integrity('patch final exit')
        except Exception as error:
            if fatal is None:fatal=dict(error=repr(error),traceback=traceback.format_exc())
        ledger=reg.ledger();ledger['forbidden_attempts']['FORMAL_ENTRY']=sum(x['category']=='FORMAL_ENTRY' for x in reg.calls)
        save(REPORT/'FORBIDDEN_CALL_LEDGER.json',ledger)
        with (REPORT/'TEST_OUTPUT.log').open('x',encoding='utf-8') as f:f.write(stream.getvalue())
    passed=bool(result is not None and result.wasSuccessful() and result.executed==list(IDS) and not result.skipped and not fatal)
    summary=dict(task=TASK,suite=SUITE,policy_sha256=args.policy_sha256,executed_ids=[] if result is None else result.executed,cases=[] if result is None else result.records,
        all_passed=passed,skips=[] if result is None else [str(x) for x in result.skipped],unexpected_successes=[] if result is None else [x.id() for x in result.unexpectedSuccesses],
        errors=[] if result is None else [dict(id=t.id(),trace=s) for t,s in result.errors],failures=[] if result is None else [dict(id=t.id(),trace=s) for t,s in result.failures],fatal=fatal,started=start,ended=time.time(),evidence_kind=LABEL)
    save(REPORT/'DETERMINISTIC_TEST_RESULTS.json',summary)
    good=passed and not reg.calls and not reg.overwritten
    print(stream.getvalue())
    return 0 if good else 1

if __name__=='__main__':raise SystemExit(main())
