"""Single serial run; never resume, repeat a gate, or repair frozen sources."""
from copy import deepcopy
import json
import math
from pathlib import Path
import sys
import time
import traceback

from .common import (ROOT, BASE, PROTOCOL, CONTRACT, ORDER, PREDICTIONS,
                     require, read_json, save_json, file_pin, sha_file, ordered_total)
from .prepare import prepare, verify, pair, attach_pins


def _audit_job(attempt, name):
    template=read_json(attempt/'jobs'/f'{name}.template.json');payload=deepcopy(template['payload'])
    prod=payload['current']['producer_records'][0]
    result=read_json(prod['env_result_file'])
    require(result.get('passed') is True and
            [r['result_file'] for r in result['items']]==payload['current']['candidate_result_files'],
            'CURRENT_PREDICTION_COVERAGE',name)
    env=Path(prod['env_result_file']).parent.resolve()
    for path in payload['current']['candidate_result_files']:
        require(not Path(path).is_symlink() and Path(path).resolve().parents[2]==env,
                'CANDIDATE_OUTSIDE_CURRENT_PRODUCER')
    prod['files']=[file_pin(p) for p in payload['current']['candidate_result_files']]
    return pair(attempt,name,attach_pins(payload,template['exact_read_files']))


def _gate1_job(attempt):
    template=read_json(attempt/'jobs/G1.template.json');payload=template['payload']
    files=[str(f) for f in (attempt/'pairs/G0').rglob('*') if f.is_file() and f.suffix in ('.json','.jsonl')]
    payload['G0_supervision_file']=str(attempt/'pairs/G0/memory_supervision_receipt.json')
    return pair(attempt,'G1',attach_pins(payload,[*template['base_paths'],*files]))


def _final_job(attempt, ledger):
    # Keep actual pre-Z bytes; never later relabel the final eleven-job ledger
    # as the worker's original ten-job input.
    save_json(attempt/'preZ_resource_ledger.json',ledger)
    payload=dict(kind='memory_final',protected_role='audit',
        memory_inputs_file=str(PROTOCOL/'INPUT_PINS.json'),
        acceptance_matrix_file=str(PROTOCOL/'ACCEPTANCE_MATRIX.json'),
        measurement_contract_file=str(PROTOCOL/'MEASUREMENT_CONTRACT.json'),
        execution_seal_file=str(attempt/'SOURCE_SEAL.json'),
        expected_source_seal_sha256=sha_file(attempt/'SOURCE_SEAL.json'),
        ledger_file=str(attempt/'preZ_resource_ledger.json'),
        gate_result_files={n:str(attempt/'pairs'/n/'env/result.json') for n in ('G0','G1')},
        audit_result_files={n:str(attempt/'pairs'/(n+'_AUDIT')/'env/result.json') for n in PREDICTIONS},
        prediction_guardian_files={n:str(attempt/'pairs'/n/'guardian_result.json') for n in PREDICTIONS},
        prediction_job_files={n:str(attempt/'dispatched_jobs'/f'{n}.json') for n in PREDICTIONS},
        run_declaration_files={n:str(attempt/'runs'/f'{n}.json') for n in PREDICTIONS},
        memory_runtime_files={n:str(attempt/'pairs'/n/'env/memory_runtime.json') for n in PREDICTIONS},
        memory_sidecar_files={n:str(attempt/'pairs'/n/'env/memory_measurements.jsonl') for n in PREDICTIONS})
    paths=[payload['memory_inputs_file'],payload['acceptance_matrix_file'],payload['measurement_contract_file'],
           payload['execution_seal_file'],payload['ledger_file']]
    for key in ('gate_result_files','audit_result_files','prediction_guardian_files','prediction_job_files',
                'run_declaration_files','memory_runtime_files','memory_sidecar_files'):
        paths.extend(payload[key].values())
    inputs=read_json(PROTOCOL/'INPUT_PINS.json')
    paths += [pin['path'] for pin in inputs['registered_reference']['saved_reference']['candidates']]
    for name in PREDICTIONS:
        # Grant report dependencies from the designated producer declaration,
        # never from a report's self-selected artifact references.
        prediction_result=read_json(attempt/'pairs'/name/'env/result.json')
        paths += [item['result_file'] for item in prediction_result['items']]
    for name in ORDER[:10]:
        paths += [str(attempt/'pairs'/name/'guardian_result.json'),
                  str(attempt/'pairs'/name/'memory_supervision_receipt.json'),
                  str(attempt/'pairs'/name/'sense/counters.json'),str(attempt/'dispatched_jobs'/f'{name}.json')]
    # Audits have already run the frozen scientific comparer. Read its actual
    # saved reports and cache receipts, never call it again in Z.
    for name in [n+'_AUDIT' for n in PREDICTIONS]:
        env=attempt/'pairs'/name/'env'
        paths += [str(f) for f in env.rglob('*') if f.is_file() and f.suffix=='.json'
                  and f.name not in ('access_audit.json','response_registry.json')]
    return pair(attempt,'Z',attach_pins(payload,paths))


