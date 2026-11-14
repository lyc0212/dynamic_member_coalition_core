"""Append-only sealing and serial online orchestration under one global budget.

The parent performs file/identity bookkeeping only; every model, selection,
reference and scientific audit runs as a registered guardian-owned worker.
"""
import ast
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import time
import traceback
from .common import CONTRACT_ID,ContractError,digest,read_json,save_json,sha_file,safe_label
ROOT=Path(__file__).resolve().parents[2]
ENTRY=ROOT/'examples/validate_stage2a5b_gq_online.py'
STEM='STAGE2A5B_GQ_ONLINE_'
LOCK=ROOT/'docs'/f'{STEM}PROTOCOL_LOCK.json'
LOCK_SHA='562a7352fb582469e403fde0bc35b94904f0d668ae32ae17c423733e36c7d8ad'


def protected():
    if sha_file(LOCK)!=LOCK_SHA:raise ContractError('Wrong pinned preparation protocol lock')
    lock=read_json(LOCK)
    for name,m in lock['files'].items():
        path=ROOT/name
        if sha_file(path)!=m['sha256'] or path.stat().st_size!=m['size']:raise ContractError('Frozen protocol input changed: '+name)
    rows=[]
    for item in lock['source_protection']:
        manifest=ROOT/item['manifest']
        if sha_file(manifest)!=item['manifest_sha256']:raise ContractError('Old source manifest changed')
        files=read_json(manifest)['files'];bad=[n for n,h in files.items() if not(ROOT/n).is_file() or sha_file(ROOT/n)!=h]
        if bad:raise ContractError('Protected old files changed: '+repr(bad))
        rows.append(dict(manifest=str(manifest),sha256=sha_file(manifest),count=len(files),mismatches=[]))
    return dict(passed=True,protocol_lock_sha256=LOCK_SHA,preparation_revision=lock['preparation_revision'],old=rows)


def pair_job(attempt,pair,payload,streams=None,mode='science'):
    return dict(attempt_id=attempt.name,pair_id=pair,env_start=payload,
        sense_start=dict(contract_id=CONTRACT_ID,mode=mode,streams=streams or []),controller_start=dict(steps=[]))


def readpaths(payload,paths):
    payload['read_files']=sorted({str(Path(p).resolve()) for p in paths})
    if len(payload['read_files'])>256:raise ContractError('Exact input list exceeds preregistered256')
    return payload


def initial_construction_fixture(case):
    """Pure JSON initial test fixture, never an authentic executed checkpoint."""
    cfg=copy.deepcopy(case['config']);histories=[];events=[];targets=[]
    for t in case['targets']:
        if t['birth']!=0.:continue
        j=t['id'];event=dict(event_index=len(events),kind='BIRTH',target_id=j,at=dict(time_seconds=0.,event_tick=0),
                            segment_id=None,progress_before=0.,progress_after=0.,reasons=['BIRTH'])
        h=dict(contract_id='gq_online_task_history_v1',target_id=j,birth_tick=0,cutoff_tick=0,active_segment_id=None,
           segments=[],unassigned_intervals=[dict(start_tick=0,end_at=None,opened_by='BIRTH',opening_event_index=event['event_index'],closing_event_index=None)],events=[event])
        h['history_digest']=digest(h);histories.append(h);events.append(event)
        targets.append(dict(id=j,birth=t['birth'],position_now=copy.deepcopy(t['position_at_birth']),velocity_now=copy.deepcopy(t['velocity']),
            required_robots=t['required_robots'],weight=t['weight'],deadline=t['deadline'],service_duration=t['service_duration']))
    slots=[dict(contract_id='gq_online_measurement_slot_v1',slot_key=dict(target_id=t['id'],robot_id=i,tick=0),state='UNQUERIED',packet=None,slot_digest=None)
           for t in targets for i in range(cfg['robots'])]
    cp=dict(message_kind='public_checkpoint',contract_id='gq_online_checkpoint_v1',previous_checkpoint_id=None,
        phase='DECISION_READY',tick=0,episode_end_tick=120,config=cfg,positions=copy.deepcopy(case['positions_initial']),
        assignment=copy.deepcopy(case['initial_assignment']),targets=targets,
        sensor_profiles=[dict(p,observed_tick=0) for p in case['sensor_declaration_schedule'][0]['profiles']],
        task_histories=histories,current_slots=slots,events_since_previous_checkpoint=events)
    cp['checkpoint_id']=digest(cp);return cp


