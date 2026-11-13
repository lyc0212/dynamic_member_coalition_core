"""Only V1-V3, with real wrappers and deterministic science stubs."""
import pathlib,sys,json,runpy,traceback
ROOT=pathlib.Path(__file__).resolve().parent
results={}
def save():
    (ROOT/'CORRECTNESS_RESULTS.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
def need(value,code):
    if not value:raise RuntimeError(code)
def reject(fn,code=None):
    try:fn()
    except BaseException as exc:
        if code:need(code in str(exc),'WRONG_ERROR/'+str(exc))
        return dict(type=type(exc).__name__,message=str(exc))
    raise RuntimeError('EXPECTED_REJECTION_ABSENT')
try:
    v1=runpy.run_path(str(ROOT/'validation_v1.py'))
    results['V1']=json.loads((ROOT/'PRECHECK_RESULT.json').read_bytes())
    need(results['V1']['status']=='PASS','V1_FAILED')
    observations=results['V1']['checks']['S3']['observations']
    need([o['phase'] for o in observations]==['PRE_SEAL','POST_SEAL'],'S3_HOOK_NOT_EXECUTED')
    Q,J=v1['Q'],v1['J']
    def context(name):
        d=ROOT/'validation'/name;d.mkdir(parents=True)
        c=Q.initialized_budget(d/'journal.jsonl','FAST_PATH_VALIDATION','SYNTH_'+name,lambda b,t:{'stub':True})
        return d,c,c.__enter__()
    def failed_close(c):
        need(c.__exit__(RuntimeError,RuntimeError('EXPECTED_SYNTHETIC_FAILURE'),None) is False,
             'SYNTHETIC_FAILURE_SUPPRESSED')
    v2={}
    d=ROOT/'validation/commit_once';d.mkdir(parents=True)
    j=J.LocalJournal(d/'journal.jsonl','SYNTHETIC','ONCE',65536)
    for call_type in ('POLICY_WLS','OBSERVATION_WLS','SOLVER','R','ASSIGNMENT'):
        event=dict(event_kind='RESOURCE_CALL',call_type=call_type,status='STARTED')
        j.append(event);need(j.committed_counts()[call_type]==1,'STARTED_COUNT')
        j.append(dict(event,status='RETURNED'));need(j.committed_counts()[call_type]==1,'RETURNED_DOUBLE_COUNT')
    need(all(v==1 for v in j.committed_counts().values()),'FIVE_COUNTS')
    j.seal();j.close();v2['committed_once']=dict(counts=j.committed_counts(),events=j.sequence)
    d=ROOT/'validation/prewrite';d.mkdir()
    j=J.LocalJournal(d/'journal.jsonl','SYNTHETIC','PREWRITE',1)
    snapshot=(j.size,j.sequence,j.previous,j.hash.digest(),j.committed_counts(),j.path.read_bytes(),j.invalid)
    error=reject(lambda:j.append(dict(event_kind='RESOURCE_CALL',call_type='SOLVER',status='STARTED')),'JOURNAL_STORAGE_LIMIT')
    need(snapshot==(j.size,j.sequence,j.previous,j.hash.digest(),j.committed_counts(),j.path.read_bytes(),j.invalid),'PREWRITE_MUTATED')
    j.records();j.seal();j.close();v2['prewrite']=dict(error=error,invalid=j.invalid,sealed=j.sealed)
    for mode in ('write_failure','post_persist_update_failure'):
        d,c,b=context(mode);executed=[];b.est=lambda x:executed.append(True)
        if mode=='write_failure':
            original=b.local.file
            class ShortWriter:
                def __getattr__(self,k):return getattr(original,k)
                def write(self,data):return 0
            b.local.file=ShortWriter()
        else:
            class BrokenCounts(dict):
                def __setitem__(self,k,v):raise RuntimeError('INJECTED_COMMIT_UPDATE')
            b.local._committed_counts=BrokenCounts(b.local._committed_counts)
        error=reject(lambda:b.estimator('MODEL_OBSERVATION_WLS')(None), 'JOURNAL_SHORT_WRITE' if mode=='write_failure' else 'INJECTED_COMMIT_UPDATE')
        need(not executed and b.local.invalid and b.ledger.counts['ACTUAL_OBSERVATION_WLS']==1,'PERSISTENCE_NOT_FAIL_STOP')
        need(b.local._committed_counts['OBSERVATION_WLS']==0,'FALSE_COMMIT_COUNT')
        raw=b.local.path.read_bytes()
        need(bool(raw)==(mode=='post_persist_update_failure'),'PERSISTENCE_LOCATION')
        # A subsequent resource entry must not reach its expensive stub.
        reject(lambda:b.estimator('MODEL_OBSERVATION_WLS')(None))
        failed_close(c)
        need(b.state==b.nested.state=='FINALIZED_FAILED','BAD_FINAL_STATE')
        v2[mode]=dict(error=error,stub_calls=len(executed),persisted_bytes=len(raw),runtime_count=1,incremental_count=0,finalization=b.finalization_report)
    d,c,b=context('count_drift');b.local._committed_counts['SOLVER']=1
    error=reject(lambda:c.__exit__(None,None,None),'BUDGET_FINALIZED_FAILED')
    need(b.state=='FINALIZED_FAILED' and not b.local.invalid and b.local.sealed,'DRIFT_NOT_REJECTED')
    v2['count_drift']=dict(error=error,finalization=b.finalization_report)
    results['V2']=dict(status='PASS',checks=v2);save()
    results['V3']=dict(status='USER_SCOPE_REMOVED',executed=False)
    results['status']='PASS';results['real_science_calls']=0;save()
except BaseException as exc:
    results['status']='FAIL';results['error']=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());save();raise
