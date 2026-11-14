# H4目标转向探索实验最终独立科学验收登记

登记日期：2026-11-15  
科学任务：`STFBS_LITE_TARGET_TURN_EXPLORATION_001`  
被验收结果提交：`f0ea43517511f61829b78cad9fe72c838e2c2a94`  
冻结科学规范：V1.0及最终R1—R4 Addendum

## 一、裁定来源与接收范围

主研员正式接受独立科研与工程审查员已经作出的最终裁定：**ACCEPTED_WITH_LIMITATIONS**。

本文件根据项目负责人本次明确的关闭登记指令，登记已经完成的独立科学验收，不是Codex重新开展的独立审核。本次不进行计算、测试、工程整改或历史证据补造。

正式接收ATTEMPT_002已完成HF KEEP的离线核验结果，以及ATTEMPT_003实际完成的HF SWITCH、HF MEMBER_CHANGE、CAP KEEP、CAP SWITCH、CAP MEMBER_CHANGE和NoCap KEEP，共七格有效科学结果。三次执行累计科学启动8次；HF KEEP没有在ATTEMPT_003重新计算。

### 历史实施错误与恢复过程

1. 首次执行在HF KEEP的D80反馈冻结处因局部提取函数缺少`DT`绑定而中止，启动1格、有效0格。错误属于局部实施问题，不是科学负面结果。原[失败记录](RAW/H4_HF_KEEP_FAILURE.json)、[最终报告](FINAL_REPORT.json)和[资源回执](RESOURCE_RECEIPT.json)保持不变。
2. ATTEMPT_002补齐冻结原值`DT=0.05`，通过针对性合成freeze与速度差分验证。HF KEEP已完整推进至D120并保存RAW，但局部审计适配按变量名`x`替换过宽，误改历史字典复制表达式，导致后置审计异常。原[RAW](ATTEMPT_002/RAW/H4_HF_KEEP.json)、[失败堆栈](ATTEMPT_002/RAW/H4_HF_KEEP_FAILURE.json)、[最终报告](ATTEMPT_002/FINAL_REPORT.json)和[资源回执](ATTEMPT_002/RESOURCE_RECEIPT.json)均保留原状，原状态仍为`BLOCKED_NO_VALID_CELLS`。
3. ATTEMPT_003仅在准确的原运动及逃逸表达式处适配审计，保留`x = deepcopy(h)`及历史摘要逻辑。使用保存的RAW、冻结视图、原始D60输入及资源记录离线核验HF KEEP，接收为`ACCEPTED_WITH_LIMITATIONS`；随后完成此前未启动的六格。未恢复或伪造缺失的原终端内存对象，也未追认未保存的原审计成功回执。

离线接收依据见[H4_HF_KEEP_OFFLINE_ACCEPTANCE.json](ATTEMPT_003/H4_HF_KEEP_OFFLINE_ACCEPTANCE.json)，其中保留`SOURCE_EXECUTION=ATTEMPT_002`、`SCIENTIFIC_REEXECUTION=NO`和`ORIGINAL_ATTEMPT_STATUS=BLOCKED_NO_VALID_CELLS`。本登记不覆盖前两次失败状态。

## 二、完整科学价值矩阵

下列数值直接引用已保存的[ATTEMPT_003报告](ATTEMPT_003/REPORT.md)、[价值矩阵](ATTEMPT_003/VALUE_MATRIX.json)和[科学分析](ATTEMPT_003/SCIENTIFIC_ANALYSIS.json)，本次未重新计算。H3仅为已验收历史参照，没有重跑。

| 动作 | H3 HF | H3 CAP | H4 HF | H4 CAP |
|---|---:|---:|---:|---:|
| KEEP | -0.3150141073101529 | -0.7125094014320741 | -0.31501434886780705 | -0.7125094014320741 |
| SWITCH | -0.157503491576509 | -0.7325026216050797 | -0.157503491576509 | -0.7325026216050797 |
| MEMBER_CHANGE | -0.7331120450139224 | -0.7330898517001428 | -0.7331122523628949 | -0.7330898517001428 |

H4 NoCap KEEP净价值为`-0.7125240900278447`。NoCap仅评估KEEP，不构成完整三动作NoCap矩阵，不据此生成完整NoCap排序、三格MAE或决策regret。

| 已接收指标 | 实际归档结果 |
|---|---|
| H4 CAP三格MAE | 0.3241721944185299 |
| H4 CAP严格排序 | KEEP > SWITCH > MEMBER_CHANGE |
| H4 HF严格排序 | SWITCH > KEEP > MEMBER_CHANGE |
| H4 CAP所选KEEP的HF regret | 0.15751085729129805 |
| H3 CAP所选KEEP的HF regret | 0.1575106157336439 |
| H3/H4 HF近似最优动作 | 均为SWITCH，无最优动作冲突 |
| H4 CAP KEEP相对HF绝对价值误差 | 0.39749505256426704 |
| H4 NoCap KEEP相对HF绝对价值误差 | 0.3975097411600376 |
| H4 NoCap相对CAP的净价值效应 | -0.000014688595770584456 |
| H4 NoCap相对CAP的绝对价值误差变化 | +0.000014688595770584456 |
| H3 NoCap相对CAP的净价值效应 | +0.3974952941219212 |
| H4与H3的NoCap净价值效应差 | -0.3975099827176918 |

