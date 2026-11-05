"""Shared-route admission jobs and gate bodies; import performs no checks.

prepare_jobs is metadata-only. Gate bodies run only after runtime sealing in the
registered guardian workers. Synthetic provenance checks never grant real state.
"""
from copy import deepcopy
import importlib
import json
import os
from pathlib import Path

from .common import CONTRACT_ID, STAGE_CONTRACT, ContractError, AccessDenied, digest, typed_digest, read_json, save_json, sha_file

ROOT = Path(__file__).resolve().parents[2]
OLD = 'research.information_service_online'
NEW = 'research.information_service_shared'


def _pin(path):
    path=Path(path).resolve()
    return dict(path=str(path),sha256=sha_file(path),size_bytes=path.stat().st_size)


def _paths(payload, paths):
    payload['read_files']=sorted({str(Path(p).resolve()) for p in paths})
    if len(payload['read_files'])>256: raise ContractError('Admission metadata exceeds exact-file limit')
    return payload


def _pair(attempt, identifier, payload, streams=(), mode='science'):
    return dict(attempt_id=attempt.name,pair_id=identifier,env_start=payload,
        sense_start=dict(contract_id=CONTRACT_ID,mode=mode,streams=list(streams)),controller_start=dict(steps=[]))


def _require(condition, message):
    if not condition: raise ContractError(message)


def _refuse(label, function, rows):
    try: function()
    except (ContractError,AccessDenied) as error:
        rows.append(dict(vector=label,refused=True,error_type=type(error).__name__,message=str(error)))
    else:
        rows.append(dict(vector=label,refused=False))
        raise ContractError('Admission negative was accepted: '+label)


def _runtime_source_binding(binding, closure, source_seal):
    """Actual metadata validator, not a callback returning a claimed pass."""
    from .contracts import validate_definition
    from .runtime import ROLE_MODULES
    from .source_admission import check_pin
    clean=validate_definition(binding,'RuntimeCacheBinding')
    _require(clean['runtime_binding_id']==typed_digest({k:v for k,v in clean.items() if k!='runtime_binding_id'}),
             'Runtime cache binding identity differs')
    _require(set(closure)==set(ROLE_MODULES),'Runtime role membership is incomplete')
    for role,allowed in ROLE_MODULES.items():
        names=[row['module'] for row in closure[role]]
        _require(len(names)==len(set(names)) and set(names)==set(allowed),'Role import closure differs: '+role)
    manifest=read_json(check_pin(source_seal['source_manifest']))['files']
    for row in clean['source_files']:
        path=check_pin(row)
        _require(str(path.relative_to(ROOT)) in manifest and manifest[str(path.relative_to(ROOT))]==row['sha256'],
                 'New source omitted from actual source seal')
    check_pin(clean['runtime_fingerprint_artifact'])
    return dict(passed=True,new_source_files=len(clean['source_files']),roles=len(closure))


def _source_gate(job,out):
    from .source_admission import validate_census_receipt,check_pin
    receipt=read_json(job['census_file']);expected=job['census_digest'];rows=[]
    positive=validate_census_receipt(receipt,expected)
    binding=read_json(job['runtime_binding_file']);closure=read_json(job['role_closures_file'])
    source_seal=read_json(job['source_seal_file'])
    _require(sha_file(job['source_seal_file'])==binding['source_seal_sha256'],'Unpinned new source seal')
    positive_runtime=_runtime_source_binding(binding,closure,source_seal)
    bad=deepcopy(receipt);bad['source_manifests'][0]['files'].pop();bad['copied_self_hash']=digest(bad)
    _refuse('SG01_N01',lambda:validate_census_receipt(bad,expected),rows)
    bad=deepcopy(receipt);bad['source_manifests'][0]['files'][0]['sha256']='0'*64
    _refuse('SG01_N02',lambda:validate_census_receipt(bad,expected),rows)
    bad=deepcopy(receipt);bad['source_manifests'][0]['files'][-1]=deepcopy(bad['source_manifests'][0]['files'][0])
    _refuse('SG01_N03',lambda:validate_census_receipt(bad,expected),rows)
    missing=deepcopy(binding);missing['source_files'][0]['path']=str(out/'never_created_entrypoint.py')
    missing['runtime_binding_id']=typed_digest({k:v for k,v in missing.items() if k!='runtime_binding_id'})
    _refuse('SG01_N04',lambda:_runtime_source_binding(missing,closure,source_seal),rows)
    incomplete=deepcopy(closure);incomplete['S']=[r for r in incomplete['S'] if r['module']!=NEW+'.motion_cache']
    _refuse('SG01_N05',lambda:_runtime_source_binding(binding,incomplete,source_seal),rows)
    return dict(passed=True,gate_id=job['gate_id'],positive=positive,runtime_source=positive_runtime,
        negatives=rows,worker_rehashed_original_267_files=False,
        scope='Externally pinned launcher census and real new source/import closure, not transferred old gate results')


