import pathlib,json,hashlib,math
from fractions import Fraction as F
from itertools import combinations
ROOT=pathlib.Path(__file__).resolve().parent;REPO=pathlib.Path(r'D:\1st\dynamic_member_coalition_core')
TASK='STFBS_LITE_ACTUAL_FULL_EPISODE_COUNTERFACTUAL_001';ACTIONS=['KEEP','SWITCH','MEMBER_CHANGE'];EPS=1e-8
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def frac(x):
 x=F.from_float(x) if isinstance(x,float) else F(x);return dict(numerator=x.numerator,denominator=x.denominator,display=float(x))
def output(n,x):
 data=dict(task_id=TASK,version='V1.0',execution_change_cost=.01,evaluation_mode='FIXED_TRAJECTORY_REVALUATION',horizon='D60_PRE_ASSIGNMENT_TO_D120_TERMINAL',numerical_tolerance=EPS,zero_change_cost_closed_loop_executed=False)
 data.update(x)
 with (ROOT/n).open('x',encoding='utf-8') as f:json.dump(data,f,indent=2,ensure_ascii=False,allow_nan=False)
def ranking(values,nominal=None):
 q={a:F.from_float(v) if isinstance(v,float) else F(v) for a,v in values.items()};best=max(q.values());reg={a:best-v for a,v in q.items()}
 return dict(values={a:float(v) for a,v in q.items()},exact_values={a:frac(v) for a,v in q.items()},ranking=sorted(q,key=lambda a:(-q[a],ACTIONS.index(a))),exact_optimal_actions=[a for a,v in q.items() if v==best],approximate_optimal_actions=[a for a,v in reg.items() if v<=F.from_float(EPS)],best_value=frac(best),regret={a:frac(v) for a,v in reg.items()},switch_regret=frac(reg['SWITCH']),actual_nominal_action=nominal,actual_nominal_regret=None if nominal not in reg else frac(reg[nominal]),nominal_suboptimality='INCONCLUSIVE' if nominal not in reg else 'CONFIRMED' if reg[nominal]>F.from_float(EPS) else 'NOT_DEMONSTRATED',pairwise_differences={a+'__'+b:frac(q[a]-q[b]) for a,b in combinations(q,2)})
def relation(a,b):
 sign=lambda v:1 if v>EPS else -1 if v<-EPS else 0
 return dict(strict_rank_reversals=[[x,y] for x,y in combinations(ACTIONS,2) if sign(a[x]-a[y])*sign(b[x]-b[y])==-1],order_changes=[[x,y] for x,y in combinations(ACTIONS,2) if sign(a[x]-a[y])!=sign(b[x]-b[y])],optimal_action_set_changed=ranking(a)['approximate_optimal_actions']!=ranking(b)['approximate_optimal_actions'])
def sensitivity(cells,nominal):
 B={a:F.from_float(cells[a]['no_change_value']) for a in ACTIONS};N={a:cells[a]['N_future'] for a in ACTIONS};pairs=[];points=set()
 for a,b in combinations(ACTIONS,2):
  d=B[a]-B[b];n=N[a]-N[b];p=d/n if n else None
  row=dict(actions=[a,b],intercept_difference=frac(d),count_difference=n,intersection=None if p is None else frac(p),parallel=n==0 and d!=0,coincident=n==0 and d==0,nonnegative=p is not None and p>=0,in_0_to_0_01=p is not None and 0<=p<=F.from_float(.01))
  if p is not None and p>=0:points.add(p)
  pairs.append(row)
 best=lambda p:[a for a in ACTIONS if B[a]-p*N[a]==max(B[b]-p*N[b] for b in ACTIONS)]
 points=sorted(points);transitions=[]
 for i,p in enumerate(points):
  lo=None if p==0 else (p+(points[i-1] if i else 0))/2;hi=(p+points[i+1])/2 if i+1<len(points) else p+max(F(1),abs(p))
  for item in pairs:
   if item['intersection'] and F(item['intersection']['numerator'],item['intersection']['denominator'])==p:
    a,b=item['actions'];third=next(x for x in ACTIONS if x not in [a,b]);item.update(third_action=third,third_value_at_intersection=frac(B[third]-p*N[third]),upper_envelope=a in best(p) and b in best(p),left_order=None if lo is None else ranking({x:B[x]-lo*N[x] for x in ACTIONS},nominal)['ranking'],right_order=ranking({x:B[x]-hi*N[x] for x in ACTIONS},nominal)['ranking'])
  if len(best(p))>1 and (None if lo is None else best(lo))!=best(hi):transitions.append(dict(lambda_value=frac(p),at=best(p),left=None if lo is None else best(lo),right=best(hi),type='FIXED_TRAJECTORY_OPTIMAL_ACTION_TRANSITION'))
 evaluate=lambda p:ranking({a:B[a]-p*N[a] for a in ACTIONS},nominal)
 return dict(action_intercepts={a:frac(B[a]) for a in ACTIONS},action_slopes={a:-N[a] for a in ACTIONS},actual_change_counts=N,lambda_0_evaluation=evaluate(F(0)),lambda_0_01_evaluation=evaluate(F.from_float(.01)),pairwise_intersections=pairs,upper_envelope_transitions=transitions)
