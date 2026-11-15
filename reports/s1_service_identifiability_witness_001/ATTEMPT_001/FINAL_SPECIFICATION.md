# S1_SERVICE_IDENTIFIABILITY_WITNESS_001

## V1.0 FINAL SPECIFICATION

## 1. 任务状态及授权边界

项目仓库：

`lyc0212/dynamic_member_coalition_core`

本任务属于新的服务可辨识性研究阶段。

负责人、主研员及独立审查员已就唯一一次世界B ACTUAL存在性验证的科研路线达成共识。

不需要再次讨论总体科研框架或增加设计审核环节。

```text
TASK = S1_SERVICE_IDENTIFIABILITY_WITNESS_001
SPECIFICATION = V1.0_FINAL
MAIN_RESEARCHER_SPECIFICATION = CONFIRMED
RESEARCH_DESIGN_CONSENSUS = ESTABLISHED
ADDITIONAL_DESIGN_REVIEW_REQUIRED = NO
OWNER_RESOURCE_APPROVAL = PENDING
EXECUTION_AUTHORIZATION = NOT_GRANTED
PRODUCTION_ADMISSION = BLOCKED
```

本规范须在负责人明确批准执行及资源预算后生效。

此前任务保持正式关闭：

```text
CCVD_INITIAL_DECISION_VALIDATION_001 = CLOSED
N1_INDEPENDENT_DECISION_VALIDATION_001 = CLOSED
N1_SWITCH_FAILURE_ATTRIBUTION_001 = CLOSED
PREDICTOR_RESEARCH_PHASE = CLOSED
BLVF_CORE = FROZEN
```

不得重新开启历史研究，不得执行预测器整改。

## 2. 唯一科研目标

检验两个具有相同合法公开信息的相容物理世界，是否具有不同的连续服务完成结果及最优联盟动作。

利用已有世界A ACTUAL证据，通过唯一一次世界B的原SWITCH实际执行，判断有限候选集合及固定Hold条件下的决策不可辨识性反例是否成立。

本任务不是：

- 新算法性能验证。
- N1预测器修复。
- BLVF专项验证。
- WLS误差认证。
- 多情景决策研究。
- 主动信息获取研究。

不预设世界B中的SWITCH必须失败。

合法负面结果具有同等科学价值。

## 3. 历史证据及冻结输入

原N1参考提交：

`69fee291885f354978ba3ed7b873579b1ba87c34`

单格归因参考提交：

`d8d3f32e00c65aafd1817073b1c3254c22717ed6`

原N1目录：

`reports/n1_independent_decision_validation_001/ATTEMPT_001/`

主要复用证据：

```text
EXPERIMENT_CONFIG.json
I/PUBLIC_D60.json
I/PREFIX_RECEIPT.json
I/DECISION_FREEZE.json
I/CANDIDATES.json
I/ACTUAL_VALUES.json
I/MODEL_VALUES.json
I/WORLDS.json
I/SERVICE_ANALYSIS.json
I/ACTUAL_K_RAW.json
I/ACTUAL_S_RAW.json
n1_entry.py
```

单格归因状态恢复回执：

```text
reports/n1_switch_failure_attribution_001/
    ATTEMPT_001/
    STATE_RECOVERY_RECEIPT.json
```

世界A共同候选ACTUAL价值：

| 动作 | 实际净值 | 完成情况 |
|---|---:|---|
| K | -0.32251923105899283 | D102完成T0 |
| S | -0.14254431500738049 | D114完成T1 |
| M | -0.32501858815285356 | D105完成T0 |

实际分析使用原始文件全精度数值，不使用报告舍入值替代。

在共同候选集合K/S/M内：

```text
A_STAR_WORLD_A = {S}
```

世界A的S相对于K的经济优势：

```text
D_A = J_A(S) - J_A(K)
    ≈ 0.17997491605161234
```

原W1 MODEL预测：

