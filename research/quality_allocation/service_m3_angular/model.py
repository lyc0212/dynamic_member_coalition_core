"""Immutable request and complete executable candidate identities."""
from dataclasses import dataclass, asdict, replace
from itertools import combinations, permutations
import hashlib
import json
import math
import numpy as np
from pursuit_v2.observation_geometry import identity, required_roles
from pursuit_v2.service import tick
from .domain import validate_observation


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()


@dataclass(frozen=True)
class Case:
    name: str
    obs: object
    until: float
    worlds: tuple
    expectation: str = 'audit'

    def __post_init__(self):
        validate_observation(self.obs)
        if tick(self.until)<=tick(self.obs.time) or self.until>self.obs.config.end_time+1e-10:
            raise ValueError('Invalid frozen prediction window')
        pos=np.array(self.obs.positions,copy=True); pos.setflags(write=False)
        object.__setattr__(self,'obs',replace(self.obs,positions=pos,targets=tuple(self.obs.targets),
                                           assignment=tuple(self.obs.assignment),service_states=tuple(self.obs.service_states)))
        object.__setattr__(self,'worlds',tuple(tuple(w) for w in self.worlds))
        if not self.worlds: raise ValueError('At least one explicit prediction world required')
        for world in self.worlds:
            if [t.id for t in world]!=[t.id for t in self.obs.targets]:
                raise ValueError('World must contain exactly the frozen visible tasks')
            for path,public in zip(world,self.obs.targets):
                if (path.required_robots,path.weight,path.birth,path.deadline,path.service_duration)!=(
                        public.required_robots,public.weight,public.birth,public.deadline,public.service_duration):
                    raise ValueError('World changed public task attributes')
                for time in [t for t,_,_ in path.turns]+[t for t,_ in path.arc_rates]: tick(time)
                if (not np.allclose(path.position(self.obs.time),public.position(self.obs.time),rtol=0,atol=1e-12)
                        or not np.allclose(path.velocity_at(self.obs.time),public.velocity_at(self.obs.time),rtol=0,atol=1e-12)):
                    raise ValueError('World does not start at the public observed state')

    def path(self,w,j):
        return next(t for t in self.worlds[w] if t.id==j)

    def observation_payload(self):
        o=self.obs
        return dict(config=o.config.to_dict(),time=o.time,stage=o.stage,positions=o.positions.tolist(),
                    targets=[t.to_dict() for t in o.targets],assignment=[a.to_dict() for a in o.assignment],
                    states=[(j,asdict(s)) for j,s in o.service_states])

    @property
    def observation_identity(self): return digest(self.observation_payload())

    def payload(self):
        return dict(name=self.name,observation=self.observation_payload(),until=self.until,
                    worlds=[[t.to_dict() for t in world] for world in self.worlds],
                    world_contract='explicit_equal_probability_v1',expectation=self.expectation)

    @property
    def identity(self): return digest(self.payload())


@dataclass(frozen=True)
class Spec:
    index: int
    target: int
    robots: tuple
    roles: tuple
    geometry_identity: tuple
    initial_service_state: object
    observation_identity: str
    request_identity: str

    @property
    def mask(self): return sum(1<<i for i in self.robots)

    @property
    def key(self): return self.target,self.robots,self.roles


def candidates(case):
    obs=case.obs; states=dict(obs.service_states)
    total=sum(math.perm(obs.config.robots,t.required_robots) for t in obs.targets)
    if total>1500: raise ValueError('v1 candidate limit exceeded; large-scale use is unvalidated')
    request,observed=case.identity,case.observation_identity
    result=[]
    for t in obs.targets:
        for robots in combinations(range(obs.config.robots),t.required_robots):
            for roles in permutations(required_roles(t.required_robots,obs.config)):
                result.append(Spec(len(result),t.id,robots,roles,identity(obs.config),states[t.id],observed,request))
    if len(result)!=total: raise ArithmeticError('Incomplete candidate generation')
    return tuple(result)


def check_specs(case,specs):
    if tuple(specs)!=candidates(case):
        raise ValueError('Complete canonical candidate set for this request required')
