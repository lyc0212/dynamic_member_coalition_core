"""Frozen online short checks through production seams, without controller rollouts.

Only the six declared public fusion calls may reach the sensing worker. Inputs
are handed to production APIs without expected fields. Independent frame/source
checks precede sensing; quality and clock checks follow it. Import runs no check.
"""
from copy import deepcopy
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace

from .common import ContractError, AccessDenied, digest, read_json, save_json


def _equal(actual,expected,path='',atol=1e-12,rtol=0.):
    if isinstance(expected,dict):
        if not isinstance(actual,dict):raise AssertionError(path+' is not a mapping')
        for k,v in expected.items():
            if k not in actual:raise AssertionError(path+'.'+k+' was not observed')
            _equal(actual[k],v,path+'.'+k,atol,rtol)
    elif isinstance(expected,list):
        if not isinstance(actual,(list,tuple)) or len(actual)!=len(expected):raise AssertionError(path+' length differs')
        for i,(a,b) in enumerate(zip(actual,expected)):_equal(a,b,path+f'[{i}]',atol,rtol)
    elif isinstance(expected,float):
        if not isinstance(actual,(int,float)) or not math.isfinite(actual) or abs(actual-expected)>atol+rtol*abs(expected):
            raise AssertionError(f'{path}: {actual!r} != {expected!r}')
    elif type(actual) is not type(expected) or actual!=expected:
        raise AssertionError(f'{path}: {actual!r} != {expected!r}')


def _reject(callback,classes=(ContractError,ValueError,TypeError)):
    try:callback()
    except classes as error:return dict(error_type=type(error).__name__,message=str(error))
    raise AssertionError('Required rejection did not occur')


def _cfg(n=3,y=1,**changes):
    from pursuit_v2.config import Config
    values=dict(robots=n,task_count=y,capture_mode='stepwise_service',geometry_mode='angular_standoff_v1',max_stages=2)
    values.update(changes)
    return Config(**values)


def _team(rows):
    return [dict(robot_id=int(r[0]),role=r[1]) if not isinstance(r,dict) else deepcopy(r) for r in rows]


def _slot(logical):
    from . import public
    if 'slot_key' in logical:return public.seal_slot(logical)
    k=logical['key']
    return public.seal_slot(dict(slot_key=dict(target_id=k['target_id'],robot_id=int(k['stable_robot_id'][1:]),tick=k['global_tick']),
        state=logical['state'],packet=deepcopy(logical.get('packet'))))


def _context(position,sigma=.02,health='available'):
    return dict(position=deepcopy(position),sigma=sigma,health=health)


def _clock(duration=.1,progress=0.,tick=20,G=True,Q='PASS',team=None,n=3):
    from .evaluator import ClockStepper
    team=[[0,'dual_neg45'],[1,'dual_pos45']] if team is None else team
    return ClockStepper(_cfg(n),duration,dict(base=progress,intervals=0,team=deepcopy(team)),team,tick,G,Q)


def _flat(assignment,progress=0.,tick=20,targets=None,positions=None):
    targets=targets or [dict(id=0,required_robots=2)]
    cfg=_cfg(len(assignment),max(t['id'] for t in targets)+1)
    histories=[]
    for t in targets:
        team=[[i,a['role']] for i,a in enumerate(assignment) if a['target']==t['id']]
        p=progress.get(str(t['id']),0.) if isinstance(progress,dict) else progress
        histories.append(dict(target_id=t['id'],clock_state=dict(base=p,intervals=0,team=team),
                              last_endpoint=dict(tick=tick,G=True,Q='PASS') if team else None))
    return dict(config=asdict(cfg),start_tick=tick,assignment=deepcopy(assignment),targets=deepcopy(targets),
                positions=deepcopy(positions or [[8.,10.] for _ in assignment]),gq_histories=histories)


def _boundary(request,actions):
    from .evaluator import boundary_transition
    before=digest(request);result=boundary_transition(request,actions)
    if digest(request)!=before:raise AssertionError('Production boundary mutated synthetic input')
    return result


def short_sensing_registration(check_id,call):
    from .runtime import validate_registration
    actual=call['execution_route']=='actual_selected_left_assembler'
    cp=digest(dict(short_check=check_id,tick=20))
    segment=digest(dict(short_check=check_id,segment='synthetic')) if actual else None
    c=dict(work_instance_id=call['call_id'],physical_environment_id='SHORT_SYNTHETIC',
        checkpoint_id=cp,request_identity=cp if actual else digest(dict(short_check=check_id,request='constructor')),
        world_identity=None if actual else digest(dict(short_check=check_id,world='zero_noise')),
        action_identity=segment if actual else digest(dict(short_check=check_id,candidate='declared_team')),
        purpose='ACTUAL_EXECUTION' if actual else 'CANDIDATE_PREDICTION',segment_id=segment,
        service_start_tick=20,first_new_fusion_tick=20)
    return validate_registration(dict(stream_id=call['call_id'],target_id=0,start_tick=20,
        allowed_sensor_ids=deepcopy(call['occupied_sensor_ids']),context=c))


def short_sensing_registrations(short_file,check_ids):
    rows=read_json(short_file)['checks']
    return [short_sensing_registration(row['check_id'],call) for row in rows if row['check_id'] in check_ids
            for call in row['input'].get('calls',[])]


def _quality_at(payload,x):
    J=[]
    for p,sigma in zip(payload['positions'],payload['sigmas']):
        dx,dy=x[0]-p[0],x[1]-p[1];r2=dx*dx+dy*dy
        J.append([dy/(sigma*r2),-dx/(sigma*r2)])
    a=math.fsum(j[0]*j[0] for j in J);b=math.fsum(j[0]*j[1] for j in J);d=math.fsum(j[1]*j[1] for j in J)
    maximum=(a+d+math.hypot(a-d,2*b))/2;minimum=(a*d-b*b)/maximum
    return dict(J=J,I=[[a,b],[b,d]],radius_proxy=math.sqrt(-2*math.log(.05)/minimum))


