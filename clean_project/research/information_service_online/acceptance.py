"""Read-only decision and paired-future audits of registered saved artifacts."""
from collections import Counter
from fractions import Fraction
from itertools import combinations,permutations,product
import math
from pathlib import Path
from .common import ContractError,digest,read_json,save_json,sha_file
from .quality_audit import close,audit_fusion

META={'frame_id','stream_id','packet_id','frame_sha256','work_identity','work_instance_id','physical_environment_id',
      'work_id','batch_id','request_id','attempt_id','pair_id','implementation','environment_id','flow_context','flow_registration'}
def semantic(value):
    if isinstance(value,dict):return {k:semantic(v) for k,v in value.items() if k not in META}
    if isinstance(value,list):return [semantic(v) for v in value]
    return value

def _authority(path,expected):
    from . import public
    if sha_file(path)!=expected:raise ContractError('Audit actual binding changed')
    return public.HistoryAuthority.from_public_binding(read_json(path))

def _specs(cp):
    result=[];roles={2:['dual_neg45','dual_pos45'],3:['tri_0','tri_120','tri_240']}
    for t in cp['targets']:
        for robots in combinations(range(cp['config']['robots']),t['required_robots']):
            for rr in permutations(roles[t['required_robots']]):
                result.append(dict(index=len(result),target=t['id'],robots=list(robots),roles=list(rr),mask=sum(1<<i for i in robots)))
    return result

def _rows_by_tick(result):
    rows={f['tick']:f for f in result['frames']}
    if sorted(rows)!=list(range(result['start_tick'],result['end_tick']+1)):raise ContractError('Incomplete forecast frame coverage')
    return rows

def audit_prediction(request,result,candidate):
    cp=request['checkpoint'];key=candidate['key'];j=key['target'];frames=_rows_by_tick(result);counts=Counter();seen=set()
    slots={(s['slot_key']['target_id'],s['slot_key']['robot_id']):s for s in cp['current_slots']}
    profiles={p['sensor_id']:p for p in cp['sensor_profiles']};target=next(t for t in cp['targets'] if t['id']==j)
    start=cp['tick'];allowed=['U'+str(i) for i in key['robots']]
    for row in result['sensing_results']:
        frame=row['frame'];tick=frame['tick']
        if (frame['target_id'],tick) in seen:raise ContractError('Duplicate target endpoint solve')
        seen.add((frame['target_id'],tick))
        if row['allowed_sensor_ids']!=allowed:raise ContractError('Candidate allowed team mismatch')
        counts.update(audit_fusion(row)['counts']);sources=row['source_slots']
        context=row['result']['flow_context']
        expected_purpose='INDEPENDENT_REFERENCE' if result.get('implementation') else 'CANDIDATE_PREDICTION'
        if (context['purpose']!=expected_purpose or context['checkpoint_id']!=cp['checkpoint_id'] or
                context['request_identity']!=result['request_identity'] or context['world_identity']!=result['world_identity'] or
                context['action_identity']!=candidate['candidate_id']):
            raise ContractError('Saved prediction flow context mismatch')
        if [r['slot_key']['robot_id'] for r in sources]!=key['robots']:raise ContractError('Wrong source-slot team order')
        for source,robot in zip(sources,key['robots']):
            current=slots[(j,robot)];observed=tick==start and current['state']!='UNQUERIED'
            if source['source']!=('OBSERVED' if observed else 'MODEL'):raise ContractError('Mixed-source tag mismatch')
            if source['slot_key']!=dict(target_id=j,robot_id=robot,tick=tick):raise ContractError('Mixed-source identity mismatch')
            if observed:
                if source['packet']!=current['packet'] or source['outcome']!=current['state'] or source['observed_slot_digest']!=current['slot_digest']:
                    raise ContractError('Observed current result was overwritten')
            else:
                profile=profiles['U'+str(robot)]
                if source['observed_slot_digest'] is not None:raise ContractError('MODEL source claims observed authority')
                if profile['health']=='missing':
                    if source['outcome']!='MISSING' or source['packet'] is not None:raise ContractError('Missing held health invented a packet')
                else:
                    p=frames[tick]['positions'][robot];packet=source['packet']
                    point=[target['position_now'][i]+target['velocity_now'][i]*(tick*.05-start*.05) for i in (0,1)]
                    angle=(math.atan2(point[1]-p[1],point[0]-p[0])+math.pi)%(2*math.pi)-math.pi
                    close(packet['position'],p,label='nominal position');close(packet['bearing'],angle,label='nominal bearing')
                    if packet['sigma']!=profile['sigma']:raise ContractError('Nominal sigma changed')
        if frames[tick]['Q'][str(j)]!=row['result']['quality']['status']:raise ContractError('Quality did not enter saved clock endpoint')
    data=result['per_target'][str(j)];keep=data['kept_history']
    expected={(j,k) for k,f in frames.items() if str(j) in f['G'] and not(k==start and keep)}
    if seen!=expected:raise ContractError('Forecast solver coverage mismatch')
    terminal=data['status'] in ('completed','escaped','unfinished')
    finish=[e for e in result['events'] if e.get('target')==j and e['type']=='completion']
    release=[e for e in result['events'] if e.get('target')==j and e['type']=='release']
    if len(finish)!=int(data['status']=='completed') or len(release)!=int(terminal):raise ContractError('Forecast settlement/release not unique')
    if data['v']!=float(data['absolute_O']-data['baseline']):raise ContractError('Candidate increment arithmetic changed')
    if any(e.get('change_cost',e.get('extra_change_cost',0.))!=0. for e in release):raise ContractError('Automatic release charged again')
    return dict(counts=dict(counts))

