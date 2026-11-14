"""Strict offline comparison; unsupported identity paths fail closed.

No candidate evaluation, controller, estimator or selector is called.
"""
import argparse
import json
from .a0_evidence import EvidenceError,Reader,inventory,require
from .a0_identity import mode_chain,IdentityMap,pointer,exact_tree,digest
from .a0_mapping import namespace

def strict_pair(left,right,artifact,path='',context=None):
    """Inspect complete trees, never delete fields or round numeric values.

    Identity differences are deliberately not accepted until a fully admitted
    artifact supplies its scientific-object binding. Fixed policy membership
    alone cannot grant that binding.
    """
    if type(left) is not type(right):
        raise EvidenceError('FAIL',path,'type mismatch')
    if isinstance(left,dict):
        for key in sorted(set(left)^set(right)):
            raise EvidenceError('INVALID_EVIDENCE',path+'/'+pointer(key),'field coverage mismatch')
        for key in left:strict_pair(left[key],right[key],artifact,path+'/'+pointer(key),context)
    elif isinstance(left,list):
        require(len(left)==len(right),path,'array length mismatch','FAIL')
        for i,(a,b) in enumerate(zip(left,right)):strict_pair(a,b,artifact,path+'/'+str(i),context)
    elif (left.hex()!=right.hex() if type(left) is float else left!=right):
        if type(left) is str:
            try:kind=namespace(artifact,path)
            except EvidenceError:
                raise EvidenceError('INVALID_EVIDENCE',path,'UNSUPPORTED_STRING_DIFFERENCE: no fixed identity rule')
            require(context is not None,path,'ADMITTED_OBJECT_BINDING_REQUIRED: '+kind)
            context['pending'].append((kind,path,left,right))
            return
        raise EvidenceError('FAIL',path,'strict scientific value mismatch')

def get_pointer(value,path):
    for part in path.split('/')[1:]:
        part=part.replace('~1','/').replace('~0','~')
        value=value[int(part)] if isinstance(value,list) else value[part]
    return value

def admitted_pair(left,right,artifact,run,tick,anchors,mappings):
    """All nonmapped leaves must match before any identity is admitted."""
    exact_tree(anchors[0],anchors[1],'/scientific_object')
    context={'pending':[]};strict_pair(left,right,artifact,context=context)
    left_id=run+'_R';right_id=run+'_S_NEW'
    for kind,path,a,b in context['pending']:
        if kind=='frame_digest':
            parent=path.rsplit('/',1)[0]
            for tree,value in [(left,a),(right,b)]:
                require(value==digest(get_pointer(tree,parent+'/normalized_frame')),path,'frame digest source mismatch')
        else:
            require(kind in ('work','environment','stream','frame','packet'),path,'scientific identity must remain equal')
            if kind in ('work','environment'):
                require(a==left_id and b==right_id,path,'foreign runtime identity')
            else:
                require(a.startswith(left_id+':') and b==right_id+a[len(left_id):],path,'runtime identity recipe mismatch')
        mappings.register(kind,(run,str(tick),artifact),path,a,b,anchors[0],anchors[1],artifact=artifact)

def compare(root,*,source_type='RUN_ARTIFACTS'):
    """Ia gates precede every cross-mode read; no evidence is modified."""
    context={};mappings=IdentityMap()
    try:
        inv=inventory(root)
        admissions={m:mode_chain(root,m) for m in ('R','S_NEW')}
        r=Reader(root);source=r.read('INPUT.json');run=r.read('RUN_OPTIONS.json')['run_id']
        end=round(source['config']['stage_dt']*source['config']['max_stages']/.05)
        for i,tick in enumerate(range(0,end,20)):
            context=dict(decision_tick=tick,candidate_key=None,modes=['R','S_NEW'])
            context['artifact']='REQUEST'
            a=r.read(f'R/D{i}/REQUEST.json');b=r.read(f'S_NEW/D{i}/REQUEST.json')
            strict_pair(a,b,'request')
            ma=r.read(f'R/D{i}/MANIFEST.json');mb=r.read(f'S_NEW/D{i}/MANIFEST.json')
            context['artifact']='MANIFEST'
            strict_pair(ma,mb,'manifest')
            def indexed(m):
                return {(c['key']['target'],tuple(c['key']['robots']),tuple(c['key']['roles'])):c for c in m['candidates']}
            ca,cb=indexed(ma),indexed(mb)
            require(ca.keys()==cb.keys(),'/candidates','canonical key coverage mismatch','FAIL')
            for key in ca:
                context['artifact']='CANDIDATE'
                context['candidate_key']=[key[0],list(key[1]),list(key[2])]
                n=ca[key]['index'];j=cb[key]['index']
                left=r.read(f'R/D{i}/PREDICT/C{n}.json')
                right=r.read(f'S_NEW/D{i}/PREDICT/B{j//4}/C{j}.json')
                strict_pair(left,right,'candidate')
            context['candidate_key']=None
            for name,artifact in [('TABLE','manifest'),('SELECTION','selection'),('STEP','step'),('AFTER','checkpoint')]:
                context['artifact']=name
                left=r.read(f'R/D{i}/{name}.json');right=r.read(f'S_NEW/D{i}/{name}.json')
                anchors=(dict(tick=tick,checkpoint=a['checkpoint'],candidate_keys=list(ca)),dict(tick=tick,checkpoint=b['checkpoint'],candidate_keys=list(cb)))
                admitted_pair(left,right,artifact,run,tick,anchors,mappings)
        for name,artifact in [('FINAL_CHECKPOINT','checkpoint'),('EVENTS','step'),('FINAL_METRICS','step')]:
            context['artifact']=name
            strict_pair(r.read('R/'+name+'.json'),r.read('S_NEW/'+name+'.json'),artifact)
        return dict(status='PASS',source_type=source_type,scope='strict science comparison',multitarget_acceptance='NOT_EVALUATED',admissions=admissions,mappings=mappings.records)
    except EvidenceError as e:
        return dict(status=e.status,path=e.path,reason=e.reason,context=context,science_acceptance='NOT_PASSED')
    except (KeyError,TypeError,ValueError,IndexError,AssertionError) as e:
        return dict(status='INVALID_EVIDENCE',path='/',reason=str(e),context=context,science_acceptance='NOT_PASSED')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('run');args=p.parse_args()
    report=compare(args.run);print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
