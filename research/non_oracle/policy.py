"""A1 certainty-equivalent prediction. Receives no private target objects."""
from copy import deepcopy
from types import SimpleNamespace
from fractions import Fraction
import math
import numpy as np
from pursuit_v2.config import Config
from pursuit_v2.types import Assignment
from pursuit_v2.observation_geometry import offset,radius
from pursuit_v2.service import ServiceState,advance_clock
from research.cooperative_sensing.estimator import estimate
from research.information_service.public_quality import assess_quality
from research.information_service_online.evaluator import components
from research.information_service_online.common import absolute_O,digest
from research.quality_allocation.certified_solver import solve,SCALE
from scripts.gq_windows.a0_plans import catalogue
from .belief import trajectory

def command(belief,tick,positions,roles,cfg):
    p,v=trajectory(belief,tick);positions=np.asarray(positions,dtype=float)
    force=np.asarray(v)+cfg.travel_gain*(np.asarray(p)+np.array([offset(r,cfg) for r in roles])-positions)
    speed=np.linalg.norm(force,axis=1)
    return force*np.minimum(1.,cfg.max_speed/np.maximum(speed,1e-15))[:,None]

def endpoint(view,target,key,tick,positions,cfg):
    p,_=trajectory(view['beliefs'][target],tick);robots=key['robots']
    G=bool(np.all(np.linalg.norm(positions[robots]-np.array(p)-np.array([offset(r,cfg) for r in key['roles']]),axis=1)<=radius(cfg)))
    records=[];slots={(s['slot_key']['target_id'],s['slot_key']['robot_id']):s for s in view['current_slots']}
    for i in robots:
        profile=view['sensor_profiles'][i]
        if profile['health']!='available':continue
        slot=slots.get((target,i)) if tick==view['tick'] else None
        if slot and slot['state']=='MISSING':continue
        if slot and slot['state']=='VALID':packet=slot['packet'];bearing=packet['bearing']
        else:bearing=(math.atan2(p[1]-positions[i,1],p[0]-positions[i,0])+math.pi)%(2*math.pi)-math.pi
        records.append((i,positions[i].tolist(),bearing,profile['sigma']))
    payload=dict(sensor_ids=['U'+str(r[0]) for r in records],positions=[r[1] for r in records],bearings=[r[2] for r in records],sigmas=[r[3] for r in records],domain=[[0.,0.],[20.,20.]])
    est=estimate(payload) if len(records)>=2 else None
    return G,assess_quality(payload,est)['status']

def evaluate(view,key,cache=None):
    before=digest(view);cfg=Config(**view['config']);j=key['target'];target=next(t for t in view['targets'] if t['id']==j)
    positions=np.array(view['positions'],dtype=float);team=tuple(zip(key['robots'],key['roles']));clock=ServiceState(team=team);left=None;keep=False
    history=next(h for h in view['histories'] if h['target_id']==j)
    segment=next((s for s in history['segments'] if s['segment_id']==history['active_segment_id']),None)
    if segment and [(m['robot_id'],m['role']) for m in segment['team']]==list(team):
        raw=segment['latest_clock'];clock=ServiceState(base=raw['base'],intervals=raw['intervals'],team=team)
        ep=segment['latest_endpoint'];left=(ep['G'],ep['quality']['status']);keep=True
    if left is None:left=endpoint(view,j,key,view['tick'],positions,cfg)
    start=view['tick'];end=min(view['end_tick'],start+60);energy=0.;completion=None;escape=None;frames=[];events=[]
    scope=digest(view)
    for tick in range(start+1,end+1):
        p,v=trajectory(view['beliefs'][j],tick-1);elapsed=.05
        active=completion is None and escape is None
        if active and p[0]>=cfg.side:elapsed=0.;escape=(tick-1)*.05
        elif active and v[0]>0 and p[0]+v[0]*.05>=cfg.side:elapsed=(cfg.side-p[0])/v[0];escape=(tick-1)*.05+elapsed
        control=np.zeros_like(positions)
        # A terminal branch holds position; it never changes the real world.
        if active:
            for robot,role in team:
                ck=(scope,j,robot,role,tick-1)
                if cache is not None and ck in cache:pos,u=deepcopy(cache[ck])
                else:
                    u=command(view['beliefs'][j],tick-1,[positions[robot]],[role],cfg)[0]
                    pos=positions[robot]+u*elapsed
                    if cache is not None:cache[ck]=(pos.copy(),u.copy())
                positions[robot]=pos;control[robot]=u
            energy+=float(np.sum(control**2))*elapsed
            if escape is not None:events.append(dict(kind='ESCAPED',tick=tick,time=escape))
            else:
                right=endpoint(view,j,key,tick,positions,cfg)
                clock,done,resets=advance_clock(clock,target['service_duration'],team,left[0] and right[0] and left[1]==right[1]=='PASS',tick*.05)
                events.extend(dict(kind='RESET',**r) for r in resets);left=right
                if done:completion=tick*.05;events.append(dict(kind='COMPLETED',tick=tick,time=completion))
        frames.append(dict(tick=tick,positions=positions.tolist(),control=control.tolist(),progress=clock.progress,G=left[0],Q=left[1]))
    # Baseline is the same public belief target left unserved, not truth.
    b=view['beliefs'][j];p,v=trajectory(b,start);base_escape=math.inf
    if p[0]>=cfg.side:base_escape=start*.05
    elif v[0]>0:
        crossing=start*.05+(cfg.side-p[0])/v[0]
        expiry=math.inf if b['last_observation_tick'] is None else (b['estimate_tick']+20)*.05
        if crossing<=expiry:base_escape=crossing
    until=end*.05;stop=completion if completion is not None else min(until,escape if escape is not None else math.inf)
    comp=components(view['config'],target,start*.05,stop,completion is not None,energy,until)
    absolute=absolute_O(comp);baseline=absolute_O(components(view['config'],target,start*.05,min(until,base_escape),False,0.,until))
    if digest(view)!=before:raise ValueError('Policy input mutated')
    return dict(key=deepcopy(key),absolute_O=absolute,baseline=baseline,v=float(absolute-baseline),components=comp,frames=frames,events=events,kept_history=keep,final_clock=dict(base=clock.base,intervals=clock.intervals,team=list(team)))

def decide(view,method='R'):
    if view.get('kind')!='A1_POLICY_INPUT':raise ValueError('Explicit A1 input required')
    if method not in ('R','S_NEW'):raise ValueError('Unknown method')
    keys=catalogue(dict(targets=view['targets'],config=view['config']));rows=[]
    for i,key in enumerate(keys):
        if i%4==0:cache={} if method=='S_NEW' else None
        rows.append(evaluate(view,key,cache))
    specs=[SimpleNamespace(**key,index=i,mask=sum(1<<r for r in key['robots'])) for i,key in enumerate(keys)]
    obs=SimpleNamespace(config=Config(**view['config']),assignment=tuple(Assignment(**a) for a in view['assignment']))
    chosen,units=solve(obs,specs,[r['v'] for r in rows]);actions=[dict(target=None,role='none') for _ in view['positions']]
    for i in chosen:
        for robot,role in zip(keys[i]['robots'],keys[i]['roles']):actions[robot]=dict(target=keys[i]['target'],role=role)
    base=0.
    for j in sorted({k['target'] for k in keys}):base+=next(r['baseline'] for k,r in zip(keys,rows) if k['target']==j)
    return dict(selected_indices=list(chosen),actions=actions,rows=rows,exact_value=str(Fraction.from_float(base)+Fraction(units,SCALE)))
