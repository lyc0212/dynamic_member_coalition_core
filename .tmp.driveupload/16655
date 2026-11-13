"""Independent decimal-rational and frozen binary64 checks; never simulates."""
from fractions import Fraction
from statistics import mean
from pathlib import Path
import json

METHODS=("M0","M1","M2")
LAMBDAS=(0.,.1,.25,.5)

def read(path):
    return json.loads(Path(path).read_bytes())

def same_float(actual, expected, path):
    if type(actual) is not float or actual.hex()!=float(expected).hex():
        raise ValueError(f"Numeric mismatch at {path}: {actual!r} != {expected!r}")

def numeric_method(classes, truths):
    if len(classes)!=8 or len(truths)!=8 or any(len(t)!=4 for t in truths):
        raise ValueError("Eight equal four-world families required")
    if any(s not in ([False],[True],[False,True]) or any(type(x) is not bool for x in s) for s in classes):
        raise ValueError("Invalid class set")
    if any(type(y) is not bool for t in truths for y in t):
        raise ValueError("Invalid true class")
    exact_world=[];float_world=[];exact_family=[];float_family=[]
    for s,t in zip(classes,truths):
        ew=[{str(l):Fraction(int(y not in s))+Fraction(str(l))*int(len(s)==2) for l in LAMBDAS} for y in t]
        fw=[{str(l):int(y not in s)+l*int(len(s)==2) for l in LAMBDAS} for y in t]
        exact_world.append(ew);float_world.append(fw)
        exact_family.append({str(l):sum(v[str(l)] for v in ew)/4 for l in LAMBDAS})
        float_family.append({str(l):mean(v[str(l)] for v in fw) for l in LAMBDAS})
    return dict(exact_world=exact_world,float_world=float_world,exact_family=exact_family,
        float_family=float_family,exact_total={str(l):sum(f[str(l)] for f in exact_family)/8 for l in LAMBDAS},
        float_total={str(l):mean(f[str(l)] for f in float_family) for l in LAMBDAS})

def check_saved_totals(calculated, saved, path="loss"):
    if set(saved)!=set(map(str,LAMBDAS)):
        raise ValueError("Loss coefficients changed")
    for key,expected in calculated["float_total"].items():
        same_float(saved[key],expected,f"{path}/{key}")

def main_criteria(exact_differences, coverage_m1, coverage_m2):
    if len(exact_differences)!=8:raise ValueError('Eight family differences required')
    return [sum(exact_differences)/8>=Fraction(1,20),
            sum(v>0 for v in exact_differences)>=5,coverage_m2>=coverage_m1]

def inputs(method,p,y):
    return ([read(p[f"{s}_{method}"]["path"])["prediction"]["predicted_completion_status_set"] for s in range(8)],
        [[read(y[f"{s}_{w}"]["path"])["label"]["completed_by_H"] for w in range(4)] for s in range(8)])

def check_sensitivity(method,p,y,saved):
    check_saved_totals(numeric_method(*inputs(method,p,y)),saved["methods"][method]["loss"],f"methods/{method}/loss")

def encode(value):
    if isinstance(value,Fraction):return str(value)
    if isinstance(value,list):return [encode(v) for v in value]
    if isinstance(value,dict):return {k:encode(v) for k,v in value.items()}
    return value