def _binding_gate(job,out):
    from .source_admission import admit_original,check_pin
    from research.information_service_online import public
    snapshot=deepcopy(job['snapshot']);registry=read_json(job['registry_path']);rows=[]
    def admit(value):
        return admit_original(value,registry,job['registry_sha'],registry_path=job['registry_path'])
    positive=admit(snapshot)
    req=read_json(check_pin(snapshot['public_inputs']['evaluation_request']))
    auth=public.HistoryAuthority.from_public_binding(read_json(check_pin(snapshot['public_inputs']['public_binding'])))
    # Mutate an actual nonzero-history source, reseal caller-owned public bytes,
    # and verify that the real registered path/pin still cannot be replaced.
    history=deepcopy(job['history_probe_snapshot'])
    cp=read_json(check_pin(history['public_inputs']['public_checkpoint']))
    active=next(h for h in cp['task_histories'] if h['active_segment_id'] is not None)
    segment=next(s for s in active['segments'] if s['segment_id']==active['active_segment_id'])
    segment['latest_clock']['intervals']+=1
    segment['segment_history_digest']=digest({k:v for k,v in segment.items() if k!='segment_history_digest'})
    active['history_digest']=digest({k:v for k,v in active.items() if k!='history_digest'})
    cp['checkpoint_id']=digest({k:v for k,v in cp.items() if k!='checkpoint_id'})
    forged=out/'forged_progress_checkpoint.json';save_json(forged,cp)
    history['public_inputs']['public_checkpoint']=_pin(forged)
    _refuse('SG02_N01',lambda:admit(history),rows)
    for field in ('trusted','verified'):
        bad=deepcopy(req);bad[field]=True
        _refuse('SG02_N02:'+field,lambda bad=bad:public.validate_request(bad,auth),rows)
    bad=deepcopy(snapshot);bad['public_inputs']['public_binding']['sha256']='0'*64
    _refuse('SG02_N03',lambda:admit(bad),rows)
    bad=deepcopy(snapshot);bad['public_inputs']['public_binding']=deepcopy(job['history_probe_snapshot']['public_inputs']['public_binding'])
    _refuse('SG02_N04',lambda:admit(bad),rows)
    foreign=out/'same_public_unregistered.json';save_json(foreign,req)
    bad=deepcopy(snapshot);bad['public_inputs']['evaluation_request']=_pin(foreign)
    _refuse('SG02_N05',lambda:admit(bad),rows)
    # An initial construction may even have identical science bytes; copying it
    # does not create the externally registered producer location.
    unit=out/'unit_only_initial_checkpoint.json';save_json(unit,req['checkpoint'])
    bad=deepcopy(snapshot);bad['public_inputs']['public_checkpoint']=_pin(unit)
    _refuse('SG02_N06',lambda:admit(bad),rows)
    return dict(passed=True,gate_id=job['gate_id'],positive=positive,negatives=rows,
                unit_fixture_promoted_to_real_history=False)


