"""Independent, truth-side acceptance of saved raw results; never a service driver."""
import json
import math
from pathlib import Path

from .common import digest, save_json
from .oracle import independent_information


def read(path):
    return json.loads(Path(path).read_text())


def close(actual, expected, atol=1e-12, rtol=0):
    if isinstance(expected,(list,tuple)):
        assert len(actual)==len(expected), (len(actual),len(expected))
        for a,b in zip(actual,expected):
            close(a,b,atol,rtol)
    else:
        assert math.isfinite(actual) and abs(actual-expected)<=atol+rtol*abs(expected), (actual,expected,atol,rtol)


def audit_accounting(attempt):
    results={}
    for case in read(attempt/'inputs/design.json')['non_success_accounting_checks']:
        saved=read(attempt/'logs'/case['case_id']/'env/result.json')
        state,snapshot,expected=saved['state'],saved['snapshot'],case['expected']
        metrics=state['metrics']
        assert state['tick']==120
        assert saved['actual_requests']==0 and metrics['measurement_requests']==0
        close(state['positions'],case['positions_initial'])
        assert all(a['target'] is None for a in state['last_assignment'])
        assert state['status'][0].upper()==expected['outcome']
        for key in ('completion','flow','late','effort','terminal'):
            close(metrics['reward_components'][key],expected[key])
        for key in ('occupied_robot_seconds','idle_robot_seconds','assignment_changes','change_cost',
                    'return_with_changes','return_without_changes'):
            close(metrics[key],expected[key])
        events=snapshot['events']
        for kind,key in (('completion','completion_events'),('escape','escape_events'),('release','robot_release_events')):
            assert sum(e['type']==kind for e in events)==expected[key], (case['case_id'],kind)
        if expected['escape_events']:
            event=next(e for e in events if e['type']=='escape')
            assert event['event_tick']==expected['escape_tick']
            close(event['time'],expected['escape_time'],atol=1e-10)
        terminal=[f for f in snapshot['frames'] if f['metrics']['reward_components']['terminal']!=0]
        assert len(terminal)==1 and terminal[0]['tick']==120
        results[case['case_id']]=dict(passed=True,metrics=metrics,events=events)
    return dict(passed=True,cases=results)


def audit_main(case, reference, saved, responses):
    cid=case['case_id']
    state,snapshot=saved['state'],saved['snapshot']
    metrics=state['metrics']
    assert state['tick']==120 and all(s=='completed' for s in state['status'])
    assert all(a['target'] is None for a in state['last_assignment'])
    close(state['completion_times'][0],reference['A_completion_time'],atol=1e-10)
    if cid=='E5':
        close(state['completion_times'][1],3.2,atol=1e-10)
        assert state['tasks'][1]['stream_start_tick']==60
        assert state['tasks'][1]['completion_window_ticks']==list(range(60,65))
        assert state['tasks'][0]['stream_id']!=state['tasks'][1]['stream_id']
    for key in ('control_integral','occupied_robot_seconds','assignment_changes','change_cost',
                'return_without_changes','return_with_changes'):
        close(metrics[key],reference[key])
    close(metrics['idle_robot_seconds'],18-reference['occupied_robot_seconds'])
    for key,value in reference['components'].items():
        close(metrics['reward_components'][key],value)
    q=case['targets'][0]['required_robots']
    frames=snapshot['frames']
    physical=[f for f in frames if f['phase']=='physical']
    assert [f['tick'] for f in physical]==list(range(1,121))
    a_end=reference['A_completion_tick']
    max_position_difference=0.
    for frame in frames:
        n=frame['tick']; ref=reference['records'][n]
        close(frame['positions'],ref['positions'])
        max_position_difference=max(max_position_difference,max(abs(a-b) for p,r in zip(frame['positions'],ref['positions']) for a,b in zip(p,r)))
        close(frame['progress'][0],ref['a_progress'])
        if cid=='E5':
            close(frame['progress'][1],min(.2,max(0,n-60)*.05))
        if n<=a_end and '0' in frame['G']:
            assert frame['G']['0']==ref['a_G'] and frame['Q']['0']==ref['a_Q']
        if frame['phase']=='physical':
            speed=.4+.2*.95**(n-1) if n<=a_end else (.4 if cid=='E5' and 60<n<=64 else 0.)
            control=[[speed,0.] for _ in range(q)]+[[0.,0.] for _ in range(3-q)]
            close(frame['control'],control)
            close(frame['positions_start'],reference['records'][n-1]['positions'])
            close(frame['effort_delta_by_robot'],[.05*speed*speed]*q+[0.]*(3-q))
        task = 0 if n<a_end else (1 if cid=='E5' and 60<=n<64 and not (n==60 and frame['phase']=='physical') else None)
        assert [a['target'] for a in frame['assignment']]==[task]*q+[None]*(3-q)
        if n==60 and cid=='E5' and frame['phase']=='decision':
            assert frame['progress'][1]==0 and frame['status'][1]=='active'
    completions=[e for e in snapshot['events'] if e['type']=='completion']
    releases=[e for e in snapshot['events'] if e['type']=='release']
    assert len(completions)==len(releases)==len(case['targets'])
    assert [e['event_tick'] for e in completions]==([a_end,64] if cid=='E5' else [a_end])
    assert all(e['virtual'] is False for e in releases)
    interruptions=[e for e in snapshot['events'] if e['type']=='interruption']
    if cid in ('E2','E3','E5'):
        assert len(interruptions)==1
        close(interruptions[0]['time'],.75,atol=1e-10)
        close(interruptions[0]['progress_before'],.4)
        assert state['tasks'][0]['completion_window_ticks']==list(range(25,47))
    else:
        assert interruptions==[]
        assert state['tasks'][0]['completion_window_ticks']==list(range(6,28))
    estimates=starts=unknown=0
    quality_rows=[]
    for row in responses:
        data=row['public_request']; frame=data['frame']; result=row['response']; quality=result['quality']
        identity=row['identity']; n=frame['tick']; j=frame['target_id']
        assert digest(data)==identity['payload_sha256']
        assert digest(result['payload'])==result['payload_sha256']==quality['payload_sha256']
        expected_q=reference['records'][n]['a_Q'] if j==0 else 'PASS'
        assert quality['status']==expected_q
        truth=[case['targets'][j]['position_at_birth'][0]+.4*(n*.05-case['targets'][j]['birth']),10.]
        actual_error=None
        if result['estimator_called']:
            estimates+=1
            assert result['estimate_result']['has_accepted_estimate']
            starts+=len(result['estimate_result']['starts'])
            assert len(result['estimate_result']['starts'])==9
            close(quality['estimate'],truth,atol=1e-6)
            actual_error=math.dist(quality['estimate'],truth)
            independent=independent_information(result['payload']['positions'],result['payload']['sigmas'],quality['estimate'])
            close(quality['J'],independent['J'],atol=1e-10,rtol=1e-10)
            close(quality['I'],independent['I'],atol=1e-9,rtol=1e-12)
            close(quality['radius_proxy'],independent['radius_proxy'],atol=1e-12,rtol=1e-12)
        else:
            unknown+=1
            assert cid=='E3' and 15<=n<25 and quality['status']=='UNKNOWN'
        quality_rows.append(dict(target=j,tick=n,time=n*.05,status=quality['status'],
            radius_proxy=quality['radius_proxy'],actual_error=actual_error,estimate=quality['estimate']))
    assert estimates==case['expected']['main_real_WLS_calls'] and starts==9*estimates
    assert saved['actual_requests']==len(responses)
    assert metrics['reported_estimator_calls']==estimates
    expected_frames=list(range(a_end+1))
    assert [r['identity']['global_tick'] for r in responses if r['identity']['target_id']==0]==expected_frames
    if cid=='E5':
        assert [r['identity']['global_tick'] for r in responses if r['identity']['target_id']==1]==list(range(60,65))
    return dict(passed=True,case_id=cid,metrics=metrics,A_completion=state['completion_times'][0],
                B_completion=state['completion_times'][1] if cid=='E5' else None,
                real_estimates=estimates,starts=starts,unknown_frames=unknown,
                quality_rows=quality_rows,max_position_difference=max_position_difference,
                releases=releases,interruptions=interruptions)


