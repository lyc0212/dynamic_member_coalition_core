"""ENG gates and actual Win32 sacrificial processes; never scientific RUNs."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tempfile
from types import SimpleNamespace

import pytest

from research.non_oracle import stfbs_lite_real_d60_source as eng
from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor

ROOT = Path(__file__).resolve().parents[1]
NATIVE = pytest.mark.skipif(os.name != 'nt',reason='Native Windows evidence required')


@pytest.fixture
def tmp_path():
    # Avoid pytest's inaccessible shared numbered-directory cache. This creates
    # only task-owned temporary files and does not change global TMP/PATH.
    with tempfile.TemporaryDirectory(prefix='stfbs-run-gates-') as directory:
        yield Path(directory)


def process_stopped(pid):
    from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API
    api = API()
    handle = api.k.OpenProcess(0x100000,False,pid)
    if not handle:
        return True
    try:
        return api.k.WaitForSingleObject(handle,3000) == 0
    finally:
        api.close(handle)


@NATIVE
def test_native_wall_kills_worker_and_descendant(tmp_path):
    pids = tmp_path/'pids.json'
    code = ("import subprocess,sys,time,json,os; "
            "p=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(30)'],creationflags=0x08000000); "
            f"open({str(pids)!r},'w').write(json.dumps([os.getpid(),p.pid]));time.sleep(30)")
    with WindowsSupervisor(wall_seconds=1.2) as s:
        s.start([sys.executable,'-B','-c',code],cwd=ROOT,log=tmp_path/'worker.log')
        result = s.wait()
    assert result['termination_reason'] == 'WALL_LIMIT'
    assert result['job_cleanup_status'] == 'PASS'
    assert result['accounting']['TotalProcesses'] >= 2
    assert all(process_stopped(pid) for pid in json.loads(pids.read_text()))


@NATIVE
def test_native_job_user_cpu_limit_is_not_total_cpu_budget(tmp_path):
    with WindowsSupervisor(wall_seconds=5.,user_cpu_seconds=.15) as s:
        s.start([sys.executable,'-B','-c','while True: pass'],cwd=ROOT,log=tmp_path/'cpu.log')
        result = s.wait()
    assert result['termination_reason'] == 'WORKER_EXITED', result
    assert result['job_cleanup_status'] == 'PASS'
    assert result['accounting']['TotalUserTime']/1e7 >= .10
    assert result['total_cpu_hard_limit'] == 'RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY'


@NATIVE
def test_native_parent_abnormal_exit_closes_job_and_tree(tmp_path):
    pids = tmp_path/'orphan-pids.json'
    child = ("import subprocess,sys,time,json,os; "
             "p=subprocess.Popen([sys.executable,'-B','-c','import time;time.sleep(30)'],creationflags=0x08000000); "
             f"open({str(pids)!r},'w').write(json.dumps([os.getpid(),p.pid]));time.sleep(30)")
    parent = ("import os,sys,time;sys.path.insert(0,"+repr(str(ROOT))+");"
              "from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor;"
              "s=WindowsSupervisor(wall_seconds=20);"
              f"s.start([{sys.executable!r},'-B','-c',{child!r}],cwd={str(ROOT)!r},log={str(tmp_path/'orphan.log')!r});"
              f"p={str(pids)!r};\n"
              "for _ in range(200):\n"
              " if os.path.exists(p): break\n"
              " time.sleep(.01)\n"
              "os._exit(17)")
    parent_process = subprocess.Popen([sys.executable,'-B','-c',parent],cwd=ROOT,creationflags=0x08000000)
    try:
        assert parent_process.wait(timeout=8) == 17
        assert pids.exists()
        assert all(process_stopped(pid) for pid in json.loads(pids.read_text()))
    finally:
        if parent_process.poll() is None:
            parent_process.kill(); parent_process.wait()


def test_durable_started_before_fake_compute_and_failure_not_rolled_back(tmp_path):
    path = tmp_path/'calls.jsonl'
    journal = eng.DurableJournal(path,attempt_id='eng',max_bytes=100000)
    ledger = eng.DurableResourceLedger(dict(zip(eng.CATEGORIES,(2,2,2))),journal)
    def fake():
        rows = eng.read_durable_journal(path,attempt_id='eng')
        assert rows[-1]['event']['status'] == 'STARTED'
        raise ValueError('fake computation failed')
    with pytest.raises(ValueError): ledger.invoke('ACTUAL_POLICY_WLS',fake)
    journal.close()
    rows = eng.read_durable_journal(path,attempt_id='eng')
    assert [r['event']['status'] for r in rows] == ['STARTED','FAILED']
    assert ledger.counts['ACTUAL_POLICY_WLS'] == 1


@NATIVE
def test_native_termination_retains_started_wls_evidence(tmp_path):
    path = tmp_path/'killed.jsonl'
    code = (f"import sys,time;sys.path.insert(0,{str(ROOT)!r});"
            "from research.non_oracle.stfbs_lite_real_d60_source import DurableJournal,DurableResourceLedger,CATEGORIES;"
            f"j=DurableJournal({str(path)!r},attempt_id='killed',max_bytes=100000);"
            "l=DurableResourceLedger(dict(zip(CATEGORIES,(2,2,2))),j);"
            "l.invoke('ACTUAL_POLICY_WLS',lambda:time.sleep(30))")
    with WindowsSupervisor(wall_seconds=1.2) as s:
        s.start([sys.executable,'-B','-c',code],cwd=ROOT,log=tmp_path/'killed.log')
        result = s.wait()
    assert result['job_cleanup_status'] == 'PASS'
    rows = eng.read_durable_journal(path,attempt_id='killed')
    audit = eng.inspect_attempt_journal(rows)
    assert audit['started_calls'] == 1 and len(audit['unfinished_calls']) == 1
    receipt=eng.persist_supervisor_receipt(path,tmp_path/'receipt.jsonl',attempt_id='killed',result=result,max_bytes=10000)
    assert receipt['journal_status']=='VERIFIED' and receipt['retry_authorized'] is False
    assert len(receipt['unfinished_calls'])==1


def test_durable_write_failure_prevents_fake_compute_and_exclusive_attempt(tmp_path):
    path = tmp_path/'exclusive.jsonl'
    j = eng.DurableJournal(path,attempt_id='once',max_bytes=1)
    with pytest.raises(FileExistsError): eng.DurableJournal(path,attempt_id='once',max_bytes=100)
    l = eng.DurableResourceLedger(dict(zip(eng.CATEGORIES,(1,1,1))),j)
    calls = []
    with pytest.raises(eng.AdmissionRejected): l.invoke('ACTUAL_POLICY_WLS',lambda:calls.append(1))
    assert calls == []
    j.close()


def test_corrupt_and_replaced_log_never_repaired(tmp_path):
    path = tmp_path/'corrupt.jsonl'
    j = eng.DurableJournal(path,attempt_id='corrupt',max_bytes=10000)
    j.append(dict(kind='ENG'))
    j.close()
    raw = path.read_bytes()
    path.write_bytes(raw[:-1])
    with pytest.raises(eng.AdmissionRejected): eng.read_durable_journal(path,attempt_id='corrupt')
    assert path.read_bytes() == raw[:-1]


class TransactionPort:
    def __init__(self, *, fail_at=None): self.tick,self.calls,self.fail_at=0,[],fail_at
    def prepare_decision(self): self.calls.append(('freeze',self.tick));return dict(tick=self.tick)
    def observe_public(self): return dict(checkpoint_id=f'cp{self.tick}')
    def step(self,actions,checkpoint_id,expected_start_tick,request_id,*,on_commit):
        assert checkpoint_id == f'cp{self.tick}' and expected_start_tick == self.tick
        self.calls.append(('step',self.tick,request_id))
        on_commit(dict(tick=self.tick+1))
        if self.tick == self.fail_at: raise RuntimeError('sacrificial fake STEP interrupted')
        lo=self.tick;self.tick+=20
        return dict(status='COMMITTED',start_tick=lo,end_tick=self.tick,checkpoint_after=dict(tick=self.tick,checkpoint_id=f'cp{self.tick}'))


@pytest.mark.parametrize('failure',[None,40])
def test_four_argument_dispatch_and_durable_transaction_boundary(tmp_path,failure):
    env=TransactionPort(fail_at=failure)
    j=eng.DurableJournal(tmp_path/'steps.jsonl',attempt_id='steps',max_bytes=100000)
    capture_calls=[]
    def capture(env,view): capture_calls.append(view['tick']);return dict(status='LIVE_CUT_STRUCTURAL_CAPTURE_PASS')
    def candidate(cut): return dict(execution_admission='MODEL_EXECUTION_ADMISSION_DENIED')
    try:
        if failure is None:
            eng._dispatch_d60(env,decide=lambda v,m:dict(actions=[]),capture=capture,map_candidate=candidate,journal=j)
        else:
            with pytest.raises(RuntimeError): eng._dispatch_d60(env,decide=lambda v,m:dict(actions=[]),capture=capture,map_candidate=candidate,journal=j)
    finally: j.close()
    rows=eng.read_durable_journal(tmp_path/'steps.jsonl',attempt_id='steps')
    audit=eng.inspect_attempt_journal(rows)
    if failure is None:
        assert audit['last_complete_step']==60 and capture_calls==[60]
        assert [c[1] for c in env.calls if c[0]=='step']==[0,20,40]
    else:
        assert audit['last_complete_step']==40 and audit['incomplete_transaction']==40
        assert capture_calls==[]


def test_production_admission_denied_before_environment_and_model(monkeypatch):
    # No production imports are needed to reject missing/self-issued permission.
    for permit in (None,True,'RUN-G1',dict(approved=True)):
        with pytest.raises(eng.AdmissionRejected): eng.production_dispatcher(permit=permit)
    assert eng.check_run_admission()['status']=='RUN_ADMISSION_BLOCKED'


def test_permit_verifier_is_not_independent_provider():
    record={k:'test-only' for k in eng.PERMIT_FIELDS}
    record.update(task_id='STFBS_LITE_REAL_D60',policy='R',target_cut_tick=60,maximum_completed_steps=3,
        stop_rule='POST_FREEZE_PRE_ASSIGNMENT_D60',policy_wls_limit=1,observation_wls_limit=1,solver_start_limit=18,
        storage_limit=100000,cpu_limit=dict(semantics='JOB_USER_SECONDS',seconds=1),wall_limit=2)
    expected=eng.content_digest(record)
    assert eng.verify_permit_record(record,independent_expected_digest=expected,expected_identity={'run_id':'test-only'})['provider']=='RUN_PERMIT_PROVIDER_NOT_READY'
    with pytest.raises(eng.AdmissionRejected): eng.verify_permit_record(dict(record,run_id='changed'),independent_expected_digest=expected,expected_identity={})
    with pytest.raises(eng.AdmissionRejected): eng.verify_permit_record({},independent_expected_digest=expected,expected_identity={})


def test_explicit_source_coverage_and_postcheck_isolation_blocked():
    inputs=['runs/a2_switch_episode_001/WORLD_INPUT.json','runs/a2_switch_episode_001/PUBLIC_INPUT.json']
    import numpy,scipy
    runtime=[sys.executable,numpy.__file__,scipy.__file__]
    names=set(eng.REQUIRED_SOURCE_PATHS)|set(inputs)|set(runtime)
    manifest={n:hashlib.sha256((Path(n) if Path(n).is_absolute() else ROOT/n).read_bytes()).hexdigest() for n in names}
    result=eng.verify_source_manifest(manifest,repository=ROOT,input_paths=inputs,runtime_paths=runtime)
    assert result['source_preflight']=='SOURCE_PREFLIGHT_NOT_READY'
    with pytest.raises(eng.AdmissionRejected): eng.verify_source_manifest({},repository=ROOT,input_paths=inputs,runtime_paths=runtime)
    manifest[inputs[0]]='0'*64
    with pytest.raises(eng.AdmissionRejected): eng.verify_source_manifest(manifest,repository=ROOT,input_paths=inputs,runtime_paths=runtime)


def test_policy_observation_solver_aliases_with_durable_accounting(tmp_path):
    solver=SimpleNamespace(least_squares=lambda:1)
    policy=SimpleNamespace(estimate=lambda:solver.least_squares())
    bridge=SimpleNamespace(_estimate=lambda:solver.least_squares())
    processor=SimpleNamespace(estimator_fn=bridge._estimate)
    j=eng.DurableJournal(tmp_path/'aliases.jsonl',attempt_id='aliases',max_bytes=100000)
    ledger=eng.DurableResourceLedger(dict(zip(eng.CATEGORIES,(1,1,2))),j)
    with eng.guard_wls_bindings(ledger,policy=policy,bridge=bridge,estimator=solver,processors=[processor]):
        policy.estimate();processor.estimator_fn()
    j.close()
    assert ledger.counts==dict(zip(eng.CATEGORIES,(1,1,2)))
    rows=eng.read_durable_journal(tmp_path/'aliases.jsonl',attempt_id='aliases')
    assert len([r for r in rows if r['event']['status']=='STARTED'])==4


def test_archived_budget_counts_read_only():
    # Statistics only, never policy.evaluate or a physical episode.
    root=ROOT/'runs/a2_switch_episode_001'
    observation=0
    policy_endpoint=0
    for tick in (0,20,40):
        record=json.loads((root/f'R_D{tick}.json').read_text())
        observation+=sum(f['result']['estimator_called'] for f in record['step']['fusion_records'])
        # Store only the known archive observation count here. A policy quota
        # cannot be inferred from this number or silently approved.
    assert observation==61


@NATIVE
def test_native_explicit_breakaway_attempt_is_denied(tmp_path):
    marker=tmp_path/'breakaway.txt'
    code=("import subprocess,sys;\ntry:\n"
          " p=subprocess.Popen([sys.executable,'-B','-c','pass'],creationflags=0x01000000|0x08000000)\n"
          " p.wait()\n"
          f" open({str(marker)!r},'w').write('ESCAPED')\n"
          "except PermissionError:\n"
          f" open({str(marker)!r},'w').write('DENIED')\n")
    with WindowsSupervisor(wall_seconds=3) as s:
        s.start([sys.executable,'-B','-c',code],cwd=ROOT,log=tmp_path/'breakaway.log')
        result=s.wait()
    assert result['job_cleanup_status']=='PASS'
    assert marker.read_text()=='DENIED'


def test_completion_marker_without_durable_result_is_rejected(tmp_path):
    j=eng.DurableJournal(tmp_path/'bad-marker.jsonl',attempt_id='bad-marker',max_bytes=10000)
    j.append(dict(kind='STEP_REQUEST',tick=0))
    j.append(dict(kind='STEP_COMPLETE',start_tick=0,end_tick=20,checkpoint_id='invented'))
    j.close()
    rows=eng.read_durable_journal(tmp_path/'bad-marker.jsonl',attempt_id='bad-marker')
    with pytest.raises(eng.AdmissionRejected):eng.inspect_attempt_journal(rows)


def test_existing_log_overwrite_detected_before_next_write(tmp_path):
    path=tmp_path/'overwrite.jsonl'
    j=eng.DurableJournal(path,attempt_id='overwrite',max_bytes=10000)
    j.append(dict(kind='ENG',value=1))
    raw=path.read_bytes()
    with path.open('r+b') as other:
        other.write(raw.replace(b'"value":1',b'"value":2'));other.flush();os.fsync(other.fileno())
    try:
        with pytest.raises(eng.AdmissionRejected):j.append(dict(kind='ENG',value=3))
    finally:j.close()


def test_missing_worker_log_cannot_invent_legal_checkpoint(tmp_path):
    result=dict(termination_reason='ABNORMAL_EXIT',worker_exit_status=1,job_cleanup_status='PASS')
    receipt=eng.persist_supervisor_receipt(tmp_path/'missing.jsonl',tmp_path/'receipt.jsonl',
        attempt_id='missing',result=result,max_bytes=10000)
    assert receipt['journal_status']=='FAILED'
    assert receipt['last_durable_checkpoint'] is None and receipt['retry_authorized'] is False
