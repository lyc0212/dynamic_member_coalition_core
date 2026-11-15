# Codex正式科研执行指令

# N1_SWITCH_FAILURE_ATTRIBUTION_001

## V1.0 FINAL SPECIFICATION — OWNER AUTHORIZED

## 1. 正式授权

项目仓库：

`lyc0212/dynamic_member_coalition_core`

负责人已明确批准：

- 正式关闭N1独立验证任务。
- 执行案例I的唯一事后同世界归因单元。
- 必要时最多一次原共同前缀重建。
- 本任务独立资源预算。

```text
TASK = N1_SWITCH_FAILURE_ATTRIBUTION_001
SPECIFICATION = V1.0_FINAL_SPECIFICATION
INDEPENDENT_DESIGN_REVIEW = APPROVED
TARGETED_INTERPRETATION_CLARIFICATIONS = INCLUDED
MAIN_RESEARCHER_CONFIRMATION = CONFIRMED
OWNER_RESOURCE_APPROVAL = APPROVED
EXECUTION_AUTHORIZATION = GRANTED
ADDITIONAL_DESIGN_REVIEW_REQUIRED = NO
PRODUCTION_ADMISSION = BLOCKED
```

原任务正式关闭：

```text
N1_INDEPENDENT_DECISION_VALIDATION_001 = CLOSED
FINAL_INDEPENDENT_SCIENTIFIC_ACCEPTANCE = ACCEPTED_WITH_LIMITATIONS
SCIENTIFIC_RESULT_STATUS = MIXED
ADDITIONAL_REMEDIATION_REQUIRED = NO
N1_FINAL_ALGORITHM_SELECTION = DEFERRED
```

保留全部历史正面及负面结果。

本任务不是重新开启N1独立验证，也不是恢复BLVF专项研究。

不需要再次申请授权或重新审核设计。

## 2. 唯一科学目标

判断N1案例I的SWITCH价值低估，有多少能够通过恢复正确外生物理世界得到解释，以及在同世界条件下还存在多少评价残差。

本次只检验冻结BLVF在特定正确外生世界条件下的服务过程及价值评价能力。

不验证完整同世界N1决策，不开发新算法。

原科研结果：

```text
V_N1_W1_S = -0.7125399940572709

J_ACTUAL_S = -0.1425443150073805

J_ACTUAL_K = -0.32251923105899283

V_N1_W1_K = -0.32251923105899283

V_N1_W1_M = -0.32501858815285356
```

实际计算时从冻结原始文件读取全精度数值，以保存数据为准。

## 3. 历史证据及源码复用

参考提交：

`69fee291885f354978ba3ed7b873579b1ba87c34`

原任务目录：

`reports/n1_independent_decision_validation_001/ATTEMPT_001/`

主要参考资产：

```text
n1_entry.py
EXPERIMENT_CONFIG.json
FINAL_SPECIFICATION.md
SOURCE_IDENTITIES.json

I/PUBLIC_D60.json
I/PREFIX_RECEIPT.json
I/MAPPING_RECEIPT.json
I/CANDIDATES.json
I/DECISION_FREEZE.json
I/WORLDS.json
I/WITNESS.json
I/MODEL_VALUES.json
I/S_W1_RAW.json
I/ACTUAL_VALUES.json
I/ACTUAL_S_RAW.json
I/SERVICE_ANALYSIS.json
```

冻结BLVF：

`reports/stfbs_lite_fb_blvf_initial_validation_001/blvf.py`

预期SHA256：

```text
204fc231bf78004c33daf151983d751685666da75ed9e9b911abb83854c7365e
```

继续复用原MODEL Branch、原consumer、原合法状态映射、原控制及服务规则。

建立独立任务局部入口及结果目录：

`reports/n1_switch_failure_attribution_001/ATTEMPT_001/`

不得直接执行原n1_entry.py完整入口。

不得导入会自动启动原完整科研任务的入口。

不得修改生产源码、默认配置、冻结BLVF及历史结果。

记录实际执行HEAD、源码身份及新增文件。

## 4. 唯一科学单元

```text
CASE = I_NEAR_SERVICE_HISTORY
ACTION = ORIGINAL_S
MODEL_WORLD = MATCHED_ACTUAL_EXOGENOUS_WORLD
ESTIMATOR = FROZEN_BLVF
START = D60
END = D120
POLICY = ORIGINAL_FIRST_ACTION_PLUS_HOLD
```

