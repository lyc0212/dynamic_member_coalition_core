"""Design documents only. Standard-library AST/JSON/text/hash reads; no science imports."""
import ast,json,hashlib,subprocess,sys
from pathlib import Path
R=Path.cwd();O=Path(__file__).resolve().parent
HEAD='cf730a41e2681efdf8880bc6b142b6deb347ac0d'
REF='c75f364bf32e6fc63be6a7080d4f21bc6d75ec55'
EXE='fa42557fd4ee453a27b38ab3644000830246ac42'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def save(n,v):
    with (O/n).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def doc(n,t):
    with (O/n).open('x',encoding='utf-8') as f:f.write(t)
assert git('rev-parse','HEAD')==HEAD
assert not git('diff','--name-only',REF,'HEAD','--','research','pursuit_v2','scripts','configs','tests')
protected={**read('reports/stfbs_lite_d1a_h1_revalidation_001/SHA256.json'),**read('reports/stfbs_lite_d1a_final_closeout_001/ADDITIONAL_SHA256.json'),**read('reports/stfbs_lite_d1a_h1_authorization_001/APPROVAL.json')['source_pins']}
assert all(sha(R/p)==s for p,s in protected.items())
decision=read('reports/stfbs_lite_d1a_final_closeout_001/FINAL_RESEARCH_DECISION.json')
assert decision['accepted_limited_conclusion']=='D1_A_MODEL_PAIR_VALIDATED'
old_boundary=read('reports/stfbs_lite_d1a_h1_revalidation_001/RAW_MEASUREMENT_AUDIT.json')
locations={}
def loc(p,s):
    if p not in locations:
        tree=ast.parse((R/p).read_text(encoding='utf-8-sig'));found={}
        def walk(nodes,prefix=''):
            for n in nodes:
                if isinstance(n,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                    k=prefix+n.name;found[k]=n;walk(n.body,k+'.')
        walk(tree.body);locations[p]=found
    n=locations[p][s]
    return dict(path=p,symbol=s,line_start=n.lineno,line_end=n.end_lineno,commit=HEAD,sha256=sha(R/p))
Q='research/information_service/public_quality.py';E='research/information_service_online/execution.py'
P='research/information_service_online/public.py';M='research/non_oracle/stfbs_d1a_model.py'
S='research/non_oracle/stfbs_d1a_state.py';H='research/non_oracle/stfbs_d1a_history.py'
T='tests/test_stfbs_d1a_state.py';TH='tests/test_stfbs_d1a_history_repair.py'
FORMAL='VERIFIED_BY_FORMAL_H1_OR_INDEPENDENT_AUDIT';UNIT='SUPPORTED_BY_HISTORICAL_UNIT_OR_NEGATIVE_TEST';FUTURE='REQUIRES_D1B_END_TO_END_VALIDATION'
rows=[]
def evidence(name,src,grade,verified,pending,tests=(),refs=()):
    rows.append(dict(mechanism=name,source_evidence=[loc(*x) for x in src],grade=grade,verified_scope=verified,unverified_scope=pending,test_locations=[loc(*x) for x in tests],evidence_refs=list(refs)))
evidence('Q三态/严格半径',[(Q,'assess_quality'),(Q,'classify_radius'),(Q,'FrameProcessor.process'),('research/information_service_bridge/public_stream.py','BridgeFrameProcessor.process')],FORMAL,'原H1固定sigma真实WLS/quality/服务审计；源码有严格三态与前置守卫。','动态sigma导致FAIL及其反事实没有实验结果。',refs=['reports/stfbs_lite_d1a_h1_revalidation_001/ALL_AUDITS.json'])
evidence('WLS权重和诊断',[('research/cooperative_sensing/estimator.py','values'),('research/cooperative_sensing/estimator.py','estimate'),('research/cooperative_sensing/estimator.py','condition')],FORMAL,'五字段公开输入，残差及Jacobian按sigma加权；原H1真实调用。','单成员sigma动态退化的三态响应未实测。',refs=['reports/stfbs_lite_d1a_h1_revalidation_001/READ_ONLY_INDEPENDENT_REVIEW_002.json'])
evidence('ACTUAL动态声明参考',[(E,'OnlineEnvironment.__init__'),(E,'OnlineEnvironment._profiles'),(E,'OnlineEnvironment._sample'),(E,'ActualMeasurementCache.query')],FUTURE,'源码支持effective_tick有序声明、正有限sigma及available/missing；按tick取最后声明。','不等于D1A MODEL已有动态profile或延迟公告。')
evidence('实际物理与公开边界',[(E,'OnlineEnvironment._checkpoint'),(E,'OnlineEnvironment._advance_tick'),(E,'OnlineEnvironment._control_command'),('research/non_oracle/environment.py','NonOracleEnvironment.prepare_decision'),('research/non_oracle/environment.py','NonOracleEnvironment._control_command')],FUTURE,'基类控制为Oracle，checkpoint含真状态；NonOracle层专门清洗并用冻结belief控制。','不得直接把ACTUAL控制/checkpoint及ACTUAL-only enqueue用于MODEL。')
evidence('D1A固定profile和MODEL接线',[(M,'Branch.__init__'),(M,'Branch.raw'),(M,'Branch.fuse'),(M,'Branch.advance'),(M,'Branch.policy_view'),(M,'Branch.assign'),(M,'Branch.run')],FORMAL,'D1A限定固定profile、联合物理与审计链已接受；profiles构造时固定，view沿用初始声明。','D1B实际/公开profile接口与预设动作驱动需新适配。',refs=['reports/stfbs_lite_d1a_final_closeout_001/FINAL_RESEARCH_DECISION.json'])
evidence('缓存身份/上下文',[(S,'ModelRawCache.__init__'),(S,'ModelRawCache.query'),(M,'Branch.raw')],UNIT,'同键复用、位置/sigma/health冲突、分支与slot摘要拒绝有历史单位证据。','真实服务段/流切换、VALID继承、pending/融合状态隔离未专项整体通过。',tests=[(T,'StateTests.test_raw_identity_matrix'),(T,'StateTests.test_inherited_slots')],refs=['reports/stfbs_lite_d1a_001/STATE_TESTS_FIRST.log','reports/stfbs_lite_d1a_h1_revalidation_001/RAW_MEASUREMENT_AUDIT.json'])
evidence('belief来源与时序',[(S,'ModelBeliefConsumer.__init__'),(S,'ModelBeliefConsumer.enqueue'),('research/non_oracle/belief.py','Beliefs.freeze')],FORMAL,'原H1 D80/D100独立重放及历史差分；冻结后新增同tick观测延后消费。','动态profile/notice账本与新场景须再验证。',tests=[(T,'StateTests.test_model_belief_differential')],refs=['reports/stfbs_lite_d1a_h1_revalidation_001/KEEP_AUDITS.json'])
evidence('换员/历史/时钟/费用',[(P,'_validate_actions'),(P,'plan_action_metadata'),(H,'prepare_assignment'),('pursuit_v2/service.py','advance_clock'),(E,'apply_assignment_boundary')],UNIT,'MEMBER_CHANGE映射TEAM_CHANGED、完整团队变化清零、逐机器人计费、隔离事务。','动态Q+新成员真实运动+真实融合的组合未验收。',tests=[(TH,'HistoryRepairTests.test_member_role_and_cut_boundaries'),(TH,'HistoryRepairTests.test_atomic_validation_and_prepare_failures')],refs=['reports/stfbs_lite_d1a_g3_history_repair_001/FINAL_IDENTITY_GUARDED_TESTS.log'])
evidence('独立审计复用',[('research/non_oracle/stfbs_d1a_history_audit.py','audit_branch_independent'),('research/non_oracle/stfbs_d1a_verify.py','verify'),('research/non_oracle/stfbs_d1a_audit.py','audit'),('research/non_oracle/stfbs_d1a_audit.py','service_audit')],FORMAL,'原H1原Branch、控制、服务、belief与经济已独立验收。','D1B需新增声明时序、同几何Q和四时间核验，不能搬旧PASS。',refs=['reports/stfbs_lite_d1a_h1_revalidation_001/READ_ONLY_INDEPENDENT_REVIEW_002.json'])
save('CODE_EVIDENCE.json',rows)
maptext='# 源码地图与证据分级\n\n当前 '+HEAD+'；科学参考 '+REF+'；原H1执行 '+EXE+'。\n\n'
for row in rows:
    maptext+='## '+row['mechanism']+'\n\n'+row['grade']+'\n\n'
    for s in row['source_evidence']+row['test_locations']:
        maptext+='- '+s['path']+':'+s['symbol']+':'+str(s['line_start'])+'–'+str(s['line_end'])+'（提交'+HEAD+'）\n'
    maptext+='\n已确认：'+row['verified_scope']+'\n\n未验证：'+row['unverified_scope']+'\n\n'
maptext+='''## 三条链路（不可混用）

ACTUAL参考：OnlineEnvironment._advance_tick → _control_command → _fuse/_sample/_profiles → ActualMeasurementCache.query → measurements.assemble_left_state → sense_callback/WLS/quality → advance_clock → _checkpoint。基类为Oracle；NonOracleEnvironment才将控制改为公开belief，并清洗策略view。本轮不执行这条链。

已验收D1A MODEL：Branch.run → assign/prepare_assignment → fuse/raw → ModelRawCache.query → BridgeFrameProcessor.process → estimator.estimate/assess_quality → ModelBeliefConsumer.enqueue；advance按冻结belief控制并结算服务/经济；policy_view冻结80/100；原run调用R。

拟议D1B（未实现）：合法新MODEL fixture → D1B raw按当前物理profile采样 → 复用真实fuse/WLS/quality/advance → 当前public profile的view投影 → FixedQMController预设B0/B1动作 → 原事务/时钟/经济 → 原审计及动态Q专项。
MODEL条件位置可用于采样和G，不可用作Oracle控制belief。私有schedule不能经公开view/closure泄漏。没有可直接宣称动态Q端到端已经通过的历史证据。
'''
doc('CODE_DEPENDENCY_MAP.md',maptext)
doc('DYNAMIC_SENSOR_CONTRACT.md','''# 动态传感器契约（设计，未实现）

sigma是bearing不确定性声明，改变WLS残差/Jacobian权重及JᵀJ半径代理，不改变首轮真实bearing扰动（恒零，无RNG）。单个sigma增大不保证FAIL，不是统计噪声鲁棒性研究。主因子只有U1 sigma，health仍available；U0/U2始终normal。B3 missing是单独UNKNOWN负例。

assess_quality先验证输入、接受估计、代表点、诊断和信息矩阵：测量不足、无接受估计、代表点不可评价、病态/歧义/边界等可为UNKNOWN；数值契约违规可抛错并必须停止。仅可评价时classify_radius严格r≤0.06 PASS/r>0.06 FAIL，p_ref=0.95，不加容差。不将missing改写为FAIL，也不将数值异常吞成UNKNOWN。
FAIL和UNKNOWN均禁止有效服务区间，有既存进度才产生原时钟reset事件；无进度仍记录invalid interval。Q FAIL仍可能有可接受位置估计，belief不能新增Q=PASS接受门槛。

## 实际、公开、决策三个时间

首版k_effective=80、k_public=80、k_decision=80，分别保存tick和秒(k×0.05)。一般未提前公告时effective≤public≤decision，decision为下一合法20tick切口。公开事件不触发额外中途belief冻结。
环境独立持有PrivateSensorSchedule（有序tick/声明/事件id/摘要），不放入A2_POLICY_INPUT、Config、seed、候选输入或可供策略读取的闭包。公开侧持有到期notice与当前profile快照，含observed_tick/版本，但不含未来行。
physical_profile_at(measurement_tick)供采样，public_profile_at(cut)供view；首版值一致而接口/身份分离。原D1A固定profiles不能直接宣称已支持。版本id放独立审计账本，通过slot/frame/endpoint关联；不修改冻结schema和摘要，不把sigma/version塞入raw key规避冲突。

## tick80唯一顺序

1. 区间开始保留belief60、旧Assignment和左79；登记effective80（只影响80及以后采样）。
2. 按旧团队及冻结belief移动79→80，遵守原速度；右80在到达位置上使用新sigma采样、融合，MODEL反馈入pending。
3. 原左79/右80结算(79,80]；G合法/Q FAIL则清零。完成/逃逸及自然释放按原优先级。
4. public80 notice在view冻结前合法发布；期间没有策略回调。消费本次冻结前已到达观测，冻结belief80并投影当前公开profiles，只冻结一次。
5. B0 KEEP，B1完整换员事务；新左80在freeze80之后生成，反馈留到100，不得倒灌冻结belief80。到100若同measurement tick重复，遵原非递增时间拒绝，不更改数学消费器。
6. (80,81]才按新团队相邻双端点结算；D100更新belief后KEEP当前团队，不做自主搜索。

若质量事件在非决策tick，采样/公开均按该tick，策略到下一合法cut才利用；不为方便改变20tick决策周期。

## 延迟公开不在首版

原_profiles同时供采样、checkpoint；packet.sigma、slot摘要、Q半径/诊断及belief都可能提前泄漏。只隐藏profile列表不够。未来public>effective须另定原包/质量/历史/缓存可见性及消息available_tick，不能改packet.sigma伪装旧声明。本轮不建延迟系统，也不宣称支持。
''')
doc('Q_ONLY_FAILURE_PROTOCOL.md','''# 有限Q-only FAIL协议（未来执行，本轮零WLS）

## 独立新MODEL场景而非修改D1A

拟议单T0、q2、三机器人；birth tick60，prior p0=(9,10)、CV=(0.40,0)，weight=1，service_duration=1.05，软deadline=5秒，episode H=120(6秒)。Config robots=3/task_count=1，其他G/Q、控制和成本公式不变，kappa=0.01。
U0/U1初始位置为p0加原dual_neg45/dual_pos45偏移；U2为p0+正角色偏移+(0.70,0)的预登记待命位置。位置仅是新场景设计，不生成物理数据；不预言修复成功，不在换员时传送U2。
新fixture必须合法构造PUBLIC_PRIOR种子、MODEL出生/未分配历史、外部上下文；D60真实MODEL首次分配/融合后，旧团队进度从0开始。不能篡改旧ACTUAL D60坐标、任务或来源标签来冒充合法checkpoint。合法fixture builder是首轮实现依赖。
原H1 T0时长2.25秒，D80重置到D120仅2秒，且原U2在(2,2)。不得机械沿用它并假定可完成；D1B独立任务/场景差异必须明确登记，不回改原验收。

## 同几何探针与有限参数

未来先用normal profiles形成一个合法MODEL参考前缀60→80，保留每端点和服务；观察截断80不收episode终止罚。它只做场景准入，不当成B0结果，不把高保真反馈共享给B0/B1。
冻结同一tick80目标条件位置、U0/U1位置、角色、几何、测量方向/零扰动、其他传感器、算法及阈值。若目标已终止、G不合法或OLD原WLS/Q不是PASS，SCENARIO_ADMISSION_FAILED并停止，不移动几何/改时刻寻找成功。
OLD独立QM_PROBE_OLD；DEGRADED独立QM_PROBE_DEGRADED_i。U1 sigma按[2,4,8,16]×0.02，即[0.04,0.08,0.16,0.32]严格升序；最多1个OLD加4个DEGRADED。每项独立生成packet/cache并真实WLS/assess_quality，只改sigma；不能复制旧packet后改字段，不能同branch/key覆盖上下文。
选择第一个两侧G PASS、OLD Q PASS、DEGRADED Q FAIL的因子；不读B0/B1净收益或恢复结果。PASS为退化不足；UNKNOWN单列并按原固定列表继续；契约/未知异常立即BLOCKED，不能宽泛except后跳过。耗尽记NO_Q_ONLY_FAIL_FOUND，不加候选、不调阈值/容差。

## 与动态执行区别

探针是同几何下两种外生条件，不是同一物理历史重复测量。实际场景不同tick用不同sigma，原始key也不同；sigma80必须在tick80第一次采样前确定。
选定因子后固定版本、身份、schedule与时序，再分别独立运行B0/B1。两者到80的几何应逐字段与探针一致（60→79声明相同，控制到80仍用冻结belief60）；原端点Q必须由真实计算确认。若动态80未实现G PASS/Q FAIL，记DYNAMIC_Q_ONLY_NOT_REALIZED，不重调参数、时刻或初态，不发布修复成功比较。
当前没有sigma候选计算、质量半径或Q-only FAIL实验结果。即使未来找不到明确FAIL，也允许完整记录为场景构造未成功，不等于方法被证明有效或无效。
''')
doc('MEMBER_CHANGE_SERVICE_CONTRACT.md','''# 合法预设换员与服务/经济

U0保留T0/dual_neg45，U1由T0/dual_pos45退出空闲，U2由空闲加入T0/dual_pos45；目标不变、团队2、角色完整、资源唯一。是实验动作，不是自主搜索。
public.plan_action_metadata区分MEMBER_CHANGE/ROLE_CHANGE；prepare_assignment映射TEAM_CHANGED，旧段关闭、新段建立、clock归零、端点和事件引用完整。D1A开段标签可能为REASSIGNMENT，不能改旧schema迎合名字；独立D1B账本另记action_kind即可。
原Branch.assign验证→隔离准备→统一提交；动态schedule/notice在准备前按tick确定，不能因事务回调随机变化，失败不得留下局部费用、缓存、pending或历史。

先按旧团队结算(79,80]，右80用已生效的新sigma。freeze80后才换员；旧进度若已因Q失效清零，不另加进度损失罚。新段初始clock=(0,0)，新左80不产生服务进度；(80,81]以后必须同段相邻G/Q均PASS才累积，UNKNOWN也invalid。
U2始终从原位置按公开belief控制移动，不能瞬移或按MODEL条件真值Oracle跟踪；合法Assignment不保证立即G合法或时域内可恢复。旧/新80两次融合可以不同，但保留U0的同tick原始slot应复用，U2只生成一次；真实流/段切换专项必须在未来验证。

## 四时间

t_change为换员事务成功commit；t_GQ为新段首个G真/Q PASS实际端点；t_resume为新段首个完整有效区间的右端点；t_complete来自真实完成事件when和processed_tick。保存tick、秒、分支/任务/段/端点/区间引用。
t_GQ可为80但t_resume最早81；孤立GQ PASS不保证连续恢复。未发生用null和NOT_OBSERVED_BY_H/ACTIVE_AT_H/REJECTED等原因，不把未完成叫永久失败；不能用ceil(when/DT)替代原处理切口。

## 经济

完整Assignment逐机器人变化：U0不变、U1退出和U2加入各1，共2*kappa；kappa=0.01时为0.02。若实际还换角色则按真实条目计，不硬填2。自然完成/逃逸释放额外费用0，后续主动变化分别结算，不能重复收费。
J=completion+flow+late+effort+terminal−change_cost；按原公式并使用新场景task_count=1正确归一化，不偷用D1A两任务分母。不重复D60前沉没费用，未服务任务若存在仍演化并计成本；deadline软约束，终止罚只在真实H120，不在probe80观察截止收取。
独立验证从帧/控制/服务/事件重算费用和各收益分量，做Fraction精确二进制及浮点残差配对，不用主程序PASS代替核算。净收益正/零/负均可接受机制结论。
首轮B0/B1在80/100只更新公开belief并采取预设KEEP/换员；不调用R求最优，不比较自主动作。D1-C另行授权。
''')
future=[
dict(id='F1',name='test_same_tick_member_change_real_fusion_reuses_retained_raw',necessary=True,
    existing='ModelRawCache同键复用；历史stream循环仅标签，事务fixture使用fake_fuse。',unverified='旧团队右80→新团队左80真实融合的端到端复用',
    source=[loc(S,'ModelRawCache.query'),loc(M,'Branch.fuse'),loc(H,'prepare_assignment')],tests=[loc(T,'StateTests.test_raw_identity_matrix'),loc(TH,'HistoryRepairTests.test_member_role_and_cut_boundaries')],
    PASS='同B1旧U0/U1右80、新U0/U2左80各合法融合；U0 producer仍1次、U2仅1次新采样，原slot不变，流/段独立。',FAIL='重采样、通过角色/流改raw key、非法复制WLS结果、部分提交。'),
dict(id='F2',name='test_valid_historical_slot_readonly_MODEL_inheritance',necessary=True,
    existing='MISSING继承fixture禁止producer；构造器检查历史slot身份。',unverified='VALID完整包/身份/来源与冲突的端到端组合',
    source=[loc(M,'Branch.__init__'),loc(S,'ModelRawCache.query')],tests=[loc(T,'StateTests.test_inherited_slots')],
    PASS='独立合法历史引用测试中VALID packet、digest、target/robot/tick、sigma/position不变，producer不调用；各上下文冲突拒绝，过去ACTUAL不改标新MODEL原始样本。',FAIL='改packet、重采样、忽略冲突、伪造ACTUAL checkpoint/endpoint。'),
dict(id='F3',name='test_cache_pending_fusion_state_cross_branch_isolation',necessary=True,
    existing='缓存层branch/摘要拒绝，不代表全部pending/融合风险已验证。',unverified='cache/packet/pending/estimate/stream逐项污染与错误流拒绝',
    source=[loc(S,'ModelRawCache.query'),loc(S,'ModelBeliefConsumer.enqueue'),loc('research/information_service_bridge/public_stream.py','BridgeFrameProcessor.process')],tests=[loc(T,'StateTests.test_raw_identity_matrix'),loc('tests/test_stfbs_d1a_audit_hardening.py','HardeningTests.test_separate_record_identity')],
    PASS='B0/B1独立可信上下文，无可变别名；修改一侧不影响另一侧；错误branch/target/stream/packet在消费/WLS前拒绝。',FAIL='跨分支污染、缺少上下文却通过、错误流或包被接受。')]
save('EVIDENCE_BOUNDARY_TRANSFER.json',future)
txt='# D1A三项证据限制传递\n\n既有D1A限定验收保持，不重开修复。本轮仅设计未来必要测试。\n\n'
for f in future:
    txt+='## '+f['id']+' / '+f['name']+'\n\n已有：'+f['existing']+'\n\n未验证：'+f['unverified']+'\n\nPASS：'+f['PASS']+'\n\nFAIL：'+f['FAIL']+'\n\n首轮必需：是；未来结果NOT_RUN。源码/测试精确位置见EVIDENCE_BOUNDARY_TRANSFER.json。\n\n'
txt+='''## 最小七项拟议用例（不是已存在或已通过函数）

1. F1真实新旧流同tick融合及保留成员raw复用；2. 同key改变sigma拒绝且正式状态不变；3. F2 VALID继承；4. VALID上下文冲突；5. F3 cache/pending/融合逐项隔离；6. 错误branch/target/stream/packet身份；7. 动态声明79/80、旧区间、冻结、换员及81新服务区间的联合时钟/费用。
每项先有合法正例再单因素篡改，核对具体拒绝原因；无文件、未启动、无上下文等无关失败不能冒充通过。历史VALID引用作为单独合法测试上下文，不移植到新主场景伪造ACTUAL前缀。优先复用ModelRawCache，不新建复杂缓存架构。
'''
doc('D1A_EVIDENCE_BOUNDARY_TRANSFER.md',txt)
common=dict(identity='D1B_QM_MODEL_V1_DESIGN_ONLY',start_tick=60,end_tick=120,model='single T0 q2; 3 robots; public-prior CV; zero angle perturbation',
    T0=dict(birth_tick=60,public_prior=[9.,10.],velocity=[.4,0.],weight=1.,service_duration=1.05,soft_deadline_seconds=5.),
    initial_state='new legal MODEL birth/unassigned/public-prior fixture; first U0/U1 assignment and left fusion60; no modified old ACTUAL checkpoint',
    positions='U0/U1=p0+original role offsets; U2=p0+positive-role offset+(0.70,0); design formulas only',normal_sigma=.02,health='available',effective_tick=80,public_tick=80,decision_ticks=[80,100],
    candidate_factors=[2,4,8,16],selection='first explicit qualified FAIL only; no value-dependent selection',economics='original formulas; robots3/task_count1; kappa0.01',control='public frozen belief only; original physics/velocity bound',
    action_rule='B0 keep; B1 preset80 swap then keep; D100 only belief update and current-team keep; no R optimization',isolation='independent branch/cache/pending/streams; no private schedule in policy view')
outputs=['source/runtime/scenario pins','effective/public notice ledger','raw key/context/packet and cache/producers','WLS payload/result/Q/diagnostics/stream identity','all G/Q endpoints and interval/reset records','positions/control/elapsed/effort','complete assignments/segments/events/terminal histories','public views/seed/pending/consumption','four recovery times with null/reasons','component/Fraction cost audit','WLS/CPU/wall/stop receipts and first failure']
cases={
'B0':dict(kind='KEEP MODEL branch',common=common,action80='keep U0/U1 T0',purpose='dynamic Q loss, service interruption and costs',raw_outputs=outputs,PASS='correct independent physical/service/accounting verification; no recovery required',FAIL='identity/leak/quality/physics/history/accounting inconsistency'),
'B1':dict(kind='preset MEMBER_CHANGE MODEL branch',common=common,action80='U0 stays negative role; U1 idle; U2 joins positive role T0',raw_outputs=outputs,PASS='legal reset/continuous motion, measured recovery or explicit nonrecovery, valid complete account; no J gain requirement',FAIL='teleport/invalid allocation, old interval overwritten, false times, leaked future or corrupted state'),
'B2':dict(kind='public-admission negative only; zero MODEL physics',fixture='independently declared two-robot/q2 public state, U0/U1 serving T0, no third distinct candidate',purpose='reject fictitious replacement before sampling/fees/history/advance',
    reason='3 robots cannot simultaneously support disjoint T0 q2 plus another complete q2 occupying R2. Missing health or far G alone is not original Assignment illegality.',
    PASS='no valid different substitute; reject with unchanged state and zero sampling/charge',FAIL='invent R2, duplicate/out-of-range member or run 3-hardcoded Branch as 2-robot simulator',
    raw_outputs=['trusted public candidate universe and state','rejection reason','before/after states and zero-call ledger'],future_dependency='If physical B2 is required, separately define a genuinely supported resource-unavailable scenario; not silently broaden first batch.'),
'B3':dict(kind='UNKNOWN MODEL negative',common_base=common,controlled_difference='U1 health=missing at80; keep old team; separate from main sigma-only causal comparison',raw_outputs=outputs,
    PASS='original insufficient-measurements UNKNOWN recorded; invalid service handled, no relabel to FAIL',FAIL='fake FAIL, swallowed numerical error or false service/completion')}
save('MINIMAL_EXPERIMENT_MATRIX.json',dict(status='DESIGN_ONLY_NOT_RUN',common=common,cases=cases,future_tests=future,
    construction_failures=['OLD not PASS','G not PASS','T0 ended before80','NO_Q_ONLY_FAIL_FOUND','DYNAMIC_Q_ONLY_NOT_REALIZED'],
    stop_on=['scientific/source mismatch','unregistered/numeric exception','information leak','invalid raw/stream/assignment','service/physics/accounting inconsistency','finite budget overrun'],
    proposed_budget_estimate=dict(scope='one future finite batch; estimates only, not measured/deployed',normal_prefix_WLS_upper=21,OLD_plus_four_probes=5,B0_upper=61,B1_upper=62,B2=0,B3_upper=61,seven_special_tests_estimate=28,total_MODEL_WLS_estimate=238,MODEL_POLICY_WLS=0,ACTUAL_WLS=0,CPU_wall='not measured; actual limits/execution version require future authorization')))
doc('MINIMAL_IMPLEMENTATION_SCOPE.md','''# 下一阶段最小实现范围（仅规划，未授权）

独立新建D1B场景/合法fixture builder、MODEL动态profile薄适配、固定实验动作controller、动态声明/Q/四时间独立审计，以及单一入口/专项测试。拟议模块名可为stfbs_d1b_qm_scenario/model/audit，不代表已存在。
1. 新fixture提供合法prior seed、MODEL出生/未分配历史和独立上下文，不改旧ACTUAL checkpoint。
2. raw覆盖读physical_profile_at(tick)，复用原cache/fuse；sigma不是key。公开view按已到期notice替换profile，不沿用D1A构造时固定声明。
3. 新controller保留80/100合法belief冻结，但80预设KEEP/换员、100 KEEP，不调用D1A run的R自动选择，不伪造R的choice/exact_value。
4. 优先复用冻结advance/服务/控制/费用、原assign事务、消费者和独立审计；用独立诊断账本补充profile版本、FAIL/UNKNOWN原因和四时间，不改原schema/数学。
5. schedule/notice在深拷贝事务中不丢失或共享；不进入策略view。控制只读公开belief，MODEL条件真值仅作采样与G。
6. 新主场景3机器人；B2只做2机器人公共准入负例，不扩展原3固定数组MODEL为通用模拟器。

先合法fixture与七项专项，再有限探针准入并固定参数/版本，后B0/B1/B3真实MODEL；B2准入负例独立记录。真实RAW/私有schedule与完整历史独立审计，别拿历史PASS代替。未恢复/未完成/净差非正均允许，找不到明确Q-only FAIL可科学收尾为构造失败，不能调规则。
设计估算至多238次MODEL WLS不是实耗；若下一实现的测试路径超出当前估算，必须在首次执行前明确固定预算，不运行后放宽。CPU/墙钟未测，复用现有watchdog机制，不新建平台；每次真实运行仍需单独授权。

禁止修改D1A源码/归档、WLS/Q/service/control/economic公式；不调用ACTUAL OnlineEnvironment模拟MODEL，不加入自主换员搜索、多动作价值排序、D1-C、连续转向、随机噪声或新缓存框架。若原内核无适配缝，停下报告最小D1B专用方案，不修改冻结实现。
''')
contracts={
'QM-G0':('版本/场景身份', ['D1A已接受且保护','独立单T0/q2/三机器人合法MODEL fixture','起始60、退化80、终点120与原团队/候选明确'],'新fixture/seed/历史构造器尚未实现，必须合法而非字段拼接。'),
'QM-G1':('Q三态与有限sigma', ['原WLS/quality阈值不改','same-geometry独立OLD/DEGRADED','有限升序首个明确FAIL','UNKNOWN和数值异常不混淆'],'真实Q-only FAIL未求得，本轮不要求求得。'),
'QM-G2':('时间/信息/缓存', ['effective/public/decision身份分开','旧区间先、新端点后','新左80观测不倒灌freeze80','未来schedule不进策略','不同反事实独立key空间'],'须实现物理profile/公开notice双接口；首版不支持延迟公告。'),
'QM-G3':('合法预设换员', ['U0保留、U1退出、U2加入同目标','q2角色完整资源唯一','TEAM_CHANGED/原子事务','真实移动无瞬移'],'动态profile/真实融合/新成员移动组合及准入B2尚未执行。'),
'QM-G4':('服务/四时间/经济', ['旧79→80结算','新段clock0、新左80不加进度','新80→81双端点','四时间null语义','两实际条目变化计费、释放免费、完整经济'],'实际GQ/恢复/完成及J必须以后测量，不保证正收益。'),
'QM-G5':('最小矩阵和独立证据', ['B0/B1相同外生/独立内部状态','B2明确仅公共准入','B3 UNKNOWN独立负例','F1/F2/F3七项专项','原始证据/独立审计/失败停止'],'后续实现/测试/资源预算必须单独授权；无任何本轮PHYSICAL_PASS。')}
matrix={}
for g,(title,terms,dep) in contracts.items():
    matrix[g]=dict(status='DESIGN_PASS_WITH_DEPENDENCIES',design_contract=dict(title=title,assertions=terms),source_evidence=rows,existing_test_evidence='CODE_EVIDENCE.json and EVIDENCE_BOUNDARY_TRANSFER.json; historical results only',future_validation_required=['legal fixture admission','applicable Q/assignment/timing end-to-end tests','independent new MODEL raw/physics/service/economics/resource audit'],open_dependencies=[dep],blocking_issue=None,physical_status='NOT_RUN')
save('QM_GATE_ACCEPTANCE_MATRIX.json',matrix)
save('ACCEPTANCE.json',dict(task='D1-B-QM-0 V1.2',status='D1_B_QM_0_DESIGN_READY_WITH_DEPENDENCIES',current_HEAD=HEAD,science_reference_HEAD=REF,formal_execution_HEAD=EXE,D1A_preserved='D1_A_MODEL_PAIR_VALIDATED',QM_Gates={g:v['status'] for g,v in matrix.items()},direct_scientific_contract_blocker=None,dependencies=[v[2] for v in contracts.values()],actual_Q_only_FAIL='NOT_RUN',actual_MEMBER_CHANGE='NOT_RUN',physical_status='NOT_RUN',WLS=0,MODEL_advance=0,ACTUAL_STEP=0,tests_run=0,new_scenarios_generated=False,scientific_code_modified=False,next_stage_authorized=False))
doc('REPORT.md','''# D1-B-QM-0 V1.2 中文设计审查

## 裁定

D1_B_QM_0_DESIGN_READY_WITH_DEPENDENCIES。QM-G0～QM-G5契约已明确，没有发现必须改变Q/WLS/服务/经济公式才能成立的直接科学冲突；合法新MODEL fixture、动态声明薄适配、真实缓存/融合组合验证是后续直接依赖，不是本轮已经完成的实现或物理PASS。
当前cf730a41e2681efdf8880bc6b142b6deb347ac0d，科学参考c75f364bf32e6fc63be6a7080d4f21bc6d75ec55，原H1实际执行fa42557fd4ee453a27b38ab3644000830246ac42。初始工作树干净，科学目录/测试/配置相对参考无变化，原H1/追加清单及45源码核对不变。D1-A限定验收及其H1相关阻断解除保持；不重开G3或H1。

## 18项审查答案

1. D1-A已由用户认可，FINAL_RESEARCH_DECISION接受D1_A_MODEL_PAIR_VALIDATED；三种版本身份和旧档保持，不把报告HEAD变化当源码失配。
2. 首轮sigma仅改变声明精度、WLS权重与质量半径；bearing保持确定性零扰动，避免同时引入测量随机性，不宣称统计鲁棒性。
3. PASS/FAIL仅在原估计/数值前置条件成立后按r≤0.06严格判定；UNKNOWN涵盖不足测量/不可接受或不可评价等；数值异常可直接阻断。missing不等于FAIL，Q FAIL不等于belief必须拒绝估计。
4. 相同tick/目标/机器人位置/角色/方向/扰动/阈值，只改U1 sigma，OLD和DEGRADED均执行原WLS/assess_quality；不直接指定结果。新动态右80还需复核同几何条件，不拿probe替代主场景。
5. OLD及各DEGRADED_i独立branch/cache/payload，不同key空间，旧packet不修改。同一key改变sigma仍应被原缓存冲突拒绝。
6. effective、public、decision分别定义并保存；首版80/80/80，一般effective≤public≤下一合法cut。参数表是私有外生机制，当前到期声明才公开。
7. 旧团队移动到80，用effective80参数生成右80并结算(79,80]；再公布/消费/冻结，提交换员并建立新左80；(80,81]才判新服务。新左80反馈不影响刚冻结的belief80。
8. 独立physical_profile_at与public_profile_at，不将未来schedule放入view/config/seed/闭包。仅隐藏profiles不足以防packet.sigma/Q/缓存泄漏，延迟公告不支持。ACTUAL基类Oracle控制和含真状态checkpoint不能直接作为MODEL公开接口。
9. ModelRawCache键/上下文、first outcome、冲突拒绝有历史单位证据；当前H1复用/冲突0。stream标签循环并非真实换流，必须用新旧端点真实融合验证。
10. F1同tick真实成员更换后复用保留U0 raw；F2 VALID历史只读继承及上下文冲突；F3 cache/pending/融合状态和错误身份分别隔离。均是首轮未来必要专项，结果NOT_RUN，不改D1A验收。
11. 固定U0负角色保留，U1退出，空闲U2加入T0正角色，完整q2/资源互斥/生命周期检查；TEAM_CHANGED关闭旧段、建新段，原子提交。是预设动作，不是自主选择算法。
12. U1退出和U2加入各变化一次，通常2*kappa=0.02；若真实还改角色须按条目重计。自然释放零额外费，不重复加进度损失罚；新场景task_count=1分母明确。
13. 旧(79,80]绝不被新动作追溯改变；新段clock0，左80本身不产生服务；新(80,81]需同段两端G/Q都PASS。U2必须按公开belief真实移动，G可暂失效，UNKNOWN也invalid。
14. t_change/t_GQ/t_resume/t_complete分别取事务、首个GQ端点、首个完整有效区间右端和真实完成事件；可不同且可null，不填虚构值/不以ceil替代processed_tick。
15. B0/B1同一初态/任务/外生变化/成本/信息规则，独立MODEL内部状态；B1仅预设干预。B2为两机器人q2公共准入负例，零physics/WLS，不虚构三机器人中的单机器人被别的完整q2占用，也不拿missing/远G当Assignment非法。B3 missing专用UNKNOWN负例，与主sigma因子分开。保存每个profile、packet、key、WLS/Q、流/段、端点/区间、公开view/消费、位移/effort、四时间、全账及资源。
16. 最小新增合法fixture、动态实际/公开profile接口、预设controller与动态审计。原fuse/WLS/事务/advance/时钟/经济尽量复用，不修改冻结实现。D1A run中自动R选择在独立D1B驱动里改为实验动作，不改R算法，不伪造R输出。B2不扩展3固定数组内核为2机器人模拟器。
17. 六QM Gate设计为DESIGN_PASS_WITH_DEPENDENCIES，无直接科学矛盾；没有任何PHYSICAL_PASS。未来必须补合法fixture、profile信息隔离、专项端到端及真实Q准入证据。
18. 真实Q-only FAIL、动态sigma结果、MEMBER_CHANGE恢复/完成/成本及自主换员均未验证。找不到明确FAIL、无恢复、未完成或净差非正都允许据实收尾；不调阈值/时刻/初态求成功。

## 关键场景选择

不机械沿用原H1作为修复成功场景：原T0时长2.25秒，D80清零后到D120只有2秒，原U2又在(2,2)，不能先验宣称能完成。
规划独立单T0、q2、三机器人MODEL fixture：birth60，prior(9,10)、CV(0.4,0)，weight1、服务1.05、软deadline5秒、终点120；原角色偏移上初始化U0/U1，U2在正角色位置外0.70待命。它只提供潜在恢复机会，不保证G/Q。新fixture须有合法PUBLIC_PRIOR/MODEL出生与历史，D60真实首次融合后clock0；不是改写旧ACTUAL坐标或来源。未来若不接受该新fixture，必须在任何WLS前另外冻结合法初态，不能运行后选有利场景。
候选退化因子[2,4,8,16]升序，仅选第一个OLD PASS/DEGRADED FAIL且G均PASS的值，最多四项。基线不合法或候选耗尽有明确构造失败状态；异常停止。没有执行任何数值搜索。

## 科研与实现边界

首轮80/100更新合法belief但不做R最优选择，B0保持旧队，B1只在80预设换员后保持新队；未来自主净价值决策属于D1-C。只用CV与零角度扰动，不引入连续转向、随机噪声、新WLS、新Q阈值或复杂缓存。
设计成本估算一次有限批次约≤238次MODEL WLS，包含初始左端点、探针及七项各至多四融合的测试估计；不是实耗或生产守卫。MODEL策略候选WLS=0、ACTUAL=0；CPU/墙钟未测。下一执行授权前固定版本、实际预算与外部保护，不能拿旧1255或预算上限当实际值。
本轮仅静态文本/JSON/AST/Git只读/SHA及文档写入；没有科学模块导入、测试、WLS、MODEL推进、ACTUAL STEP或新物理场景，也没有修改旧档/源码/配置或提交推送。
设计完成后停止，等待独立设计审查；不自动进入任何实现/实验阶段。
''')
save('BASELINE.json',dict(current_HEAD=HEAD,science_reference_HEAD=REF,formal_execution_HEAD=EXE,branch=git('branch','--show-current'),initial_worktree='clean; checked before creating this directory',science_diff_from_reference=[],protected_before=protected,source_locations=rows))
assert all(sha(R/p)==s for p,s in protected.items())
assert not git('diff','--name-only',HEAD,'--','research','pursuit_v2','scripts','tests','configs')
assert not any(n.startswith(('research.','pursuit_v2.','numpy','scipy')) for n in sys.modules)
save('ZERO_EXECUTION_AND_PRESERVATION.json',dict(scientific_modules_imported=False,tests_run=0,WLS=0,MODEL_run=0,MODEL_advance=0,ACTUAL_STEP=0,sigma_candidates_evaluated=0,new_physical_scenarios=0,protected_pins_match=True,scientific_files_modified=[],method='Static standard-library AST/text/JSON/hash and Git read-only queries only'))
save('SHA256.json',{p.relative_to(R).as_posix():sha(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='SHA256.json'})
print('D1_B_QM_0_DESIGN_READY_WITH_DEPENDENCIES; design only; zero WLS/physics/tests.')
