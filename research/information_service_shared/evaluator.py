"""Full GQ evaluation; only component motion acquisition is shared.

The original measurement/clock/reward/terminal kernels remain independent per
candidate. Main requests require real externally admitted history. Explicit unit
capabilities expose the same workspace, step and assembler for zero-WLS probes.
"""
from copy import deepcopy
from itertools import count
import math
from types import SimpleNamespace

import numpy as np

from pursuit_v2.config import Config
from pursuit_v2 import observation_geometry as geometry
from pursuit_v2.service import TOL
from research.information_service.public_quality import prepare_frame
from research.information_service_online import public, measurements
from research.information_service_online.adapter import legacy_spec
from research.information_service_online import evaluator as original
from research.information_service_online.evaluator import (
    ClockStepper, boundary_transition, canonical_team, components, escape_time,
    escape_precedes_endpoint, interval_stop, termination_reason, unattended,
)
from .common import SCIENTIFIC_CONTRACT, STAGE_CONTRACT, DT, ContractError, digest, typed_digest, absolute_O
from . import contracts
from .motion_cache import MotionComponentCache

# This is the identical production assembler called inside the unchanged online
# assemble_current/future functions, not a checker-owned replacement.
assemble_left_state = measurements.assemble_left_state
_WORKSPACE_SERIAL = count()


def energy_increment(force, elapsed):
    """Actual production reduction seam, preserving q-by-2 NumPy summation."""
    return float(np.sum(force**2))*elapsed


class CandidateWorkspace(SimpleNamespace):
    def ownership_record(self, full_scope_id, other_workspaces=()):
        checks=[]
        for other in other_workspaces:
            checks.append({'left_storage_token':self.positions_token,'right_storage_token':other.positions_token,
                           'shares_storage':bool(np.shares_memory(self.positions,other.positions))})
            checks.append({'left_storage_token':self.clock_token,'right_storage_token':other.clock_token,
                           'shares_storage':self.clock is other.clock})
        row={'message_kind':'candidate_state_ownership','contract_id':STAGE_CONTRACT,
             'full_scope_id':full_scope_id,'candidate_id':self.descriptor['candidate_id'],
             'candidate_key':deepcopy(self.descriptor['key']),'candidate_instance_id':self.instance_id,
             'positions_storage_token':self.positions_token,'clock_instance_token':self.clock_token,
             'events_storage_token':self.events_token,'metrics_storage_token':self.metrics_token,
             'positions_shape':list(self.positions.shape),'initial_positions_typed_digest':self.initial_positions_digest,
             'observed_alias_checks':checks}
        return contracts.validate_definition(row,'CandidateStateOwnership')


def _manifest_and_flat(request,spec,history_authority,unit_fixture):
    if unit_fixture is not None:
        flat,manifest=contracts.admit_request(request,unit_fixture=unit_fixture,history_authority=history_authority)
        descriptor=contracts.select_descriptor(manifest,spec)
        return manifest,manifest.get('unit_public_request'),descriptor,flat,legacy_spec(descriptor)
    # Retain the r2 admission order, including its repeated per-candidate checks.
    if type(history_authority) is not public.HistoryAuthority:
        raise ContractError('Main shared candidate needs exact external history authority')
    manifest=public.build_manifest(request,authority=history_authority)
    online_request=manifest['payload']
    descriptor=public.validate_candidate(online_request,spec,authority=history_authority)
    flat,selected=original.validate_candidate(online_request,descriptor,history_authority=history_authority)
    if typed_digest(request)!=typed_digest(online_request):
        raise ContractError('Unexpected main request normalization')
    contracts._fresh_profiles(flat)
    if any(t['required_robots']!=2 for t in flat['targets']): raise ContractError('Shared first round is q=2')
    return manifest,online_request,descriptor,flat,selected


def _unit_assembly(workspace,tick):
    """Explicit unit-only synthetic data; never used by a main request."""
    w=workspace
    if type(w.unit_fixture) is not contracts.UnitFixtureCapability:
        raise ContractError('Synthetic assembly requires the explicit fixture capability')
    if w.online_request is not None:
        raise ContractError('Public-shaped unit input must use the common endpoint callsite')
    elapsed=tick*DT-w.start*DT
    point=[w.target['position_now'][i]+w.target['velocity_now'][i]*elapsed for i in (0,1)]
    profiles=[deepcopy(p)|{'observed_tick':tick} for p in w.request['sensor_profiles']]
    slots=[public.seal_slot({'slot_key':{'target_id':w.j,'robot_id':i,'tick':tick},
                            'state':'UNQUERIED','packet':None}) for i in range(w.cfg.robots)]
    team=[{'robot_id':i,'role':role} for i,role in w.team]
    return assemble_left_state(tick=tick,target_id=w.j,target_position=point,positions=w.positions.tolist(),
        sensor_profiles=profiles,current_slots=slots,team=team,stream_id=w.stream,actual=False)