S必须为原冻结SWITCH候选：

```text
U0 -> T1 / dual_neg45
U1 -> T1 / dual_pos45
U2 -> IDLE
```

从原DECISION_FREEZE读取并核对完整Assignment身份。

不重新生成候选，不调用原R，不调用Assignment优化。

## 5. D60状态恢复

优先使用路径A，必要时允许路径B。

### 路径A：直接复用

只读检查是否已经保存完整可信的D60公开状态及consumer种子。

PUBLIC_D60本身不是完整consumer种子。

MAPPING_RECEIPT本身也不是完整consumer种子。

必须具有原映射所需的合法内部状态、接受位置历史、接受回执及必要历史信息。

若存在可直接可信复用的完整材料，直接使用，不重建前缀。

不为此开发新的状态桥接框架，不通过人工拼装伪造历史。

### 路径B：最多一次共同前缀重建

如果路径A不能直接可信复用，则允许按照原案例I冻结配置重建一次共同前缀：

```text
D0：全部机器人空闲
D20：U0/U1共同服务T0
D40：保持同一联盟
D60：合法反馈消费后、提交首动作前冻结
```

使用原案例I物理配置、原传感器、原实际观测定位及原控制规则。

允许必要的前缀ACTUAL观测WLS及底层solver调用。

该前缀只执行至D60，不得执行任何ACTUAL未来候选。

继续使用既有：

```python
cut = capture_live_cut(env, view)
mapped = prepare_real_cut_model_input(cut)
seed = mapped["candidate"]["consumer_seed"]
```

通过原映射接口恢复合法MODEL种子。

### 状态核对

无论采用哪条路径，均需保护以下科学不变量：

- 原D60公开状态及对应digest。
- 原机器人位置。
- 原Assignment。
- T0已有0.15秒连续服务进度。
- 合法服务历史及当前端点。
- 原控制belief。
- 合法consumer历史及其来源。

路径B还需核对原共同前缀经济账本及原映射结果。

不得将真实外生位置或速度植入控制belief。

不得将历史ACTUAL未来观测加入D60种子。

若无法可信恢复必要状态，则保存限制及失败证据，停止。

不要求补建无法恢复且不影响科学不变量的非关键历史记录。

前缀重建最多启动一次，失败计入上限，不允许自动重试。

## 6. 事后匹配外生物理世界

仅将MODEL物理世界修改为原案例I实际外生CV定义。

从冻结EXPERIMENT_CONFIG读取对应物理定义。

以D60为预测起点，预期：

```text
T0:
    position_at_D60 = (9.2, 10.0)
    velocity = (0.4, 0.0)

T1:
    position_at_D60 = (9.0, 10.0)
    velocity = (0.6, 0.0)
```

T0和T1均使用原实际外生运动定义。

不得修改公开公告或真实D60控制belief。

特别是T1初始控制belief仍然来自原合法公开信息，而不是直接获得上述真实外生运动。

真实外生运动仅用于本次事后MODEL物理轨迹生成。

禁止回流至：

- 原N1事前决策。
- 原R或R-CV。
- 候选生成。
- 任何新增算法选择。

不复制或回放ACTUAL未来观测流。

未来MODEL观测必须根据本次候选自身的模拟物理状态独立生成。

## 7. 保持原执行语义

使用冻结BLVF及原MODEL Branch。

仅提交原S候选。

D80、D100：

- 合法消费本分支生成的观测反馈。
- 保持当前有效Assignment。
- 不进行主动重新分配。

自然完成及释放资源继续遵循原规则。

D120统一结束。

不得使用会调用未来原R的默认完整Branch.run路径。

继续保持：

```text
change_cost = 0.0
```

复用已验证的任务局部ECON-NOC严格schema适配。

仅允许局部替换费用常量，保留原校验约束，作用域退出后恢复。

不修改任何生产文件，不取消连续服务重置或其他经济机制。

## 8. 必须保存的归因结果

令本次新增评价：

```text
X = V_MATCHED_WORLD_S
```

计算：

```text
E_total    = J_ACTUAL_S - V_N1_W1_S

E_world    = X - V_N1_W1_S

E_residual = J_ACTUAL_S - X
```

核对：

```text
E_total = E_world + E_residual
```

