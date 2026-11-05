"""Online full-candidate evaluation with admitted mixed current measurements.

Only public requests enter this module. Truth-side fixtures, prefix sources and
the independent joint executor are deliberately absent from its dependencies.
"""
from copy import deepcopy
from dataclasses import asdict, replace
import math

import numpy as np

from pursuit_v2.config import Config
from pursuit_v2 import observation_geometry as geometry
from pursuit_v2.service import advance_clock, initial_state, restore_state, TOL
from research.information_service.common import CONTRACT_ID as MEASUREMENT_CONTRACT
from research.information_service.public_quality import prepare_frame
from .common import CONTRACT_ID, DT, ContractError, digest, absolute_O
from . import public, measurements
from .adapter import flatten_request, legacy_spec


def progress(clock):
    return float(clock['base']+clock['intervals']*DT)


def canonical_team(actions,target):
    return [[i,a['role']] for i,a in enumerate(actions) if a['target']==target]


def actions_from_candidates(request,specs):
    actions=[dict(target=None,role='none') for _ in range(request['config']['robots'])]
    targets=set()
    for spec in specs:
        if spec['target'] in targets:raise ContractError('At most one candidate per task')
        targets.add(spec['target'])
        if len(spec['robots'])!=len(spec['roles']):raise ContractError('Member/role length mismatch')
        for i,role in zip(spec['robots'],spec['roles']):
            if isinstance(i,bool) or not isinstance(i,int) or not 0<=i<len(actions) or actions[i]['target'] is not None:
                raise ContractError('Duplicate or invalid robot resource')
            actions[i]=dict(target=spec['target'],role=role)
    boundary_transition(request,actions)
    return actions


def interval_stop(lo,hi,escape):
    return max(lo,min(hi,escape))


def escape_precedes_endpoint(escape,hi):
    return escape<=hi+TOL


def termination_reason(completed,escaped,until,episode_end):
    return 'completed' if completed else ('escaped' if escaped else
           ('episode_end' if until>=episode_end-TOL else 'horizon_truncated'))


def boundary_transition(request,actions):
    """Pure atomic full-Assignment transaction, also exposed to unit-only seams."""
    x=request['config']['robots']
    if not isinstance(actions,(tuple,list)) or len(actions)!=x:
        raise ContractError('Exactly one action per stable Uk required')
    actions=deepcopy(list(actions));targets={t['id']:t for t in request['targets']}
    for a in actions:
        if not isinstance(a,dict) or set(a)!={'target','role'}:
            raise ContractError('Exact Assignment fields required')
        if a['target'] is None:
            if a['role']!='none':raise ContractError('Invalid IDLE')
        elif isinstance(a['target'],bool) or not isinstance(a['target'],int) or a['target'] not in targets:
            raise ContractError('Cannot assign a hidden, ended, or unknown target')
    cfg=Config(**request['config'])
    clocks={};left={};events=[];needs=[]
    histories={h['target_id']:h for h in request['gq_histories']}
    for j,t in targets.items():
        team=canonical_team(actions,j)
        if team:
            try:complete=geometry.validate_roles(t['required_robots'],[v[1] for v in team],cfg)
            except (ValueError,TypeError) as exc:raise ContractError('Invalid team roles') from exc
            if not complete:raise ContractError('Partial initial or replacement team is illegal')
        h=histories[j];old=deepcopy(h['clock_state']);same=team==old['team']
        if team and same and h['last_endpoint'] is not None:
            clocks[str(j)]=old;left[str(j)]=deepcopy(h['last_endpoint'])
        else:
            clocks[str(j)]=dict(base=0.,intervals=0,team=team)
            left[str(j)]=None
            if team:needs.append(j)
            if progress(old)>0:
                events.append(dict(type='interruption',reason='team_changed',target=j,
                    time=request['start_tick']*DT,event_tick=request['start_tick'],progress_before=progress(old)))
    changes=sum(a!=b for a,b in zip(request['assignment'],actions))
    return dict(actions=actions,clock_states=clocks,retained_left=left,needs_new_endpoint=needs,
                events=events,assignment_changes=changes,change_cost=float(cfg.change_cost*changes),
                positions=deepcopy(request['positions']),boundary_elapsed_seconds=0.)


