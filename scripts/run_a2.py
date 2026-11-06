"""独立 A2 入口。完整运行须另行授权。"""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.run_a1 import Sensing, exact_tree, IdentityMap, admitted_pair
from research.non_oracle.environment import StaggeredEnvironment
from research.non_oracle.policy import decide
from research.non_oracle.a2_analysis import decision_evidence

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('world','announcements','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();world=json.loads(args.world.read_text(encoding='utf-8'));ann=json.loads(args.announcements.read_text(encoding='utf-8'))
    args.output.mkdir(parents=True,exist_ok=False)
    def save(name,value):(args.output/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    save('WORLD_INPUT',world);save('PUBLIC_INPUT',ann);runs={}
    for mode in ('R','S_NEW'):
        env=StaggeredEnvironment(world,Sensing(),'A2_'+mode,ann['announcements']);records=[]
        while not env.done:
            view=env.prepare_decision();tick=view['tick'];choice=decide(view,mode);evidence=decision_evidence(view,choice,env.beliefs.accepted_receipts)
            result=env.step(choice['actions'],env.observe_public()['checkpoint_id'],tick,f'{mode}_D{tick}')
            record=dict(policy_input=view,choice=choice,evidence=evidence,step=result);save(f'{mode}_D{tick}',record)
            if result['status']!='COMMITTED':raise RuntimeError(f'A2 {mode} tick {tick} 未提交')
            records.append(record)
        runs[mode]=records;save(mode,dict(records=records,final=env.private_snapshot(),metrics=env.metrics(),observations_consumed=env.beliefs.consumed))
    exact_tree(len(runs['R']),len(runs['S_NEW']),'/decision_count');mapping=IdentityMap()
    for a,b in zip(runs['R'],runs['S_NEW']):
        tick=a['policy_input']['tick']
        for key in ('policy_input','choice','evidence'):exact_tree(a[key],b[key],f'/D{tick}/{key}')
        admitted_pair(a['step'],b['step'],'step','A2',tick,(a['policy_input'],b['policy_input']),mapping)
    save('PAIR_CHECK',dict(status='PASS',mappings=mapping.records))
    save('SUMMARY',dict(status='EXECUTION_COMPLETE_NOT_SCIENTIFIC_ACCEPTANCE',decision_count=len(runs['R'])))

if __name__=='__main__':main()