def _short_streams(short,ids):
    result=[]
    for row in short['checks']:
        if row['check_id'] not in ids:continue
        cid=row['check_id'];cp=digest(dict(short_check=cid,tick=20))
        for call in row['input'].get('calls',[]):
            actual=call['execution_route']=='actual_selected_left_assembler';segment=digest(dict(short_check=cid,segment='synthetic')) if actual else None
            context=dict(work_instance_id=call['call_id'],physical_environment_id='SHORT_SYNTHETIC',checkpoint_id=cp,
                request_identity=cp if actual else digest(dict(short_check=cid,request='constructor')),
                world_identity=None if actual else digest(dict(short_check=cid,world='zero_noise')),
                action_identity=segment if actual else digest(dict(short_check=cid,candidate='declared_team')),
                purpose='ACTUAL_EXECUTION' if actual else 'CANDIDATE_PREDICTION',segment_id=segment,
                service_start_tick=20,first_new_fusion_tick=20)
            result.append(dict(stream_id=call['call_id'],target_id=0,start_tick=20,
                               allowed_sensor_ids=call['occupied_sensor_ids'],context=context))
    return result


def build_manifest_fixtures(attempt,short):
    fixture=next(r['input'] for r in short['checks'] if r['check_id']=='S29')
    base=attempt/'short_fixtures/S29';base.mkdir(parents=True)
    for row in fixture['fixture_files']:
        p=base/row['relative_path'];p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(row['json_content'],ensure_ascii=False,sort_keys=True,separators=(',',':')))
    link=fixture['symlink'];(base/link['relative_path']).symlink_to(link['target'])
    entries=[dict(file_id=r['file_id'],relative_path=r['relative_path'],sha256=r['content_sha256']) for r in fixture['permitted_manifest_entries']]
    save_json(base/'manifest.json',dict(contract_id='gq_online_exact_input_manifest_v1',entries=entries))
    # IF03 reuses exactly the three legal input files; other files exist only as denial probes.
    root=attempt/'compact_fixtures';root.mkdir()
    for r in fixture['fixture_files']:
        p=root/r['relative_path'];p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(r['json_content'],ensure_ascii=False,sort_keys=True,separators=(',',':')))
    (root/'needed/symlink_to_private.json').symlink_to('../private_expected.json')
    def manifest(name,items):
        path=root/name;save_json(path,dict(contract_id='gq_online_exact_input_manifest_v1',entries=items))
        return dict(path=str(path),sha256=sha_file(path),input_root=str(root))
    positive=manifest('manifest.json',entries)
    negative={}
    negative['wrong_hash']=dict(positive,sha256='0'*64)
    negative['path_traversal']=manifest('traversal.json',[dict(file_id='bad',relative_path='../private_admission/expected.json',sha256=sha_file(attempt/'private_admission/expected.json'))])
    negative['symlink']=manifest('symlink.json',[dict(file_id='bad',relative_path='needed/symlink_to_private.json',sha256=sha_file(root/'private_expected.json'))])
    negative['too_many']=manifest('too_many.json',[dict(file_id=f'row{i}',relative_path='needed/F0000.json',sha256=entries[0]['sha256']) for i in range(257)])
    reads=[base/'manifest.json',*[base/r['relative_path'] for r in entries]]
    compact_reads=[root/'manifest.json',*[root/r['relative_path'] for r in entries],root/'traversal.json',root/'symlink.json',root/'too_many.json']
    return dict(short_read_files=list(map(str,reads)),short_manifest_reference=dict(path=str(base/'manifest.json'),sha256=sha_file(base/'manifest.json'),input_root=str(base)),compact_read_files=list(map(str,compact_reads)),
        positive=positive,negative=negative,nested_probes=[str(root/'unlisted.json'),str(root/'private_expected.json'),str(root/'needed/symlink_to_private.json')])


