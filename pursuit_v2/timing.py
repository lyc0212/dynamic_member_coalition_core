"""Process CPU boundary for online observation and policy decision only."""
from __future__ import annotations

import time


ONLINE_CPU_BOUNDARY = {
    "version": 1,
    "clock": "time.process_time_ns",
    "entry": "immediately before environment.observe()",
    "exit": "immediately after Policy.decide(observation) returns",
    "included": ["public observation construction", "risk trigger", "prediction",
                 "candidate scoring", "allocation solver", "local repair and fallback",
                 "decision log construction inside Policy.decide"],
    "excluded": ["imports and environment/policy construction", "scenario generation",
                 "environment.step and physical control execution", "reward integration",
                 "post-decision forecast bookkeeping", "offline forecast audit",
                 "serialization, replay generation and file IO"],
    "secondary": "Policy.decide-only process CPU; observation reported separately",
    "old_experiment_equivalence": "not assumed; this is a separately defined boundary",
}


def measured_decision(environment, policy, clock=None):
    """Do exactly one observe/decide; logging these timings happens after exit."""
    clock = time.process_time_ns if clock is None else clock
    start = clock()
    observation = environment.observe()
    observed = clock()
    decision = policy.decide(observation)
    end = clock()
    if not start <= observed <= end:
        raise RuntimeError("Process CPU clock moved backwards")
    return observation, decision, {
        "online_cpu_seconds": (end - start) / 1e9,
        "online_observation_cpu_seconds": (observed - start) / 1e9,
        "online_policy_cpu_seconds": (end - observed) / 1e9,
    }
