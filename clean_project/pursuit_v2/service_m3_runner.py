"""Explicit fixed-cadence online adapter; physical state changes only via Environment."""
from dataclasses import asdict
import hashlib
import json
import math
from fractions import Fraction
from pathlib import Path
from .environment import TimedEnvironment
from .service_m3 import make_service_m3_policy, POLICY_NAME
from research.quality_allocation.service_m3_angular.worlds import public_request
from research.quality_allocation.service_m3_angular.model import candidates


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()


def state_payload(env):
    times=lambda values:[float(x) if math.isfinite(x) else None for x in values]
    return dict(time=env.time,stage=env.stage,positions=env.positions.tolist(),status=list(env.status),
                states=[asdict(s) for s in env._service_states],progress=env.service_progress.tolist(),
                teams=list(env.service_team),completion=times(env.completion_times),escape=times(env.escape_times),
                assignment=[a.to_dict() for a in env.last_assignment],new_ids=env.new_ids,ended_ids=env.ended_ids,
                total_reward=env.total_reward,total_change_cost=env.total_change_cost,
                total_changes=env.total_changes,total_effort=env.total_effort,peak_speed=env.peak_speed,
                scenario_identity=digest(env.scenario.to_dict()),config=env.cfg.to_dict())


def validate_config(cfg):
    if (cfg.capture_mode!='stepwise_service' or cfg.geometry_mode!='angular_standoff_v1'
            or cfg.motion_model!='continuous_turn' or cfg.turn_interval!=1. or cfg.stage_dt!=3.
            or cfg.step_dt!=.05):
        raise ValueError('Online v1 requires angular service, continuous_turn, 1-second decisions and .05 physics')


def _run_loop(env, decide, *, driver_label):
    """Shared orchestration; controlled acceptance callers must label their driver."""
    decisions=[]; steps=[]
    while not env.done:
        before=state_payload(env)
        obs=env.observe()
        request=public_request(obs)
        public=request.observation_payload()
        if state_payload(env)!=before: raise RuntimeError('observe mutated environment')
        decision=decide(obs)
        if state_payload(env)!=before or public_request(obs).observation_payload()!=public:
            raise RuntimeError('decide mutated environment or public observation')
        actions=env._validate(decision.assignment)
        specs=candidates(request)
        if decision.log.get('policy')==POLICY_NAME:
            log=decision.log; cert=log['certificate']
            L,U=Fraction(cert['L']),Fraction(cert['U'])
            if (log['observation_identity']!=request.observation_identity or log['request_identity']!=request.identity
                    or log['window']!=[obs.time,request.until] or log['world_contract']!='public_cv_v1'
                    or log['candidate_count']!=len(specs) or U<L or Fraction(cert['gap'])!=U-L):
                raise RuntimeError('Decision certificate belongs to a different frozen request')
            if cert['accuracy_met'] and U-L>Fraction.from_float(float(cert['epsilon'])):
                raise RuntimeError('Decision falsely reports requested accuracy')
        # No reward, release, or clock update here: the single env.step owns them.
        entry=dict(observation_id=len(decisions),observation_time=obs.time,
                   observation_sha256=request.observation_identity,observation=public,
                   previous_assignment=[a.to_dict() for a in obs.assignment],
                   previous_service_progress=env.service_progress.tolist(),
                   candidate_manifest=[dict(index=s.index,target=s.target,robots=s.robots,roles=s.roles,
                                            resource_mask=s.mask,geometry_identity=s.geometry_identity) for s in specs],
                   returned_assignment=[a.to_dict() for a in actions],decision=decision.log,
                   state_before=before,decide_pure=True)
        result=env.step(actions,trace=True)
        entry['actual_assignment']=result.info['assignment']
        entry['state_after']=state_payload(env)
        if result.info['start']!=obs.time: raise RuntimeError('Action applied to the wrong interval')
        decisions.append(entry); steps.append(result.info)
    expected=[float(n) for n in range(round(env.cfg.end_time))]
    if [d['observation_time'] for d in decisions]!=expected:
        raise RuntimeError('Online decision cadence violated')
    return dict(version='STAGE2A3C-ONLINE-INTEGRATION-v1.0',driver=driver_label,
                config=env.cfg.to_dict(),scenario=env.scenario.to_dict(),decisions=decisions,steps=steps,
                metrics=env.metrics(),final_state=state_payload(env),
                certificate_scope='Each decision separately; no episode optimality certificate')


def run_service_m3_episode(cfg,scenario,*,policy_name,epsilon=0.,budget=None,output=None):
    if policy_name!=POLICY_NAME: raise ValueError('Select M3_service_angular_v1 explicitly')
    validate_config(cfg)
    if output is not None and Path(output).exists(): raise FileExistsError(output)
    env=TimedEnvironment(cfg,scenario)
    policy=make_service_m3_policy(policy_name,epsilon=epsilon,budget=budget)
    record=_run_loop(env,policy.decide,driver_label=POLICY_NAME)
    if output is not None:
        path=Path(output); path.mkdir(parents=True,exist_ok=False)
        (path/'episode.json').write_text(json.dumps(record,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    return record