def prepare(attempt):
    if (attempt/'SEAL_I.json').exists():raise FileExistsError('Runtime seal already exists; cannot overwrite')
    before=protected();attempt.mkdir(parents=True,exist_ok=True);(attempt/'inputs').mkdir(exist_ok=True)
    for name in ('DESIGN','SCHEMA','SHORT_CHECKS','ADMISSION','BATCHES'):
        shutil.copyfile(ROOT/'docs'/f'{STEM}{name}.json',attempt/'inputs'/f'{name}.json')
    design=read_json(attempt/'inputs/DESIGN.json');batches=read_json(attempt/'inputs/BATCHES.json');short=read_json(attempt/'inputs/SHORT_CHECKS.json')
    private_inputs={}
    for e in design['episodes']:
        path=attempt/'inputs/private'/f"{e['episode_id']}.json";save_json(path,e['private_execution_input']);private_inputs[e['episode_id']]=str(path)
    fixture_file=attempt/'inputs/admission_public_fixture.json'
    save_json(fixture_file,initial_construction_fixture(design['episodes'][0]['private_execution_input']))
    for name,body in [('expected',{'expected_canary':'DENY'}),('private_resume',{'private_future_canary':True}),
                      ('audit_sidecar',{'source_only_canary':True}),('future_turns',{'arc_rates':[[1.,.15],[2.,0.]]})]:
        save_json(attempt/'private_admission'/f'{name}.json',body)
    (attempt/'public-looking.json').symlink_to(attempt/'private_admission/expected.json')
    fixtures=build_manifest_fixtures(attempt,short)
    save_json(attempt/'inputs/fixture_registration.json',fixtures);save_json(attempt/'inputs/private_input_files.json',private_inputs)
    from .admission import supervision_jobs,isolation_job_specs,interface_failure_jobs
    jobs=[]
    def add(job,phase):
        jobs.append(dict(phase=phase,job=job));save_json(attempt/'jobs'/f"{safe_label(job['pair_id'])}.json",jobs[-1])
    for job in supervision_jobs(attempt.name):add(job,'supervision')
    for job in isolation_job_specs(attempt.name,attempt,public_checkpoint_file=fixture_file):add(job,'isolation')
    payload=readpaths(dict(kind='interface_checks',compact_positive_reference=fixtures['positive'],
        compact_negative_references=fixtures['negative'],compact_nested_probes=fixtures['nested_probes']),fixtures['compact_read_files'])
    add(pair_job(attempt,'ONLINE_INTERFACE_GATES',payload),'interface')
    for job in interface_failure_jobs(attempt.name,public_checkpoint_file=fixture_file):add(job,'interface_failure')
    for batch in batches['short_batches']:
        streams=_short_streams(short,batch['check_ids'])
        paths=[attempt/'inputs/SHORT_CHECKS.json']+(list(map(Path,fixtures['short_read_files'])) if 'S29' in batch['check_ids'] else [])
        payload=readpaths(dict(kind='short',short_file=str(attempt/'inputs/SHORT_CHECKS.json'),check_ids=batch['check_ids'],
                              fixture_root=str(attempt/'short_fixtures'),short_manifest_reference=fixtures['short_manifest_reference'] if 'S29' in batch['check_ids'] else None,streams=streams),paths)
        add(pair_job(attempt,batch['batch_id'],payload,streams),'short')
    for batch in batches['regression_batches']:
        new=batch['batch_id']=='REG_FULL_EVALUATION_UNIT'
        payload=dict(kind='new_unit' if new else 'regression',batch_id=batch['batch_id'],modules=batch['modules'],historical_test_count=batch['historical_test_count'])
        files=[ROOT/'docs/STAGE2A5B_GQ_FULL_EVALUATION_DESIGN.json'] if new else [ROOT/'docs/STAGE2A5B_GQ_FULL_EVALUATION_BATCHES.json']
        add(pair_job(attempt,batch['batch_id'],readpaths(payload,files)),'regression')
    save_json(attempt/'pre_main_jobs.json',jobs)
    save_json(attempt/'inputs/runtime_job_rules.json',dict(contract_id=CONTRACT_ID,
        episodes=design['episode_ids'],decision_ticks=[0,20,40,60,80,100],actual_init_jobs=5,actual_step_jobs=30,
        candidate_order='manifest target then robots then roles; no quality/cost filtering',candidate_batch_max=4,
        dynamic_registration='Only sealed actual producer checkpoint/binding/request/catalog can materialize work; action streams come only from sealed exact selector',
        actual_source='Registered prior actual private snapshot, never predictor result',
        source_authentication='guardian-owned sealed execution role + exact output identities + monotone parent checkpoint/source chain; separate public binding SHA',
        references='all actual candidates at predeclared boundary after episode, fresh numerical execution under public input only',
        audit_inputs='exact per-decision or per-episode needed files; <=256; no all-JSON recursive START',
        budgets=dict(cpu=1200,wall=2400,pair_cpu=60,pair_wall=120),no_extra_wls=True))
    save_json(attempt/'protection_before.json',before)
    names=set(read_json(LOCK)['files'])|{str(LOCK.relative_to(ROOT))}
    for row in read_json(LOCK)['source_protection']:
        names.update(read_json(ROOT/row['manifest'])['files']);names.add(row['manifest'])
    names.update(str(p.relative_to(ROOT)) for p in (ROOT/'research/information_service_online').glob('*.py'))
    names.add(str(ENTRY.relative_to(ROOT)))
    syntax=[]
    for name in sorted(names):
        if name.endswith('.py'):ast.parse((ROOT/name).read_text(),filename=name);syntax.append(name)
    manifest={name:sha_file(ROOT/name) for name in sorted(names)}
    for name in manifest:
        dst=attempt/'frozen_sources'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,dst)
    save_json(attempt/'input_source_manifest.json',dict(count=len(manifest),files=manifest))
    runtime={str(Path(sys.executable).resolve()):sha_file(Path(sys.executable).resolve())}
    for name in ('numpy','scipy'):
        spec=importlib.util.find_spec(name);runtime[spec.origin]=sha_file(spec.origin)
        package=Path(spec.origin).parent
        patterns=('_core/_multiarray_umath*.so','linalg/_umath_linalg*.so') if name=='numpy' else ('linalg/_fblas*.so','optimize/_minpack*.so','optimize/_lsq/least_squares.py')
        for pattern in patterns:
            for binary in package.glob(pattern):runtime[str(binary)]=sha_file(binary)
    frozen={}
    for folder in ('inputs','jobs','private_admission','short_fixtures','compact_fixtures'):
        for p in sorted((attempt/folder).rglob('*')):
            if p.is_file() and not p.is_symlink():frozen[str(p.relative_to(attempt))]=dict(size=p.stat().st_size,sha256=sha_file(p))
    for name in ('authorization.json','pre_main_jobs.json','input_source_manifest.json','protection_before.json'):
        p=attempt/name;frozen[name]=dict(size=p.stat().st_size,sha256=sha_file(p))
    seal=dict(contract_id=CONTRACT_ID,status='SEALED_IMPLEMENTATION_PENDING_ADMISSION',files=frozen,
        source_manifest_sha256=sha_file(attempt/'input_source_manifest.json'),runtime=runtime,python=sys.version,executable=sys.executable,
        protocol_lock_sha256=LOCK_SHA,preparation_revision=read_json(LOCK)['preparation_revision'],
        AST_checked=syntax,budget=read_json(LOCK)['budget'],
        no_actual_online_checkpoint_created=True,presealed_fixture_is_synthetic=True,
        actual_new_source_count=len(list((ROOT/'research/information_service_online').glob('*.py'))),
        new_implementation_unittest_modules=[],short_contract_checks=30,zero_WLS_short_checks=26,
        repair_rejection_probes=dict(count=57,real_wls_calls=0,control_steps=0,
            scope='Nine malformed-output dispatch rejections for each of six fixed fusion calls, plus three missing-slot rejections for S08'),
        old_protection=before)
    save_json(attempt/'SEAL_I.json',seal)
    return dict(passed=True,seal_I_sha256=sha_file(attempt/'SEAL_I.json'),source_file_count=len(manifest),pre_main_jobs=len(jobs))


