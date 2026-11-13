from common import *
import argparse
import ctypes as C
from datetime import datetime,timezone
from research.non_oracle.stfbs_lite_local_dev import process_identity
from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import API,ExtendedLimit
AUTHORIZATION_SHA=sha(ROOT/'authorization.json')
def utc():return datetime.now(timezone.utc).isoformat()
def preflight():
 from model_driver import verify_frozen
 a=verify_frozen()
 require(not (ROOT/'attempt.consumed').exists() and not (ROOT/'parent_start_attempt.lock').exists(),'ATTEMPT_ALREADY_USED')
 require(os.name=='nt' and C.sizeof(C.c_void_p)==8,'WINDOWS_X64_REQUIRED')
 return a,API()
def main(preflight_only=False):
    record,api=preflight()
    if preflight_only:
        save('preflight.json',dict(status='PRECHECK_COMPLETE_NO_PARENT_STARTED',utc=utc(),
            head=record['git_head'],approval_sha256=AUTHORIZATION_SHA,python=record['runtime'],
            source_file_count=len(record['source_sha256']),mode=record['mode'],budget=record['budget'],
            outer_wall_seconds=2460,output_absent=True,attempt_absent=True,
            nested_job_compatibility='REQUIRES_SINGLE_NATIVE_EXECUTION',source_authentication='NOT_VERIFIED'))
        return 0
    freeze=json.loads((ROOT/'execution_freeze.json').read_text(encoding='utf-8-sig'))
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=freeze['controller_sha256']:
        raise RuntimeError('CONTROLLER_BYTES_DRIFT')
    job=None;pi=None;retained={};identities=[];waits=[];errors=[];actions=[]
    state='NOT_CREATED';final=None;parent_exit=None;timed_out=False;attempts=0
    began=utc();started=time.monotonic()
    def close_job(fallback=False):
        nonlocal state,final
        if state!='OPEN':return
        state='CLOSE_ATTEMPTED'
        if fallback:final=None
        try:
            api.close(job);state='CLOSED'
            actions.append(dict(kind='JOB_CLOSE',fallback=fallback,result='SUCCEEDED',elapsed=time.monotonic()-started))
        except BaseException as exc:
            state='CLOSE_FAILED_OR_UNCERTAIN'
            errors.append(dict(stage='JOB_CLOSE',fallback=fallback,type=type(exc).__name__,message=str(exc)))
    def terminate(stage):
        if state!='OPEN':return
        actions.append(dict(kind='TERMINATE_JOB',stage=stage,elapsed=time.monotonic()-started))
        try:
            api.terminate(job)
            actions.append(dict(kind='TERMINATE_JOB_RETURNED',stage=stage,result='SUCCEEDED'))
        except BaseException as exc:
            errors.append(dict(stage=stage,type=type(exc).__name__,message=str(exc)))
            close_job(fallback=True)  # Immediate, before query/wait/persistence.
    try:
        job=api.job(None);state='OPEN'
        limits=ExtendedLimit()
        api.check(api.k.QueryInformationJobObject(job,9,C.byref(limits),C.sizeof(limits),None),'QUERY_OUTER_LIMITS')
        flags=int(limits.BasicLimitInformation.LimitFlags)
        if not flags & 0x2000 or flags & 0x1800:raise RuntimeError('UNSAFE_OUTER_JOB_FLAGS')
        save('outer_config.json',dict(job_handle=int(job),limit_flags=flags,
            current_controller_in_any_job=api.member(api.k.GetCurrentProcess(),None),
            atomic_creation='PROC_THREAD_ATTRIBUTE_JOB_LIST',suspended=True,
            inherited_handles='ONLY_FROZEN_STD_HANDLE_LIST_NO_JOB_HANDLE',outer_wall_seconds=2460))
        with (ROOT/'parent_start_attempt.lock').open('x') as f:
            f.write(record['attempt_id']);f.flush();os.fsync(f.fileno())
        attempts=1
        pi=api.create(job,[sys.executable,'-I','-S','-B',str(ROOT/'model_driver.py'),'--parent'],
            REPO,dict(os.environ,PYTHONDONTWRITEBYTECODE='1'),ROOT/'parent_console.log')
        if not api.member(pi.hProcess,job):raise RuntimeError('PARENT_NOT_CONTAINED_BEFORE_RESUME')
        identities.append(dict(role='LOCAL_DEV_PARENT_SUSPENDED',**process_identity(api,pi.hProcess),member=True))
        api.resume(pi.hThread)
        while True:
            if time.monotonic()-started>=2460:
                timed_out=True;terminate('OUTER_WALL_LIMIT');break
            final=api.accounting(job)
            if final['ActiveProcesses']==0:break
            for pid in api.pids(job):
                if pid in retained:continue
                h=api.k.OpenProcess(0x100000|0x1000|1,False,pid)
                api.check(h,'OpenProcess/RETAIN_OUTER_MEMBER')
                try:
                    identity=process_identity(api,h)
                    if identity['pid']!=pid or not api.member(h,job):raise RuntimeError('OUTER_MEMBER_IDENTITY_CONFLICT')
                except BaseException:
                    api.close(h);raise
                retained[pid]=h
                identities.append(dict(role='RETAINED_OUTER_MEMBER',**identity,member=True))
            time.sleep(.01)
    except BaseException as exc:
        errors.append(dict(stage='OUTER_CONTROL',type=type(exc).__name__,message=str(exc)))
        terminate('OUTER_EXCEPTION')
    finally:
        if state=='OPEN':
            deadline=time.monotonic()+3
            try:
                while True:
                    final=api.accounting(job)
                    if final['ActiveProcesses']==0:break
                    if time.monotonic()>=deadline:
                        terminate('CLEANUP_DEADLINE');break
                    time.sleep(.01)
            except BaseException as exc:
                errors.append(dict(stage='FINAL_ACCOUNTING',type=type(exc).__name__,message=str(exc)))
                final=None;terminate('FINAL_ACCOUNTING_FAILURE')
        for pid,h in retained.items():
            status=int(api.k.WaitForSingleObject(h,0))
            remedial=status!=0
            if remedial:
                actions.append(dict(kind='VERIFIED_HANDLE_REMEDIAL_TERMINATE',pid=pid))
                try:api.check(api.k.TerminateProcess(h,98),'REMEDIAL_TERMINATE')
                except BaseException as exc:errors.append(dict(stage='REMEDIAL_TERMINATE',pid=pid,message=str(exc)))
                status=int(api.k.WaitForSingleObject(h,100))
            waits.append(dict(pid=pid,wait_status=status,remedial_termination_attempted=remedial))
        parent_wait=None
        if pi is not None:
            parent_wait=int(api.k.WaitForSingleObject(pi.hProcess,100))
            if parent_wait==0:parent_exit=api.exit_code(pi.hProcess)
        clean=final is not None and final['ActiveProcesses']==0 and parent_wait==0 and all(w['wait_status']==0 for w in waits)
        for h in list(retained.values())+([] if pi is None else [pi.hThread,pi.hProcess]):
            try:api.close(h)
            except BaseException as exc:errors.append(dict(stage='HANDLE_CLOSE',message=str(exc)))
        close_job()
        ok=clean and not timed_out and not errors and parent_exit==0
        result=dict(status='OUTER_CONTROL_COMPLETE' if ok else 'FAIL_OR_INCOMPLETE',
            run_id=record['run_id'],attempt_id=record['attempt_id'],approval_sha256=AUTHORIZATION_SHA,
            parent_start_calls=attempts,started_utc=began,ended_utc=utc(),elapsed_seconds=time.monotonic()-started,
            outer_wall_seconds=2460,timed_out=timed_out,parent_exit_code=parent_exit,parent_wait_status=parent_wait,
            job_handle_diagnostic=None if job is None else int(job),job_handle_state=state,
            final_outer_accounting=final,process_tree_exit_confirmed=clean,identities=identities,
            handle_waits=waits,actions=actions,errors=errors,production_admission='RUN_ADMISSION_BLOCKED')
        save('outer_receipt.json',result)
        print(json.dumps(dict(status=result['status'],parent_start_calls=attempts,parent_exit=parent_exit)))
    return 0 if ok else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--preflight-only',action='store_true')
    args=parser.parse_args()
    raise SystemExit(main(args.preflight_only))