def _usage(guardian):
    """Use final wait4 facts; missing or malformed facts are never zero fees."""
    if isinstance(guardian,dict):
        from research.information_service_bridge.guardian import audit_final_records
        records=guardian.get('ledger',[])
        try:
            audit=audit_final_records([r for r in records if r.get('created') is True])
            if ('ledger' in guardian and type(records) is list and guardian.get('processes')==records and
                    audit['complete'] and guardian.get('accounting_complete') is True and
                    guardian.get('all_reaped') is True and guardian.get('worker_cpu')==audit['worker_cpu'] and
                    all(type(guardian.get(k)) in (int,float) and math.isfinite(guardian[k]) and guardian[k]>=0
                        for k in ('guardian_cpu','wall'))):
                return dict(accounting_complete=True,all_reaped=True,worker_cpu=audit['worker_cpu'],
                    controller_cpu=audit['controller_cpu'],guardian_cpu=guardian.get('guardian_cpu'),wall=guardian.get('wall'))
        except BaseException:
            pass
    known=[];seen=set()
    records=guardian.get('ledger',[]) if isinstance(guardian,dict) else []
    for row in records if isinstance(records,list) else []:
        if not isinstance(row,dict):
            continue
        identity=(row.get('pid'),row.get('start_ticks'))
        vals=[row.get('wait4_user_cpu'),row.get('wait4_system_cpu')]
        if identity not in seen and row.get('reaped') and row.get('role') in ('env','sense') and all(
                type(v) in (int,float) and math.isfinite(v) and v>=0 for v in vals):
            known.append(vals[0]+vals[1]);seen.add(identity)
    return dict(accounting_complete=False,all_reaped=False,worker_cpu=None,controller_cpu=None,
                guardian_cpu=None,wall=None,known_worker_CPU_lower_bound=math.fsum(known))


def _worker_lower_bound(rows):
    return math.fsum(r['worker_cpu'] if r['accounting_complete'] else
                     r.get('known_worker_CPU_lower_bound',0.) for r in rows)


def _actual_runtime(attempt, name, g):
    entry=read_json(attempt/'SOURCE_SEAL.json')['entry']
    for row in g['processes']:
        r=read_json(attempt/'pairs'/name/row['role']/'entry_runtime.json')
        require(r['pid']==row['pid'] and r['pgid']==row['pgid'] and
                r['attempt_id']==attempt.name and r['pair_id']==name,'ACTUAL_RUNTIME_IDENTITY')
        require(r['rlimit_cpu']==[60,61] and r['rlimit_as']==[4*1024**3]*2 and r['rlimit_core']==[0,0],
                'ACTUAL_RUNTIME_LIMITS')
        require(len(r['thread_env'])==4 and all(v=='1' for v in r['thread_env'].values()),'ACTUAL_THREAD_LIMITS')
        require(Path(r['executable']).resolve()==Path(sys.executable).resolve(),'ACTUAL_INTERPRETER')
        require(r['entry_file']==entry['path'] and r['entry_sha256']==entry['sha256'],
                'ACTUAL_ENTRY_SOURCE_IDENTITY')


