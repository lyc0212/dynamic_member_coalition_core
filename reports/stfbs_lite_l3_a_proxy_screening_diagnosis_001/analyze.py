import time
C,W=time.process_time(),time.monotonic()
import pathlib,json,hashlib,collections
from fractions import Fraction as F
R=pathlib.Path(__file__).resolve().parents[2];D=pathlib.Path(__file__).resolve().parent;S=R/'reports/stfbs_lite_h2_h3_extension_005'
pins={}
def read(p):
 pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return json.loads(p.read_bytes())
def save(n,x):(D/n).write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
def check():
 assert time.process_time()-C<60 and time.monotonic()-W<120
 assert sum(p.stat().st_size for p in D.rglob('*') if p.is_file())<10485760
# Read HEAD directly without invoking Git.
head=(R/'.git/HEAD').read_text().strip();ref=head.split(': ',1)[1];p=R/'.git'/ref
if p.exists():actual=p.read_text().strip()
else:actual=next(line.split()[0] for line in (R/'.git/packed-refs').read_text().splitlines() if line.endswith(' '+ref))
assert ref=='refs/heads/main' and actual=='7d905fbb1f349d1f63af92ab15cfc979c2017252'
worlds=read(S/'WORLD_LIBRARY.json')['worlds'];table=read(S/'PROXY_VALUE_TABLE.json');selection=read(S/'WORLD_SELECTION.json');mapping=read(S/'MODEL_WORLD_MAPPING.json');matrix=read(S/'NINE_CELL_VALUE_MATRIX.json')['matrix'];read(S/'SCIENTIFIC_SUMMARY.json');view=read(S/'PUBLIC_INPUT_FREEZE.json');candidates=read(S/'CANDIDATE_FREEZE.json')
assert len(worlds)==100 and len(table)==300
keys={str(x['assignment_key']):x['kind'] for x in candidates};cells={}
for key,out in table:
 action=keys[str(key[0])];assert key[1]==out['world_digest']
 assert (action,key[1]) not in cells
 cells[action,key[1]]=out
assert len(cells)==300
actions=['KEEP','SWITCH','MEMBER_CHANGE'];h1=next(h for h in worlds if h['is_h1'])
def cell(a,h):return cells[a,h['world_digest']]
def val(a,h):return F.from_float(cell(a,h)['value'])
def rational(x):return None if x is None else dict(numerator=x.numerator,denominator=x.denominator,display=float(x))
scores=[]
for h in worlds:
 margins=[]
 for a in actions:
  for t in cell(a,h)['tasks'].values():
   if t['complete_team'] and (t['P0']>0 or t['NG']>0):
    margin=(120-t['completion_tick'])*.05 if t['completion_tick'] is not None else t['Pmax']-(t['duration']-1e-10)
    margins.append(abs(F.from_float(margin)))
 sensitivity=max(abs((val(a,h)-val('KEEP',h))-(val(a,h1)-val('KEEP',h1))) for a in actions if a!='KEEP')
 scores.append(dict(ordinal=h['world_ordinal'],digest=h['world_digest'],T0_perturbed=h['motion']['0']!=h1['motion']['0'],h2=min(margins) if margins and not h['is_h1'] else None,h3=sensitivity))
h2=min((x for x in scores if x['h2'] is not None),key=lambda x:(x['h2'],x['ordinal']))
h3=min((x for x in scores if x['ordinal'] not in [h1['world_ordinal'],h2['ordinal']]),key=lambda x:(-x['h3'],x['ordinal']))
assert h2['ordinal']==selection['H2']['world_ordinal'] and h3['ordinal']==selection['H3']['world_ordinal']
assert h2['h2']==F(**selection['h2_score']) and h3['h3']==F(**selection['h3_score'])
eligible2=sorted({x['h2'] for x in scores if x['h2'] is not None});eligible3=sorted({x['h3'] for x in scores if x['ordinal'] not in [0,h2['ordinal']]},reverse=True)
risk=[];rankings=collections.Counter()
for h,s in zip(worlds,scores):
 order=sorted(actions,key=lambda a:-val(a,h));rankings[' > '.join(order)]+=1
 flags=dict(keep_above_switch=val('KEEP',h)>val('SWITCH',h),switch_T1_unfinished=cell('SWITCH',h)['tasks']['1']['completion_tick'] is None,member_above_keep=val('MEMBER_CHANGE',h)>val('KEEP',h),member_above_switch=val('MEMBER_CHANGE',h)>val('SWITCH',h),member_best=val('MEMBER_CHANGE',h)>max(val('KEEP',h),val('SWITCH',h)))
 s.update(h2_rank=None if s['h2'] is None else eligible2.index(s['h2'])+1,h3_rank=None if s['ordinal'] in [0,h2['ordinal']] else eligible3.index(s['h3'])+1,selected=s['ordinal'] in [0,h2['ordinal'],h3['ordinal']],risk=flags)
 risk.append(dict(ordinal=s['ordinal'],**flags,order=order,proxy_values={a:cell(a,h)['value'] for a in actions},switch_geometry_interruption='NOT_IDENTIFIABLE_FROM_ARCHIVED_PROXY_SUMMARY'))