def prepare_candidate_endpoint(workspace,tick):
    """Actual S current/future assembly seam; returns before any estimator call."""
    w=workspace
    if w.online_request is None:
        if w.unit_fixture is None: raise ContractError('Main endpoint requires an admitted public request')
        return _unit_assembly(w,tick)
    # The public-shaped C07 fixture and real S candidates traverse this same
    # callsite. Unit authority is explicit; current slots are never rewritten.
    admission={'unit_only':True} if w.unit_fixture is not None else {'authority':w.history_authority}
    if tick==w.start:
        return measurements.assemble_current(w.online_request,w.descriptor,w.work_identity,
            physical_environment_id=w.physical_environment_id,**admission)
    return measurements.assemble_future(w.online_request,w.descriptor,tick,w.positions.tolist(),w.work_identity,
        physical_environment_id=w.physical_environment_id,**admission)


def _target_at(w,tick): return w.p0+w.velocity*(tick*DT-w.t0)


def _geometry_valid(w,tick):
    return bool(np.all(np.linalg.norm(w.positions[w.robots]-_target_at(w,tick)-w.offsets,axis=1)<=geometry.radius(w.cfg)))


def _sense(w,tick):
    G=_geometry_valid(w,tick)
    if w.mode=='G_ONLY': return dict(G=G,Q='PASS',result=None)
    assembly=prepare_candidate_endpoint(w,tick)
    if assembly.get('reused_actual_endpoint'):
        raise ContractError('KEEP must reuse its admitted endpoint without entering new sensing')
    frame=assembly['frame'];allowed=[f'U{i}' for i in w.robots];prepared=prepare_frame(frame,allowed)
    sent=deepcopy(frame);identity=digest(sent)
    if not callable(w.sense_callback): raise ContractError('A new endpoint requires an explicit sensing callback')
    result=w.sense_callback(sent,allowed,w.first);w.requests+=1
    if digest(sent)!=identity: raise ContractError('Sensing mutated input')
    if not isinstance(result,dict): raise ContractError('Missing public sensing result')
    for field in ('tick','target_id','stream_id','frame_id'):
        if result.get(field)!=frame[field]: raise ContractError('Sensing identity mismatch')
    q=result.get('quality',{})
    if (result.get('payload_sha256')!=prepared['payload_sha256'] or
        q.get('payload_sha256')!=prepared['payload_sha256'] or q.get('status') not in ('PASS','FAIL','UNKNOWN')):
        raise ContractError('Sensing quality/payload contract mismatch')
    w.estimator_calls+=int(result.get('estimator_called') is True)
    return dict(G=G,Q=q['status'],result=result,public_frame=frame,source_slots=assembly['source_slots'])


def _frame(w,n,command,lo,stop,point):
    return dict(tick=n,time=n*DT,lo_time=lo,control_stop_time=stop,positions=w.positions.tolist(),
        control=command.tolist(),assignment=deepcopy(w.actions),progress={str(w.j):w.clock.state.progress},
        G={str(w.j):point['G']} if point else {},Q={str(w.j):point['Q']} if point else {},
        sensing_results=[] if not point or point.get('result') is None else [dict(
            frame=point['public_frame'],allowed_sensor_ids=[f'U{i}' for i in w.robots],
            start_tick=w.first,result=point['result'],source_slots=point['source_slots'])],
        reused_actual_endpoint=bool(point and point.get('reused_actual_endpoint')),
        clock_state=w.clock.raw(),control_integral=w.total,energy=w.total,
        occupied_robot_seconds=w.occupied,status={str(w.j):w.status})


