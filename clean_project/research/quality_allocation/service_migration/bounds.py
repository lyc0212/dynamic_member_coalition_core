"""D: optimistic service clock + zero effort, not the old capture bound.

For finite operations and nonnegative O weights: all-valid service from the
eligible initial clock cannot finish later than an actual interrupted clock.
Completion benefits decrease with completion time; failed completion has only
nonpositive control cost. The SAME binary64 expression is used for optimistic
and evaluated scores, composed of monotone operations. A nextafter is outward
display/storage protection, not an empirical additive margin. This is not a
universal floating-point/geometry program proof.
"""
import math
import numpy as np
from pursuit_v2.service import ServiceState,advance_clock,canonical_team,tick,DT,TOL
from pursuit_v2.types import role_offset
from .reference import benefit


def world_bound(case,spec,w):
    from .domain import require_legacy
    require_legacy(case)
    path=case.path(w,spec.target); cfg=case.obs.config
    team=canonical_team(zip(spec.robots,spec.roles))
    state=dict(case.obs.service_states)[spec.target]
    offsets=np.array([role_offset(r,cfg) for r in spec.roles])
    pos=case.obs.positions[list(spec.robots)]
    valid=bool(np.all(np.linalg.norm(pos-path.position(case.obs.time)-offsets,axis=1)<=cfg.capture_radius+TOL))
    inherited=state.team==team and valid
    if not inherited:
        state=ServiceState(team=team)
    eligible=state.progress
    earliest=None
    for n in range(tick(case.obs.time)+1,tick(case.until)+1):
        state,done,_=advance_clock(state,path.service_duration,team,True,n*DT)
        if done:
            earliest=n*DT
            break
    escape=path.escape_time(cfg.side)
    possible=earliest is not None and escape>earliest+TOL
    # No completion: B=-nonnegative control cost <=0, not identically zero.
    optimistic=benefit(case,path,earliest,0.) if possible else 0.
    upper=math.nextafter(max(0.,optimistic),math.inf) if optimistic>0 else 0.
    if not math.isfinite(upper):
        raise ArithmeticError('Non-finite bound: outside finite gate contract')
    return dict(value=upper,eligible_progress=eligible,inherited=inherited,
                earliest=earliest,completion_branch_possible=possible,
                failure_branch_upper=0.,escape=escape if math.isfinite(escape) else None)


def all_bounds(case,specs):
    from .domain import require_legacy
    require_legacy(case)
    details={s.index:[world_bound(case,s,w) for w in range(len(case.worlds))] for s in specs}
    values=[]
    for s in specs:
        average=sum(row['value'] for row in details[s.index])/len(case.worlds)
        values.append(math.nextafter(average,math.inf) if average>0 else 0.)
    return values,details