预期原总低估约为：

```text
0.569995679050
```

所有分项均使用有符号量。

可以报告：

```text
world_contribution_ratio = E_world / E_total
```

不将该比例截断在0%至100%。

不预设E_world或E_residual必须为正。

E_world表示冻结评价器在两个外生世界之间的联合价值变化，包含位置、速度与内生反馈的交互作用。

不声称独立识别了位置、速度或反馈的纯因果贡献。

## 9. 三维结果比较

分别报告以下三个维度。

### 9.1 服务机制恢复

对照原案例I实际S：

| 项目 | 原ACTUAL |
|---|---|
| T0撤回时进度损失 | 0.15秒 |
| T1早期G/Q服务 | 存在 |
| T1服务中断 | D74 |
| 中断前连续进度 | 0.65秒 |
| 中断原因 | GEOMETRY_INVALID |
| 中断时Q | PASS |
| 后续G/Q恢复 | D93 |
| T1完成 | D114 |
| T0完成 | 否 |

报告本次MODEL对应结果及差异。

事件口径须考虑MODEL与ACTUAL记录格式差异，按科学语义对齐，不要求原始事件命名完全一致。

保存D80、D100关键反馈更新及服务时钟变化。

可利用轨迹计算最大连续服务进度及服务不足量。

任务完成后时钟释放不得误解释为最大进度为零。

### 9.2 经济价值恢复

逐项比较：

```text
completion
flow
late
effort
terminal
change_cost
net
```

报告本次MODEL值、原ACTUAL值及各项残差。

确认统一D60—D120全任务经济口径。

净值接近但分项误差相互抵消时，必须明确说明。

### 9.3 决策意义恢复

计算：

```text
D_K = X - V_N1_W1_K

D_M = X - V_N1_W1_M
```

并比较X与原ACTUAL K价值。

原冻结K/M中的最高值约为：

```text
-0.322519231059
```

若X严格超过该值，则说明仅替换S评分时，SWITCH能够超过原冻结K/M评分。

原世界变更贡献跨越该排序阈值所需的变化约为：

```text
0.390020762998
```

约为原总价值低估的68.4%。

该比例仅为本案例单格替换排序阈值的数学解释。

不得作为强制科学验收阈值或新的算法决策参数。

如果数值接近并列，报告实际差值及原确定性并列口径。

本结果不是完整同世界N1决策，因为K/M未在新世界中重新评价。

不得据此宣称已经验证修正后的N1算法。

## 10. 科学结果解释

允许出现以下任何结果。

### A：基本恢复

服务完成、关键事件及经济价值基本恢复，且单格替换后排序正确。

科学含义：

参考世界失配能够解释本案例的主要预测误差。

BLVF可以作为具有条件性支持的科研评价工具保留。

但不建立单参考N1的可靠性。

### B：部分恢复

例如：

恢复正确排序，但存在服务时间、事件或经济残差；或者部分价值误差得到解释，但排序仍未恢复。

科学含义：

分别记录世界变更贡献及同世界残差。

不得将部分恢复夸大为完整验证。

### C：未恢复关键机制

仍不能恢复实际完成状态或相对价值关系。

科学含义：

同世界评价残差可能具有实质决策意义。

作为有效负面科学结果保存。

不自动修复评价器，不自动追加其他诊断。

### D：实施阻断

无法可信恢复D60初态，信息隔离失败，候选身份错误，或者执行语义不一致。

不将无效实施结果解释为BLVF科学失败。

保存具体阻断证据并停止。

三个结果维度分别评价，不要求通过复杂量化验收阈值。

合法执行后获得负面科学结果，同样可以正常完成科研任务。

## 11. 科学启动硬上限

```text
MODEL_CELLS_STARTED <= 1

PREFIX_RECONSTRUCTIONS_STARTED <= 1

ACTUAL_FUTURE_RUNS_STARTED = 0

R_CALLS = 0

ASSIGNMENT_OPTIMIZATION_CALLS = 0

RCV_SCORES = 0

HF_EXTRA = 0

K_MATCHED_EXTRA = 0

M_MATCHED_EXTRA = 0

CASE_II_EXTRA = 0

POSITION_ONLY_ABLATION = 0

VELOCITY_ONLY_ABLATION = 0

NEW_CASES = 0

PARAMETER_SWEEPS = 0

AUTOMATIC_RETRIES = 0
```