def _claims_from_partial(attempt, matrix, final_worker):
    found={}
    if isinstance(final_worker,dict):
        rows=final_worker.get('preliminary_claims',final_worker.get('claims',[]))
        if isinstance(rows,dict):rows=list(rows.values())
        for row in rows:
            if isinstance(row,dict) and row.get('id')!='C09':found[row['id']]=deepcopy(row)
    if final_worker is None:
        for name in ('G0','G1'):
            source=attempt/'pairs'/name/'env/result.json'
            if not source.is_file():
                continue
            gate=read_json(source)
            rows=gate.get('claims',gate.get('preliminary_claims',[]))
            if isinstance(rows,dict):rows=list(rows.values())
            for row in rows:
                if isinstance(row,dict) and row.get('id')!='C09':found[row['id']]=deepcopy(row)
    return [found.get(s['id'],dict(id=s['id'],status='NOT_EVALUATED',owner=s['owner'],
        evidence_refs=[],checks_completed=[],actual_work_counters={},unknown_or_missing_evidence=['not completed']))
        for s in matrix['claims']]


def run(attempt, expected_sha):
    from .supervision import run_pair, register_run
    from .claims import decide
    started=time.monotonic();parent_start=time.process_time();deadline=started+480.
    attempt=Path(attempt).resolve()
    require(attempt.parent==BASE and attempt.name.startswith('attempt_'),'INDEPENDENT_ATTEMPT')
    require(not (attempt/'execution_started.json').exists(),'NO_RETRY_OR_RESUME')
    require(all(not (attempt/name).exists() for name in (
        'pairs','dispatched_jobs','resource_ledger.json','preZ_resource_ledger.json',
        'result.json','finalization_receipt.json','protection_after.json')),
        'FORMAL_EXECUTION_ARTIFACT_ALREADY_EXISTS')
    require(type(expected_sha) is str and len(expected_sha)==64 and sha_file(attempt/'SEAL.json')==expected_sha,
            'EXTERNAL_EXECUTION_SEAL_MISMATCH')
    seal=verify(attempt);manifest=read_json(attempt/'manifest.json')
    require(manifest['order']==ORDER,'FIXED_ORDER_CHANGED')
    matrix=read_json(PROTOCOL/'ACCEPTANCE_MATRIX.json')
    save_json(attempt/'execution_started.json',dict(started_monotonic=started,absolute_deadline=deadline,
        execution_SEAL_sha256=expected_sha,automatic_retry=False,user_authorized_full_sequence=ORDER))
    register_run(attempt.name,started,deadline)
    rows=[];cpu=0.;totals=dict(WLS_calls=0,start_attempts=0,completed_estimates=0)
    numerical_complete=True;failure=None;final_worker=None;current=None;guardians={}
    def ledger():
        value=dict(jobs=rows,worker_cpu=cpu,totals=dict(totals) if numerical_complete else None,
                   known_worker_CPU_lower_bound=_worker_lower_bound(rows),
                   known_counter_totals_lower_bound=dict(totals),numerical_accounting_complete=numerical_complete,
                   wall=time.monotonic()-started,absolute_deadline=deadline,failed_fees_included=True,
                   unknown_fees_never_zero_filled=True)
        save_json(attempt/'resource_ledger.json',value)
        return value
    def settle(g,name):
        nonlocal cpu,numerical_complete
        use=_usage(g)
        if use['accounting_complete']:
            cpu=cpu+use['worker_cpu'] if cpu is not None else None
        else:
            cpu=None
        row=dict(pair_id=name,**use,accepted=False,raw_passed=g.get('passed') if isinstance(g,dict) else None,
            guardian_result_file=str(attempt/'pairs'/name/'guardian_result.json'))
        counter=attempt/'pairs'/name/'sense/counters.json'
        try:
            counts=read_json(counter) if counter.is_file() else None
        except BaseException as counter_error:
            counts=None
            row['sense_counter_read_error']=str(counter_error)
        row['sense_counters_present']=counts is not None
        for outkey,inkey in [('WLS_calls','estimator_calls'),('start_attempts','start_attempts'),('completed_estimates','completed_estimates')]:
            value=counts.get(inkey) if isinstance(counts,dict) else None
            if type(value) is not int or value<0:
                numerical_complete=False;row[outkey]=None
            else:
                row[outkey]=value;totals[outkey]+=value
        rows.append(row);ledger();return row
    try:
        for spec in manifest['jobs']:
            name=spec['pair_id'];current=name
            require(cpu is not None and cpu<240 and time.monotonic()<deadline-5.,'RESOURCE_BUDGET_BEFORE_DISPATCH')
            if name=='G1':job=_gate1_job(attempt)
            elif name.endswith('_AUDIT'):job=_audit_job(attempt,name)
            elif name=='Z':job=_final_job(attempt,ledger())
            else:job=read_json(attempt/'jobs'/f'{name}.json')
            save_json(attempt/'dispatched_jobs'/f'{name}.json',dict(job=job,sequence=len(rows)))
            g=None
            try:
                g=run_pair(job,attempt/'pairs'/name,deadline,cpu)
            except BaseException as error:
                g=getattr(error,'guardian_result',None)
                if g is None and (attempt/'pairs'/name/'guardian_result.json').is_file():
                    try:g=read_json(attempt/'pairs'/name/'guardian_result.json')
                    except BaseException:pass
                failed_row=settle(g,name)
                try:
                    _actual_runtime(attempt,name,g)
                    failed_row['entry_runtime_validated']=True
                except BaseException as runtime_error:
                    failed_row['entry_runtime_validated']=False
                    failed_row['entry_runtime_error']=str(runtime_error)
                failed_row['supervision_validated']=False
                ledger()
                raise
            guardians[name]=g;row=settle(g,name)
            _actual_runtime(attempt,name,g)
            row['entry_runtime_validated']=True;row['supervision_validated']=True
            require(g['passed'] and row['accounting_complete'] and row['all_reaped'],'JOB_FAILED',name,
                    guardian_failure=g.get('failure'))
            expected=244 if name in PREDICTIONS else 0
            require(row['WLS_calls']==expected and row['completed_estimates']==expected and
                    row['start_attempts']==expected*9,'NUMERICAL_WORK_COUNT',name)
            require(numerical_complete and totals['WLS_calls']<=976 and totals['start_attempts']<=8784,'NUMERICAL_ACCOUNTING')
            result=read_json(attempt/'pairs'/name/'env/result.json')
            require(result.get('passed') is True,'ENV_JOB_FAILED',name)
            if name=='Z':final_worker=result
            row['accepted']=True;ledger()
            print(json.dumps(dict(job=name,accepted=True,worker_CPU=cpu,wall=time.monotonic()-started)),flush=True)
        require([r['pair_id'] for r in rows]==ORDER and all(r['accepted'] for r in rows),'FINAL_COVERAGE')
        require(totals==dict(WLS_calls=976,start_attempts=8784,completed_estimates=976),'FINAL_NUMERICAL_COUNTS')
        require(cpu<240 and time.monotonic()<=deadline,'FINAL_RESOURCE_LIMIT')
    except BaseException as error:
        failure=dict(stage=current,error_type=type(error).__name__,error=str(error),code=getattr(error,'code',None),
            details=getattr(error,'details',None),traceback=traceback.format_exc(),automatic_retry=False)
        ledger()
    protection_error=None
    try:verify(attempt);protected=True
    except BaseException as error:protected=False;protection_error=str(error)
    save_json(attempt/'protection_after.json',dict(passed=protected,error=protection_error,source_count=seal['source_count']))
    claims=_claims_from_partial(attempt,matrix,final_worker)
    accounted_actual=(bool(rows) and all(r['accounting_complete'] and r['all_reaped'] and
        r.get('entry_runtime_validated') is True and r.get('supervision_validated') is True for r in rows)
        and protected and cpu is not None and cpu<240 and numerical_complete and time.monotonic()<=deadline)
    all_final=(len(rows)==11 and all(r['accepted'] and r['accounting_complete'] and r['all_reaped'] for r in rows)
               and failure is None and protected and cpu is not None and cpu<240 and time.monotonic()<=deadline)
    c09=next(r for r in claims if r['id']=='C09')
    c09.update(status='VERIFIED' if accounted_actual else 'FAILED',owner='final_launcher',
        evidence_refs=[str(attempt/'resource_ledger.json'),str(attempt/'protection_after.json'),str(attempt/'finalization_receipt.json')],
        checks_completed=['every actual job final wait4/resources/protection and result persistence'] if accounted_actual else ['actual protection/resource accounting incomplete'],
        actual_work_counters=dict(jobs=len(rows),**totals),unknown_or_missing_evidence=[] if accounted_actual else ['incomplete final accounting'])
    decision=decide(claims,matrix,executed=True,final=True)
    result=dict(decision,passed=bool(all_final and decision.get('correctness_passed')),claims=claims,
        attempt_id=attempt.name,failure=failure,accepted=sum(r['accepted'] for r in rows),jobs=len(rows),
        worker_CPU=cpu,totals=dict(totals) if numerical_complete else None,
        known_worker_CPU_lower_bound=_worker_lower_bound(rows),
        known_counter_totals_lower_bound=dict(totals),numerical_accounting_complete=numerical_complete,
        controller_CPU=ordered_total([r['controller_cpu'] for r in rows]) if all(r['controller_cpu'] is not None for r in rows) else None,
        guardian_CPU_subset_of_launcher=ordered_total([r['guardian_cpu'] for r in rows]) if all(r['guardian_cpu'] is not None for r in rows) else None,
        launcher_CPU_before_result=time.process_time()-parent_start,parent_lifetime_CPU_before_result=time.process_time(),
        guardian_CPU_included_in_launcher=True,wall_before_result=time.monotonic()-started,
        automatic_retry=False,source_seal_sha256=seal['source_seal_sha256'],
        historical_statement='原轮Z失败、原整轮未通过；保存证据独立最终汇总已通过，历史结果不改写',
        finalization_authority='Success requires matching finalization_receipt SHA, result_passed=true and deadline_met=true')
    def downgrade(code,error):
        c09['status']='FAILED';c09['unknown_or_missing_evidence']=[str(error)]
        result.update(decide(claims,matrix,executed=True,final=True))
        result.update(passed=False,failure=dict(code=code,error=str(error),previous_failure=result.get('failure'),automatic_retry=False))
    def persist():
        save_json(attempt/'result.json',result);digest=sha_file(attempt/'result.json');stamp=time.monotonic()
        return dict(result_sha256=digest,result_passed=result['passed'],deadline_met=stamp<=deadline,
            wall_through_result_persistence_and_hash=stamp-started,absolute_deadline=deadline,
            launcher_CPU_through_result_hash=time.process_time()-parent_start,
            parent_lifetime_CPU_through_result_hash=time.process_time(),receipt_excludes_own_last_write=True)
    try:
        receipt=persist()
        if not receipt['deadline_met']:
            downgrade('FINAL_PERSISTENCE_DEADLINE','Absolute deadline reached during protection/result/SHA')
            receipt=persist()
        save_json(attempt/'finalization_receipt.json',receipt)
    except BaseException as error:
        downgrade('FINALIZATION_PERSISTENCE_FAILED',error)
        try:save_json(attempt/'result.json',result)
        except BaseException as write_error:
            result['failure']['failure_write_error']=str(write_error)
            try:(attempt/'result.json').replace(attempt/'result.persistence_unconfirmed.json')
            except BaseException as move_error:result['failure']['invalidation_error']=str(move_error)
        try:save_json(attempt/'finalization_failure.json',result['failure'])
        except BaseException:pass
    print(json.dumps(result,ensure_ascii=False),flush=True)
    return 0 if result['passed'] else 1


def dispatch(args):
    if args.command=='prepare':
        print(json.dumps(prepare(Path(args.attempt)),ensure_ascii=False));return 0
    require(args.command=='run','EXPLICIT_COMMAND_REQUIRED')
    return run(Path(args.attempt),args.expected_seal_sha256)
