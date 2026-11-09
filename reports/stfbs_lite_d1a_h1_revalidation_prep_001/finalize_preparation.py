"""Read-only fingerprint review and preparation report assembly; no MODEL execution."""
from pathlib import Path
import json,hashlib,subprocess

root=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(name,value):(root/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
baseline=read(root/'BASELINE.json')
# Correct the one interface file already edited when the bulk snapshot was taken;
# use exact committed bytes, not shell text/newline conversion.
baseline['tracked_sha256']['research/non_oracle/stfbs_d1a_verify.py']=hashlib.sha256(subprocess.check_output(['git','show','HEAD:research/non_oracle/stfbs_d1a_verify.py'])).hexdigest()
baseline['note']='Initial HEAD and clean tree observed before edits. Pins cover scientific code/config/docs and four historical report trees. Original verify bytes recovered exactly from HEAD; this one-line edit preceded bulk snapshot. Git runtime staging excluded.'
save('BASELINE.json',baseline)
evidence=read(root/'TEST_EVIDENCE_004.json')
assert evidence['success']
assert read(root/'TEST_EVIDENCE_002.json')['success']
for p in root.glob('ZERO_WLS_STEP_PROOF_*.json'):assert not any(read(p)['calls'].values())
allowed={'scripts/stfbs_d1a_run.py','research/non_oracle/stfbs_d1a_verify.py'}
changed=[p for p,v in baseline['tracked_sha256'].items() if sha(p)!=v]
assert set(changed)<=allowed,changed
old=[p for p in baseline['tracked_sha256'] if p.startswith('reports/stfbs_lite_d1a_')]
save('PRESERVATION_CHECK.json',dict(changed_tracked=changed,unchanged_old_archive_files=len(old),all_other_scientific_pins_unchanged=True,scope=baseline['scope']))
original=Path(r'C:\Users\14738\.codex\attachments\7b5f1f16-765f-49a5-bfc2-2cb4070e57b8\已粘贴的文本.txt')
prep=Path(r'C:\Users\14738\.codex\attachments\df79cbb6-96a6-4291-8a12-ecd09051c5fc\已粘贴的文本.txt')
(root/'ORIGINAL_D1A_V1_3_REFERENCE.txt').write_bytes(original.read_bytes())
(root/'PREPARATION_V0_2_REFERENCE.txt').write_bytes(prep.read_bytes())
save('AUTHORIZATION_REFERENCE_PINS.json',{'original_V1_3':sha(original),'preparation_V0_2':sha(prep),'note':'Historical reference only; no future H1 approval has been created'})
cases=evidence['cases']
frozen=next(c for c in cases if c['group']=='FROZEN')
save('FROZEN_H1_IDENTITY.json',frozen)
for filename,group in [('MOTION_ID_TYPE_TESTS.json','TYPE'),('REAL_PURE_STATE_AUDIT_TESTS.json','C2'),('STUB_ORCHESTRATION_TESTS.json','C1')]:save(filename,[c for c in cases if c['group']==group])
save('H1_ENTRY_FAIL_CLOSED_TESTS.json',[c for c in cases if c['group'].startswith('ENTRY')])
save('MOTION_ID_TYPE_CONTRACT.json',dict(status='INTERFACE_TYPE_CONTRACT_PASS',boundary='stfbs_d1a_audit_input.audit_input',input='integer or canonical decimal JSON keys in world.motion only',output='isolated copy with integer target keys',reject=['int/string alias duplicates','bool','noncanonical IDs','unknown/missing IDs'],unchanged=['original world','motion numbers','world_digest','source JSON'],scope='Full JSON reload of every other result map is NOT certified; the main run passes in-memory results through this same boundary'))
save('G3_CLOSEOUT_DEPENDENCY.json',dict(accepted_prior_repairs=['g3_history_repair_001','g3_supplement_001','g3_audit_hardening_001'],new_H1_G3='NOT_RUN',prior_finite_repair_not_full_G3=True))
save('EXTERNAL_CONTEXT_FLOW.json',dict(status='PASS',sequence=['verified_registration source-pinned recovery','external KEEP/SWITCH context registration','frozen world and plan comparison','one Budget shared','Branch construction/run (stub this round)','audit_branch_independent on same Branch/context','one audit_input copy','verify/context + service_audit + audit','budget check','both branches valid before pair candidate'],C1='stub call order and object identity tests',C2='actual Branch/transaction/auditor; synthetic fusion only'))
limits=dict(MODEL_OBSERVATION_WLS=1000,MODEL_POLICY_EVALUATION_WLS=4000,MODEL_TOTAL_WLS=5000,ACTUAL_WLS=0,cpu_seconds=600,wall_seconds=900)
save('SHARED_BUDGET_CONTRACT.json',dict(limits=limits,scope='whole KEEP/SWITCH pair, not per branch',proof='C1 same Budget identity and cumulative before/after snapshots',actual_H1_cost='NOT_RUN',historical_MODEL_WLS=3765,historical_cost_not_new_measurement=True))
save('ZERO_WLS_STEP_PROOF.json',dict(attempts={p.name:read(p) for p in root.glob('ZERO_WLS_STEP_PROOF_*.json')},actual_WLS=0,MODEL_physics_advances=0,ACTUAL_STEP=0,real_Branch_run=0,real_Branch_advance=0,main_pair_runs=0,subprocess_scope='CLI no-args/missing args/help return before registration; -B disables bytecode writes'))
definitions={
'G0':('合法历史、内部 states/冻结快照区分、历史前缀重放、已有 D60 slots 的身份、H1 三态相容性',['verified_registration','frozen_registration','execute_registered compatibility'],['BELIEF_REPLAY_SEED.json','runs/a2_switch_episode_001/R_D*.json','H1_CONTRACT.json'],['EXTERNAL_REGISTRATION.json','H1_CONTRACT.json','H1_COMPATIBILITY.json'],[]),
'G1':('MODEL belief 更新及20-tick冻结等价',['ModelBeliefConsumer','verify'],['research/non_oracle/stfbs_d1a_state.py','tests/test_stfbs_d1a_*.py'],['原合成差分/负例测试及源码指纹','KEEP_AUDITS.json','SWITCH_AUDITS.json'],['G0']),
'G2':('KEEP/SWITCH 强制受约束选择、完整枚举、身份冻结',['select','frozen_registration'],['reports/stfbs_lite_d1a_001/PLAN_SELECTION.json','runs/a2_switch_episode_001/R_D60.json'],['PLAN_SELECTION.json','冻结世界、来源和计划摘要'],['G0']),
'G3':('三层测量身份、原始缓存复用与冲突拒绝、D60端点、完整D80/D100 view、联合物理正确',['Branch.run','audit_branch_independent','verify','service_audit'],['stfbs_d1a_model.py','stfbs_d1a_state.py','stfbs_d1a_history_audit.py'],['KEEP_RAW.json','SWITCH_RAW.json','KEEP_AUDITS.json','SWITCH_AUDITS.json','原缓存负例与事务证据'],['G0','G1','G2']),
'G4':('两条分支生命周期与独立完整收益核验',['audit','service_audit','verify'],['stfbs_d1a_audit.py','stfbs_d1a_verify.py'],['ALL_AUDITS.json','MODEL_PAIR_RESULT.json','逐帧成本、事件、释放、改派和精确二进制会计残差'],['G3']),
'G5':('原始测量、端点融合、WLS分账、预算护栏、正负例及复现证据',['Budget.estimator','Budget.check','main/run_pair','外部进程计时'],['stfbs_d1a_model.py Budget','原 V1.3 第十节'],['COST.json','KEEP_RESOURCE.json','SWITCH_RESOURCE.json','外部MAIN_TIMING和进程退出日志','失败时MAIN_FAILURE.json/分支PARTIAL'],['G0','G1','G2','G3','G4'])}
matrix={}
for gate,(definition,entry,sources,required,dependencies) in definitions.items():
    matrix[gate]=dict(original_definition=definition,source_files=sources,entry_points=entry,required_evidence=required,dependencies=dependencies,assertion='保持原V1.3对应章节全部条款；本表索引不得替代或缩减原文',independent_method={'G0':'已冻结SHA + 历史观测重放与冻结快照逐字段比对','G1':'原Beliefs数学差分、来源/时序负例和运行中独立belief重放','G2':'原候选表受约束选择与独立完整枚举，逐字段对照原计划','G3':'原Branch+外部不可变上下文的完整历史语义审计，独立控制/服务审计，测量身份与冲突负例','G4':'逐帧与事件重算收益各分量及改派费；Fraction二进制精确和配对差核验','G5':'共享预算计数前后差、原始融合/策略调用账本、外部墙钟与进程CPU对照'}[gate],PASS='所有原始断言成立且必要证据齐全',FAIL='任一实质差异、来源或预算违规；保存首次失败，禁止自动重跑',missing_evidence='NOT_VERIFIED，不得推定PASS',current_new_H1_status='NOT_RUN')
save('GATE_ACCEPTANCE_MATRIX.json',matrix)
save('ENGINEERING_FAILURES.json',dict(initial_command_failure='python absent from PATH; switched to D:/anaconda3/python.exe',aborted_baseline_attempt='broad baseline helper interrupted before completing; selected scientific/archive pins collected via PowerShell instead; no physics calls',first_test='TEST_ATTEMPT_001.log: misspelled supplement module, 20 real tests passed + 1 loader error',repair='corrected tests.test_stfbs_d1a_history_supplement',subsequent=['TEST_ATTEMPT_002.log: 26/26','TEST_ATTEMPT_003.log: 8/8 affected','TEST_ATTEMPT_004.log: 8/8 final affected'],no_science_changes=True))
(root/'AUDIT_WIRING_DESIGN.md').write_text('''# 审计接线

`main → authorize → 一个Budget → frozen_registration → 新目录独占创建 → execute_registered → run_pair`。
来源六份原始文件由已有登记器核验。KEEP/SWITCH 外部上下文在任何 Branch 创建前固定，由主驱动分别持有；不用 Branch 自带的可变上下文替代独立上下文。

每条分支运行后先保存原始结果，直接审计原 Branch，再将同一个只读隔离审计副本交给 verify、service_audit、audit。只有 world.motion 的 ID 映射经过一个边界规范化；verify 仅一处字符串访问改为整数访问，公式未改。类型测试只证明这个映射合同，不宣称所有JSON重载字段或完整物理结果已经验收。

一个必要审计抛错、返回非PASS或预算失败，立即阻止下条分支和收益发布；阶段状态保留FAIL/NOT_RUN。真实运行异常保存部分帧、事件、反馈、历史和成本。最终结果只标 PAIR_AUDITS_PASS_PENDING_G0_G5_REVIEW，不自动签发整个D1-A通过。

默认CLI无任何实验输出；导入与help不执行。未来批准记录必须绑定实际HEAD、逐文件源码SHA、固定H1身份、预算及显式新路径。批准JSON是负责人授权的记录，不是对恶意Python代码的安全沙箱。本轮未创建有效批准记录。
''',encoding='utf-8')
(root/'H1_REVALIDATION_PROTOCOL.md').write_text('''# 冻结H1成对复验协议（待另行授权）

本文件为准备产物，不是执行授权。原V1.3全文见 ORIGINAL_D1A_V1_3_REFERENCE.txt；本次准备V0.2全文亦附档。GATE_ACCEPTANCE_MATRIX.json 原样保留原V1.3的六项Gate定义及其依赖。准备简表对G1/G3的概括不替代原定义。

## 固定条件

同一原A2-SWITCH公开D60与历史种子；D60—D120；H1、KEEP、受约束SWITCH与原身份逐字段相同。D80/D100继续用R，不使用私有未来。零角度扰动、原传感器、原G/Q/时钟、原收益与控制均不变。旧三组运行及3765次MODEL WLS仅作工程历史；原正差额不作为新结果。

## 下次授权后的执行前关口

负责人明确批准一次复验，固定实际执行版本和源码依赖指纹。只用新目录 reports/stfbs_lite_d1a_h1_revalidation_001（若已存在立即停止）。外部批准记录字段：status=APPROVED_FOR_ONE_H1_REVALIDATION、experiment=D1_A_FROZEN_H1、authorized_by、实际head、完整source_pins路径→SHA256、output_dir、limits（见SHARED_BUDGET_CONTRACT）。还需固定world_digest/public_digest和PLAN_SELECTION身份供独立复核；驱动由原档逐字段强制核对。该记录必须来自新的负责人授权，本轮未生成。

未来命令形态：D:/anaconda3/python.exe -B scripts/stfbs_d1a_run.py --execute-frozen-h1 --approval-manifest <外部批准文件> --output-dir <新目录>。本轮不执行此命令。

## 顺序与判据

按G0/G1/G2来源、合成差分与计划关口核验，再各执行一条KEEP/SWITCH。两者共用一个Budget，每条分支有独立缓存、观测、MODEL反馈与belief。独立审计必须接收原Branch和事先注册的外部上下文；每条result经唯一类型边界进入verify/service/audit。完整历史覆盖、终止处理tick、ACTUAL前缀身份与MODEL身份不能只凭摘要判定。

G4只能在G3成立后接受：J=completion+flow+late+effort+terminal-change_cost；ΔJ=各分量配对差之和-改派费配对差。按独立逐帧及事件会计、Fraction精确二进制核算与原浮点累计残差分开报告。继承的D60前沉没费用不重复进入增量；自然释放不另收费，终端惩罚仅D120结算。任何控制、位移、belief、服务、生命周期或会计差异均不能静默放宽。

G5复核每条前后计数与整组总计，分开MODEL观测、MODEL策略评价、ACTUAL=0；记录实际CPU、外部墙钟、缓存与融合次数。全部原Gate证据齐全、独立核验通过后才可提出D1_A_MODEL_PAIR_VALIDATED。当前六Gate的新H1运行一律NOT_RUN。

失败不重试、不换H1、不换计划、不增加预算。保留RAW/PARTIAL、异常栈、分支和审计阶段、NOT_RUN检查及已经花费的成本，不发布有效新收益差额。完成复验后仍需独立科研审查。
''',encoding='utf-8')
(root/'RESOURCE_AND_STOP_RULES.md').write_text('''# 资源及停止

整组上限为观测WLS1000、策略WLS4000、合计5000、ACTUAL0，CPU600秒、墙钟900秒；严禁分支重置。主驱动在来源重放前创建同一个Budget，并在来源/分支/审计后检查；原Budget的估计器调用守卫不变。未来需另由可信外层记录完整进程CPU和墙钟（包括初始化、证据写入），并实施900秒外部进程超时；协作式Budget.check不能证明卡住的底层调用能被异步打断。未来尚未实际运行外部超时，本轮不冒称已经验收。

准备测试资源见每次 ZERO_WLS_STEP_PROOF_*，其测量覆盖守护测试区间，含子进程等待墙钟，父进程CPU不含子进程CPU；不是未来H1的算法耗时。遗留缺失CPU不得填0。失败证据与全部历史成本保留，不重跑旧主实验。
''',encoding='utf-8')
accept=dict(status='D1_A_H1_REVALIDATION_PREP_READY_FOR_REVIEW',D1_A_status='D1_A_BLOCKED',type_contract='INTERFACE_TYPE_CONTRACT_PASS',entry='H1_ENTRY_FAIL_CLOSED_PASS',orchestration='STUB_ORCHESTRATION_PASS',pure_state='REAL_PURE_STATE_INTERFACE_PASS',full_regression='26/26',final_affected='8/8',new_H1_runs=0,new_WLS=0,new_MODEL_advance=0,new_ACTUAL_STEP=0,actual_full_physical_economic_validation='NOT_RUN',independent_review_pending=True)
save('ACCEPTANCE.json',accept)
(root/'REPORT.md').write_text('''# H1复验准备收尾报告

结论：D1_A_H1_REVALIDATION_PREP_READY_FOR_REVIEW。D1-A仍为D1_A_BLOCKED。

基准 c7fd250c78eeae2a0bd430f211c13e25c607fc67，main，初始工作树干净；不进行远端同步或声称已核验GitHub当前状态。新增只读类型适配器与测试，修改主驱动和verify的一行motion访问；冻结MODEL内核、G3核心、科学公式与历史归档未改。

统一类型边界把world.motion规范化为整数ID的隔离副本，拒绝混合重复、非法、未知、缺失ID；原world、数值、world_digest和文件不变。主脚本默认拒绝，导入与help不运行，授权及新目录检查在写入和Branch创建前完成。未来有效批准记录本轮没有创建。

26组全回归通过，最终8组受影响测试通过。真实纯状态KEEP/SWITCH分别调用原Branch构造器、合法事务和真实独立审计器，错误/缺失外部上下文及前缀篡改均拒绝；融合由确定性替身提供。Stub编排验证原对象、外部上下文、共享Budget及每个必要审计失败传播，不把Stub PASS当作物理PASS。第一次测试模块名错误及修正日志完整保留。

七个可执行哨兵覆盖估计器、融合入口、ACTUAL step、真实Branch.run/advance，计数全0。CLI子进程只执行未授权/帮助路径，未创建正式复验目录。未重跑H1，未签发新的收益差额；原3765次MODEL WLS及三组旧结果原样保留。

原H1身份与原计划逐字段比对成立；D80/D100 R策略和共享1000/4000/5000、CPU600秒/墙钟900秒限制不变。本轮只核验接线。未来真实联合运行的完整D60—D120历史、观测缓存、belief、控制/服务、生命周期、独立经济核算及实际成本仍全部待新授权复验。还需实际部署外部进程计时/超时，固定未来执行版本与批准记录，不得把准备工作树直接当作已授权版本。

完整协议见 H1_REVALIDATION_PROTOCOL.md、GATE_ACCEPTANCE_MATRIX.json；来源、保护、测试、成本、修改和原档不变性见同目录JSON与日志。已停止，不启动复验、D1-B/C/D、DEV/TEST，也未提交或推送。
''',encoding='utf-8')
files=set(baseline['tracked_sha256'])|{'research/non_oracle/stfbs_d1a_audit_input.py','tests/test_stfbs_d1a_h1_revalidation_prep.py'}
save('SOURCE_PINS.json',{p:sha(p) for p in sorted(files)})
(root/'REPAIR.diff').write_bytes(subprocess.check_output(['git','diff','--','scripts/stfbs_d1a_run.py','research/non_oracle/stfbs_d1a_verify.py']))
save('SHA256.json',{p.name:sha(p) for p in sorted(root.iterdir()) if p.is_file() and p.name!='SHA256.json'})
print(json.dumps(accept,ensure_ascii=False));print('Historical archived files unchanged:',len(old))
