"""Versioned, hand-specified fixtures. No seed search or result-driven tuning."""
from dataclasses import dataclass, asdict, replace
from itertools import combinations, permutations
import hashlib
import json
import numpy as np

from pursuit_v2.config import Config
from pursuit_v2.types import Target, Observation, Assignment, IDLE
from pursuit_v2.service import ServiceState


@dataclass(frozen=True)
class Spec:
    index: int
    target: int
    robots: tuple
    roles: tuple

    @property
    def mask(self):
        return sum(1 << i for i in self.robots)

    @property
    def key(self):
        return self.target, self.robots, self.roles


@dataclass(frozen=True)
class Case:
    name: str
    obs: Observation
    until: float
    worlds: tuple  # each world is a tuple of predicted Target paths
    expectation: str = 'audit'

    def path(self, world, target):
        return next(t for t in self.worlds[world] if t.id == target)

    def payload(self):
        return dict(name=self.name, config=self.obs.config.to_dict(), start=self.obs.time,
                    until=self.until, positions=self.obs.positions.tolist(),
                    public_targets=[t.to_dict() for t in self.obs.targets],
                    assignment=[a.to_dict() for a in self.obs.assignment],
                    service_states=[(j, asdict(s)) for j, s in self.obs.service_states],
                    worlds=[[t.to_dict() for t in world] for world in self.worlds],
                    expectation=self.expectation)

    @property
    def identity(self):
        return hashlib.sha256(json.dumps(self.payload(), sort_keys=True, allow_nan=False).encode()).hexdigest()


def candidates(case):
    from .domain import require_legacy
    require_legacy(case)
    assert all(not t.arc_rates and not t.turns for t in case.obs.targets), 'Private future in public input'
    specs = []
    for target in case.obs.targets:
        roles = ('center',) if target.required_robots == 1 else ('upper', 'lower')
        for robots in combinations(range(case.obs.config.robots), target.required_robots):
            for assignment in permutations(roles):
                specs.append(Spec(len(specs), target.id, robots, assignment))
    return specs


def make_case(name, robots, task_rows, positions, start=0., until=3.,
              states=(), old=None, rates=(0.,), expectation='audit', speed_max=.8):
    cfg = Config(robots=robots, task_count=len(task_rows), side=20., max_stages=2,
                 capture_mode='stepwise_service', target_speed_max=speed_max)
    worlds = []
    for rate in rates:
        world = []
        for j, (xy, velocity, q, weight, duration) in enumerate(task_rows):
            world.append(Target(j, 0., xy, velocity, q, weight, 4.,
                                arc_rates=((start if start else 1., rate), (6., 0.)),
                                service_duration=duration))
        worlds.append(tuple(world))
    pos = np.array(positions, float)
    pos.setflags(write=False)
    public = tuple(t.observed(start) for t in worlds[0])
    obs = Observation(cfg, int(start//cfg.stage_dt), pos, public,
                      tuple(old) if old else (IDLE,)*robots, (), (), start,
                      tuple(states) if states else tuple((t.id, ServiceState()) for t in public))
    assert all(s.progress <= start-t.birth+1e-10 for t in public for j,s in obs.service_states if j==t.id)
    for world in worlds:
        for path, observed in zip(world, public):
            np.testing.assert_allclose(path.position(start), observed.position(start), atol=1e-12)
            np.testing.assert_allclose(path.velocity_at(start), observed.velocity_at(start), atol=1e-12)
    return Case(name, obs, until, tuple(worlds), expectation)


def frozen_cases():
    return (
        make_case('skip_v1', 2,
                  [((5.,5.),(.4,0.),1,4.,.15), ((12.,12.),(.4,0.),1,1.,10.)],
                  [[5.,5.],[5.1,5.05]], expectation='skip'),
        make_case('full_v1', 2, [((5.,5.),(.4,0.),1,2.,.15)],
                  [[6.,5.],[7.,5.]], expectation='full'),
        make_case('history_terminal_v1', 3,
                  [((5.,5.),(.4,0.),1,3.,2.), ((7.,7.),(.4,0.),2,2.,.3)],
                  [[6.2,5.],[8.2,7.6],[9.,9.]], start=3., until=6., rates=(0.,.05),
                  states=((0,ServiceState(1.5,0,((0,'center'),))),
                          (1,ServiceState(0.,0,((1,'upper'),(2,'lower'))))),
                  old=(Assignment(0,'center'),Assignment(1,'upper'),Assignment(1,'lower'))),
        make_case('escape_edges_v1', 3,
                  [((19.927,5.),(1.,0.),1,1.,.15),
                   ((19.85,5.),(1.,0.),1,1.,.15),
                   ((19.7,5.),(1.,0.),1,1.,.12)],
                  [[19.927,5.],[19.85,5.],[19.7,5.]], rates=(0.,.01,-.01,.02), speed_max=1.),
        make_case('pair_shared_v1', 4,
                  [((5.,5.),(.4,0.),2,3.,.4), ((8.,8.),(.4,0.),1,2.,.2)],
                  [[6.2,5.6],[6.2,4.4],[6.2,3.9],[9.2,8.]], start=3., until=6., rates=(0.,.03),
                  states=((0,ServiceState(.1,0,((0,'upper'),(1,'lower')))),(1,ServiceState())),
                  old=(Assignment(0,'upper'),Assignment(0,'lower'),IDLE,Assignment(1,'center'))),
    )


def clock_boundary_cases():
    base=frozen_cases()[1]
    result=[]
    for duration in (5e-11,.10000000005,.1000000002,.12):
        worlds=tuple(tuple(replace(t,service_duration=duration) for t in world) for world in base.worlds)
        obs=replace(base.obs,targets=tuple(t.observed(base.obs.time) for t in worlds[0]))
        result.append(replace(base,name=f'boundary_H_{duration}',worlds=worlds,obs=obs,expectation='boundary'))
    return tuple(result)
