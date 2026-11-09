"""MODEL-only staged history mutations; independent audit lives separately."""
from copy import deepcopy
from .stfbs_d1a_history_audit import model_segment_id

def event(branch,j,kind,segment_id=None,when=None):
    when=branch.tick*.05 if when is None else when
    index=1+max((e['event_index'] for h in branch.histories.values() for e in h['events']),default=-1)
    tick=round(when/.05)
    segment=next((s for s in branch.histories[j]['segments'] if s['segment_id']==segment_id),None)
    before=0. if segment is None else segment['latest_clock']['base']+segment['latest_clock']['intervals']*.05
    after=0. if kind in ('WITHDRAWN','TEAM_CHANGED','ROLE_CHANGED','ASSIGNED') else before
    e=dict(event_index=index,target_id=j,kind=kind,segment_id=segment_id,
        model_branch_id=branch.name,
        at=dict(time_seconds=when,event_tick=tick if abs(when-tick*.05)<=1e-10 else None),
        progress_before=before,progress_after=after,reasons=[],provenance='SIMULATED',observation_origin='MODEL')
    h=branch.histories[j];h['events'].append(e)
    if segment_id:
        next(s for s in h['segments'] if s['segment_id']==segment_id)['events'].append(deepcopy(e))
    return e

def close_segment(s,e,reason):
    s['closure']=dict(reason=reason,at=deepcopy(e['at']),closing_event_index=e['event_index'])

def prepare_assignment(branch,actions):
    for j in branch.targets:
        if branch.status[j]!='active':continue
        h=branch.histories[j];old=branch.segment(j)
        team=[dict(robot_id=i,role=a['role']) for i,a in enumerate(actions) if a['target']==j]
        if old and old['team']==team:
            old['first_fusion_tick']=branch.tick+1;continue
        if old:
            reason='WITHDRAWN' if not team else 'ROLE_CHANGED' if [m['robot_id'] for m in old['team']]==[m['robot_id'] for m in team] else 'TEAM_CHANGED'
            e=event(branch,j,reason,old['segment_id']);close_segment(old,e,reason)
            if not team:h['unassigned_intervals'].append(dict(start_tick=branch.tick,end_at=None,opened_by='WITHDRAWAL',opening_event_index=e['event_index'],closing_event_index=None))
        h['active_segment_id']=None
        if team:
            zero=dict(base=0.,intervals=0,team=deepcopy(team))
            s=dict(target_id=j,segment_index=len(h['segments']),previous_segment_id=h['segments'][-1]['segment_id'] if h['segments'] else None,start_tick=branch.tick,team=team,initial_clock=deepcopy(zero),latest_clock=deepcopy(zero),closure=None,events=[],contract_id='D1A_MODEL_SERVICE_SEGMENT_V1',opened_by='FIRST_ASSIGNMENT' if not h['segments'] else 'REASSIGNMENT',first_fusion_tick=branch.tick)
            s['model_branch_id']=branch.name;s['segment_id']=model_segment_id(s);h['segments'].append(s);h['active_segment_id']=s['segment_id']
            e=event(branch,j,'ASSIGNED',s['segment_id'])
            for gap in h['unassigned_intervals']:
                if gap['end_at'] is None:gap.update(end_at=deepcopy(e['at']),closing_event_index=e['event_index'])
            s['latest_endpoint']=branch.fuse(j,s,branch.tick)
            ep=s['latest_endpoint']
            if ep.get('branch')!=branch.name or ep.get('target_id')!=j or ep.get('team')!=team:raise ValueError('Foreign MODEL endpoint identity')
    branch.actions=deepcopy(actions)

def prepare_terminal(branch,j,status,when):
    h=branch.histories[j];s=branch.segment(j);kind={'completed':'COMPLETED','escaped':'ESCAPED','unfinished':'EPISODE_END'}[status]
    e=event(branch,j,kind,s['segment_id'] if s else None,when)
    if s:close_segment(s,e,kind)
    for gap in h['unassigned_intervals']:
        if gap['end_at'] is None:gap.update(end_at=deepcopy(e['at']),closing_event_index=e['event_index'])
    h['active_segment_id']=None;branch.status[j]=status
    for task,history in branch.histories.items():
        if task==j or branch.status[task]=='active':history['cutoff_tick']=branch.tick
    for i,a in enumerate(branch.actions):
        if a['target']==j:branch.actions[i]=dict(target=None,role='none')
    branch.events.append(dict(target=j,kind=status,time=when,tick=branch.tick,release_change_cost=0.))
    if status=='completed':branch.components['completion']+=branch.targets[j]['weight']/branch.cfg.weight_reference
