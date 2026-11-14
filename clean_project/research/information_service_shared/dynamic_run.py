"""Fresh controlled-source autonomous D loop, using the one parent budget."""
from copy import deepcopy
from pathlib import Path
from .common import ContractError,digest,read_json,save_json,sha_file
from .source_admission import ROOT,check_pin,validate_new_receipt
from .preparation import pin


def run_dynamic(attempt,batches,binding,B_results,execute,forecast,select,compare):
    from .runner import pair_job,readpaths
    snapshots={s['snapshot_id']:s for s in batches['B_snapshots']}
    source_catalog=attempt/'inputs/execution_step_sources.json'
    source_meta=read_json(attempt/'SEAL_I.json')['files']['inputs/execution_step_sources.json']
    check_pin(dict(path=str(source_catalog),**source_meta))
    old_steps={(r['episode_id'],r['start_tick']):r for r in read_json(source_catalog)['entries']}
    if len(old_steps)!=30:raise ContractError('Missing frozen execution-step source catalogue')
    registry=[];indices=[]
    old_design=ROOT/'docs/STAGE2A5B_GQ_ONLINE_DESIGN.json'
    for episode in batches['D_episodes']:
        eid=episode['episode_id'];physical=attempt.name+':D:'+eid
        private=check_pin(episode['private_initial_input_executor_only'])
        payload=readpaths(dict(kind='initialize',episode_id=eid,physical_environment_id=physical,
            private_input_file=str(private)),[private])
        answer,resultfile=execute(pair_job(attempt,episode['initialization']['work_id'],payload),'initialize')
        previous=None;index=None
        for cut_number,declared_cut in enumerate(episode['cuts']):
            artifacts=answer['artifacts'];producer=Path(resultfile).parent.resolve()
            if any(Path(p).is_symlink() or Path(p).resolve().parent!=producer for p in artifacts.values()):
                raise ContractError('New D artifacts did not come from the registered actual worker')
            checkpoint=read_json(artifacts['public_checkpoint']);private_state=read_json(artifacts['private_snapshot'])
            public_binding=read_json(artifacts['public_binding'])
            if (answer['physical_environment_id']!=physical or private_state['physical_environment_id']!=physical or
                    private_state['source_identity']!=digest(read_json(private)) or private_state['failed'] or
                    private_state['inflight'] is not None or private_state['checkpoint']!=checkpoint or
                    public_binding['public_checkpoint']!=checkpoint):
                raise ContractError('New D state/source/commit mismatch')
            if checkpoint['tick']!=declared_cut['tick']:
                raise ContractError('New actual cut differs from the declared cadence')
            action_link=None
            if previous is not None:
                request_id=read_json(selected['action_file'])['operation']['request_id']
                if request_id not in private_state['successful_requests']:
                    raise ContractError('Actual successful request cache omitted submitted action')
                action_link=digest(private_state['successful_requests'][request_id])
            receipt=dict(source_kind='NEW_COMMITTED_EXECUTION',physical_environment_id=physical,
                producer_role='execution',producer_passed=answer.get('passed') is True,committed=True,
                selector_input_origin='NEW_CURRENT_COMPLETE_TABLE',episode_id=eid,tick=checkpoint['tick'],
                checkpoint_id=checkpoint['checkpoint_id'],previous_checkpoint_id=checkpoint['previous_checkpoint_id'],
                previous_receipt_id=None if previous is None else digest(previous),successful_action_cache_link=action_link,
                producer_result_pin=pin(resultfile),producer_guardian_pin=pin(producer.parent/'guardian_result.json'),
                producer_job_pin=pin(attempt/'dispatched_jobs'/f'{producer.parent.name}.json'),
                artifacts={k:pin(v) for k,v in artifacts.items()},seal_I_sha256=sha_file(attempt/'SEAL_I.json'))
            validate_new_receipt(receipt,attempt_id=attempt.name,episode_id=eid,previous=previous)
            # Registration is pending until the independently supervised source
            # audit accepts both provenance and the complete old public cut.
            pending=attempt/'pending_sources'/f'{eid}_k{checkpoint["tick"]:03d}.json';save_json(pending,receipt)
            old_pin=declared_cut['r2_public_expected_auditor_only']['checkpoint']
            source_payload=dict(kind='shared_source',source_mode='fresh',receipt=receipt,receipt_file=str(pending),previous=previous,
                attempt_id=attempt.name,episode_id=eid,old_checkpoint_pin=old_pin,expected_public_checkpoint_file=str(check_pin(old_pin)),private_input_pin=pin(private),
                previous_receipt_file=None if previous is None else str(attempt/'pending_sources'/f'{eid}_k{previous["tick"]:03d}.json'))
            paths=[private,pending,resultfile,producer.parent/'guardian_result.json',receipt['producer_job_pin']['path'],check_pin(old_pin),*artifacts.values()]
            if previous is not None:
                paths.append(source_payload['previous_receipt_file'])
                producer_job=read_json(receipt['producer_job_pin']['path'])['job']['env_start']
                paths += [producer_job['action_file'],producer_job['private_snapshot_file'],answer['step_result_file']]
                old=deepcopy(old_steps[(eid,previous['tick'])])
                for fixed in old['old_source_pins'].values():check_pin(fixed)
                check_pin(dict(path=old['old_registry_file'],sha256=old['old_registry_sha']))
                check_pin(dict(path=old['old_episode_index_file'],sha256=old['old_episode_index_sha']))
                new_side=dict(step_result_file=answer['step_result_file'],
                    producer_job_file=receipt['producer_job_pin']['path'],
                    guardian_result_file=receipt['producer_guardian_pin']['path'],
                    response_registry_file=str(producer/'response_registry.json'),env_result_file=resultfile,
                    action_file=producer_job['action_file'],
                    previous_public_checkpoint_file=previous['artifacts']['public_checkpoint']['path'],
                    previous_public_binding_file=previous['artifacts']['public_binding']['path'],
                    previous_private_snapshot_file=previous['artifacts']['private_snapshot']['path'],
                    current_private_snapshot_file=artifacts['private_snapshot'],
                    current_public_checkpoint_file=artifacts['public_checkpoint'],
                    current_public_binding_file=artifacts['public_binding'],private_input_file=str(private))
                source_payload['execution_comparison']=dict(old=old['old'],new=new_side,
                    old_source_pins=old['old_source_pins'],old_registry_file=old['old_registry_file'],
                    old_registry_sha=old['old_registry_sha'],old_episode_index_file=old['old_episode_index_file'],
                    old_episode_index_sha=old['old_episode_index_sha'])
                paths += [*old['old'].values(),*new_side.values(),old['old_registry_file'],old['old_episode_index_file']]
            if previous is not None:paths += [p['path'] for p in previous['artifacts'].values()]
            _,source_audit_file=execute(pair_job(attempt,declared_cut['source_audit']['work_id'],readpaths(source_payload,paths)),'source')
            registry.append(receipt);save_json(attempt/'actual_checkpoint_registry.json',registry)
            save_json(attempt/'checkpoint_seals'/f'{eid}_k{checkpoint["tick"]:03d}.json',dict(receipt=receipt,source_audit=pin(source_audit_file)))
            if index is None:
                index=dict(episode_id=eid,private_input_file=str(private),design_file=str(old_design),
                    initial_artifacts=artifacts,decisions=[],final_artifacts=None)
            index['final_artifacts']=artifacts
            indexfile=attempt/'episode_indices'/f'{eid}.json';save_json(indexfile,index)
            if checkpoint['tick']==episode['episode_end_tick']:
                break
            decision=episode['decisions'][cut_number];snapshot=snapshots[f'{eid}:k{checkpoint["tick"]:03d}']
            catalog=read_json(artifacts['candidate_catalog']);group=deepcopy(decision)
            # New descriptors and segment contexts originate in the new actual
            # producer. Only work order/limits are reused from the frozen plan.
            for batch in group['prediction_batches']:
                batch['method']='S';batch['work_items']=[]
                for i in batch['candidate_indices_in_execution_order']:
                    c=catalog[i];work=attempt.name+':'+batch['batch_id']+f':C{i:04d}'
                    reg=deepcopy(c['PRIMARY']['registration']);reg['stream_id']=work+f":T{c['candidate']['key']['target']}:first{reg['start_tick']}"
                    reg['context']['work_instance_id']=work;reg['context']['physical_environment_id']=physical
                    batch['work_items'].append(dict(candidate_index=i,candidate_id=c['candidate']['candidate_id'],
                        work_instance_id_template=work,registration_template=reg))
            table=select(group,snapshot,forecast(group,snapshot,receipt),receipt)
            selected=table['selection_answer']
            # Same zero-WLS job performs exact finite-table audit and strict
            # comparison with the newly recomputed B-R table before execution.
            audit_job=dict(kind='audit_decision',request_file=artifacts['evaluation_request'],binding_file=artifacts['public_binding'],
                binding_sha256=receipt['artifacts']['public_binding']['sha256'],candidate_result_files=table['candidate_result_files'],
                reference_result_files=[],reference_required=False,selection_file=table['selection_result_file'])
            _,auditfile=compare(group['selection_audit']['work_id'],snapshot,B_results[snapshot['snapshot_id']]['R'],table,
                actual=receipt,decision_audit_job=audit_job)
            streams=read_json(selected['stream_file']);actual=group['actual_execution']
            payload=readpaths(dict(kind='execute',episode_id=eid,physical_environment_id=physical,private_input_file=str(private),
                private_snapshot_file=artifacts['private_snapshot'],private_snapshot_sha256=receipt['artifacts']['private_snapshot']['sha256'],
                action_file=selected['action_file'],work_identity=table['actual_work_identity'],streams=streams),
                [private,artifacts['private_snapshot'],selected['action_file']])
            next_answer,next_result=execute(pair_job(attempt,actual['work_id'],payload,streams),'actual',actual['real_wls_upper_bound'])
            index['decisions'].append(dict(tick=checkpoint['tick'],artifacts=artifacts,
                binding_sha256=receipt['artifacts']['public_binding']['sha256'],candidate_result_files=table['candidate_result_files'],
                reference_result_files=[],selection_file=table['selection_result_file'],selection_audit_file=auditfile,
                action_file=selected['action_file'],step_result_file=next_answer['step_result_file'],
                execution_result_file=next_result,artifacts_after=next_answer['artifacts']))
            save_json(indexfile,index);previous=receipt;answer,resultfile=next_answer,next_result
        exact=[indexfile,private,old_design,*index['initial_artifacts'].values(),*index['final_artifacts'].values()]
        for d in index['decisions']:
            exact += [d[k] for k in ('selection_file','selection_audit_file','action_file','step_result_file','execution_result_file')]
            exact += list(d['artifacts'].values())+list(d['artifacts_after'].values())
        payload=readpaths(dict(kind='audit_episode',episode_index_file=str(indexfile)),exact)
        _,apath=execute(pair_job(attempt,episode['episode_audit']['work_id'],payload),'audit')
        index['episode_audit_file']=apath;save_json(indexfile,index);indices.append(str(indexfile))
    paired=[p for p in indices if Path(p).stem in ('N4A','N4B')];paths=list(paired)
    for p in paired:
        for d in read_json(p)['decisions']:
            if d['tick'] in (0,20):paths += [d['artifacts']['evaluation_request'],d['selection_file'],*d['candidate_result_files']]
    payload=readpaths(dict(kind='audit_pair',episode_index_files=paired),paths)
    execute(pair_job(attempt,batches['D_n4_pair_audit']['work_id'],payload),'audit')
    if len(registry)!=35:raise ContractError('Expected35 independently admitted actual cuts')
    return indices
