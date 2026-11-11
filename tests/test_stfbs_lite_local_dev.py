"""LOCAL_DEV contracts, CODE ONLY. No tests executed during implementation.

All execution examples below use artificial objects. Native engineering worker
execution and any ACTUAL input/budget/attempt need separate user authorization.
"""
import builtins
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

from research.non_oracle import stfbs_lite_local_dev as local
from research.non_oracle import stfbs_lite_real_d60_source as production

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def approval(tmp_path,monkeypatch):
    def git(argv,**kwargs):
        return '' if argv[1]=='status' else ('main\n' if argv[1]=='branch' else 'ARTIFICIAL_HEAD\n')
    monkeypatch.setattr(local.subprocess,'check_output',git)
    dependency=tmp_path/'artificial_dependency.txt'
    dependency.write_text('ARTIFICIAL_ONLY')
    record=dict(schema='STFBS_LOCAL_DEV_APPROVAL_V1',mode=local.ENGINEERING,execution_authorized=True,
        approval_reference='ARTIFICIAL_TEST_NOT_ACTUAL_AUTHORIZATION',approved_by='TEST_ONLY',
        git_head='ARTIFICIAL_HEAD',source_sha256={p:local.digest_file(ROOT/p) for p in local.LOCAL_PATHS|production.REQUIRED_SOURCE_PATHS},
        inputs={},world_id='ARTIFICIAL_WORLD',physical_environment_id='ARTIFICIAL_ENV',run_id='artificial-run',
        attempt_id='artificial-attempt',runtime={'python':sys.executable,'version':sys.version,
        'python_sha256':local.digest_file(sys.executable),'dependency_sha256':{str(dependency):local.digest_file(dependency)}},
        budget={'total_cpu_seconds':1.,'wall_seconds':2.,'wls':dict.fromkeys(production.CATEGORIES,0),'storage_bytes':2_000_000},
        stop_rule=local.STOP,output_directory=str(tmp_path/'output'),attempt_directory=str(tmp_path/'attempts'),
        overshoot_disposition='FAIL_ATTEMPT')
    path=tmp_path/'authorization.json'
    path.write_text(json.dumps(record))
    return record,path,local.digest_file(path)


def add_start(journal,record,sha):
    journal.append({'kind':'LOCAL_WORKER_START','mode':record['mode'],'attempt_id':record['attempt_id'],
                    'approval_digest':sha,'worker_pid':222,'evidence_kind':local.ARTIFICIAL})


def finish_artificial(journal,record,sha):
    add_start(journal,record,sha)
    candidate,wls=local.execute_worker_mode(record,journal)
    journal.append({'kind':'LOCAL_WORKER_COMPLETE','mode':record['mode'],'tick':60,
        'stop_rule':local.STOP,'wls':wls,'candidate_status':candidate['candidate_status'],
        'model_admission':'MODEL_EXECUTION_ADMISSION_DENIED'})


def resource_result(record):
    return dict(execution_entry='RUN_MONITORED',attempt_identity=record['attempt_id'],
        job_cleanup_status='PASS',process_tree_status='PROCESS_TREE_EXIT_CONFIRMED',worker_exit_status=0,
        stop_reason='NATURAL_EXIT',accounting_status='FINAL_VALID',evidence_completeness_status='COMPLETE_IN_MEMORY',errors=[],
        accounting={'TotalUserTime':10,'TotalKernelTime':5,'ActiveProcesses':0},final_cpu_ticks=15,total_cpu_ticks=15,
        cpu_limit_ticks=10_000_000,wall_limit_seconds=2.,cpu_overshoot_ticks=0,wall_elapsed_at_tree_exit=.5,
        cpu_semantics='TOTAL_CPU_SECONDS',cpu_scope='WHOLE_JOB',supervisor_cpu_ticks=1,
        supervisor_cpu_scope='CURRENT_PROCESS_EXCLUDED_FROM_JOB')


def test_explicit_local_approval_required(approval):
    record,_,_=approval
    record['execution_authorized']=False
    with pytest.raises(production.AdmissionRejected,match='APPROVAL_REQUIRED'):
        local.validate_approval(record,ROOT)


def test_approval_sha_mismatch_rejected(approval):
    _,path,_=approval
    with pytest.raises(production.AdmissionRejected,match='BYTES_CONFLICT'):
        local.load_approval(path,'0'*64)


def test_engineering_rejects_actual_inputs_or_wls(approval):
    record,_,_=approval
    record['budget']['wls']['ACTUAL_POLICY_WLS']=1
    with pytest.raises(production.AdmissionRejected,match='ENGINEERING_MUST'):
        local.validate_approval(record,ROOT)


