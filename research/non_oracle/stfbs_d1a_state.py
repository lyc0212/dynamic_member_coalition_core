"""Isolated MODEL replay state and first-outcome raw measurement cache."""
from copy import deepcopy
from .belief import Beliefs
from .stfbs_d1a_replay import digest

class ModelBeliefConsumer(Beliefs):
    def __init__(self,seed):
        super().__init__(seed['announcements'],deferred=True)
        for attr,key in (('states','internal_states_at_D60'),('history','accepted_position_history'),
            ('pending','pending_observations'),('consumed','consumed_records'),('accepted_receipts','accepted_receipts')):
            setattr(self,attr,deepcopy(seed[key]))
        self.model_measurements=[]
    def enqueue(self,row):
        if row.get('provenance')!='SIMULATED' or row.get('observation_origin')!='MODEL':
            raise ValueError('MODEL provenance required')
        if row['available_tick']<row['measurement_tick'] or row['target_id'] not in self.states:
            raise ValueError('Invalid MODEL observation')
        self.pending.append(deepcopy(row));self.model_measurements.append(deepcopy(row))
    # The production mathematical freeze is reused without calling ACTUAL enqueue.
    # Historical descriptive state fields retain the production schema; the
    # consumer, input observations and outer execution identity are always MODEL.

class ModelRawCache:
    def __init__(self,branch,historical=()):
        self.branch=branch;self.rows={};self.history=deepcopy(list(historical))
        self.counts=dict(requests=0,new=0,reuses=0,conflicts=0,inherited_reuses=0)
    def query(self,branch,target,robot,tick,context,producer):
        if branch!=self.branch:raise ValueError('Foreign MODEL branch')
        key=(branch,target,robot,tick);ctx=digest(context);self.counts['requests']+=1
        for row in self.history:
            if row['slot']['slot_key']==dict(target_id=target,robot_id=robot,tick=tick) and row['slot']['state']!='UNQUERIED':
                if row['context_digest']!=ctx:
                    self.counts['conflicts']+=1;raise ValueError('Historical raw context conflict')
                self.counts['inherited_reuses']+=1
                return deepcopy(row['slot'])
        if key in self.rows:
            if digest(self.rows[key]['slot'])!=self.rows[key]['slot_digest']:
                raise ValueError('MODEL raw slot digest changed')
            if self.rows[key]['context_digest']!=ctx:
                self.counts['conflicts']+=1;raise ValueError('MODEL raw context conflict')
            self.counts['reuses']+=1
            return deepcopy(self.rows[key]['slot'])
        slot=producer()
        if slot['state'] not in ('VALID','MISSING') or slot['slot_key']!=dict(target_id=target,robot_id=robot,tick=tick):
            raise ValueError('Invalid produced raw slot')
        self.rows[key]=dict(context_digest=ctx,slot=deepcopy(slot),slot_digest=digest(slot))
        self.counts['new']+=1
        return deepcopy(slot)
