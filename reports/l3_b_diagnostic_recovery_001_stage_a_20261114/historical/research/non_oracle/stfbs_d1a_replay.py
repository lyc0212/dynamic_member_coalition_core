"""D1-A historical-only replay. Never samples, estimates, or executes STEP."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json

from .belief import Beliefs

def read(p):return json.loads(Path(p).read_bytes())
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def recover(directory):
    directory=Path(directory)
    announcements=read(directory/'PUBLIC_INPUT.json')['announcements']
    consumer=Beliefs(announcements,deferred=True)
    checks=[];sources={};generated=[]
    for tick in (0,20,40,60):
        path=directory/f'R_D{tick}.json'
        sources[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        record=read(path);view=record['policy_input']
        consumer.activate_visible(tick,{t['id'] for t in view['targets']})
        frozen=consumer.freeze(tick)
        expected={int(k):v for k,v in view['beliefs'].items()}
        view['beliefs']=deepcopy(expected)
        if frozen!=expected:raise ValueError(f'BLOCKED_STATE_RECONSTRUCTION: D{tick} beliefs')
        checks.append(dict(tick=tick,frozen_equal=True,consumed_count=len(consumer.consumed),pending_count=len(consumer.pending)))
        if tick==60:break
        for fusion in record['step']['fusion_records']:
            f=fusion['frame']
            row=dict(source='ACTUAL',target_id=f['target_id'],measurement_tick=f['tick'],available_tick=f['tick'],estimate=deepcopy(fusion['result']['estimate_result']))
            if f['tick']>60:raise ValueError('Future observation in historical seed')
            consumer.enqueue(row);generated.append(dict(row,generated_tick=f['tick']))
    final=read(directory/'R.json')
    consumed=[r for r in final['observations_consumed'] if r['consumed_tick']<=60]
    if consumed!=consumer.consumed:raise ValueError('BLOCKED_STATE_RECONSTRUCTION: consumed order')
    seed=dict(internal_states_at_D60=deepcopy(consumer.states),frozen_policy_beliefs_at_D60=frozen,
        accepted_position_history=deepcopy(consumer.history),pending_observations=deepcopy(consumer.pending),
        consumed_records=deepcopy(consumer.consumed),accepted_receipts=deepcopy(consumer.accepted_receipts),
        announcements=announcements,public_D60_digest=digest(view),source_files=sources,generated=generated)
    return view,seed,dict(status='PASS',cuts=checks,consumed_order_equal=True,seed_digest=digest(seed),
        method='Replay saved ACTUAL estimate results through production Beliefs; no new WLS or STEP')
