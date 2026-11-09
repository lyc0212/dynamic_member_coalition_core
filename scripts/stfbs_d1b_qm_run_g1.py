"""Future single authorized scientific child. Never run during Release engineering."""
import argparse,json,sys,traceback
from pathlib import Path

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--approval-file',required=True);parser.add_argument('--launch-ticket',required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
    from research.non_oracle.stfbs_d1b_qm_run_release import authorize_policy,verify_g1_launch,runtime_scope
    permit=authorize_policy(args.approval_file)
    binding=verify_g1_launch(permit,args.approval_file,args.launch_ticket)
    output=Path(permit.bindings['output_dir'])
    def save(name,value):
        with (output/name).open('x',encoding='utf-8') as f:json.dump(value,f,sort_keys=True,ensure_ascii=False,indent=2)
    save('RUNTIME_BINDING.json',binding)
    from research.non_oracle.stfbs_d1b_qm_budget import D1BBudget,inspect_journal
    from research.non_oracle.stfbs_d1b_qm_scenario import build_fixture
    from research.non_oracle.stfbs_d1b_qm_run_evidence import RealBatchOps,coordinate_batch
    budget=None;ops=None;result=None;error=None
    with runtime_scope(permit,binding):
        try:
            budget=D1BBudget.from_release(permit,output/'RAW_CALLS.jsonl')
            ops=RealBatchOps(permit,budget,build_fixture())
            result=coordinate_batch(ops)
            save('INDEPENDENT_AUDITS.json',ops.audits)
        except BaseException as exception:
            error=dict(error=repr(exception),traceback=traceback.format_exc())
            if ops is not None:ops.preserve_partial(exception)
        finally:
            if budget is not None:
                save('BUDGET_SNAPSHOT.json',budget.snapshot());budget.journal.close()
            ledger=inspect_journal(output/'RAW_CALLS.jsonl') if (output/'RAW_CALLS.jsonl').exists() else dict(status='RESOURCE_LEDGER_INCOMPLETE',reason='no journal')
            save('CALL_JOURNAL_AUDIT.json',ledger)
    if error or ledger['status']!='COMPLETE':
        save('SCIENTIFIC_RESULT.json',dict(status='BLOCKED',EXECUTION_VALID=False,reason=error,ledger_status=ledger['status'],partial_result=result));return 1
    save('SCIENTIFIC_RESULT.json',dict(status='COMPLETED_FROZEN_ATTEMPT',EXECUTION_VALID=True,result=result,ledger_status=ledger['status'],scope='Independent MODEL simulation; not ACTUAL flight; no automatic retry'))
    return 0

if __name__=='__main__':raise SystemExit(main())