def initialize_candidate_state(request,spec,sense_callback=None,*,history_authority=None,
                               unit_fixture=None,mode='GQ',work_identity='candidate',
                               physical_environment_id='prediction-context'):
    """The production initializer, including the real/mocked left endpoint.

    Zero-WLS fixtures supply their declared callback explicitly. This initializer
    is used unchanged by evaluate_candidate, including its independent clock.
    """
    if mode!='GQ' and not(unit_fixture is not None and mode=='G_ONLY'):
        raise ContractError('Main shared evaluation requires GQ')
    original_request=deepcopy(request)
    manifest,online_request,descriptor,flat,selected=_manifest_and_flat(request,spec,history_authority,unit_fixture)
    cfg=Config(**flat['config']);j=selected['target'];target=next(t for t in flat['targets'] if t['id']==j)
    actions=[dict(target=None,role='none') for _ in range(cfg.robots)]
    for robot,role in zip(selected['robots'],selected['roles']): actions[robot]=dict(target=j,role=role)
    boundary=boundary_transition(flat,actions);actions=boundary['actions']
    team=canonical_team(actions,j);robots=[v[0] for v in team]
    offsets=np.array([geometry.offset(role,cfg) for _,role in team])
    positions=np.array(flat['positions'],dtype=float,copy=True)
    p0=np.array(target['position_now'],dtype=float);velocity=np.array(target['velocity_now'],dtype=float)
    start=flat['start_tick'];end=flat['prediction_end_tick'];t0=start*DT;until=end*DT
    escape=escape_time(flat,target);retained=boundary['retained_left'][str(j)]
    first=start+1 if retained is not None else start
    stream=f'{work_identity}:T{j}:first{first}'
    w=CandidateWorkspace(original_request=original_request,manifest=manifest,online_request=online_request,
        descriptor=descriptor,request=flat,spec=selected,before=digest(flat),cfg=cfg,j=j,target=target,
        actions=actions,boundary=boundary,team=team,robots=robots,offsets=offsets,positions=positions,
        p0=p0,velocity=velocity,start=start,end=end,t0=t0,until=until,escape=escape,retained=retained,
        first=first,stream=stream,frames=[],events=deepcopy(boundary['events']),metrics={},total=0.,occupied=0.,
        status='active',completion=None,escaped=None,current=None,estimator_calls=0,requests=0,
        history_authority=history_authority,unit_fixture=unit_fixture,mode=mode,sense_callback=sense_callback,
        work_identity=work_identity,physical_environment_id=physical_environment_id)
    if escape_precedes_endpoint(escape,t0):
        w.status='escaped';w.escaped=escape
        event_tick=round(escape/DT) if math.isclose(escape,round(escape/DT)*DT,abs_tol=TOL,rel_tol=0) else None
        w.events.append(dict(type='escape',target=j,time=escape,event_tick=event_tick))
        w.events.append(dict(type='release',target=j,time=escape,robots=robots,extra_change_cost=0.))
        w.actions=[dict(target=None,role='none') for _ in range(cfg.robots)]
    elif retained is not None:
        if retained['tick']!=start or retained['G']!=_geometry_valid(w,start):
            raise ContractError('KEEP endpoint not current or physical predicate inconsistent')
        w.current=dict(G=retained['G'],Q=retained['Q'],result=None,reused_actual_endpoint=True)
    else:
        try: w.current=_sense(w,start)
        except BaseException as error:
            error.gq_last_committed=dict(tick=start,positions=deepcopy(flat['positions']),
                assignment=deepcopy(flat['assignment']),boundary_committed=False)
            raise
    w.clock=ClockStepper(cfg,target['service_duration'],boundary['clock_states'][str(j)],team,start,
        True if w.current is None else w.current['G'],'PASS' if w.current is None else w.current['Q'])
    w.frames.append(_frame(w,start,np.zeros_like(positions),t0,t0,w.current))
    w.instance_id=f'{work_identity}:workspace:{next(_WORKSPACE_SERIAL)}'
    w.positions_token=f'positions:{w.instance_id}:{id(w.positions)}'
    w.clock_token=f'clock:{w.instance_id}:{id(w.clock)}'
    w.events_token=f'events:{w.instance_id}:{id(w.events)}'
    w.metrics_token=f'metrics:{w.instance_id}:{id(w.metrics)}'
    w.initial_positions_digest=typed_digest(flat['positions'])
    return w