def audit_attempt(attempt,out):
    design=read(attempt/'inputs/design.json')
    references=read(attempt/'inputs/independent_reference.json')
    accounting=audit_accounting(attempt)
    cases={}
    controls={}
    for case in design['cases']:
        cid=case['case_id']; base=attempt/'logs'/cid/'env'
        cases[cid]=audit_main(case,references[cid],read(base/'result.json'),read(base/'sensing_responses.json'))
        sensed=attempt/'logs'/cid/'sense'
        counts=read(sensed/'counters.json')
        assert counts['estimator_calls']==counts['completed_estimates']==cases[cid]['real_estimates']
        assert counts['start_attempts']==cases[cid]['starts']
        records=sorted((sensed/'estimates').glob('*.json'))
        assert len(records)==cases[cid]['real_estimates']
        returned={r['identity']['sense_request_id']:r for r in read(base/'sensing_responses.json')}
        for path in records:
            record=read(path)
            assert record['status']=='returned'
            assert len(record['native_starts'])==len(record['result']['starts'])==9
            matching=returned[record['identity']['sense_request_id']]
            assert record['identity']==matching['identity']
            assert digest(record['result'])==digest(matching['response']['estimate_result'])
        if cid!='E5':
            old=read(attempt/'logs'/(cid+'_old_G')/'env/result.json')
            assert old['metrics']['completed_count']==1
            close(old['metrics']['outcomes'][0]['completion_time'],1.35,atol=1e-10)
            new=read(base/'result.json')['snapshot']['frames']
            new_positions={f['tick']:f['positions'] for f in new if f['phase']=='physical'}
            for step in old['steps']:
                for frame in step['frames']:
                    n=round(frame['time']/.05)
                    if 0<n<=27:
                        close(frame['positions'],new_positions[n])
            controls[cid]=dict(passed=True,completion_time=1.35,common_motion_prefix_ticks=27,
                               metrics=old['metrics'])
    total=sum(c['real_estimates'] for c in cases.values())
    starts=sum(c['starts'] for c in cases.values())
    assert total==192 and starts==1728
    result=dict(passed=True,scope='deterministic execution mechanism; not reliability or M3 evidence',
                cases=cases,accounting=accounting,old_G_controls=controls,
                main_real_estimates=total,main_starts=starts)
    save_json(out/'scientific_audit.json',result)
    return result
