"""Executable online admission callbacks and declared job factories.

Importing this module runs no checks. The launcher seals actual canaries/input
files and invokes these callbacks only inside the declared supervised workers.
"""
from contextlib import contextmanager
import copy
import importlib
import json
from pathlib import Path

from .common import CONTRACT_ID, ContractError, AccessDenied, digest
from .runtime import (ResponseContextRegistry, transport_digest, validate_context,
                      serialized_message_size, read_compact_manifest)

PREFIX='research.information_service_online'


def supervision_jobs(attempt_id):
    from research.information_service_bridge.gate_probes import gate_jobs
    return gate_jobs(attempt_id)


def validate_supervision(result,job):
    from research.information_service_bridge.gate_probes import validate_gate
    if result['limits']['total_cpu']!=1200.:
        raise ContractError('Old300 CPU budget cannot certify the online route')
    return validate_gate(result,job)


@contextmanager
def forbid_solver_calls():
    from research.cooperative_sensing import estimator
    counts=dict(estimator_calls=0,optimizer_start_calls=0)
    old_estimate,old_native=estimator.estimate,estimator.least_squares
    def no_estimate(*args,**kwargs):
        counts['estimator_calls']+=1
        raise ContractError('Zero-WLS admission attempted estimator entry')
    def no_native(*args,**kwargs):
        counts['optimizer_start_calls']+=1
        raise ContractError('Zero-WLS admission attempted optimizer entry')
    estimator.estimate,estimator.least_squares=no_estimate,no_native
    try:yield counts
    finally:estimator.estimate,estimator.least_squares=old_estimate,old_native


def _require(condition,message):
    if not condition:raise ContractError(message)


def public_registration(stream='admission-public',first=0,purpose='CANDIDATE_PREDICTION'):
    checkpoint=digest({'synthetic_admission_checkpoint':True,'tick':first})
    actual=purpose=='ACTUAL_EXECUTION';segment=digest({'synthetic_segment':0}) if actual else None
    context=dict(work_instance_id='admission-work',physical_environment_id='admission-synthetic-episode',
        checkpoint_id=checkpoint,request_identity=checkpoint if actual else digest({'request':0}),
        world_identity=None if actual else digest({'world':0}),
        action_identity=segment if actual else digest({'candidate':0}),purpose=purpose,segment_id=segment,
        service_start_tick=first,first_new_fusion_tick=first)
    validate_context(context)
    return dict(stream_id=stream,target_id=0,start_tick=first,allowed_sensor_ids=['U0','U1'],context=context)


def positive_sensing_config():
    return dict(contract_id=CONTRACT_ID,mode='isolation_probe',streams=[public_registration()])


def positive_sensing_body():
    return dict(frame=dict(contract_id='STAGE2A5B-A-MINIMAL-v0.2',stream_id='admission-public',
        frame_id='admission-public:tick0',tick=0,target_id=0,measurement_time=0.,available_time=0.,records=[]),
        allowed_sensor_ids=['U0','U1'],start_tick=0)


def isolation_vectors(attempt_root,role):
    root=Path(__file__).resolve().parents[2];attempt=Path(attempt_root).resolve()
    private=attempt/'private_admission'
    files=[root/'docs/STAGE2A5B_GQ_ONLINE_DESIGN.json',private/'expected.json',
           private/'private_resume.json',private/'audit_sidecar.json',private/'future_turns.json',
           attempt/'public-looking.json']
    relative=str((private/'expected.json').relative_to(root)) if (private/'expected.json').is_relative_to(root) else str(private/'expected.json')
    probes=[dict(action='read',target=str(p)) for p in files]+[dict(action='read',target=relative)]
    modules=[PREFIX+'.private_probe',PREFIX+'.execution']
    if role=='sense':modules += [PREFIX+'.public',PREFIX+'.measurements','pursuit_v2.environment']
    if role=='predictor':modules += [PREFIX+'.reference']
    if role=='reference':modules += [PREFIX+'.evaluator']
    return probes+[dict(action='import',target=m) for m in modules]


