"""Deterministic inputs, fixed before any algorithm scoring or resource precheck."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import numpy as np
from pursuit_v2.config import Config
from pursuit_v2.types import Target, Scenario, Assignment, Observation, IDLE
from pursuit_v2.environment import TimedEnvironment
from pursuit_v2.observation_geometry import required_roles, offset
from pursuit_v2.service import restore_state


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def payload(obs):
    return dict(config=obs.config.to_dict(), stage=obs.stage, time=obs.time,
                positions=obs.positions.tolist(), targets=[t.to_dict() for t in obs.targets],
                assignment=[a.to_dict() for a in obs.assignment], new_ids=obs.new_ids,
                ended_ids=obs.ended_ids, states=[(j, asdict(s)) for j, s in obs.service_states])


def restore(raw):
    cfg=Config(**raw['config'])
    return Observation(cfg, raw['stage'], np.array(raw['positions'], float),
        tuple(Target(**t) for t in raw['targets']), tuple(Assignment(**a) for a in raw['assignment']),
        tuple(raw['new_ids']), tuple(raw['ended_ids']), raw['time'],
        tuple((j, restore_state(cfg, s)) for j, s in raw['states']))


def freeze(out):
    out=Path(out); out.mkdir(parents=True, exist_ok=False)
    fixtures=[]; observations=[]
    for name, qs, expected in [('S1',(1,3),28), ('S2',(2,3),80), ('S3',(1,2,3),156)]:
        cfg=Config(robots=sum(qs), task_count=len(qs), side=20., max_stages=3,
                   capture_mode='stepwise_service', geometry_mode='angular_standoff_v1')
        targets=[]; positions=[]; actions=[]
        for j,q in enumerate(qs):
            xy=(5.+2.*j, 5.+2.*j)
            # No outcome-dependent tuning: H(q)=2+0.4q; common deadline=6, weight=2.
            targets.append(Target(j,0.,xy,(.4,0.),q,2.,6.,arc_rates=((1.,0.),),service_duration=2.+.4*q))
            for r in required_roles(q,cfg):
                positions.append((np.array(xy)+offset(r,cfg)+np.array((.05,0.))).tolist())
                actions.append(Assignment(j,r))
        scenario=Scenario(np.array(positions),tuple(targets))
        env=TimedEnvironment(cfg,scenario)
        fixtures.append(dict(scenario_id=name, config=cfg.to_dict(), scenario=scenario.to_dict(),
                             fixed_action=[a.to_dict() for a in actions], expected_candidates=expected,
                             observation_times=[0.,1.]))
        for k in range(2):
            obs=env.observe(); assert len(obs.targets)==len(qs)
            observations.append(dict(id=name+'/O'+str(k), scenario_id=name,
                                     expected_candidates=expected, observation=payload(obs)))
            if k==0: env.step(tuple(actions))
    save(out/'fixtures_v1.json',fixtures); save(out/'observations_v1.json',observations)
    save(out/'input_manifest.json',dict(version='STAGE2A4-PILOT-ABLATION-v1.2',
        rules='H=2+0.4q; xy=(5+2j,5+2j); v=(.4,0); weight=2; deadline=6; robot offset=(.05,0)',
        observations=[dict(id=r['id'],sha256=digest(r['observation'])) for r in observations],
        boundary_cases=['empty','negative_baseline','role_restart','tiny_H','escape_tie','full_refinement']))
    save(out/'input_sha256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in out.glob('*.json')})
    return observations
