"""A0-Ic offline integration: pair, exact plans, competition kept separate."""
import argparse,json
from .a0_compare import compare
from .a0_evidence import Reader,EvidenceError
from .a0_plans import verify_selection

def accept(root,*,source_type='RUN_ARTIFACTS'):
    pair=compare(root,source_type=source_type)
    report=dict(source_type=source_type,PAIR_CONSISTENCY=pair,PLAN_OPTIMALITY={'status':'NOT_EVALUATED'},COMPETITION={'status':'NOT_EVALUATED','real_multitarget_episode':'NOT_EVALUATED'})
    if pair['status']!='PASS':return report
    records=[];context={}
    try:
        r=Reader(root);source=r.read('INPUT.json')
        end=round(source['config']['stage_dt']*source['config']['max_stages']/.05)
        for mode in ('R','S_NEW'):
            for i,tick in enumerate(range(0,end,20)):
                context=dict(mode=mode,tick=tick);folder=f'{mode}/D{i}'
                req=r.read(folder+'/REQUEST.json');m=r.read(folder+'/MANIFEST.json');rows=[]
                for n,c in enumerate(m['candidates']):
                    label=folder+'/PREDICT/'+(f'C{n}' if mode=='R' else f'B{n//4}/C{n}')
                    rows.append(r.read(label+'.json')['per_target'][str(c['key']['target'])])
                result=verify_selection(req['checkpoint'],[c['key'] for c in m['candidates']],rows,r.read(folder+'/SELECTION.json'))
                records.append(dict(context,**result))
        report['PLAN_OPTIMALITY']=dict(status='PASS',decisions=records)
        dual=source['config']['robots']==3 and len(source['targets'])==2
        evidence='FIXTURE' if source_type=='FIXTURE' else ('REAL_MULTITARGET' if dual else 'HISTORICAL_SINGLE_TARGET')
        report['COMPETITION']=dict(status='EVALUATED',evidence_type=evidence,structural_witness=any(x['structural_competition'] for x in records),positive_margin_witness=any(x['competition']['activated'] for x in records),real_multitarget_episode='EVALUATED' if dual and source_type!='FIXTURE' else 'NOT_EVALUATED')
    except (EvidenceError,ValueError,KeyError,TypeError,StopIteration) as e:
        report['PLAN_OPTIMALITY']=dict(status='FAIL',context=context,reason=str(e))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');args=p.parse_args();r=accept(args.run)
    print(json.dumps(r,ensure_ascii=False,indent=2))
    return 0 if r['PAIR_CONSISTENCY']['status']=='PASS' and r['PLAN_OPTIMALITY']['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
