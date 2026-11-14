"""Private zero-WLS interface gates and explicitly synthetic test inputs.
These fabricated clocks are never main-episode history or a real execution claim.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from . import public
from .common import ContractError, DT, digest, save_json

UNIT_SOURCE = {'config': {'robots': 3, 'task_count': 1, 'side': 20.0, 'stage_dt': 3.0, 'capture_check': 2.8, 'step_dt': 0.05, 'max_stages': 2, 'prediction_stages': 1, 'max_plan_age': 3, 'max_speed': 3.0, 'travel_gain': 1.0, 'capture_radius': 0.3, 'anchor_offset': 0.6, 'time_gain': 2.0, 'singularity_epsilon': 0.02, 'hold_gain': 2.0, 'target_speed_min': 0.4, 'target_speed_max': 0.8, 'turn_interval': 1.0, 'turn_max_angle': 0.5, 'turn_hold_ticks': 1, 'speed_delta_max': 0.0, 'motion_model': 'continuous_turn', 'risk_samples': 8, 'risk_trigger_samples': 2, 'risk_prediction_dt': 0.05, 'risk_threshold': 0.65, 'local_substitutes': 2, 'initial_fraction': 0.6, 'two_robot_probability': 0.4, 'flow_weight': 0.1, 'late_weight': 0.3, 'control_weight': 0.02, 'unfinished_weight': 2.0, 'control_reference': 10.0, 'change_cost': 0.01, 'capture_mode': 'stepwise_service', 'geometry_mode': 'angular_standoff_v1', 'observation_radius': 0.6, 'observation_tolerance': 0.15}, 'positions_initial': [[8.224264068711928, 9.575735931288072], [8.224264068711928, 10.424264068711928], [2.0, 2.0]], 'targets': [{'id': 0, 'birth': 0.0, 'position_at_birth': [8.0, 10.0], 'velocity': [0.4, 0.0], 'required_robots': 2, 'weight': 1.0, 'deadline': 2.0, 'turns': [], 'turn_increment': 0.0, 'arc_rates': [[6.0, 0.0]], 'service_duration': 1.05}], 'initial_assignment': [{'target': None, 'role': 'none'}, {'target': None, 'role': 'none'}, {'target': None, 'role': 'none'}], 'sensor_declaration_schedule': [{'effective_tick': 0, 'profiles': [{'sensor_id': 'U0', 'sigma': 0.02, 'health': 'available'}, {'sensor_id': 'U1', 'sigma': 0.02, 'health': 'available'}, {'sensor_id': 'U2', 'sigma': 0.02, 'health': 'available'}]}], 'measurement_model': {'kind': 'planar_bearing', 'bearing_units': 'radian', 'perturbation_source_id': 'main_zero_angle_by_raw_key_v1', 'angle_perturbation': 0.0, 'draw_rule': 'constant zero per physical-environment/target/Uk/tick; no RNG or query-order counter', 'public_search_domain': [[0.0, 0.0], [20.0, 20.0]], 'position_units': 'model coordinates; no physical metre claim'}}


def _event(index,target,kind,tick,segment=None,before=0.,after=0.,reason=None):
    return {'event_index':index,'kind':kind,'target_id':target,'at':{'time_seconds':tick*DT,'event_tick':tick},
            'segment_id':segment,'progress_before':float(before),'progress_after':float(after),
            'reasons':[reason or ('BIRTH' if kind=='BIRTH' else 'INITIAL_ASSIGNMENT')]}


def _point(target,tick,team,slots,G=True,Q='PASS'):
    chosen=[next(s for s in slots if s['slot_key']=={'target_id':target,'robot_id':m['robot_id'],'tick':tick}) for m in team]
    packets=[s['packet'] for s in chosen if s['state']=='VALID']
    payload={'sensor_ids':[p['sensor_id'] for p in packets],'positions':[p['position'] for p in packets],
       'bearings':[p['bearing'] for p in packets],'sigmas':[p['sigma'] for p in packets],'domain':[[0.,0.],[20.,20.]]}
    return public.seal_endpoint({'target_id':target,'tick':tick,'team':team,'G':G,
      'quality':{'contract_id':public.IDS['quality'],'status':Q,'payload_digest':digest(payload),
                 'radius_proxy':None if Q=='UNKNOWN' else .03 if Q=='PASS' else .1},
      'slots':[{'slot_key':s['slot_key'],'slot_digest':s['slot_digest'],'state':s['state']} for s in chosen]})


def _segment(target,index,start,team,cut,slots,intervals,*,previous=None,opened='INITIAL_ASSIGNMENT',events=None,closure=None,Q='PASS',G=True):
    core={'target_id':target,'segment_index':index,'previous_segment_id':previous,'start_tick':start,'team':team,'opened_by':opened}
    core['segment_id']=public.segment_identity(core)
    return public.seal_segment(core|{'initial_clock':{'base':0.,'intervals':0,'team':deepcopy(team)},
      'latest_clock':{'base':0.,'intervals':intervals,'team':deepcopy(team)},
      'latest_endpoint':_point(target,cut,team,slots,G,Q),'events':events or [],'closure':closure})


def synthetic_checkpoint(kind='two_task',tick=None):
    """Fixed artificial state; use only test authority/unit_only, not main input.

    short_S20 exactly encodes the declared current .25/.10 clocks at tick100.
    two_task carries a closed segment and current VALID/MISSING/UNQUERIED slots.
    initial is a t0 one-task public construction fixture.
    """
    if kind not in ('initial','two_task','short_S20','writeback'): raise ContractError('Unknown fixed synthetic fixture')
    if tick is None: tick=0 if kind=='initial' else 100 if kind=='short_S20' else 20
    if kind=='initial' and tick!=0 or kind=='two_task' and tick!=20 or kind=='short_S20' and tick not in (80,100) or kind=='writeback' and tick!=20:
        raise ContractError('Synthetic fixture supports only its declared cuts')
    cfg=deepcopy(UNIT_SOURCE['config']);x=3 if kind in ('initial','writeback') else 4;cfg.update(robots=x,task_count=1 if x==3 else 2)
    ids=[0] if kind in ('initial','writeback') else [0,1];a=.6/math.sqrt(2)
    targets=[]
    for j in ids:
        birth=3. if kind=='short_S20' and j==1 else 0.
        targets.append({'id':j,'birth':birth,'position_now':[8.+.4*(tick*DT-birth),8.+4*j if kind!='initial' else 10.],
          'velocity_now':[.4,0.],'required_robots':2,'weight':1.,'deadline':6.,'service_duration':1.})
    if kind in ('initial','writeback'):
        positions=deepcopy(UNIT_SOURCE['positions_initial']) if kind=='initial' else [[8.,9.],[8.,11.],[2.,2.]]
        targets[0]['position_now']=[8.+.4*tick*DT,10.]
        targets[0]['deadline']=UNIT_SOURCE['targets'][0]['deadline']
        targets[0]['service_duration']=UNIT_SOURCE['targets'][0]['service_duration']
    else:
        positions=[[targets[j]['position_now'][0]+a,targets[j]['position_now'][1]+sign*a] for j in ids for sign in (-1,1)]
    profiles=[{'sensor_id':f'U{i}','sigma':.02,'health':'available','observed_tick':tick} for i in range(x)]
    teams={j:[{'robot_id':2*j,'role':'dual_neg45'},{'robot_id':2*j+1,'role':'dual_pos45'}] for j in ids}
    assignment=[{'target':None,'role':'none'} for _ in range(x)]
    if kind not in ('initial','writeback'):
        for j,team in teams.items():
            for m in team:assignment[m['robot_id']]={'target':j,'role':m['role']}
    slots=[]
    for j in ids:
        needed={m['robot_id'] for m in teams[j]} if kind not in ('initial','writeback') else set()
        if kind=='two_task' and j==0:needed.add(2)
        for i in range(x):
            state='UNQUERIED' if i not in needed else 'MISSING' if kind=='two_task' and j==1 and i==3 else 'VALID'
            packet=None
            if state=='VALID':
                point=targets[j]['position_now'];angle=math.atan2(point[1]-positions[i][1],point[0]-positions[i][0])
                packet={'sensor_id':f'U{i}','position':deepcopy(positions[i]),'bearing':angle,'sigma':.02,
                        'measurement_tick':tick,'available_tick':tick,'status':'ok'}
            slots.append(public.seal_slot({'slot_key':{'target_id':j,'robot_id':i,'tick':tick},'state':state,'packet':packet}))
    histories=[];all_events=[]
    for j in ids:
        birth=round(targets[j]['birth']/DT)
        if kind in ('initial','writeback'):
            events=[_event(0,j,'BIRTH',0)];segments=[];active=None
            gaps=[{'start_tick':0,'end_at':None,'opened_by':'BIRTH','opening_event_index':0,'closing_event_index':None}]
        elif kind=='short_S20':
            start=0 if j==0 else 80;base_index=0 if j==0 else 2
            core={'target_id':j,'segment_index':0,'previous_segment_id':None,'start_tick':start,'team':teams[j],'opened_by':'INITIAL_ASSIGNMENT'}
            sid=public.segment_identity(core)
            events=[_event(base_index,j,'BIRTH',birth),_event(base_index+1,j,'ASSIGNED',start,sid)]
            intervals=max(0,tick-(95 if j==0 else 98));Q='PASS' if tick>=(95 if j==0 else 98) else 'FAIL'
            segments=[_segment(j,0,start,teams[j],tick,slots,intervals,events=[events[1]],Q=Q)];active=sid
            gaps=[{'start_tick':birth,'end_at':{'time_seconds':start*DT,'event_tick':start},'opened_by':'BIRTH',
                   'opening_event_index':base_index,'closing_event_index':base_index+1}]
        elif j==0:
            old_team=[{'robot_id':0,'role':'dual_neg45'},{'robot_id':2,'role':'dual_pos45'}]
            old_sid=public.segment_identity({'target_id':0,'segment_index':0,'previous_segment_id':None,'start_tick':0,'team':old_team,'opened_by':'INITIAL_ASSIGNMENT'})
            new_sid=public.segment_identity({'target_id':0,'segment_index':1,'previous_segment_id':old_sid,'start_tick':20,'team':teams[0],'opened_by':'MEMBER_CHANGE'})
            events=[_event(0,0,'BIRTH',0),_event(2,0,'ASSIGNED',0,old_sid),
                    _event(3,0,'TEAM_CHANGED',20,old_sid,reason='MEMBER_CHANGE'),_event(4,0,'ASSIGNED',20,new_sid,reason='MEMBER_CHANGE')]
            close={'reason':'TEAM_CHANGED','at':{'time_seconds':1.,'event_tick':20},'closing_event_index':3}
            segments=[_segment(0,0,0,old_team,20,slots,0,events=events[1:3],closure=close,G=False),
                      _segment(0,1,20,teams[0],20,slots,0,previous=old_sid,opened='MEMBER_CHANGE',events=[events[3]])]
            active=new_sid;gaps=[{'start_tick':0,'end_at':{'time_seconds':0.,'event_tick':0},'opened_by':'BIRTH','opening_event_index':0,'closing_event_index':2}]
        else:
            sid=public.segment_identity({'target_id':1,'segment_index':0,'previous_segment_id':None,'start_tick':20,'team':teams[1],'opened_by':'INITIAL_ASSIGNMENT'})
            events=[_event(1,1,'BIRTH',0),_event(5,1,'ASSIGNED',20,sid)]
            segments=[_segment(1,0,20,teams[1],20,slots,0,events=[events[1]],Q='UNKNOWN')];active=sid
            gaps=[{'start_tick':0,'end_at':{'time_seconds':1.,'event_tick':20},'opened_by':'BIRTH','opening_event_index':1,'closing_event_index':5}]
        histories.append(public.seal_history({'target_id':j,'birth_tick':birth,'cutoff_tick':tick,'active_segment_id':active,
          'segments':segments,'unassigned_intervals':gaps,'events':events}));all_events.extend(events)
    cp=public.seal_checkpoint({'previous_checkpoint_id':None if tick==0 else digest({'synthetic_prior_cut':tick-20}),
       'phase':'DECISION_READY','tick':tick,'episode_end_tick':120,'config':cfg,'positions':positions,
       'assignment':assignment,'targets':targets,'sensor_profiles':profiles,'task_histories':histories,
       'current_slots':slots,'events_since_previous_checkpoint':sorted([e for e in all_events if e['at']['time_seconds']>=(tick-20)*DT and not (tick>0 and e['kind']=='BIRTH' and e['at']['time_seconds']==(tick-20)*DT)],key=lambda e:e['event_index'])})
    return public.validate_checkpoint(cp,unit_only=True)


def synthetic_authority(checkpoint):
    """Test-only externally fixed fixture registry, never real-history admission."""
    binding=public.binding_from_checkpoint(checkpoint)
    wire=json.dumps(binding,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
    registry_sha=hashlib.sha256(wire).hexdigest()
    loaded=json.loads(wire)
    if hashlib.sha256(wire).hexdigest()!=registry_sha: raise AssertionError('Synthetic external pin changed')
    return public.HistoryAuthority.from_public_binding(loaded)


def _reject(function):
    try:function()
    except ContractError as error:return {'rejected':True,'error':str(error)}
    raise AssertionError('Declared invalid input accepted')


def _reseal(cp):
    for h in cp['task_histories']:
        h['segments']=[public.seal_segment(s) for s in h['segments']]
    cp['task_histories']=[public.seal_history(h) for h in cp['task_histories']]
    return public.seal_checkpoint(cp)


def run_history_gate(checkpoint=None,include_manual=True):
    cp=synthetic_checkpoint('short_S20') if checkpoint is None else deepcopy(checkpoint)
    authority=synthetic_authority(cp);positive=public.validate_checkpoint(cp,authority=authority)
    vectors={}
    vectors['sha_only']=_reject(lambda:public.validate_checkpoint(cp,authority={'sha256':digest(cp)}))
    for field in ('trusted','unit_only'):
        bad=deepcopy(cp);bad[field]=True
        vectors[field]=_reject(lambda bad=bad:public.validate_checkpoint(bad,authority=authority))
    bad_binding=authority.to_public_binding();bad_binding['target_history_digests'][0]['target_id']=99
    vectors['wrong_target_binding']=_reject(lambda:public.HistoryAuthority.from_public_binding(bad_binding))
    prior=synthetic_authority(synthetic_checkpoint('short_S20',80))
    vectors['prior_checkpoint_binding']=_reject(lambda:public.validate_checkpoint(cp,authority=prior))
    if include_manual:
        changed=deepcopy(cp);changed['task_histories'][0]['segments'][-1]['latest_clock']['intervals']+=1
        changed=_reseal(changed)
        vectors['manual_progress_rehashed']=_reject(lambda:public.validate_checkpoint(changed,authority=authority))
    return {'passed':len(vectors)==(6 if include_manual else 5),'scope':'synthetic explicit fixture binding only; not actual history',
            'positive_checkpoint_id':positive['checkpoint_id'],'vectors':vectors,'real_wls_calls':0}


def _private_resume_gate():
    from .execution import ActualMeasurementCache,RequestJournal,OnlineEnvironment
    def poison(*args,**kwargs):raise AssertionError('Zero-WLS gate called fusion')
    cache=ActualMeasurementCache('synthetic-cache')
    ctx={'position':[1.,2.],'sigma':.02,'health':'available'}
    packet={'sensor_id':'U0','position':[1.,2.],'bearing':.1,'sigma':.02,'measurement_tick':20,'available_tick':20,'status':'ok'}
    cache.query(0,0,20,ctx,lambda:{'state':'VALID','packet':packet})
    cache.query(0,1,20,ctx,lambda:{'state':'MISSING','packet':None})
    saved=cache.snapshot();restored=ActualMeasurementCache('synthetic-cache',json.loads(json.dumps(saved)))
    if restored.snapshot()!=saved:raise AssertionError('Actual cache roundtrip changed bytes')
    if restored.query(0,1,20,ctx,poison)['state']!='MISSING' or restored.peek(0,2,20)['state']!='UNQUERIED':raise AssertionError('Missing/unqueried state lost')
    journal=RequestJournal();fp=digest({'synthetic_action':1});journal.begin('req0',fp,100.,10.)
    committed={'charged_once':.02,'checkpoint_id':digest({'synthetic':0})};journal.commit(committed)
    replay=RequestJournal(json.loads(json.dumps(journal.snapshot()))).lookup('req0',fp)
    if replay!={'state':'REPLAY','result':committed}:raise AssertionError('Successful replay cache lost')
    env=OnlineEnvironment(deepcopy(UNIT_SOURCE),poison,'synthetic-resume',work_identity='synthetic-resume')
    state=env.private_snapshot();clone=OnlineEnvironment(deepcopy(UNIT_SOURCE),poison,'synthetic-resume',restored=deepcopy(state),work_identity='synthetic-resume')
    if clone.private_snapshot()!=state:raise AssertionError('Actual environment initial clean-cut roundtrip differs')
    bad=deepcopy(state);bad['failed']=True;bad['snapshot_digest']=digest({k:v for k,v in bad.items() if k!='snapshot_digest'})
    failed=_reject(lambda:OnlineEnvironment(deepcopy(UNIT_SOURCE),poison,'synthetic-resume',restored=bad))
    inflight=deepcopy(state);inflight['inflight']={'request_id':'pending'}
    inflight['snapshot_digest']=digest({k:v for k,v in inflight.items() if k!='snapshot_digest'})
    pending=_reject(lambda:OnlineEnvironment(deepcopy(UNIT_SOURCE),poison,'synthetic-resume',restored=inflight))
    future=deepcopy(UNIT_SOURCE);future['targets'][0]['arc_rates']=[[1.,.1],[2.,0.],[6.,0.]]
    variant=OnlineEnvironment(future,poison,'synthetic-resume-other-environment',work_identity='synthetic-resume-variant')
    if variant.observe_public()!=env.observe_public():raise AssertionError('Private future affected initial public checkpoint')
    return {'passed':True,'cache_roundtrip':True,'missing_reused_without_producer':True,'journal_replay_equal':True,
      'actual_environment_initial_cut_roundtrip':True,'failed_resume_rejection':failed,'inflight_resume_rejection':pending,'private_future_public_equality':True,
      'scope':'actual cache/journal APIs and initial clean-cut actual constructor; nonzero actual restore is separately covered by main serial jobs','real_wls_calls':0}


def _run_owned_gates(out,gate=None):
    """Run ON_IF01/05/07 through real new validation/restore APIs; no fusion."""
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    wanted=['ON_IF01_SCHEMA_AND_IDENTITY','ON_IF05_LIVE_HISTORY_AND_RESUME','ON_IF07_NO_PREDICTION_STATE_WRITEBACK']
    if gate is not None:
        wanted=[g for g in wanted if g==gate]
        if not wanted:raise ContractError('Unknown implemented interface gate')
    results=[]
    for name in wanted:
        target=out/(name+'.json')
        if target.exists():raise FileExistsError(target)
        try:
            if name.startswith('ON_IF01'):
                cp=synthetic_checkpoint('initial');authority=synthetic_authority(cp)
                positive=public.validate_checkpoint(cp,authority=authority)
                count=len(public.enumerate_candidates(public.request_from_checkpoint(cp,authority=authority),authority=authority))
                if count!=6:raise AssertionError('Initial canonical candidate count differs')
                vectors=[]
                for mutation in ('private_future','trusted','unit_only','bool_tick','duplicate_slot','missing_slot','stale_profile','INVALID'):
                    bad=deepcopy(cp)
                    if mutation in ('private_future','trusted','unit_only'):bad[mutation]=True
                    if mutation=='bool_tick':bad['tick']=True
                    if mutation=='duplicate_slot':bad['current_slots'].append(deepcopy(bad['current_slots'][0]))
                    if mutation=='missing_slot':bad['current_slots'].pop()
                    if mutation=='stale_profile':bad['sensor_profiles'][0]['observed_tick']=20
                    if mutation=='INVALID':bad['current_slots'][0]['state']='INVALID'
                    vectors.append({'mutation':mutation,**_reject(lambda bad=bad:public.validate_checkpoint(bad,authority=authority))})
                public.validate_checkpoint(synthetic_checkpoint('two_task'),authority=synthetic_authority(synthetic_checkpoint('two_task')))
                result={'passed':True,'candidate_count':count,'vectors':vectors,'input_unchanged':positive==cp}
            elif name.startswith('ON_IF05'):
                cp=synthetic_checkpoint('two_task');authority=synthetic_authority(cp)
                reordered=deepcopy(cp);reordered['task_histories'][0]['segments'].reverse()
                bad_order=_reject(lambda:public.validate_checkpoint(public.seal_checkpoint(reordered),authority=authority))
                vectors=run_history_gate()
                old_g=deepcopy(cp);old_g['task_histories'][0]['contract_id']='old_G_only_history'
                old_g['checkpoint_id']=digest({k:v for k,v in old_g.items() if k!='checkpoint_id'})
                old_g_reject=_reject(lambda:public.validate_checkpoint(old_g,authority=authority))
                missing=deepcopy(cp);slot=next(s for s in missing['current_slots'] if s['state']=='MISSING')
                slot.update(state='UNQUERIED',slot_digest=None);missing=public.seal_checkpoint(missing)
                missing_reject=_reject(lambda:public.validate_checkpoint(missing,authority=authority))
                private_id=deepcopy(cp);private_id['checkpoint_id']=digest({'private_future':True,'source_path':'audit-only'})
                private_id_reject=_reject(lambda:public.validate_checkpoint(private_id,authority=authority))
                result={'passed':vectors['passed'],'public_history_gate':vectors,'closed_segment_order':bad_order,
                        'old_G_history_rejection':old_g_reject,'missing_to_unqueried_rejection':missing_reject,
                        'private_source_as_science_id_rejection':private_id_reject,
                        'actual_resume_components':_private_resume_gate()}
            else:
                cp=synthetic_checkpoint('writeback',20);before=digest(cp)
                envelope={'message_kind':'action_request','operation':{'physical_environment_id':'synthetic-writeback','request_id':'r0'},
                  'payload':{'contract_id':public.IDS['action_transaction'],'checkpoint_id':cp['checkpoint_id'],
                             'expected_start_tick':cp['tick'],'assignment':deepcopy(cp['assignment'])}}
                public.validate_action_request(envelope,cp);vectors=[]
                for field,value in [('predicted_positions',[[0.,0.]]*3),('predicted_completion',{'tick':47,'time_seconds':2.35}),('predicted_clock',1.),('forecast_PASS_as_actual',True)]:
                    bad=deepcopy(envelope);bad['payload'][field]=value
                    vectors.append({'field':field,**_reject(lambda bad=bad:public.validate_action_request(bad,cp))})
                if digest(cp)!=before:raise AssertionError('Invalid action mutated current public state')
                result={'passed':True,'vectors':vectors,'public_state_unchanged':True,'actual_step_called':False}
            result|={'gate_id':name,'real_wls_calls':0,'local_optimizer_starts':0,
                     'scope':'declared synthetic zero-WLS interface gate; not a main scientific episode'}
            save_json(target,result);results.append(result)
        except BaseException as error:
            save_json(target,{'passed':False,'gate_id':name,'error':{'type':type(error).__name__,'message':str(error)},'real_wls_calls':0})
            raise
    return {'passed':all(r['passed'] for r in results),'gates':results,'real_wls_calls':0,'local_optimizer_starts':0}


def run_short_history_admission(inputs):
    """Frozen S30 adapter: five negative variants and one explicit test registry."""
    expected=['self_computed_sha_only','trusted_true_field','unit_only_bypass','wrong_target_binding','prior_checkpoint_binding']
    if inputs['checkpoint_tick']!=100 or [v['kind'] for v in inputs['variants']]!=expected:
        raise ContractError('S30 fixed input declaration differs')
    cp=synthetic_checkpoint('short_S20',100);before=digest(cp)
    result=run_history_gate(cp,include_manual=False)
    retained=digest(cp)==before
    if not result['passed'] or not retained:raise AssertionError('S30 public trust admission failed')
    return {'all_five_negative_variants_rejected':all(v['rejected'] for v in result['vectors'].values()),
      'actual_sampling_calls':0,'model_steps':0,'prior_valid_committed_state_retained':retained,
      'positive_adapter_contract_required':True,'synthetic_fixture_never_claimed_actual_runtime_history':True,
      'evidence':result}


def run_interface_checks(job,out,guard):
    """Model-worker dispatcher; IF04 transport faults run in separate pairs."""
    from . import admission,supervision
    names=job.get('gate_ids',job.get('gate_id'))
    if names is None:names=['ON_IF01_SCHEMA_AND_IDENTITY','ON_IF02_RESPONSE_CONTEXT','ON_IF03_COMPACT_AUDIT_INPUTS',
      'ON_IF05_LIVE_HISTORY_AND_RESUME','ON_IF06_RESOURCE_AND_OWNERSHIP','ON_IF07_NO_PREDICTION_STATE_WRITEBACK']
    if isinstance(names,str):names=[names]
    out=Path(out);out.mkdir(parents=True,exist_ok=True);results=[]
    with admission.forbid_solver_calls() as counters:
        for name in names:
            if name.startswith(('ON_IF01','ON_IF05','ON_IF07')):
                result=_run_owned_gates(out,gate=name)['gates'][0]
            elif name=='ON_IF02_RESPONSE_CONTEXT':
                result=admission.run_response_context_gate();save_json(out/(name+'.json'),result)
            elif name=='ON_IF03_COMPACT_AUDIT_INPUTS':
                result=admission.run_compact_manifest_gate(guard,job['compact_positive_reference'],
                    job['compact_negative_references'],nested_probes=job.get('compact_nested_probes'))
                save_json(out/(name+'.json'),result)
            elif name=='ON_IF06_RESOURCE_AND_OWNERSHIP':
                result=admission.run_resource_gate(supervision.resource_contract,supervision.validate_resource_arithmetic,
                                                   supervision.validate_resource_contract)
                save_json(out/(name+'.json'),result)
            else:raise ContractError('Unknown interface gate or IF04 incorrectly routed to zero-WLS dispatcher')
            if result.get('passed') is not True:raise AssertionError('Interface gate failed: '+name)
            results.append(result)
        if any(counters.values()):raise AssertionError('Interface gate invoked a scientific solver')
    return {'passed':True,'gates':results,'observed_solver_sentinel_counts':dict(counters),
            'real_wls_calls':0,'local_optimizer_starts':0}