def compare_candidate(primary,reference,key):
    j=str(key['target']);a,b=primary['per_target'][j],reference['per_target'][j]
    for field in ('status','termination_reason','completion_time','completion_tick','escape_time','clock_state','components',
                  'absolute_O','baseline','v','control_integral','occupied_robot_seconds'):
        close(a[field],b[field],label=field)
    if primary['candidate_identity']!=reference['candidate_identity'] or primary['request_identity']!=reference['request_identity']:
        raise ContractError('Reference scientific identity mismatch')
    af,bf=_rows_by_tick(primary),_rows_by_tick(reference)
    for tick in af:
        for i in key['robots']:
            close(af[tick]['positions'][i],bf[tick]['positions'][i],label='reference position')
            close(af[tick]['control'][i],bf[tick]['control'][i],label='reference control')
            if af[tick]['assignment'][i]!=bf[tick]['assignment'][i]:raise ContractError('Reference resource ownership differs')
        close(af[tick]['progress'][j],bf[tick]['progress'][j],label='reference progress')
        if af[tick]['G'].get(j)!=bf[tick]['G'].get(j) or af[tick]['Q'].get(j)!=bf[tick]['Q'].get(j):raise ContractError('Reference G/Q differs')
    # Fusion origin/packet values agree after operational labels are excluded.
    close(semantic(primary['sensing_results']),semantic(reference['sensing_results']),label='reference measurements')