def _check_assembled(expected,I,r):
    """Independent audit of all occupied slots and only contributing records.

    Frozen answers stay in this checker, never in the production assembler.
    Exact digests here distinguish missing fields, extra fields and binary64 data.
    """
    cid=r['call_id'];a=r['assembled'];given=r['assembler_input']
    call=next(c for c in I['calls'] if c['call_id']==cid)
    def exact(value,reference,label):
        if digest(value)!=digest(reference):raise AssertionError(label+' differs')
    team=_team(I['assembler_inputs']['team']);robots=[m['robot_id'] for m in team]
    allowed=[f'U{i}' for i in robots]
    exact(a['team'],team,'occupied team')
    exact(a['allowed_sensor_ids'],allowed,'allowed occupied sensors')
    exact(allowed,call['occupied_sensor_ids'],'frozen occupied sensors')
    exact(a['actual'],call['execution_route']=='actual_selected_left_assembler','actual/model route')
    frame=expected['assembled_frames'][cid]
    exact(a['frame'],frame,'assembled frame')
    exact([s['slot_key']['robot_id'] for s in a['source_slots']],robots,'all occupied source slots')
    packets={p['sensor_id']:{k:deepcopy(v) for k,v in p.items() if k!='packet_id'} for p in frame['records']}
    if len(packets)!=len(frame['records']):raise AssertionError('Duplicate expected contributing identity')
    current={s['slot_key']['robot_id']:s for s in given['current_slots']}
    references=[]
    for robot in robots:
        s=current[robot];sid=f'U{robot}'
        if s['state']=='UNQUERIED':
            outcome='MISSING' if given['sensor_profiles'][robot]['health']=='missing' else 'VALID'
            source='MODEL';observed=None;packet=packets.get(sid)
        else:
            outcome=s['state'];source='OBSERVED';observed=s['slot_digest'];packet=deepcopy(s['packet'])
        if (outcome=='VALID')!=(sid in packets):raise AssertionError('Contributing identities disagree with slot outcome')
        if outcome=='MISSING' and packet is not None:raise AssertionError('Missing occupied slot contains a packet')
        if outcome=='VALID':exact(packet,packets[sid],'contributing packet '+sid)
        references.append(dict(slot_key=deepcopy(s['slot_key']),source=source,outcome=outcome,
                               packet=packet,observed_slot_digest=observed))
    exact(a['source_slots'],references,'complete occupied slot provenance')
    by_sensor={f"U{s['slot_key']['robot_id']}":s for s in a['source_slots']}
    contributing=[p['sensor_id'] for p in frame['records']]
    tags=expected['assembled_source_tags'][cid]
    if len(tags)!=len(contributing):raise AssertionError('Frozen contributing tag count differs')
    exact({sid:by_sensor[sid]['source'] for sid in contributing},dict(zip(contributing,tags)),
          'source tags by contributing sensor identity')
    expected_payload=dict(sensor_ids=contributing,positions=[p['position'] for p in frame['records']],
        bearings=[p['bearing'] for p in frame['records']],sigmas=[p['sigma'] for p in frame['records']],domain=[[0.,0.],[20.,20.]])
    exact(a['payload'],expected_payload,'assembled public payload')
    exact(a['payload_digest'],digest(expected_payload),'assembled public payload digest')
    return dict(passed=True,before_wls=True,occupied_sensor_ids=allowed,contributing_sensor_ids=contributing,
                slot_outcomes=[s['outcome'] for s in references],sources=[s['source'] for s in references])


def _check_then_sense(r,check,sense_callback,before_sense):
    r['pre_wls_check']=check(r)
    before_sense(r)
    a=r['assembled'];registration=r['registration']
    return sense_callback(a['frame'],a['allowed_sensor_ids'],registration['start_tick'],registration['context'])


def _pre_wls_rejection_probes(row,check):
    """Mutate saved copies, exercising the real check-to-sense dispatch seam.

    No estimator, motion or new assembly. Any call to the sensing spy is failure.
    """
    mutations={
        'frame_bearing':lambda a:a['frame']['records'][0].__setitem__('bearing',42.),
        'occupied_team_dropped':lambda a:a['team'].pop(),
        'occupied_role_changed':lambda a:a['team'][0].__setitem__('role','invalid'),
        'allowed_member_dropped':lambda a:a['allowed_sensor_ids'].pop(),
        'source_slot_dropped':lambda a:a['source_slots'].pop(),
        'source_tag_changed':lambda a:a['source_slots'][0].__setitem__('source','INVALID'),
        'source_digest_changed':lambda a:a['source_slots'][0].__setitem__('observed_slot_digest','invalid'),
        'payload_bearing':lambda a:a['payload']['bearings'].__setitem__(0,42.),
        'payload_digest_changed':lambda a:a.__setitem__('payload_digest','invalid'),
    }
    missing=next((i for i,s in enumerate(row['assembled']['source_slots']) if s['outcome']=='MISSING'),None)
    if missing is not None:
        mutations.update({
            'missing_packet_invented':lambda a:a['source_slots'][missing].__setitem__('packet',deepcopy(a['source_slots'][0]['packet'])),
            'missing_relabelled_model':lambda a:a['source_slots'][missing].__setitem__('source','MODEL'),
            'missing_relabelled_valid':lambda a:a['source_slots'][missing].__setitem__('outcome','VALID'),
        })
    outcomes=[]
    for name,mutate in mutations.items():
        altered=deepcopy(row);mutate(altered['assembled']);calls={'sense':0,'before_sense':0}
        def forbid_sense(*args,**kwargs):
            calls['sense']+=1;raise AssertionError('Rejected assembly reached sensing')
        def before_sense(r):calls['before_sense']+=1
        try:_check_then_sense(altered,check,forbid_sense,before_sense)
        except AssertionError as error:reason=str(error)
        else:raise AssertionError('Malformed assembly accepted: '+name)
        if any(calls.values()):raise AssertionError('Malformed assembly reached dispatch: '+name)
        outcomes.append(dict(probe=name,rejected_before_wls=True,reason=reason,sense_calls=0))
    return dict(passed=True,probe_count=len(outcomes),probes=outcomes,real_wls_calls=0,control_steps=0)


def _run_real(check_id,I,sense_callback,out,check_assembled):
    from . import public,measurements
    from .execution import ActualMeasurementCache
    base=deepcopy(I['assembler_inputs']);slots=[public.seal_slot(s) for s in base['current_slots']]
    records=[];actual_attempts=0
    for call in I['calls']:
        actual=call['execution_route']=='actual_selected_left_assembler'
        if check_id=='S07' and actual:
            cache=ActualMeasurementCache('SHORT_SYNTHETIC')
            for s in slots:
                if s['state']!='UNQUERIED':
                    robot=s['slot_key']['robot_id'];profile=base['sensor_profiles'][robot]
                    cache.record_outcome(0,robot,20,_context(base['all_Uk_positions'][robot],profile['sigma'],profile['health']),
                                         dict(state=s['state'],packet=s['packet']))
            fixed=I['actual_sampler_only_outcomes'][0]
            p=base['sensor_profiles'][1]
            acquired=cache.query(0,1,20,_context(base['all_Uk_positions'][1],p['sigma'],p['health']),
                                 lambda:dict(state=fixed['state'],packet=deepcopy(fixed['packet'])))
            slots[1]=acquired;actual_attempts=len(cache.attempts)
            save_json(out/'actual_sampler_log.json',cache.snapshot())
        kwargs=dict(tick=base['tick'],target_id=base['target_id'],target_position=base['public_target_position'],
            positions=base['all_Uk_positions'],sensor_profiles=base['sensor_profiles'],current_slots=deepcopy(slots),
            team=_team(base['team']),stream_id=call['call_id'],actual=actual,
            traversal_robot_ids=call['assembly_traversal_robot_ids'])
        before=digest(kwargs);assembled=measurements.assemble_left_state(**kwargs)
        if digest(kwargs)!=before:raise AssertionError('Assembler changed supplied public inputs')
        registration=short_sensing_registration(check_id,call)
        row=dict(call_id=call['call_id'],assembler_module=measurements.__name__,assembler_function='assemble_left_state',
            assembler_input=deepcopy(kwargs),assembler_input_digest=before,assembled=deepcopy(assembled),registration=registration)
        # Persist evidence even if the independent pre-sensing check rejects it.
        save_json(out/(call['call_id']+'_assembled.json'),row)
        row['rejection_probes']=_pre_wls_rejection_probes(row,check_assembled)
        result=_check_then_sense(row,check_assembled,sense_callback,
                                lambda checked:save_json(out/(call['call_id']+'_before_sense.json'),checked))
        row['sensing_result']=result;records.append(row)
        save_json(out/(call['call_id']+'_result.json'),row)
    return dict(calls=records,assembler_calls=len(records),actual_sample_attempts=actual_attempts,
                real_wls_calls=len(records),start_records=sum(len(r['sensing_result']['estimate_result']['starts']) for r in records))


