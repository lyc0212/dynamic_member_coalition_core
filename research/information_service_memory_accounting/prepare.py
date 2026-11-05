"""Metadata-only preparation. No cache instance, gate, oracle or WLS is run."""
import ast
from copy import deepcopy
from pathlib import Path
import shutil
import sys

from research.information_service_shared.common import typed_digest, CONTRACT_ID as SENSOR_CONTRACT
from .common import (ROOT, BASE, PROTOCOL, PROTOCOL_SHA, CONTRACT, ENTRY,
                     ORDER, PREDICTIONS, require, read_json, save_json,
                     file_pin, check_pin, sha_file)

CLOSED = ROOT/'evidence/stage2a5b_gq_future_profile/attempt_supplement_preparation_20261027_v02'
OLD_FUTURE = ROOT/'evidence/stage2a5b_gq_future_profile/attempt_preparation_20261025_future_v01_r2'
HERE = Path(__file__).resolve().parent


def protect():
    require(sha_file(PROTOCOL/'PREPARATION_PACKAGE_SEAL.json') == PROTOCOL_SHA, 'PROTOCOL_PACKAGE_CHANGED')
    package = read_json(PROTOCOL/'PREPARATION_PACKAGE_SEAL.json')
    for name, value in package['files'].items():
        check_pin(dict(path=str(PROTOCOL/name), **value))
    check_pin(package['protocol_source'])
    input_pins={}
    def collect(value):
        if isinstance(value,dict):
            if isinstance(value.get('path'),str) and isinstance(value.get('sha256'),str):
                previous=input_pins.get(value['path'])
                require(previous is None or previous['sha256']==value['sha256'],'CONFLICTING_INPUT_PIN')
                input_pins[value['path']]=value
            for child in value.values():collect(child)
        elif isinstance(value,list):
            for child in value:collect(child)
    collect(read_json(PROTOCOL/'INPUT_PINS.json'))
    require(len(input_pins)==53,'INPUT_PIN_COVERAGE')
    for value in input_pins.values():check_pin(value)
    # This inherited entry verifies bytes/source census only, never saved-data
    # semantics, a cache constructor, an oracle or a gate.
    from research.information_service_final_summary.prepare import verify as verify_closed
    verify_closed(CLOSED)
    saved = read_json(ROOT/'evidence/stage2a5b_gq_future_profile/supplement_execution_review_20261027_v02/COMPLETED_ATTEMPT_FILES.json')
    require({str(f.relative_to(CLOSED)) for f in CLOSED.rglob('*') if f.is_file()} == set(saved['files']),
            'CLOSED_SNAPSHOT_MEMBERSHIP')
    for name, value in saved['files'].items():
        check_pin(dict(path=str(CLOSED/name), **value))
    return dict(passed=True, source_count=437, runtime_fingerprints=8, unique_input_files=len(input_pins),
                original_failed_attempt_files=3811, closed_supplement_files=len(saved['files']),
                source_scope='metadata identities only; no memory or scientific gate execution')


def attach_pins(payload, paths):
    payload = deepcopy(payload)
    names = sorted({str(Path(p).resolve()) for p in paths})
    require(len(names) <= 256, 'READ_FILE_LIMIT', str(len(names)))
    payload.update(read_files=names, source_pins={name:file_pin(name) for name in names})
    return payload


def pair(attempt, name, payload, streams=()):
    return dict(attempt_id=attempt.name, pair_id=name, env_start=payload,
                sense_start=dict(contract_id=SENSOR_CONTRACT, mode='science', streams=list(streams)),
                controller_start=dict(steps=[]))


def table_paths(table):
    paths = list(table['candidate_result_files'])
    for prod in table['producer_records']:
        paths += [prod[k] for k in ('job_file','guardian_result_file','response_registry_file','env_result_file')]
        paths += [prod[k] for k in ('supervision_receipt_file','sense_counters_file',
            'memory_sidecar_file','memory_receipt_file','memory_snapshot_file','memory_runtime_file') if k in prod]
    for cache in table.get('cache_batches', []):
        paths += [v for k,v in cache.items() if k.endswith('_file')]
    return paths