def audit_decision(job,out):
    from . import public
    auth=_authority(job['binding_file'],job['binding_sha256']);request=public.validate_request(read_json(job['request_file']),auth)
    manifest=public.build_manifest(request,auth);cp=request['checkpoint'];specs=_specs(cp)
    if [s['key'] for s in manifest['candidates']]!=[{k:s[k] for k in ('target','robots','roles')} for s in specs]:raise ContractError('Canonical candidate catalogue differs')
    results={r['candidate_identity']:r for r in [read_json(p) for p in job['candidate_result_files']]}
    if set(results)!={s['candidate_id'] for s in manifest['candidates']}:raise ContractError('Main candidate coverage incomplete')
    refs={r['candidate_identity']:r for r in [read_json(p) for p in job.get('reference_result_files',[])]}
    if job['reference_required'] and set(refs)!=set(results):raise ContractError('Declared independent reference coverage incomplete')
    counts=Counter();base_by_target={};values=[]
    for c,s in zip(manifest['candidates'],specs):
        value=results[c['candidate_id']];counts.update(audit_prediction(request,value,c)['counts'])
        row=value['per_target'][str(s['target'])];values.append(row['v']);base_by_target.setdefault(s['target'],row['baseline'])
        if row['baseline'].hex()!=base_by_target[s['target']].hex():raise ContractError('Different unattended baselines')
        if c['candidate_id'] in refs:
            counts.update(audit_prediction(request,refs[c['candidate_id']],c)['counts']);compare_candidate(value,refs[c['candidate_id']],c['key'])
    base=0.
    for j in sorted(base_by_target):base+=base_by_target[j]
    choices=[[None]+[s for s in specs if s['target']==t['id']] for t in cp['targets']];plans=[]
    for option in product(*choices):
        chosen=[s for s in option if s];members=[i for s in chosen for i in s['robots']]
        if len(members)!=len(set(members)):continue
        actions=[dict(target=None,role='none') for _ in cp['positions']]
        for s in chosen:
            for i,r in zip(s['robots'],s['roles']):actions[i]=dict(target=s['target'],role=r)
        n=sum(a!=b for a,b in zip(actions,cp['assignment']))
        val=Fraction.from_float(base)+sum((Fraction.from_float(values[s['index']]) for s in chosen),Fraction())-Fraction.from_float(cp['config']['change_cost'])*n
        plans.append((val,actions))
    selection=read_json(job['selection_file']);best=max(p[0] for p in plans)
    from types import SimpleNamespace
    from pursuit_v2.types import Assignment
    from research.quality_allocation.certified_solver import solve,SCALE
    obs=SimpleNamespace(config=SimpleNamespace(change_cost=cp['config']['change_cost']),assignment=tuple(Assignment(**a) for a in cp['assignment']))
    chosen,units=solve(obs,[SimpleNamespace(**s) for s in specs],values)
    if list(chosen)!=selection['selected_indices'] or Fraction.from_float(base)+Fraction(units,SCALE)!=best:
        raise ContractError('Saved selection differs from the fixed canonical DP tie rule')
    if Fraction(selection['exact_table_value'])!=best:raise ContractError('Saved decision is not exact finite-table optimum')
    if not any(v==best and a==selection['actions'] for v,a in plans):raise ContractError('Saved optimal value does not match selected actions')
    if selection['legal_plan_count']!=len(plans):raise ContractError('Legal combination count mismatch')
    result=dict(passed=True,tick=cp['tick'],candidate_count=len(specs),reference_count=len(refs),
        exact_optimum=str(best),selected_indices=selection['selected_indices'],legal_plan_count=len(plans),measurement_counts=dict(counts))
    save_json(Path(out)/'decision_audit.json',result);return result

def audit_episode(job,out):
    from .episode_audit import audit_episode as invoke
    return invoke(job,out)

def audit_pair(job,out):
    a,b=[read_json(p) for p in job['episode_index_files']];checks=[]
    for tick in (0,20):
        da=next(d for d in a['decisions'] if d['tick']==tick);db=next(d for d in b['decisions'] if d['tick']==tick)
        ra,rb=read_json(da['artifacts']['evaluation_request']),read_json(db['artifacts']['evaluation_request'])
        if ra!=rb:raise ContractError('Private future changed a pre-divergence public request')
        sa,sb=read_json(da['selection_file']),read_json(db['selection_file'])
        for key in ('table','selected_indices','actions','exact_table_value','request_identity','world_identity'):
            if sa[key]!=sb[key]:raise ContractError('Private future changed table/selection before visible divergence')
        ca={r['candidate_identity']:r for r in [read_json(p) for p in da['candidate_result_files']]}
        cb={r['candidate_identity']:r for r in [read_json(p) for p in db['candidate_result_files']]}
        if semantic(ca)!=semantic(cb):raise ContractError('Paired future changed pre-divergence scientific candidate results')
        checks.append(dict(tick=tick,request_equal=True,table_equal=True,choice_equal=True))
    result=dict(passed=True,predivergence=checks,first_possible_motion_divergence_tick=21,
        later_choice_difference_required=False)
    save_json(Path(out)/'paired_audit.json',result);return result