排序与近似最优集合继续沿用epsilon=1e-8。预测误差按目标—控制tick去重，配对比较采用对应目标、相同控制时刻的共同有效记录，完整任务价值不截断至该范围。有效分母、共同tick、位置与速度误差及停止控制时刻均引用既有[SCIENTIFIC_ANALYSIS.json](ATTEMPT_003/SCIENTIFIC_ANALYSIS.json)中的预测汇总和配对比较，不新增控制记录、不插补数据。

## 三、正式接收的核心科学发现

以下内容依据主研员接受的独立审查裁定及既有实际归档登记，不冒充本次新开展的独立核验。

1. **运动模型失配。** 在本案例中，正确的D60初始位置和速度估计不能保证未来状态预测正确。T0在D75位置连续、瞬时速度右连续转向；D75的位置仍只含转向前位移，D76起才包含转向后位移。
2. **NoCap普遍充分性的反例。** NoCap在H3恢复KEEP任务完成，但在H4未恢复任务完成。因此，当前反例否定“仅取消一秒截断就普遍足以恢复完成能力”的主张，不等于否定NoCap在其他条件下的作用。
3. **状态精度与服务阈值。** 按独立审查已接收的共同有效控制记录口径，H4 NoCap的位置预测误差下降约40.31%、速度预测误差下降约46.95%；最大连续服务进度由CAP的1.90秒提高至2.10秒，但仍未达到2.25秒阈值。百分比为既有独立裁定的登记值，不是本次重新计算结果；完整有效范围与分母以原分析为准。
4. **状态精度与经济价值分离。** H4 NoCap相对CAP净价值下降`0.000014688595770584456`，差异来自控制成本增加。CAP与NoCap KEEP均未完成，其他相关经济分项保持原记录；不能把位置或速度误差下降自动等同于价值改善。
5. **HF实际反馈响应。** HF KEEP在D80实际冻结时已适应转向，估计速度约为`(0.3510330247561484, 0.19177021544167872)`，对应真实速度约为`(0.35103302475614784, 0.19177021544168052)`；归档速度误差为`1.8875832159447663e-15`。其于D93完成任务，服务进度达到2.25秒，未发生服务重置。这是实际响应过程证据，不是关闭反馈对照下的净因果效应证明。
6. **动作依赖的信息演化。** 不同候选动作对应不同的观测目标与后续信息演化。被分配目标的MODEL观测可更新其belief；未被观测的目标仍可能保持旧估计及传播误差，不能假定所有动作共享相同的未来信息。
7. **动作选择误差保留。** H4原代理仍选择KEEP，而HF最优动作仍为SWITCH，代理所选动作的HF regret为`0.15751085729129805`。
8. **未观察到跨世界最优动作冲突。** H3/H4的HF最优动作均为SWITCH。该负面发现完整保留，不为追求冲突而增加世界、调整转向参数或追加计算。

## 四、科学与证据限制

- 本次只有一个确定性转向案例，不支持总体统计推断或推广至全部非匀速目标运动。
- 公开目标属性仍为constant_velocity，实际H4分段转向，属于明确的公开运动模型失配诊断。D75瞬时转向不是有限加速度的平滑转弯模型。
- HF采用固定候选动作及D80/D100同动作保持事务，区别于重新调用R的动态策略；不宣称验证了历史动态R策略在H4中的表现。
- HF观测属于MODEL/SIMULATED来源，保留算法内部ACTUAL_WLS等描述标签，不因此将其归类为ACTUAL观测计算。
- 未新增关闭HF反馈的对照，HF反馈净因果效应未独立识别。
- NoCap仅KEEP一格，不构成完整动作矩阵，也不能单独证明决策排序或完整鲁棒策略优势。
- HF KEEP原终端Branch内存及部分完整终端历史对象缺失。离线核验依据保存的RAW、事件、物理帧、冻结视图及资源记录；不伪造原内存或原审计成功回执。相关限制见离线接收文件。
- 预测精度、连续服务进度、是否跨过完成阈值和最终净价值是不同层次，不相互替代。
- 资源会计继续为INCOMPLETE，完整资源合规为NOT_ESTABLISHED。未知资源不得记零，低CPU记录不证明生产算法的计算效率优势。

## 五、三次独立窗口资源登记

直接保留三次原始资源回执：[首次](RESOURCE_RECEIPT.json)、[ATTEMPT_002](ATTEMPT_002/RESOURCE_RECEIPT.json)、[ATTEMPT_003](ATTEMPT_003/RESOURCE_RECEIPT.json)。下表为本次正式验收指令给出的可确定累计，不重新运行资源核算。