def _check_real(row,observed):
    E=row['expected'];oracles=E['fusion_oracles']
    for r in observed['calls']:
        cid=r['call_id'];assembly=r['assembled'];result=r['sensing_result'];quality=result['quality']
        _equal(r['pre_wls_check']['passed'],True,'pre-WLS conformance')
        _equal(r['pre_wls_check']['before_wls'],True,'pre-WLS ordering')
        _equal(quality['contributing_sensor_ids'],r['pre_wls_check']['contributing_sensor_ids'],'fusion contributors')
        _equal(quality['estimate'],oracles[cid]['point'],'analytic ray intersection',atol=1e-6)
        _equal(quality['status'],'PASS','quality status')
        if abs(result['estimate_result']['Q'])>1e-8:raise AssertionError('Ray-intersection objective exceeds frozen tolerance')
        if len(result['estimate_result']['starts'])!=9:raise AssertionError('All nine real start records required')
        independent=_quality_at(assembly['payload'],quality['estimate'])
        _equal(quality['J'],independent['J'],'J(xhat)',1e-10,1e-10)
        _equal(quality['I'],independent['I'],'I(xhat)',1e-9,1e-12)
        _equal(quality['radius_proxy'],independent['radius_proxy'],'r(xhat)',1e-12,1e-12)
        if quality['radius_proxy']>.06:raise AssertionError('Analytic probe failed exact quality threshold')
    if row['check_id']=='S05':
        a,b=observed['calls'];_equal(a['assembled']['payload'],b['assembled']['payload'],'reordered payload',0.)
    if row['check_id']=='S07':
        if observed['actual_sample_attempts']!=1:raise AssertionError('Actual packet must be sampled once')
        a,b=observed['calls']
        if a['sensing_result']['quality']['estimate']==b['sensing_result']['quality']['estimate']:
            raise AssertionError('Actual nonzero newly acquired packet was ignored')
    if row['check_id']=='S08':
        I=row['input'];r=observed['calls'][0];a=r['assembled']
        team=[[m['robot_id'],m['role']] for m in a['team']]
        _equal(team,I['occupied_team'],'observed occupied team')
        _equal([m[0] for m in team],E['occupied_robots'],'observed occupied robots')
        _equal(len(team),I['q'],'physical demand')
        end=I['artificial_following_endpoint'];start=a['tick']
        c=_clock(I['H_seconds'],team=team,tick=start,G=True,Q=r['sensing_result']['quality']['status'],
                 n=len(r['assembler_input']['positions']))
        p,done,_=c.advance(end['tick'],end['G'],end['Q'])
        occupied=float(Fraction(len(team)*(end['tick']-start),20))
        _equal(p,E['progress_seconds']);_equal(done,True);_equal(occupied,E['occupied_robot_seconds'])
        observed['artificial_clock']=dict(progress_seconds=p,occupied_robot_seconds=occupied,occupied_team=team,
            returned_geometric_G=a['G'],clock_left_G='ARTIFICIAL_TRUE',actual_G_not_claimed=True)
    _equal(observed['real_wls_calls'],row['real_wls_upper_bound'])
    _equal(observed['start_records'],row['local_start_upper_bound'])


def _base_assembly(I,team=None,slots=None,positions=None):
    from . import public,measurements
    pos=positions or I.get('positions') or [[8.6,10.],[8.,10.6],[7.4,10.]]
    rows=slots if slots is not None else I.get('slots',[])
    by={int(s['key']['stable_robot_id'][1:]):_slot(s) for s in rows}
    complete=[by.get(i) or public.seal_slot(dict(slot_key=dict(target_id=0,robot_id=i,tick=20),state='UNQUERIED',packet=None)) for i in range(len(pos))]
    return measurements.assemble_left_state(tick=20,target_id=0,target_position=I.get('public_target_position',[8.,10.]),
        positions=pos,sensor_profiles=[dict(sensor_id=f'U{i}',sigma=.02,health='available',observed_tick=20) for i in range(len(pos))],
        current_slots=complete,team=_team(team or [[0,'dual_neg45'],[1,'dual_pos45']]),stream_id='synthetic-zero',actual=False)