def _new_source_gate(job,out):
    from .source_admission import validate_new_receipt
    data=read_json(job['unit_receipts_file']);previous=data['previous'];current=data['current'];rows=[]
    before=digest(data)
    validate_new_receipt(previous,attempt_id=job['attempt_id'],episode_id='N1',unit_only=True)
    positive=validate_new_receipt(current,attempt_id=job['attempt_id'],episode_id='N1',previous=previous,unit_only=True)
    _require(positive.get('unit_only') is True and positive.get('grants_main_authority') is False,'Unit receipt acquired actual authority')
    def validate(value,unit=True):
        return validate_new_receipt(value,attempt_id=job['attempt_id'],episode_id='N1',previous=previous,unit_only=unit)
    bad=deepcopy(current);bad.update(source_kind='R2_ACTUAL_REGISTERED',physical_environment_id='old-r2:N1')
    _refuse('SG03_N01',lambda:validate(bad),rows)
    bad=deepcopy(current);bad['producer_role']='predictor';bad['purpose']='CANDIDATE_PREDICTION'
    _refuse('SG03_N02',lambda:validate(bad),rows)
    bad=deepcopy(current);bad['committed']=False
    _refuse('SG03_N03',lambda:validate(bad),rows)
    bad=deepcopy(current);bad['previous_checkpoint_id']=None;bad['successful_action_cache_link']=None
    _refuse('SG03_N04',lambda:validate(bad),rows)
    bad=deepcopy(current);bad['selector_input_origin']='OLD_R2_WINNER'
    _refuse('SG03_N05',lambda:validate(bad),rows)
    _refuse('SG03_N06',lambda:validate(current,False),rows)
    _require(digest(data)==before,'Source validator changed fixture input')
    return dict(passed=True,gate_id=job['gate_id'],positive=positive,negatives=rows,
                fixture_kind='UNIT_ONLY_STRUCTURAL_RECEIPTS',real_physical_history_created=False,
                D_actual_source_happy_path_not_claimed=True)


def _role_inputs_gate(job,out,guard):
    from .runtime import validate_exact_inputs,serialized_message_size
    _require(guard.role=='selector','SG04 must run under the actual selector guard')
    rows=[];actual=[]
    permitted=job['policy_paths_256'];_require(len(permitted)==256,'Frozen positive needs exactly256 paths')
    p1=validate_exact_inputs('selector',permitted)
    entries=guard.admit_manifest(job['positive_manifest'])
    _require(len(entries)==255,'Positive manifest membership changed')
    request=read_json(job['toy_request_file']);table=read_json(job['toy_table_file'])
    _require(table['scope']=='EXPLICIT_UNIT_ONLY_TOY_TABLE' and table['request_identity']==request['evaluation_request_id']
             and len(table['rows'])==6,'Selector did not read the declared complete toy input')
    actual.append(dict(vector='SG04_P04',public_request_read=True,toy_table_rows=len(table['rows']),selection_run=False))
    public_files=job['original_public_files']
    p2=[validate_exact_inputs(role,public_files,operation='prediction') for role in ('R','S')]
    p3=validate_exact_inputs('audit',job['audit_policy_files'],operation='saved_output_audit')
    _refuse('SG04_N01',lambda:validate_exact_inputs('selector',permitted+[job['extra_existing_file']]),rows)
    _refuse('SG04_N02',lambda:serialized_message_size('x'*2097151),rows)
    _require(serialized_message_size('x'*2097150)==2097152,'Exact2MiB control changed')
    def denied_read(path):
        _require(Path(path).is_file(),'Missing real denial fixture, not a pass: '+str(path))
        try:
            with open(path,'rb') as stream:stream.read(1)
        except AccessDenied as error: return dict(path=str(path),error_type='AccessDenied',message=str(error))
        raise ContractError('Selector opened a forbidden existing file: '+str(path))
    actual.append(dict(vector='SG04_N03',observed=denied_read(job['nested_private_file'])))
    for path in job['path_alias_policy_negatives']:
        _refuse('SG04_N04',lambda path=path:validate_exact_inputs('selector',[path]),rows)
    _refuse('SG04_N05:cache_data',lambda:validate_exact_inputs('R',[job['cache_canary']],operation='prediction'),rows)
    _refuse('SG04_N05:source_module',lambda:validate_exact_inputs('R',[],source_modules=[NEW+'.motion_cache']),rows)
    for path in job['private_policy_files']:
        _refuse('SG04_N06',lambda path=path:validate_exact_inputs('S',[path],operation='prediction'),rows)
    _refuse('SG04_N07',lambda:validate_exact_inputs('reference',[job['toy_table_file']],operation='prediction'),rows)
    for path in job['actual_selector_denial_paths']:
        actual.append(dict(vector='SG04_N08',observed=denied_read(path)))
    for module in ('research.cooperative_sensing.estimator',OLD+'.execution',NEW+'.evaluator'):
        _refuse('SG04_N09',lambda module=module:validate_exact_inputs('audit',[],source_modules=[module],operation='saved_output_audit'),rows)
    _refuse('SG04_N10',lambda:validate_exact_inputs('selector',[str(ROOT/'research')]),rows)
    return dict(passed=True,gate_id=job['gate_id'],positives=dict(P01=p1,P02=p2,P03=p3),
        policy_negatives=rows,actual_selector_reads=actual,actual_guard_role=guard.role,
        audit_policy_is_not_actual_auditor_read=True,access_events=deepcopy(guard.events))