def historical_table(inputs):
    ref = inputs['registered_reference'];src = ref['source_job'];saved = ref['saved_reference']
    files = {Path(r['path']).name:r['path'] for r in saved['cache_files']}
    prod = dict(pair_id=src['expected_pair_id'], job_file=src['job']['path'],
        guardian_result_file=src['guardian']['path'],response_registry_file=src['response_registry']['path'],
        env_result_file=saved['producer_result']['path'])
    refs = [p['path'] for p in saved['candidates']]
    cache = dict(batch_id=src['expected_pair_id'], producer_job_file=prod['job_file'],
        cache_diagnostics_file=files['cache_diagnostics.json'],cache_trace_file=files['cache_trace.json'],
        cache_trace_jsonl_file=files['cache_trace.jsonl'],cache_scope_file=files['cache_scope.json'],
        cache_instrumentation_file=files['cache_instrumentation.json'],candidate_ownership_file=files['candidate_ownership.json'],
        canonical_batch_table_file=files['canonical_batch_table.json'],oracle_file=ref['motion_oracle']['path'],
        candidate_result_files=refs)
    return dict(source_role='historical_reference',method='S',candidate_result_files=refs,
                producer_records=[prod],cache_batches=[cache])


def current_table(attempt, name, prediction, inputs):
    from research.information_service_shared.common import safe_label
    env=attempt/'pairs'/name/'env'
    refs=[str(env/'work'/safe_label(w['work_id'])/'result.json') for w in prediction['env_start']['work_items']]
    prod=dict(pair_id=name, job_file=str(attempt/'dispatched_jobs'/f'{name}.json'),
        guardian_result_file=str(env.parent/'guardian_result.json'),response_registry_file=str(env/'response_registry.json'),
        env_result_file=str(env/'result.json'),files=[],
        supervision_receipt_file=str(env.parent/'memory_supervision_receipt.json'),
        sense_counters_file=str(env.parent/'sense/counters.json'),
        memory_sidecar_file=str(env/'memory_measurements.jsonl'),memory_receipt_file=str(env/'observer_receipt.json'),
        memory_snapshot_file=str(env/'memory_accounting.json'),memory_runtime_file=str(env/'memory_runtime.json'))
    cache=dict(batch_id=name,producer_job_file=prod['job_file'],candidate_result_files=refs,
        oracle_file=inputs['registered_reference']['motion_oracle']['path'])
    for key,filename in (('cache_diagnostics_file','cache_diagnostics.json'),('cache_trace_file','cache_trace.json'),
        ('cache_trace_jsonl_file','cache_trace.jsonl'),('cache_scope_file','cache_scope.json'),
        ('cache_instrumentation_file','cache_instrumentation.json'),('candidate_ownership_file','candidate_ownership.json'),
        ('canonical_batch_table_file','canonical_batch_table.json')):
        cache[key]=str(env/filename)
    return dict(source_role='current_designated_run',method='S',candidate_result_files=refs,
                producer_records=[prod],cache_batches=[cache],registrations=prediction['sense_start']['streams'])


