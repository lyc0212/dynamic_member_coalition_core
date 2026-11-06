# 仅执行冻结场景的单次配对前缀。
import json,hashlib,traceback
from fractions import Fraction
from pathlib import Path
from scripts.run_a1 import Sensing
from scripts.gq_windows.a0_identity import exact_tree,IdentityMap
from scripts.gq_windows.a0_compare import admitted_pair
from scripts.gq_windows.a0_plans import plans
from research.non_oracle.environment import StaggeredEnvironment
from research.non_oracle.policy import decide
from research.non_oracle.a2_analysis import decision_evidence

p=Path('reports/a2_switch_preflight_001')
def save(name,value):
    with (p/(name+'.json')).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)
w=json.loads(Path('configs/a2_switch_two_target_v1.json').read_bytes())
a=json.loads(Path('configs/a2_switch_public_announcements_v1.json').read_bytes())
maps=IdentityMap()
runs={}
phase='prefix'
try:
    for mode in ('R','S_NEW'):
        env=StaggeredEnvironment(w,Sensing(),'A2_SWITCH_'+mode,a['announcements'])
        prefix=[]
        for tick in (0,20,40):
            view=env.prepare_decision()
            assert view['tick']==tick and [t['id'] for t in view['targets']]==[0] and set(view['beliefs'])=={0}
            choice=decide(view,mode)
            evidence=decision_evidence(view,choice,env.beliefs.accepted_receipts)
            step=env.step(choice['actions'],env.observe_public()['checkpoint_id'],tick,f'{mode}_D{tick}')
            d=dict(policy_input=view,choice=choice,evidence=evidence,step=step,observations_consumed=env.beliefs.consumed.copy())
            save(f'{mode}_D{tick}',d)
            assert step['status']=='COMMITTED' and env.tick==tick+20
            prefix.append(d)
            print(mode,'推进至',env.tick,flush=True)
        phase='ranking'
        view=env.prepare_decision()
        assert view['tick']==60 and view['first_policy_visible_ticks'][1]==60 and view['beliefs'][1]['status']=='PRIOR_ONLY'
        assert view['beliefs'][1]['last_observation_tick'] is None
        choice=decide(view,mode)
        evidence=decision_evidence(view,choice,env.beliefs.accepted_receipts)
        keys=[x['key'] for x in choice['rows']]
        table=plans(view,keys,choice['rows'])
        idle=next(x for x in table if not x['selected'])
        rank=sorted(table,key=lambda x:Fraction(x['exact_value']),reverse=True)
        for x in rank:
            x['net_margin']=str(Fraction(x['exact_value'])-Fraction(idle['exact_value']))
            x['change_cost']=str(Fraction.from_float(view['config']['change_cost'])*x['changes'])
        keep=next(x for x in table if x['actions']==view['assignment'])
        switch=next(x for x in rank if x['selected'] and keys[x['selected'][0]]['target']==1)
        progress=prefix[-1]['step']['frames'][-1]['progress'].get('0',0.)
        team=[i for i,x in enumerate(view['assignment']) if x['target']==0]
        active=0 in {t['id'] for t in view['targets']}
        conditions=active and len(team)==2 and progress>0 and len(table)==13 and len(keys)==12
        unique=len(rank)>1 and Fraction(rank[0]['exact_value'])>Fraction(rank[1]['exact_value'])
        switch_wins=unique and rank[0]['selected']==switch['selected']
        gap=str(Fraction(rank[0]['exact_value'])-Fraction(rank[1]['exact_value'])) if len(rank)>1 else None
        cut=dict(policy_input=view,choice=choice,evidence=evidence,progress=progress,old_team=team,old_active=active,conditions=conditions,strict_unique_switch=switch_wins,keep=keep,switch=switch,idle=idle,ranked_plans=rank,best_gap=gap)
        save(f'{mode}_D60',cut)
        runs[mode]=(env,prefix,cut)
        phase='prefix'
    phase='pair'
    for x,y in zip(runs['R'][1],runs['S_NEW'][1]):
        tick=x['policy_input']['tick']
        for key in ('policy_input','choice','evidence','observations_consumed'):
            exact_tree(x[key],y[key],f'/D{tick}/{key}')
        admitted_pair(x['step'],y['step'],'step','A2_SWITCH',tick,(x['policy_input'],y['policy_input']),maps)
    exact_tree(runs['R'][2],runs['S_NEW'][2],'/D60')
    cut=runs['R'][2]
    state='F1' if not cut['conditions'] else ('F2' if not cut['strict_unique_switch'] else 'PASS')
    if state=='PASS':
        phase='commit60'
        results={}
        for mode,(env,_,c) in runs.items():
            assert c['choice']['selected_indices']==c['switch']['selected']
            step=env.step(c['choice']['actions'],env.observe_public()['checkpoint_id'],60,f'{mode}_D60')
            save(f'{mode}_STEP60',step)
            assert step['status']=='COMMITTED' and env.tick==80
            transitions={t['target_id']:t for t in step['action_commit']['transitions']}
            assert transitions[0]['kind']=='WITHDRAW' and transitions[1]['kind']=='FIRST_ASSIGNMENT'
            event=next(e for e in step['events'] if e['kind']=='WITHDRAWN' and e['target_id']==0)
            assert event['progress_before']==c['progress'] and event['progress_after']==0
            assert step['frames'][0]['progress']=={'0':0.,'1':0.}
            changes=c['switch']['changes']
            assert step['action_commit']['assignment_change_count']==changes
            assert step['action_commit']['change_cost']==changes*w['config']['change_cost']
            pending=[x for x in env.beliefs.pending if x['target_id']==1]
            assert pending and pending[0]['measurement_tick']==60
            assert not any(x['target_id']==1 for x in env.beliefs.consumed)
            save(f'{mode}_D80_STATE',dict(progress=step['frames'][-1]['progress'],new_target_pending=pending,observations_consumed=env.beliefs.consumed))
            results[mode]=step
        admitted_pair(results['R'],results['S_NEW'],'step','A2_SWITCH',60,(cut['policy_input'],runs['S_NEW'][2]['policy_input']),maps)
    save('SUMMARY',dict(status=state,pair='PASS',PREFLIGHT_SWITCH_RANKING='PASS' if state=='PASS' else 'NOT_ESTABLISHED',last_tick=80 if state=='PASS' else 60,complete_episode=False,keep=cut['keep'],switch=cut['switch'],idle=cut['idle'],progress=cut['progress'],best_gap=cut['best_gap'],mappings=maps.records))
    print(state,cut['progress'],cut['keep']['net_margin'],cut['switch']['net_margin'],flush=True)
except Exception:
    save('FAILURE',dict(phase=phase,traceback=traceback.format_exc()))
    raise
finally:
    before=json.loads((p/'BEFORE.json').read_text(encoding='utf-8'))
    changed=[f for f,h in before['pins'].items() if hashlib.sha256(Path(f).read_bytes()).hexdigest()!=h]
    save('AFTER',dict(changed=changed))
    if changed:raise RuntimeError('冻结文件发生变化')
