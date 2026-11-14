"""Supervised role dispatcher; private dependencies are loaded after guard install."""
from copy import deepcopy
from pathlib import Path
import os
import resource
import sys
import traceback
from research.information_service_bridge.wire import WireClient
from .common import CONTRACT_ID,ContractError,digest,read_json,save_json,sha_file,safe_label
from .runtime import install_role_guard,validate_worker_startup,ResponseContextRegistry,transport_digest


def submit_action(env,envelope,*,work_identity,on_commit=None):
    """Actual RPC seam: exact input shape first, successful replay before time checks."""
    from . import public
    envelope=public.validate_schema(envelope,'ActionRequest')
    payload,operation=envelope['payload'],envelope['operation']
    if operation['physical_environment_id']!=env.physical_environment_id:
        raise ContractError('Foreign action environment')
    known=operation['request_id'] in env.journal.successful or env.journal.inflight is not None
    if not known:
        public.validate_action_request(envelope,env.observe_public())
    return env.step(payload['assignment'],payload['checkpoint_id'],payload['expected_start_tick'],
        operation['request_id'],work_identity=work_identity,on_commit=on_commit)


def main(args):
    args=validate_worker_startup(args,transport_role='env')
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    wire=WireClient(args.fd);guard=None;last_committed=None;sequence=0
    registry=ResponseContextRegistry(args.attempt_id,args.pair_id);stream_context={};records=[];env=None
    try:
        wire.send(dict(type='READY',role='env',contract_id=CONTRACT_ID))
        start=wire.recv(timeout=12.)
        if start.get('type')!='START':raise ContractError('Expected START')
        job=start['payload'];kind=job['kind']
        role=job.get('protected_role') or ('execution' if kind in ('initialize','execute') else
             'predictor' if kind=='predict' else 'reference' if kind=='reference' else
             'selector' if kind=='select' else 'regression' if kind in ('regression','new_unit') else 'audit')
        guard=install_role_guard(role,out,args.fd,read_files=job.get('read_files',[]))
        guard.check_loaded_modules()
        save_json(out/'runtime.json',dict(role=role,pid=os.getpid(),pgid=os.getpgrp(),python=sys.version,executable=sys.executable,
          rlimit_cpu=list(resource.getrlimit(resource.RLIMIT_CPU)),rlimit_as=list(resource.getrlimit(resource.RLIMIT_AS)),
          thread_env={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}))
        def register(reg):
            registry.register_stream(reg);stream_context[reg['stream_id']]=deepcopy(reg['context'])
        for reg in job.get('streams',[]):register(reg)
        def exchange(body,message_type,context=None):
            nonlocal sequence
            sequence+=1
            frame=body.get('frame',{});ident=dict(attempt_id=args.attempt_id,pair_id=args.pair_id,
                sense_request_id=f'sense-{sequence}',target_id=frame.get('target_id',0),
                stream_id=frame.get('stream_id','isolation'),global_tick=frame.get('tick',sequence),payload_sha256=transport_digest(body))
            if context is not None:registry.bind_request(ident,context)
            record=dict(identity=ident,body=deepcopy(body),message_type=message_type,status='pending')
            save_json(out/'ipc'/f'{sequence:06d}.json',record)
            wire.send(dict(type='AUTHORIZE',identity=ident));reply=wire.recv(timeout=12.)
            if reply.get('type')!='AUTHORIZED' or reply.get('identity')!=ident:raise ContractError('Invalid authorization')
            wire.send(dict(type=message_type,identity=ident,**body));reply=wire.recv(timeout=12.)
            if reply.get('type')!=('SENSE_RESULT' if message_type=='SENSE' else 'ISOLATION_RESULT') or reply.get('identity')!=ident:
                raise ContractError('Wrong sensing reply identity/type')
            result=reply['result']
            if message_type=='SENSE':
                from research.information_service.public_quality import prepare_frame
                prepared=prepare_frame(body['frame'],body['allowed_sensor_ids'])
                if any(result.get(k)!=frame[k] for k in ('frame_id','stream_id','target_id','tick')):
                    raise ContractError('Wrong public endpoint identity')
                if (result.get('payload_sha256')!=prepared['payload_sha256'] or
                     result.get('quality',{}).get('payload_sha256')!=prepared['payload_sha256'] or
                     result.get('quality',{}).get('status') not in ('PASS','FAIL','UNKNOWN')):
                    raise ContractError('Invalid numerical/public result contract')
            if context is not None:registry.accept_response(ident,result,context)
            record.update(status='validated',result=result);save_json(out/'ipc'/f'{sequence:06d}.json',record)
            records.append(record);wire.send(dict(type='SENSE_ACK',identity=ident))
            return result
        def sense(frame,allowed_sensor_ids,start_tick,context=None):
            expected=stream_context.get(frame['stream_id'])
            if expected is None or context is not None and context!=expected:raise ContractError('Unregistered or mismatched flow context')
            return exchange(dict(frame=frame,allowed_sensor_ids=list(allowed_sensor_ids),start_tick=start_tick),'SENSE',expected)
        def commit(frame):
            nonlocal last_committed
            last_committed=deepcopy(frame);save_json(out/'last_committed_state.json',last_committed)
        def authority_for(path,expected_sha):
            from . import public
            if sha_file(path)!=expected_sha:raise ContractError('External actual binding bytes changed')
            return public.HistoryAuthority.from_public_binding(read_json(path))
        def publish_actual(env):
            from . import public
            checkpoint=env.observe_public();binding=env.public_binding()
            save_json(out/'private_snapshot.json',env.private_snapshot())
            save_json(out/'public_checkpoint.json',checkpoint);save_json(out/'public_binding.json',binding)
            artifacts=dict(private_snapshot=str(out/'private_snapshot.json'),public_checkpoint=str(out/'public_checkpoint.json'),
                           public_binding=str(out/'public_binding.json'))
            if checkpoint['phase']=='DECISION_READY':
                # This producer owns actual committed state. Downstream readers
                # still require the external launcher's pinned public binding.
                auth=public.HistoryAuthority.from_public_binding(binding)
                request=public.request_from_checkpoint(checkpoint,auth);manifest=public.build_manifest(request,auth)
                save_json(out/'evaluation_request.json',request)
                catalog=[]
                for c in manifest['candidates']:
                    row=dict(candidate=c)
                    for operation,purpose in [('PRIMARY','CANDIDATE_PREDICTION'),('INDEPENDENT_REFERENCE','INDEPENDENT_REFERENCE')]:
                        work=f"{job['episode_id']}:k{checkpoint['tick']:03d}:{operation}:C{c['index']:04d}"
                        meta=public.prediction_metadata(request,c,work,auth,
                            physical_environment_id=job['physical_environment_id'],purpose=purpose)
                        row[operation]=dict(work_id=work,registration=meta['registration'])
                    catalog.append(row)
                save_json(out/'candidate_catalog.json',catalog)
                artifacts.update(evaluation_request=str(out/'evaluation_request.json'),candidate_catalog=str(out/'candidate_catalog.json'))
            return dict(passed=True,artifacts=artifacts,checkpoint_id=checkpoint['checkpoint_id'],tick=checkpoint['tick'],
                        phase=checkpoint['phase'],metrics=env.metrics(),physical_environment_id=job['physical_environment_id'])
        if kind=='admission_sensor_isolation':
            checked=[]
            for probe in job['probes']:
                r=exchange(probe,'ISOLATION_PROBE')
                if not r.get('passed') or r.get('error_type')!='AccessDenied':raise ContractError('Private probe admitted')
                checked.append(r)
            positive=exchange(job['positive_body'],'SENSE')
            if positive['quality']['status']!='UNKNOWN' or not positive['skipped']:raise ContractError('Empty public control failed')
            result=dict(passed=True,probes=checked,positive=positive,real_wls_calls=0)
        elif kind=='admission_role_isolation':
            from . import public,admission
            cp=read_json(job['public_checkpoint_file'])
            result=admission.run_access_probes(guard,job['probes'],public_checkpoint=cp,
                validate_checkpoint=lambda x:public.validate_checkpoint(x,unit_only=True),
                enumerate_candidates=lambda x:public.enumerate_candidates(x,unit_only=True))
        elif kind=='admission_startup_no_work':
            raise ContractError('Startup negative probe unexpectedly entered worker')
        elif kind=='admission_interface_failure':
            from .admission import public_registration
            reg=job['stream']
            if reg['stream_id'] not in stream_context:register(reg)
            commit(dict(tick=20,synthetic_pending_fixture=True,physical_steps=0,
                unique_sampling_attempts_retained=1,new_actions_prepared_not_committed=True))
            save_json(out/'sampling_attempts.json',[dict(fixture=True,sequence=1,committed_action=False)])
            f=dict(contract_id='STAGE2A5B-A-MINIMAL-v0.2',stream_id=reg['stream_id'],frame_id='IF04:tick20',
                   tick=20,target_id=0,measurement_time=1.,available_time=1.,records=[])
            sense(f,reg['allowed_sensor_ids'],reg['start_tick'])
            raise ContractError('Injected failure did not stop the evaluator')
        elif kind=='interface_checks':
            from .interface_checks import run_interface_checks
            result=run_interface_checks(job,out,guard)
        elif kind=='short':
            from .short_checks import run_checks
            result=run_checks(job['short_file'],job['check_ids'],out,sense,fixture_root=job.get('fixture_root'),manifest_reference=job.get('short_manifest_reference'))
        elif kind in ('regression','new_unit'):
            from research.information_service_evaluation.regression_runner import run_regression
            result=run_regression(job,out)
        elif kind in ('initialize','execute'):
            from .execution import OnlineEnvironment
            case=read_json(job['private_input_file'])
            restored=None
            if kind=='execute':
                if sha_file(job['private_snapshot_file'])!=job['private_snapshot_sha256']:raise ContractError('Actual resume bytes changed')
                restored=read_json(job['private_snapshot_file'])
            env=OnlineEnvironment(case,sense,job['physical_environment_id'],restored=restored,work_identity=job.get('work_identity',args.pair_id))
            env.sampler.on_change=lambda snapshot:save_json(out/'actual_sampling_journal.json',snapshot)
            save_json(out/'actual_sampling_journal.json',env.sampler.snapshot())
            if kind=='initialize':
                env.initialize();commit(env.observe_public())
            else:
                envelope=read_json(job['action_file'])
                step=submit_action(env,envelope,work_identity=job['work_identity'],on_commit=commit)
                if step.get('status')!='COMMITTED':raise ContractError('Registered actual action was not committed')
                save_json(out/'step_result.json',step)
            result=publish_actual(env)
            if kind=='execute':result['step_result_file']=str(out/'step_result.json')
        elif kind in ('predict','reference'):
            from . import public
            auth=authority_for(job['binding_file'],job['binding_sha256'])
            req=read_json(job['request_file']);public.validate_request(req,auth)
            if kind=='predict':
                from .evaluator import evaluate_candidate
            else:
                from .reference import execute_joint
            items=[]
            for w in job['work_items']:
                candidate=public.validate_candidate(req,w['candidate'],auth)
                work_out=out/'work'/safe_label(w['work_id']);work_out.mkdir(parents=True,exist_ok=False)
                if kind=='predict':value=evaluate_candidate(req,candidate,sense,history_authority=auth,work_identity=w['work_id'],on_commit=commit,physical_environment_id=job['physical_environment_id'])
                else:
                    actions=[dict(target=None,role='none') for _ in req['checkpoint']['positions']]
                    for i,r in zip(candidate['key']['robots'],candidate['key']['roles']):actions[i]=dict(target=candidate['key']['target'],role=r)
                    value=execute_joint(req,actions,sense,history_authority=auth,work_identity=w['work_id'],on_commit=commit)
                save_json(work_out/'result.json',value)
                items.append(dict(work_id=w['work_id'],candidate_id=candidate['candidate_id'],result_file=str(work_out/'result.json')))
                save_json(out/'completed_items.json',items)
            result=dict(passed=True,items=items)
        elif kind=='select':
            from .selection import select
            from . import public
            auth=authority_for(job['binding_file'],job['binding_sha256'])
            request=read_json(job['request_file'])
            results=[read_json(p) for p in job['candidate_result_files']]
            result=select(request,results,authority=auth,work_identity=job['actual_work_identity'],
                          physical_environment_id=job['physical_environment_id'])
            envelope=dict(message_kind='action_request',operation=dict(physical_environment_id=job['physical_environment_id'],
                request_id=job['action_request_id']),payload=dict(contract_id='gq_online_action_transaction_v1',checkpoint_id=result['checkpoint_id'],
                    expected_start_tick=request['checkpoint']['tick'],assignment=result['actions']))
            public.validate_action_request(envelope,request['checkpoint'])
            save_json(out/'action_request.json',envelope)
            registrations=[m['registration'] for m in result['action_metadata']['flows']]
            save_json(out/'actual_stream_registrations.json',registrations)
            result.update(action_file=str(out/'action_request.json'),stream_file=str(out/'actual_stream_registrations.json'))
        elif kind=='audit_decision':
            from .acceptance import audit_decision
            result=audit_decision(job,out)
        elif kind=='audit_episode':
            from .acceptance import audit_episode
            result=audit_episode(job,out)
        elif kind=='audit_pair':
            from .acceptance import audit_pair
            result=audit_pair(job,out)
        else:raise ContractError('Unknown registered worker operation '+kind)
        if not isinstance(result,dict) or result.get('passed') is False:raise ContractError('Worker checks did not pass')
        guard.check_loaded_modules();save_json(out/'result.json',result)
        save_json(out/'response_registry.json',registry.snapshot());save_json(out/'access_audit.json',dict(role=role,events=guard.events))
        wire.send(dict(type='ENV_DONE',result=dict(passed=True)))
        stop=wire.recv(timeout=12.)
        if stop.get('type')!='STOP' or stop.get('attempt_id')!=args.attempt_id or stop.get('pair_id')!=args.pair_id:
            raise ContractError('Expected matching STOP')
        wire.send(dict(type='STOP_ACK',role='env'));return 0
    except BaseException as error:
        if env is not None:
            save_json(out/'failed_private_snapshot.json',env.private_snapshot())
            save_json(out/'actual_sampling_journal.json',env.sampler.snapshot())
        save_json(out/'failure.json',dict(error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),
            last_committed_state=last_committed,sensing_requests=sequence,registry=registry.snapshot()))
        if guard is not None:save_json(out/'access_audit.json',dict(events=guard.events))
        try:wire.send(dict(type='WORKER_ERROR',error=f'{type(error).__name__}: {error}'))
        except BaseException:pass
        raise
    finally:wire.close()