ties2=[s['ordinal'] for s in scores if s['h2']==h2['h2']];ties3=[s['ordinal'] for s in scores if s['ordinal'] not in [0,h2['ordinal']] and s['h3']==h3['h3']]
save('WORLD_SCORES_AND_TIES.json',dict(scores=[dict(s,h2=rational(s['h2']),h3=rational(s['h3'])) for s in scores],H2=h2['ordinal'],H3=h3['ordinal'],H2_exact_ties=ties2,H3_exact_ties=ties3,H2_ordinal_tie_break_used=len(ties2)>1,H3_ordinal_tie_break_used=len(ties3)>1,H2_groups=[dict(score=rational(x),ordinals=[s['ordinal'] for s in scores if s['h2']==x]) for x in eligible2],H3_groups=[dict(score=rational(x),ordinals=[s['ordinal'] for s in scores if s['ordinal'] not in [0,h2['ordinal']] and s['h3']==x]) for x in eligible3]))
counts={k:sum(x[k] for x in risk) for k in flags}
intersections=collections.Counter(tuple(x[k] for k in flags) for x in risk)
save('PROXY_RISK_STATISTICS.json',dict(counts=counts,worlds=risk,rankings=dict(rankings),intersection_flag_order=list(flags),intersections=[dict(flags=list(k),count=v) for k,v in intersections.items()],geometry_interruption='NOT_IDENTIFIABLE_FROM_ARCHIVED_PROXY_SUMMARY',probability_interpretation=False))
coverage={}
for j in ['0','1']:
 distribution=collections.Counter(tuple(h['motion'][j]['position']+h['motion'][j]['velocity']) for h in worlds)
 coverage[j]=[dict(state=list(k),count=v) for k,v in distribution.items()]
actual_world=read(R/'runs/a2_switch_episode_001/WORLD_INPUT.json');target=actual_world['targets'][1];actual_pos=[p+v*(3-target['birth']) for p,v in zip(target['position_at_birth'],target['velocity'])]
save('WORLD_COVERAGE.json',dict(target_states=coverage,T0_perturbed=sum(s['T0_perturbed'] for s in scores),selected=[dict(label=h,motion=selection[h]['motion']) for h in ['H1','H2','H3']],actual_T1_position=actual_pos,actual_T1_velocity=target['velocity'],actual_T1_joint_state_covered=any(h['motion']['1']==dict(position=actual_pos,velocity=target['velocity']) for h in worlds),joint_state_combinations=len({json.dumps(h['motion'],sort_keys=True) for h in worlds})))
errors=[];mechanisms=[]
h1dir=pathlib.Path(r'D:\1st\stfbs_member_change_001_c18fb23902c84dd4bb3f29931a411158')
for label in ['H1','H2','H3']:
 h=selection[label]
 if label!='H1':assert mapping[label]['perturbation']['stfbs_world_digest']==h['world_digest'] and mapping[label]['motion']==h['motion']
 for a in actions:
  proxy=cell(a,h);truth=matrix[label][a]
  path=(h1dir/('MEMBER_CHANGE_RAW.json' if a=='MEMBER_CHANGE' else 'reused_historical/'+a+'_RAW.json')) if label=='H1' else S/(label+'_'+a)/'BRANCH_RAW.json'
  raw=read(path) if path.exists() else None
  if raw:assert abs(raw['net']-truth)<1e-8
  errors.append(dict(world=label,action=a,proxy=proxy['value'],high_fidelity=truth,signed_error=proxy['value']-truth,absolute_error=abs(proxy['value']-truth)))
  mechanisms.append(dict(world=label,action=a,proxy_tasks=proxy['tasks'],high_fidelity_events=None if raw is None else raw['events'],high_fidelity_boundaries=None if raw is None else raw['boundaries'],high_fidelity_status=None if raw is None else raw['status'],source=str(path),limitation=None if raw else 'HISTORICAL_MECHANISM_EVIDENCE_MISSING'))