```text
V_W1(S) = -0.71253999405727086
T1_COMPLETED = NO
```

该预测仅作为待检验的科学假设。

注意：原R_EXTRA的ACTUAL价值略高于S。

因此，世界A中S的唯一最优性仅限于K/S/M共同候选，不是完整合法候选目录最优性。

## 4. 唯一新增物理世界B

直接读取原`EXPERIMENT_CONFIG.json`中的案例I。

保留完整public配置。

对原physical进行深拷贝，仅修改T1的以下两个隐藏物理字段：

```python
target1["position_at_birth"] = [9.45, 10.0]
target1["velocity"] = [0.4, 0.0]
```

世界定义：

| 参数 | 世界A | 世界B |
|---|---|---|
| T1真实出生位置 | (9.0,10) | (9.45,10) |
| T1真实速度 | (0.6,0) | (0.4,0) |
| T1公开公告位置 | (9.45,10) | 不变 |
| T1公开控制速度先验 | (0,0) | 不变 |
| T1出生时间 | D60 | 不变 |
| T0物理定义 | 原案例I | 不变 |
| 机器人初始位置 | 原案例I | 不变 |
| 传感器配置 | 原案例I | 不变 |
| 测量角度扰动 | 0 | 不变 |
| 经济配置 | ECON-NOC | 不变 |

保留原T1的turns、turn_increment及arc_rates等运动配置。

确认D60—D120期间T1真实物理轨迹为：

```text
p_x(t) = 9.45 + 0.4 * (t - 3)
p_y(t) = 10.0
```

其中t为全局仿真时间。

世界B使用原案例I的T0真实物理定义，不使用W1中经合法历史差分得到的浮点近似速度替换T0。

除上述T1的两个字段外，禁止修改任何科研参数。

保存世界A至世界B的配置差异。

不根据结果调整世界B。

## 5. 世界合法性与信息边界

两个世界均需符合原研究预声明条件：

```text
POSITION_ERROR_BOUND = 0.5
SPEED_SUPPORT = [0.4, 0.8]
HEADING_SUPPORT = [-0.5, 0.5]
```

世界B：

```text
T1_POSITION_ERROR = 0
T1_SPEED = 0.4
T1_HEADING = 0
```

位置误差界属于冻结研究设定，不解释为经过校准的WLS置信区间。

真实T1位置及速度仅用于ACTUAL物理环境及事后分析。

不得将其输入：

- 公开公告。
- 初始控制belief。
- 原有控制状态。
- 候选生成器。
- 联盟选择算法。

使用原非Oracle信息机制。

本任务不重新生成候选，不进行新的事前联盟优化。

两个世界允许具有不同的后台物理身份及私有状态摘要。

但提交首动作之前，合法公开policy view必须一致。

不得为追求摘要一致而删除、屏蔽或修改公开信息字段。

## 6. 唯一ACTUAL执行的共同前缀

从D0正常构造世界B的原`StaggeredEnvironment`。

使用原`scripts.run_a1.Sensing`及ACTUAL WLS路径。

复用原N1案例I的受控前缀：

| 时刻 | 动作 |
|---|---|
| D0 | 全部机器人空闲 |
| D20 | U0、U1服务T0 |
| D40 | 保持原联盟 |
| D60 | 合法反馈消费后冻结 |

D20及D40分配：

```json
[
  {"target": 0, "role": "dual_neg45"},
  {"target": 0, "role": "dual_pos45"},
  {"target": null, "role": "none"}
]
```

禁止调用原R产生前缀分配。

不得人工设置D60机器人位置、控制belief、服务时钟或观测历史。

D60仅执行一次原`prepare_decision()`。

D60冻结边界：

```text
POST_FREEZE_PRE_ASSIGNMENT
```

共同前缀是唯一ACTUAL完整执行的组成部分。

完成D60核查后，直接使用同一个环境对象继续执行未来S分支。

