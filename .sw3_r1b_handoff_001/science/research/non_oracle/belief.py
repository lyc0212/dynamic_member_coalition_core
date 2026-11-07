"""Actual-only belief updates and immutable-by-copy decision snapshots."""
from copy import deepcopy
import math

DT=.05

def trajectory(belief, tick):
    origin=belief['estimate_tick'];age=(tick-origin)*DT
    if age<0:raise ValueError('Cannot predict before estimate')
    prior=belief['last_observation_tick'] is None
    span=age if prior else min(age,1.)
    p=[p+v*span for p,v in zip(belief['position_estimate'],belief['velocity_estimate'])]
    v=list(belief['velocity_estimate']) if prior or age<=1. else [0.,0.]
    return p,v

class Beliefs:
    def __init__(self, announcements, *, deferred=False):
        self.announcements=deepcopy(announcements);self.states={};self.pending=[];self.history={};self.consumed=[]
        self.accepted_receipts={}
        if not deferred:
            for a in announcements:self._activate(a)

    def _activate(self,a):
        j=a['id'];self.states[j]=dict(target_id=j,estimate_tick=a['announcement_tick'],available_tick=a['announcement_tick'],position_estimate=list(a['coarse_position']),velocity_estimate=list(a['velocity_prior']),velocity_source='PUBLIC_PRIOR',last_observation_tick=None,source='PUBLIC_PRIOR',status='PRIOR_ONLY',diagnostics=None)
        self.history[j]=[]

    def activate_visible(self,tick,active_ids):
        for a in self.announcements:
            if a['id'] in active_ids and a['announcement_tick']<=tick and a['id'] not in self.states:self._activate(a)
    def enqueue(self,row):
        if row['source']!='ACTUAL':raise ValueError('MODEL observations prohibited')
        if row['available_tick']<row['measurement_tick']:raise ValueError('Negative latency')
        if row['target_id'] not in self.states:raise ValueError('Observation for unannounced target')
        self.pending.append(deepcopy(row))
    def freeze(self,tick):
        remaining=[]
        # Queue boundary is taken before action preparation; same-tick later
        # observations stay queued until the next explicit decision freeze.
        for row in self.pending:
            if row['available_tick']>tick:remaining.append(row);continue
            j=row['target_id'];e=row['estimate'];b=self.states[j]
            self.consumed.append(dict(target_id=j,measurement_tick=row['measurement_tick'],available_tick=row['available_tick'],consumed_tick=tick))
            if e is None or not e.get('has_accepted_estimate') or not e.get('optimizer_converged') or any(e.get(k,True) for k in ('numerical_ill_conditioned','ambiguity_detected','boundary_active','numeric_contract_violation')):continue
            p=e['estimate'];t=row['measurement_tick']
            if len(p)!=2 or not all(math.isfinite(x) for x in p):continue
            if self.history[j] and t<=self.history[j][-1][0]:continue
            previous=next(((s,q) for s,q in reversed(self.history[j]) if t-s>=5),None)
            velocity=list(b['velocity_estimate'])
            if previous:
                s,q=previous;velocity=[(x-y)/((t-s)*DT) for x,y in zip(p,q)]
                limit=next(a['speed_limit'] for a in self.announcements if a['id']==j);speed=math.hypot(*velocity)
                if speed>limit:velocity=[v*limit/speed for v in velocity]
            self.history[j].append((t,list(p)))
            self.accepted_receipts[j]=self.consumed[-1].copy()
            b.update(estimate_tick=t,available_tick=row['available_tick'],position_estimate=list(p),velocity_estimate=velocity,velocity_source='ACTUAL_POSITION_DIFFERENCE' if previous else b['velocity_source'],last_observation_tick=t,source='ACTUAL_WLS',status='OBSERVED',diagnostics=deepcopy(e))
        self.pending=remaining
        snapshot=deepcopy(self.states)
        for b in snapshot.values():
            if b['last_observation_tick'] is not None and tick-b['last_observation_tick']>20:b['status']='DEGRADED'
        return snapshot