def run_access_probes(guard,probes,*,public_checkpoint=None,validate_checkpoint=None,enumerate_candidates=None):
    rows=[];positive=None
    with forbid_solver_calls() as counts:
        for probe in probes:
            if not isinstance(probe,dict) or set(probe)!={'action','target'}:raise ContractError('Exact access probe schema')
            action,target=probe['action'],probe['target']
            exists=(Path(target).is_file() if action=='read' else
                    guard.root.joinpath(*target.split('.')).with_suffix('.py').is_file())
            _require(exists,'Real isolation canary is absent: '+target)
            try:
                if action=='read':
                    with open(target,'rb') as stream:stream.read(1)
                elif action=='import':importlib.import_module(target)
                else:raise ContractError('Unknown access operation')
            except AccessDenied as error:
                rows.append(dict(**probe,passed=True,error_type='AccessDenied',error=str(error)))
            else:raise ContractError('Private capability unexpectedly admitted: '+target)
        if public_checkpoint is not None:
            _require(callable(validate_checkpoint) and callable(enumerate_candidates),'Use actual role public APIs for positive admission')
            before=digest(public_checkpoint);clean=validate_checkpoint(copy.deepcopy(public_checkpoint))
            specs=enumerate_candidates(clean)
            _require(len(specs)==6 and digest(public_checkpoint)==before,'N1 public construction positive failed')
            for private in (lambda:public_checkpoint,dict(public_checkpoint,private_expected={'value':1})):
                try:validate_checkpoint(private)
                except (ContractError,ValueError,TypeError):pass
                else:raise ContractError('Private closure/expected object was accepted as public checkpoint')
            positive=dict(candidate_count=6,public_input_unchanged=True,private_callable_and_expected_rejected=True)
        _require(not any(counts.values()),'Access admission attempted numerical work')
    return dict(passed=True,probes=rows,positive=positive,role=guard.role,real_wls_calls=0,
                observed_solver_sentinel_counts=counts,access_events=copy.deepcopy(guard.events))


def run_schema_gate(checkpoints,validate_checkpoint,enumerate_candidates):
    """ON_IF01 calls actual validators; the launcher supplies pinned provenance."""
    positives=[];negatives=[]
    with forbid_solver_calls() as counts:
        for index,original in enumerate(checkpoints):
            before=digest(original);clean=validate_checkpoint(copy.deepcopy(original))
            specs=enumerate_candidates(clean)
            _require(digest(original)==before,'Schema positive mutated its public input')
            positives.append(dict(fixture_index=index,candidate_count=len(specs)))
            variants=[]
            for field in ('private_future','trusted','unit_only'):
                bad=copy.deepcopy(original);bad[field]=True;variants.append((field,bad))
            bad=copy.deepcopy(original);bad['tick']=True;variants.append(('bool_tick',bad))
            bad=copy.deepcopy(original);bad['current_slots'][0]['slot_key']['robot_id']=True;variants.append(('bool_robot',bad))
            bad=copy.deepcopy(original);bad['current_slots'].append(copy.deepcopy(bad['current_slots'][0]));variants.append(('duplicate_slot',bad))
            bad=copy.deepcopy(original)
            pos=next((i for i,r in enumerate(bad['current_slots']) if r['state']=='UNQUERIED'),None)
            _require(pos is not None,'Declared schema fixture must include an explicit UNQUERIED row')
            bad['current_slots'].pop(pos);variants.append(('missing_UNQUERIED_slot',bad))
            bad=copy.deepcopy(original);bad['sensor_profiles'][0]['observed_tick']+=1;variants.append(('wrong_profile_tick',bad))
            bad=copy.deepcopy(original);bad['current_slots'][0]['state']='INVALID';variants.append(('INVALID_slot',bad))
            for name,bad in variants:
                try:validate_checkpoint(bad)
                except (ContractError,ValueError,TypeError) as error:
                    negatives.append(dict(fixture_index=index,vector=name,error_type=type(error).__name__))
                else:raise ContractError('Schema admitted negative vector '+name)
        _require(not any(counts.values()),'Schema admission invoked estimator')
    return dict(passed=True,gate_id='ON_IF01_SCHEMA_AND_IDENTITY',positives=positives,
                negatives=negatives,real_wls_calls=0,observed_solver_sentinel_counts=counts)