def dual_audit(p,y,saved):
    tracks={m:numeric_method(*inputs(m,p,y)) for m in METHODS}
    checks=[]
    def check(actual,expected,path):
        same_float(actual,expected,path)
        checks.append(dict(path=path,recalculated=expected,saved=actual,binary64_hex=actual.hex(),match=True))
    for m,t in tracks.items():
        check_saved_totals(t,saved["methods"][m]["loss"],f"methods/{m}/loss")
        for s in range(8):
            for w in range(4):
                row=saved["worlds"][4*s+w]
                if (row["slot"],row["world"])!=(s,w):raise ValueError("Wrong saved world order")
                for key,val in t["float_world"][s][w].items():
                    check(row["methods"][m]["losses"][key],val,f"worlds/{s}/{w}/{m}/{key}")
            family=saved["families"][s]
            if family["slot"]!=s:raise ValueError("Wrong saved family order")
            for key,val in t["float_family"][s].items():
                check(family["losses"][m][key],val,f"families/{s}/{m}/{key}")
        for key,val in t["float_total"].items():check(saved["methods"][m]["loss"][key],val,f"methods/{m}/loss/{key}")
    exact_D={};float_D={}
    for key in map(str,LAMBDAS):
        exact_D[key]=[tracks['M1']['exact_family'][s][key]-tracks['M2']['exact_family'][s][key] for s in range(8)]
        float_D[key]=[tracks['M1']['float_family'][s][key]-tracks['M2']['float_family'][s][key] for s in range(8)]
        for s,val in enumerate(float_D[key]):check(saved['families'][s]['D'][key],val,f"families/{s}/D/{key}")
    d=sum(exact_D['0.25'])/8;fd=mean(float_D['0.25']);wins=sum(v>0 for v in exact_D['0.25'])
    coverage={m:sum(yv in s for s,t in zip(*inputs(m,p,y)) for yv in t) for m in METHODS}
    criteria=main_criteria(exact_D['0.25'],coverage['M1'],coverage['M2'])
    float_criteria=[fd>=.05,sum(v>0 for v in float_D['0.25'])>=5,coverage['M2']>=coverage['M1']]
    if criteria!=float_criteria:raise ValueError("Main criteria disagree across numeric tracks")
    check(saved['mean_D'],fd,'mean_D')
    if wins!=saved['improved_families'] or (all(criteria))!=(saved['result']=='PREDICTIVE_GAIN_OBSERVED'):
        raise ValueError("Main decision mismatch")
    return dict(tracks=encode(tracks),exact_D=encode(exact_D),binary64_D=float_D,
        exact_mean_D=str(d),criteria=criteria,coverage=coverage,improved_families=wins,checks=checks,
        result='PREDICTIVE_GAIN_OBSERVED' if all(criteria) else 'NO_DEMONSTRATED_GAIN',tolerance_used=False)