所有启动失败均计入对应上限。

路径A成功时不启动路径B。

禁止利用未使用的计算额度开展其他科研单元。

## 12. 独立资源预算

负责人批准：

```text
CUMULATIVE_CPU_LIMIT_SECONDS = 120

CUMULATIVE_WALL_LIMIT_SECONDS = 900

CUMULATIVE_CONTROLLED_LOGICAL_WRITE_LIMIT_BYTES = 134217728
```

累计受控逻辑写入上限为128 MiB。

预算包含必要的局部实施准备、状态核查、可选前缀重建、唯一MODEL、失败证据保存及最终分析报告。

尽可能从准备阶段开始记录。

需要单独记录：

- 实际采用路径A还是B。
- 前缀重建启动次数。
- MODEL启动及有效次数。
- ACTUAL前缀观测WLS。
- MODEL解析估计。
- MODEL观测非线性WLS。
- 底层solver调用。
- 原R及Assignment调用。
- 已记录CPU、墙钟及累计受控逻辑写入。

预留停止及证据保存资源。

已监测预算触限时停止新增科学计算。

未能完整计量的资源如实登记UNKNOWN或INCOMPLETE。

不得把未知消耗记为零，不得为资源计量重跑科学单元。

不开发新的通用资源监督框架。

## 13. 有限验收原则

BLOCKER：

- 原D60必要初态无法可信恢复。
- 真实隐藏状态污染控制belief。
- 错误候选。
- 错误经济配置。
- 错误MODEL执行语义。
- 其他破坏核心科学不变量的问题。

LIMITATION：

- 位置与速度贡献无法独立区分。
- 合法同世界评价仍存在残差。
- 完整资源会计未建立。
- 非关键历史记录无法恢复。

OPTIONAL：

- 更丰富的图表。
- 额外解释指标。
- 非必要轨迹可视化。

科学验收不要求BLVF必须恢复实际结果。

不得为了使结果由负转正而修改代码、参数或再次执行。

## 14. 建议输出

新任务目录内保存必要证据：

```text
FINAL_SPECIFICATION.md
OWNER_AUTHORIZATION.md
SOURCE_IDENTITIES.json
STATE_RECOVERY_RECEIPT.json
MATCHED_WORLD.json
MATCHED_S_RAW.json
ATTRIBUTION_ANALYSIS.json
RESOURCE_RECEIPT.json
EXECUTION_STATUS.json
N1_SWITCH_FAILURE_ATTRIBUTION_REPORT.md
```

文件名可以根据现有规范作必要调整。

不需要重复复制大量历史原始文件。

保证新结果能够追溯至冻结历史证据。

最终报告至少提供：

1. 实际执行状态。
2. 路径A/B及D60状态恢复依据。
3. 唯一MODEL的实际结果。
4. 原N1预测、同世界评价、原ACTUAL三者比较。
5. 总误差、世界变更贡献及同世界残差。
6. G/Q及连续服务关键事件比较。
7. 经济分项比较。
8. 相对于原冻结K/M的单格替换排序。
9. 实际资源消耗及计量限制。
10. 新增文件位置、提交身份及历史资产保护情况。

分别登记：

```text
IMPLEMENTATION_STATUS
SCIENTIFIC_RESULT_STATUS
SERVICE_MECHANISM_RECOVERY
ECONOMIC_VALUE_RECOVERY
SINGLE_CELL_RANKING_RECOVERY
REFERENCE_WORLD_CONTRIBUTION
MATCHED_WORLD_RESIDUAL
RESOURCE_ACCOUNTING
RESOURCE_COMPLIANCE
INDEPENDENT_ACCEPTANCE
PRODUCTION_ADMISSION
```

完成后独立验收仍为PENDING，生产准入仍为BLOCKED。

## 15. 最终停止要求

本任务是当前预测研究阶段的止损性检查。

无论科学结果为正、为负或部分恢复，完成这一格之后停止。

不启动Attempt 002。

不恢复BLVF专项修复。

不扩大N1验证。

不开发N1/R-CV混合算法。

不启动信息获取、不确定性优化或新运动估计研究。

保存完整实际结果及资源回执，提交负责人，由主研员分析、独立审查员审核、负责人决定后续科研方向。

本指令已获得正式授权，请直接在限定范围内执行。
