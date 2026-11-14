from __future__ import annotations

from pursuit_v2.service import reject_service

from dataclasses import dataclass
from itertools import combinations
import hashlib
import json

from pursuit_v2.types import Assignment, IDLE


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class Spec:
    index: int
    target: int
    robots: tuple[int, ...]
    roles: tuple[str, ...]

    @property
    def mask(self):
        return sum(1 << k for k in self.robots)

    @property
    def key(self):
        return self.target, self.robots, self.roles


def enumerate_specs(obs):
    reject_service(obs.config)
    specs = []
    for target in obs.targets:
        rolesets = (("center",),) if target.required_robots == 1 else (
            ("upper", "lower"), ("lower", "upper"))
        for group in combinations(range(obs.config.robots), target.required_robots):
            for roles in rolesets:
                specs.append(Spec(len(specs), target.id, tuple(group), roles))
    return specs


def actions_from(specs, selected, robots):
    actions = [IDLE] * robots
    targets, used = set(), set()
    for index in selected:
        spec = specs[index]
        if spec.target in targets or used.intersection(spec.robots):
            raise ValueError('Non-feasible joint allocation')
        targets.add(spec.target)
        used.update(spec.robots)
        for k, role in zip(spec.robots, spec.roles):
            actions[k] = Assignment(spec.target, role)
    return tuple(actions)

