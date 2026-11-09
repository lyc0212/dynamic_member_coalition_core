"""Archive the completed one-shot execution and its existing read-only review."""
import json,hashlib,subprocess
from pathlib import Path
from fractions import Fraction
OUT=Path('reports/stfbs_lite_d1a_h1_revalidation_001')
AUTH=Path('reports/stfbs_lite_d1a_h1_authorization_001')
WATCH=Path('reports/stfbs_lite_d1a_h1_revalidation_001_watchdog')
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,v):
    with (OUT/name).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
approval=read(AUTH/'APPROVAL.json');pre=read(AUTH/'PRECHECK.json')
review=read(OUT/'READ_ONLY_INDEPENDENT_REVIEW_002.json');assert review['status']=='PASS'
pair=read(OUT/'MODEL_PAIR_RESULT.json');cost=read(OUT/'COST.json');receipt=read(WATCH/'WATCHDOG_RECEIPT.json')
assert receipt['exit_code']==0 and receipt['cpu_complete'] and receipt['attempts']==1
assert all(sha(p)==s for p,s in approval['source_pins'].items())
assert all(sha(p)==s for p,s in pre['protected_before'].items())
assert read(WATCH/'LAUNCH.json')['approval_sha256']==sha(AUTH/'APPROVAL.json')
definitions=read('reports/stfbs_lite_d1a_h1_revalidation_prep_001/GATE_ACCEPTANCE_MATRIX.json')
gate_details={
'G0':('PASS','原六份D60来源指纹、历史重放、内部states/冻结快照区分、slots和原H1兼容性检查均成立；相容性为有明确局限的通过，不声称统计覆盖。',['EXTERNAL_REGISTRATION.json','BELIEF_PREFIX_REPLAY_002.json','BELIEF_REPLAY_SEED_002.json','H1_CONTRACT.json','H1_COMPATIBILITY.json','../stfbs_lite_d1a_h1_authorization_001/PRECHECK.json']),
'G1':('PASS','本次四个D80/D100切口的belief独立重放与冻结快照一致；原MODEL消费器数学未改变，按授权复用原差分和来源/时序负例证据，没有把旧物理结果替代新运行。',['KEEP_AUDITS.json','SWITCH_AUDITS.json','READ_ONLY_INDEPENDENT_REVIEW_002.json','REGISTERED_TEST_EVIDENCE_REUSE_002.json']),
'G2':('PASS','原KEEP及受约束SWITCH逐字段一致，六个合法SWITCH/十三完整计划的原选择规则保留；D80/D100 R策略由固定源码保证，实际边界动作与保存的choice一致。',['PLAN_SELECTION.json','KEEP_RAW.json','SWITCH_RAW.json','../stfbs_lite_d1a_h1_authorization_001/APPROVAL.json']),
'G3':('PASS','两条完成的原Branch分别通过外部可信上下文的完整终态历史审计；四个保存的D80/D100历史在只读阶段再次通过语义审计，控制与belief独立验证、服务审计、端点/流/slot身份和跨分支隔离均成立。缓存冲突/复用负例沿用已登记证据，当前H1本身无复用和冲突。',['KEEP_AUDITS.json','SWITCH_AUDITS.json','KEEP_RAW.json','SWITCH_RAW.json','READ_ONLY_INDEPENDENT_REVIEW_002.json','REGISTERED_TEST_EVIDENCE_REUSE_002.json']),
'G4':('PASS','完整D60—D120记录经运行时独立物理/服务/经济审计，通过只读逐帧位移及完整任务账本重算。两条生命周期、释放零附加费、T0未服务机会成本、终端结算及Fraction配对会计均一致。',['ALL_AUDITS.json','READ_ONLY_INDEPENDENT_REVIEW_002.json','MODEL_PAIR_RESULT.json']),
'G5':('PASS','正式watchdog正常退出、完整主进程与Job整树CPU、外部墙钟、原始日志齐全；verify_watchdog_receipt通过。71次观测WLS和1184次策略WLS由原始反馈/候选帧独立复核，共享预算前后计数连续，ACTUAL为0，全部预算满足。',['COST.json','KEEP_RESOURCE.json','SWITCH_RESOURCE.json','../stfbs_lite_d1a_h1_revalidation_001_watchdog/LAUNCH.json','../stfbs_lite_d1a_h1_revalidation_001_watchdog/WATCHDOG_RECEIPT.json','../stfbs_lite_d1a_h1_revalidation_001_watchdog/stdout.bin','../stfbs_lite_d1a_h1_revalidation_001_watchdog/stderr.bin','READ_ONLY_INDEPENDENT_REVIEW_002.json'])}
matrix={g:dict(status=s,original_definition=definitions[g]['original_definition'],dependencies=definitions[g]['dependencies'],conclusion=why,evidence=ev,scope='本次原冻结H1 MODEL；提交主研员/独立审查员复核，不是ACTUAL或泛化结论') for g,(s,why,ev) in gate_details.items()}
save('GATE_ACCEPTANCE_MATRIX.json',matrix)
save('ACCEPTANCE.json',dict(status='D1_A_H1_REVALIDATION_EVIDENCE_READY_FOR_REVIEW',proposed_conclusion='D1_A_MODEL_PAIR_VALIDATED',final_ACCEPTED_declared=False,prior_overall_status='D1_A_BLOCKED',overall_status='D1_A_BLOCKED_PENDING_INDEPENDENT_REVIEW',Gates={g:r['status'] for g,r in matrix.items()},formal_pair_attempts=1,KEEP_runs=1,SWITCH_runs=1,ACTUAL_STEP=0,MODEL_WLS=cost['MODEL_TOTAL_WLS'],ACTUAL_WLS=0,readonly_review_status='PASS',evidence_assembly_incident='First read-only manifest comparison failed on int versus JSON string keys; equal canonical digests proven; first code/error retained; only read-only comparison corrected, no execution/source/raw/approval changes or repeated H1',limitations=['single public-conditional constant-velocity H1','not independent ACTUAL physical validation','not proof of algorithm or closed-loop net benefit','final live Branch audit is retained as runtime independent audit result; D80/D100 full histories also persisted/re-audited','historical tests reused as explicitly allowed, not counted as newly run tests']))
save('EXECUTION_RECORD.json',dict(head=approval['head'],branch=pre['branch'],approved_source_count=45,actual_source_pins={p:sha(p) for p in approval['source_pins']},approval_sha256=sha(AUTH/'APPROVAL.json'),watchdog_PID=receipt['watchdog_pid'],MODEL_process_PID=receipt['child_pid'],watchdog_attempts=receipt['attempts'],watchdog_start_utc=receipt['start_utc'],watchdog_end_utc=receipt['end_utc'],source_unchanged=True,protected_archive_file_count=len(pre['protected_before']),source_worktree_final=subprocess.check_output(['git','status','--short'],text=True),execution_command=['D:\\anaconda3\\python.exe','-B','scripts/stfbs_d1a_watchdog.py','--execute-frozen-h1','--approval-manifest',str(AUTH/'APPROVAL.json'),'--output-dir',str(OUT),'--evidence-dir',str(WATCH)],automatic_retry=False,automatic_commit=False,automatic_push=False))
save('RESOURCE_LEDGER.json',dict(new_H1=dict(internal=cost,external=dict(main_process_CPU_seconds=receipt['process_cpu_seconds'],tree_CPU_seconds=receipt['tree_cpu_seconds'],descendant_CPU_seconds=receipt['descendant_cpu_seconds'],wall_seconds=receipt['wall_seconds'],cpu_complete=receipt['cpu_complete'],total_processes=receipt['total_processes'],remaining_processes=receipt['active_processes'])),branches={n:review['resource'][n] for n in ('KEEP','SWITCH')},historical_three_engineering_runs_MODEL_WLS=3765,cumulative_four_H1_runs_MODEL_WLS=3765+cost['MODEL_TOTAL_WLS'],readonly_audit_attempts=[read(OUT/'READ_ONLY_AUDIT_COST.json'),read(OUT/'READ_ONLY_AUDIT_COST_002.json')],accounting_scope='Historical/extra precheck and shell-command total CPU not fully instrumented; do not infer a cumulative CPU. Complete formal H1 CPU/wall is measured externally above; offline review costs are separate.'))
lines=[]
for k in pair['component_differences']:
    a=review['economics']['KEEP']['components'][k];b=review['economics']['SWITCH']['components'][k]
    lines.append(f'| {k} | {a:.17g} | {b:.17g} | {pair["component_differences"][k]:.17g} |')