def shared_candidate_step(workspace,cache,n):
    """One original candidate step; active components are requested individually."""
    w=workspace
    if type(n) is not int or n!=w.frames[-1]['tick']+1 or n>w.end:
        raise ContractError('Candidate steps must be contiguous inside the horizon')
    lo=(n-1)*DT;hi=n*DT;command=np.zeros_like(w.positions);stop=lo;point=None
    if w.status=='active':
        stop=interval_stop(lo,hi,w.escape);elapsed=max(0.,stop-lo)
        pos=w.positions[w.robots].copy()
        rows=[cache.get_interval(w.j,i,role,n-1,cache.full_scope_id) for i,role in w.team]
        # Verify that the detached prefix is the candidate's own pre-stop state.
        if any(typed_digest(row['x_start'])!=typed_digest(pos[k].tolist()) or
               contracts.f64hex(row['elapsed'])!=contracts.f64hex(float(elapsed)) for k,row in enumerate(rows)):
            raise ContractError('Cached interval does not match candidate state/elapsed')
        force=np.array([row['u'] for row in rows],dtype=float,order='C',copy=True)
        w.positions[w.robots]=np.array([row['x_end'] for row in rows],dtype=float,order='C');command[w.robots]=force
        w.total+=energy_increment(force,elapsed);w.occupied+=len(w.robots)*elapsed
        if escape_precedes_endpoint(w.escape,hi):
            w.status='escaped';w.escaped=w.escape
            event_tick=round(w.escape/DT) if math.isclose(w.escape,round(w.escape/DT)*DT,abs_tol=TOL,rel_tol=0) else None
            w.events.append(dict(type='escape',target=w.j,time=w.escape,event_tick=event_tick))
        else:
            try: point,_,done,interruptions=w.clock.consume(n,lambda:_sense(w,n))
            except BaseException as error:
                error.gq_last_committed=deepcopy(w.frames[-1])
                raise
            w.events.extend(dict(e,type='interruption',target=w.j) for e in interruptions)
            if done:
                w.status='completed';w.completion=hi
                w.events.append(dict(type='completion',target=w.j,time=hi,event_tick=n))
        if w.status!='active':
            at=w.completion if w.completion is not None else w.escaped
            w.events.append(dict(type='release',target=w.j,time=at,robots=w.robots,extra_change_cost=0.))
            w.actions=[dict(target=None,role='none') for _ in range(w.cfg.robots)]
    if w.status=='active' and n==w.end and w.end>=round(w.cfg.end_time/DT):
        w.status='unfinished'
        w.events.append(dict(type='release',target=w.j,time=w.until,robots=w.robots,reason='episode_end',extra_change_cost=0.))
        w.actions=[dict(target=None,role='none') for _ in range(w.cfg.robots)]
    result=_frame(w,n,command,lo,stop,point);w.frames.append(result)
    return result


def evaluate_candidate(request,spec,sense_callback,*,cache,history_authority=None,mode='GQ',
                       work_identity='candidate',unit_fixture=None,on_commit=None,
                       physical_environment_id='prediction-context',on_ownership=None):
    if type(cache) is not MotionComponentCache: raise ContractError('Production motion cache required')
    cache.assert_request(request,unit_fixture=unit_fixture)
    w=initialize_candidate_state(request,spec,sense_callback,history_authority=history_authority,
        unit_fixture=unit_fixture,mode=mode,work_identity=work_identity,physical_environment_id=physical_environment_id)
    if on_ownership is not None: on_ownership(w.ownership_record(cache.full_scope_id))
    if on_commit: on_commit(w.frames[-1])
    for n in range(w.start+1,w.end+1):
        frame=shared_candidate_step(w,cache,n)
        if on_commit: on_commit(frame)
    cost_stop=w.completion if w.completion is not None else min(w.until,w.escape)
    comp=components(w.request['config'],w.target,w.t0,cost_stop,w.completion is not None,w.total,w.until)
    value=absolute_O(comp);baseline=unattended(w.request,w.target)
    reason=termination_reason(w.completion is not None,w.escaped is not None,w.until,w.cfg.end_time)
    row=dict(target=w.j,status=w.status,termination_reason=reason,completion_time=w.completion,
        completion_tick=None if w.completion is None else round(w.completion/DT),escape_time=w.escaped,
        clock_state=dict(w.clock.raw(),geometry_identity=geometry.identity(w.cfg)),
        kept_history=w.retained is not None,selected_team=deepcopy(w.team),
        final_progress=w.clock.state.progress,components=comp,absolute_O=value,
        baseline=baseline,v=float(value-baseline),control_integral=w.total,occupied_robot_seconds=w.occupied,
        measurement_requests=w.requests,reported_estimator_calls=w.estimator_calls)
    if digest(w.request)!=w.before: raise ContractError('Evaluator mutated source observation')
    if unit_fixture is None and digest(w.original_request)!=digest(w.online_request):
        raise ContractError('Unexpected input normalization/mutation')
    if typed_digest(request)!=typed_digest(w.original_request): raise ContractError('Shared evaluation mutated original request')
    w.metrics.update(components=comp,physical_O=value,B64=baseline,net_O=float(value-w.boundary['change_cost']),
        change_cost=w.boundary['change_cost'],assignment_changes=w.boundary['assignment_changes'],
        control_integral=w.total,occupied_robot_seconds=w.occupied)
    return dict(kind='candidate_evaluation',execution_contract_id=SCIENTIFIC_CONTRACT,mode=mode,
        request_identity=w.manifest['request_identity'],world_identity=w.manifest['world_identity'],
        candidate_identity=w.spec.get('candidate_identity'),candidate=w.spec,start_tick=w.start,end_tick=w.end,
        frames=w.frames,events=w.events,per_target={str(w.j):row},
        sensing_results=[s for f in w.frames for s in f['sensing_results']],metrics=w.metrics,
        final_positions=w.positions.tolist(),final_assignment=w.actions,input_unchanged=True)
