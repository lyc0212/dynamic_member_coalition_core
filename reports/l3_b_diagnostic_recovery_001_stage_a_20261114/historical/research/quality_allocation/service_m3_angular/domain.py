"""Strict request validation, separate from frozen physical semantics."""
import math
import numpy as np
from pursuit_v2 import observation_geometry as geometry
from pursuit_v2.service import GeometryServiceState, tick
from pursuit_v2.types import Assignment, IDLE


def validate_observation(obs):
    cfg=obs.config
    if cfg.capture_mode!='stepwise_service' or cfg.geometry_mode!='angular_standoff_v1':
        raise ValueError('M3_service_angular_v1 requires angular stepwise_service')
    tick(obs.time)
    if not 0<=obs.time<cfg.end_time:
        raise ValueError('A live observation is required')
    if obs.positions.shape!=(cfg.robots,2) or not np.isfinite(obs.positions).all():
        raise ValueError('Invalid independent robot positions')
    ids=[t.id for t in obs.targets]
    if len(set(ids))!=len(ids) or ids!=sorted(ids) or len(ids)>cfg.task_count:
        raise ValueError('Visible targets must have unique sorted IDs')
    states=dict(obs.service_states)
    if len(states)!=len(obs.service_states) or set(states)!=set(ids):
        raise ValueError('Exactly one service state per visible task is required')
    for t in obs.targets:
        if (t.turns or t.arc_rates or t.service_duration is None or t.birth>obs.time
                or t.id>=cfg.task_count):
            raise ValueError('Only public current targets with explicit service H are allowed')
        state=states[t.id]
        if (not isinstance(state,GeometryServiceState) or state.geometry_identity!=geometry.identity(cfg)
                or state.progress>=t.service_duration or state.progress>obs.time-t.birth+1e-10):
            raise ValueError('Invalid active service progress or geometry identity')
        if any(i>=cfg.robots for i,_ in state.team):
            raise ValueError('Service robot outside resource range')
        complete=geometry.validate_roles(t.required_robots,[r for _,r in state.team],cfg)
        if state.progress>0 and not complete:
            raise ValueError('Positive service history requires a complete legal team')
    if len(obs.assignment)!=cfg.robots or any(not isinstance(a,Assignment) for a in obs.assignment):
        raise ValueError('One public Assignment per robot required')
    targets={t.id:t for t in obs.targets}
    for a in obs.assignment:
        if a.target is None:
            if a!=IDLE: raise ValueError('Invalid idle assignment')
        elif a.target not in targets:
            raise ValueError('Assignment must be cleaned to active targets')
    for j,t in targets.items():
        geometry.validate_roles(t.required_robots,[a.role for a in obs.assignment if a.target==j],cfg)


def require_angular(case):
    # Case constructor validates the full frozen request; hot paths check domain.
    if (case.obs.config.capture_mode!='stepwise_service'
            or case.obs.config.geometry_mode!='angular_standoff_v1'):
        raise ValueError('Angular M3 request required')