text=f'''# 原冻结 H1 一次 MODEL 成对复验报告

**结果：D1_A_H1_REVALIDATION_EVIDENCE_READY_FOR_REVIEW。提出 D1_A_MODEL_PAIR_VALIDATED，供主研员及独立审查员复核；不宣布 D1-A 最终 ACCEPTED。**

## 执行身份与次数

实际HEAD `{approval['head']}`，分支 `{pre['branch']}`。45项必需源码逐文件匹配既有准备快照及本次外部批准记录，运行前后均不变；Python/NumPy/SciPy/psutil和已登记解释器DLL/psutil本地扩展身份一致。没有Git提交、推送、同步或代码修复。原档{len(pre['protected_before'])}份及原A2-SWITCH来源指纹保持不变。

批准来源是用户本次对话直接授权，不编造签名或个人身份。APPROVAL仅创建一次，其SHA与主程序副本、watchdog LAUNCH绑定一致。唯一watchdog PID {receipt['watchdog_pid']}，MODEL子进程PID {receipt['child_pid']}；attempts=1。KEEP/SWITCH各运行一次，均完成tick61—120的60个MODEL区间，未启动第二次实验。

## 原冻结条件及真实审计

同一公开D60、历史重放种子、机器人位置、传感器与原H1；world_digest=`{approval['world_digest']}`，public_digest=`{approval['public_digest']}`。原KEEP/SWITCH逐字段一致，D80/D100都使用固定R策略。两条分支各自形成MODEL反馈与belief，不读取私有实际未来。

KEEP在tick93（4.65秒仿真时间）完成T0，T1在tick120未完成；SWITCH在tick97（4.8500000000000005秒）完成T1，T0在tick120未完成。本H1没有逃逸事件。撤离T0的未服务成本未遗漏，完成/终止和自然释放与事件一致；自然释放均不额外收费。

两条原Branch在运行完成后直接交给独立历史审计，KEEP/SWITCH分别检查2/4条新MODEL历史事件并PASS。verify各检查180个控制/停止项，D80/D100位置、Assignment、任务、历史摘要和belief重放均PASS；服务审计分别检查33/37个区间。只读复核再次验证四个保存的决策历史、belief、流/slot/端点身份及完整逐帧经济账本。G0—G5本次均提交PASS证据，详见GATE_ACCEPTANCE_MATRIX.json；不将准备期Mock结果当作本次实际运行通过。

原Branch终态历史审计的证据是本次运行时直接审计结果；保存的完整D80/D100历史另外进行了只读再审计，未重建伪Branch代替原对象。旧数学/缓存负例依据授权复用，并核对相关源文件未变；旧三组H1的历史验收失败原样保留，不被新结果覆盖。

## MODEL净价值与独立会计

| 分量 | KEEP | SWITCH | SWITCH−KEEP |
|---|---:|---:|---:|
'''+ '\n'.join(lines)+f'''
| change_cost（扣除项） | 0 | 0.02 | 0.02 |
| net | {pair['J_KEEP']:.17g} | {pair['J_SWITCH']:.17g} | {pair['delta']:.17g} |

本次新差额 **+{pair['delta']}** 来自本次合法MODEL运行，未拿旧差额填充。净收益公式保持 completion+flow+late+effort+terminal−change_cost；D60前沉没部分不重复结算，终端惩罚只在D120计入。

净值binary64的精确配对差为 `{review['paired_net_exact']}`；从分量分别作精确配对差再相加为 `{review['paired_component_exact']}`，两者差 `{review['binary64_net_vs_component_residual']}`，由原浮点累计/减法顺序产生，未通过放宽容差掩盖。每条分支的逐项精确增量和残差见READ_ONLY_INDEPENDENT_REVIEW_002.json。

## 实际计算成本与唯一运行保护

| 项目 | 实耗 |
|---|---:|
| KEEP MODEL WLS（观测+策略） | 33+590=623 |
| SWITCH MODEL WLS（观测+策略） | 38+594=632 |
| 整组MODEL观测WLS | 71 |
| 整组MODEL策略WLS | 1184 |
| 整组MODEL WLS | 1255 |
| 新ACTUAL WLS / ACTUAL STEP | 0 / 0 |
| 完整主进程CPU秒 | {receipt['process_cpu_seconds']} |
| Windows Job整树CPU秒 | {receipt['tree_cpu_seconds']} |
| 其中后代CPU秒 | {receipt['descendant_cpu_seconds']} |
| 外部墙钟秒 | {receipt['wall_seconds']} |

共享Budget从KEEP的0/0连续到33/590，再到71/1184，未重置；WLS由保存的反馈estimator_called和候选预测帧独立复核。原始测量请求/新生成分别为KEEP66/66、SWITCH76/76，融合33/38；本H1缓存复用/冲突均0。各类WLS、CPU和900秒墙钟均在原预算内。

watchdog以EXITED/0正常退出，Job累计12个进程（含Git预检子进程），活动进程0，没有强制终止；完整CPU计量成立，无缺失值。verify_watchdog_receipt返回资源必要条件PASS，并另外复核了WLS与所有G5证据，没有将启动成功视作G5自动通过。原三组历史工程运行3765次MODEL WLS仍单列，本次新增1255，累计5020；不虚构历史累计CPU。

## 只读证据组装事件及限制

首个只读辅助检查把内存清单整数键与JSON字符串键直接比较，产生AssertionError。诊断确认两侧规范摘要完全相同；原辅助代码及READ_ONLY_REVIEW_FAILURE.json均保留。随后只修正报告清单的规范摘要比较，全部新检查输出使用_002后缀，不覆盖原失败证据。这里不是MODEL分支、科学数据或运行时独立审计失败，未修改45项源码、原始RAW、批准记录或任何科学条件，也没有重启watchdog、Branch或WLS。额外只读审计禁用哨兵均0，CPU/墙钟独立登记。

这是一个公开条件下、二维匀速、零扰动的H1 MODEL比较，不是ACTUAL独立物理验证，更不等于真实机器人或动态闭环系统收益改善。未充分说明新方法跨场景预测增益，正差额不是验收依据。原总状态保留D1_A_BLOCKED，现具备向负责人申请解除阻断的证据条件，最终裁定待审查。

**本轮已结束。没有第二次H1、修复后重跑、D1-B/C/D、连续转向、ACTUAL闭环或自动Git操作。**
'''
with (OUT/'REPORT.md').open('x',encoding='utf-8') as f:f.write(text)
index={}
for directory in (AUTH,OUT,WATCH):
    for p in sorted(directory.rglob('*')):
        if p.is_file() and p.name!='SHA256.json':index[p.as_posix()]=sha(p)
save('SHA256.json',index)
print('Archived: evidence ready for review; proposal only, no final ACCEPTED.')
