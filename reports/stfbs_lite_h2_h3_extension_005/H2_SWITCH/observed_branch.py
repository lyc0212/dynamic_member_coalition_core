from common import *
from math import hypot,isfinite

def conditions(row,history):
 e=row['estimate']
 if e is None:return ['ESTIMATE_MISSING']
 out=[]
 if not e.get('has_accepted_estimate'):out.append('NO_ACCEPTED_ESTIMATE')
 if not e.get('optimizer_converged'):out.append('OPTIMIZER_NOT_CONVERGED')
 for k in ['numerical_ill_conditioned','ambiguity_detected','boundary_active','numeric_contract_violation']:
  if e.get(k,True):out.append(k.upper())
 if out:return out
 p=e['estimate']
 if len(p)!=2:return ['INVALID_ESTIMATE_DIMENSION']
 if not all(isfinite(x) for x in p):return ['NONFINITE_ESTIMATE']
 if history and row['measurement_tick']<=history[-1][0]:return ['NONINCREASING_MEASUREMENT_TICK']
 return []

def make_branch(Base):
 class Observed(Base):
  def fuse(self,j,segment,tick):
   endpoint=super().fuse(j,segment,tick);f=self.feedback[-1]
   record=dict(branch_id=self.name,target_id=j,segment_id=segment['segment_id'],stream_id=f['frame']['stream_id'],frame_id=f['frame']['frame_id'],tick=tick,endpoint_side=self._phase,feedback_event_ordinal=len(self.feedback)-1,transaction_identity=self._transaction,team=deepcopy(segment['team']),endpoint=deepcopy(endpoint),feedback_digest=digest(f))
   self._endpoint_connections=getattr(self,'_endpoint_connections',[])+[record]
   return endpoint
  def assign(self,actions,**kwargs):
   self._phase='MODEL_ASSIGNMENT_LEFT';self._transaction=f'{self.name}:ASSIGN:{self.tick}'
   before=deepcopy(self.histories);n=len(self.feedback)
   super().assign(actions,**kwargs)
   save('D%d_TRANSACTION.json'%self.tick,dict(transaction_identity=self._transaction,before_histories=before,after_histories=deepcopy(self.histories),boundary=deepcopy(self.boundaries[-1]),committed_feedback_ordinals=list(range(n,len(self.feedback))),connections=deepcopy(getattr(self,'_endpoint_connections',[]))))
  def advance(self):
   self._phase='MODEL_INTERVAL_RIGHT';self._transaction=f'{self.name}:ADVANCE:{self.tick+1}'
   super().advance()
  def policy_view(self):
   before=deepcopy(self.consumer);events=[];queue=deepcopy(before.pending);pending=[]
   previous_events=getattr(self,'_queue_audit',[])
   for ordinal,row in enumerate(queue):
    j=row['target_id'];t=row['measurement_tick'];origin=row.get('observation_origin','SOURCE_UNRESOLVED')
    if row['available_tick']>self.tick:
     pending.append(row);events.append(dict(queue_ordinal=ordinal,target_id=j,measurement_tick=t,available_tick=row['available_tick'],status='PENDING',observation_origin=origin));continue
    hist=deepcopy(before.history[j]);state=deepcopy(before.states[j]);reasons=conditions(row,hist)
    before.pending=[row];before.freeze(self.tick);accepted=len(before.history[j])>len(hist)
    require(accepted==(not reasons),'ACCEPTANCE_RULE_REPLAY_MISMATCH')
    model_index=sum(e.get('status')!='PENDING' and e.get('observation_origin')=='MODEL' for e in previous_events+events)
    f=self.feedback[model_index] if origin=='MODEL' else None
    if f is not None:require(f['frame']['target_id']==j and f['frame']['tick']==t and f['result']['estimate_result']==row['estimate'],'MODEL_OBSERVATION_BINDING')
    event_id=f'{self.name}:freeze{self.tick}:queue{ordinal}';speed=None
    if accepted:
     p=row['estimate']['estimate'];old_index=next((i for i in range(len(hist)-1,-1,-1) if t-hist[i][0]>=5),None)
     if old_index is not None:
      s,q=hist[old_index];dt=(t-s)*.05;delta=[x-y for x,y in zip(p,q)];raw=[d/dt for d in delta];limit=next(a['speed_limit'] for a in before.announcements if a['id']==j);norm=hypot(*raw);scale=limit/norm if norm>limit else 1.;velocity=[v*limit/norm for v in raw] if norm>limit else raw
      source=next((e for e in reversed(previous_events+events) if e.get('accepted') and e['target_id']==j and e['accepted_history_index']==old_index),None)
      speed=dict(current_event=event_id,current_tick=t,current_position=p,current_origin=origin,previous_event=source['event_id'] if source else 'SOURCE_UNRESOLVED',previous_origin=source['observation_origin'] if source else 'SOURCE_UNRESOLVED',previous_tick=s,previous_position=q,history_index=old_index,tick_interval=t-s,DT=.05,position_difference=delta,unclipped_velocity=raw,unclipped_norm=norm,speed_limit=limit,clipped=norm>limit,scale=scale,velocity=velocity)
     else:
      velocity=state['velocity_estimate'];speed=dict(current_event=event_id,retained_velocity=velocity,retained_velocity_source=state['velocity_source'],previous_source_chain='seed or previous accepted event retained')
     require(velocity==before.states[j]['velocity_estimate'],'VELOCITY_REPLAY')
     speed['final_velocity_source']=before.states[j]['velocity_source']
    events.append(dict(event_id=event_id,queue_ordinal=ordinal,target_id=j,measurement_tick=t,available_tick=row['available_tick'],consumed_tick=self.tick,observation_origin=origin,feedback_identity=f['frame']['frame_id'] if f else 'SOURCE_UNRESOLVED',feedback_digest=digest(f) if f else None,status='ACCEPTED' if accepted else 'REJECTED',accepted=accepted,rejected=not accepted,rejection_conditions=reasons,accepted_history_index=len(before.history[j])-1 if accepted else None,accepted_receipt=deepcopy(before.accepted_receipts[j]) if accepted else None,speed_provenance=speed))
   result=super().policy_view()
   require(before.states==self.consumer.states and before.history==self.consumer.history and before.accepted_receipts==self.consumer.accepted_receipts and pending==self.consumer.pending,'CONSUMER_STATE_REPLAY')
   self._queue_audit=previous_events+events
   return result
 return Observed
