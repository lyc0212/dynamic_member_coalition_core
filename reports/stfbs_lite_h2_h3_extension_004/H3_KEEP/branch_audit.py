import math
from copy import deepcopy
import numpy as np
from pursuit_v2.config import Config
from pursuit_v2.observation_geometry import offset,radius
def legacy_clock_audit(result,view):
    clocks={};left={};teams={};targets={t['id']:t for t in view['targets']};cfg=Config(**view['config'])
    for h in view['histories']:
        j=h['target_id'];s=next((s for s in h['segments'] if s['segment_id']==h['active_segment_id']),None)
        clocks[j]=deepcopy(s['latest_clock']) if s else dict(base=0.,intervals=0,team=[])
        teams[j]=deepcopy(s['team']) if s else [];left[j]=deepcopy(s['latest_endpoint']) if s else None
    feedback={};left_feedback={}
    for f in result['feedback']:
        k=(f['frame']['target_id'],f['frame']['tick']);feedback.setdefault(k,f);left_feedback[k]=f
    boundaries={b['tick']:b for b in result['boundaries']};checked=0
    for frame in result['frames']:
        n=frame['tick'];boundary=boundaries.get(n-1)
        if boundary:
            for j in targets:
                team=[dict(robot_id=i,role=a['role']) for i,a in enumerate(boundary['after']) if a['target']==j]
                if team!=teams[j]:
                    clocks[j]=dict(base=0.,intervals=0,team=deepcopy(team));teams[j]=team
                    left[j]=left_feedback[j,n-1]['endpoint'] if team else None
        for j,t in targets.items():
            terminal=next((e for e in result['events'] if e['target']==j and e['kind'] in ('completed','escaped','unfinished')),None)
            if not teams[j] or terminal and terminal['time']<(n-1)*.05-1e-10:continue
            if terminal and terminal['kind']=='escaped' and terminal['time']<=n*.05+1e-10:
                teams[j]=[];continue
            row=feedback.get((j,n))
            if row is None:raise ValueError('Missing MODEL endpoint evidence')
            right=row['endpoint'];motion=result['world']['motion'][j]
            p=np.asarray(motion['position'])+np.asarray(motion['velocity'])*((n-60)*.05)
            positions={int(r['sensor_id'][1:]):r['position'] for r in row['frame']['records']}
            # Geometry requires positions even for missing sensors; use physical frame.
            actual_G=all(np.linalg.norm(np.asarray(frame['positions'][m['robot_id']])-p-offset(m['role'],cfg))<=radius(cfg) for m in teams[j])
            if actual_G!=right['G']:raise ValueError('MODEL endpoint geometry mismatch')
            valid=left[j]['G'] and right['G'] and left[j]['quality']['status']==right['quality']['status']=='PASS'
            if valid:clocks[j]['intervals']+=1
            else:clocks[j].update(base=0.,intervals=0)
            progress=math.fsum((clocks[j]['base'],clocks[j]['intervals']*.05))
            done=progress>=t['service_duration']-1e-10
            if done:
                if not terminal or terminal['kind']!='completed' or terminal['tick']!=n:raise ValueError('Service completion mismatch')
                teams[j]=[]
            elif frame['clocks'][j] is not None and frame['clocks'][j]!=clocks[j]:raise ValueError('Service clock mismatch')
            left[j]=right;checked+=1
    return dict(status='PASS',checked_intervals=checked)


def service_audit(result,view,*,branch=None):
    from endpoint_graph import connect
    if branch is None:raise ValueError('Real committed branch context required')
    from common import digest,save,require
    records=deepcopy(getattr(branch,'_endpoint_connections',[]));require(len(records)==len(result['feedback']),'UNEXPLAINED_FEEDBACK')
    eps=[];lefts={};intervals=[]
    for h in view['histories']:
        s=next((s for s in h['segments'] if s['segment_id']==h['active_segment_id']),None)
        if s:
            e=s['latest_endpoint'];key='ACTUAL:'+s['segment_id'];eps.append(dict(endpoint_id=key,branch_id=branch.name,target_id=h['target_id'],segment_id=s['segment_id'],stream_id='INHERITED_ACTUAL',frame_id='INHERITED_ACTUAL_D60',tick=60,endpoint_side='INHERITED_ACTUAL_LEFT',event_order=-1,team=s['team'],G=e['G'],Q=e['quality']['status']));lefts[h['target_id']]=eps[-1]
    for n,c in enumerate(records):
        f=result['feedback'][n];require(c['feedback_event_ordinal']==n and c['feedback_digest']==digest(f),'FEEDBACK_BINDING');require(c['branch_id']==branch.name and c['frame_id']==f['frame']['frame_id'] and c['stream_id']==f['frame']['stream_id'],'FRAME_IDENTITY')
        j=c['target_id'];require(c['endpoint']==f['endpoint'] and c['team']==f['endpoint']['team'],'ENDPOINT_IDENTITY')
        segments=branch.histories[j]['segments'];seg=next((s for s in segments if s['segment_id']==c['segment_id']),None);require(seg is not None and seg['team']==c['team'],'SEGMENT_IDENTITY')
        key=f'{branch.name}:feedback{n}';e=dict(c,endpoint_id=key,event_order=n,G=c['endpoint']['G'],Q=c['endpoint']['quality']['status']);eps.append(e)
        if c['endpoint_side']=='MODEL_ASSIGNMENT_LEFT':require(seg['start_tick']==c['tick'] and c['transaction_identity']==f'{branch.name}:ASSIGN:{c["tick"]}','LEFT_TRANSACTION')
        elif c['endpoint_side']=='MODEL_INTERVAL_RIGHT':
            require(j in lefts,'MISSING_LEFT');l=lefts[j];intervals.append(dict(left=l['endpoint_id'],right=key,segment_id=c['segment_id'],transaction_identity=c['transaction_identity']))
        else:raise ValueError('INVALID_ENDPOINT_SIDE')
        lefts[j]=e
    graph=connect(eps,intervals,branch.name);clocks=legacy_clock_audit(result,view)
    save('ENDPOINT_CONNECTION_DETAILS.json',dict(endpoints=eps,connections=graph,clock_audit=clocks,committed_only=True))
    return dict(status='PASS',checked_intervals=len(intervals),detail='ENDPOINT_CONNECTION_DETAILS.json')