def _zero_case(number,I,events,out,fixture_root,manifest_reference=None):
    from . import public
    from .execution import ActualMeasurementCache,RequestJournal,BoundaryTransaction,apply_assignment_boundary
    from .evaluator import components,interval_stop,escape_precedes_endpoint,termination_reason
    if number==1:
        before=digest(I);calls=[_base_assembly(I,[[r,'dual_neg45' if k==0 else 'dual_pos45'] for k,r in enumerate(e['robots'])]) for e in events]
        return dict(actual_sample_attempts=sum(r['real_sampling_calls'] for r in calls),actual_cache_writes=0,
            actual_state_changes=int(digest(I)!=before),sources=[[s['source'] for s in r['source_slots']] for r in calls],
            slot_states_after=[r['state'] for r in I['slots']],candidate_progress_seconds=[0.]*len(calls),missing_count=0)
    if number==2:
        cache=ActualMeasurementCache('E0');outcomes=[];context=_context([8.6,10.])
        for _ in range(4):outcomes.append(cache.query(0,1,20,context,lambda:dict(state='MISSING',packet=None))['state'])
        saved=json.loads(json.dumps(cache.snapshot()));cache=ActualMeasurementCache('E0',saved)
        before=len(cache.attempts);outcomes.append(cache.query(0,1,20,context,lambda:(_ for _ in ()).throw(AssertionError('Resampled missing')))['state'])
        return dict(unique_sample_attempts=len(cache.attempts),cache_reuses=cache.reuses,state=cache.peek(0,1,20)['state'],new_packets=0,
            query_outcomes=outcomes,real_wls_calls=0,roundtrip=dict(same_physical_environment_id=cache.physical_environment_id=='E0',
            same_raw_key=cache.snapshot()['entries'][0]['raw_key']==['E0',0,1,20],missing_outcome_preserved=outcomes[-1]=='MISSING',new_sample_attempts_after_restore=len(cache.attempts)-before))
    if number==3:
        original=I['existing'];packet=original['packet'];context=_context(packet['position'],packet['sigma']);denied=[]
        for mutation in I['mutations']:
            cache=ActualMeasurementCache('E0');cache.record_outcome(0,0,20,context,dict(state='VALID',packet=packet))
            before=digest(cache.peek(0,0,20));outcome=dict(state='VALID',packet=deepcopy(packet));ctx=deepcopy(context)
            if mutation['field']=='state':outcome=dict(state=mutation['value'],packet=None)
            elif mutation['field']=='position':outcome['packet']['position']=mutation['value'];ctx['position']=mutation['value']
            else:outcome['packet'][mutation['field']]=mutation['value']
            denied.append(_reject(lambda:cache.record_outcome(0,0,20,ctx,outcome)))
            if digest(cache.peek(0,0,20))!=before:raise AssertionError('Conflict overwrote cached outcome')
        return dict(all_rejected=len(denied)==4,error_class='ContractError',original_slot_retained=True,actual_sample_attempts=0,commit_count=0,quality_fallback_forbidden=True)
    if number==4:
        cache=ActualMeasurementCache('E0');positions=[[8.6,10.],[8.,10.6],[7.4,10.]]
        for logical in I['slots']:
            if logical['state']!='UNQUERIED':
                r=int(logical['key']['stable_robot_id'][1:]);cache.record_outcome(0,r,20,_context(positions[r]),dict(state=logical['state'],packet=logical.get('packet')))
        old_missing=cache.peek(0,1,20);cache.query(0,0,20,_context(positions[0]),lambda:(_ for _ in ()).throw(AssertionError('Requery')))
        produced=I['U2_fixed_outcome'];cache.query(0,2,20,_context(positions[2]),lambda:dict(state='VALID',packet=produced['packet']))
        b=_boundary(_flat(I['old_assignment']),I['new_assignment'])
        return dict(new_sample_keys=[I['slots'][2]['key']],reused_keys=[I['slots'][0]['key']],untouched_keys=[I['slots'][1]['key']],
            sample_attempts=len(cache.attempts),assignment=b['actions'],new_segment_progress=b['clock_states']['0']['base'],
            changed_robots=[i for i,(a,z) in enumerate(zip(I['old_assignment'],b['actions'])) if a!=z],change_cost=b['change_cost'],
            positions_unchanged=b['positions']==_flat(I['old_assignment'])['positions'])
    if number==6:
        from research.information_service.public_quality import prepare_frame,assess_quality
        a=_base_assembly(I);p=prepare_frame(a['frame'],a['allowed_sensor_ids']);q=assess_quality(p['payload'],None)
        return dict(sources=[s['source'] for s in a['source_slots']],contributing_sensor_ids=p['payload']['sensor_ids'],valid_sensor_count=p['valid_sensor_count'],
            Q=q['status'],reason=q['reasons'][0],estimator_calls=0,sample_attempts=0,slot_U1_after=I['slots'][1]['state'],progress_seconds=0.)
    if number==10:
        r=_flat(I['assignment'],I['progress_seconds']);before=digest(r)
        b=_boundary(r,I['assignment']);b2=_boundary(r,I['assignment'])
        return dict(progress_seconds=b['clock_states']['0']['base'],segment=I['segment'],fusion_calls=len(b['needs_new_endpoint']),sample_attempts=0,
            interval_credits=0,change_cost=b['change_cost'],positions_unchanged=b['positions']==r['positions'] and digest(r)==before and b==b2)
    if number==11:
        from .execution import validate_boundary_request
        observations=[]
        for variant in I['variants']:
            c=_clock(I['H_seconds'],tick=20,Q=variant['actual_Q']);values={'20':c.state.progress}
            rejection=validate_boundary_request(tick=20,end_tick=120,checkpoint_id='C20',current_checkpoint_id='C20',expected_start_tick=20,boundary_committed_tick=20)
            if not rejection:raise AssertionError('Same-boundary reselection admitted')
            for endpoint in I['following_Q']:values[str(endpoint['tick'])]=c.advance(endpoint['tick'],True,endpoint['Q'])[0]
            observations.append((values,c.done))
        if observations[0]!=observations[1]:raise AssertionError('FAIL/UNKNOWN start difference')
        return dict(second_selection='REJECT',actual_assignment=I['chosen_assignment'],progress_by_tick=observations[0][0],actual_completed=observations[0][1],
            selection_count=1,completion_not_copied=not observations[0][1],occupied_robot_seconds=2*2*.05)
    if number==12:
        c=_clock(I['H_seconds'],I['previous_progress_seconds'],19);p,done,_=c.advance(20,True,'FAIL')
        return dict(progress_seen_by_observe=p,progress_seen_by_KEEP=p,completed=done,old_Q_reused=c.Q!='FAIL',interval_credit_at20=0.,occupation_retained=len(c.team)==2)
    if number==13:
        r=_flat(I['old_assignment'],I['old_progress_seconds'],positions=I['positions']);b=_boundary(r,I['new_assignment'])
        team=b['clock_states']['0']['team'];c=_clock(.5,0.,20,team=team);p=c.advance(21,True,'PASS')[0]
        return dict(old_segment_closed=bool(b['events']),new_segment_start_tick=20,progress_by_tick={'20':b['clock_states']['0']['base'],'21':p},
            change_count=b['assignment_changes'],change_cost=b['change_cost'],positions_at_commit=b['positions'],no_credit_before_tick20=b['boundary_elapsed_seconds']==0.)
    if number==14:
        from research.cooperative_sensing.estimator import NumericContractViolation
        original=dict(assignment=deepcopy(I['committed_assignment']),progress=deepcopy(I['committed_progress']),change_cost=I['committed_change_cost'])
        before=digest(original);cache=ActualMeasurementCache('E0');transaction=BoundaryTransaction(original)
        def prepare(draft):
            draft['assignment']=deepcopy(I['proposed_assignment']);draft['change_cost']+=.04
            for robot in (2,3):
                cache.query(0,robot,20,_context([8.,10.]),lambda robot=robot:dict(state='VALID',packet=dict(
                    sensor_id=f'U{robot}',position=[8.,10.],bearing=0.,sigma=.02,measurement_tick=20,available_tick=20,status='ok')))
            raise NumericContractViolation(I['failure_on_second_task'])
        _reject(lambda:transaction.prepare(prepare),(NumericContractViolation,))
        return dict(attempt_failed=True,assignment_retained=original['assignment'],progress_retained=original['progress'],change_cost_retained=original['change_cost'],
            partial_commits=int(digest(original)!=before),simulation_ticks_advanced=0,partial_occupancy_changes=0,
            first_task_sample_attempts_retained=len(cache.attempts),append_only_sample_cache_retained=len(cache.entries)==2,exception_not_Q_UNKNOWN=True)
    if number==15:
        journal=RequestJournal();responses=[]
        origin=journal.begin(I['request_id'],I['content_token'],now_wall=100.,timeout_seconds=10.);responses.append(origin['state'])
        for when in (103.,109.9):
            r=journal.begin(I['request_id'],I['content_token'],now_wall=when,timeout_seconds=10.)
            if r.get('state')!='IN_PROGRESS' or r.get('deadline_extended') or r.get('new_transaction_started'):
                raise AssertionError('Pending duplicate changed transaction/deadline')
            responses.append(r['state'])
        _reject(lambda:journal.check_deadline(110.),(ContractError,TimeoutError));responses.append('REQUEST_TIMEOUT')
        snap=journal.snapshot()
        return dict(deadline_wall=snap['inflight']['deadline_wall'],responses=responses,created_transactions=1,deadline_renewals=0,simulation_tick=20,change_cost=0.,successful_commits=len(snap['successful']),
                    journal_snapshot=snap)
    if number==16:
        from .model_worker import submit_action
        from .execution import OnlineEnvironment
        # Preserve the frozen logical fixture, adapting only its transport shape.
        # The cached payload is synthetic; no completed actual transaction is claimed.
        physical='S16-synthetic-physical-environment'
        payload=deepcopy(I['cached_content'])
        payload['contract_id']='gq_online_action_transaction_v1'
        payload['checkpoint_id']=digest(dict(synthetic_logical_checkpoint=payload['checkpoint_id']))
        envelope=dict(message_kind='action_request',operation=dict(
            physical_environment_id=physical,request_id=I['request_id']),payload=payload)
        fingerprint=digest(dict(physical_environment_id=physical,checkpoint_id=payload['checkpoint_id'],
            expected_start_tick=payload['expected_start_tick'],assignment=payload['assignment']))
        journal=RequestJournal();journal.begin(I['request_id'],fingerprint)
        journal.commit(deepcopy(I['cached_result']))
        prior_attempts=[dict(synthetic_prior_attempt=i) for i in range(I['actual_cache_attempts_so_far'])]
        stored=dict(journal=journal.snapshot(),state=dict(tick=I['current_tick'],
            change_cost=I['current_total_change_cost'],assignment=deepcopy(I['cached_content']['assignment']),
            charged_once_marker=I['current_total_change_cost']==I['cached_result']['change_cost']),
            sampler_attempts=prior_attempts)
        restored=json.loads(json.dumps(stored,allow_nan=False))
        if restored!=stored:raise AssertionError('S16 declared prior ledger did not roundtrip exactly')
        forbidden_names=('observe_public','current_state_read','current_checkpoint_read',
            'prepare_boundary','prepare_boundary_state','sample','sampling_cache_query',
            'sampling_cache_record_outcome','sampling_cache_read','fusion','sense_callback',
            'controller_steps','checkpoint_commit','state_commit','journal_begin',
            'journal_commit','journal_abort','on_commit')
        forbidden={name:0 for name in forbidden_names}
        calls=dict(rpc_entry=0,replay=0,conflict=0,journal_lookup=0)
        active={'value':False}
        def fail_on_call(name):
            def forbidden_call(*args,**kwargs):
                forbidden[name]+=1
                raise AssertionError('Successful/conflicting replay reached forbidden path: '+name)
            return forbidden_call
        class GuardedState(dict):
            def __init__(self,value,read_counter):
                dict.__init__(self,value);self.read_counter=read_counter
            def _read(self):
                if active['value']:fail_on_call(self.read_counter)()
            def __getitem__(self,key):
                self._read();return dict.__getitem__(self,key)
            def get(self,*args):
                self._read();return dict.get(self,*args)
            def items(self):
                self._read();return dict.items(self)
            def keys(self):
                self._read();return dict.keys(self)
            def values(self):
                self._read();return dict.values(self)
            def __iter__(self):
                self._read();return dict.__iter__(self)
            def __setitem__(self,key,value):
                if active['value']:fail_on_call('state_commit')()
                return dict.__setitem__(self,key,value)
        # Use the actual production class and its unchanged bound step method.
        # No constructor/control/physics is needed for an already-cached replay.
        env=object.__new__(OnlineEnvironment)
        env.physical_environment_id=physical
        env.journal=RequestJournal(restored['journal'])
        env._state=GuardedState(restored['state'],'current_state_read')
        env._last_checkpoint=GuardedState(dict(
            checkpoint_id=digest(dict(synthetic_current_tick=I['current_tick'])),
            tick=I['current_tick']),'current_checkpoint_read')
        env.failed=False;env.end_tick=I['current_tick']+20
        env._boundary_committed_tick=I['current_tick'];env.work_identity='S16-zero-controller'
        env.frames=[];env.fusions=[];env.action_commits=[]
        env.sampler=SimpleNamespace(attempts=deepcopy(restored['sampler_attempts']))
        for attribute,counter in (
            ('observe_public','observe_public'),('_prepare_boundary','prepare_boundary'),
            ('_prepare_boundary_state','prepare_boundary_state'),('_sample','sample'),
            ('_fuse','fusion'),('sense_callback','sense_callback'),
            ('_advance_tick','controller_steps'),('_checkpoint','checkpoint_commit')):
            setattr(env,attribute,fail_on_call(counter))
        for attribute,counter in (('query','sampling_cache_query'),
                ('record_outcome','sampling_cache_record_outcome'),('peek','sampling_cache_read'),('get','sampling_cache_read')):
            setattr(env.sampler,attribute,fail_on_call(counter))
        real_lookup=env.journal.lookup
        def counted_lookup(request_id,content_fingerprint):
            calls['journal_lookup']+=1
            return real_lookup(request_id,content_fingerprint)
        env.journal.lookup=counted_lookup
        for attribute,counter in (('begin','journal_begin'),('commit','journal_commit'),('abort','journal_abort')):
            setattr(env.journal,attribute,fail_on_call(counter))
        step_is_production=getattr(env.step,'__func__',None) is OnlineEnvironment.step
        if not step_is_production:raise AssertionError('S16 must call the production OnlineEnvironment.step')
        def ledger():
            return dict(state=dict(env._state),journal=env.journal.snapshot(),
                sampler_attempts=deepcopy(env.sampler.attempts),frames=deepcopy(env.frames),
                fusions=deepcopy(env.fusions),action_commits=deepcopy(env.action_commits),
                work_identity=env.work_identity,boundary_committed_tick=env._boundary_committed_tick,
                failed=env.failed,current_checkpoint=dict(env._last_checkpoint))
        before=ledger();before_digest=digest(before);before_attempts=len(env.sampler.attempts)
        on_commit=fail_on_call('on_commit')
        def invoke(value,kind):
            calls['rpc_entry']+=1;calls[kind]+=1;active['value']=True
            try:
                return submit_action(env,value,work_identity='S16-zero-controller',on_commit=on_commit)
            finally:active['value']=False
        first=invoke(deepcopy(envelope),'replay')
        expected_replay=dict(deepcopy(I['cached_result']),replayed=True)
        if first!=expected_replay or first.get('replayed') is not True:
            raise AssertionError('Production step did not return the unchanged cached payload plus replayed=True')
        first_record=deepcopy(first)
        # Caller mutation must not change the successful cache or its old charge.
        first['change_cost']=-1.;first['caller_mutation']='must_not_reach_cache'
        cache_after_caller_mutation=env.journal.snapshot()
        bad=deepcopy(envelope)
        changed=next(e['assignment'] for e in events if e['op']=='replay_same_id_changed_assignment')
        bad['payload']['assignment']=deepcopy(changed)
        conflict=invoke(bad,'conflict')
        expected_conflict=dict(contract_id='gq_online_action_transaction_v1',status='REJECTED',
            reason='REQUEST_ID_CONFLICT',committed_assignment_or_fees_changed=False,new_sampling_attempts=0)
        if conflict!=expected_conflict:raise AssertionError('Production conflict response shape/reason differs')
        second=invoke(deepcopy(envelope),'replay')
        if second!=expected_replay or second.get('replayed') is not True:
            raise AssertionError('Repeated production replay lost its immutable cached payload')
        after=ledger();unchanged=digest(after)==before_digest
        cache_preserved=(cache_after_caller_mutation==before['journal']==after['journal'])
        measured_samples=(len(env.sampler.attempts)-before_attempts)+forbidden['sample']+forbidden['sampling_cache_query']
        measured_fusions=(len(env.fusions)-len(before['fusions']))+forbidden['fusion']+forbidden['sense_callback']
        measured_commits=(len(env.action_commits)-len(before['action_commits']))+forbidden['journal_commit']+forbidden['checkpoint_commit']+forbidden['state_commit']+forbidden['on_commit']
        if (any(forbidden.values()) or calls!=dict(rpc_entry=3,replay=2,conflict=1,journal_lookup=3)
                or not unchanged or not cache_preserved):
            raise AssertionError('Production RPC replay observed current state, created work, or changed prior ledger')
        # The frozen oracle names a logical ContractError category. The real API
        # returns the REJECTED mapping above; do not misreport an actual exception.
        logical_error=type(ContractError(conflict['reason'])).__name__
        roundtrip=dict(
            successful_request_id_and_content_preserved=(I['request_id'] in after['journal']['successful'] and
                after['journal']['successful'][I['request_id']]['fingerprint']==fingerprint),
            cached_result_preserved=after['journal']['successful'][I['request_id']]['result']==I['cached_result'],
            charged_once_marker_preserved=(after['state']['charged_once_marker'] is True and
                after['state']['change_cost']==before['state']['change_cost']==I['current_total_change_cost']))
        return dict(first_returns_cached_result=first_record==expected_replay,second_error=logical_error,
            new_samples=measured_samples,new_fusions=measured_fusions,new_commits=measured_commits,
            tick_after=after['state']['tick'],total_change_cost=after['state']['change_cost'],roundtrip=roundtrip,
            production_replay_coverage=dict(production_step_exercised=step_is_production and calls['journal_lookup']==3,
                production_replay_flag=first_record.get('replayed') is True and second.get('replayed') is True,
                cached_result_deepcopy_preserved=cache_preserved and second==expected_replay,
                replay_calls=calls['replay'],conflict_calls=calls['conflict'],journal_lookup_calls=calls['journal_lookup'],
                forbidden_call_counts=forbidden,ledger_unchanged=unchanged),
            rpc_entry_seam=dict(function='model_worker.submit_action -> OnlineEnvironment.step',
                actual_replay_result=first_record,actual_second_replay_result=second,actual_conflict_result=conflict,
                calls=calls,prior_ledger_digest=before_digest,final_ledger_digest=digest(after),
                current_state_observer='fail_on_call',logical_checkpoint_to_schema_adapter=payload['checkpoint_id'],
                payload_contract_id=payload['contract_id'],
                cached_payload_scope='frozen synthetic cached_result fixture; not a completed actual/main transaction',
                logical_error_scope='ContractError is the frozen oracle category; production returned the recorded REJECTED mapping'))
    if number==17:
        from .execution import validate_boundary_request
        idle=[dict(target=None,role='none') for _ in range(I['n_robots'])];r=_flat(idle,targets=[dict(id=j,required_robots=q) for j,q in [(0,2),(1,2)]])
        for variant in I['variants']:
            if 'assignment' in variant:_reject(lambda:_boundary(r,variant['assignment']))
            else:
                rejected=validate_boundary_request(tick=20,end_tick=120,checkpoint_id=variant['checkpoint'],current_checkpoint_id='C20',
                    boundary_committed_tick=None,expected_start_tick=variant['start_tick'])
                if not rejected:raise AssertionError('Stale/wrong boundary admitted')
        return dict(all_rejected=True,commit_count=0,actual_sample_attempts=0,new_change_cost=0.,original_state_unchanged=r['assignment']==idle)
    if number==18:
        initial=I['assignment'];idle=[dict(target=None,role='none') for _ in initial]
        request=_flat(initial,I['progress_seconds']);withdraw=_boundary(request,idle)
        state=dict(assignment=deepcopy(initial),changes=0,change_cost=0.)
        a=apply_assignment_boundary(state,idle,I['change_cost'])
        resumed=_boundary(_flat(idle,0.,40),initial);b=apply_assignment_boundary(state,initial,I['change_cost'])
        target=dict(I['task']);target['required_robots']=2;target['service_duration']=target.pop('H')
        cfg=asdict(_cfg(3,I['task_count']));comp=components(cfg,target,1.,2.,False,0.,2.)
        raw_flow=target['weight']*(2.-1.);raw_late=target['weight']*(2.-max(1.,target['deadline']))
        synthetic=dict(task=target,closed=[withdraw],new=[resumed],state=state,flow=raw_flow,late=raw_late)
        restored=json.loads(json.dumps(synthetic));_equal(restored,synthetic)
        p=resumed['clock_states']['0']['base']
        return dict(task_id=target['id'],task_birth=target['birth'],task_deadline=target['deadline'],task_status='active',new_progress_seconds=p,
            closed_segments=len(withdraw['events']),new_segments=len(resumed['needs_new_endpoint']),changes=[a['assignment_changes'],b['assignment_changes']],
            change_cost=state['change_cost'],raw_flow=raw_flow,raw_late=raw_late,flow_component=comp['flow'],late_component=comp['late'],
            idle_robot_seconds_in_gap=3.,occupied_robot_seconds_in_gap=0.,roundtrip=dict(lifecycle_and_segment_links_preserved=restored==synthetic,
                progress_seconds=restored['new'][0]['clock_states']['0']['base'],raw_flow=restored['flow'],raw_late=restored['late'],
                change_cost=restored['state']['change_cost'],extra_charges_on_restore=0.,discarded_progress_not_restored=p==0.))
    if number==19:
        results={}
        for route in events:
            state=dict(assignment=deepcopy(route['initial_assignment']),changes=0,change_cost=0.)
            for transition in route['transitions']:apply_assignment_boundary(state,transition['after'],I['change_cost'])
            results[route['variant']]=dict(change_count=state['changes'],change_cost=state['change_cost'])
        results['direct']['changed_robots']=[i for i,(a,b) in enumerate(zip(I['first'],I['last'])) if a!=b]
        transition=_boundary(_flat(I['first'],.4,targets=[dict(id=0,required_robots=2),dict(id=1,required_robots=2)]),I['last'])
        results['old_progress_recoverable']=transition['clock_states']['1']['base']>0
        return results
    if number==20:
        from .interface_checks import synthetic_checkpoint
        cp=synthetic_checkpoint(kind='short_S20',tick=100)
        restored=json.loads(json.dumps(cp));_equal(restored,cp)
        authority=public.HistoryAuthority.from_public_binding(public.binding_from_checkpoint(cp))
        normalized=public.validate_checkpoint(restored,authority=authority)
        values={};first={}
        for h in normalized['task_histories']:
            segment=next(s for s in h['segments'] if s['segment_id']==h['active_segment_id'])
            values[str(h['target_id'])]=public.clock_progress(segment['latest_clock'])
            first[str(h['target_id'])]=segment['start_tick']
        return dict(progress_by_target=values,first_possible_measurement_tick=first,target1_tick0_required=first['1']==0,
            history_cross_contamination=values['0']==values['1'],source_binding_required=True,
            roundtrip=dict(checkpoint_tick=normalized['tick'],canonical_public_checkpoint_bytes_equal=digest(normalized)==digest(cp),
                both_segment_histories_preserved=restored['task_histories']==cp['task_histories'],source_binding_retained=True,fusion_or_sampling_during_restore=0))
    if number==21:
        from .execution import release_assignment
        c=_clock(I['H_seconds']);completion=None
        for e in I['artificial_endpoints'][1:]:
            _,done,_=c.advance(e['tick'],e['G'],e['Q'])
            if done:completion=e['tick'];break
        duration=(completion-I['start_tick'])*.05;occupied=sum(a['target'] is not None for a in I['assignment'])
        energy=math.fsum(I['constant_powers'])*duration;span=(I['next_decision_tick']-I['start_tick'])*.05
        released,_=release_assignment(I['assignment'],0)
        return dict(completion_tick=completion,completion_events=int(completion is not None),release_tick=completion,
            new_decision_ticks=[I['next_decision_tick']],assignment_at22=released,
            occupied_robot_seconds=occupied*duration,control_integral=energy,idle_robot_seconds_to40=I['n_robots']*span-occupied*duration,
            automatic_release_change_cost=0.)
    if number==22:
        c=_clock(I['H_seconds'],tick=0);c.advance(1,True,'PASS')
        stop=interval_stop(.05,.1,I['escape_time']);escaped=escape_precedes_endpoint(I['escape_time'],.1)
        dt=Fraction(str(I['escape_time']));energy=sum(Fraction(str(v)) for v in I['constant_powers'])*dt
        return dict(completed=c.done,escaped=escaped,escape_events=int(escaped),last_full_credited_endpoint=c.tick,
            credited_service_before_escape=c.state.progress,no_endpoint2_measurement=escaped,occupied_robot_seconds=float(len(I['occupied'])*dt),
            control_integral=float(energy),raw_flow=float(I['weight']*dt),raw_late=float(dt-Fraction(str(I['deadline']))),no_post_escape_task_cost=stop==I['escape_time'])
    if number==23:
        from .execution import release_assignment
        c=_clock(I['H_seconds'],I['progress_at_tick1'],tick=1)
        escaped=escape_precedes_endpoint(I['escape_time'],.1)
        if not escaped:c.advance(2,True,'PASS')
        actions=[dict(target=0,role=role) for role in ('dual_neg45','dual_pos45')]+[dict(target=None,role='none')]
        _,released=release_assignment(actions,0)
        return dict(status=termination_reason(c.done,escaped,.1,6.),completion_events=int(c.done),escape_events=int(escaped),release_events=int(bool(released)),
            completion_reward=0.,endpoint2_wls_calls=0,terminal_unfinished_eligibility=not c.done)
    if number==24:
        from .execution import settle_terminal_once
        t0,t1=I['tasks'];c=_clock(t0['H'],t0['progress_at59'],59,n=I['n_robots']);c.advance(60,True,'PASS')
        cfg=asdict(_cfg(I['n_robots'],I['task_count'],max_stages=1));statuses=['completed' if c.done else 'active',t1['status_at59']]
        terminal=math.fsum(components(cfg,dict(id=t['id'],weight=t['weight'],birth=0.,deadline=3.),3.,3.,statuses[i]=='completed',0.,3.)['terminal'] for i,t in enumerate(I['tasks']))
        settled=dict(terminal_settled=False,statuses=statuses,components={'terminal':0.});count=0;deltas=[]
        for _ in range(2):
            was_settled=settled['terminal_settled'];deltas.append(settle_terminal_once(settled,cfg,[t['weight'] for t in I['tasks']]))
            count+=int(not was_settled and settled['terminal_settled'])
        return dict(statuses=statuses,completion_events=int(c.done),terminal_settlements=count,terminal_component=settled['components']['terminal'],
            decision_calls_at_T=0,automatic_release_change_cost=0.,repeated_terminal_extra_cost=deltas[-1])
    if number==25:
        from .execution import collect_interval_events,legal_decision_ticks
        active=[x['target'] for x in I['declared_births'] if x['birth_tick']<=60]
        projected=[dict(kind={'completed':'COMPLETED','escaped':'ESCAPED','born':'BIRTH'}[e['type']],
            at=dict(time_seconds=e['tick']*.05,event_tick=e['tick']),target_id=e['target']) for e in I['separate_event_collection_fixture']]
        ended,new=collect_interval_events(projected,20,40)
        times=events[-1]['current_times'];ends=[min(I['T'],t+events[-1]['prediction_seconds']) for t in times]
        ticks=legal_decision_ticks(0,60,20)
        return dict(assignments_at_empty_decisions=[deepcopy(I['assignment']) for _ in ticks],active_at60=active,first_target0_service_credit=0.,
            interval_ended_ids=ended,interval_new_ids=new,forecast_end_times=ends,prediction_terminal_included=[t==I['T'] for t in ends])
    if number==26:
        lo,hi=I['actual_interval'];dt=Fraction(str(hi))-Fraction(str(lo));energy=sum(Fraction(str(v)) for v in I['constant_powers'])*dt
        cfg=asdict(_cfg(I['n_robots'],I['task_count']));target=dict(id=0,weight=I['task_weight'],birth=0.,deadline=I['deadline'])
        comp=components(cfg,target,lo,hi,I['completion'],float(energy),hi)
        change=I['actual_change_count']*I['change_cost'];net=math.fsum(comp.values())-change
        return dict(raw_flow=float(dt*I['task_weight']),raw_late=float((Fraction(str(hi))-Fraction(str(max(lo,I['deadline']))))*I['task_weight']),
            control_integral=float(energy),occupied_robot_seconds=float(len(I['occupied'])*dt),idle_robot_seconds=float((I['n_robots']-len(I['occupied']))*dt),
            flow_component=comp['flow'],late_component=comp['late'],effort_reference=cfg['robots']*cfg['stage_dt']*cfg['control_reference']**2,
            effort_component=comp['effort'],terminal_component=comp['terminal'],change_component=-change,net_O=net,prediction_J_contribution=0.)
    if number==27:
        from pursuit_v2.types import Assignment
        from research.quality_allocation.certified_solver import solve,units
        from research.quality_allocation.candidates import actions_from
        specs=[SimpleNamespace(**s) for s in I['specs']]
        obs=SimpleNamespace(config=SimpleNamespace(change_cost=I['change_cost']),assignment=[Assignment(**a) for a in I['assignment']])
        picked,score=solve(obs,specs,I['values']);actions=[a.to_dict() for a in actions_from(specs,picked,I['n_robots'])]
        v=I['second_variant'];obs2=SimpleNamespace(config=obs.config,assignment=[Assignment(**a) for a in v['assignment']])
        picked2,score2=solve(obs2,[SimpleNamespace(**s) for s in v['specs']],v['values'])
        if score!=units(1.)-2*units(.01):raise AssertionError('Exact dyadic tie objective changed')
        return dict(first_selected_indices=list(picked),first_mask=specs[picked[0]].mask,first_assignment=actions,
            first_objective_expression='units(1.0)-2*units(0.01)',second_selected_indices=list(picked2),second_objective=float(score2/(1<<1074)),
            reason='KEEP raw v=0 has positive profit relative to charged all-IDLE; no added tie preference')
    if number==28:
        from pursuit_v2.types import Assignment
        from research.quality_allocation.certified_solver import solve
        from .selection import restore_canonical_table
        from .adapter import legacy_spec
        from .common import CONTRACT_ID
        request_id=I['identity_fixture']['request_identity'];world_id=I['identity_fixture']['world_identity']
        descriptors=[]
        for spec in I['canonical_specs']:
            key={name:deepcopy(spec[name]) for name in ('target','robots','roles')}
            descriptors.append(dict(message_kind='candidate_descriptor',index=spec['index'],key=key,
                resource_mask=spec['mask'],evaluation_request_id=request_id,world_id=world_id,
                candidate_id=digest(dict(evaluation_request_id=request_id,world_id=world_id,key=key))))
        # This declared toy catalog exercises the production table interface;
        # it never gains actual-history authority or claims physical enumeration.
        manifest=dict(payload=dict(checkpoint=dict(tick=I['start_tick']),prediction_end_tick=I['end_tick']),
            request_identity=request_id,world_identity=world_id,candidate_count=len(descriptors),candidates=descriptors)
        calls=[]
        def restore(results,label):
            calls.append(dict(label=label,input_digest=digest(results),status='ENTERED'))
            try:value=restore_canonical_table(manifest,results)
            except ContractError as error:
                calls[-1].update(status='REJECTED',error=str(error));raise
            calls[-1].update(status='RETURNED',output_digest=digest(value));return value
        def exercise(values,label):
            results=[]
            for descriptor,value in zip(descriptors,values):
                spec=legacy_spec(descriptor);j=spec['target'];value=float(value)
                results.append(dict(kind='candidate_evaluation',execution_contract_id=CONTRACT_ID,mode='GQ',
                    request_identity=request_id,world_identity=world_id,candidate_identity=spec['candidate_identity'],
                    candidate=spec,start_tick=I['start_tick'],end_tick=I['end_tick'],
                    per_target={str(j):dict(target=j,selected_team=[[i,r] for i,r in zip(spec['robots'],spec['roles'])],
                        absolute_O=value,baseline=0.,v=value)},synthetic_fixture=True))
            tables=[];choices=[]
            for run,order in enumerate(I['evaluation_orders']):
                if sorted(order)!=list(range(len(results))):raise AssertionError('S28 order is not a permutation')
                emitted=[deepcopy(results[i]) for i in order];restored=restore(emitted,f'{label}:order{run}')
                rows=[]
                for spec,table_row,value in zip(restored['specs'],restored['table'],restored['values']):
                    if (digest(table_row['key'])!=digest(spec['structural_key']) or
                            table_row['index']!=spec['index'] or table_row['candidate_id']!=spec['candidate_identity'] or
                            value!=table_row['v']):raise AssertionError('S28 restored identity/value views disagree')
                    rows.append(dict(index=table_row['index'],**deepcopy(table_row['key']),mask=spec['mask'],v=table_row['v'],
                        candidate_identity=table_row['candidate_id'],request_identity=spec['request_identity'],world_identity=spec['world_identity']))
                if len(rows)!=len(results) or restored['B64']!=0.:raise AssertionError('S28 toy table coverage/baseline differs')
                tables.append(rows)
                obs=SimpleNamespace(config=SimpleNamespace(robots=I['n_robots'],change_cost=I['change_cost']),
                                    assignment=[Assignment(**a) for a in I['assignment']])
                choices.append(list(solve(obs,[SimpleNamespace(**s) for s in restored['specs']],restored['values'])[0]))
            if any(digest(t)!=digest(tables[0]) for t in tables):raise AssertionError('S28 restored rows depend on arrival order')
            rejected=[]
            for variant in I['negative_variants']:
                altered=deepcopy(results);i=variant['row']
                if variant.get('operation')=='append_copy':altered.append(deepcopy(altered[i]))
                elif variant.get('operation')=='remove':altered.pop(i)
                else:
                    node=altered[i]
                    for field in variant['path'][:-1]:node=node[field]
                    node[variant['path'][-1]]=deepcopy(variant['value'])
                _reject(lambda:restore(altered,f"{label}:negative:{variant['name']}"),(ContractError,))
                rejected.append(variant['name'])
            return dict(canonical_rows=tables[0],canonical_rows_by_order=tables,
                        selected_indices_by_run=choices,rejected_variants=rejected)
        non_equal=exercise(I['canonical_values'],'non_equal');equal=exercise(I['equal_value_case'],'equal')
        observed=dict(production_helper='selection.restore_canonical_table',**non_equal,equal_value_case=equal,
            does_not_test_hidden_future=True,scope=I['responsibility']['scope'],restoration_calls=calls,
            physical_candidate_enumeration_claimed=False,model_or_wls_execution_claimed=False)
        save_json(out/'production_table_restoration.json',observed)
        return observed
    if number==29:
        from .runtime import RoleAccessGuard,read_compact_manifest,serialized_message_size
        if fixture_root is None:raise ContractError('S29 needs sealed real fixture files')
        base=Path(fixture_root)/'S29';manifest=base/'manifest.json'
        if not isinstance(manifest_reference,dict) or set(manifest_reference)!={'path','sha256','input_root'}:
            raise ContractError('S29 requires the externally pinned manifest reference from the sealed job')
        reference=deepcopy(manifest_reference)
        if (Path(reference['path']).resolve()!=manifest.resolve() or
                Path(reference['input_root']).resolve()!=base.resolve()):
            raise ContractError('S29 manifest path/input root differs from its fixed fixture directory')
        entries=read_compact_manifest(reference)
        guard=RoleAccessGuard('predictor',Path(__file__).resolve().parents[2],out/'guarded_output',read_files=[manifest])
        with guard:
            admitted=guard.admit_manifest(reference)
            for entry in admitted:
                if hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()!=entry['sha256']:raise AssertionError('S29 actual file hash')
            for probe in I['forbidden_reads']:
                anchor=base/'needed' if probe['base'].endswith('/needed') else base
                _reject(lambda anchor=anchor,probe=probe:(anchor/probe['path']).read_bytes(),(AccessDenied,))
        raw='x'*I['exact_boundary_payload_recipe']['repeat'];exact=serialized_message_size(raw)
        oversize='x'*I['oversize_payload_recipe']['repeat'];oversize_len=len(json.dumps(oversize).encode())
        _reject(lambda:serialized_message_size(oversize))
        return dict(exact_boundary_payload_bytes=exact,exact_boundary_framing_admitted=exact==2097152,oversize_payload_bytes=oversize_len,
            oversize_rejected_before_enqueue=True,oversize_bytes_sent=0,application_schema_validation_still_required=True,
            allowed_input_file_count=len(entries),unlisted_reads_denied=True,symlink_realpath_checked=True,model_reruns=0,real_wls_calls=0)
    if number==30:
        from .interface_checks import run_short_history_admission
        return run_short_history_admission(I)
    raise ContractError(f'No actual short-check implementation for S{number:02d}')


