"""One native diagnostic attempt, fixed .15 user-CPU/5 wall; never a RUN gate PASS."""
import ctypes as C
from ctypes import wintypes as W
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

ROOT = Path(__file__).resolve().parents[1]
HEAD = '606d9bac6bc6d6238291baf0f61e241c18bc2673'


@pytest.mark.skipif(os.name != 'nt', reason='Native Windows evidence required; skip is not PASS')
def test_single_native_job_cpu_diagnostic():
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == HEAD
    layout()
    evidence = dict(task_id='STFBS_LITE_REAL_D60_JOB_CPU_DIAGNOSTIC_V1',git_head=HEAD,
        windows_version=platform.platform(),python_executable=sys.executable,
        configured_user_cpu_seconds=.15,configured_wall_seconds=5.,readbacks=[],
        readback_win32_error_if_any=[],pretermination_samples=[],termination_events=[],
        wall_termination_requested=False,wall_termination_result=None,
        supervisor_final_cleanup=None,job_cleanup_confirmed=False,
        diagnostic_classification='JOB_CPU_DIAGNOSTIC_INCONCLUSIVE',remaining_uncertainties=[])
    phase = 'OBSERVATION'
    supervisor = None
    original_terminate = None
    try:
        with tempfile.TemporaryDirectory(prefix='stfbs-job-cpu-diagnostic-') as directory:
            supervisor = WindowsSupervisor(wall_seconds=5.,user_cpu_seconds=.15)
            api = supervisor.api

            def wait(handle, label):
                C.set_last_error(0)
                result = int(api.k.WaitForSingleObject(handle,0))
                if result == 0xffffffff:
                    error=C.get_last_error()
                    evidence['readback_win32_error_if_any'].append(dict(operation=label,error=error,message=C.FormatError(error)))
                    raise OSError(error,label)
                assert result in (0,0x102)
                return result

            class EndOfJobTime(C.Structure):
                _fields_=[('EndOfJobTimeAction',W.DWORD)]

            def readback(stage):
                extended, end = ExtendedLimit(), EndOfJobTime()
                for info, kind in ((extended,9),(end,6)):
                    C.set_last_error(0)
                    ok = api.k.QueryInformationJobObject(supervisor.job,kind,C.byref(info),C.sizeof(info),None)
                    if not ok:
                        error=C.get_last_error()
                        evidence['readback_win32_error_if_any'].append(dict(operation=f'QueryInformationJobObject/{kind}',error=error,message=C.FormatError(error)))
                        raise OSError(error,'Job readback failed')
                row=dict(stage=stage,LimitFlags=int(extended.BasicLimitInformation.LimitFlags),
                         PerJobUserTimeLimit=int(extended.BasicLimitInformation.PerJobUserTimeLimit),
                         EndOfJobTimeAction=int(end.EndOfJobTimeAction))
                evidence['readbacks'].append(row)

            evidence['parent_in_any_job']=api.member(api.k.GetCurrentProcess(),None)
            readback('BEFORE_WORKER_START')
            original_resume=api.resume
            def checked_resume(thread):
                evidence['worker_target_job_membership_before_resume']=api.member(supervisor.pi.hProcess,supervisor.job)
                if not evidence['worker_target_job_membership_before_resume']:
                    raise RuntimeError('Worker not contained before resume')
                original_resume(thread)
            api.resume=checked_resume
            original_terminate=api.terminate
            def recorded_terminate(job):
                elapsed=time.monotonic()-supervisor.started if hasattr(supervisor,'started') else None
                row=dict(kind=phase,elapsed_wall=elapsed,result=None)
                evidence['termination_events'].append(row)
                try:
                    original_terminate(job)
                    row['result']='SUCCESS'
                    if phase == 'SUPERVISOR_FINAL_CLEANUP':
                        if supervisor.pi is not None:
                            api.k.WaitForSingleObject(supervisor.pi.hProcess,3000)
                        deadline=time.monotonic()+3.
                        while api.accounting(job)['ActiveProcesses'] and time.monotonic()<deadline:
                            time.sleep(.01)
                        evidence['job_cleanup_confirmed']=api.accounting(job)['ActiveProcesses']==0
                        evidence['supervisor_final_cleanup']=dict(row)
                except BaseException as exc:
                    row['result']=type(exc).__name__
                    raise
            api.terminate=recorded_terminate
            try:
                evidence['worker_pid']=supervisor.start([sys.executable,'-B','-c','while True: pass'],
                    cwd=ROOT,log=Path(directory)/'worker.log')
                readback('AFTER_CONTAINMENT_AND_RESUME')
                evidence['worker_target_job_membership']=api.member(supervisor.pi.hProcess,supervisor.job)
                evidence['worker_any_job_membership']=api.member(supervisor.pi.hProcess,None)
                evidence['target_job_process_ids']=api.pids(supervisor.job)
                evidence['target_job_active_processes']=api.accounting(supervisor.job)['ActiveProcesses']

                def sample():
                    job_signal=wait(supervisor.job,'Job signal')
                    process_signal=wait(supervisor.pi.hProcess,'Worker signal')
                    accounting=api.accounting(supervisor.job)
                    return dict(elapsed_wall=time.monotonic()-supervisor.started,
                        job_signal_state=job_signal,worker_signal_state=process_signal,
                        active_processes=accounting['ActiveProcesses'],
                        total_user_time_100ns=accounting['TotalUserTime'],
                        total_kernel_time_100ns=accounting['TotalKernelTime'],
                        worker_exit_code_if_exited=api.exit_code(supervisor.pi.hProcess) if process_signal==0 else None)

                last=None
                while True:
                    last=sample()
                    evidence['pretermination_samples'].append(last)
                    if last['worker_signal_state']==0:
                        break
                    if time.monotonic()-supervisor.started >= 5.:
                        evidence['job_signal_before_wall_kill']=last['job_signal_state']
                        evidence['worker_signal_before_wall_kill']=last['worker_signal_state']
                        evidence['wall_termination_requested']=True
                        phase='WALL_TERMINATE_JOB_REQUESTED'
                        api.terminate(supervisor.job)
                        evidence['wall_termination_result']='SUCCESS'
                        break
                    remaining=5.-(time.monotonic()-supervisor.started)
                    time.sleep(min(.05,max(0.,remaining)))
                evidence['pretermination_last']=last
                api.k.WaitForSingleObject(supervisor.pi.hProcess,3000)
                accounting=api.accounting(supervisor.job)
                evidence.update(worker_exit_code=api.exit_code(supervisor.pi.hProcess),
                    total_user_time_100ns=accounting['TotalUserTime'],total_kernel_time_100ns=accounting['TotalKernelTime'])
                config_ok=all(r['LimitFlags']==0x2004 and r['PerJobUserTimeLimit']==1500000
                              and r['EndOfJobTimeAction']==0 for r in evidence['readbacks'])
                if not config_ok:
                    evidence['diagnostic_classification']='JOB_CPU_CONFIGURATION_READBACK_CONFLICT'
                elif evidence['wall_termination_requested']:
                    evidence['diagnostic_classification']='JOB_CPU_LIMIT_NOT_ENFORCED_WITHIN_OBSERVED_WINDOW'
                elif (last['job_signal_state']==0 and last['worker_signal_state']==0
                      and last['worker_exit_code_if_exited']==1816 and last['total_user_time_100ns']>=1500000
                      and last['elapsed_wall']<5.):
                    evidence['termination_events'].append(dict(kind='CPU_LIMIT_TERMINATION_OBSERVED',sample=last))
                    evidence['diagnostic_classification']='JOB_CPU_TERMINATION_OBSERVED'
                else:
                    evidence['remaining_uncertainties'].append('WORKER_EXIT_CAUSE_UNVERIFIED')
            finally:
                phase='SUPERVISOR_FINAL_CLEANUP'
                supervisor.close()
    except BaseException as exc:
        evidence['diagnostic_error']=dict(type=type(exc).__name__,message=str(exc))
        evidence['remaining_uncertainties'].append('PARTIAL_API_OR_CLEANUP_EVIDENCE')
    finally:
        if supervisor is not None and not supervisor.closed:
            phase='SUPERVISOR_FINAL_CLEANUP'
            try: supervisor.close()
            except BaseException as exc:
                evidence['cleanup_error']=dict(type=type(exc).__name__,message=str(exc))
        evidence['evidence_status']=('JOB_CPU_DIAGNOSTIC_EVIDENCE_CAPTURED'
            if evidence['job_cleanup_confirmed'] and 'diagnostic_error' not in evidence else 'JOB_CPU_DIAGNOSTIC_PARTIAL')
        evidence['remaining_uncertainties'].extend([
            'ONE_ATTEMPT_DOES_NOT_EXPLAIN_PRIOR_FAILURE_OR_ESTABLISH_RELIABILITY',
            'FULL_JOB_ANCESTRY_NOT_ENUMERATED','CPU_GATE_AND_REAL_RUN_ADMISSION_REMAIN_UNVERIFIED'])
        print(json.dumps(evidence,sort_keys=True,ensure_ascii=False),flush=True)
    assert evidence['job_cleanup_confirmed'], 'Native worker cleanup not confirmed'
    assert 'diagnostic_error' not in evidence, 'Partial diagnostic: see structured JSON evidence'
