"""D1-A isolated joint MODEL kernel. No actual Environment or STEP is called."""
from copy import deepcopy
import math
from time import process_time,monotonic
from unittest.mock import patch
import numpy as np
from pursuit_v2.config import Config
from pursuit_v2.observation_geometry import offset,radius
from pursuit_v2.service import ServiceState,advance_clock,TOL
from research.information_service_online import public
from research.information_service_bridge.public_stream import BridgeFrameProcessor
from research.cooperative_sensing.estimator import estimate
from . import policy
from .belief import trajectory
from .stfbs_d1a_replay import digest
from .stfbs_d1a_state import ModelRawCache,ModelBeliefConsumer

class Budget:
    def __init__(self):
        self.cpu=process_time();self.wall=monotonic();self.counts=dict(MODEL_OBSERVATION_WLS=0,MODEL_POLICY_EVALUATION_WLS=0,ACTUAL_WLS=0)
    def check(self):
        if process_time()-self.cpu>600 or monotonic()-self.wall>900:raise RuntimeError('D1-A time budget')
    def estimator(self,kind):
        def call(payload):
            self.check();self.counts[kind]+=1
            if self.counts[kind]>(1000 if kind=='MODEL_OBSERVATION_WLS' else 4000) or sum(self.counts.values())>5000:raise RuntimeError('D1-A WLS budget')
            return estimate(payload)
        return call
    def choose(self,view):
        with patch.object(policy,'estimate',self.estimator('MODEL_POLICY_EVALUATION_WLS')):
            return policy.decide(view,method='R')

def nominal_world(view):
    motions={t['id']:dict(position=list(trajectory(view['beliefs'][t['id']],60)[0]),velocity=list(trajectory(view['beliefs'][t['id']],60)[1])) for t in view['targets']}
    world=dict(public_digest=digest(view),motion=motions,start_tick=60,end_tick=120,
        motion_rule='constant_velocity_from_public_D60_v1',perturbation='zero_v1',provenance='SIMULATED',observation_origin='MODEL')
    world['world_digest']=digest(world)
    return world

def point(world,j,tick):
    m=world['motion'][j]
    return np.asarray(m['position'])+np.asarray(m['velocity'])*((tick-60)*.05)