def run_checks(short_file,check_ids,out,sense_callback,fixture_root=None,*,manifest_reference=None):
    from .admission import forbid_solver_calls
    document=read_json(short_file);catalog={r['check_id']:r for r in document['checks']}
    if (not isinstance(check_ids,list) or not 1<=len(check_ids)<=5 or len(check_ids)!=len(set(check_ids))
            or any(i not in catalog for i in check_ids)):
        raise ContractError('One declared short batch contains one to five unique check IDs')
    out=Path(out);out.mkdir(parents=True,exist_ok=True);results=[];real=starts=0
    for check_id in check_ids:
        row=catalog[check_id];folder=out/check_id;folder.mkdir(exist_ok=False)
        I,events=deepcopy(row['input']),deepcopy(row['events']);before=digest(dict(input=I,events=events))
        if before!=row['input_events_sha256']:raise ContractError('Frozen short input/events fingerprint differs')
        if row['real_wls_upper_bound']:
            observed=_run_real(check_id,I,sense_callback,folder,
                               lambda generated:_check_assembled(row['expected'],I,generated))
            save_json(folder/'observed_before_comparison.json',observed)
            _check_real(row,observed);real+=observed['real_wls_calls'];starts+=observed['start_records']
            comparison='actual production assembler, exact expected frame, analytic point, independently recomputed quality at actual xhat'
        else:
            with forbid_solver_calls() as counts:
                observed=_zero_case(int(check_id[1:]),I,events,folder,fixture_root,manifest_reference=manifest_reference)
                if any(counts.values()):raise AssertionError('Zero-WLS short case entered a solver')
            save_json(folder/'observed_before_comparison.json',observed)
            # S28 restores predeclared binary64 values, with no integration or
            # estimation error allowance: identity/value rows are exact.
            _equal(observed,row['expected'],check_id,atol=0. if check_id=='S28' else 1e-12)
            observed['solver_sentinel_counts']=counts;comparison='production seam result versus frozen expected; no control rollout'
        if digest(dict(input=I,events=events))!=before:raise AssertionError('Short fixture inputs mutated')
        save_json(folder/'observed_after_comparison.json',observed)
        result=dict(check_id=check_id,passed=True,real_wls_calls=row['real_wls_upper_bound'],
                    local_start_records=row['local_start_upper_bound'],comparison=comparison,synthetic_not_actual_history=True)
        save_json(folder/'result.json',result);results.append(result)
    result=dict(passed=True,checks=results,real_wls_calls=real,local_start_records=starts,
                actual_control_rollouts=0,scope='frozen short inputs only; no reliability/performance claim')
    save_json(out/'result.json',result)
    return result