def run_gate(job,out,guard):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    from research.information_service_online.admission import forbid_solver_calls
    with forbid_solver_calls() as counts:
        gate=job['gate_id']
        if gate=='SG01_SOURCE_CENSUS': result=_source_gate(job,out)
        elif gate=='SG02_PUBLIC_BINDING': result=_binding_gate(job,out)
        elif gate=='SG03_D_NEW_SOURCE': result=_new_source_gate(job,out)
        elif gate=='SG04_EXACT_ROLE_INPUTS': result=_role_inputs_gate(job,out,guard)
        elif gate=='SG05_COMPARATOR_SELFTEST':
            from .comparison_checks import run_checks
            result=run_checks(job['comparison_file'],out,expected_sha256=job['comparison_sha256'])
        else: raise ContractError('Unknown shared admission gate')
        _require(not any(counts.values()),'Zero-WLS gate entered numerical solver')
        result.update(observed_solver_sentinel_counts=dict(counts),real_wls_calls=0,local_optimizer_starts=0)
        save_json(out/'gate_observed.json',result)
        return result


def run_interface_response_gate(job,out,guard):
    """Reuse frozen probe vectors while constructing the actual new registry.

    This is a single isolated gate worker. The old module binding is restored in
    finally; no old source file is changed and no fake registry is substituted.
    """
    from research.information_service_online import admission as old_admission
    from .runtime import ResponseContextRegistry
    names=job.get('gate_ids',job.get('gate_id'))
    if isinstance(names,str): names=[names]
    _require(names==['ON_IF02_RESPONSE_CONTEXT'],'Only IF02 belongs to this new-registry seam')
    actual_instances=[];previous=old_admission.ResponseContextRegistry
    def construct_actual(*args,**kwargs):
        registry=ResponseContextRegistry(*args,**kwargs)
        _require(type(registry) is ResponseContextRegistry,'Registry factory did not return production class')
        actual_instances.append(dict(class_module=type(registry).__module__,class_name=type(registry).__name__))
        return registry
    try:
        old_admission.ResponseContextRegistry=construct_actual
        result=old_admission.run_response_context_gate()
    finally:
        old_admission.ResponseContextRegistry=previous
    _require(len(actual_instances)==10,'Not all original response-context vectors reached new registry')
    result['actual_registry_constructions']=actual_instances
    result['new_production_registry_reached']=all(r['class_module']==NEW+'.runtime' for r in actual_instances)
    _require(result['new_production_registry_reached'],'Old registry cannot certify new runtime')
    save_json(Path(out)/'ON_IF02_RESPONSE_CONTEXT.json',result)
    return dict(passed=True,gates=[result],real_wls_calls=0,local_optimizer_starts=0)