不得重新启动一个额外前缀。

## 7. D60公开信息等同性核查

在提交S之前必须核对：

```text
PUBLIC_D60_WORLD_B == PUBLIC_D60_WORLD_A
```

复用原N1执行入口实际使用的digest函数：

```python
from research.non_oracle.stfbs_d1a_replay import digest
```

原冻结公开状态摘要：

```text
4ca524be946aafaeece4058597433de613cdb29452d18efa63f45d1c2b8441fe
```

从原`DECISION_FREEZE.json`和`PUBLIC_D60.json`读取并核对。

要求：

- 完整公开policy view一致。
- 机器人位置一致。
- 当前Assignment一致。
- T0已有连续服务进度为0.15秒。
- T0合法控制belief及服务历史一致。
- T1三个机器人观测slot均为UNQUERIED。
- T1观测packet均为空。
- T1控制belief仍为原PUBLIC_PRIOR、PRIOR_ONLY。
- T1初始位置估计仍为(9.45,10)。
- T1初始速度估计仍为(0,0)。
- T1尚无已接受历史观测。

共同前缀经济账本与原`PREFIX_RECEIPT.json`中的metrics比较。

已经验收的归因任务`STATE_RECOVERY_RECEIPT.json`中的`prefix_metrics`可作为辅助交叉核对依据。

前缀历史净收益约为：

```text
-0.025017527612236214
```

实际比较使用全精度历史记录。

若存在关键公开状态或经济账本差异，保存差异并停止，不提交未来S分支。

本任务不需要MODEL映射、consumer种子构造或BLVF初始化。

## 8. 唯一未来ACTUAL动作

直接读取原`I/DECISION_FREEZE.json`中的：

```text
candidates.S
```

冻结完整Assignment：

```json
[
  {"target": 1, "role": "dual_neg45"},
  {"target": 1, "role": "dual_pos45"},
  {"target": null, "role": "none"}
]
```

机器人身份及角色排列必须与原冻结候选一致。

D60撤回T0时，原0.15秒进度按原连续服务规则处理。

不得人为保留被撤回的T0进度。

禁止重新选择SWITCH代表。

禁止新增Assignment优化。

## 9. ACTUAL执行机制与Hold

复用原N1的ACTUAL实际执行路径。

主要源码：

```text
scripts/run_a1.py
research/non_oracle/environment.py
research/non_oracle/belief.py
research/information_service_online/execution.py
research/information_service_online/measurements.py
research/cooperative_sensing/estimator.py
research/information_service/public_quality.py
pursuit_v2/service.py
```

执行顺序：

```text
D0—D60原合法共同前缀
    ↓
D60公开信息及前缀经济核查
    ↓
提交冻结S
    ↓
D60—D80 ACTUAL
    ↓
D80合法反馈消费及Hold
    ↓
D80—D100 ACTUAL
    ↓
D100合法反馈消费及Hold
    ↓
D100—D120 ACTUAL
    ↓
保存结果
    ↓
停止
```

D80及D100采用当时有效的Assignment保持策略。

允许原自然完成、逃逸及资源释放。

不得在任务完成后重新提交最初的SWITCH动作。

全程保留：

- 原ACTUAL九起点非线性WLS。
- 原合法位置历史。
- 原速度差分及速度裁剪。
- 原belief传播截断。
- 原控制律与物理限速。
- 原G/Q服务判定。
- 原双端点连续服务时钟。
- 原反馈消费时刻。

不得使用BLVF代替WLS。

不得强制D80获得准确位置或速度。

不得修改WLS返回结果。

不需要证明WLS满足此前提出的0.0048位置误差充分界。

本次直接观察原执行机制的真实仿真结果。

## 10. ECON-NOC与经济评价

固定：

```text
change_cost = 0.0
```

复用此前已成功使用的任务局部严格schema适配。

仅局部修改：

```text
/$defs/Config/properties/change_cost/const
```

