"""Read-only supplementary checks; no estimator, policy or physical STEP calls."""
from copy import deepcopy
import math
import numpy as np
from pursuit_v2.config import Config
from pursuit_v2.observation_geometry import offset
from .belief import trajectory
from .stfbs_d1a_state import ModelBeliefConsumer
from .stfbs_d1a_replay import digest

def verify(result,view,seed,*,audit_context=None):
    if audit_context is None:raise ValueError('External trusted audit context required')
    cfg=Config(**view['config']);boundaries={b['tick']:b for b in result['boundaries']}
    decisions={d['view']['tick']:d['view'] for d in result['decisions']}
    frozen=view['beliefs'];actions=deepcopy(view['assignment']);checked=0
    terminals={e['target']:e for e in result['events'] if e['kind'] in ('completed','escaped','unfinished')}
    for frame in result['frames']:
        n=frame['tick'];lo=(n-1)*.05
        if n-1 in boundaries:actions=boundaries[n-1]['after']
        if n-1 in decisions:frozen={int(k):v for k,v in decisions[n-1]['beliefs'].items()}
        for i,a in enumerate(actions):
            u=np.zeros(2);dt=0.
            if a['target'] is not None:
                j=a['target'];event=terminals[j]
                if event['time']>=lo and not (event['time']==lo and event['tick']<n):
                    p,v=trajectory(frozen[j],n-1)
                    force=np.asarray(v)+cfg.travel_gain*(np.asarray(p)+offset(a['role'],cfg)-np.asarray(frame['before'][i]))
                    u=force*min(1.,cfg.max_speed/max(float(np.linalg.norm(force)),1e-15))
                    motion=result['world']['motion'][str(j)]
                    x=motion['position'][0]+motion['velocity'][0]*(lo-3.)
                    escape=lo if x>=cfg.side else lo+(cfg.side-x)/motion['velocity'][0] if motion['velocity'][0]>0 else math.inf
                    dt=max(0.,min(n*.05,escape)-lo)
            # Different ndarray reduction shapes are bounded locally, not by a global tolerance.
            error=np.max(np.abs(u-np.asarray(frame['control'][i])))
            bound=16*math.ulp(max(1.,float(np.max(np.abs(u)))))
            if error>bound or dt!=frame['elapsed'][i]:raise ValueError('Independent control/stop-time mismatch')
            checked+=1
    history_checks=[]
    for tick,v in sorted(decisions.items()):
        previous=result['frames'][tick-61]
        if v['positions']!=previous['positions'] or v['assignment']!=previous['assignment']:raise ValueError('Decision state discontinuity')
        active=sorted(int(j) for j,s in previous['status'].items() if s=='active')
        if sorted(t['id'] for t in v['targets'])!=active:raise ValueError('Wrong visible tasks')
        if v['kind']!='A2_POLICY_INPUT' or v['end_tick']!=120 or v['tick']!=tick:raise ValueError('Wrong decision interface')
        from .stfbs_d1a_history_audit import audit_histories
        audit_histories({h['target_id']:h for h in v['histories']},v['assignment'],{j:'active' for j in active},tick,context=audit_context)
        for h in v['histories']:
            x=deepcopy(h);saved=x.pop('history_digest')
            if saved!=digest(x) or h['contract_id']!='D1A_MODEL_TASK_HISTORY_V1':raise ValueError('MODEL history digest mismatch')
            s=next((s for s in h['segments'] if s['segment_id']==h['active_segment_id']),None)
            team=[dict(robot_id=i,role=a['role']) for i,a in enumerate(v['assignment']) if a['target']==h['target_id']]
            if (s['team'] if s else [])!=team:raise ValueError('MODEL team mismatch')
            if s and s['latest_endpoint']['tick']!=tick:raise ValueError('Stale endpoint')
        c=ModelBeliefConsumer(seed)
        for f in result['feedback']:
            ft=f['frame']['tick'];stream=f['frame']['stream_id']
            if ft>tick or ft==tick and stream.endswith(f'first{tick}'):continue
            c.enqueue(dict(source='MODEL',provenance='SIMULATED',observation_origin='MODEL',target_id=f['frame']['target_id'],measurement_tick=ft,available_tick=ft,estimate=deepcopy(f['result']['estimate_result'])))
        frozen_check=c.freeze(tick)
        if frozen_check!={int(k):b for k,b in v['beliefs'].items()}:raise ValueError('Decision belief replay mismatch')
        history_checks.append(dict(tick=tick,positions=True,assignment=True,active_tasks=True,history_digest=True,belief_replay=True))
    first_ticks={}
    for f in result['feedback']:
        stream=f['frame']['stream_id']
        if not stream.startswith(result['branch']+':'):raise ValueError('Cross-branch fusion stream')
        first_ticks.setdefault(f['frame']['target_id'],f['frame']['tick'])
    return dict(status='PASS',control_stop_checks=checked,decision_views=history_checks,first_model_endpoint_tick=first_ticks)
