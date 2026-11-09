"""Independent interval/event graph audit; no mutation, sensing or WLS."""
import math
import json
from dataclasses import dataclass
from .stfbs_d1a_replay import digest

def model_segment_id(s):
    return 'MODEL:'+digest({k:s[k] for k in ('model_branch_id','target_id','segment_index','previous_segment_id','start_tick','team')})

@dataclass(frozen=True)
class AuditContext:
    expected_branch_id: str
    prefix_json: str

def register_context(branch_id,histories):
    return AuditContext(branch_id,json.dumps(histories,sort_keys=True))

def audit_histories(histories,actions,statuses,cut,terminal_times=None,*,context=None):
    terminal_times=terminal_times or {};checked=0
    all_model_indices=[]
    for j,h in histories.items():
        if context is None and any(e.get('observation_origin')=='MODEL' for e in h['events']):raise ValueError('External trusted audit context required')
        terminal_events=[e for e in h['events'] if e['kind'] in ('COMPLETED','ESCAPED','EPISODE_END')]
        expected_cut=cut if statuses[j]=='active' else terminal_events[-1].get('processed_tick') if terminal_events else None
        if statuses[j]!='active':
            if type(expected_cut) is not int or not 0<=expected_cut<=cut:raise ValueError('Invalid processed cut')
            when=terminal_events[-1]['at']['time_seconds']
            if not (expected_cut-1)*.05-1e-10<=when<=expected_cut*.05+1e-10:raise ValueError('Terminal time outside processed interval')
        if h['cutoff_tick']!=expected_cut:raise ValueError('History cutoff mismatch')
        if context is not None:
            original=json.loads(context.prefix_json)[str(j)]
            if h['events'][:len(original['events'])]!=original['events']:raise ValueError('D60 event prefix modified')
            for i,s0 in enumerate(original['segments']):
                s=h['segments'][i]
                for key in ('target_id','segment_index','segment_id','previous_segment_id','start_tick','team','opened_by','initial_clock'):
                    if s[key]!=s0[key]:raise ValueError('D60 segment identity modified')
                if s['events'][:len(s0['events'])]!=s0['events']:raise ValueError('D60 segment event prefix modified')
                if s0['closure'] is not None and s!=s0:raise ValueError('Closed D60 segment modified')
            for i,g0 in enumerate(original['unassigned_intervals']):
                g=h['unassigned_intervals'][i]
                for key in ('start_tick','opened_by','opening_event_index'):
                    if g[key]!=g0[key]:raise ValueError('D60 gap identity modified')
                if g0['end_at'] is not None and g!=g0:raise ValueError('Closed D60 gap modified')
            inherited=len(original['events'])
            for e in h['events'][inherited:]:
                if e.get('model_branch_id')!=context.expected_branch_id or e.get('provenance')!='SIMULATED' or e.get('observation_origin')!='MODEL':raise ValueError('Untrusted new event identity')
            for s in h['segments'][len(original['segments']):]:
                if s.get('model_branch_id')!=context.expected_branch_id or s.get('provenance')!='SIMULATED' or s.get('observation_origin')!='MODEL':raise ValueError('Untrusted new segment identity')
            for s in h['segments']:
                ep=s['latest_endpoint']
                oldep=next((x['latest_endpoint'] for x in original['segments'] if x['segment_id']==s['segment_id']),None)
                if ep!=oldep and (ep.get('branch')!=context.expected_branch_id or ep.get('target_id')!=j or ep.get('provenance')!='SIMULATED' or ep.get('observation_origin')!='MODEL'):raise ValueError('Untrusted endpoint identity')
        events=h['events'];indices=[e['event_index'] for e in events]
        if len(set(indices))!=len(indices) or indices!=sorted(indices):raise ValueError('Event indices/order')
        times=[e['at']['time_seconds'] for e in events]
        if any(not math.isfinite(t) for t in times) or times!=sorted(times):raise ValueError('Event time order')
        emap={e['event_index']:e for e in events}
        for e in events:
            if e['target_id']!=j:raise ValueError('Foreign task event')
            if e.get('observation_origin')=='MODEL':
                if e.get('provenance')!='SIMULATED':raise ValueError('MODEL provenance')
                all_model_indices.append(e['event_index'])
        intervals=[];opened=[];previous=None
        for index,s in enumerate(h['segments']):
            if s['segment_index']!=index or s['previous_segment_id']!=previous:raise ValueError('Segment predecessor/order')
            previous=s['segment_id']
            if s.get('contract_id')=='D1A_MODEL_SERVICE_SEGMENT_V1' and (not s.get('model_branch_id') or s['segment_id']!=model_segment_id(s)):raise ValueError('MODEL segment identity')
            if s.get('contract_id')!='D1A_MODEL_SERVICE_SEGMENT_V1':
                from research.information_service_online.public import segment_identity
                if s['segment_id']!=segment_identity(s):raise ValueError('Inherited segment identity')
            team=s['team']
            if len(team)!=2 or len({m['robot_id'] for m in team})!=2 or {m['role'] for m in team}!={'dual_neg45','dual_pos45'}:raise ValueError('Invalid history team')
            if s['latest_clock']['team']!=team or s['initial_clock']['team']!=team:raise ValueError('Clock team')
            if s['initial_clock']['base']!=0. or s['initial_clock']['intervals']!=0:raise ValueError('Nonzero initial clock')
            clock=s['latest_clock']
            if clock['base']<0 or type(clock['intervals']) is not int or clock['intervals']<0:raise ValueError('Invalid clock')
            endpoint=s['latest_endpoint']
            if endpoint.get('observation_origin')=='MODEL' and (endpoint.get('provenance')!='SIMULATED' or endpoint.get('target_id')!=j or endpoint.get('team')!=team):raise ValueError('MODEL endpoint identity/provenance')
            if not s['start_tick']<=endpoint['tick']<=cut:raise ValueError('Endpoint time')
            if clock['base']+clock['intervals']*.05>0 and (not endpoint['G'] or endpoint['quality']['status']!='PASS'):raise ValueError('Progress on invalid endpoint')
            for event in s['events']:
                if emap.get(event['event_index'])!=event or event['segment_id']!=s['segment_id']:raise ValueError('Segment event reference')
            if {e['event_index'] for e in events if e.get('segment_id')==s['segment_id']}!={e['event_index'] for e in s['events']}:raise ValueError('Missing segment event link')
            opening=[e for e in s['events'] if e['kind']=='ASSIGNED']
            if len(opening)!=1 or abs(opening[0]['at']['time_seconds']-s['start_tick']*.05)>1e-10:raise ValueError('Segment opening event')
            close=s['closure']
            if close is None:stop=cut*.05;opened.append(('segment',s))
            else:
                if close.get('reason') not in ('WITHDRAWN','TEAM_CHANGED','ROLE_CHANGED','COMPLETED','ESCAPED','EPISODE_END'):raise ValueError('Closure reason')
                event=emap.get(close.get('closing_event_index'))
                if event is None or event['at']!=close.get('at') or event['segment_id']!=s['segment_id']:raise ValueError('Closure event/time')
                expected={'WITHDRAWN':'WITHDRAWN','TEAM_CHANGED':'TEAM_CHANGED','ROLE_CHANGED':'ROLE_CHANGED','COMPLETED':'COMPLETED','ESCAPED':'ESCAPED','EPISODE_END':'EPISODE_END'}[close['reason']]
                if event['kind']!=expected:raise ValueError('Closure event reason')
                if event.get('observation_origin')=='MODEL':
                    progress=clock['base']+clock['intervals']*.05
                    after=0. if expected in ('WITHDRAWN','TEAM_CHANGED','ROLE_CHANGED') else progress
                    if event['progress_before']!=progress or event['progress_after']!=after:raise ValueError('Closure progress mismatch')
                stop=close['at']['time_seconds']
            intervals.append((s['start_tick']*.05,stop))
        for gap in h['unassigned_intervals']:
            op=emap.get(gap['opening_event_index'])
            if op is None or abs(op['at']['time_seconds']-gap['start_tick']*.05)>1e-10:raise ValueError('Gap opening reference/time')
            if gap['end_at'] is None:
                if gap['closing_event_index'] is not None:raise ValueError('Open gap closure')
                stop=cut*.05;opened.append(('gap',gap))
            else:
                cl=emap.get(gap['closing_event_index'])
                if cl is None or cl['at']!=gap['end_at']:raise ValueError('Gap closing reference')
                if cl['kind'] not in ('ASSIGNED','COMPLETED','ESCAPED','EPISODE_END'):raise ValueError('Gap closing reason')
                stop=gap['end_at']['time_seconds']
            intervals.append((gap['start_tick']*.05,stop))
        cursor=h['birth_tick']*.05
        for lo,hi in sorted(intervals):
            if hi<lo-1e-10 or abs(lo-cursor)>1e-10:raise ValueError('History coverage overlap/gap')
            cursor=hi
        end=terminal_times.get(j,cut*.05)
        if abs(cursor-end)>1e-10:raise ValueError('History incomplete coverage')
        team=[dict(robot_id=i,role=a['role']) for i,a in enumerate(actions) if a['target']==j]
        if statuses[j]=='active':
            if len(opened)!=1:raise ValueError('Current state not unique')
            if team:
                if opened[0][0]!='segment' or opened[0][1]['team']!=team or h['active_segment_id']!=opened[0][1]['segment_id']:raise ValueError('Assigned history mismatch')
                if opened[0][1]['latest_endpoint']['tick']!=cut:raise ValueError('Stale current endpoint')
            elif opened[0][0]!='gap' or h['active_segment_id'] is not None:raise ValueError('Unassigned history mismatch')
        else:
            if opened or team or h['active_segment_id'] is not None:raise ValueError('Terminal residual active state')
            expected={'completed':'COMPLETED','escaped':'ESCAPED','unfinished':'EPISODE_END'}.get(statuses[j])
            terminal=[e for e in events if e['kind'] in ('COMPLETED','ESCAPED','EPISODE_END')]
            if expected is None or len(terminal)!=1 or terminal[0]['kind']!=expected or abs(terminal[0]['at']['time_seconds']-end)>1e-10:raise ValueError('Terminal event/status mismatch')
        checked+=1
    if len(all_model_indices)!=len(set(all_model_indices)):raise ValueError('Duplicate MODEL global event index')
    return dict(status='PASS',tasks=checked,model_events=len(all_model_indices))