def run_response_context_gate():
    reg=public_registration('IF02-public',20,'ACTUAL_EXECUTION');ctx=reg['context']
    identity=dict(attempt_id='IF02-attempt',pair_id='IF02-pair',sense_request_id='IF02-r0',
                  target_id=0,stream_id=reg['stream_id'],global_tick=20,payload_sha256=transport_digest({'synthetic':True}))
    answer=dict(synthetic=True,value='same',flow_context=ctx,flow_registration=copy.deepcopy(reg))
    def initial():
        r=ResponseContextRegistry(identity['attempt_id'],identity['pair_id']);r.register_stream(reg)
        r.bind_request(identity,ctx);r.accept_response(identity,answer,ctx)
        return r
    with forbid_solver_calls() as counts:
        r=initial();duplicate=r.accept_response(identity,copy.deepcopy(answer),ctx)
        _require(duplicate['duplicate'] and not duplicate['committed'] and len(r.committed)==1,'Identical reply committed twice')
        negatives=[]
        for name in ('wrong_known_candidate','wrong_checkpoint','wrong_tick','wrong_target','old_segment',
                     'forecast_as_actual','conflicting_same_identity','wrong_allowed_context','prior_work_instance'):
            r=initial();before=copy.deepcopy(r.committed);trial_id=copy.deepcopy(identity);trial=copy.deepcopy(answer)
            if name=='wrong_known_candidate':trial['flow_context']['action_identity']=digest({'other_candidate':True})
            elif name=='wrong_checkpoint':trial['flow_context']['checkpoint_id']=digest({'other_checkpoint':True})
            elif name=='wrong_tick':trial_id['global_tick']+=1
            elif name=='wrong_target':trial_id['target_id']+=1
            elif name=='old_segment':trial['flow_context']['segment_id']=digest({'old_segment':True})
            elif name=='forecast_as_actual':trial['flow_context']['purpose']='CANDIDATE_PREDICTION'
            elif name=='wrong_allowed_context':trial['flow_registration']['allowed_sensor_ids']=['U0','U2']
            elif name=='prior_work_instance':trial['flow_context']['work_instance_id']='prior-work'
            else:trial['value']='conflict'
            try:r.accept_response(trial_id,trial,ctx)
            except ContractError:
                _require(r.failed and r.committed==before,'Invalid reply changed prior commits')
                negatives.append(dict(vector=name,prior_committed_state_retained=True))
            else:raise ContractError('Response context negative was accepted: '+name)
    return dict(passed=True,gate_id='ON_IF02_RESPONSE_CONTEXT',duplicate=duplicate,negatives=negatives,
                real_wls_calls=0,observed_solver_sentinel_counts=counts)


def run_compact_manifest_gate(guard,positive_reference,negative_references,nested_probes=None):
    """Each negative reference identifies real presealed fixture bytes."""
    before=set(guard.read_files)
    rows=guard.admit_manifest(positive_reference)
    _require(len(rows)>0,'Positive exact manifest cannot be empty')
    denied=[]
    for vector,ref in negative_references.items():
        try:guard.admit_manifest(ref)
        except (AccessDenied,ContractError) as error:
            denied.append(dict(vector=vector,error_type=type(error).__name__))
        else:raise ContractError('Compact manifest negative accepted: '+vector)
    for target in ([] if nested_probes is None else nested_probes):
        if not isinstance(target,str) or not Path(target).is_file():
            raise ContractError('Nested negative must name a real existing unregistered file')
        try:
            with open(target,'rb') as stream:stream.read(1)
        except AccessDenied as error:
            denied.append(dict(vector='unregistered_nested_file',target=target,error_type='AccessDenied'))
        else:raise ContractError('Registered parent manifest incorrectly granted a nested file')
    try:serialized_message_size('x'*2097151)
    except ContractError:oversize=True
    else:raise ContractError('Oversized body was not rejected before dispatch')
    _require(serialized_message_size('x'*2097150)==2097152,'Exact2MiB framing changed')
    return dict(passed=True,gate_id='ON_IF03_COMPACT_AUDIT_INPUTS',positive_entries=len(rows),
                negative_vectors=denied,oversize_rejected_before_dispatch=oversize,real_wls_calls=0,
                previous_exact_file_count=len(before),new_exact_file_count=len(guard.read_files))


def run_callback_gate(gate_id,callback):
    """Wrap actual history/action APIs supplied by model_worker, never fake them."""
    _require(gate_id in ('ON_IF05_LIVE_HISTORY_AND_RESUME','ON_IF07_NO_PREDICTION_STATE_WRITEBACK'),
             'Unknown actual API callback gate')
    with forbid_solver_calls() as counts:
        result=callback()
        _require(isinstance(result,dict) and result.get('passed') is True,'Actual API admission callback failed')
        _require(not any(counts.values()),'Live history/action gate invoked WLS')
    return dict(result,gate_id=gate_id,real_wls_calls=0,observed_solver_sentinel_counts=counts)