从0.01替换为0.0。

保留原其他schema约束及原校验函数。

正常及异常退出均恢复原schema引用。

禁止修改生产配置文件。

主要科研参数：

```text
T0.service_duration = 2.25
T1.service_duration = 1.05

T0.weight = 1.0
T1.weight = 1.5

T0.deadline = 2.0
T1.deadline = 5.0

DT = 0.05
START_TICK = 60
END_TICK = 120
```

统一经济评价窗口为D60—D120。

计算：

```text
J_B(S) =
    FINAL_RETURN_WITH_CHANGES
    - PREFIX_RETURN_WITH_CHANGES
```

每个经济分项同样扣除共同前缀已经产生的分项。

保存：

```text
completion
flow
late
effort
terminal
change_cost
net
```

禁止重复计入D60以前共同前缀经济收益。

## 11. KEEP结构性不变性

本任务不新增世界B的KEEP实际执行。

根据冻结条件，使用：

```text
J_B(K) = J_A(K)
```

其成立依据为：

1. 世界A与世界B仅改变未服务T1的隐藏物理运动。
2. K始终服务T0，直至完成和自然释放。
3. T0物理运动、机器人初态、控制belief及服务历史相同。
4. 原控制和观测机制按任务及当前团队处理。
5. 未服务T1不参与T0观测定位或运动控制。
6. T1在两个世界中均不会在D120之前逃逸。
7. T1经济参数及终端结算规则相同。
8. 固定Hold不因T1隐藏运动变化主动改变分配。

通过有限源码核查确认上述结构条件。

无需为此开展通用执行框架认证。

若条件成立，则：

```text
J_B(K) = -0.32251923105899283
```

该值必须明确标识：

```text
SOURCE = STRUCTURAL_INVARIANCE
```

不得标识为新增ACTUAL测量值。

若发现足以破坏该推论的真实耦合：

- 保存唯一S实际执行结果。
- 不再使用结构性K价值作确定排序。
- 将决策不可辨识性登记为未建立。
- 不追加K或M执行。

## 12. 服务完成可辨识性分析

令：

```text
C_A = T1_COMPLETION_UNDER_S_WORLD_A
C_B = T1_COMPLETION_UNDER_S_WORLD_B
```

历史已知：

```text
C_A = 1
```

报告两个世界原S的：

| 指标 | 世界A ACTUAL | 世界B ACTUAL |
|---|---|---|
| 初始G/Q | 读取历史 | 实际结果 |
| 服务中断 | D74 | 实际结果 |
| 后续恢复 | D93 | 实际结果 |
| T1完成 | YES | 实际结果 |
| T1完成时刻 | D114 | 实际结果 |
| 最大连续服务进度 | 1.05秒 | 实际结果 |
| 净价值 | -0.142544315007 | 实际结果 |

同时保存：

- D60、D80、D100关键控制belief。
- 首次G/Q合格端点。
- 后续连续服务区间。
- G/Q变化及进度重置。
- D99关键端点状态。
- 最大连续服务进度。
- 完成或未完成原因。

最大连续服务进度从完整轨迹和完成事件共同恢复，不因自然释放后的时钟消失而记为零。

若世界合法性、公开信息等同性及执行有效性成立，且：

```text
C_A = 1
C_B = 0
```

则可建立该S动作下T1服务完成状态的不可辨识性见证。

这一判断不需要KEEP结构性不变性成立。

## 13. 最优动作不可辨识性分析

令：

```text
X = J_B(S)
```

计算：

```text
D_A = J_A(S) - J_A(K)

D_B = X - J_A(K)
```

仅在KEEP结构性不变性成立时，D_B具有以下含义：

```text
D_B = J_B(S) - J_B(K)
```

数值比较统一使用：

```text
ECONOMIC_COMPARISON_EPSILON = 1e-8
```

该容差只用于科学结果判读，不是算法决策参数。

若：