def _selector_fixtures(attempt,snapshot):
    """Only metadata/files, including actual existing denial paths; no policy run."""
    folder=attempt/'selector_fixture';folder.mkdir(parents=True,exist_ok=False)
    public=snapshot['public_inputs']
    def source(pin):
        p=Path(pin['path']);return p if p.is_absolute() else ROOT/p
    request=read_json(source(public['evaluation_request']))
    catalog=read_json(source(public['candidate_catalog']))
    req=folder/'evaluation_request.json';table=folder/'candidate_table.json'
    save_json(req,request)
    save_json(table,dict(scope='EXPLICIT_UNIT_ONLY_TOY_TABLE',request_identity=request['evaluation_request_id'],
        rows=[dict(candidate_id=row['candidate']['candidate_id'],key=row['candidate']['key'],v=0.) for row in catalog]))
    paths=[req,table]
    for i in range(253):
        p=folder/f'F{i:04d}.json';save_json(p,dict(fixture_member=i,scope='SG04_EXACT_INPUT_BOUNDARY'))
        paths.append(p)
    extra=folder/'extra_257.json';save_json(extra,dict(extra_limit_probe=True))
    nested=folder/'unlisted_nested.json';save_json(nested,dict(nested_canary='DENY'))
    # One permitted data file names an unregistered child; no recursive authority.
    save_json(paths[-1],dict(fixture_member=252,nested=str(nested),scope='SG04_EXACT_INPUT_BOUNDARY'))
    manifest=folder/'manifest.json'
    entries=[dict(file_id=f'F{i:04d}',relative_path=p.name,sha256=sha_file(p)) for i,p in enumerate(paths)]
    save_json(manifest,dict(contract_id='gq_online_exact_input_manifest_v1',entries=entries))
    old_winner=ROOT/'evidence/stage2a5b_gq_online/attempt_0779f047b65149369a4e06dc5959b4fb/pairs/N1_k000_SELECT/env/action_request.json'
    if not old_winner.is_file(): raise ContractError('Declared historical winner denial canary absent')
    link=folder/'old_action_alias.json';link.symlink_to(old_winner)
    foreign=attempt/'private_admission/foreign_selected_action.json';save_json(foreign,dict(foreign_method='R',action='AUDIT_ONLY_DENY'))
    cache=folder/'cache_diagnostics.json';save_json(cache,dict(cache_canary='DENY_TO_R'))
    relative=os.path.relpath(old_winner,ROOT)
    traversal=str(folder/'..'/'selector_fixture'/'old_action_alias.json')
    return dict(toy_request_file=str(req),toy_table_file=str(table),
        policy_paths_256=[str(p) for p in paths]+[str(manifest)],
        positive_manifest=dict(path=str(manifest),sha256=sha_file(manifest),input_root=str(folder)),
        extra_existing_file=str(extra),nested_private_file=str(nested),cache_canary=str(cache),
        original_public_files=[str(source(public[k]).resolve()) for k in ('evaluation_request','public_binding')],
        audit_policy_files=[str(old_winner),str(cache)],
        path_alias_policy_negatives=[str(link),traversal,relative],
        private_policy_files=[str(ROOT/'docs/STAGE2A5B_GQ_SHARED_FULL_DESIGN.json'),str(foreign)],
        actual_selector_denial_paths=[str(old_winner),str(foreign),str(link),relative])