def analyze(index):
 source={};cells={};mechanisms=[]
 def track(p):source[str(p)]=sha(p);return read(p)
 reference=track(ROOT/'FULL_SWITCH/D60_PRE_INTERVENTION.json');assignment=reference['science']['nominal_choice']['actions']
 frozen=track(ROOT/'ACTION_FREEZE.json');nominal=next((x['kind'] for x in frozen if x['actions']==assignment),None)
 for item in index:
  d=pathlib.Path(item['directory']);raw=track(d/'FULL_EPISODE_RAW.json');e=track(d/'ECONOMIC_LEDGER.json');fees=[]
  for rec in raw['records']:
   before=rec['policy_input']['assignment'];after=rec['submitted_assignment'];c=rec['step']['action_commit'];n=sum(a!=b for a,b in zip(before,after))
   need(n==c['assignment_change_count'] and abs(c['change_cost']-.01*n)<=EPS,'ACTUAL_CHARGE_BOUNDARY')
   fees.append(dict(tick=rec['policy_input']['tick'],before=before,submitted_assignment=after,changes=n,cost=c['change_cost'],nominal_actions=rec['nominal_choice']['actions']))
  n=sum(x['changes'] for x in fees);c=sum(x['cost'] for x in fees);np=sum(x['changes'] for x in fees if x['tick']<60);cp=sum(x['cost'] for x in fees if x['tick']<60)
  need(n==raw['metrics']['assignment_changes'] and abs(c-raw['metrics']['change_cost'])<=EPS and np==e['prefix']['assignment_changes'] and abs(cp-e['prefix']['change_cost'])<=EPS,'FULL_PREFIX_FEE_TOTAL')
  nf=n-np;cf=c-cp;no=e['future_net']+e['future_change_cost'];parts=sum(e['future_components'].values())
  need(nf>=0 and abs(cf-.01*nf)<=EPS and abs(cf-e['future_change_cost'])<=EPS and abs(no-parts)<=EPS,'FUTURE_FEE_COMPONENTS')
  cells[item['action']]=dict(action=item['action'],full_net=e['full_net'],prefix_net=e['prefix_net'],original_value=e['future_net'],no_change_value=no,exact_no_change_value=frac(no),N_full=n,C_full=c,N_prefix=np,C_prefix=cp,N_future=nf,C_future=cf,boundaries=fees,components=e['future_components'],component_sum=parts,floating_residual=no-parts,source_path=str(d/'FULL_EPISODE_RAW.json'),source_sha256=sha(d/'FULL_EPISODE_RAW.json'),nonchargeable_terminal_releases=[x for x in raw['final']['state']['archives'].values() if x['release_change_cost']==0],execution_origin='ORIGINAL_ACTUAL_EXECUTOR')
  state=raw['final']['state'];hist=state['histories']
  progress={j:max([0.]+[x['progress_before'] for x in h['events']]+[math.fsum([s['latest_clock']['base'],s['latest_clock']['intervals']*.05]) for s in h['segments']]) for j,h in hist.items()}
  mechanisms.append(dict(action=item['action'],D60_progress=raw['records'][2]['step']['frames'][-1]['progress'],D60_boundary=raw['records'][3]['step']['frames'][0],later_decisions=[dict(tick=x['policy_input']['tick'],beliefs=x['policy_input']['beliefs'],nominal_choice=x['nominal_choice'],submitted_assignment=x['submitted_assignment']) for x in raw['records'][4:]],statuses=state['statuses'],completion_times=state['completion_times'],escape_times=state['escape_times'],maximum_service_progress=progress,events=state['events'],histories=hist,components=e['future_components'],cost=cf))
 original={a:cells[a]['original_value'] for a in ACTIONS};zero={a:cells[a]['no_change_value'] for a in ACTIONS};orig=ranking(original,nominal);no=ranking(zero,nominal);effect=relation(original,zero)
 output('ACTUAL_THREE_ACTION_VALUE_MATRIX.json',dict(evaluation_mode='ORIGINAL_EXECUTION_VALUE',cells=cells,source_evidence=source))
 output('ACTUAL_ACTION_RANKING.json',dict(main=orig))
 output('ACTUAL_DECISION_REGRET.json',dict(main=orig,SWITCH_C6_REGRET=orig['switch_regret'],ACTUAL_NOMINAL_ACTION_REGRET=orig['actual_nominal_regret'],HISTORICAL_NOMINAL_SWITCH_REGRET_INTERPRETATION='DIRECT_REPRODUCTION' if read(ROOT/'HISTORICAL_CASE_REPRODUCTION.json')['status']=='CONFIRMED' else 'NEW_SCENE_ONLY'))
 output('ASSIGNMENT_CHANGE_COST_LEDGER.json',dict(cells=cells,source_evidence=source))
 output('ACTUAL_NO_CHANGE_COST_VALUE_MATRIX.json',dict(cells=cells,values=zero))
 output('ACTUAL_CHANGE_COST_RANKING_COMPARISON.json',dict(original=orig,no_change=no,effect=effect,pairwise_direct_fee_contribution={a+'__'+b:dict(delta_original=original[a]-original[b],delta_no_change=zero[a]-zero[b],fee_contribution=-(cells[a]['C_future']-cells[b]['C_future'])) for a,b in combinations(ACTIONS,2)}))
 output('ACTUAL_CHANGE_COST_REGRET_COMPARISON.json',dict(original=orig,no_change=no,FEE_REMOVAL_OPTIMAL_ACTION_SET_CHANGED=effect['optimal_action_set_changed'],FEE_REMOVAL_PAIRWISE_RANK_REVERSALS=effect['strict_rank_reversals'],FEE_REMOVAL_PAIRWISE_ORDER_CHANGES=effect['order_changes'],FEE_REMOVAL_NOMINAL_SUBOPTIMALITY_CHANGED=orig['nominal_suboptimality']!=no['nominal_suboptimality'],REGRET_DIFFERENCE=no['switch_regret']['display']-orig['switch_regret']['display']))
 sens=sensitivity(cells,nominal);output('FIXED_TRAJECTORY_CHANGE_COST_SENSITIVITY.json',dict(main=sens,source_evidence=source))
 matrix=track(REPO/'reports/stfbs_lite_h2_h3_extension_005/NINE_CELL_VALUE_MATRIX.json')['matrix'];four=dict(matrix,NEW_ACTUAL=original);aux={h:{} for h in matrix};missing=[];auxcells=[]
 h1=pathlib.Path(r'D:\1st\stfbs_member_change_001_c18fb23902c84dd4bb3f29931a411158')
 need(sha(h1/'THREE_ACTION_COMPARISON.json')=='59d5402db2a429c78e05bbc1e6a9039520c21589be4de2ee147cde373b5e4a42','H1_SUMMARY')
 for x in track(h1/'evidence_manifest_final.json')['files']:need(sha(h1/x['path'])==x['sha256'],'H1_MANIFEST')
 for world in ['H1','H2','H3']:
  for action in ACTIONS:
   path=(h1/('MEMBER_CHANGE_RAW.json' if action=='MEMBER_CHANGE' else 'reused_historical/'+action+'_RAW.json')) if world=='H1' else REPO/'reports/stfbs_lite_h2_h3_extension_005'/(world+'_'+action)/'BRANCH_RAW.json'
   if not path.is_file():missing.append(dict(world=world,action=action));continue
   raw=track(path);need(raw['net']==matrix[world][action],'AUX_VALUE')
   n=sum(sum(a!=b for a,b in zip(x['before'],x['after'])) for x in raw['boundaries']);cost=sum(x['cost'] for x in raw['boundaries'])
   need(all(sum(a!=b for a,b in zip(x['before'],x['after']))==x['changes'] and abs(x['cost']-.01*x['changes'])<=EPS for x in raw['boundaries']) and abs(raw['change_cost']-cost)<=EPS and abs(cost-.01*n)<=EPS,'AUX_COST')
   value=raw['net']+cost;need(abs(value-sum(raw['components'].values()))<=EPS,'AUX_COMPONENTS');aux[world][action]=value;auxcells.append(dict(world=world,action=action,original=raw['net'],changes=n,cost=cost,no_change=value,path=str(path),sha256=sha(path)))
 aux['NEW_ACTUAL']=zero;origins=dict(H1_H2_H3_EXECUTION_ORIGIN='CONDITIONAL_HIGH_FIDELITY_MODEL',NEW_ACTUAL_EXECUTION_ORIGIN='ORIGINAL_ACTUAL_EXECUTOR',COMPARISON_SCOPE='DESCRIPTIVE_CROSS_EXECUTOR_COMPARISON',UNIFIED_FOUR_WORLD_ROBUST_DECISION_MATRIX='NOT_ESTABLISHED')
 output('FOUR_WORLD_THREE_ACTION_COMPARISON.json',dict(matrix=four,origins=origins,rankings={h:ranking(v) for h,v in four.items()},H1_to_ACTUAL=relation(matrix['H1'],original)))
 output('FOUR_WORLD_THREE_ACTION_NO_CHANGE_COST_MATRIX.json',dict(matrix=aux,origins=origins,source_cells=auxcells,missing_or_unverified_items=missing,rankings={h:ranking(v) for h,v in aux.items() if len(v)==3},H1_to_ACTUAL=relation(aux['H1'],zero) if len(aux['H1'])==3 else None))
 output('SCIENTIFIC_MECHANISM_DETAILS.json',dict(branches=mechanisms,source_evidence=source))
 output('HISTORICAL_DECISION_INERTIA.json',dict(decisions={str(t):track(REPO/('runs/a2_switch_episode_001/R_D%d.json'%t))['choice'] for t in [80,100]},meaning='Saved candidate evidence only; no zero-fee Assignment'))
 discussion='实际执行change_cost=0.01；无费用值仅为FIXED_TRAJECTORY_REVALUATION，ZERO_CHANGE_COST_CLOSED_LOOP_EXECUTED=FALSE。\n移除固定费用仍保留服务进度损失、几何恢复、运动努力、完成时间和终端损失；KEEP与成员变化的差异涉及多因素，不能作单因素因果证明。\n固定费用可能代表未建模通信、协调、组织和模式切换成本或重构正则化，均为待验证解释。不能认定重复计费，也不能宣称0.01具已验证独立经济意义。\n历史D80/D100维持T1可避免撤队0.02的候选证据见HISTORICAL_DECISION_INERTIA.json，新运行的实际选择单独记录；不能推导零费用闭环策略。\n后续可研究不含固定费用任务收益并独立报告变化次数，但本任务不改变收益函数，不安排后续实验。\nH1/H2/H3为MODEL，新ACTUAL为原仿真执行器，仅描述性对照，不是统一鲁棒决策矩阵，也不代表一般算法优势或生产准入。\n'
 (ROOT/'CHANGE_COST_MODELING_DISCUSSION.md').write_text('# 固定费用建模讨论\n\n'+discussion,encoding='utf-8')
 report='# ACTUAL全时域三动作反事实科研报告\n\n三个独立D0—D120 ACTUAL场次，D60是唯一初始干预，后续继续真实A2-R。共同前缀及历史复现分别裁定。\n\n| 动作 | 全程净值 | D60前缀 | 未来净值 | 未来变化次数 | 费用 | 无费用同轨迹值 |\n|---|---:|---:|---:|---:|---:|---:|\n'
 for a in ACTIONS:
  x=cells[a];report+='| %s | %r | %r | %r | %d | %r | %r |\n'%(a,x['full_net'],x['prefix_net'],x['original_value'],x['N_future'],x['C_future'],x['no_change_value'])
 report+='\n实际名义动作：'+str(nominal)+'；原始排序：'+str(orig['ranking'])+'；无费用排序：'+str(no['ranking'])+'。\n原始遗憾：'+str(orig['regret'])+'；无费用遗憾：'+str(no['regret'])+'。\n费用移除最优集合改变：'+str(effect['optimal_action_set_changed'])+'；严格反转：'+str(effect['strict_rank_reversals'])+'。\n\n'
 for m in mechanisms:
  report+='## '+m['action']+'\nD60原进度：'+str(m['D60_progress'])+'；干预后进度：'+str(m['D60_boundary']['progress'])+'。\n状态：'+str(m['statuses'])+'；完成时间：'+str(m['completion_times'])+'；最大进度：'+str(m['maximum_service_progress'])+'。\n未来分量：'+str(m['components'])+'；费用：'+str(m['cost'])+'。\nD80/D100实际分配：'+str([dict(tick=x['tick'],actions=x['submitted_assignment']) for x in m['later_decisions']])+'。\n完整服务事件、合格G/Q区间、观测和信念见分支物理审计及SCIENTIFIC_MECHANISM_DETAILS.json。\n\n'
 report+='## 费用敏感性及四世界描述性对照\nlambda=0、0.01端点、两两交点及第三动作上包络核验见对应JSON；不重新求解策略。H1/H2/H3与新ACTUAL的执行器及世界同时变化，不把排序变化全部归因于不确定性，不重算005 Minimax。\n\n## 建模与科学限制\n'+discussion+'\n## 资源及证据\n三个新身份各一次，旧ACF路线未恢复，生产源码未改。分支资源三方对账、调用闭合、6个STEP及120物理步、Job退出见回执。G0/G4及工作目录和归档实际新增存储均计量；最终结果见FINAL_REPORT、AGGREGATE_RESOURCE_LEDGER及ARCHIVE_VERIFICATION。\n'
 (ROOT/'SCIENTIFIC_SUMMARY.md').write_text(report,encoding='utf-8')
 return dict(complete=not missing,cells=cells,original=orig,no_change=no,effect=effect,sensitivity=sens,missing_auxiliary=missing,nominal=nominal)
