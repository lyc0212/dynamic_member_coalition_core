"""Serial declared work orchestration; all scientific work is guardian owned."""
from copy import deepcopy
from pathlib import Path
import json
import time
import traceback
from .common import (CONTRACT_ID, STAGE_CONTRACT, ContractError, digest,
                     typed_digest, read_json, save_json, sha_file, safe_label)
from .source_admission import ROOT, check_pin, source_census
from .preparation import ENTRY, prepare, verify_seal, pin


def pair_job(attempt,pair,payload,streams=None,mode='science'):
    return dict(attempt_id=attempt.name,pair_id=pair,env_start=payload,
        sense_start=dict(contract_id=CONTRACT_ID,mode=mode,streams=streams or []),controller_start=dict(steps=[]))


def readpaths(payload,paths):
    payload['read_files']=sorted({str(Path(p).resolve()) for p in paths})
    if len(payload['read_files'])>256:
        raise ContractError('More than256 exact data files; no directory fallback')
    return payload


def substitute(value,attempt):
    if isinstance(value,str):return value.replace('{attempt_id}',attempt.name).replace('{attempt}',str(attempt))
    if isinstance(value,list):return [substitute(v,attempt) for v in value]
    if isinstance(value,dict):return {k:substitute(v,attempt) for k,v in value.items()}
    return value


def forecast_job(attempt,batch,snapshot,binding,actual=None):
    """Materialize only needed public fields, never forward whole design/batches."""
    request_pin=(snapshot['public_inputs']['evaluation_request'] if actual is None else actual['artifacts']['evaluation_request'])
    binding_pin=(snapshot['public_inputs']['public_binding'] if actual is None else actual['artifacts']['public_binding'])
    request_path=check_pin(request_pin);binding_path=check_pin(binding_pin)
    request=read_json(request_path);cp=request['checkpoint'];works=[];streams=[]
    physical=attempt.name+(':B_C_PUBLIC:' if actual is None else ':D:')+snapshot['episode']
    catalog=None if actual is None else read_json(check_pin(actual['artifacts']['candidate_catalog']))
    for w in batch['work_items']:
        i=w['candidate_index'];candidate=deepcopy(snapshot['candidates'][i]['descriptor'] if catalog is None else catalog[i]['candidate'])
        if candidate['candidate_id']!=w['candidate_id']:
            raise ContractError('New D catalog has left the frozen accepted domain')
        work=substitute(w['work_instance_id_template'],attempt)
        reg=substitute(w['registration_template'],attempt)
        reg['context']['physical_environment_id']=physical
        works.append(dict(candidate=candidate,work_id=work));streams.append(reg)
    method=batch['method']
    payload=dict(kind='predict' if method=='R' else 'predict_shared',method=method,
        physical_environment_id=physical,request_file=str(request_path),binding_file=str(binding_path),
        binding_sha256=binding_pin['sha256'],work_items=works,streams=streams,
        runtime_binding_id=binding['runtime_binding_id'])
    if method=='S':
        scope=dict(message_kind='motion_cache_scope',contract_id=STAGE_CONTRACT,
            runtime_binding_id=binding['runtime_binding_id'],scope_kind='MAIN_RUNTIME',unit_fixture_id=None,
            attempt_id=attempt.name,decision_id=snapshot['snapshot_id'],batch_id=batch['batch_id'],
            cache_instance_id=batch['batch_id']+':cache',evaluation_request_id=request['evaluation_request_id'],
            world_id=digest({k:request[k] for k in ('forecast_contract_id','current_endpoint_contract_id','evaluation_request_id')}),
            motion_geometry_contract_version='gq_shared_motion_prefix_v1',config_digest=digest(cp['config']),
            start_tick=cp['tick'],prediction_end_tick=request['prediction_end_tick'],
            robots=cp['config']['robots'],task_count=cp['config']['task_count'])
        scope['full_scope_id']=typed_digest(scope);payload['cache_scope']=scope
    return pair_job(attempt,batch['batch_id'],readpaths(payload,[request_path,binding_path]),streams)