def prepare_jobs(attempt,binding):
    """Create 72 registered jobs using stdlib metadata and old pure factories.

    It does not call online public checkpoint/request admission, a Schema engine,
    comparator, cache, model, test runner or gate body. Old transport factories
    do validate their small context metadata using stdlib only. SOURCE_SEAL
    exists before this is called.
    """
    from research.information_service_online.runner import build_manifest_fixtures,_short_streams
    from research.information_service_online.admission import (supervision_jobs,interface_failure_jobs,
        public_registration,positive_sensing_body,positive_sensing_config)
    attempt=Path(attempt).resolve();batches=read_json(attempt/'inputs/BATCHES.json')
    admission=read_json(attempt/'inputs/ADMISSION.json');A=batches['A_admission_and_regression'];jobs=[]
    snapshot=next(s for s in batches['B_snapshots'] if s['episode']=='N1' and s['tick']==0)
    history=next(s for s in batches['B_snapshots'] if s['episode']=='N1' and s['tick']==20)
    def absolute(pin):
        path=Path(pin['path']);return path.resolve() if path.is_absolute() else (ROOT/path).resolve()
    fixture_file=attempt/'inputs/admission_public_fixture.json'
    save_json(fixture_file,read_json(absolute(snapshot['public_inputs']['public_checkpoint'])))
    for name,body in [('expected',dict(expected_canary='DENY')),('private_resume',dict(private_state=True)),
                      ('audit_sidecar',dict(source_only=True)),('future_turns',dict(arc_rates=[[1.,.15],[2.,0.]]))]:
        save_json(attempt/'private_admission'/f'{name}.json',body)
    (attempt/'public-looking.json').symlink_to(attempt/'private_admission/expected.json')
    old_short_pin=A['legacy_short_batches'][0]['input_ref'];old_short_path=absolute(old_short_pin)
    old_short=read_json(old_short_path);fixtures=build_manifest_fixtures(attempt,old_short)
    save_json(attempt/'inputs/fixture_registration.json',fixtures)
    def add(job,phase,wls=0):
        row=dict(phase=phase,job=job,WLS_limit=wls);jobs.append(row)
        save_json(attempt/'jobs'/(job['pair_id']+'.json'),row)
    for job in supervision_jobs(attempt.name): add(job,'supervision')
    # Four actual protected-role jobs plus six actual startup injection jobs.
    private=[ROOT/'docs/STAGE2A5B_GQ_SHARED_FULL_DESIGN.json',attempt/'private_admission/expected.json',
        attempt/'private_admission/private_resume.json',attempt/'private_admission/audit_sidecar.json',
        attempt/'private_admission/future_turns.json',attempt/'public-looking.json']
    old_winner=ROOT/'evidence/stage2a5b_gq_online/attempt_0779f047b65149369a4e06dc5959b4fb/pairs/N1_k000_SELECT/env/action_request.json'
    if not old_winner.is_file(): raise ContractError('Real old-winner canary missing')
    for role in ('R','S','sense','reference'):
        modules=[OLD+'.execution',OLD+'.private_probe']
        if role=='R': modules += [NEW+'.motion_cache',NEW+'.evaluator',OLD+'.reference']
        if role=='S': modules += [OLD+'.reference',NEW+'.source_admission']
        if role=='sense': modules += [NEW+'.motion_cache',NEW+'.evaluator',OLD+'.public',OLD+'.measurements','pursuit_v2.environment']
        if role=='reference': modules += [NEW+'.motion_cache',NEW+'.evaluator',OLD+'.evaluator']
        for module in modules:
            if not ROOT.joinpath(*module.split('.')).with_suffix('.py').is_file():
                raise ContractError('Real module denial canary absent: '+module)
        probes=[dict(action='read',target=str(p)) for p in [*private,old_winner]]
        probes.append(dict(action='read',target=os.path.relpath(private[1],ROOT)))
        probes += [dict(action='import',target=module) for module in modules]
        if role=='sense':
            payload=dict(kind='admission_sensor_isolation',probes=probes,positive_body=positive_sensing_body())
            job=_pair(attempt,'ISOLATION_SENSE',_paths(payload,[]),mode='isolation_probe')
            job['sense_start']=positive_sensing_config()
        else:
            payload=_paths(dict(kind='admission_role_isolation',protected_role=role,
                public_checkpoint_file=str(fixture_file),probes=probes),[fixture_file])
            job=_pair(attempt,'ISOLATION_'+role.upper(),payload,mode='isolation_probe')
        job['expected']=dict(accepted=True,real_wls_calls=0);add(job,'isolation')
    for role,transport in [('R','env'),('S','env'),('sense','sense')]:
        for channel in ('argv','env'):
            job=_pair(attempt,f'I03_{role.upper()}_{channel.upper()}',
                _paths(dict(kind='admission_startup_no_work',protected_role=role if role!='sense' else 'R'),[]),mode='isolation_probe')
            job['predeclared_isolation_probe']=True
            job['expected']=dict(guardian_success=False,protected_role=role,real_wls_calls=0,must_observe_explicit_startup_rejection=True)
            job[transport+('_argv_extra' if channel=='argv' else '_env_extra')]=['--private-scenario','FORBIDDEN'] if channel=='argv' else {'GQ_PRIVATE_SCENARIO':'FORBIDDEN'}
            add(job,'isolation')
    for row in admission['online_interface_cases']:
        if row['id'].startswith('ON_IF04'): continue
        payload=dict(kind='interface_checks',gate_ids=[row['id']])
        paths=[]
        if row['id'].startswith('ON_IF03'):
            payload.update(compact_positive_reference=fixtures['positive'],compact_negative_references=fixtures['negative'],
                           compact_nested_probes=fixtures['nested_probes']);paths=fixtures['compact_read_files']
        add(_pair(attempt,row['id'],_paths(payload,paths)),'interface')
    for job in interface_failure_jobs(attempt.name,public_checkpoint_file=fixture_file): add(job,'interface_failure')
    # SG01's receipt is replaced by a newly pinned census in runner immediately
    # before dispatch. Preparation records its initial trusted metadata receipt.
    binding_file=attempt/'runtime_cache_binding.json';source_seal=attempt/'SOURCE_SEAL.json'
    source_document=read_json(source_seal)
    sg1=_paths(dict(kind='shared_gate',gate_id='SG01_SOURCE_CENSUS',census_file=str(attempt/'protection_before.json'),
        census_digest=digest(read_json(attempt/'protection_before.json')),runtime_binding_file=str(binding_file),
        role_closures_file=str(attempt/'role_closures.json'),source_seal_file=str(source_seal)),
        [attempt/'protection_before.json',binding_file,attempt/'role_closures.json',source_seal,
         source_document['source_manifest']['path'],binding['runtime_fingerprint_artifact']['path'],
         *[p['path'] for p in binding['source_files']]])
    add(_pair(attempt,'SG01_SOURCE_CENSUS',sg1),'shared_gate')
    registry=absolute(batches['source_pins']['actual_checkpoint_registry'])
    sourcepaths=[registry]
    for snap in (snapshot,history):
        sourcepaths += [absolute(p) for p in snap['public_inputs'].values()]
        sourcepaths.append(absolute(snap['source_registration']['registered_execution_result_auditor_only']))
    sg2=_paths(dict(kind='shared_gate',gate_id='SG02_PUBLIC_BINDING',snapshot=snapshot,
        history_probe_snapshot=history,registry_path=str(registry),registry_sha=batches['source_pins']['actual_checkpoint_registry']['sha256']),sourcepaths)
    add(_pair(attempt,'SG02_PUBLIC_BINDING',sg2),'shared_gate')
    producer=attempt/'inputs/SG03_unit_producer.json';save_json(producer,dict(scope='UNIT_ONLY',committed=True,physical_history_created=False))
    previous=dict(source_kind='UNIT_ONLY',physical_environment_id='unit:D:N1',producer_role='execution',
        committed=True,producer_passed=True,tick=0,previous_checkpoint_id=None,
        checkpoint_id=digest(dict(unit='SG03',tick=0)),selector_input_origin='NEW_CURRENT_COMPLETE_TABLE',
        artifacts=dict(public_checkpoint=_pin(fixture_file)),producer_result_pin=_pin(producer),
        previous_receipt_id=None,successful_action_cache_link=None)
    current=dict(previous,tick=20,previous_checkpoint_id=previous['checkpoint_id'],
        checkpoint_id=digest(dict(unit='SG03',tick=20)),previous_receipt_id=digest(previous),
        successful_action_cache_link=digest(dict(unit='SG03',successful_action=0)))
    receipts=attempt/'inputs/SG03_unit_receipts.json';save_json(receipts,dict(previous=previous,current=current))
    sg3=_paths(dict(kind='shared_gate',gate_id='SG03_D_NEW_SOURCE',attempt_id=attempt.name,unit_receipts_file=str(receipts)),[receipts])
    add(_pair(attempt,'SG03_D_NEW_SOURCE',sg3),'shared_gate')
    selector=_selector_fixtures(attempt,snapshot)
    sg4=_paths(dict(kind='shared_gate',protected_role='selector',gate_id='SG04_EXACT_ROLE_INPUTS',**selector),selector['policy_paths_256'])
    add(_pair(attempt,'SG04_EXACT_ROLE_INPUTS',sg4),'shared_gate')
    comp=attempt/'inputs/COMPARISON.json'
    sg5=_paths(dict(kind='shared_gate',gate_id='SG05_COMPARATOR_SELFTEST',comparison_file=str(comp),comparison_sha256=sha_file(comp)),[comp])
    add(_pair(attempt,'SG05_COMPARATOR_SELFTEST',sg5),'shared_gate')
    for batch in A['cache_contract_checks']['batches']:
        payload=_paths(dict(kind='shared_short',attempt_id=attempt.name,pair_id=batch['work_id'],short_file=str(attempt/'inputs/SHORT_CHECKS.json'),
            check_ids=batch['check_ids'],runtime_binding_id=binding['runtime_binding_id'],
            comparison_file=str(comp),comparison_sha256=sha_file(comp)),[attempt/'inputs/SHORT_CHECKS.json',comp])
        add(_pair(attempt,batch['work_id'],payload),'shared_short')
    for batch in A['legacy_short_batches']:
        streams=_short_streams(old_short,batch['check_ids'])
        paths=[old_short_path]+(list(map(Path,fixtures['short_read_files'])) if 'S29' in batch['check_ids'] else [])
        payload=_paths(dict(kind='short',short_file=str(old_short_path),check_ids=batch['check_ids'],
            fixture_root=str(attempt/'short_fixtures'),short_manifest_reference=fixtures['short_manifest_reference'] if 'S29' in batch['check_ids'] else None,
            streams=streams),paths)
        add(_pair(attempt,batch['batch_id'],payload,streams),'short',batch['real_wls_upper_bound'])
    for batch in A['legacy_regression_batches']:
        new='FULL_EVALUATION_UNIT' in batch['batch_id']
        paths=[ROOT/'docs/STAGE2A5B_GQ_FULL_EVALUATION_DESIGN.json'] if new else [ROOT/'docs/STAGE2A5B_GQ_FULL_EVALUATION_BATCHES.json']
        # The external job keeps the new A_R2 label; the frozen dispatcher still
        # requires its original registered regression batch identifier.
        legacy_batch_id=batch['batch_id'].removeprefix('A_R2_')
        payload=_paths(dict(kind='new_unit' if new else 'regression',batch_id=legacy_batch_id,
            modules=batch['modules'],historical_test_count=batch['historical_test_count']),paths)
        add(_pair(attempt,batch['batch_id'],payload),'regression',batch['real_wls_upper_bound'])
    _require(len(jobs)==72 and len({j['job']['pair_id'] for j in jobs})==72,'Declared72 pre-main jobs not materialized uniquely')
    return jobs