def test_actual_requires_independent_mode_specific_approval_inputs_and_budget(approval):
    record,_,_=approval
    record['mode']=local.ACTUAL
    with pytest.raises(production.AdmissionRejected,match='ACTUAL_INPUTS_AND_BUDGET'):
        local.validate_approval(record,ROOT)


def test_missing_time_budget_has_no_default(approval):
    record,_,_=approval
    del record['budget']['total_cpu_seconds']
    with pytest.raises(production.AdmissionRejected,match='BUDGET_MISSING'):
        local.validate_approval(record,ROOT)


def test_engineering_dispatch_never_imports_science(approval,tmp_path,monkeypatch):
    record,_,sha=approval
    original=builtins.__import__
    def guarded(name,*args,**kwargs):
        if name in {'scripts.run_a1','research.non_oracle.environment','research.non_oracle.policy',
                    'research.cooperative_sensing','research.information_service_bridge'}:
            pytest.fail('Engineering must not import scientific execution')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',guarded)
    output=Path(record['output_directory']);output.mkdir()
    journal=local.LocalJournal(output,record['attempt_id'],record['budget']['storage_bytes'])
    try: finish_artificial(journal,record,sha)
    finally: journal.close()
    rows=production.read_durable_journal(journal.path,attempt_id=record['attempt_id'])
    audited=local.audit_local_result(record,resource_result(record),rows,sha)
    assert audited['boundary']['last_complete_step']==60
    assert audited['wls_counts']==dict.fromkeys(production.CATEGORIES,0)
    assert audited['candidate']['evidence_kind']==local.ARTIFICIAL


def test_actual_helper_requires_job_context_before_scientific_import(approval):
    record,_,_=approval
    record['mode']=local.ACTUAL
    with pytest.raises(production.AdmissionRejected,match='WORKER_CONTEXT_REQUIRED'):
        local.execute_worker_mode(record,None)


def test_dynamic_processor_keeps_guarded_observation_reference():
    wrapped=lambda payload:payload
    bridge=SimpleNamespace(_estimate=wrapped)
    sensing=SimpleNamespace(streams={})
    local.verify_sensing_streams(sensing,bridge)
    sensing.streams['new']=SimpleNamespace(estimator_fn=wrapped)
    local.verify_sensing_streams(sensing,bridge)
    sensing.streams['new'].estimator_fn=lambda payload:payload
    with pytest.raises(production.AdmissionRejected,match='UNGUARDED_PROCESSOR'):
        local.verify_sensing_streams(sensing,bridge)


def test_started_persisted_before_artificial_expensive_call(tmp_path):
    journal=production.DurableJournal(tmp_path/'journal',attempt_id='manual-only',max_bytes=10000)
    ledger=production.DurableResourceLedger(dict.fromkeys(production.CATEGORIES,1),journal)
    called=[]
    def artificial():
        rows=production.read_durable_journal(journal.path,attempt_id='manual-only')
        assert rows[-1]['event']['status']=='STARTED'
        called.append(True)
        return 7
    try: assert ledger.invoke('ACTUAL_POLICY_WLS',artificial)==7
    finally: journal.close()
    assert called==[True]


def test_storage_budget_rejects_before_write(tmp_path):
    with pytest.raises(production.AdmissionRejected,match='STORAGE_EXHAUSTED'):
        local.write_new(tmp_path,'too-large.json',{'data':'x'*100},1)
    assert not (tmp_path/'too-large.json').exists()


@pytest.mark.parametrize('field,value',[('job_cleanup_status','FAIL'),('accounting',None),
    ('evidence_completeness_status','INCOMPLETE'),('cpu_overshoot_ticks',1),('worker_exit_status',1)])
def test_incomplete_resource_never_success(approval,field,value):
    record,_,sha=approval
    result=resource_result(record);result[field]=value
    with pytest.raises(production.AdmissionRejected):
        local.audit_local_result(record,result,[],sha)


def test_partial_step_never_complete(approval,tmp_path):
    record,_,sha=approval
    output=Path(record['output_directory']);output.mkdir()
    journal=local.LocalJournal(output,record['attempt_id'],record['budget']['storage_bytes'])
    try:
        add_start(journal,record,sha)
        journal.append({'kind':'STEP_REQUEST','tick':0})
        journal.append({'kind':'STEP_FRAME','frame':{'tick':1}})
    finally: journal.close()
    rows=production.read_durable_journal(journal.path,attempt_id=record['attempt_id'])
    with pytest.raises(production.AdmissionRejected,match='D60_INCOMPLETE'):
        local.audit_local_result(record,resource_result(record),rows,sha)


