"""A: full service rollout and O-accounting, separate from old capture reward."""
import numpy as np
from pursuit_v2.service import rollout_fixed_service


def stop_without_service(case, path):
    from .domain import require_legacy
    require_legacy(case)
    return min(case.until, path.escape_time(case.obs.config.side))


def unattended(case, path):
    from .domain import require_legacy
    require_legacy(case)
    cfg, start = case.obs.config, case.obs.time
    stop = stop_without_service(case, path)
    flow = -cfg.flow_weight*path.weight*max(0.,stop-max(start,path.birth))/(cfg.weight_reference*cfg.stage_dt)
    late = -cfg.late_weight*path.weight*max(0.,stop-max(start,path.birth,path.deadline))/(cfg.weight_reference*cfg.stage_dt)
    terminal = -cfg.unfinished_weight*path.weight/cfg.weight_reference if case.until >= cfg.end_time-1e-10 else 0.
    return float(flow+late+terminal)


def benefit(case, path, completion, effort):
    from .domain import require_legacy
    require_legacy(case)
    """Fixed binary64 operation order; monotone positive completion terms minus cost."""
    cfg, start = case.obs.config, case.obs.time
    bar = stop_without_service(case,path)
    success = completion is not None
    stop = completion if success else bar
    finish = path.weight/cfg.weight_reference if success else 0.
    flow = cfg.flow_weight*path.weight*max(0.,bar-stop)/(cfg.weight_reference*cfg.stage_dt)
    origin = max(start,path.birth,path.deadline)
    late = cfg.late_weight*path.weight*(max(0.,bar-origin)-max(0.,stop-origin))/(cfg.weight_reference*cfg.stage_dt)
    terminal = cfg.unfinished_weight*path.weight/cfg.weight_reference if success and case.until >= cfg.end_time-1e-10 else 0.
    control = cfg.control_weight*effort/cfg.effort_reference
    return float(((finish+flow)+late)+terminal-control)


def physical_baseline(case):
    from .domain import require_legacy
    require_legacy(case)
    return sum(sum(unattended(case,p) for p in world) for world in case.worlds)/len(case.worlds)


def evaluate(case, spec):
    from .domain import require_legacy
    require_legacy(case)
    states = dict(case.obs.service_states)
    rows = []
    for w in range(len(case.worlds)):
        path = case.path(w,spec.target)
        result = rollout_fixed_service(case.obs.config,path,
                    case.obs.positions[list(spec.robots)], tuple(zip(spec.robots,spec.roles)),
                    case.obs.time,case.until,states[spec.target])
        rows.append((result,benefit(case,path,result.completion_time,result.effort)))
    return rows


def mean_score(rows):
    return sum(score for _,score in rows)/len(rows)


def environment_value(case, selected, trace=False):
    from .domain import require_legacy
    require_legacy(case)
    """Run frozen actions in actual 2A-1 environments, including the empty baseline."""
    from pursuit_v2.environment import Environment,TimedEnvironment
    from pursuit_v2.types import Scenario,Assignment,IDLE
    values = []
    traces = []
    for world in case.worlds:
        cfg = case.obs.config
        cls = TimedEnvironment if cfg.motion_model=='continuous_turn' or cfg.turn_max_angle>0 else Environment
        env = cls(cfg,Scenario(case.obs.positions,world))
        if isinstance(env,TimedEnvironment):
            env._time=case.obs.time
        env.stage=case.obs.stage
        env.last_assignment=case.obs.assignment
        env._service_states=list(dict(case.obs.service_states)[j] for j in range(cfg.task_count))
        env.service_progress[:]=[s.progress for s in env._service_states]
        env.service_team=[s.team for s in env._service_states]
        actions=[IDLE]*cfg.robots
        for spec in selected:
            for i,r in zip(spec.robots,spec.roles): actions[i]=Assignment(spec.target,r)
        rows=[]
        while env.time < case.until-1e-10:
            live=tuple(a if a.target in env.active_ids else IDLE for a in actions)
            result=env.step(live,trace=trace)
            rows.append(result.info)
        values.append(env.total_reward-env.total_change_cost)
        traces.append(rows)
    return sum(values)/len(values),traces
