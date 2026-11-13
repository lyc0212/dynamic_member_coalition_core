from task_support import *
from fractions import Fraction as F
from itertools import combinations
ACTIONS=['KEEP','SWITCH','MEMBER_CHANGE']
def frac(x):
 x=F.from_float(x) if isinstance(x,float) else F(x)
 return dict(numerator=x.numerator,denominator=x.denominator,display=float(x))
def ranking(values):
 q={a:F.from_float(v) if isinstance(v,float) else F(v) for a,v in values.items()};best=max(q.values());reg={a:best-v for a,v in q.items()}
 return dict(values={a:float(v) for a,v in q.items()},exact_values={a:frac(v) for a,v in q.items()},ranking=sorted(q,key=lambda a:(-q[a],ACTIONS.index(a))),best_value=frac(best),exact_optimal_actions=[a for a,v in q.items() if v==best],approximate_optimal_actions=[a for a,v in reg.items() if v<=F.from_float(EPS)],regret={a:frac(v) for a,v in reg.items()},pairwise_differences={a+'__'+b:frac(q[a]-q[b]) for a,b in combinations(q,2)},nominal_switch_suboptimality='CONFIRMED' if reg['SWITCH']>F.from_float(EPS) else 'NOT_DEMONSTRATED')
def analyze(root,index):
 metadata=dict(task_id=TASK,version='V1.2',execution_change_cost=.01,evaluation_mode='FIXED_TRAJECTORY_REVALUATION',horizon='D60_PRE_ASSIGNMENT_TO_D120_TERMINAL',numerical_tolerance=EPS,counterfactual_policy_execution=False,zero_change_cost_closed_loop_executed=False,scientific_boundary='One fixed D60; same later A2-R; no zero-fee closed-loop or policy reoptimization',missing_or_unverified_items=[])
 def output(n,x):save(n,dict(metadata,**x))
 source={}
 def track(p):source[str(p)]=sha(p);return read(p)
 h=track(ROOT/'HISTORICAL_ACTUAL_VALUE_LEDGER.json');model={};ledgers=[];mechanisms=[]
 def ledger(world,action,path,expected):
  raw=track(path);need(abs(raw['net']-expected)<=EPS,'ACCEPTED_RAW_VALUE')
  boundaries=raw['boundaries'];need([b['tick'] for b in boundaries]==[60,80,100],'BOUNDARY_TICKS')
  records=[]
  for b in boundaries:
   count=sum(x!=y for x,y in zip(b['before'],b['after']))
   need(type(b['changes']) is int and b['changes']==count and abs(b['cost']-.01*count)<=EPS,'FEE_BOUNDARY')
   records.append(dict(b,branch_id=raw['branch'],source_path=str(path)))
  n=sum(b['changes'] for b in records);cost=sum(b['cost'] for b in records)
  need(abs(cost-raw['change_cost'])<=EPS and abs(sum(raw['components'].values())-cost-raw['net'])<=EPS,'FEE_TOTAL')
  no=raw['net']+raw['change_cost'];parts=sum(raw['components'].values());need(abs(no-parts)<=EPS,'NO_FEE_COMPONENTS')
  row=dict(world=world,action=action,execution_origin='MODEL',horizon=[60,120],execution_change_cost=.01,original_value=raw['net'],chargeable_boundary_records=records,total_assignment_changes=n,total_change_cost=raw['change_cost'],non_change_cost_components=raw['components'],no_change_value=no,independent_component_sum=parts,floating_residual=no-parts,exact_no_change_value=frac(no),source_paths=[str(path)],source_sha256={str(path):sha(path)},ledger_validation_status='PASS',nonchargeable_terminal_releases=[e for e in raw['events'] if e.get('release_change_cost')==0])
  ledgers.append(row);return row
 for row in index:
  d=pathlib.Path(row['directory']);rep=track(d/'FINAL_BRANCH_REPORT.json');need(rep['valid_cell_candidate'],'UNACCEPTED_CELL')
  for e in track(d/'evidence_manifest.json')['files']:need(sha(d/e['path'])==e['sha256'],'CELL_MANIFEST')
  x=ledger('A_HISTORICAL_MODEL',row['action'],d/'BRANCH_RAW.json',rep['raw_net']);model[row['action']]=x
  raw=read(d/'BRANCH_RAW.json');history=track(d/'TERMINAL_BRANCH_HISTORY.json')['histories']
  maxprogress={}
  for j in history:
   maxprogress[j]=max([0.]+[math.fsum([s['latest_clock']['base'],s['latest_clock']['intervals']*.05]) for s in history[j]['segments']]+[e.get('progress_before',0.) for e in history[j]['events']])
  mechanisms.append(dict(action=row['action'],components=raw['components'],change_cost=raw['change_cost'],events=raw['events'],status=raw['status'],boundaries=raw['boundaries'],decisions=[dict(tick=d['view']['tick'],beliefs=d['view']['beliefs'],actions=d['choice']['actions'],exact_value=d['choice']['exact_value']) for d in raw['decisions']],maximum_service_progress=maxprogress,histories=history,observation_acceptance_summary=raw.get('raw_counts')))
 histrow=dict(world='A_HISTORICAL',action='SWITCH',execution_origin='HISTORICAL_ACTUAL',horizon=[60,120],execution_change_cost=.01,original_value=h['net'],chargeable_boundary_records=h['boundaries'],total_assignment_changes=h['N_change'],total_change_cost=h['change_cost'],non_change_cost_components=h['components'],no_change_value=h['net']+h['change_cost'],independent_component_sum=sum(h['components'].values()),floating_residual=h['net']+h['change_cost']-sum(h['components'].values()),source_paths=list(h['source_sha256']),source_sha256=h['source_sha256'],ledger_validation_status='PASS')
 ledgers.append(histrow);main=dict(model);main['SWITCH']=histrow
 original={a:main[a]['original_value'] for a in ACTIONS};zero={a:main[a]['no_change_value'] for a in ACTIONS}
 modeloriginal={a:model[a]['original_value'] for a in ACTIONS};modelzero={a:model[a]['no_change_value'] for a in ACTIONS}
 orig=ranking(original);no=ranking(zero);mo=ranking(modeloriginal);mn=ranking(modelzero)
 nominal=orig['nominal_switch_suboptimality'] if orig['nominal_switch_suboptimality']==mo['nominal_switch_suboptimality'] else 'INCONCLUSIVE'
 output('ACTUAL_THREE_ACTION_VALUE_MATRIX.json',dict(evaluation_mode='ORIGINAL_EXECUTION_VALUE',main=original,all_model=modeloriginal,historical_actual_switch_value=h['net'],model_replayed_switch_value=modeloriginal['SWITCH'],model_minus_historical_difference=modeloriginal['SWITCH']-h['net']))
 output('ACTUAL_ACTION_RANKING.json',dict(main=orig,all_model=mo))
 output('ACTUAL_DECISION_REGRET.json',dict(main=orig,all_model=mo,ORIGINAL_NOMINAL_ACTION_SUBOPTIMALITY=nominal))
 archive=REPO/'reports/stfbs_lite_h2_h3_extension_005';matrix=track(archive/'NINE_CELL_VALUE_MATRIX.json')['matrix'];four=dict(matrix,A_HISTORICAL=original)
 h1=pathlib.Path(r'D:\1st\stfbs_member_change_001_c18fb23902c84dd4bb3f29931a411158')
 comparison=h1/'THREE_ACTION_COMPARISON.json';need(sha(comparison)=='59d5402db2a429c78e05bbc1e6a9039520c21589be4de2ee147cde373b5e4a42','H1_SUMMARY')
 for e in track(h1/'evidence_manifest_final.json')['files']:need(sha(h1/e['path'])==e['sha256'],'H1_MANIFEST')
 auxiliary={};missing=[]
 for world in ['H1','H2','H3']:
  auxiliary[world]={}
  for action in ACTIONS:
   path=(h1/('MEMBER_CHANGE_RAW.json' if action=='MEMBER_CHANGE' else 'reused_historical/'+action+'_RAW.json')) if world=='H1' else archive/(world+'_'+action)/'BRANCH_RAW.json'
   if not path.is_file():missing.append(dict(world=world,action=action,reason='RAW_LEDGER_UNAVAILABLE'));continue
   x=ledger(world,action,path,matrix[world][action]);auxiliary[world][action]=x['no_change_value']
 auxiliary['A_HISTORICAL']=zero
 def reversals(a,b):
  pairs=[];orders=[]
  for x,y in combinations(ACTIONS,2):
   d=a[x]-a[y];e=b[x]-b[y]
   sign=lambda v:1 if v>EPS else -1 if v<-EPS else 0
   if sign(d)*sign(e)==-1:pairs.append([x,y])
   if sign(d)!=sign(e):orders.append([x,y])
  return dict(strict_rank_reversals=pairs,order_changes=orders,optimal_action_set_changed=ranking(a)['approximate_optimal_actions']!=ranking(b)['approximate_optimal_actions'])
 h1orig=reversals(matrix['H1'],original);fee=reversals(original,zero)
 h1zero=reversals(auxiliary['H1'],zero) if len(auxiliary['H1'])==3 else None
 output('FOUR_WORLD_THREE_ACTION_COMPARISON.json',dict(matrix=four,H1_to_ACTUAL=h1orig))
 output('ASSIGNMENT_CHANGE_COST_LEDGER.json',dict(cells=ledgers,source_evidence=source,missing_or_unverified_items=missing,rule='Complete Assignment changes at committed D60/D80/D100 only; natural release not charged; historical prefix subtracted'))
 output('ACTUAL_NO_CHANGE_COST_VALUE_MATRIX.json',dict(main=zero,all_model=modelzero,actual_cells={a:main[a] for a in ACTIONS},model_cells=model))
 output('FOUR_WORLD_THREE_ACTION_NO_CHANGE_COST_MATRIX.json',dict(matrix=auxiliary,world_rankings={h:ranking(v) for h,v in auxiliary.items() if len(v)==3},H1_to_ACTUAL=h1zero,missing_or_unverified_items=missing))
 contributions={a+'__'+b:dict(delta_original=original[a]-original[b],delta_no_change=zero[a]-zero[b],direct_fee_contribution=-(main[a]['total_change_cost']-main[b]['total_change_cost'])) for a,b in combinations(ACTIONS,2)}
 output('ACTUAL_CHANGE_COST_RANKING_COMPARISON.json',dict(original=orig,no_change=no,all_model_original=mo,all_model_no_change=mn,fee_effect=fee,pairwise_direct_contribution=contributions,H1_original_to_ACTUAL=h1orig,H1_no_change_to_ACTUAL=h1zero))
 output('ACTUAL_CHANGE_COST_REGRET_COMPARISON.json',dict(original=orig,no_change=no,all_model_original=mo,all_model_no_change=mn,ORIGINAL_NOMINAL_ACTION_SUBOPTIMALITY=nominal,NO_CHANGE_COST_FIXED_TRAJECTORY_NOMINAL_ACTION_SUBOPTIMALITY=no['nominal_switch_suboptimality'] if no['nominal_switch_suboptimality']==mn['nominal_switch_suboptimality'] else 'INCONCLUSIVE',FEE_REMOVAL_OPTIMAL_ACTION_SET_CHANGED=fee['optimal_action_set_changed'],FEE_REMOVAL_PAIRWISE_RANK_REVERSALS=fee['strict_rank_reversals'],FEE_REMOVAL_NOMINAL_SUBOPTIMALITY_CHANGED=orig['nominal_switch_suboptimality']!=no['nominal_switch_suboptimality'],REGRET_DIFFERENCE=no['regret']['SWITCH']['display']-orig['regret']['SWITCH']['display']))
 def sensitivity(cells):
  B={a:F.from_float(cells[a]['no_change_value']) for a in ACTIONS};N={a:cells[a]['total_assignment_changes'] for a in ACTIONS};pairs=[];points=set()
  for a,b in combinations(ACTIONS,2):
   db=B[a]-B[b];dn=N[a]-N[b];x=db/dn if dn else None
   item=dict(actions=[a,b],intercept_difference=frac(db),change_count_difference=dn,intersection=None if x is None else frac(x),parallel=dn==0 and db!=0,coincident=dn==0 and db==0,nonnegative=x is not None and x>=0,in_0_to_0_01=x is not None and 0<=x<=F.from_float(.01))
   if x is not None and x>=0:points.add(x)
   pairs.append(item)
  points=sorted(points);transitions=[]
  best=lambda x:[a for a in ACTIONS if B[a]-x*N[a]==max(B[b]-x*N[b] for b in ACTIONS)]
  for i,x in enumerate(points):
   left=None if x==0 else (x+(points[i-1] if i else F(0)))/2
   right=(x+points[i+1])/2 if i+1<len(points) else x+max(F(1),abs(x))
   at=best(x);lo=[] if left is None else best(left);hi=best(right)
   if len(at)>1 and lo!=hi:transitions.append(dict(type='FIXED_TRAJECTORY_OPTIMAL_ACTION_TRANSITION',lambda_value=frac(x),at=at,left=lo,right=hi,left_domain_exists=left is not None))
   for item in pairs:
    if item['intersection'] and F(item['intersection']['numerator'],item['intersection']['denominator'])==x:item.update(upper_envelope=all(a in at for a in item['actions']),left_optimal=lo,right_optimal=hi)
  evaluate=lambda x:ranking({a:B[a]-x*N[a] for a in ACTIONS})
  return dict(action_intercepts={a:frac(v) for a,v in B.items()},action_slopes={a:-N[a] for a in ACTIONS},actual_change_counts=N,lambda_0_evaluation=evaluate(F(0)),lambda_0_01_evaluation=evaluate(F.from_float(.01)),pairwise_intersections=pairs,upper_envelope_transitions=transitions)
 aux_sens={}
 for world in ['H1','H2','H3']:
  cells={x['action']:x for x in ledgers if x['world']==world}
  if len(cells)==3:aux_sens[world]=sensitivity(cells)
 output('FIXED_TRAJECTORY_CHANGE_COST_SENSITIVITY.json',dict(execution_lambda=.01,main=sensitivity(main),all_model=sensitivity(model),auxiliary=aux_sens,source_evidence=source,missing_or_unverified_items=missing))
 # Historical decision candidate ledgers, no Assignment invocation.
 inertia=[]
 for tick in [80,100]:
  record=track(REPO/('runs/a2_switch_episode_001/R_D%d.json'%tick))
  inertia.append(dict(tick=tick,selected_actions=record['choice']['actions'],selected_rows=record['choice']['rows'],evidence=record['evidence'],interpretation='Historical selected candidate bookkeeping only; no zero-fee reoptimization'))
 output('HISTORICAL_DECISION_INERTIA.json',dict(decisions=inertia))
 output('SCIENTIFIC_MECHANISM_DETAILS.json',dict(branches=mechanisms,source_evidence=source))
 discussion="""# 固定改派费用建模讨论
实际执行change_cost=0.01；本任务无费用结果只为FIXED_TRAJECTORY_REVALUATION，COUNTERFACTUAL_POLICY_EXECUTION=FALSE，ZERO_CHANGE_COST_CLOSED_LOOP_EXECUTED=FALSE。
移除固定费用仍保留实际服务进度损失、观测/几何恢复、控制努力、任务完成时间及终端惩罚。账本分解不等于单因素因果证明，KEEP与MEMBER_CHANGE差异不能仅归于时钟重置。
固定费用可能代表未建模通信、组织、模式切换开销或抑制频繁重构的正则化；这些为待验证解释。不能认定费用重复惩罚，也不能宣称0.01有已验证的独立经济意义。
D80/D100维持T1的历史候选及费用见HISTORICAL_DECISION_INERTIA.json。该账本能说明直接会计贡献与可能惯性，不能推导零费用重新求解后的动作或轨迹。
是否将无固定费用任务净收益作为主要评价目标应由研究者结合本次双口径结果决定。可将变化次数作为独立指标保留；本任务不改变冻结收益函数，不自动安排零费用闭环研究。
"""
 (ROOT/'CHANGE_COST_MODELING_DISCUSSION.md').write_text(discussion,encoding='utf-8')
 report='# ACTUAL 三动作反事实 V1.2 科研报告\n\n实际执行费用0.01，无费用结果仅为同轨迹重评价；未执行零费用闭环。\n\n共同D60为POST_FREEZE_PRE_ASSIGNMENT，原联盟U0/U1服务目标0，已有约0.6秒合法进度。历史原始证据恢复与当前候选一致。SWITCH采用一次MODEL校准，结果见SWITCH_REPLAY_EQUIVALENCE.json，不能将历史值静默替换为MODEL值。\n\n| 动作 | 原始价值 | 收费变化次数 | 实际费用 | 无费用同轨迹价值 |\n|---|---:|---:|---:|---:|\n'
 for a in ACTIONS:report+='| %s | %r | %d | %r | %r |\n'%(a,original[a],main[a]['total_assignment_changes'],main[a]['total_change_cost'],zero[a])
 report+='\n原始排序：'+str(orig['ranking'])+'；无费用排序：'+str(no['ranking'])+'。\n原始SWITCH遗憾：'+str(orig['regret']['SWITCH'])+'；无费用SWITCH遗憾：'+str(no['regret']['SWITCH'])+'。\n费用移除最优集合改变：'+str(fee['optimal_action_set_changed'])+'；严格反转：'+str(fee['strict_rank_reversals'])+'。\n\n'
 for b in mechanisms:
  report+='## '+b['action']+'\n经济分量：'+str(b['components'])+'；费用：'+str(b['change_cost'])+'。\n终端事件：'+str(b['events'])+'。\n最大连续服务进度：'+str(b['maximum_service_progress'])+'；实际分配边界：'+str(b['boundaries'])+'。\nD80/D100策略、信念、完整服务历史和G/Q端点见SCIENTIFIC_MECHANISM_DETAILS.json及各分支原始反馈。\n\n'
 report+='## 费用敏感性与解释\n临界点与上包络逐项见FIXED_TRAJECTORY_CHANGE_COST_SENSITIVITY.json；lambda=0及0.01端点均计算。两线交叉不自动视为最优集合变化。费用直接贡献见ACTUAL_CHANGE_COST_RANKING_COMPARISON.json，四世界双口径及排序反转见对应矩阵文件。\n\n服务时钟重置、成员位置、控制努力、观测信念与完成结果共同决定价值，不能把全部差异归为单一因素。无费用下优势不依赖固定费用直接扣除，但仍可能依赖原费用影响的后续策略。建模意义和决策惯性见CHANGE_COST_MODELING_DISCUSSION.md。\n\n结论限定一个历史D60、一个真实外生世界、三个初始动作及相同后续A2-R；不证明一般统计优势、全动态策略最优或零费用闭环优势。生产准入BLOCKED。源代码未改，历史实验未重跑；仅执行授权的新反事实分支。实际资源、attempt与进程退出见FINAL_REPORT和AGGREGATE_RESOURCE_LEDGER，SHA256归档核验另行保存。\n'
 (ROOT/'SCIENTIFIC_SUMMARY.md').write_text(report,encoding='utf-8')
 return dict(complete=not missing,original_counterfactual='PASS_CANDIDATE',G4_change_cost_analysis='PASS_CANDIDATE' if not missing else 'INCOMPLETE',original_ranking=orig,no_change_ranking=no,model_ranking=mo,nominal_suboptimality=nominal,fee_effect=fee,missing=missing)