save('NINE_CELL_ERROR_COMPARISON.json',dict(cells=errors,rankings={h:dict(proxy=sorted(actions,key=lambda a:-cell(a,selection[h])['value']),high_fidelity=sorted(actions,key=lambda a:-matrix[h][a])) for h in matrix},mechanisms=mechanisms))
for n in ['stfbs_lite_worlds.py','stfbs_lite_proxy.py','belief.py']:
 p=R/'research/non_oracle'/n;pins[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
actual=read(R/'reports/stfbs_lite_actual_full_episode_counterfactual_001_continuation_001/ACTUAL_THREE_ACTION_VALUE_MATRIX.json')
summary=dict(status='L3_A_PROXY_SCREENING_DIAGNOSIS_PASS_CANDIDATE',H2=h2['ordinal'],H3=h3['ordinal'],H2_ties=ties2,H3_ties=ties3,T0_perturbed_worlds=sum(s['T0_perturbed'] for s in scores),risk_counts=counts,unselected_high_fidelity_unknown=97,actual_used_only_posthoc=True,new_proxy_evaluations=0,new_WLS=0,new_Assignment=0,new_simulations=0,new_attempts=0)
report='# L3-A 代理筛选诊断\n\n'+json.dumps(summary,ensure_ascii=False,indent=2)+'\n\n'
report+='## 世界覆盖与筛选事实\n世界生成对每个目标仅采用原点与四个轴向位置偏移，速度仅不变或增加东向半限速，再作笛卡尔组合。ACTUAL T1相对名义[9.0,10.3]的联合偏移约[0.2,-0.2]不在该位置库内；这是精确状态覆盖不足，不等于已证明代理或高保真风险未覆盖。\nH2先作binary64边界距离运算再转Fraction，H3先将代理价值转Fraction再作差。本次精确平局及ordinal影响见评分文件；没有改变原选择。\n'
for category in [False,True]:
 ss=[s for s in scores if s['T0_perturbed']==category]
 report+='T0扰动='+str(category)+'：世界数'+str(len(ss))+'，最小可用H2分数='+str(min((float(s['h2']) for s in ss if s['h2'] is not None),default=None))+'，最大H3分数='+str(max(float(s['h3']) for s in ss))+'。\n'
report+='H2取跨全部动作/任务的最小有效服务边界距离，并非最差动作遗憾；H3衡量相对H1的动作价值差变化，并非ACTUAL风险或真实遗憾。T0世界未入选的直接依据是完整精确评分、资格与ordinal排序，不能仅凭扰动标签归因。\n\n## 代理风险与误差\n代理风险数目见PROXY_RISK_STATISTICS。任务未完成与动作次优是不同事件；世界数占比只代表确定性假设库，不是真实风险概率。汇总NG/Pmax不能还原几何中断时序，全部标记NOT_IDENTIFIABLE_FROM_ARCHIVED_PROXY_SUMMARY，没有重跑代理。\n\n| 世界 | 动作 | 代理值 | 高保真值 | 代理减高保真 |\n|---|---|---:|---:|---:|\n'
for x in errors:report+='| %s | %s | %r | %r | %r |\n'%(x['world'],x['action'],x['proxy'],x['high_fidelity'],x['signed_error'])
report+='\n## 机制证据与候选解释\nCONFIRMED：run_proxy固定使用view beliefs和初始团队，按G-only及乐观未知Q推进，不生成观测、不更新信念，不执行D80/D100策略。belief.trajectory对已有观测的外推超过1秒后截断，固定信念长期控制会与闭环反馈不同。高保真原始事件、完成时刻、P0/Pmax和分配演化逐格保存在误差文件，H1来自独立历史原件而非净值反推。\nH2/H3代理KEEP高于SWITCH而高保真反向，表明选中世界已经含代理动作风险信号，但该信号不是可信高保真排序；不能把这个事实简化为筛选完全没有发现风险。\nHYPOTHESIS：固定旧信念及一秒截断、G-only服务与缺少反馈/后续改派共同造成排序误差；本任务没有单因素消融，不能确定各机制的独立贡献或主要因果瓶颈。\n\n## 下一步优先方向\n优先验证代理闭环反馈一致性，特别是固定信念/一秒截断对KEEP服务完成预测的影响。依据是已有九格中可直接观察的完成状态与排序误差；仅扩充世界或改筛选尚不能保证代理排名可信。这是待验证研究方向，不在本轮修改算法或启动L3-B。世界联合位置覆盖及筛选分数目标仍有独立局限；97个未选世界高保真风险未知，不能按代理标签当作真值。ACTUAL只用于事后诊断，未参与原筛选或新鲁棒矩阵。\n\n生产准入BLOCKED；无Git操作、生产修改、新科学计算或attempt消费。\n'
(D/'REPORT.md').write_text(report,encoding='utf-8');check()
save('INPUT_SHA256.json',pins);summary.update(cpu_seconds=time.process_time()-C,wall_seconds=time.monotonic()-W,storage_bytes=sum(p.stat().st_size for p in D.rglob('*') if p.is_file()));save('FINAL_REPORT.json',summary)
save('evidence_manifest.json',dict(files=[dict(path=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in D.iterdir() if p.is_file()]))
check();print(json.dumps(summary))
