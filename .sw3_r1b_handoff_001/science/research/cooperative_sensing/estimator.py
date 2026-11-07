"""Public-input-only nine-start WLS. Evaluation truth is deliberately absent."""
import itertools
import numpy as np
from scipy.optimize import least_squares

class NumericContractViolation(RuntimeError):
    pass

class EvaluationGuard(RuntimeError):
    def __init__(self,reason,x=None,sensor_id=None):
        super().__init__(reason)
        self.detail=dict(reason=reason,x=None if x is None else np.asarray(x).tolist(),sensor_id=sensor_id)

def wrap(x):
    return (np.asarray(x)+np.pi)%(2*np.pi)-np.pi

def values(data,x):
    d=np.asarray(x)-np.asarray(data['positions']); r2=np.sum(d*d,axis=1)
    if np.any(r2<=1e-18):
        raise EvaluationGuard('sensor_distance',x,data['sensor_ids'][int(np.flatnonzero(r2<=1e-18)[0])])
    raw=wrap(np.asarray(data['bearings'])-np.arctan2(d[:,1],d[:,0]))
    if np.any(np.pi-np.abs(raw)<=1e-8):
        raise EvaluationGuard('residual_branch',x,data['sensor_ids'][int(np.flatnonzero(np.pi-np.abs(raw)<=1e-8)[0])])
    s=np.asarray(data['sigmas'])
    return raw/s, np.column_stack((d[:,1],-d[:,0]))/(s*r2)[:,None]

def independent_q(data,x):
    terms=[]
    import math
    for p,z,s in zip(data['positions'],data['bearings'],data['sigmas']):
        dx,dy=float(x[0])-p[0],float(x[1])-p[1]
        if math.hypot(dx,dy)<=1e-9:raise EvaluationGuard('recompute_sensor_distance')
        a=(z-math.atan2(dy,dx)+math.pi)%(2*math.pi)-math.pi
        if math.pi-abs(a)<=1e-8:raise EvaluationGuard('recompute_branch')
        terms.append((a/s)**2)
    return math.fsum(terms)

def condition(j):
    s=np.linalg.svd(j,compute_uv=False).tolist()
    s+= [0.]*(2-len(s))
    return dict(singular_values=s,ill=bool(s[0]==0 or s[-1]/s[0]<1e-4))

def choose(rows):
    accepted=[r for r in rows if r['accepted']]
    if not accepted:return None,[]
    q=min(r['Q'] for r in accepted)
    near=[r for r in accepted if abs(r['Q']-q)<=1e-10+1e-10*max(1.,abs(q))]
    return min(near,key=lambda r:r['start_id']),near

def estimate(data):
    if set(data)!={'sensor_ids','positions','bearings','sigmas','domain'}:
        raise ValueError('Estimator public-input whitelist')
    m=len(data['sensor_ids'])
    if m<1 or len(set(data['sensor_ids']))!=m:raise ValueError('sensor identities')
    p=np.asarray(data['positions']);s=np.asarray(data['sigmas']);z=np.asarray(data['bearings'])
    if p.shape!=(m,2) or s.shape!=(m,) or z.shape!=(m,) or not np.all(s>0):raise ValueError('measurement shape')
    if not all(np.all(np.isfinite(v)) for v in (p,s,z)):raise ValueError('nonfinite input')
    rows=[]
    for k,start in enumerate(itertools.product((4.,10.,16.),repeat=2)):
        row=dict(start_id=k,start=list(start),accepted=False,guard=None,status=None,success=False,
            optimality=None,nfev=None,njev=None,active_mask=None,cost=None,Q=None,x=None)
        calls=dict(fun=0,jac=0)
        phase='fun'
        def fun(x):
            nonlocal phase
            phase='fun';calls['fun']+=1;return values(data,x)[0]
        def jac(x):
            nonlocal phase
            phase='jac';calls['jac']+=1;return values(data,x)[1]
        try:
            r=least_squares(fun,start,jac=jac,bounds=data['domain'],method='trf',tr_solver='exact',
                loss='linear',x_scale=1.,ftol=1e-10,xtol=1e-10,gtol=1e-10,max_nfev=300,verbose=0)
            row.update(status=int(r.status),success=bool(r.success),optimality=float(r.optimality),
                nfev=r.nfev,njev=r.njev,active_mask=r.active_mask.tolist(),cost=float(r.cost),x=r.x.tolist())
            phase='recompute';q=independent_q(data,r.x);row['Q']=q
            if np.isfinite(r.cost) and np.isfinite(q) and abs(q-2*r.cost)>1e-10+1e-10*max(1.,abs(q),abs(2*r.cost)):
                raise NumericContractViolation(repr(row))
            f,j=values(data,r.x)
            row['accepted']=bool(r.status>0 and np.all(np.isfinite(r.x)) and np.all(np.isfinite(f))
                and np.all(np.isfinite(j)) and np.isfinite(r.cost) and np.isfinite(q)
                and np.all(r.x>=np.asarray(data['domain'][0])-1e-10)
                and np.all(r.x<=np.asarray(data['domain'][1])+1e-10))
        except EvaluationGuard as e:
            row.update(guard=e.detail,phase=phase,reason='undefined_or_branch_guard')
        row['evaluation_calls']=calls
        rows.append(row)
    selected,near=choose(rows)
    out=dict(starts=rows,has_accepted_estimate=selected is not None,estimate=None,
        optimizer_converged=False,numerical_ill_conditioned=None,ambiguity_detected=None,
        boundary_active=None,branch_guard_triggered=any(r['guard'] and 'branch' in r['guard']['reason'] for r in rows),numeric_contract_violation=False)
    if selected:
        info=condition(values(data,selected['x'])[1])
        out.update(estimate=selected['x'],selected_start=selected['start_id'],Q=selected['Q'],
            optimizer_converged=True,numerical_ill_conditioned=info['ill'],singular_values=info['singular_values'],
            boundary_active=any(selected['active_mask']),
            ambiguity_detected=any(np.linalg.norm(np.array(a['x'])-b['x'])>.3 for a,b in itertools.combinations(near,2)))
    return out