```text
D_B < -1e-8
```

则S严格劣于世界B中的K。

由于原世界A在共同K/S/M候选内唯一最优动作是S：

```text
A_STAR_WORLD_A = {S}
S NOT_IN A_STAR_WORLD_B
```

因此：

```text
INTERSECTION(
    A_STAR_WORLD_A,
    A_STAR_WORLD_B
) = EMPTY
```

在上述科学不变量成立时，即可建立：

在相同D60公开信息、原ACTUAL控制机制及固定Hold条件下，不存在一个确定性共同候选首动作，能够在这两个世界中同时取得各自的最优候选价值。

不需要确定世界B的完整最优动作。

不得将K直接称为世界B唯一最优动作。

## 14. 确定性候选遗憾下界

若最优动作不可辨识性反例成立，定义：

```text
R(a,w) = max_b J(b,w) - J(a,w)
```

其中候选b仅来自冻结K/S/M。

计算：

```text
A_K_GAP = J_A(S) - J_A(K)

A_M_GAP = J_A(S) - J_A(M)

B_S_GAP = J_A(K) - X
```

则保守的确定性最坏情况候选遗憾下界为：

```text
REGRET_LOWER_BOUND =
    min(A_K_GAP, A_M_GAP, B_S_GAP)
```

由于历史上：

```text
A_M_GAP > A_K_GAP
```

可以化简为：

```text
REGRET_LOWER_BOUND =
    min(A_K_GAP, B_S_GAP)
```

若世界B两个任务均未完成，根据原经济公式：

```text
J_B(S) <= -0.7125
```

因此预期：

```text
B_S_GAP >= 0.389980768941
```

对应保守遗憾下界约为：

```text
0.179974916052
```

以上是条件性解析预期，实际报告以新增ACTUAL结果为准。

该下界仅适用于冻结共同候选及确定性首动作Hold策略。

不是完整候选空间、随机策略或任意多阶段自适应策略的性能下界。

不开展Minimax Regret优化。

## 15. 原W1预测对照

计算：

```text
MODEL_RESIDUAL_B =
    J_B(S) - V_W1(S)
```

报告：

- 原W1 MODEL完成状态。
- 新增ACTUAL完成状态。
- 原W1预测净值。
- 新增ACTUAL净值。
- 关键G/Q恢复时间差。
- 经济分项差异。

原W1中T0的参考CV见证与T0真实运动存在浮点尺度的表达差异，应保持原世界B定义，不为消除该差异修改T0。

上述比较用于报告原参考世界预测与实际执行的一致程度。

不新增MODEL。

不启动预测器修复。

不开展同世界残差的进一步因果定位。

## 16. 预声明科学裁定

服务不可辨识性与决策不可辨识性分别判断。

| 新增ACTUAL结果 | 服务完成不可辨识性 | 最优动作不可辨识性 |
|---|---|---|
| T1未完成，D_B严格为负 | 建立见证 | 建立有限反例 |
| T1完成，D_B严格为负 | 该对世界未建立 | 建立有限反例 |
| T1完成，D_B严格为正 | 该对世界未建立 | 本次比较未建立 |
| D_B处于数值并列范围 | 根据完成状态独立判断 | 严格排序未建立 |

决策不可辨识性成立还要求KEEP结构性不变性得到支持。

若公共信息不一致、世界不合法或执行语义错误，则不得将所得结果作为有效反例证据。

若T1未完成但经济结果不符合原未完成价值上界，应检查已有账本及执行语义，报告不一致，不自动重试。

若ACTUAL结果与原MODEL预测相反，保留真实结果。

不得改动世界B以获得预期结论。

SWITCH优于KEEP时，不能宣称SWITCH在世界B中全体共同候选最优，因为M没有实际评价。

本次没有建立反例，不代表一般不可辨识性命题被证明错误。

## 17. 科学启动硬上限

