"""BLVF V0.1: public two-bearing forward-ray intersection. No world input."""
import math,sys
from research.information_service.public_quality import _validated_payload
from research.information_service.common import ContractError
from research.cooperative_sensing.estimator import values,independent_q,condition,EvaluationGuard,NumericContractViolation
METHOD='ANALYTIC_BEARING_INTERSECTION'
DET_TOL=64*sys.float_info.epsilon
BOUNDARY_TOL=64*sys.float_info.epsilon*20.
def cross(a,b):return a[0]*b[1]-a[1]*b[0]
def estimate(payload):
    out=dict(estimator_method=METHOD,analytic_solution_success=False,nonlinear_solver_starts=0,observation_origin='MODEL',provenance='SIMULATED',starts=[],has_accepted_estimate=False,estimate=None,optimizer_converged=False,numerical_ill_conditioned=False,ambiguity_detected=False,boundary_active=False,branch_guard_triggered=False,numeric_contract_violation=False,selected_start=None,Q=None,rejection_reason=None,compatibility_note='optimizer_converged means analytic success, not nonlinear optimization; starts empty; uniqueness is geometric, not nine-start ambiguity testing')
    try:data=_validated_payload(payload)
    except ContractError as exc:out['rejection_reason']='PUBLIC_INPUT_CONTRACT: '+str(exc);return out
    if len(data['sensor_ids'])!=2:out['rejection_reason']='UNSUPPORTED_SENSOR_COUNT';return out
    a,b=data['positions'];z1,z2=data['bearings'];d1=(math.cos(z1),math.sin(z1));d2=(math.cos(z2),math.sin(z2));delta=(b[0]-a[0],b[1]-a[1]);det=cross(d1,d2)
    out['direction_determinant']=det;out['determinant_machine_safety_threshold']=DET_TOL
    if abs(det)<=DET_TOL:out['rejection_reason']='PARALLEL_OR_MACHINE_DEGENERATE';return out
    l1=cross(delta,d2)/det;l2=cross(delta,d1)/det;out['forward_distances']=[l1,l2]
    if not all(math.isfinite(v) for v in (l1,l2)) or l1<=0 or l2<=0:out['rejection_reason']='NONFORWARD_OR_NONFINITE_INTERSECTION';return out
    p=[a[i]+l1*d1[i] for i in (0,1)]
    if not all(math.isfinite(x) for x in p):out['rejection_reason']='NONFINITE_POSITION';return out
    if not all(data['domain'][0][i]<=p[i]<=data['domain'][1][i] for i in (0,1)):out['rejection_reason']='OUTSIDE_DOMAIN_NO_CLIPPING';return out
    try:
        residual,jacobian=values(data,p);q=independent_q(data,p);info=condition(jacobian)
    except EvaluationGuard as exc:out['rejection_reason']='PUBLIC_RESIDUAL_OR_DISTANCE_GUARD';out['analytic_guard']=exc.detail;return out
    if not math.isfinite(q) or not all(math.isfinite(float(x)) for x in residual) or not all(math.isfinite(float(x)) for row in jacobian for x in row):raise NumericContractViolation('Nonfinite analytic residual/Jacobian')
    q_residual=math.fsum(float(x)*float(x) for x in residual)
    if abs(q-q_residual)>1e-10+1e-10*max(1.,abs(q),abs(q_residual)):raise NumericContractViolation('Independent analytic residual mismatch')
    boundary=any(abs(p[i]-bound[i])<=BOUNDARY_TOL for i in (0,1) for bound in data['domain'])
    out.update(analytic_solution_success=True,has_accepted_estimate=True,estimate=p,optimizer_converged=True,numerical_ill_conditioned=bool(info['ill']),boundary_active=boundary,singular_values=info['singular_values'],Q=q,standardized_residual=[float(x) for x in residual],numeric_condition_ratio=0. if info['singular_values'][0]==0 else info['singular_values'][-1]/info['singular_values'][0],boundary_machine_tolerance=BOUNDARY_TOL)
    return out
