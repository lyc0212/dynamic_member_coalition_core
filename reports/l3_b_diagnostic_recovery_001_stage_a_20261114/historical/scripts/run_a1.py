"""A1 episode entry; implementation only, execute after separate authorization."""
from pathlib import Path
import argparse,json,sys,copy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from research.non_oracle.environment import NonOracleEnvironment
from research.non_oracle.policy import decide
from research.information_service_bridge.public_stream import BridgeFrameProcessor
from scripts.gq_windows.a0_identity import exact_tree,IdentityMap
from scripts.gq_windows.a0_compare import admitted_pair

class Sensing:
    def __init__(self):self.streams={}
    def __call__(self,frame,allowed,start,context):
        stream=frame['stream_id']
        if stream not in self.streams:self.streams[stream]=BridgeFrameProcessor(allowed,start,stream,frame['target_id'])
        result=self.streams[stream].process(frame);result['flow_context']=copy.deepcopy(context)
        result['flow_registration']=dict(stream_id=stream,target_id=frame['target_id'],start_tick=start,allowed_sensor_ids=list(allowed),context=copy.deepcopy(context))
        return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--world',required=True,type=Path);p.add_argument('--announcements',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--method',choices=['R','S_NEW','both'],default='both');args=p.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    source=json.loads(args.world.read_text());ann=json.loads(args.announcements.read_text())
    args.output.mkdir(parents=True)
    def save(name,value):(args.output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    save('WORLD_INPUT.json',source);save('PUBLIC_INPUT.json',ann)
    results=[];reference=None;mapping=IdentityMap()
    for method in (['R','S_NEW'] if args.method=='both' else [args.method]):
        env=NonOracleEnvironment(copy.deepcopy(source),Sensing(),'A1_'+method,ann['announcements']);records=[]
        while not env.done:
            view=env.prepare_decision();choice=decide(view,method)
            cp=env.observe_public() # driver-only action transaction token
            step=env.step(choice['actions'],cp['checkpoint_id'],view['tick'],method+'_D'+str(view['tick']))
            records.append(dict(policy_input=view,choice=choice,step=step))
            save(method+'_D'+str(view['tick'])+'.json',records[-1])
        save(method+'.json',dict(kind='A1_NON_ORACLE_RESULT',records=records,observations_consumed=env.beliefs.consumed,final=env.private_snapshot(),metrics=env.metrics()))
        if reference is None:reference=records
        else:
            if len(reference)!=len(records):raise ValueError('A1 decision coverage differs')
            for a,b in zip(reference,records):
                tick=a['policy_input']['tick'];exact_tree(a['policy_input'],b['policy_input'],f'/D{tick}/policy_input');exact_tree(a['choice'],b['choice'],f'/D{tick}/choice')
                admitted_pair(a['step'],b['step'],'step','A1',tick,(a['policy_input'],b['policy_input']),mapping)
            save('PAIR_CHECK.json',dict(status='PASS',scope='A1 policy inputs, predictions, choices, actual STEP; not a completed scientific stage',mappings=mapping.records))
        results.append(dict(method=method,terminal=env.done,tick=env.tick))
    save('SUMMARY.json',dict(status='EXECUTION_COMPLETE_NOT_SCIENTIFIC_ACCEPTANCE',runs=results))
if __name__=='__main__':main()
