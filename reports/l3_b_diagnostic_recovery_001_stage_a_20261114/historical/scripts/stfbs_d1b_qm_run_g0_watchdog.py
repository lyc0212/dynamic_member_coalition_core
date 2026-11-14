"""Only the RUN_G0 whitelist suite, once, under the existing generic Job watchdog."""
import argparse,json,sys,os,time,hashlib,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from research.non_oracle.stfbs_d1b_qm_run_audit import static_preflight,verify_receipts,sha,read,save,HEAD,TASK,SUITE,NEW_FILES,IDS

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--suite',required=True,choices=[SUITE]);parser.add_argument('--evidence-dir',required=True)
    args=parser.parse_args();report=ROOT/'reports/stfbs_lite_d1b_qm_run_g0_001'
    evidence=Path(args.evidence_dir).resolve()
    if Path.cwd().resolve()!=ROOT or evidence!=report/'WATCHDOG_TEST_001':raise ValueError('RUN_G0 controlled paths required')
    if evidence.exists() or any((report/n).exists() for n in ('RUN_POLICY.json','TEST_ATTEMPT.json','ACCEPTANCE.json')):raise ValueError('RUN_G0 attempt/path already exists; no retry')
    pins=static_preflight(ROOT)
    import psutil
    # Environment identities are checked against the already recorded runtime, not invented here.
    runtime=read(ROOT/'reports/stfbs_lite_d1a_h1_preflight_lock_001/RUNTIME_IDENTITY.json')['runtime']
    if sys.version!=runtime['python']['version'] or sha(sys.executable)!=runtime['python']['exe_sha256'] or psutil.__version__!=runtime['psutil']['version'] or sha(psutil.__file__)!=runtime['psutil']['module_sha256']:raise ValueError('RUN_G0 runtime identity mismatch')
    for p,s in {**runtime['python']['DLLs'],**runtime['psutil_native']}.items():
        if sha(p)!=s:raise ValueError('RUN_G0 runtime binary mismatch')
    me=psutil.Process();entry=ROOT/'scripts/stfbs_d1b_qm_run_g0_test_entry.py';policy_path=report/'RUN_POLICY.json'
    command=[str(Path(sys.executable).resolve()),'-I','-B',str(entry),'--suite',SUITE,'--launch-ticket',str(evidence/'LAUNCH.json'),'--run-policy',str(policy_path),'--policy-sha256','<RUN_POLICY_SHA256>']
    policy=dict(task=TASK,suite=SUITE,root=str(ROOT),head=HEAD,test_ids=list(IDS),python=str(Path(sys.executable).resolve()),python_sha256=sha(sys.executable),
        watchdog_script=str(Path(__file__).resolve()),entry_script=str(entry),watchdog_pid=me.pid,watchdog_create_time=me.create_time(),watchdog_command=me.cmdline(),
        allowed_child_command=command,command_digest_rule='Replace sole <RUN_POLICY_SHA256> placeholder with actual policy bytes SHA256; avoids self-referential hash',
        cpu_limit=120,wall_limit=180,attempts=1,forbidden_science=['WLS','real fusion','raw physical sampling','MODEL advancement','ACTUAL STEP','R search'],
        source_pins=pins['source_pins'],new_source_pins=pins['new_source_pins'],archive_identity=str(report),evidence_dir=str(evidence))
    save(policy_path,policy);policy_sha=sha(policy_path)
    save(report/'SOURCE_DIFF_MANIFEST.json',dict(head=HEAD,new_files=list(NEW_FILES),new_source_pins=pins['new_source_pins'],existing_sources_unchanged=False,allowed_existing_modifications=['research/non_oracle/stfbs_d1b_qm_execution.py','research/non_oracle/stfbs_d1b_qm_budget.py'],frozen_science_and_archives_unchanged=True,design_archives_unchanged=True))
    save(report/'STATIC_GUARD_COVERAGE.json',dict(status='STATIC_REVIEWED',test_ids=list(IDS),guard_install_order='estimator/solver first; production/new module imports; wrappers/aliases/quality/physics; verify guards; only then import ten tests',known_paths=['Branch.assign -> prepare_assignment -> Branch.fuse (only test-scoped fake allowed)','real fuse -> raw/cache -> BridgeFrameProcessor.process -> delayed _estimate -> estimator.estimate -> least_squares','public_quality.FrameProcessor.process and delayed _estimate','Budget.estimator closure -> model.estimate; policy estimate aliases','Branch.run/advance/finish, QMBranch.run, OnlineEnvironment.step/_advance_tick, Environment/TimedEnvironment.step, service rollout/advance_clock','R policy decide/evaluate are forbidden, not used by preset actions'],allowed_nonphysical=['Config/Target validation','public prior activation/empty-queue freeze','role offset construction','raw cache with labelled synthetic producer','guarded fake-fuse assignment transactions','ProbeSchedule real QMBranch gate rejects before assign/advance; synthetic port only','execute_probe/execute_dynamic/real_estimator_binding fail closed before scientific methods','public candidate-only rejection']))
    actual_command=[policy_sha if s=='<RUN_POLICY_SHA256>' else s for s in command]
    # This exclusive record consumes the one formal attempt even if launch fails.
    save(report/'TEST_ATTEMPT.json',dict(task=TASK,suite=SUITE,attempt=1,watchdog_pid=me.pid,policy_sha256=policy_sha,
        started_utc=time.time(),command=actual_command,supervise_args=dict(wall_limit=180,cpu_limit=120,cwd=str(ROOT),approval_path=None),automatic_retry=False))
    from scripts.stfbs_d1a_watchdog import supervise
    receipt=supervise(actual_command,evidence,wall_limit=180,cpu_limit=120,cwd=ROOT,approval_path=None)
    verification=None;problem=None
    try:verification=verify_receipts(report)
    except Exception as error:problem=repr(error)
    ready=verification is not None
    save(report/'FINAL_SUPERVISION_VERIFICATION.json',dict(status='PASS' if ready else 'PROTECTION_NOT_VERIFIED',verification=verification,error=problem))
    save(report/'RESOURCE_LEDGER.json',dict(task=TASK,policy_sha256=policy_sha,actual_supervise_args=dict(cpu_limit=120,wall_limit=180,cwd=str(ROOT),approval_path=None),
        receipt=receipt,measurement_scope='Existing Windows Job accounting covers primary process and descendants; no H1-specific validator used',verification='PASS' if ready else 'PROTECTION_NOT_VERIFIED'))
    status='D1_B_QM_1B_RUN_G0_READY_FOR_REVIEW' if ready else 'D1_B_QM_1B_RUN_G0_BLOCKED'
    save(report/'ACCEPTANCE.json',dict(status=status,task=TASK,suite=SUITE,formal_attempts=1,protection_verified=ready,problem=problem,
        fixture_status='STRUCTURALLY_VALIDATED_UNFUSED_MODEL_FIXTURE',physical_validation=False,real_Q_results=False,next_stage_authorized=False))
    return 0 if ready else 1

if __name__=='__main__':raise SystemExit(main())