def audit_branch(branch,context=None):
    context=branch._audit_context if context is None else context
    if branch.name!=context.expected_branch_id:raise ValueError('Trusted branch mismatch')
    terminal={e['target']:e['time'] for e in branch.events if e['kind'] in ('completed','escaped','unfinished')}
    result=audit_histories(branch.histories,branch.actions,branch.status,branch.tick,terminal,context=context)
    for e in branch.events:
        if e['kind'] in ('completed','escaped','unfinished'):
            entries=[x for x in branch.histories[e['target']]['events'] if x['kind'] in ('COMPLETED','ESCAPED','EPISODE_END')]
            if len(entries)!=1 or entries[0]['processed_tick']!=e['processed_tick'] or entries[0]['at']['time_seconds']!=e['time']:raise ValueError('Terminal metadata disagreement')
    for h in branch.histories.values():
        for s in h['segments']:
            ep=s['latest_endpoint']
            if ep.get('observation_origin')=='MODEL' and ep.get('branch')!=branch.name:raise ValueError('Cross-branch endpoint')
    fees=0.
    for b in branch.boundaries:
        n=sum(x!=y for x,y in zip(b['before'],b['after']))
        if b['changes']!=n or b['cost']!=branch.cfg.change_cost*n:raise ValueError('Boundary charge mismatch')
        fees+=b['cost']
    if fees!=branch.change_cost:raise ValueError('Spurious or repeated fee')
    for e in branch.events:
        if e['kind'] in ('completed','escaped','unfinished') and e.get('release_change_cost')!=0.:raise ValueError('Charged natural release')
    return dict(result,change_cost=fees)