def prepare(attempt):
    attempt=Path(attempt).resolve()
    require(attempt.parent==BASE and attempt.name.startswith('attempt_'), 'INDEPENDENT_ATTEMPT')
    require(not attempt.exists() or not any(attempt.iterdir()), 'FRESH_PREPARATION')
    protection=protect();inputs=read_json(PROTOCOL/'INPUT_PINS.json')
    require(sys.platform.startswith('linux'), 'LINUX_REQUIRED')
    runtime=read_json(CLOSED/'SEAL.json')['runtime']
    require(str(Path(sys.executable).resolve()) in runtime, 'INTERPRETER_CHANGED')
    attempt.mkdir(parents=True,exist_ok=True)
    save_json(attempt/'protection_before.json',protection)
    for f in sorted(PROTOCOL.iterdir()):
        if f.is_file():
            dst=attempt/'protocol'/f.name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dst)
    sources=read_json(CLOSED/'source_manifest.json')['files'].copy()
    new=[*sorted(HERE.glob('*.py')), *sorted(HERE.glob('*.json')), ENTRY,
         *sorted((ROOT/'tests').glob('test_memory_accounting*.py'))]
    for f in new:
        if f.suffix=='.py':ast.parse(f.read_text(),filename=str(f))
        sources[str(f.relative_to(ROOT))]=sha_file(f)
    for name,digest in sources.items():
        require(sha_file(ROOT/name)==digest,'SOURCE_CHANGED_DURING_PREPARE',name)
        dst=attempt/'frozen_sources'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dst)
    save_json(attempt/'source_manifest.json',dict(files=sources,count=len(sources)))
    from .runtime import role_modules
    closures={role:sorted(role_modules(role)) for role in ('S','admission','audit','sense')}
    save_json(attempt/'role_closures.json',closures)
    source_seal=dict(contract_id=CONTRACT,verification_attempt_id=attempt.name,
        protocol_package=file_pin(PROTOCOL/'PREPARATION_PACKAGE_SEAL.json'),
        controls={f.name:file_pin(f) for f in PROTOCOL.iterdir() if f.is_file()},
        source_manifest=file_pin(attempt/'source_manifest.json'),role_closures=file_pin(attempt/'role_closures.json'),
        runtime=runtime,entry=file_pin(ENTRY),declared_order=ORDER,resources=read_json(PROTOCOL/'JOB_PLAN.json')['proposed_limits'],
        scientific_input_pins=inputs['public_prediction_inputs'],new_measurement_implementation=True,
        empty_exchange_recipe_source=file_pin(OLD_FUTURE/'dispatched_jobs/G0.json'))
    save_json(attempt/'SOURCE_SEAL.json',source_seal);source_sha=sha_file(attempt/'SOURCE_SEAL.json')
    request,binding=[p['path'] for p in inputs['public_prediction_inputs']]
    oldjob=read_json(inputs['registered_reference']['source_job']['job']['path'])['job']
    oldscope=oldjob['env_start']['cache_scope']
    def scoped(name):
        runtime_id=typed_digest(dict(source_seal_sha256=source_sha,run_id=name,contract=CONTRACT))
        scope=deepcopy(oldscope);scope.update(attempt_id=attempt.name,batch_id=name,cache_instance_id=name+':cache',
            runtime_binding_id=runtime_id);scope['full_scope_id']=typed_digest({k:v for k,v in scope.items() if k!='full_scope_id'})
        return runtime_id,scope
    controls=dict(memory_inputs_file=str(PROTOCOL/'INPUT_PINS.json'),
        gate_sequence_file=str(PROTOCOL/'G0_SEQUENCE.json'),gate_checklist_file=str(PROTOCOL/'GATE_CHECKLIST.json'),
        object_contract_file=str(PROTOCOL/'OBJECT_MUTATION_CONTRACT.json'),
        measurement_contract_file=str(PROTOCOL/'MEASUREMENT_CONTRACT.json'),
        acceptance_matrix_file=str(PROTOCOL/'ACCEPTANCE_MATRIX.json'),
        execution_seal_file=str(attempt/'SOURCE_SEAL.json'),
        expected_source_seal_sha256=source_sha,request_file=request,binding_file=binding,binding_sha256=sha_file(binding))
    control_paths=[*inputs['public_prediction_inputs'],file_pin(attempt/'SOURCE_SEAL.json'),
                   file_pin(attempt/'source_manifest.json'),file_pin(attempt/'role_closures.json')]
    gatepaths=[v['path'] for v in control_paths]+[str(f) for f in PROTOCOL.iterdir() if f.is_file()]
    # Frozen source bytes needed by the gate's source/clone identity checks are
    # source permissions, not recursively admitted historical data.
    rid,scope=scoped('G0')
    gate_identity={k:scope[k] for k in ('attempt_id','decision_id','batch_id','cache_instance_id','runtime_binding_id')}
    gate_payload=dict(kind='memory_gate',gate='G0',protected_role='admission',
        inputs_file=str(PROTOCOL/'INPUT_PINS.json'),gate_identity=gate_identity,
        original_public_scope=oldscope,runtime_binding_id=rid,
        gate_budget_limits=read_json(PROTOCOL/'GATE_CHECKLIST.json')['G0_work_totals'],**controls)
    zero_source=read_json(OLD_FUTURE/'dispatched_jobs/G0.json')['job']['env_start']
    registration=deepcopy(zero_source['streams'][0]);stream_id=attempt.name+':G0:T0:first20'
    registration['stream_id']=stream_id
    registration['context'].update(work_instance_id=attempt.name+':G0',physical_environment_id=attempt.name+':G0')
    frame=deepcopy(zero_source['frame']);frame.update(stream_id=stream_id,frame_id=stream_id+':tick20')
    gate_payload.update(streams=[registration],frame=frame,allowed_sensor_ids=zero_source['allowed_sensor_ids'],start_tick=20)
    save_json(attempt/'jobs/G0.json',pair(attempt,'G0',attach_pins(gate_payload,gatepaths),[registration]))
    gate1=dict(gate_payload,gate='G1',G0_result_file=str(attempt/'pairs/G0/env/result.json'),
               G0_guardian_file=str(attempt/'pairs/G0/guardian_result.json'))
    gate1.update(streams=[])
    save_json(attempt/'jobs/G1.template.json',dict(payload=gate1,base_paths=gatepaths))
    declarations=[];predictions={};hist=historical_table(inputs)
    for name in PREDICTIONS:
        variant=name.split('_')[0];repeat=name[-1];rid,scope=scoped(name)
        decl=dict(run_id=name,condition=variant,variant=variant,repeat=repeat,method='S',
            attempt_id=attempt.name,pair_id=name,physical_environment_id=attempt.name+':'+name,
            runtime_binding_id=rid,expected_source_seal_sha256=source_sha,expected_indices=[8,9,10,11],
            detailed_timing=False,cache_scope_id=scope['full_scope_id'])
        declfile=attempt/'runs'/f'{name}.json';save_json(declfile,decl);declarations.append(file_pin(declfile))
        works=deepcopy(oldjob['env_start']['work_items']);streams=deepcopy(oldjob['sense_start']['streams'])
        for work,reg in zip(works,streams):
            wid=attempt.name+':'+name+f":C{work['candidate']['index']:04d}"
            work['work_id']=wid;reg['stream_id']=wid+':T0:first20';reg['context'].update(work_instance_id=wid,physical_environment_id=decl['physical_environment_id'])
        meta=dict(variant=variant,run_id=name,condition=variant,repeat=repeat,
            execution_source_seal_sha256=source_sha,run_declaration_file=str(declfile),
            protocol_file=str(PROTOCOL/'SPEC.md'),inputs_file=str(PROTOCOL/'INPUT_PINS.json'),runtime_binding_id=rid)
        payload=dict(kind='predict_shared',method='S',protected_role='S',physical_environment_id=decl['physical_environment_id'],
            runtime_binding_id=rid,request_file=request,binding_file=binding,binding_sha256=sha_file(binding),
            cache_scope=scope,work_items=works,streams=streams,memory_accounting=meta)
        prediction=pair(attempt,name,attach_pins(payload,[request,binding]),streams)
        predictions[name]=prediction;save_json(attempt/'jobs'/f'{name}.json',prediction)
        current=current_table(attempt,name,prediction,inputs)
        audit=dict(kind='memory_audit',protected_role='audit',run_id=name,inputs_file=str(OLD_FUTURE/'inputs.json'),
            historical=hist,current=current,run_declaration_file=str(declfile),expected_current=decl,**controls)
        paths=[str(OLD_FUTURE/'inputs.json'),str(declfile),*table_paths(hist),*table_paths(current),
               inputs['registered_reference']['historical_seal']['path'],
               request,binding,str(attempt/'SOURCE_SEAL.json'),str(PROTOCOL/'INPUT_PINS.json'),str(PROTOCOL/'MEASUREMENT_CONTRACT.json')]
        if name in ('NEW_a','OLD_b'):
            other='OLD_a' if name=='NEW_a' else 'NEW_b'
            audit.update(paired_run_id=other,paired_sidecar_file=str(attempt/'pairs'/other/'env/memory_measurements.jsonl'),
                         paired_audit_file=str(attempt/'pairs'/(other+'_AUDIT')/'env/result.json'))
            paths += [audit['paired_sidecar_file'],audit['paired_audit_file']]
        save_json(attempt/'jobs'/f'{name}_AUDIT.template.json',dict(payload=audit,exact_read_files=sorted(set(paths))))
    save_json(attempt/'manifest.json',dict(contract_id=CONTRACT,order=ORDER,runs=declarations,
        jobs=[dict(pair_id=name,kind='prediction' if name in PREDICTIONS else 'postrun_audit' if name.endswith('_AUDIT') else 'gate' if name in ('G0','G1') else 'final') for name in ORDER],
        resources=read_json(PROTOCOL/'JOB_PLAN.json')['proposed_limits'],
        budget_assessment=file_pin(PROTOCOL/'BUDGET_ASSESSMENT.json'),budget_sufficiency_established=False,
        risk_acceptance='User authorizes one automatic hard-capped run after static preparation; no budget extension or trial G0 outside this ledger'))
    budget=dict(read_json(PROTOCOL/'BUDGET_ASSESSMENT.json'),implementation_source_manifest=file_pin(attempt/'source_manifest.json'),
        implementation_new_files=len(new),budget_sufficiency_established=False,
        complete_work_counts_fixed=True,additional_implementation_costs_unmeasured=True,
        NoWLS_gate_call_barrier_CPU='additional callback overhead is inside nonprediction job CPU; no such profiler in performance runs',
        execution_policy='Single 240/480 attempt authorized; G0 and failures consume same account; resource limit causes stop, no retry')
    save_json(attempt/'IMPLEMENTATION_BUDGET_REVIEW.json',budget)
    # Check only static START serialization. Dynamic audits are checked at their
    # actual dispatch, once their sources exist and have external file pins.
    from research.information_service_online.runtime import serialized_message_size
    sizes={}
    for name in ['G0',*PREDICTIONS]:
        job=read_json(attempt/'jobs'/f'{name}.json')
        sizes[name]={r:serialized_message_size(dict(type='START',payload=job[r+'_start'])) for r in ('env','sense','controller')}
        require(all(v<=2*1024**2 for v in sizes[name].values()),'START_SIZE_LIMIT',name)
    save_json(attempt/'static_checks.json',dict(passed=True,scope='AST/source/file identity and START metadata only',
        new_source_assets=len(new),source_count=len(sources),START_sizes=sizes,
        gates_run=0,cache_instances_created=0,scientific_calls=0,role_closures=closures))
    assets={str(f.relative_to(attempt)):dict(size_bytes=f.stat().st_size,sha256=sha_file(f))
            for f in sorted(attempt.rglob('*')) if f.is_file() and 'frozen_sources' not in f.parts}
    save_json(attempt/'SEAL.json',dict(contract_id=CONTRACT,status='IMPLEMENTED_PREPARED_NOT_RUN',
        files=assets,source_count=len(sources),source_seal_sha256=source_sha,runtime=runtime,
        protocol_package_sha256=PROTOCOL_SHA))
    return dict(prepared=True,attempt=str(attempt),seal=file_pin(attempt/'SEAL.json'),
                source_count=len(sources),new_source_assets=len(new),assets=len(assets),START_sizes=sizes,
                gates_run=0,budget_sufficiency_established=False)


def verify(attempt):
    attempt=Path(attempt).resolve();require(attempt.parent==BASE and attempt.name.startswith('attempt_'),'INDEPENDENT_ATTEMPT')
    seal=read_json(attempt/'SEAL.json')
    require(seal['contract_id']==CONTRACT and seal['protocol_package_sha256']==PROTOCOL_SHA,'EXECUTION_CONTRACT_CHANGED')
    for name,value in seal['files'].items():check_pin(dict(path=str(attempt/name),**value))
    for name,digest in read_json(attempt/'source_manifest.json')['files'].items():
        require(sha_file(ROOT/name)==digest and sha_file(attempt/'frozen_sources'/name)==digest,'SEALED_SOURCE_CHANGED',name)
    for value in seal['runtime'].values():check_pin(value)
    require(str(Path(sys.executable).resolve()) in seal['runtime'],'INTERPRETER_CHANGED')
    require(sha_file(attempt/'SOURCE_SEAL.json')==seal['source_seal_sha256'],'SOURCE_SEAL_CHANGED')
    protect()
    return seal