def run_resource_gate(resource_contract,validate_arithmetic,validate_contract=None):
    contract=resource_contract()
    _require(contract['total_cpu']==1200. and contract['total_wall']==2400. and
             contract['pair_cpu']==60. and contract['pair_wall']==120.,'Frozen online resource defaults differ')
    copied=validate_arithmetic(1199.9,.2)
    _require(copied['tripped'] and copied['limit']==1200.,'Cumulative plus live CPU did not trip1200')
    if validate_contract is None:raise ContractError('Actual supervisor resource validator required')
    validate_contract(contract)
    try:validate_contract(dict(contract,total_cpu=300.))
    except ContractError:legacy_rejected=True
    else:raise ContractError('Legacy300 resource configuration was admitted')
    return dict(passed=True,gate_id='ON_IF06_RESOURCE_AND_OWNERSHIP',contract=contract,legacy300_rejected=legacy_rejected,
                copied_arithmetic=copied,real_wls_calls=0,
                note='Unique wait4 ownership is additionally reverified by24 actual supervisor probes.')


def isolation_job_specs(attempt_id,attempt_root,*,public_checkpoint_file=None):
    common=dict(attempt_id=str(attempt_id),controller_start=dict(steps=[]))
    jobs=[dict(common,pair_id='ISOLATION_SENSE',env_start=dict(kind='admission_sensor_isolation',
        probes=isolation_vectors(attempt_root,'sense'),positive_body=positive_sensing_body()),
        sense_start=positive_sensing_config(),expected=dict(accepted=True,real_wls_calls=0))]
    if public_checkpoint_file is not None:
        for role in ('predictor','reference'):
            jobs.append(dict(common,pair_id='ISOLATION_'+role.upper(),env_start=dict(kind='admission_role_isolation',
                protected_role=role,public_checkpoint_file=str(public_checkpoint_file),
                read_files=[str(public_checkpoint_file)],probes=isolation_vectors(attempt_root,role)),
                sense_start=dict(contract_id=CONTRACT_ID,mode='isolation_probe',streams=[]),
                expected=dict(accepted=True,real_wls_calls=0)))
    for role,transport in [('sense','sense'),('predictor','env')]:
        for channel in ('argv','env'):
            job=dict(common,pair_id=f'I03_{role.upper()}_{channel.upper()}',predeclared_isolation_probe=True,
                env_start=dict(kind='admission_startup_no_work',protected_role='predictor'),
                sense_start=dict(contract_id=CONTRACT_ID,mode='isolation_probe',streams=[]),
                expected=dict(guardian_success=False,protected_role=role,real_wls_calls=0,
                              must_observe_explicit_startup_rejection=True))
            job[transport+('_argv_extra' if channel=='argv' else '_env_extra')]=(
                ['--private-scenario','FORBIDDEN'] if channel=='argv' else {'GQ_PRIVATE_SCENARIO':'FORBIDDEN'})
            jobs.append(job)
    return jobs


def interface_failure_jobs(attempt_id,*,public_checkpoint_file=None):
    registration=public_registration('IF04-public',20,'ACTUAL_EXECUTION')
    jobs=[]
    for fault in ('no_response','worker_exit','numeric_contract_violation'):
        jobs.append(dict(attempt_id=str(attempt_id),pair_id='ON_IF04_'+fault,
            env_start=dict(kind='admission_interface_failure',fault=fault,
                public_checkpoint_file=None if public_checkpoint_file is None else str(public_checkpoint_file),
                read_files=[] if public_checkpoint_file is None else [str(public_checkpoint_file)],
                last_committed_tick=20,new_actions_prepared_not_committed=True,
                recorded_unique_sampling_attempts=1,stream=registration),
            sense_start=dict(contract_id=CONTRACT_ID,mode='interface_probe',streams=[registration],interface_fault=dict(type=fault)),
            controller_start=dict(steps=[]),expected=dict(guardian_success=False,real_wls_calls=0,
                last_valid_state_retained=True,retained_unique_sampling_attempts=1,
                required_sensor_exit_code=7 if fault=='worker_exit' else None,
                required_error_message='INJECTED_ONLINE_NUMERIC_CONTRACT_ERROR' if fault=='numeric_contract_violation' else None)))
    return jobs