class Branch:
    def __init__(self,view,seed,world,name,budget):
        identity=deepcopy(world);saved=identity.pop('world_digest',None)
        if world.get('public_digest')!=digest(view) or saved!=digest(identity):
            raise ValueError('MODEL world/public identity mismatch')
        self.view=deepcopy(view);self.world=deepcopy(world);self.name=name;self.budget=budget
        self.cfg=Config(**view['config']);self.tick=60;self.positions=np.array(view['positions']);self.actions=deepcopy(view['assignment'])
        self.targets={t['id']:deepcopy(t) for t in view['targets']};self.histories={h['target_id']:deepcopy(h) for h in view['histories']}
        self.profiles=deepcopy(view['sensor_profiles']);self.consumer=ModelBeliefConsumer(seed);self.frozen=deepcopy(view['beliefs'])
        self.status={j:'active' for j in self.targets};self.streams={};self.frames=[];self.events=[];self.boundaries=[];self.feedback=[];self.decisions=[]
        self.components={k:0. for k in ('completion','flow','late','effort','terminal')};self.change_cost=0.;self.fusions=0
        historical=[]
        for slot in view['current_slots']:
            if slot['state']!='UNQUERIED':
                i=slot['slot_key']['robot_id'];profile=self.profiles[i]
                if public.seal_slot(slot)!=slot:raise ValueError('Historical slot digest')
                if slot['state']=='VALID' and (slot['packet']['position']!=view['positions'][i] or slot['packet']['sigma']!=profile['sigma']):raise ValueError('Historical slot context')
                historical.append(dict(slot=deepcopy(slot),context_digest=digest(dict(position=view['positions'][i],sigma=profile['sigma'],health=profile['health']))))
        self.cache=ModelRawCache(name,historical)
    def segment(self,j):
        h=self.histories[j]
        return next((s for s in h['segments'] if s['segment_id']==h['active_segment_id']),None)
    def raw(self,j,i,tick):
        profile=self.profiles[i];pos=self.positions[i].tolist();ctx=dict(position=pos,sigma=profile['sigma'],health=profile['health'])
        def producer():
            packet=None;state='MISSING'
            if profile['health']=='available':
                p=point(self.world,j,tick);angle=math.atan2(float(p[1]-pos[1]),float(p[0]-pos[0]));bearing=(angle+math.pi)%(2*math.pi)-math.pi
                packet=dict(sensor_id=f'U{i}',position=pos,bearing=bearing,sigma=profile['sigma'],measurement_tick=tick,available_tick=tick,status='ok');state='VALID'
            return public.seal_slot(dict(slot_key=dict(target_id=j,robot_id=i,tick=tick),state=state,packet=packet,slot_digest=None))
        return self.cache.query(self.name,j,i,tick,ctx,producer)
    def fuse(self,j,segment,tick):
        team=segment['team'];stream=f"{self.name}:T{j}:first{segment['first_fusion_tick']}"
        if stream not in self.streams:self.streams[stream]=BridgeFrameProcessor([f"U{m['robot_id']}" for m in team],tick,stream,j,estimator_fn=self.budget.estimator('MODEL_OBSERVATION_WLS'))
        records=[];slots=[]
        for m in team:
            slot=self.raw(j,m['robot_id'],tick);slots.append(slot)
            if slot['state']=='VALID':
                packet=deepcopy(slot['packet']);packet['packet_id']=f"{stream}:tick{tick}:U{m['robot_id']}";records.append(packet)
        frame=dict(contract_id='STAGE2A5B-A-MINIMAL-v0.2',stream_id=stream,frame_id=f'{stream}:tick{tick}',target_id=j,tick=tick,measurement_time=tick*.05,available_time=tick*.05,records=records)
        result=self.streams[stream].process(frame);self.fusions+=1
        p=point(self.world,j,tick)
        G=all(np.linalg.norm(self.positions[m['robot_id']]-p-offset(m['role'],self.cfg))<=radius(self.cfg) for m in team)
        endpoint=dict(tick=tick,G=bool(G),quality=deepcopy(result['quality']),provenance='SIMULATED',observation_origin='MODEL',branch=self.name)
        row=dict(source='MODEL',provenance='SIMULATED',observation_origin='MODEL',target_id=j,measurement_tick=tick,available_tick=tick,estimate=deepcopy(result['estimate_result']))
        self.consumer.enqueue(row);self.feedback.append(dict(branch=self.name,frame=frame,result=result,endpoint=endpoint,slots=slots))
        return endpoint
    def assign(self,actions):
        if len(actions)!=3:raise ValueError('Incomplete Assignment')
        change=sum(a!=b for a,b in zip(self.actions,actions));self.change_cost+=self.cfg.change_cost*change
        self.boundaries.append(dict(tick=self.tick,before=deepcopy(self.actions),after=deepcopy(actions),changes=change,cost=self.cfg.change_cost*change))
        for j in self.targets:
            if self.status[j]!='active':continue
            team=[dict(robot_id=i,role=a['role']) for i,a in enumerate(actions) if a['target']==j]
            if team and (len(team)!=2 or {m['role'] for m in team}!={'dual_neg45','dual_pos45'}):raise ValueError('Invalid q2 team')
            old=self.segment(j)
            if old and old['team']==team:
                old['first_fusion_tick']=self.tick+1
                continue
            h=self.histories[j]
            if old:old['closure']=dict(reason='MODEL_ASSIGNMENT_CHANGE',tick=self.tick)
            h['active_segment_id']=None
            if team:
                s=dict(target_id=j,segment_index=len(h['segments']),previous_segment_id=h['segments'][-1]['segment_id'] if h['segments'] else None,start_tick=self.tick,opened_by='MODEL_ASSIGNMENT',initial_clock=dict(base=0.,intervals=0,team=team),events=[],contract_id='D1A_MODEL_SERVICE_SEGMENT_V1',segment_id=f'{self.name}:{j}:{self.tick}',team=team,latest_clock=dict(base=0.,intervals=0,team=team),closure=None,first_fusion_tick=self.tick)
                h['segments'].append(s);h['active_segment_id']=s['segment_id'];s['latest_endpoint']=self.fuse(j,s,self.tick)
        self.actions=deepcopy(actions)
    def finish(self,j,status,time):
        self.status[j]=status;self.events.append(dict(target=j,kind=status,time=time,tick=self.tick))
        s=self.segment(j)
        if s:s['closure']=dict(reason=status,tick=self.tick)
        self.histories[j]['active_segment_id']=None
        for i,a in enumerate(self.actions):
            if a['target']==j:self.actions[i]=dict(target=None,role='none')
        if status=='completed':self.components['completion']+=self.targets[j]['weight']/self.cfg.weight_reference
    def advance(self):
        self.budget.check();lo=self.tick*.05;self.tick+=1;hi=self.tick*.05
        before=self.positions.copy();control=np.zeros_like(self.positions);elapsed=[0.]*3;running=[]
        for j,t in self.targets.items():
            if self.status[j]!='active':continue
            p=point(self.world,j,self.tick-1);v=self.world['motion'][j]['velocity'];escape=lo if p[0]>=self.cfg.side else lo+(self.cfg.side-p[0])/v[0] if v[0]>0 else math.inf
            stop=min(hi,escape);dt=max(0.,stop-lo);s=self.segment(j)
            if s:
                for m in s['team']:
                    i=m['robot_id'];u=policy.command(self.frozen[j],self.tick-1,[self.positions[i]],[m['role']],self.cfg)[0]
                    self.positions[i]+=u*dt;control[i]=u;elapsed[i]=dt
                if escape<=hi+TOL:self.finish(j,'escaped',escape)
                else:
                    left=s['latest_endpoint'];right=self.fuse(j,s,self.tick);raw=s['latest_clock'];team=tuple((m['robot_id'],m['role']) for m in s['team'])
                    clock,done,resets=advance_clock(ServiceState(raw['base'],raw['intervals'],team),t['service_duration'],team,left['G'] and right['G'] and left['quality']['status']==right['quality']['status']=='PASS',hi)
                    s['latest_clock']=dict(base=clock.base,intervals=clock.intervals,team=deepcopy(s['team']));s['latest_endpoint']=right
                    for reset in resets:self.events.append(dict(target=j,kind='reset',tick=self.tick,**reset))
                    if done:self.finish(j,'completed',hi)
            elif escape<=hi+TOL:self.finish(j,'escaped',escape)
            flow=t['weight']*max(0.,stop-max(lo,t['birth']));late=t['weight']*max(0.,stop-max(lo,t['birth'],t['deadline']))
            self.components['flow']-=self.cfg.flow_weight*flow/(self.cfg.weight_reference*self.cfg.stage_dt)
            self.components['late']-=self.cfg.late_weight*late/(self.cfg.weight_reference*self.cfg.stage_dt);running.append(dict(target=j,stop=stop,flow=flow,late=late))
        energy=sum(float(np.sum(control[i]**2))*elapsed[i] for i in range(3));self.components['effort']-=self.cfg.control_weight*energy/self.cfg.effort_reference
        if self.tick==120:
            for j in self.targets:
                if self.status[j]=='active':self.finish(j,'unfinished',hi)
            self.components['terminal']=-self.cfg.unfinished_weight*math.fsum(t['weight'] for j,t in self.targets.items() if self.status[j]!='completed')/self.cfg.weight_reference
        self.frames.append(dict(tick=self.tick,before=before.tolist(),positions=self.positions.tolist(),control=control.tolist(),elapsed=elapsed,running=running,energy=energy,assignment=deepcopy(self.actions),status=deepcopy(self.status),clocks={j:deepcopy(self.segment(j)['latest_clock']) if self.segment(j) else None for j in self.targets}))
    def policy_view(self):
        self.frozen=self.consumer.freeze(self.tick)
        active=[j for j in self.targets if self.status[j]=='active'];slots=[]
        for j in active:
            h=self.histories[j];h['cutoff_tick']=self.tick
            h['inherited_actual_history_digest']=self.view['histories'][next(i for i,x in enumerate(self.view['histories']) if x['target_id']==j)].get('history_digest')
            h['contract_id']='D1A_MODEL_TASK_HISTORY_V1'
            for s in h['segments']:
                s.pop('segment_history_digest',None)
                s['segment_history_digest']=digest(s)
            h.pop('history_digest',None);h['history_digest']=digest(h)
        for j in active:
            for i in range(3):
                found=next((deepcopy(v['slot']) for k,v in self.cache.rows.items() if k==(self.name,j,i,self.tick)),None)
                slots.append(found or public.seal_slot(dict(slot_key=dict(target_id=j,robot_id=i,tick=self.tick),state='UNQUERIED',packet=None,slot_digest=None)))
        view=deepcopy(self.view);view.update(tick=self.tick,positions=self.positions.tolist(),assignment=deepcopy(self.actions),targets=[self.targets[j] for j in active],histories=[self.histories[j] for j in active],current_slots=slots,beliefs=deepcopy(self.frozen))
        return view
    def run(self,initial):
        self.assign(initial)
        while self.tick<120:
            self.advance()
            if self.tick in (80,100):
                view=self.policy_view();decision=self.budget.choose(view);self.decisions.append(dict(view=deepcopy(view),choice=decision));self.assign(decision['actions'])
        net=sum(self.components.values())-self.change_cost
        return dict(branch=self.name,world=deepcopy(self.world),provenance='SIMULATED',observation_origin='MODEL',components=self.components,change_cost=self.change_cost,net=net,frames=self.frames,events=self.events,boundaries=self.boundaries,decisions=self.decisions,feedback=self.feedback,status=self.status,raw_counts=self.cache.counts,endpoint_fusions=self.fusions)