class ClockStepper:
    """The actual two-endpoint clock used by evaluation and zero-WLS short checks."""
    def __init__(self,cfg,duration,clock,team,start_tick,G,Q):
        self.cfg=cfg;self.duration=float(duration);self.team=tuple(tuple(v) for v in team)
        self.state=restore_state(cfg,dict(clock,geometry_identity=geometry.identity(cfg)))
        self.tick=int(start_tick);self.G=bool(G);self.Q=Q;self.done=False;self.events=[]
        if not G or Q!='PASS':
            if self.state.progress>0:
                self.events.append(dict(time=start_tick*DT,reason='observation_invalid',progress_before=self.state.progress))
            self.state=replace(self.state,base=0.,intervals=0,team=self.team)

    def advance(self,tick,G,Q):
        if self.done:raise ContractError('Terminal clock cannot advance')
        if tick!=self.tick+1:raise ContractError('Clock endpoints must be contiguous')
        if Q not in ('PASS','FAIL','UNKNOWN'):raise ContractError('Unknown quality state')
        state,done,events=advance_clock(self.state,self.duration,self.team,
            self.G and self.Q=='PASS' and G and Q=='PASS',tick*DT)
        self.state=state;self.done=done;self.tick=tick;self.G=bool(G);self.Q=Q;self.events.extend(events)
        return self.state.progress,done,events

    def raw(self):
        return dict(base=self.state.base,intervals=self.state.intervals,team=[list(t) for t in self.state.team])

    def consume(self,tick,producer):
        point=producer()  # Exceptions propagate before any clock state changes.
        value,done,events=self.advance(tick,point['G'],point['Q'])
        return point,value,done,events


def components(config,target,start,stop,completion,energy,until):
    """Absolute per-task O, excluding changes and all pre-start sunk costs."""
    wr=4*config['task_count'];denom=wr*config['stage_dt']
    return dict(completion=target['weight']/wr if completion else 0.,
        flow=-config['flow_weight']*target['weight']*max(0.,stop-max(start,target['birth']))/denom,
        late=-config['late_weight']*target['weight']*max(0.,stop-max(start,target['birth'],target['deadline']))/denom,
        effort=-config['control_weight']*energy/(config['robots']*config['stage_dt']*config['control_reference']**2),
        terminal=(-config['unfinished_weight']*target['weight']/wr if
            until>=config['stage_dt']*config['max_stages']-TOL and not completion else 0.))


def escape_time(request,target):
    start=request['start_tick']*DT;x=target['position_now'][0];vx=target['velocity_now'][0]
    if x>=request['config']['side']:return start
    return start+(request['config']['side']-x)/vx if vx>0 else math.inf


def unattended(request,target):
    start=request['start_tick']*DT;until=request['prediction_end_tick']*DT
    return absolute_O(components(request['config'],target,start,min(until,escape_time(request,target)),False,0.,until))


def validate_candidate(request,spec,*,history_authority=None,unit_only=False):
    manifest=public.build_manifest(request,authority=history_authority,unit_only=unit_only)
    descriptor=public.validate_candidate(manifest['payload'],spec,authority=history_authority,unit_only=unit_only)
    flat,_=flatten_request(manifest['payload'],authority=history_authority,unit_only=unit_only)
    return flat,legacy_spec(descriptor)