def materialize_offline_jobs(attempt,binding):
    batches=read_json(attempt/'inputs/BATCHES.json');snapshots={s['snapshot_id']:s for s in batches['B_snapshots']}
    jobs=[]
    for snapshot in batches['B_snapshots']:
        for method in snapshot['method_passes']:
            for batch in method['prediction_batches']:
                jobs.append(dict(phase='B',job=forecast_job(attempt,batch,snapshot,binding),
                                 WLS_limit=batch['real_wls_upper_bound']))
    for group in batches['C_transformations']:
        for batch in group['prediction_batches']:
            jobs.append(dict(phase='C',job=forecast_job(attempt,batch,snapshots[group['snapshot_ref']],binding),
                             WLS_limit=batch['real_wls_upper_bound']))
    if len(jobs)!=82 or sum(len(j['job']['env_start']['work_items']) for j in jobs)!=288:
        raise ContractError('Frozen B/C batch/candidate count mismatch')
    return jobs


def run(attempt):
    """No automatic resume. A failed attempt is permanently retained."""
    from research.information_service_online.supervision import run_pair
    from research.information_service_online.admission import validate_supervision
    from research.information_service_online.runner import _accept_negative
    started=time.monotonic();launcher_start=time.process_time();deadline=started+2400.
    if (attempt/'execution_started.json').exists():raise FileExistsError('Attempt already started')
    seal=verify_seal(attempt)
    save_json(attempt/'execution_started.json',dict(monotonic=started,deadline=deadline,seal_I_sha256=sha_file(attempt/'SEAL_I.json')))
    cpu=0.;jobs=[];actual_registry=[];B_results={};episode_indices=[];totals=dict(real_wls=0,starts=0)
    batches=read_json(attempt/'inputs/BATCHES.json');binding=read_json(attempt/'runtime_cache_binding.json')
    snapshots={s['snapshot_id']:s for s in batches['B_snapshots']}
    oracle_index={r['batch_id']:r['reference'] for r in read_json(attempt/'inputs/DESIGN.json')['batch_oracles']}
    offline={d['job']['pair_id']:d for d in read_json(attempt/'offline_jobs.json')}

    def final_accounting():
        """Called after the final source census on both success and failure."""
        parent_lifetime=time.process_time();wall=time.monotonic()-started
        controller=sum(r['controller_cpu'] for r in jobs)
        guardian=sum(r['guardian_cpu'] for r in jobs)
        return dict(scientific_cpu=cpu,wall=wall,
            trusted_launcher_cpu=parent_lifetime-launcher_start,
            parent_cpu_before_run=launcher_start,parent_process_lifetime_cpu_at_record=parent_lifetime,
            controller_cpu=controller,guardian_cpu=guardian,
            nonoverlapping_process_cpu=parent_lifetime+cpu+controller,
            accounting_scope='wall and launcher window include post-run source census; guardian/census are subsets of launcher CPU, not additional process CPU')

    def persist_result(result):
        write_started=time.monotonic()
        save_json(attempt/'result.json',result)
        # The result cannot contain the end time of its own write. Preserve a
        # separate receipt instead of treating that persistence time as zero.
        save_json(attempt/'finalization_receipt.json',dict(result_sha256=sha_file(attempt/'result.json'),
            result_status=result['status'],wall_through_result_persistence=time.monotonic()-started,
            result_write_seconds=time.monotonic()-write_started,
            launcher_cpu_through_result_persistence=time.process_time()-launcher_start,
            parent_process_lifetime_cpu_through_result_persistence=time.process_time(),
            receipt_write_not_in_its_own_timestamps=True))

    def execute(job,phase,wls_limit=0):
        nonlocal cpu
        from .runtime import serialized_message_size,validate_exact_inputs
        if cpu>=1200. or time.monotonic()>=deadline-5:
            raise ContractError('Original cumulative resource budget exhausted')
        payload=job.get('env_start',{});kind=payload.get('kind')
        if kind=='predict_shared':
            scope=payload['cache_scope']
            if (payload['runtime_binding_id']!=binding['runtime_binding_id'] or
                    scope['runtime_binding_id']!=binding['runtime_binding_id'] or
                    scope['attempt_id']!=attempt.name or scope['batch_id']!=job['pair_id'] or
                    scope['scope_kind']!='MAIN_RUNTIME'):
                raise ContractError('Shared job does not bind the externally sealed runtime/batch')
        role=payload.get('protected_role') or ('R' if kind=='predict' else 'S' if kind=='predict_shared' else
            'selector' if kind=='select' else 'execution' if kind in ('initialize','execute') else
            'regression' if kind in ('regression','new_unit') else 'short_cache' if kind=='shared_short' else
            'admission' if kind in ('shared_gate','short','interface_checks','admission_interface_failure') else 'audit')
        if not job.get('synthetic'):
            validate_exact_inputs(role,payload.get('read_files',[]),operation='prediction' if kind in ('predict','predict_shared') else None)
        payload['source_pins']={p:pin(p) for p in payload.get('read_files',[])}
        for name in ('env_start','sense_start','controller_start'):
            serialized_message_size(dict(type='START',payload=job.get(name,{})))
        out=attempt/'pairs'/safe_label(job['pair_id'])
        jobfile=attempt/'dispatched_jobs'/f"{safe_label(job['pair_id'])}.json"
        save_json(jobfile,dict(phase=phase,job=job,WLS_limit=wls_limit))
        r=run_pair(job,out,ENTRY,deadline,cpu);cpu+=r['worker_cpu']
        row=dict(pair_id=job['pair_id'],phase=phase,worker_cpu=r['worker_cpu'],controller_cpu=r['controller_cpu'],
            guardian_cpu=r['guardian_cpu'],wall=r['wall'],raw_passed=r['passed'],guardian_result=str(out/'guardian_result.json'))
        jobs.append(row)
        try:
            counts=read_json(out/'sense/counters.json') if (out/'sense/counters.json').exists() else {}
            used=counts.get('estimator_calls',0);starts=counts.get('start_attempts',0)
            if phase=='regression' and (out/'env/estimate_counts.json').exists():
                c=read_json(out/'env/estimate_counts.json');used+=c['real_estimates'];starts+=c['native_start_attempts']
            totals['real_wls']+=used;totals['starts']+=starts
            row.update(real_wls=used,starts=starts,sense_counter_file_present=(out/'sense/counters.json').exists())
            gate=validate_supervision(r,job) if phase=='supervision' else _accept_negative(r,job,out)
            if not gate['passed']:raise ContractError('Declared runtime gate failed')
            if phase=='regression' and not (out/'env/estimate_counts.json').exists():
                raise ContractError('Missing final regression numerical accounting')
            if used>wls_limit or starts>9*wls_limit or totals['real_wls']>25270 or totals['starts']>227430:
                raise ContractError('Predeclared numerical call ceiling exceeded')
            row.update(accepted=True,real_wls=used,starts=starts)
            result=read_json(out/'env/result.json') if (out/'env/result.json').exists() else {}
            save_json(out/'acceptance.json',dict(passed=True,gate=gate))
            print(json.dumps(dict(pair_id=job['pair_id'],accepted=True,cpu=round(cpu,3),wall=round(time.monotonic()-started,3))),flush=True)
            return result,str(out/'env/result.json')
        except BaseException as error:
            row.update(accepted=False,error=str(error));raise
        finally:
            save_json(attempt/'resource_ledger.json',dict(jobs=jobs,worker_cpu=cpu,totals=totals,wall=time.monotonic()-started))

    def forecast(group,snapshot,actual=None):
        files=[];producers=[];cache_batches=[]
        for batch in group['prediction_batches']:
            job=(offline[batch['batch_id']]['job'] if actual is None else forecast_job(attempt,batch,snapshot,binding,actual))
            answer,resultfile=execute(job,'prediction',batch['real_wls_upper_bound'])
            part=[r['result_file'] for r in answer['items']];files+=part
            base=Path(resultfile).parent
            producers.append(dict(pair_id=job['pair_id'],job_file=str(attempt/'dispatched_jobs'/f"{safe_label(job['pair_id'])}.json"),
                guardian_result_file=str(base.parent/'guardian_result.json'),response_registry_file=str(base/'response_registry.json'),
                env_result_file=resultfile,files=[pin(p) for p in part]))
            if batch['method']=='S':
                ordinal=int(batch['batch_id'].rsplit('_B',1)[1])
                if batch['batch_id'].startswith('C_REGROUP_'):
                    oracle_name=f"{snapshot['episode']}_k{snapshot['tick']:03d}_REBATCH_{ordinal:02d}"
                else:
                    oracle_name=snapshot['original_batches'][ordinal-1]['source_pair_id']
                    if batch['batch_id'].startswith('C_REVERSE_'):oracle_name+='_REVERSE'
                oracle=check_pin(oracle_index[oracle_name])
                cache_batches.append(dict(producer_job_file=str(attempt/'dispatched_jobs'/f"{safe_label(job['pair_id'])}.json"),cache_diagnostics_file=str(base/'cache_diagnostics.json'),cache_trace_file=str(base/'cache_trace.json'),
                    cache_instrumentation_file=str(base/'cache_instrumentation.json'),oracle_file=str(oracle),
                    candidate_ownership_file=str(base/'candidate_ownership.json'),candidate_result_files=part,
                    batch_id=batch['batch_id']))
        return dict(candidate_result_files=files,producer_records=producers,cache_batches=cache_batches,
                    registrations=[reg for batch in group['prediction_batches'] for reg in substitute(
                        [w['registration_template'] for w in batch['work_items']],attempt)])

    def select(group,snapshot,table,actual=None):
        arts=snapshot['public_inputs'] if actual is None else actual['artifacts']
        req=str(check_pin(arts['evaluation_request']));bind=str(check_pin(arts['public_binding']))
        physical=attempt.name+(':B_C_PUBLIC:' if actual is None else ':D:')+snapshot['episode']
        work=group['selection']['work_id'];actual_work=work+':ACTUAL'
        payload=readpaths(dict(kind='select',request_file=req,binding_file=bind,binding_sha256=arts['public_binding']['sha256'],
            candidate_result_files=table['candidate_result_files'],actual_work_identity=actual_work,
            physical_environment_id=physical,action_request_id=work+':request'),[req,bind,*table['candidate_result_files']])
        answer,path=execute(pair_job(attempt,work,payload),'select')
        table['selection_producer']=dict(pair_id=work,job_file=str(attempt/'dispatched_jobs'/f'{safe_label(work)}.json'),
            guardian_result_file=str(Path(path).parent.parent/'guardian_result.json'),
            response_registry_file=str(Path(path).parent/'response_registry.json'),env_result_file=path,
            files=[pin(answer['scientific_file'])])
        table['selection_registrations']=read_json(answer['stream_file'])
        table.update(selection_file=answer['scientific_file'],selection_result_file=path,
            actual_work_identity=actual_work,selection_answer=answer)
        return table

    def audit_selection(work,snapshot,table,actual=None):
        arts=snapshot['public_inputs'] if actual is None else actual['artifacts']
        req=str(check_pin(arts['evaluation_request']));bind=str(check_pin(arts['public_binding']))
        refs=[str(check_pin(c['historical_independent_witness_auditor_only'])) for c in snapshot['candidates']]
        payload=readpaths(dict(kind='audit_decision',request_file=req,binding_file=bind,binding_sha256=arts['public_binding']['sha256'],
            candidate_result_files=table['candidate_result_files'],reference_result_files=refs,
            reference_required=True,selection_file=table['selection_result_file']),[req,bind,table['selection_result_file'],*table['candidate_result_files'],*refs])
        answer,path=execute(pair_job(attempt,work,payload),'audit')
        table['selection_audit_file']=path;return answer

    def compare(work,snapshot,left,right,*,actual=None,decision_audit_job=None):
        arts=snapshot['public_inputs'] if actual is None else actual['artifacts']
        req=str(check_pin(arts['evaluation_request']));bind=str(check_pin(arts['public_binding']))
        payload=dict(kind='shared_compare',comparison_file=str(attempt/'inputs/COMPARISON.json'),request_file=req,
            binding_file=bind,binding_sha256=arts['public_binding']['sha256'],left=left,right=right,
            decision_audit_job=decision_audit_job,snapshot_id=snapshot['snapshot_id'])
        paths=[req,bind,attempt/'inputs/COMPARISON.json']
        for table in (left,right):
            paths += [*table['candidate_result_files'],table['selection_file']]
            for p in table['producer_records']+[table['selection_producer']]:
                paths += [p[k] for k in ('job_file','guardian_result_file','response_registry_file','env_result_file')]
                producer_job=read_json(p['job_file'])['job']['env_start']
                paths += [producer_job[k] for k in ('request_file','binding_file')]
            for cache in table['cache_batches']:paths += [cache['cache_diagnostics_file'],cache['cache_trace_file'],cache['cache_instrumentation_file'],cache['oracle_file'],cache['candidate_ownership_file']]
        if decision_audit_job is not None:paths.append(decision_audit_job['selection_file'])
        return execute(pair_job(attempt,work,readpaths(payload,paths)),'audit')

    try:
        runtime_census=source_census();save_json(attempt/'runtime_source_census.json',runtime_census)
        for declared in read_json(attempt/'pre_main_jobs.json'):
            job=deepcopy(declared['job'])
            if job['env_start'].get('gate_id')=='SG01_SOURCE_CENSUS':
                job['env_start']['census_file']=str(attempt/'runtime_source_census.json')
                job['env_start']['census_digest']=digest(runtime_census)
                job['env_start']['read_files'].append(str(attempt/'runtime_source_census.json'))
            execute(job,declared['phase'],declared.get('WLS_limit',0))
        for snapshot in batches['B_snapshots']:
            payload=dict(kind='shared_source',source_mode='original',snapshot=snapshot,
                registry_path=str(check_pin(batches['source_pins']['actual_checkpoint_registry'])),
                registry_sha=batches['source_pins']['actual_checkpoint_registry']['sha256'])
            paths=[payload['registry_path'],*[check_pin(p) for p in snapshot['public_inputs'].values()],
                   check_pin(snapshot['source_registration']['registered_execution_result_auditor_only'])]
            execute(pair_job(attempt,snapshot['source_admission']['work_id'],readpaths(payload,paths)),'source')
            results={}
            for method in snapshot['method_order']:
                group=next(g for g in snapshot['method_passes'] if g['method']==method)
                table=select(group,snapshot,forecast(group,snapshot))
                audit_selection(group['selection_audit']['work_id'],snapshot,table)
                results[method]=table
            compare(snapshot['paired_comparison']['work_id'],snapshot,results['R'],results['S'])
            B_results[snapshot['snapshot_id']]=results
            save_json(attempt/'B_index.json',B_results)
        for group in batches['C_transformations']:
            snapshot=snapshots[group['snapshot_ref']]
            table=select(group,snapshot,forecast(group,snapshot))
            compare(group['comparison']['work_id'],snapshot,B_results[snapshot['snapshot_id']]['S'],table)
        # Dynamic execution is deliberately encapsulated in a separate source
        # module. It can only dispatch through this same monotone budget closure.
        from .dynamic_run import run_dynamic
        episode_indices=run_dynamic(attempt,batches,binding,B_results,execute,forecast,select,compare)
        from .final_audit import final_payload
        payload=final_payload(attempt,jobs,B_results,episode_indices,totals)
        execute(pair_job(attempt,batches['final_audit']['work_id'],payload),'audit')
        verify_seal(attempt);save_json(attempt/'protection_after.json',source_census())
        result=dict(passed=True,status='DETERMINISTIC_EQUIVALENCE_ACCEPTED',totals=totals,job_count=len(jobs),
            episode_index_files=episode_indices,no_stable_speedup_claim=True,**final_accounting())
        if cpu>1200. or result['wall']>2400.:raise ContractError('Final resource cap exceeded')
        persist_result(result);return result
    except BaseException as error:
        result=dict(passed=False,status='STOPPED_WITH_RETAINED_EVIDENCE',error_type=type(error).__name__,error=str(error),
            traceback=traceback.format_exc(),totals=totals,job_count=len(jobs),automatic_retry=False)
        try:save_json(attempt/'protection_after.json',source_census())
        except BaseException as e:result['protection_error']=str(e)
        result.update(final_accounting())
        persist_result(result);raise


def dispatch(args):
    attempt=Path(args.attempt).resolve()
    if not attempt.is_relative_to(ROOT/'evidence/stage2a5b_gq_shared_full'):
        raise ContractError('Dedicated shared-full evidence directory required')
    if args.command=='prepare':value=prepare(attempt)
    elif args.command=='run':value=run(attempt)
    else:
        from .reporting import report
        value=report(attempt)
    print(json.dumps(value,ensure_ascii=False),flush=True);return 0
