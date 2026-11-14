"""Small source-pinned external registration, before constructing MODEL branches."""
from pathlib import Path
import json,hashlib
from .stfbs_d1a_replay import recover,digest
from .stfbs_d1a_history_audit import register_context

def verified_registration():
    directory=Path('runs/a2_switch_episode_001')
    seed_path=Path('reports/stfbs_lite_d1a_001/BELIEF_REPLAY_SEED.json')
    baseline_path=Path('reports/stfbs_lite_d1a_001/BASELINE.json')
    prior=json.loads(seed_path.read_bytes());pins=json.loads(baseline_path.read_bytes())['tracked_fingerprints'];rows=[]
    for name in ('R_D0.json','R_D20.json','R_D40.json','R_D60.json','R.json','PUBLIC_INPUT.json'):
        p=directory/name;actual=hashlib.sha256(p.read_bytes()).hexdigest()
        expected=prior['source_files'].get(str(p),pins.get(p.as_posix()))
        if expected is None or actual!=expected:raise ValueError('D60 historical source pin missing/mismatched: '+str(p))
        rows.append(dict(path=str(p),size=p.stat().st_size,file_id=p.stat().st_ino,actual_sha256=actual,preexisting_sha256=expected,match=True,anchor=str(seed_path) if str(p) in prior['source_files'] else str(baseline_path)))
    view,seed,replay=recover(directory)
    if digest(view)!=prior['public_D60_digest']:raise ValueError('Historical public digest mismatch')
    raw=json.loads((directory/'R_D60.json').read_bytes())['policy_input']
    if digest(raw)!=digest(view):raise ValueError('Raw D60/public view mismatch')
    histories={h['target_id']:h for h in view['histories']}
    from research.information_service_online.public import seal_history
    if any(seal_history(h)!=h for h in histories.values()):raise ValueError('Historical task digest mismatch')
    contexts={name:register_context(name,histories) for name in ('KEEP','SWITCH')}
    manifest=dict(source_files=rows,public_digest=digest(view),assignment_digest=digest(view['assignment']),targets=[t['id'] for t in view['targets']],histories={j:dict(saved_history_digest=h['history_digest'],object_digest=digest(h)) for j,h in histories.items()},seed_digest=digest(seed),registration_order='source checks -> recover -> register KEEP/SWITCH -> Branch construction',registry={k:dict(expected_branch_id=c.expected_branch_id,prefix_digest=hashlib.sha256(c.prefix_json.encode()).hexdigest()) for k,c in contexts.items()})
    return view,seed,contexts,manifest