def verify_seal(attempt):
    seal=read_json(attempt/'SEAL_I.json')
    for name,m in seal['files'].items():
        p=attempt/name
        if sha_file(p)!=m['sha256'] or p.stat().st_size!=m['size']:raise ContractError('Sealed input changed: '+name)
    for name,h in read_json(attempt/'input_source_manifest.json')['files'].items():
        if sha_file(ROOT/name)!=h:raise ContractError('Sealed source changed: '+name)
    for path,h in seal['runtime'].items():
        if sha_file(path)!=h:raise ContractError('Runtime changed: '+path)
    protected();return seal


def _accept_negative(r,job,out):
    if not r['accounting_complete'] or not r['all_reaped'] or r['orphan_records']:raise ContractError('Incomplete guardian lifecycle accounting')
    if job.get('expected',{}).get('guardian_success') is not False:
        if not r['passed']:raise ContractError('Unexpected registered scientific job failure')
        return dict(passed=True)
    if r['passed']:raise ContractError('Declared failure unexpectedly succeeded')
    expected=job['expected']
    if expected.get('must_observe_explicit_startup_rejection'):
        role='sense' if expected['protected_role']=='sense' else 'env'
        log=(out/role/'stdout_stderr.log').read_text()
        if not any(s in log for s in ('unrecognized arguments','GQ_PRIVATE_SCENARIO')):raise ContractError('Startup denial not explicit')
    if job['env_start']['kind']=='admission_interface_failure':
        state=read_json(out/'env/last_committed_state.json')
        if state['tick']!=20 or state['unique_sampling_attempts_retained']!=1 or state['physical_steps']!=0:raise ContractError('IF04 changed previous committed fixture')
        fault=job['env_start']['fault']
        if fault=='no_response' and r['failure']['kind']!='REQUEST_TIMEOUT':raise ContractError('IF04 wrong deadline failure')
        if fault=='worker_exit' and not any(p['role']=='sense' and p.get('returncode')==7 for p in r['processes']):raise ContractError('IF04 exit7 missing')
        if fault=='numeric_contract_violation':
            error=read_json(out/'sense/error.json')
            if error['error_type']!='NumericContractViolation' or error['error']!='INJECTED_ONLINE_NUMERIC_CONTRACT_ERROR':raise ContractError('IF04 actual numerical contract failure missing')
    return dict(passed=True,expected_failure=r['failure'])


