"""Exactly one nonphysical patch attempt under the existing generic Windows Job."""
import argparse,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.stfbs_d1b_qm_b3_minimal_patch_test_entry import HEAD,TASK,SUITE,IDS,PATCH_FILES,REPORT,sha,read,save,static_preflight,verify_receipts

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--suite',required=True,choices=[SUITE]);parser.add_argument('--evidence-dir',required=True)
    args=parser.parse_args();evidence=Path(args.evidence_dir).resolve()
    if Path.cwd().resolve()!=ROOT or evidence!=REPORT/'WATCHDOG_TEST_001':raise ValueError('Controlled patch paths required')
    if evidence.exists() or any((REPORT/n).exists() for n in ('RUN_POLICY.json','TEST_ATTEMPT.json','FINAL_ACCEPTANCE.json')):raise ValueError('Patch attempt already exists; no retry')
    # Failure here stops before registration; no automatic repair or restart.
    pins=static_preflight()
    import psutil
    proc=psutil.Process();entry=ROOT/'scripts/stfbs_d1b_qm_b3_minimal_patch_test_entry.py';policy_path=REPORT/'RUN_POLICY.json'
    command=[str(Path(sys.executable).resolve()),'-I','-B',str(entry),'--suite',SUITE,'--launch-ticket',str(evidence/'LAUNCH.json'),'--run-policy',str(policy_path),'--policy-sha256','<RUN_POLICY_SHA256>']
    policy=dict(task=TASK,suite=SUITE,head=HEAD,root=str(ROOT),test_ids=list(IDS),python=str(Path(sys.executable).resolve()),python_sha256=sha(sys.executable),
        python_version=sys.version,psutil_version=psutil.__version__,watchdog_script=str(Path(__file__).resolve()),entry_script=str(entry),
        watchdog_pid=proc.pid,watchdog_create_time=proc.create_time(),watchdog_command=proc.cmdline(),allowed_child_command=command,
        cpu_limit=120,wall_limit=180,attempts=1,source_pins=pins['source_pins'],patch_source_pins=pins['patch_source_pins'],evidence_dir=str(evidence),
        evidence_kind='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE',approval_path=None,real_g1_authorized=False)
    save(policy_path,policy);policy_sha=sha(policy_path)
    save(REPORT/'PATCH_SOURCE_SHA256.json',pins['patch_source_pins'])
    actual_command=[policy_sha if x=='<RUN_POLICY_SHA256>' else x for x in command]
    save(REPORT/'TEST_ATTEMPT.json',dict(task=TASK,suite=SUITE,attempt=1,watchdog_pid=proc.pid,policy_sha256=policy_sha,started_utc=time.time(),command=actual_command,automatic_retry=False))
    receipt=None;supervise_error=None
    try:
        from scripts.stfbs_d1a_watchdog import supervise
        receipt=supervise(actual_command,evidence,cpu_limit=120,wall_limit=180,cwd=ROOT,approval_path=None)
    except BaseException as error:supervise_error=repr(error)
    verified=None;error=None
    try:verified=verify_receipts(REPORT)
    except Exception as exception:error=repr(exception)
    ready=verified is not None
    save(REPORT/'FINAL_SUPERVISION_VERIFICATION.json',dict(status='PASS' if ready else 'BLOCKED',verification=verified,error=error,supervise_error=supervise_error))
    save(REPORT/'RESOURCE_LEDGER.json',dict(task=TASK,policy_sha256=policy_sha,actual_supervise_args=dict(cpu_limit=120,wall_limit=180,cwd=str(ROOT),approval_path=None),receipt=receipt,
        verification='PASS' if ready else 'UNVERIFIED',scope='Actual protected patch child process tree; synthetic G1 receipts are separate test inputs',supervise_error=supervise_error))
    save(REPORT/'FINAL_ACCEPTANCE.json',dict(status='B3_MINIMAL_PATCH_READY_FOR_INDEPENDENT_REVIEW' if ready else 'B3_MINIMAL_PATCH_BLOCKED',
        test_count=4,formal_attempts=1,protection_verified=ready,problem=error,real_science_executed=False,run_g1_authorized=False, historical_science_status='BLOCKED'))
    return 0 if ready else 1

if __name__=='__main__':raise SystemExit(main())
