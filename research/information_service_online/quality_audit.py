"""Independent saved-measurement checks; never calls an estimator or controller."""
from collections import Counter
import math
import numpy as np
from .common import ContractError,digest


def close(a,b,atol=1e-12,rtol=0.,label=''):
    if isinstance(b,dict):
        if set(a)!=set(b):raise AssertionError((label,'fields',set(a),set(b)))
        for k in b:close(a[k],b[k],atol,rtol,label+'/'+str(k))
    elif isinstance(b,(list,tuple)):
        if len(a)!=len(b):raise AssertionError((label,'length'))
        for i,(x,y) in enumerate(zip(a,b)):close(x,y,atol,rtol,label+'/'+str(i))
    elif b is None or isinstance(b,(str,bool)):
        if a!=b:raise AssertionError((label,a,b))
    elif not(math.isfinite(a) and math.isfinite(b) and abs(a-b)<=atol+rtol*abs(b)):
        raise AssertionError((label,a,b))


def audit_fusion(row):
    frame=row['frame'];result=row['result'];payload=result['payload'];quality=result['quality']
    if set(payload)!={'sensor_ids','positions','bearings','sigmas','domain'}:raise ContractError('Unexpected saved estimator input fields')
    if digest(payload)!=result['payload_sha256'] or quality['payload_sha256']!=result['payload_sha256']:
        raise ContractError('Saved public payload identity differs')
    for field in ('stream_id','target_id','tick','frame_id'):
        if result[field]!=frame[field]:raise ContractError('Saved fusion identity mismatch')
    allowed=row['allowed_sensor_ids'];records=sorted(frame['records'],key=lambda r:int(r['sensor_id'][1:]))
    if len({r['sensor_id'] for r in records})!=len(records) or any(r['sensor_id'] not in allowed for r in records):
        raise ContractError('Saved valid sensors are not a subset of the occupied team')
    reconstructed=dict(sensor_ids=[r['sensor_id'] for r in records],positions=[r['position'] for r in records],
        bearings=[r['bearing'] for r in records],sigmas=[r['sigma'] for r in records],domain=[[0.,0.],[20.,20.]])
    if reconstructed!=payload:raise ContractError('Saved frame differs from estimator payload')
    for r in records:
        if r['measurement_tick']!=frame['tick'] or r['available_tick']!=frame['tick'] or r['status']!='ok':
            raise ContractError('Unexpected timestamp/status in zero-delay saved frame')
    counts=Counter(requests=1);counts[quality['status']]+=1
    if len(records)<2:
        if not result['skipped'] or result['estimator_called'] or result['estimate_result'] is not None or quality['status']!='UNKNOWN':
            raise ContractError('Insufficient measurements did not skip WLS')
        counts['skipped']+=1;return dict(counts=counts)
    estimated=result['estimate_result']
    if result['skipped'] or not result['estimator_called'] or len(estimated['starts'])!=9 or estimated['numeric_contract_violation']:
        raise ContractError('Full nine-start numeric contract missing')
    counts['real_estimates']+=1;counts['starts']+=9
    counts['guarded_starts']+=sum(s.get('guard') is not None for s in estimated['starts'])
    for s in estimated['starts']:
        if s.get('Q') is not None and s.get('cost') is not None:
            close(s['Q'],2*s['cost'],1e-10,1e-12,'Q versus twice cost')
    if not estimated['has_accepted_estimate']:
        if quality['status']!='UNKNOWN' or quality['has_estimate']:raise ContractError('No accepted estimate cannot pass quality')
    if quality.get('J') is None:
        if quality['status']!='UNKNOWN':raise ContractError('No information diagnostic but quality passed')
        return dict(counts=counts)
    x,y=quality['estimate'];J=[]
    for p,sigma in zip(payload['positions'],payload['sigmas']):
        dx,dy=x-p[0],y-p[1];r2=dx*dx+dy*dy
        if r2<=1e-18:raise ContractError('Accepted diagnostic coincides with sensor')
        J.append([dy/(sigma*r2),-dx/(sigma*r2)])
    I=[[math.fsum(r[a]*r[b] for r in J) for b in (0,1)] for a in (0,1)]
    singular=np.linalg.svd(np.array(J),compute_uv=False).tolist();singular+=[0.]*(2-len(singular))
    close(quality['J'],J,1e-10,1e-10,'independent J');close(quality['I'],I,1e-9,1e-12,'independent I')
    radius=math.sqrt(-2*math.log(.05))/singular[-1] if singular[-1]>0 else None
    close(quality['radius_proxy'],radius,1e-12,1e-12,'independent radius')
    ill=singular[0]==0 or singular[-1]/singular[0]<1e-4
    unavailable=ill or estimated['numerical_ill_conditioned'] or estimated['ambiguity_detected'] or estimated['boundary_active']
    expected='UNKNOWN' if unavailable or radius is None else 'PASS' if radius<=.06 else 'FAIL'
    if quality['status']!=expected:raise ContractError('Saved quality differs from independent decision')
    return dict(counts=counts,radius=radius)
