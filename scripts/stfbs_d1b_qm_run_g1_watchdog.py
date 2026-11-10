"""Future approved batch supervisor. No CLI toggle or in-policy SHA grants authority."""
import argparse,json,sys,time,hashlib,math
from pathlib import Path

def validate_final_resource_receipt(receipt,approved_cpu_limit,approved_wall_limit):
    """Pure final validation; receipt limits never confer approval themselves."""
    r=receipt if type(receipt) is dict else {}
    def finite_number(value):return type(value) is int or type(value) is float and math.isfinite(value)
    cpu=r.get('tree_cpu_seconds');wall=r.get('wall_seconds')
    cpu_cap=r.get('cpu_limit');wall_cap=r.get('wall_limit')
    approved_valid=all(finite_number(v) and v>0 for v in (approved_cpu_limit,approved_wall_limit))
    measurement_valid=all(finite_number(v) and v>=0 for v in (cpu,wall))
    receipt_limits_valid=all(finite_number(v) and v>0 for v in (cpu_cap,wall_cap))
    numeric_valid=approved_valid and measurement_valid and receipt_limits_valid
    limits_match=approved_valid and receipt_limits_valid and cpu_cap==approved_cpu_limit and wall_cap==approved_wall_limit
    cpu_within=approved_valid and finite_number(cpu) and cpu>=0 and cpu<=approved_cpu_limit
    wall_within=approved_valid and finite_number(wall) and wall>=0 and wall<=approved_wall_limit
    single=type(r.get('attempts')) is int and r['attempts']==1
    exit_valid=(r.get('status')=='EXITED' and type(r.get('exit_code')) is int and r['exit_code']==0)
    cleanup_valid=type(r.get('active_processes')) is int and r['active_processes']==0
    reasons=[]
    if not approved_valid:reasons.append('INVALID_APPROVED_LIMIT')
    if not measurement_valid or not receipt_limits_valid:reasons.append('INVALID_RESOURCE_MEASUREMENT')
    if approved_valid and receipt_limits_valid and not limits_match:reasons.append('APPROVED_LIMIT_MISMATCH')
    if approved_valid and finite_number(cpu) and cpu>approved_cpu_limit:reasons.append('TREE_CPU_LIMIT_EXCEEDED')
    if approved_valid and finite_number(wall) and wall>approved_wall_limit:reasons.append('WALL_LIMIT_EXCEEDED')
    if not single:reasons.append('INVALID_ATTEMPT_COUNT')
    if not exit_valid:reasons.append('INVALID_EXIT_STATE')
    if r.get('cpu_complete') is not True:reasons.append('CPU_ACCOUNTING_INCOMPLETE')
    if not cleanup_valid:reasons.append('PROCESS_CLEANUP_NOT_VERIFIED')
    return dict(status='PASS' if not reasons else 'BLOCKED',numeric_valid=numeric_valid,
        approved_cpu_limit=approved_cpu_limit,approved_wall_limit=approved_wall_limit,
        receipt_cpu_limit=cpu_cap,receipt_wall_limit=wall_cap,tree_cpu_seconds=cpu,wall_seconds=wall,
        limits_match=limits_match,cpu_within_limit=cpu_within,wall_within_limit=wall_within,
        single_attempt_valid=single,exit_valid=exit_valid,cleanup_valid=cleanup_valid,
        cpu_accounting_complete=r.get('cpu_complete') is True,failure_reasons=reasons)

def final_resource_audit(receipt,approved_cpu_limit,approved_wall_limit,ledger,source_pins_unchanged):
    """The same final decision is used by main() and synthetic tests."""
    resource=validate_final_resource_receipt(receipt,approved_cpu_limit,approved_wall_limit)
    ledger_complete=type(ledger) is dict and ledger.get('status')=='COMPLETE'
    sources_valid=source_pins_unchanged is True
    reasons=list(resource['failure_reasons'])
    if not ledger_complete:reasons.append('RESOURCE_LEDGER_INCOMPLETE')
    if not sources_valid:reasons.append('SOURCE_PINS_CHANGED_OR_UNVERIFIED')
    valid=resource['status']=='PASS' and ledger_complete and sources_valid
    return dict(status='PASS' if valid else 'BLOCKED',source_pins_unchanged=source_pins_unchanged,
        receipt=receipt,journal_status=ledger.get('status') if type(ledger) is dict else None,no_retry=True,
        resource_validation=resource,ledger_complete=ledger_complete,failure_reasons=reasons)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--approval-file',required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
    from research.non_oracle.stfbs_d1b_qm_run_release import authorize_policy
    permit=authorize_policy(args.approval_file)  # Independent user root required before output/attempt creation.
    import psutil
    output=Path(permit.bindings['output_dir']);output.mkdir(exist_ok=False)
    approval_sha=hashlib.sha256(Path(args.approval_file).read_bytes()).hexdigest()
    with (output/'ATTEMPT.json').open('x',encoding='utf-8') as f:
        json.dump(dict(batch_id=permit.bindings['batch_id'],attempt_id=permit.bindings['attempt_id'],watchdog_pid=psutil.Process().pid,watchdog_create_time=psutil.Process().create_time(),approval_sha256=approval_sha,started_utc=time.time(),attempt=1,automatic_retry=False),f,indent=2)
    with (output/'APPROVAL_COPY.json').open('xb') as f:f.write(Path(args.approval_file).read_bytes())
    command=[str(Path(sys.executable).resolve()),'-I','-B',str(root/'scripts/stfbs_d1b_qm_run_g1.py'),'--approval-file',str(Path(args.approval_file).resolve()),'--launch-ticket',str(output/'WATCHDOG'/'LAUNCH.json')]
    from scripts.stfbs_d1a_watchdog import supervise
    receipt=supervise(command,output/'WATCHDOG',cpu_limit=permit.bindings['cpu_limit'],wall_limit=permit.bindings['wall_limit'],cwd=root,approval_path=Path(args.approval_file))
    from research.non_oracle.stfbs_d1b_qm_budget import inspect_journal
    ledger=inspect_journal(output/'RAW_CALLS.jsonl') if (output/'RAW_CALLS.jsonl').is_file() else dict(status='RESOURCE_LEDGER_INCOMPLETE')
    unchanged=all(hashlib.sha256((root/name).read_bytes()).hexdigest()==wanted for name,wanted in permit.bindings['source_pins'].items())
    audit=final_resource_audit(receipt,permit.bindings['cpu_limit'],permit.bindings['wall_limit'],ledger,unchanged)
    valid=audit['status']=='PASS'
    with (output/'FINAL_EXTERNAL_RESOURCE_AUDIT.json').open('x',encoding='utf-8') as f:json.dump(audit,f,indent=2)
    return 0 if valid else 1

if __name__=='__main__':raise SystemExit(main())