def run(attempt):
    verify_seal(attempt)
    if (attempt/'execution_started.json').exists():raise FileExistsError('This attempt already ran; never overwrite/resume a failed run')
    from .supervision import run_pair
    from .admission import validate_supervision
    started=time.monotonic();deadline=started+2400.;cpu=0.;jobs=[];actual_registry=[]
    save_json(attempt/'execution_started.json',dict(monotonic=started,wall_time=time.time(),deadline=deadline,
        seal_I_sha256=sha_file(attempt/'SEAL_I.json'),cpu_ceiling=1200,wall_ceiling=2400))
    design=read_json(attempt/'inputs/DESIGN.json');batches=read_json(attempt/'inputs/BATCHES.json');inputs=read_json(attempt/'inputs/private_input_files.json')
    indices=[];all_decisions=0;table_items=reference_items=0
    def execute(job,phase):
        nonlocal cpu
        if cpu>=1200. or time.monotonic()>=deadline-5:raise ContractError('Original cumulative budget exhausted before next job')
        out=attempt/'pairs'/safe_label(job['pair_id'])
        save_json(attempt/'dispatched_jobs'/f"{safe_label(job['pair_id'])}.json",dict(phase=phase,job=job))
        r=run_pair(job,out,ENTRY,deadline,cpu);cpu+=r['worker_cpu']
        row=dict(pair_id=job['pair_id'],phase=phase,worker_cpu=r['worker_cpu'],controller_cpu=r['controller_cpu'],guardian_cpu=r['guardian_cpu'],
            wall=r['wall'],cumulative_worker_cpu=cpu,raw_passed=r['passed'],guardian_result=str(out/'guardian_result.json'))
        jobs.append(row);save_json(attempt/'resource_ledger.json',dict(jobs=jobs,worker_cpu=cpu,wall=time.monotonic()-started))
        try:
            gate=validate_supervision(r,job) if phase=='supervision' else _accept_negative(r,job,out)
            if gate.get('passed') is not True:raise ContractError('Declared admission checks failed')
            c=read_json(out/'sense/counters.json') if (out/'sense/counters.json').exists() else {}
            if phase not in ('short','primary','reference','actual') and c.get('estimator_calls',0):raise ContractError('Zero-WLS phase invoked estimator')
            row['accepted']=True;row['acceptance']=gate
            value=read_json(out/'env/result.json') if (out/'env/result.json').exists() else {}
            save_json(out/'acceptance.json',dict(passed=True,gate=gate))
            print(json.dumps(dict(pair_id=job['pair_id'],accepted=True,cpu=round(cpu,3),wall=round(time.monotonic()-started,3)),ensure_ascii=False),flush=True)
            return value,str(out/'env/result.json')
        except BaseException as error:
            row['accepted']=False;row['acceptance_error']=str(error);save_json(out/'acceptance.json',dict(passed=False,error=str(error)));raise
        finally:save_json(attempt/'resource_ledger.json',dict(jobs=jobs,worker_cpu=cpu,wall=time.monotonic()-started))
    def register_actual(answer,result_file,eid,previous=None):
        artifacts=answer['artifacts'];producer=Path(result_file).parent.resolve()
        if any(Path(p).is_symlink() or Path(p).resolve().parent!=producer for p in artifacts.values()):raise ContractError('Actual artifact did not come from its registered execution worker')
        cp=read_json(artifacts['public_checkpoint']);binding=read_json(artifacts['public_binding'])
        required={'private_snapshot','public_checkpoint','public_binding'}|({'evaluation_request','candidate_catalog'} if cp['phase']=='DECISION_READY' else set())
        if set(artifacts)!=required or answer['physical_environment_id']!=attempt.name+':'+eid:raise ContractError('Wrong actual producer artifact/environment identity')
        private=read_json(artifacts['private_snapshot'])
        if private['source_identity']!=digest(read_json(inputs[eid])) or private['failed'] or private['inflight'] is not None:raise ContractError('Actual source changed or is not cleanly committed')
        if cp['checkpoint_id']!=answer['checkpoint_id'] or binding['public_checkpoint']!=cp:raise ContractError('Actual producer public artifacts disagree')
        if previous is not None and (cp['tick']!=previous['tick']+20 or cp['previous_checkpoint_id']!=previous['checkpoint_id']):raise ContractError('Actual checkpoint lineage discontinuity')
        if previous is None and (cp['tick']!=0 or cp['previous_checkpoint_id'] is not None):raise ContractError('Initial actual cut is not initial')
        row=dict(episode_id=eid,tick=cp['tick'],checkpoint_id=cp['checkpoint_id'],previous_checkpoint_id=cp['previous_checkpoint_id'],
            physical_environment_id=answer['physical_environment_id'],registered_execution_result=result_file,
            seal_I_sha256=sha_file(attempt/'SEAL_I.json'),artifacts={k:dict(path=v,sha256=sha_file(v),size=Path(v).stat().st_size) for k,v in artifacts.items()})
        actual_registry.append(row);save_json(attempt/'actual_checkpoint_registry.json',actual_registry)
        save_json(attempt/'checkpoint_seals'/f'{eid}_k{cp["tick"]:03d}.json',row)
        return row
    def forecast_batches(eid,cut,operation):
        nonlocal table_items,reference_items
        catalog=read_json(cut['artifacts']['candidate_catalog']['path']);items=[]
        for i in range(0,len(catalog),4):
            part=catalog[i:i+4];works=[dict(candidate=r['candidate'],work_id=r[operation]['work_id']) for r in part]
            streams=[r[operation]['registration'] for r in part]
            kind='predict' if operation=='PRIMARY' else 'reference';phase='primary' if kind=='predict' else 'reference'
            payload=readpaths(dict(kind=kind,physical_environment_id=cut['physical_environment_id'],request_file=cut['artifacts']['evaluation_request']['path'],
                binding_file=cut['artifacts']['public_binding']['path'],binding_sha256=cut['artifacts']['public_binding']['sha256'],
                work_items=works,streams=streams),[cut['artifacts']['evaluation_request']['path'],cut['artifacts']['public_binding']['path']])
            pair=f'{eid}_k{cut["tick"]:03d}_{operation}_B{i//4+1:02d}'
            value,_=execute(pair_job(attempt,pair,payload,streams),phase);items+=value['items']
        if operation=='PRIMARY':table_items+=len(items)
        else:reference_items+=len(items)
        if {i['candidate_id'] for i in items}!={r['candidate']['candidate_id'] for r in catalog}:raise ContractError('Incomplete current active table/reference')
        return [i['result_file'] for i in items]
    try:
        for declared in read_json(attempt/'pre_main_jobs.json'):execute(declared['job'],declared['phase'])
        for episode in design['episodes']:
            eid=episode['episode_id'];physical=attempt.name+':'+eid
            payload=readpaths(dict(kind='initialize',episode_id=eid,physical_environment_id=physical,private_input_file=inputs[eid]),[inputs[eid]])
            answer,result_file=execute(pair_job(attempt,eid+'_INITIALIZE',payload),'initialize')
            cut=register_actual(answer,result_file,eid)
            index=dict(episode_id=eid,private_input_file=inputs[eid],design_file=str(attempt/'inputs/DESIGN.json'),
                initial_artifacts=answer['artifacts'],decisions=[],final_artifacts=None)
            index_file=attempt/'episode_indices'/f'{eid}.json';save_json(index_file,index)
            for tick in episode['timing']['decision_ticks']:
                if cut['tick']!=tick:raise ContractError('Actual decision cadence differs')
                current_artifacts={k:v['path'] for k,v in cut['artifacts'].items()}
                candidate_files=forecast_batches(eid,cut,'PRIMARY')
                actual_work=f'{eid}:ACTUAL:k{tick:03d}'
                payload=readpaths(dict(kind='select',request_file=current_artifacts['evaluation_request'],binding_file=current_artifacts['public_binding'],
                    binding_sha256=cut['artifacts']['public_binding']['sha256'],candidate_result_files=candidate_files,
                    actual_work_identity=actual_work,physical_environment_id=physical,action_request_id=f'{eid}:decision:{tick}'),
                    [current_artifacts['evaluation_request'],current_artifacts['public_binding'],*candidate_files])
                selected,selection_file=execute(pair_job(attempt,f'{eid}_k{tick:03d}_SELECT',payload),'select')
                streams=read_json(selected['stream_file'])
                payload=readpaths(dict(kind='execute',episode_id=eid,physical_environment_id=physical,private_input_file=inputs[eid],
                    private_snapshot_file=current_artifacts['private_snapshot'],private_snapshot_sha256=cut['artifacts']['private_snapshot']['sha256'],
                    action_file=selected['action_file'],work_identity=actual_work,streams=streams),
                    [inputs[eid],current_artifacts['private_snapshot'],selected['action_file']])
                answer,result_file=execute(pair_job(attempt,f'{eid}_k{tick:03d}_ACTUAL',payload,streams),'actual')
                nextcut=register_actual(answer,result_file,eid,cut)
                index['decisions'].append(dict(tick=tick,artifacts=current_artifacts,binding_sha256=cut['artifacts']['public_binding']['sha256'],
                    candidate_result_files=candidate_files,reference_result_files=[],selection_file=selection_file,
                    action_file=selected['action_file'],step_result_file=answer['step_result_file'],
                    execution_result_file=result_file,artifacts_after=answer['artifacts']))
                cut=nextcut;all_decisions+=1;index['final_artifacts']=answer['artifacts'];save_json(index_file,index)
            for decision in index['decisions']:
                tick=decision['tick'];reference=tick in episode['audit_decision_ticks']
                registered=next(r for r in actual_registry if r['episode_id']==eid and r['tick']==tick)
                ref_files=forecast_batches(eid,registered,'INDEPENDENT_REFERENCE') if reference else []
                decision['reference_result_files']=ref_files
                arts=decision['artifacts']
                payload=readpaths(dict(kind='audit_decision',request_file=arts['evaluation_request'],binding_file=arts['public_binding'],
                    binding_sha256=decision['binding_sha256'],candidate_result_files=decision['candidate_result_files'],
                    reference_result_files=ref_files,reference_required=reference,selection_file=decision['selection_file']),
                    [arts['evaluation_request'],arts['public_binding'],decision['selection_file'],*decision['candidate_result_files'],*ref_files])
                audit,afile=execute(pair_job(attempt,f'{eid}_k{tick:03d}_AUDIT',payload),'audit')
                decision['selection_audit_file']=afile;save_json(index_file,index)
            exact=[index_file,inputs[eid],attempt/'inputs/DESIGN.json',*index['initial_artifacts'].values(),*index['final_artifacts'].values()]
            for d in index['decisions']:
                exact += [d['selection_file'],d['selection_audit_file'],d['step_result_file'],d['action_file'],d['execution_result_file'],*d['artifacts'].values(),*d['artifacts_after'].values()]
            payload=readpaths(dict(kind='audit_episode',episode_index_file=str(index_file)),exact)
            audited,apath=execute(pair_job(attempt,eid+'_EPISODE_AUDIT',payload),'audit')
            index['episode_audit_file']=apath;save_json(index_file,index);indices.append(str(index_file))
        paired=[p for p in indices if Path(p).stem in ('N4A','N4B')];exact=list(paired)
        for p in paired:
            idx=read_json(p)
            for d in idx['decisions']:
                if d['tick'] in (0,20):exact += [d['artifacts']['evaluation_request'],d['selection_file'],*d['candidate_result_files']]
        payload=readpaths(dict(kind='audit_pair',episode_index_files=paired),exact)
        pair_audit,pair_path=execute(pair_job(attempt,'N4_PAIRED_FUTURE_AUDIT',payload),'audit')
        verify_seal(attempt);protection=protected();save_json(attempt/'protection_after.json',protection)
        totals=dict(real_wls=0,starts=0,regression_real_wls=0,regression_starts=0)
        for row in jobs:
            base=attempt/'pairs'/safe_label(row['pair_id'])
            if (base/'sense/counters.json').exists():
                c=read_json(base/'sense/counters.json');totals['real_wls']+=c['estimator_calls'];totals['starts']+=c['start_attempts']
            if row['phase']=='regression':
                c=read_json(base/'env/estimate_counts.json');totals['regression_real_wls']+=c['real_estimates'];totals['regression_starts']+=c['native_start_attempts']
        totals['real_wls']+=totals['regression_real_wls'];totals['starts']+=totals['regression_starts']
        if totals['real_wls']>25357 or totals['starts']>228213:raise ContractError('Predeclared numerical call ceiling exceeded')
        episode_audits=[read_json(read_json(p)['episode_audit_file']) for p in indices]
        coverage=all(a['all_episode_objectives_passed'] for a in episode_audits)
        result=dict(passed=coverage,numerical_and_contract_passed=True,research_coverage_passed=coverage,
            status='PASSED' if coverage else 'LEGAL_PATH_BUT_REQUIRED_RESEARCH_WITNESS_NOT_OBTAINED',
            episode_index_files=indices,episode_audits=episode_audits,paired_future_audit=pair_path,
            actual_decisions=all_decisions,primary_candidate_evaluations=table_items,independent_candidate_evaluations=reference_items,
            totals=totals,resource=dict(scientific_cpu=cpu,wall=time.monotonic()-started,
                controller_cpu=sum(r['controller_cpu'] for r in jobs),guardian_cpu=sum(r['guardian_cpu'] for r in jobs)),
            accepted_jobs=sum(r.get('accepted',False) for r in jobs),job_count=len(jobs),old_protection=protection,
            seal_I_sha256=sha_file(attempt/'SEAL_I.json'))
        if result['resource']['wall']>2400. or cpu>1200.:raise ContractError('Final original budget exceeded')
        save_json(attempt/'result.json',result)
        return result
    except BaseException as error:
        failed=dict(passed=False,status='STOPPED_WITH_RETAINED_EVIDENCE',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),
            actual_decisions=all_decisions,primary_candidate_evaluations=table_items,independent_candidate_evaluations=reference_items,
            accepted_jobs=sum(r.get('accepted',False) for r in jobs),job_count=len(jobs),last_job=jobs[-1] if jobs else None,
            resource=dict(scientific_cpu=cpu,wall=time.monotonic()-started),automatic_retry=False)
        try:failed['old_protection']=protected()
        except BaseException as p:failed['protection_error']=str(p)
        save_json(attempt/'result.json',failed);print(json.dumps(failed,ensure_ascii=False),flush=True);raise


def dispatch(args):
    attempt=Path(args.attempt).resolve()
    if not attempt.is_relative_to(ROOT/'evidence/stage2a5b_gq_online'):raise ContractError('Dedicated new online evidence path required')
    if args.command=='prepare':value=prepare(attempt)
    elif args.command=='run':value=run(attempt)
    else:
        from .reporting import report
        value=report(attempt)
    print(json.dumps(value,ensure_ascii=False),flush=True);return 0