| 指标 | 可确定累计 |
|---|---:|
| 科学启动 | 8 |
| 有效科学单元 | 7 |
| Observation WLS | 165 |
| Solver启动 | 1485 |
| 已闭合内部资源调用 | 1650 |
| 已测CPU小计 | 16.484375秒 |
| 各窗口已记录墙钟之和 | 2118.995377秒 |
| 受控累计逻辑写入 | 8596553 bytes |

墙钟合计是三个分别授权窗口已记录区间之和，不是一个共享1800秒连续窗口的消费。前两次消费不退款、不归零，未知覆盖继续保留，不能以新窗口证明旧窗口整体合规。

## 六、后续窗口授权记录及来源限制

以下授权依据为执行本系列任务的用户—Codex会话中项目负责人实际提供的明确授权原文，不依据本次关闭登记倒推历史授权。未另行提供可独立核实的原始会话导出、签名授权文件或独立授权核验回执，故仍保留独立核实状态限制。

### ATTEMPT_002

项目负责人在本会话明确表示：

> 正式批准 `STFBS_LITE_TARGET_TURN_EXPLORATION_001_ATTEMPT_002`，接受上述最小修复、针对性验证、七格执行范围及全部第二次资源上限；采用路径B，接受探索性资源会计INCOMPLETE，保留首次失败及全部消耗。再次失败时停止，不自动修复重试。

对应范围为补齐冻结DT及直接依赖检查、必要合成freeze验证、新独立窗口最多3个HF和4个代理单元；CPU300秒、连续墙钟1800秒、受控逻辑写入536870912 bytes，Observation WLS每HF格63次/总189次，Solver每格600次/总1800次，其他禁止调用保持原状。执行自述与身份关联另见[ATTEMPT_002准备记录](ATTEMPT_002/PREPARATION_ACCOUNTING.json)，该执行方记录不替代独立授权证据。

### ATTEMPT_003

项目负责人在本会话明确表示：

> 正式批准ATTEMPT_003，授权最小审计修复、ATTEMPT_002 HF KEEP离线核验及剩余最多六格执行。批准CPU 300秒、连续墙钟1800秒、受控累计逻辑写入536870912 bytes；新增HF最多2格、代理最多4格，Observation WLS每格63次、合计126次，Solver每格600次、合计1200次，其余禁止调用保持不变。采用路径B，接受资源会计INCOMPLETE；保留前两次全部记录，不重跑HF KEEP，不自动重试。

执行身份关联见[ATTEMPT_003准备记录](ATTEMPT_003/PREPARATION_ACCOUNTING.json)。未为这些授权补造原始时间戳、签名或独立证明。

```ini
OWNER_AUTHORIZATION_SOURCE = EXPLICIT_USER_MESSAGES_IN_EXECUTION_CONVERSATION
CONTINUATION_AUTHORIZATION_RECORD = NOT_INDEPENDENTLY_VERIFIED
```

该授权证据的独立核实限制与七格科学有效性分别判断，不修改前两次失败状态，也不影响本次按主研员正式裁定登记的有限科学接收。

## 七、最终状态及阶段关闭

```ini
HF_KEEP_OFFLINE_ACCEPTANCE = ACCEPTED_WITH_LIMITATIONS
TOTAL_VALID_DIAGNOSTIC_CELLS = 7/7
TOTAL_SCIENTIFIC_STARTS = 8

MOTION_MODEL_MISMATCH = SUPPORTED_IN_TESTED_CASE
NOCAP_GENERAL_SUFFICIENCY = REFUTED_BY_H4
STATE_ACCURACY_VALUE_DIVERGENCE = VERIFIED
SERVICE_THRESHOLD_EFFECT = VERIFIED
HF_FEEDBACK_ADAPTATION = OBSERVED
ACTION_DEPENDENT_INFORMATION = OBSERVED
CROSS_WORLD_OPTIMUM_CONFLICT = NOT_OBSERVED

INDEPENDENT_SCIENTIFIC_ACCEPTANCE = ACCEPTED_WITH_LIMITATIONS
RESEARCH_LEAD_ACCEPTANCE = CONFIRMED

SCIENTIFIC_BLOCKERS = NONE
SCIENTIFIC_REEXECUTION_REQUIRED = NO
ADDITIONAL_DIAGNOSTIC_EXPERIMENTS = NOT_REQUIRED
ADDITIONAL_ENGINEERING_REMEDIATION = NOT_REQUIRED

RESOURCE_ACCOUNTING = INCOMPLETE
RESOURCE_COMPLIANCE = NOT_ESTABLISHED

TARGET_TURN_EXPLORATION = CLOSED
L3_B_EXPLORATORY_STAGE = CLOSED
L3_B_FORMAL_STATUS = L3_B_BLOCKED
L3_C_EXECUTION_AUTHORIZATION = NOT_GRANTED
PRODUCTION_ADMISSION = BLOCKED
```

本次仅新增本登记文件，关闭已完成有限独立验收的目标转向探索阶段；不开展新科学计算、工程整改或测试，不修改原始结果与状态，不启动L3-C。