def secondary_audit(p,y,saved):
    """All ratio denominators, time rows and cost fields, independently from raw artifacts."""
    checks=[]
    def compare(actual,expected,path):
        if actual!=expected:raise ValueError(f"Secondary mismatch at {path}: {actual!r} != {expected!r}")
        checks.append(dict(path=path,recalculated=expected,saved=actual,match=True))
    def ratio(vals):
        return dict(numerator=sum(vals),denominator=len(vals),value=mean(vals) if vals else None)
    raw_truths=[[read(y[f'{s}_{w}']['path'])['label'] for w in range(4)] for s in range(8)]
    tables={}
    for m in METHODS:
        rows=[]
        for s in range(8):
            payload=read(p[f'{s}_{m}']['path']);pred=payload['prediction'];classes=pred['predicted_completion_status_set'];ticks=pred['predicted_completion_ticks']
            nominal=read(p[f'{s}_M0']['path'])['prediction']['predicted_completion_status_set']
            for w,label in enumerate(raw_truths[s]):
                truth=label['completed_by_H'];tick=label['completion_tick']
                r=dict(truth=truth,covered=truth in classes,classes=classes,
                    optimistic=nominal==[True] and not truth,pessimistic=nominal==[False] and truth,
                    correct=nominal==[True] and truth,empty_time=truth and not ticks,
                    discrete_hit=tick in ticks if truth else None,
                    envelope_hit=bool(ticks and ticks[0]<=tick<=ticks[-1]) if truth else None,
                    width=ticks[-1]-ticks[0] if ticks else None,
                    median_error=abs(ticks[(len(ticks)-1)//2]-tick) if truth and ticks else None,
                    nearest_error=min(abs(t-tick) for t in ticks) if truth and ticks else None)
                rows.append(r)
                savedrow=saved['worlds'][4*s+w]
                compare(savedrow['actual'],label,f'worlds/{s}/{w}/actual')
                for k in ('covered','classes','empty_time','discrete_hit','envelope_hit','width','median_error','nearest_error'):
                    compare(savedrow['methods'][m][k],r[k],f'worlds/{s}/{w}/{m}/{k}')
            select=payload['selection']
            implementation=dict(K=len(select['selected']),high_fidelity_calls=len(pred['results']),
                geometry_endpoints=select['geometry_endpoints'],screening_wls=select['screening_wls'],end_to_end=payload['end_to_end'])
            compare(saved['costs'][str(s)][m],dict(simulation=pred['cost'],implementation=implementation),f'costs/{s}/{m}')
        tables[m]=rows;summary=saved['methods'][m]
        compare(summary['coverage'],ratio([r['covered'] for r in rows]),f'methods/{m}/coverage')
        for truth in (False,True):
            compare(summary['class_coverage'][str(truth)],ratio([r['covered'] for r in rows if r['truth']==truth]),f'methods/{m}/class_coverage/{truth}')
        for classes in ([False],[True],[False,True]):
            compare(summary['sets'][str(classes)],ratio([r['classes']==classes for r in rows]),f'methods/{m}/sets/{classes}')
        for field,condition,category in (('optimistic_recovery','optimistic',False),('pessimistic_recovery','pessimistic',True),('false_alarm','correct',False)):
            compare(summary[field],ratio([category in r['classes'] for r in rows if r[condition]]),f'methods/{m}/{field}')
        for field in ('empty_time','discrete_hit','envelope_hit'):
            compare(summary[field],ratio([r[field] for r in rows if r['truth']]),f'methods/{m}/{field}')
        for field in ('median_error','nearest_error','width'):
            vals=[r[field] for r in rows if r[field] is not None]
            compare(summary['errors'][field],dict(n=len(vals),mean=mean(vals) if vals else None),f'methods/{m}/errors/{field}')
    common=[i for i in range(32) if all(tables[m][i]['median_error'] is not None for m in ('M1','M2'))]
    expected=dict(n=len(common),excluded=sum(l['completed_by_H'] for row in raw_truths for l in row)-len(common),
        means={m:{k:mean(tables[m][i][k] for i in common) if common else None for k in ('median_error','nearest_error')} for m in ('M1','M2')})
    compare(saved['time_common'],expected,'time_common')
    compare(saved['service_diagnostics'],[l.get('service_diagnostics') for row in raw_truths for l in row],'service_diagnostics')
    return checks

def model_wls_audit(folder):
    p=read(Path(folder)/'predictions/MANIFEST.json');by_method={m:0 for m in METHODS};rows=[]
    for s in range(8):
        for m in METHODS:
            payload=read(p[f'{s}_{m}']['path']);pred=payload['prediction'];selected=payload['selection'];k=1 if m=='M0' else 3
            if payload['method']!=m or len(pred['results'])!=k or len(selected['selected'])!=k:
                raise ValueError('MODEL hypothesis identity mismatch')
            calls=0
            for hypothesis,record in zip(selected['selected'],pred['results'],strict=True):
                n=record['cost']['wls']
                if type(n) is not int or not 0<=n<=41 or record['hypothesis']!=hypothesis['label']:
                    raise ValueError('MODEL per-hypothesis budget/identity')
                calls+=n
            if calls!=pred['cost']['wls'] or calls>41*k or selected['screening_wls']!=0:
                raise ValueError('MODEL aggregate mismatch')
            by_method[m]+=calls;rows.append(dict(slot=s,method=m,wls=calls,hypothesis_wls=[r['cost']['wls'] for r in pred['results']]))
    total=sum(by_method.values())
    if total>2296:raise ValueError('MODEL total budget')
    return dict(by_method=by_method,by_family={s:sum(r['wls'] for r in rows if r['slot']==s) for s in range(8)},total=total,rows=rows)