def test_parent_consumes_then_uses_monitored_worker_and_persists_separate_success(approval,monkeypatch):
    record,path,sha=approval
    calls=[]
    class FakeSupervisor:
        def __init__(self,**kwargs):
            self.closed=False;self.result=None
            self.api=SimpleNamespace(create=lambda *a:SimpleNamespace(hProcess=2,hThread=3),
                member=lambda *a:True,k=SimpleNamespace(GetCurrentProcess=lambda:1))
        def run_monitored(self,argv,*,cwd,log):
            assert list(Path(record['attempt_directory']).glob('*.consumed'))
            calls.append('run_monitored')
            self.api.create(9,argv,cwd,{},log)
            assert (Path(record['output_directory'])/'handoff.json').exists()
            journal=local.LocalJournal(record['output_directory'],record['attempt_id'],record['budget']['storage_bytes'])
            try: finish_artificial(journal,record,sha)
            finally: journal.close()
            self.result=resource_result(record)
            return self.result
        def close(self):self.closed=True
    monkeypatch.setattr(local,'WindowsSupervisor',FakeSupervisor)
    monkeypatch.setattr(local,'process_identity',lambda api,h:{'pid':111 if h==1 else 222,'creation_ticks':h})
    result=local.run_parent(path,sha,ROOT)
    assert calls==['run_monitored']
    assert result['evidence_kind']==local.ARTIFICIAL
    assert result['source_authentication']=='NOT_VERIFIED'
    assert (Path(record['output_directory'])/'success.json').is_file()
    assert not (Path(record['output_directory'])/'failure.json').exists()
    with pytest.raises(production.AdmissionRejected,match='OUTPUT_ALREADY_EXISTS'):
        local.run_parent(path,sha,ROOT)
    assert calls==['run_monitored']


def test_failed_worker_launch_keeps_attempt_consumed(approval,monkeypatch):
    record,path,sha=approval
    calls=[]
    class BrokenSupervisor:
        result=None
        def __init__(self,**kwargs):raise OSError('artificial create failure')
    monkeypatch.setattr(local,'WindowsSupervisor',BrokenSupervisor)
    result=local.run_parent(path,sha,ROOT)
    assert result['status']=='LOCAL_DEV_FAILED_OR_INCOMPLETE'
    assert list(Path(record['attempt_directory']).glob('*.consumed'))
    assert (Path(record['output_directory'])/'failure.json').exists()
    assert not (Path(record['output_directory'])/'success.json').exists()


def test_production_gate_unchanged():
    assert production.check_run_admission()['status']=='RUN_ADMISSION_BLOCKED'
    with pytest.raises(production.AdmissionRejected):production.production_dispatcher()


@pytest.mark.parametrize('mode',[local.ENGINEERING,local.ACTUAL])
def test_worker_job_check_precedes_mode_execution(approval,tmp_path,monkeypatch,mode):
    record,_,_=approval
    record['mode']=mode
    path=tmp_path/'worker-approval.json';path.write_text(json.dumps(record))
    handoff=tmp_path/'handoff.json';handoff.write_text('{}')
    monkeypatch.setattr(local,'validate_approval',lambda *a,**k: record)
    def no_job(*args):raise production.AdmissionRejected('ARTIFICIAL_NO_JOB')
    monkeypatch.setattr(local,'verify_local_job_handoff',no_job)
    monkeypatch.setattr(local,'execute_worker_mode',lambda *a,**k: pytest.fail('must not execute mode'))
    with pytest.raises(production.AdmissionRejected,match='NO_JOB'):
        local.worker_main(path,local.digest_file(path),handoff,ROOT)
    assert not Path(record['output_directory']).exists()


def test_new_processor_uses_guarded_observation_and_nested_solver(tmp_path):
    journal=production.DurableJournal(tmp_path/'resource.jsonl',attempt_id='ARTIFICIAL',max_bytes=20000)
    ledger=production.DurableResourceLedger(dict.fromkeys(production.CATEGORIES,2),journal)
    estimator=SimpleNamespace(least_squares=lambda payload: payload)
    policy=SimpleNamespace(estimate=lambda payload: estimator.least_squares(payload))
    bridge=SimpleNamespace(_estimate=lambda payload: estimator.least_squares(payload))
    try:
        with production.guard_wls_bindings(ledger,policy=policy,bridge=bridge,estimator=estimator):
            processor=SimpleNamespace(estimator_fn=bridge._estimate)
            local.verify_sensing_streams(SimpleNamespace(streams={'new':processor}),bridge)
            assert processor.estimator_fn('ARTIFICIAL')=='ARTIFICIAL'
        assert ledger.counts=={'ACTUAL_POLICY_WLS':0,'ACTUAL_OBSERVATION_WLS':1,'ACTUAL_SOLVER_START':1}
    finally:journal.close()


def test_sha256_uppercase_is_equivalent(approval):
    _,path,sha=approval
    assert local.load_approval(path,sha.upper())[0]['mode']==local.ENGINEERING