```text
ACTUAL_COMPLETE_EXECUTIONS_STARTED <= 1

PREFIX_RUNS_STARTED <= 1

ACTUAL_FUTURE_RUNS_STARTED <= 1

MODEL_CELLS_STARTED = 0

BLVF_ANALYTIC_ESTIMATE_CALLS = 0

R_CALLS = 0

RCV_SCORES = 0

ASSIGNMENT_OPTIMIZATION_CALLS = 0

KEEP_EXTRA = 0

MEMBER_CHANGE_EXTRA = 0

NEW_WORLDS_EXTRA = 0

PARAMETER_SWEEPS = 0

AUTOMATIC_RETRIES = 0
```

共同前缀及未来分支是同一次ACTUAL完整执行的组成部分。

前缀和未来分支分别计数，不重复计作两个完整ACTUAL实验。

原ACTUAL自然发生的观测WLS及底层非线性Solver调用属于允许的计算。

失败启动计入上限。

不使用未消耗额度开展其他科研任务。

## 18. 独立资源预算

待负责人批准：

```text
CUMULATIVE_CPU_LIMIT_SECONDS = 120

CUMULATIVE_WALL_LIMIT_SECONDS = 900

CUMULATIVE_CONTROLLED_LOGICAL_WRITE_LIMIT_BYTES = 134217728
```

累计受控逻辑写入上限为128 MiB。

预算覆盖：

- 必要实施准备。
- 唯一共同前缀。
- 唯一ACTUAL未来分支。
- 实际观测WLS和Solver。
- 原始证据保存。
- 最终分析与报告。

分别记录：

```text
ACTUAL_PREFIX_WLS_CALLS
ACTUAL_FUTURE_WLS_CALLS
NONLINEAR_SOLVER_STARTS
ACTUAL_COMPLETE_EXECUTIONS_STARTED
ACTUAL_COMPLETE_EXECUTIONS_VALID
PREFIX_RUNS_STARTED
ACTUAL_FUTURE_RUNS_STARTED
```

同时记录禁止项实际调用次数。

尽可能从任务准备阶段开始计量。

为停止及必要证据保存预留资源。

受监测预算触限时停止新增科学计算。

未知计量项登记为UNKNOWN或INCOMPLETE。

不得将未知资源消耗记为零。

不得以最终目录大小替代累计逻辑写入。

不开发新的通用资源监督框架。

## 19. 实施与历史资产保护

建议新增独立目录：

```text
reports/
    s1_service_identifiability_witness_001/
        ATTEMPT_001/
```

建立任务局部执行入口，例如：

```text
s1_witness_entry.py
```

允许复用原N1的共同前缀及ACTUAL执行逻辑。

不得直接执行或导入会启动历史完整实验的入口。

不修改：

- 生产核心源码。
- 原生产默认配置。
- 原冻结BLVF。
- 原N1决策及ACTUAL记录。
- 已关闭任务的报告和证据。

执行前记录HEAD、分支、工作树及关键文件身份。

保留任何已有用户工作。

不开展通用工程重构。

若发现无法在本任务局部范围内解决的关键实施阻断，保存具体证据并停止。

## 20. 输出证据

建议保存：

```text
FINAL_SPECIFICATION.md
OWNER_AUTHORIZATION.md
EXPERIMENT_CONFIG.json
WORLD_COMPARISON.json
SOURCE_IDENTITIES.json
SCHEMA_ADAPTATION.json
PUBLIC_D60.json
COMMON_PREFIX_RECEIPT.json
KEEP_INVARIANCE_ANALYSIS.json
ACTUAL_S_RAW.json
ACTUAL_VALUES.json
SERVICE_ANALYSIS.json
IDENTIFIABILITY_ANALYSIS.json
RESOURCE_RECEIPT.json
EXECUTION_STATUS.json
S1_WITNESS_RESEARCH_REPORT.md
```

文件可以按现有格式合理合并。

不要求为所有细节建立重复证据文件。

