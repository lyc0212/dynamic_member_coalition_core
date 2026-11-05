"""Generator and truth-side evaluator, never imported by the estimator."""
import hashlib
import json
import math
import numpy as np

TRUTH=np.array([8.2,11.4]);R=.6;SIGMA=.02;Q0=1/(R*SIGMA)**2
CONFIGS=[([0],[1],[1]),([0,0],[1,1.5],[1,1]),([0,180],[1,1],[1,1]),
    ([0,30],[1,1],[1,1]),([0,60],[1,1],[1,1]),([0,90],[1,1],[1,1]),
    ([0,120],[1,1],[1,1]),([0,120,240],[1,1,1],[1,1,1]),
    ([0,120],[1,1],[1,1]),([0,120,240],[1,1,1],[1,1,2]),
    ([0,90],[1,1],[1,2]),([0,90],[1,1.5],[1,1])]

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()

def public_input(case,noise,truth=TRUTH,radius=R):
    angles,dist,scales=CONFIGS[case-1]
    theta=np.deg2rad(angles);p=np.array(truth)+radius*np.array(dist)[:,None]*np.column_stack((np.cos(theta),np.sin(theta)))
    delta=np.array(truth)-p;sig=SIGMA*np.array(scales)
    z=(np.arctan2(delta[:,1],delta[:,0])+sig*np.asarray(noise)[:len(p)]+np.pi)%(2*np.pi)-np.pi
    return dict(sensor_ids=['U'+str(i) for i in range(len(p))],positions=p.tolist(),bearings=z.tolist(),sigmas=sig.tolist(),domain=[[0.,0.],[20.,20.]])

def evaluate(data,estimate,truth=TRUTH):
    # Independent scalar information contribution, no estimator function calls.
    a=b=c=0.
    for p,s in zip(data['positions'],data['sigmas']):
        dx,dy=float(truth[0])-p[0],float(truth[1])-p[1];v=1/(s*s*(dx*dx+dy*dy)**2)
        a+=v*dy*dy;b-=v*dx*dy;c+=v*dx*dx
    mat=np.array([[a,b],[b,c]]);e=np.linalg.eigvalsh(mat);tol=1e-12*max(1.,Q0,abs(e[1]))
    if e[0]<-tol:raise RuntimeError('FIM negative-eigenvalue contract')
    deg=bool(e[1]<=0 or max(0.,e[0])/e[1]<=1e-12)
    result=dict(FIM=mat.tolist(),eigenvalues=e.tolist(),structural_degenerate=deg,
        CRLB='undefined_singular' if deg else np.linalg.inv(mat).tolist())
    if estimate is not None:
        d=np.asarray(estimate)-truth;result.update(error_vector=d.tolist(),error=float(np.linalg.norm(d)),extreme=bool(np.linalg.norm(d)>3*R))
    return result

def freeze(folder):
    from pathlib import Path
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=False)
    noise=np.random.Generator(np.random.PCG64(20261023)).standard_normal((64,3))
    np.save(folder/'noise.npy',noise,allow_pickle=False)
    (folder/'noise_hex.json').write_text(json.dumps([[v.hex() for v in row] for row in noise]),encoding='utf-8')
    inputs=[dict(case=c,trial=k,input=public_input(c,noise[k])) for c in range(4,13) for k in range(64)]
    for row in inputs:row['input_sha256']=digest(row['input'])
    (folder/'inputs.json').write_text(json.dumps(inputs,indent=2),encoding='utf-8')
    (folder/'definition.json').write_text(json.dumps(dict(configs=CONFIGS,truth=TRUTH.tolist(),R=R,sigma=SIGMA,
        seed=20261023,generator='PCG64',numpy=np.__version__,noise_sha256=hashlib.sha256((folder/'noise.npy').read_bytes()).hexdigest()),indent=2),encoding='utf-8')
    return inputs
