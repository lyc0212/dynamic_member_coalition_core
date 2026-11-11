"""Single fixed-parameter native attempt; no CPU repair or scientific RUN."""
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

import pytest

from research.non_oracle.stfbs_lite_real_d60_supervisor_win import WindowsSupervisor
from research.quality_allocation.service_m3_benchmarks.windows_job_monitor.api import ExtendedLimit, layout

ROOT=Path(__file__).resolve().parents[1]
HEAD='2897e5a477cf750a6ed80e1cae1875612a2d7c89'


@pytest.mark.skipif(os.name!='nt',reason='Windows native evidence required')
def test_single_job_process_membership_diagnostic():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==HEAD
    layout()
    directory=Path(tempfile.mkdtemp(prefix='stfbs-job-membership-'))
    evidence=dict(task_id='STFBS_LITE_REAL_D60_JOB_PROCESS_MEMBERSHIP_DIAGNOSTIC_V1',git_head=HEAD,
        windows_version=platform.platform(),python_executable=sys.executable,configured_cpu_limit=.15,
        configured_wall_limit=5.,supervisor_pid=os.getpid(),sampling_records=[],identities={},query_errors=[],
        observed_accounting_changes=[],observed_pid_changes=[],wall_termination_requested=False,
        wall_termination_result=None,supervisor_final_cleanup=None,job_cleanup_confirmed=False,
        diagnostic_classification='JOB_PROCESS_MEMBERSHIP_DIAGNOSTIC_PARTIAL',
        cpu_root_cause_status='NOT_DETERMINED',remaining_uncertainties=['JOB_ANCESTRY_NOT_FULLY_VERIFIED',
          'NON_ATOMIC_CPU_QUERIES_DIFFERENT_ACCUMULATION_ORIGINS',
          'COOPERATIVE_DEADLINE_CHECK_NOT_INDEPENDENT_HARD_SUPERVISION'])
    supervisor=None
    phase='OBSERVATION'
    try:
        supervisor=WindowsSupervisor(wall_seconds=5.,user_cpu_seconds=.15)
        api=supervisor.api
        k=api.k
        class ProcessEntry(C.Structure):
            _fields_=[('dwSize',W.DWORD),('cntUsage',W.DWORD),('th32ProcessID',W.DWORD),
                ('th32DefaultHeapID',C.c_size_t),('th32ModuleID',W.DWORD),('cntThreads',W.DWORD),
                ('th32ParentProcessID',W.DWORD),('pcPriClassBase',W.LONG),('dwFlags',W.DWORD),('szExeFile',W.WCHAR*260)]
        assert C.sizeof(ProcessEntry)==568
        signatures={
            'CreateToolhelp32Snapshot':([W.DWORD,W.DWORD],W.HANDLE),
            'Process32FirstW':([W.HANDLE,C.POINTER(ProcessEntry)],W.BOOL),
            'Process32NextW':([W.HANDLE,C.POINTER(ProcessEntry)],W.BOOL),
            'QueryFullProcessImageNameW':([W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)],W.BOOL),
            'GetProcessTimes':([W.HANDLE]+[C.POINTER(W.FILETIME)]*4,W.BOOL),
            'GetSystemTimeAsFileTime':([C.POINTER(W.FILETIME)],None)}
        for name,(args,ret) in signatures.items():
            fn=getattr(k,name);fn.argtypes=args;fn.restype=ret

        def error(op,errors):
            number=C.get_last_error()
            errors.append(dict(operation=op,win32_error=number,message=C.FormatError(number)))

        def ft(value): return (int(value.dwHighDateTime)<<32)|int(value.dwLowDateTime)

        def signal(handle,errors,label):
            result=int(k.WaitForSingleObject(handle,0))
            if result==0xffffffff:error(label,errors)
            return result

        def process_times(handle,errors):
            creation,exit_time,kernel,user=(W.FILETIME() for _ in range(4))
            if not k.GetProcessTimes(handle,C.byref(creation),C.byref(exit_time),C.byref(kernel),C.byref(user)):
                error('GetProcessTimes',errors);return None
            state=signal(handle,errors,'Process signal')
            return dict(CreationTime=ft(creation),ExitTime=ft(exit_time) if state==0 else None,
                        UserTime=ft(user),KernelTime=ft(kernel),signal=state)

        def pid_list(errors):
            capacity=16
            while capacity<=4096:
                class PIDList(C.Structure):
                    _fields_=[('NumberOfAssignedProcesses',W.DWORD),('NumberOfProcessIdsInList',W.DWORD),
                              ('ProcessIdList',C.c_size_t*capacity)]
                data=PIDList();length=W.DWORD()
                C.set_last_error(0)
                ok=k.QueryInformationJobObject(supervisor.job,3,C.byref(data),C.sizeof(data),C.byref(length))
                code=C.get_last_error() if not ok else 0
                if ok:
                    n=int(data.NumberOfProcessIdsInList)
                    return dict(NumberOfAssignedProcesses=int(data.NumberOfAssignedProcesses),
                        NumberOfProcessIdsInList=n,ProcessIdList=[int(p) for p in data.ProcessIdList[:min(n,capacity)]],
                        capacity=capacity,returned_length=int(length.value),api_success=True,win32_error=0,
                        complete_list=n<=capacity and n==int(data.NumberOfAssignedProcesses))
                if code!=234:
                    error('QueryInformationJobObject/PIDList',errors);break
                capacity*=2
                if hasattr(supervisor,'started') and time.monotonic()-supervisor.started>=4.75:
                    break
            return dict(complete_list=False,status='PID_QUERY_INCOMPLETE',win32_error=code,capacity=capacity)

        def member(handle,job,errors):
            try:return api.member(handle,job)
            except OSError as exc:
                errors.append(dict(operation='IsProcessInJob',win32_error=exc.winerror,message=str(exc)))
                return None

        def identity_queries(pids,elapsed,errors):
            if time.monotonic()-supervisor.started>=4.75:
                return [dict(status='IDENTITY_QUERY_SKIPPED_FOR_WALL_DEADLINE')]
            snapshot=k.CreateToolhelp32Snapshot(2,0)
            names={}
            if snapshot==C.c_void_p(-1).value:
                error('CreateToolhelp32Snapshot',errors)
            else:
                try:
                    entry=ProcessEntry();entry.dwSize=C.sizeof(entry)
                    ok=k.Process32FirstW(snapshot,C.byref(entry))
                    while ok:
                        if int(entry.th32ProcessID) in pids:
                            names[int(entry.th32ProcessID)]=dict(parent_pid=int(entry.th32ParentProcessID),executable_name=entry.szExeFile)
                        if time.monotonic()-supervisor.started>=4.75:break
                        ok=k.Process32NextW(snapshot,C.byref(entry))
                    if not ok and C.get_last_error()!=18:error('Toolhelp process enumeration',errors)
                finally:api.close(snapshot)
            found=[]
            for pid in pids:
                if time.monotonic()-supervisor.started>=4.75:
                    found.append(dict(pid=pid,status='IDENTITY_QUERY_SKIPPED_FOR_WALL_DEADLINE'));continue
                row=dict(pid=pid,**names.get(pid,{}))
                handle=k.OpenProcess(0x1000|0x100000,False,pid)
                if not handle:
                    error('OpenProcess/QUERY_LIMITED',errors);row['identity_status']='UNAVAILABLE';found.append(row);continue
                try:
                    times=process_times(handle,errors);row['process_times']=times
                    path=C.create_unicode_buffer(32768);size=W.DWORD(len(path))
                    if k.QueryFullProcessImageNameW(handle,0,path,C.byref(size)):row['executable_path']=path.value
                    else:error('QueryFullProcessImageNameW',errors)
                    row['member_of_target_job']=member(handle,supervisor.job,errors)
                    row['member_of_any_job']=member(handle,None,errors)
                    key=f"{pid}:{times['CreationTime'] if times else 'UNKNOWN_CREATION'}"
                    existing=evidence['identities'].get(key)
                    row['first_observed_wall_time']=elapsed if existing is None else existing['first_observed_wall_time']
                    row['last_observed_wall_time']=elapsed
                    evidence['identities'][key]=dict(row)
                finally:api.close(handle)
                found.append(row)
            return found

        extended=ExtendedLimit()
        api.check(k.QueryInformationJobObject(supervisor.job,9,C.byref(extended),C.sizeof(extended),None),'CPU limit readback')
        evidence['readback_cpu_limit']=dict(LimitFlags=int(extended.BasicLimitInformation.LimitFlags),
            PerJobUserTimeLimit=int(extended.BasicLimitInformation.PerJobUserTimeLimit))
        evidence['parent_in_any_job']=member(k.GetCurrentProcess(),None,evidence['query_errors'])
        evidence['parent_in_target_job']=member(k.GetCurrentProcess(),supervisor.job,evidence['query_errors'])
        original_resume=api.resume
        def resume(thread):
            evidence['worker_in_target_job_before_resume']=member(supervisor.pi.hProcess,supervisor.job,evidence['query_errors'])
            assert evidence['worker_in_target_job_before_resume'] is True
            original_resume(thread)
        api.resume=resume
        terminate=api.terminate
        def tracked_terminate(job):
            row=dict(kind=phase,elapsed_wall=time.monotonic()-supervisor.started)
            terminate(job);row['result']='SUCCESS'
            if phase=='SUPERVISOR_FINAL_CLEANUP':
                k.WaitForSingleObject(supervisor.pi.hProcess,3000)
                until=time.monotonic()+3.
                while api.accounting(job)['ActiveProcesses'] and time.monotonic()<until:time.sleep(.01)
                evidence['job_cleanup_confirmed']=api.accounting(job)['ActiveProcesses']==0
                evidence['supervisor_final_cleanup']=row
            else:evidence['wall_termination_result']=row
        api.terminate=tracked_terminate
        utc=W.FILETIME();k.GetSystemTimeAsFileTime(C.byref(utc));evidence['window_start_filetime']=ft(utc)
        evidence['worker_pid']=supervisor.start([sys.executable,'-B','-c','while True: pass'],cwd=ROOT,log=directory/'worker.log')
        evidence['worker_in_target_job']=member(supervisor.pi.hProcess,supervisor.job,evidence['query_errors'])
        evidence['worker_in_any_job']=member(supervisor.pi.hProcess,None,evidence['query_errors'])
        last_counts,last_pids=None,None
        while True:
            if time.monotonic()-supervisor.started>=5.:
                phase='WALL_TERMINATE_JOB_REQUESTED'
                evidence['job_signal_before_wall_kill']=signal(supervisor.job,evidence['query_errors'],'Job signal before wall')
                evidence['worker_signal_before_wall_kill']=signal(supervisor.pi.hProcess,evidence['query_errors'],'Worker signal before wall')
                if evidence['worker_signal_before_wall_kill']!=0:
                    evidence['wall_termination_requested']=True;api.terminate(supervisor.job)
                break
            row=dict(timestamp_start=time.monotonic()-supervisor.started,query_errors=[])
            row['accounting_before']=api.accounting(supervisor.job)
            row['pid_query']=pid_list(row['query_errors'])
            row['accounting_after']=api.accounting(supervisor.job)
            row['timestamp_end']=time.monotonic()-supervisor.started
            row['worker_process_times']=process_times(supervisor.pi.hProcess,row['query_errors'])
            row['job_signal']=signal(supervisor.job,row['query_errors'],'Job signal')
            row['worker_signal']=signal(supervisor.pi.hProcess,row['query_errors'],'Worker signal')
            counts=tuple(row['accounting_after'][k] for k in ('TotalProcesses','ActiveProcesses','TotalTerminatedProcesses'))
            pids=row['pid_query'].get('ProcessIdList',[])
            if any(row['accounting_before'][k]!=row['accounting_after'][k] for k in ('TotalProcesses','ActiveProcesses','TotalTerminatedProcesses')):
                row['non_atomic_warning']='NON_ATOMIC_SNAPSHOT_OR_PROCESS_TRANSITION_POSSIBLE'
            changed=counts!=last_counts or pids!=last_pids
            if counts!=last_counts:evidence['observed_accounting_changes'].append(dict(elapsed_wall=row['timestamp_end'],counts=counts))
            if pids!=last_pids:evidence['observed_pid_changes'].append(dict(elapsed_wall=row['timestamp_end'],pids=pids))
            if changed:
                row['relevant_pid_identities']=identity_queries(pids,row['timestamp_end'],row['query_errors'])
            else:row['relevant_pid_identities']=[]
            evidence['sampling_records'].append(row)
            last_counts,last_pids=counts,list(pids)
            if row['worker_signal']==0:
                evidence['worker_exit_before_wall']=dict(elapsed_wall=time.monotonic()-supervisor.started,
                    exit_code=api.exit_code(supervisor.pi.hProcess),job_signal=row['job_signal'])
                break
            time.sleep(min(.05,max(0.,5.-(time.monotonic()-supervisor.started))))
        k.GetSystemTimeAsFileTime(C.byref(utc));evidence['window_end_filetime']=ft(utc)
        records=evidence['sampling_records']
        extra=any(any(pid!=evidence['worker_pid'] for pid in r['pid_query'].get('ProcessIdList',[])) for r in records)
        mismatch=any(r['pid_query']['complete_list'] and r['accounting_before']['ActiveProcesses']==r['accounting_after']['ActiveProcesses']
                     and r['accounting_after']['ActiveProcesses']!=len(r['pid_query']['ProcessIdList']) for r in records)
        evidence['diagnostic_classification']=('JOB_ADDITIONAL_PID_OBSERVED' if extra else
            'JOB_ACCOUNTING_PID_LIST_DISCREPANCY_OBSERVED' if mismatch else 'JOB_MEMBERSHIP_DISCREPANCY_NOT_REPRODUCED')
        if any(not r['pid_query']['complete_list'] for r in records):
            evidence['remaining_uncertainties'].append('PID_QUERY_INCOMPLETE')
    except BaseException as exc:
        evidence['diagnostic_error']=dict(type=type(exc).__name__,message=str(exc))
        evidence['diagnostic_classification']='JOB_PROCESS_MEMBERSHIP_DIAGNOSTIC_PARTIAL'
    finally:
        if supervisor is not None:
            phase='SUPERVISOR_FINAL_CLEANUP'
            try:supervisor.close()
            except BaseException as exc:evidence['cleanup_error']=dict(type=type(exc).__name__,message=str(exc))
        raw=json.dumps(evidence,sort_keys=True,ensure_ascii=False,indent=2).encode('utf-8')
        path=directory/'evidence.json';path.write_bytes(raw)
        summary={k:v for k,v in evidence.items() if k not in ('sampling_records',)}
        summary.update(evidence_path=str(path),evidence_sha256=hashlib.sha256(raw).hexdigest(),
                       sample_count=len(evidence['sampling_records']),
                       last_sample=evidence['sampling_records'][-1] if evidence['sampling_records'] else None)
        print(json.dumps(summary,sort_keys=True,ensure_ascii=False),flush=True)
    assert evidence['job_cleanup_confirmed'], 'Worker/Job cleanup not confirmed'
    assert 'diagnostic_error' not in evidence, 'Partial diagnostic; no automatic rerun permitted'