保证科学结论可追溯即可。

核心证据：

1. 世界A至世界B的唯一物理配置变化。
2. D60合法公开信息等同性。
3. 共同前缀经济一致性。
4. 原冻结S身份。
5. 原ACTUAL WLS及Hold实际执行记录。
6. 原始G/Q、连续服务和完成事件。
7. 实际净值及经济分项。
8. KEEP结构性不变性依据。
9. 资源计数及历史资产保护记录。

## 21. 最终报告状态

分别登记：

```text
IMPLEMENTATION_STATUS

SCIENTIFIC_RESULT_STATUS

WORLD_LEGALITY

PUBLIC_INFORMATION_EQUIVALENCE

KEEP_STRUCTURAL_INVARIANCE

WORLD_B_SWITCH_COMPLETION

SERVICE_NON_IDENTIFIABILITY

DECISION_NON_IDENTIFIABILITY

REGRET_LOWER_BOUND

MODEL_RESIDUAL_B

RESOURCE_ACCOUNTING

RESOURCE_COMPLIANCE

INDEPENDENT_ACCEPTANCE

PRODUCTION_ADMISSION
```

服务和决策不可辨识性允许分别为：

```text
ESTABLISHED_FOR_THIS_WITNESS
NOT_ESTABLISHED
NOT_IDENTIFIABLE_FROM_VALID_EVIDENCE
```

不得因科研结果为负而将有效实施判为工程失败。

完整资源计量未建立时，不宣称完整资源合规。

独立验收保持PENDING。

生产准入保持BLOCKED。

## 22. 有限验收原则

BLOCKER：

- 世界定义错误。
- 公开信息不等同。
- 隐藏真值污染控制belief。
- 候选身份错误。
- 执行语义错误。
- 关键经济口径错误。
- 其他破坏必要科学不变量的问题。

LIMITATION：

- 世界B完整价值矩阵未知。
- WLS数值误差界未建立。
- 原MODEL残差的具体来源未定位。
- 有效执行后未建立预期反例。
- 完整资源会计未建立。

OPTIONAL：

- 更详细的轨迹图。
- 额外理论解释。
- 非关键诊断量。

不要求世界B的SWITCH必须失败。

不要求MODEL与ACTUAL价值必须一致。

不要求精确恢复原W1预测轨迹。

不因非关键限制重新执行。

## 23. 最终停止规则

唯一ACTUAL执行完成后，无论结果为正面、负面或不确定，均停止。

禁止：

```text
ATTEMPT_002
KEEP_REEXECUTION
MEMBER_CHANGE_REEXECUTION
EXTRA_WORLD
EXTRA_MODEL
WLS_CERTIFICATION_PROJECT
N1_REPAIR
BLVF_REPAIR
S2_IMPLEMENTATION
S3_IMPLEMENTATION
```

不得自动调整案例或寻找其他反例。

如果反例成立，提交主研员开展后续理论机制研究。

如果反例未建立，保留结果，由主研员和负责人决定S1后续方向。

Codex不自行选择新的科研路线。

## 24. 最终执行要求

负责人正式批准本规范及资源预算后：

直接进行必要的只读输入核查，建立局部入口，并执行唯一世界B ACTUAL SWITCH。

不再次讨论已确定的总体科研设计。

完成后保存结果并向负责人提交：

1. 实际执行状态。
2. D60公开信息是否完全一致。
3. 世界B的T1完成状态及服务过程。
4. 世界B的SWITCH实际净值及经济分项。
5. 相对于结构性KEEP价值的实际收益差。
6. 服务完成不可辨识性裁定。
7. 有限候选最优动作不可辨识性裁定。
8. 若适用，确定性候选遗憾下界。
9. 原W1 MODEL预测残差。
10. 资源回执、提交身份及历史资产保护结果。

严格执行一次，并停止。

获得正式执行授权之前，不启动科研计算。