def evaluate_candidate(request,spec,sense_callback,*,history_authority=None,mode='GQ',
                       work_identity='candidate',unit_only=False,on_commit=None,physical_environment_id='prediction-context'):
    original_request=deepcopy(request)
    manifest=public.build_manifest(request,authority=history_authority,unit_only=unit_only)
    online_request=manifest['payload']
    descriptor=public.validate_candidate(online_request,spec,authority=history_authority,unit_only=unit_only)
    request,selected=validate_candidate(online_request,descriptor,history_authority=history_authority,unit_only=unit_only)
    spec=selected
    before=digest(request)
    if mode not in ('GQ','G_ONLY'):raise ContractError('Unknown evaluator mode')
    cfg=Config(**request['config']);j=spec['target']
    target=next(t for t in request['targets'] if t['id']==j)
    actions=[dict(target=None,role='none') for _ in range(cfg.robots)]
    for robot,role in zip(spec['robots'],spec['roles']):actions[robot]=dict(target=j,role=role)
    boundary=boundary_transition(request,actions);actions=boundary['actions']
    team=canonical_team(actions,j);robots=[v[0] for v in team]
    offsets=np.array([geometry.offset(role,cfg) for _,role in team])
    positions=np.array(request['positions'],dtype=float,copy=True)
    p0=np.array(target['position_now'],dtype=float);velocity=np.array(target['velocity_now'],dtype=float)
    profiles={p['sensor_id']:p for p in request['sensor_profiles']}
    start=request['start_tick'];end=request['prediction_end_tick'];t0=start*DT;until=end*DT
    escape=escape_time(request,target);retained=boundary['retained_left'][str(j)]
    first=start+1 if retained is not None else start
    stream=f'{work_identity}:T{j}:first{first}'
    frames=[];events=deepcopy(boundary['events']);total=0.;occupied=0.;status='active'
    completion=None;escaped=None;current=None;estimator_calls=0;requests=0
    def target_at(tick):return p0+velocity*(tick*DT-t0)
    def geometry_valid(tick):
        return bool(np.all(np.linalg.norm(positions[robots]-target_at(tick)-offsets,axis=1)<=geometry.radius(cfg)))
    def sense(tick):
        nonlocal estimator_calls,requests
        G=geometry_valid(tick)
        if mode=='G_ONLY':return dict(G=G,Q='PASS',result=None)
        if tick==start:
            assembly=measurements.assemble_current(online_request,descriptor,work_identity,
                authority=history_authority,unit_only=unit_only,physical_environment_id=physical_environment_id)
        else:
            assembly=measurements.assemble_future(online_request,descriptor,tick,positions.tolist(),work_identity,
                authority=history_authority,unit_only=unit_only,physical_environment_id=physical_environment_id)
        if assembly.get('reused_actual_endpoint'):
            raise ContractError('KEEP must reuse its admitted endpoint without entering new sensing')
        frame=assembly['frame']
        allowed=[f'U{i}' for i in robots];prepared=prepare_frame(frame,allowed)
        sent=deepcopy(frame);identity=digest(sent)
        result=sense_callback(sent,allowed,first);requests+=1
        if digest(sent)!=identity:raise ContractError('Sensing mutated input')
        if not isinstance(result,dict):raise ContractError('Missing public sensing result')
        for field in ('tick','target_id','stream_id','frame_id'):
            if result.get(field)!=frame[field]:raise ContractError('Sensing identity mismatch')
        q=result.get('quality',{})
        if (result.get('payload_sha256')!=prepared['payload_sha256'] or
            q.get('payload_sha256')!=prepared['payload_sha256'] or q.get('status') not in ('PASS','FAIL','UNKNOWN')):
            raise ContractError('Sensing quality/payload contract mismatch')
        estimator_calls+=int(result.get('estimator_called') is True)
        return dict(G=G,Q=q['status'],result=result,public_frame=frame,source_slots=assembly['source_slots'])
    if escape_precedes_endpoint(escape,t0):
        status='escaped';escaped=escape
        event_tick=round(escape/DT) if math.isclose(escape,round(escape/DT)*DT,abs_tol=TOL,rel_tol=0) else None
        events.append(dict(type='escape',target=j,time=escape,event_tick=event_tick))
        events.append(dict(type='release',target=j,time=escape,robots=robots,extra_change_cost=0.))
        actions=[dict(target=None,role='none') for _ in range(cfg.robots)]
    elif retained is not None:
        if retained['tick']!=start or retained['G']!=geometry_valid(start):raise ContractError('KEEP endpoint not current or physical predicate inconsistent')
        current=dict(G=retained['G'],Q=retained['Q'],result=None,reused_actual_endpoint=True)
    else:
        try:current=sense(start)
        except BaseException as error:
            error.gq_last_committed=dict(tick=start,positions=deepcopy(request['positions']),
                assignment=deepcopy(request['assignment']),boundary_committed=False)
            raise
    # A task already escaping under the production tolerance has no new
    # measurement endpoint. Preserve its pre-termination clock without credit.
    clock=ClockStepper(cfg,target['service_duration'],boundary['clock_states'][str(j)],team,start,
                       True if current is None else current['G'],'PASS' if current is None else current['Q'])
    def frame(n,command,lo,stop,point):
        return dict(tick=n,time=n*DT,lo_time=lo,control_stop_time=stop,positions=positions.tolist(),
            control=command.tolist(),assignment=deepcopy(actions),progress={str(j):clock.state.progress},
            G={str(j):point['G']} if point else {},Q={str(j):point['Q']} if point else {},
            sensing_results=[] if not point or point.get('result') is None else [dict(
                frame=point['public_frame'],allowed_sensor_ids=[f'U{i}' for i in robots],
                start_tick=first,result=point['result'],source_slots=point['source_slots'])],
            reused_actual_endpoint=bool(point and point.get('reused_actual_endpoint')),
            clock_state=clock.raw(),
            control_integral=total,energy=total,occupied_robot_seconds=occupied,status={str(j):status})
    frames.append(frame(start,np.zeros_like(positions),t0,t0,current))
    if on_commit:on_commit(frames[-1])
    for n in range(start+1,end+1):
        lo=(n-1)*DT;hi=n*DT;command=np.zeros_like(positions);stop=lo;point=None
        if status=='active':
            stop=interval_stop(lo,hi,escape);elapsed=max(0.,stop-lo)
            pos=positions[robots].copy()
            force=velocity+cfg.travel_gain*(target_at(n-1)+offsets-pos)
            speeds=np.linalg.norm(force,axis=1)
            force*=np.minimum(1.,cfg.max_speed/np.maximum(speeds,1e-15))[:,None]
            positions[robots]=pos+force*elapsed;command[robots]=force
            total+=float(np.sum(force**2))*elapsed;occupied+=len(robots)*elapsed
            if escape_precedes_endpoint(escape,hi):
                status='escaped';escaped=escape
                event_tick=round(escape/DT) if math.isclose(escape,round(escape/DT)*DT,abs_tol=TOL,rel_tol=0) else None
                events.append(dict(type='escape',target=j,time=escape,event_tick=event_tick))
            else:
                try:point,_,done,interruptions=clock.consume(n,lambda:sense(n))
                except BaseException as error:
                    error.gq_last_committed=deepcopy(frames[-1])
                    raise
                events.extend(dict(e,type='interruption',target=j) for e in interruptions)
                if done:
                    status='completed';completion=hi
                    events.append(dict(type='completion',target=j,time=hi,event_tick=n))
            if status!='active':
                at=completion if completion is not None else escaped
                events.append(dict(type='release',target=j,time=at,robots=robots,extra_change_cost=0.))
                actions=[dict(target=None,role='none') for _ in range(cfg.robots)]
        if status=='active' and n==end and end>=round(cfg.end_time/DT):
            status='unfinished'
            events.append(dict(type='release',target=j,time=until,robots=robots,reason='episode_end',extra_change_cost=0.))
            actions=[dict(target=None,role='none') for _ in range(cfg.robots)]
        frames.append(frame(n,command,lo,stop,point))
        if on_commit:on_commit(frames[-1])
    cost_stop=completion if completion is not None else min(until,escape)
    comp=components(request['config'],target,t0,cost_stop,completion is not None,total,until)
    value=absolute_O(comp);baseline=unattended(request,target)
    reason=termination_reason(completion is not None,escaped is not None,until,cfg.end_time)
    row=dict(target=j,status=status,termination_reason=reason,completion_time=completion,
        completion_tick=None if completion is None else round(completion/DT),escape_time=escaped,
        clock_state=dict(clock.raw(),geometry_identity=geometry.identity(cfg)),
        kept_history=retained is not None,selected_team=deepcopy(team),
        final_progress=clock.state.progress,components=comp,absolute_O=value,
        baseline=baseline,v=float(value-baseline),control_integral=total,occupied_robot_seconds=occupied,
        measurement_requests=requests,reported_estimator_calls=estimator_calls)
    if digest(request)!=before:raise ContractError('Evaluator mutated source observation')
    if digest(original_request)!=digest(online_request):raise ContractError('Unexpected input normalization/mutation')
    return dict(kind='candidate_evaluation',execution_contract_id=CONTRACT_ID,mode=mode,
        request_identity=manifest['request_identity'],world_identity=manifest['world_identity'],
        candidate_identity=selected.get('candidate_identity'),candidate=selected,start_tick=start,end_tick=end,
        frames=frames,events=events,per_target={str(j):row},
        sensing_results=[s for f in frames for s in f['sensing_results']],
        metrics=dict(components=comp,physical_O=value,B64=baseline,net_O=float(value-boundary['change_cost']),
            change_cost=boundary['change_cost'],assignment_changes=boundary['assignment_changes'],
            control_integral=total,occupied_robot_seconds=occupied),
        final_positions=positions.tolist(),final_assignment=actions,input_unchanged=True)
