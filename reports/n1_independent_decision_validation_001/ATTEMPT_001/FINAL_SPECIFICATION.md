# Codex正式科研执行指令

# N1_INDEPENDENT_DECISION_VALIDATION_001

## V1.0 FINAL SPECIFICATION — OWNER AUTHORIZED

## 1. 正式授权及任务状态

项目仓库：

`lyc0212/dynamic_member_coalition_core`

负责人已经明确批准：

1. N1 V1.0最终科研规范。
2. 独立审查员提出的R1—R5全部澄清。
3. 两个新案例及其具体参数。
4. 本任务科学启动规模及独立资源预算。
5. Codex实施并执行本轮科研验证。

当前状态：

```text
TASK = N1_INDEPENDENT_DECISION_VALIDATION_001
SPECIFICATION = V1.0_FINAL_SPECIFICATION
INDEPENDENT_DESIGN_REVIEW = APPROVED_WITH_TARGETED_CLARIFICATIONS
MAIN_RESEARCHER_CONFIRMATION = CONFIRMED
OWNER_SPECIFICATION_APPROVAL = APPROVED
OWNER_RESOURCE_APPROVAL = APPROVED
EXECUTION_AUTHORIZATION = GRANTED
ADDITIONAL_REVIEW_REQUIRED = NO
PRODUCTION_ADMISSION = BLOCKED
```

不需要再次申请执行授权，不需要重新审核总体科研方案。

此前任务：

```text
CCVD_INITIAL_DECISION_VALIDATION_001 = CLOSED
FINAL_INDEPENDENT_SCIENTIFIC_ACCEPTANCE = ACCEPTED_WITH_LIMITATIONS
ATTEMPT_003_REQUIRED = NO
HISTORICAL_RERUN_REQUIRED = NO
```

不得重新运行旧任务，不得重新研究BLVF专项问题，不得恢复CCVD保守多情景研究。

## 2. 本次科研目标

本轮研究的主要对象为N1单运动情景闭环联盟价值决策。

需要回答三个科学问题：

- H1：当真实目标运动与事前参考运动不一致时，N1是否仍能改善实际联盟选择？
- H2：相比采用相同参考物理轨迹的简单确定性等效方法R-CV，N1是否具有额外实际决策价值？
- H3：在真实连续服务历史条件下，N1能否合理处理KEEP、SWITCH及MEMBER_CHANGE之间的选择？

本轮不预设N1必须取得正面结果。

如果更简单的R-CV已经取得有效实际决策结果，则支持科研进一步剪枝。

如果两种方法均失败，则如实报告，不自动修复、调参或追加实验。

本任务仅验证固定窗口首动作决策，不验证完整动态多阶段在线调度性能。

## 3. 参考代码及历史资产保护

设计参考提交：

`d32a6c73c7447ea9708614ea9265e9e0840658ab`

执行前记录实际HEAD、分支及工作树状态。

主要复用路径：

```text
reports/ccvd_initial_decision_validation_001/ATTEMPT_002/ccvd_entry.py

reports/ccvd_initial_decision_validation_001/ATTEMPT_002/EXPERIMENT_CONFIG.json

reports/stfbs_lite_fb_blvf_initial_validation_001/blvf.py

research/non_oracle/policy.py

research/non_oracle/belief.py

research/non_oracle/environment.py

research/non_oracle/stfbs_d1a_model.py

research/non_oracle/stfbs_lite_live_cut.py

research/non_oracle/stfbs_lite_real_cut_to_model.py

research/information_service_online/execution.py

research/information_service_online/evaluator.py
```

冻结BLVF预期SHA256：

```text
204fc231bf78004c33daf151983d751685666da75ed9e9b911abb83854c7365e
```

允许参考Attempt 002的成功实现，但不得直接运行历史执行入口，也不得导入会启动历史实验的模块。

建立独立任务局部执行入口。

建议输出目录：

```text
reports/n1_independent_decision_validation_001/
    ATTEMPT_001/
```

新任务使用独立Attempt编号，与历史CCVD Attempt 001、002无关。

保护要求：

- 不修改生产核心源码。
- 不修改生产默认配置。
- 不修改冻结BLVF。
- 不覆盖旧任务的失败或成功证据。
- 不重置、覆盖或删除已有用户工作。
- 不通过修改通用框架来解决本轮局部研究适配问题。

如果局部复用无法实现关键科学语义，报告具体实施阻断并停止，不自行开展通用重构。

## 4. ECON-NOC配置

统一采用：

```text
change_cost = 0.0
```

沿用Attempt 002已经成功使用的任务局部严格schema适配。

仅允许在本任务进程作用域内将费用常量从0.01替换为0.0。

要求：

- 继续使用原schema校验函数。
- 保留其他全部schema约束。
- 不伪造生产schema身份或认证状态。
- 正常退出及异常退出均恢复原schema引用。
- 不修改生产配置文件。

成员变化引起的连续服务重置、完成奖励、未完成惩罚、时间成本及控制成本仍然有效。

不得取消任何其他经济或物理机制。

## 5. 公共实验配置

除本指令明确修改的字段外，继承Attempt 002配置及原物理、控制、估计和服务规则。

主要配置如下：

| 参数 | 数值 |
|---|---:|
| robots | 3 |
| task_count | 2 |
| side | 20 |
| step_dt | 0.05 |
| stage_dt | 3 |
| max_stages | 2 |
| max_speed | 3 |
| travel_gain | 1 |
| observation_radius | 0.6 |
| observation_tolerance | 0.15 |
| flow_weight | 0.1 |
| late_weight | 0.3 |
| control_weight | 0.02 |
| unfinished_weight | 2 |
| control_reference | 10 |
| change_cost | 0 |
| capture_mode | stepwise_service |
| geometry_mode | angular_standoff_v1 |
| sensor sigma | 0.02 |
| actual angle perturbation | 0 |
| D60决策时刻 | 3秒 |
| D120终端时刻 | 6秒 |

任务定义：

| 参数 | T0 | T1 |
|---|---:|---:|
| birth | 0 | 3 |
| weight | 1 | 1.5 |
| deadline | 2 | 5 |
| required_robots | 2 | 2 |
| service_duration | 2.25 | 1.05 |

真实物理运动均采用确定性CV。

可以继续复用原continuous_turn物理接口，以零角速度表达CV。

注意：案例II的0.25 rad是初始速度方向，不是随时间持续转向的角速度。

不增加噪声、随机扰动、任务数量或机器人数量。

## 6. 冻结两个新案例

### 6.1 共同T0定义

真实出生位置：

```text
(8.0, 10.0)
```

真实速度：

```text
(0.4, 0.0)
```

公开公告位置：

```text
(8.45, 10.0)
```

公开控制速度先验：

```text
(0.0, 0.0)
```

公开位置误差设计界：

```text
0.5
```

公开速度上界：

```text
0.8
```

T0真实物理定义仅供ACTUAL执行器使用，不得作为T0事前参考运动的直接输入。

### 6.2 案例I

```text
CASE_ID = I_NEAR_SERVICE_HISTORY
```

D0机器人初始位置：

```text
U0 = (8.874264, 9.575736)
U1 = (8.874264, 10.424264)
U2 = (9.6, 9.6)
```

T1公开出生位置：

```text
(9.45, 10.0)
```

T1真实出生位置：

```text
(9.0, 10.0)
```

T1真实速度：

```text
(0.6, 0.0)
```

T1公开控制速度先验仍为：

```text
(0.0, 0.0)
```

研究作用：真实正服务进度形成机会、原联盟保持价值及新任务竞争。

不预设KEEP或SWITCH获胜。

### 6.3 案例II

```text
CASE_ID = II_MEMBER_GEOMETRY_IMBALANCE
```

D0机器人初始位置：

```text
U0 = (6.874264, 9.575736)
U1 = (8.874264, 10.424264)
U2 = (9.6, 9.6)
```

T1公开出生位置：

```text
(9.8, 10.3)
```

T1真实出生位置：

```text
(9.8, 10.1)
```

T1真实速度大小：

```text
0.8
```

T1真实速度方向：

```text
0.25 rad
```

实际速度向量：

```text
(0.8*cos(0.25), 0.8*sin(0.25))
```

T1公开控制速度先验仍为：

```text
(0.0, 0.0)
```

研究作用：原成员几何不平衡、替代成员竞争及更明显的运动参考失配。

不预设MEMBER_CHANGE获胜。

### 6.4 案例冻结原则

两个案例均按上述参数执行。

不得根据前缀结果、MODEL预测或ACTUAL结果修改：

- 机器人位置。
- 目标出生位置。
- 真实目标速度及方向。
- 公开公告。
- 参考运动。
- 服务时长。
- 几何容差。
- 经济参数。
- 决策时刻。

不得增加第三个案例。

两个案例是预声明受控新案例，不是随机独立样本，不得在报告中将其描述为严格盲测或统计泛化实验。

## 7. 延迟服务启动共同前缀

两个案例采用相同受控前缀。

D0：

```text
U0 = IDLE
U1 = IDLE
U2 = IDLE
```

D20：

```text
U0 -> T0 / dual_neg45
U1 -> T0 / dual_pos45
U2 -> IDLE
```

D40：

继续保持上述合法分配。

D60：

合法完成反馈消费后，冻结：

```text
POST_FREEZE_PRE_ASSIGNMENT
```

尚未提交本轮首动作。

受控前缀不得调用原R自主生成分配。

必须使用真实执行机制产生：

- 机器人位置。
- 合法观测及反馈。
- 控制belief。
- G/Q服务历史。
- 连续服务时钟。
- 当前Assignment。
- 共同前缀经济账本。

不允许人工构造正服务进度，不允许从旧任务复制D60快照。

理论上D20至D60最多形成2秒连续服务，低于T0的2.25秒完成要求。

但实际正进度是否形成，完全以真实执行结果为准。

正进度为零不构成工程失败，也不是重新运行或修改案例的理由。

若合法当前联盟不存在，记录适用范围限制，不制造KEEP候选。

## 8. D60合法信息边界与T0参考运动

继续采用已验证的公开状态及consumer映射路径。

事前规划只允许访问：

- 合法公开policy view。
- 当前机器人位置。
- 当前Assignment。
- 公开任务公告及参数。
- 公开服务历史。
- 合法已查询观测slot。
- 合法已接受、待消费及已消费观测历史。
- 原控制belief。

consumer种子继续使用此前冻结白名单。

T0参考运动由合法接受位置历史构造。

选择最近两个满足原差分间隔要求的合法接受位置，至少间隔5 tick。

计算：

```text
v0 = (pb - pa) / ((kb - ka) * DT)
p0_at_D60 = pb + v0 * ((60 - kb) * DT)
```

沿用此前T0必要历史相容性检查，包括公开出生位置支持、速度支持、适用航向支持、合法历史方位角、当前合法观测及已有公开G/Q服务端点。

不得从ACTUAL隐藏目标定义、私有位置或私有速度直接补齐参考运动。

不得扩大既有容差。

核查历史观测和G/Q时，仅允许使用已经合法公开或映射白名单中可用的数据，不因实现便利读取额外隐藏物理状态。

如果无法建立必要相容性，记录该案例的具体限制并停止其相关评价。

不恢复通用逆求解器，不增加新的运动估计研究。

## 9. 冻结参考世界

共同公开研究运动支持：

```text
speed_support = [0.4, 0.8]
heading_support = [-0.5, 0.5]
```

T0：

使用第8节构造的同一合法CV见证。

T1：

从各自案例D60公开公告读取出生位置。

不得硬编码历史Attempt 002的T1位置。

两个正式参考世界：

| 世界 | T0 | T1 |
|---|---|---|
| W0 | 合法CV见证 | 公开公告位置，速度(0,0) |
| W1 | 相同合法CV见证 | 相同公开公告位置，速度(0.4,0) |

W1参考速度采用公开速度支持下界，航向采用公开航向支持中心。

不得根据隐藏真实速度修改参考情景。

不生成W2。

不进行多情景搜索、概率估计或保守增量优化。

N1的参考物理世界与模拟机器人原合法控制belief必须保持分离。

## 10. 候选生成及原R基线

D60原R基于未修改的合法公开状态调用一次。

保存完整候选目录、名义评分及原R推荐。

采用与CCVD Attempt 002相同的候选代表定义：

K：

完整保持当前任务、成员、角色及空闲身份。

S：

保持当前双成员集合，切换至另一活动任务。从合法角色排列中选择原R名义最佳代表。

M：

保持当前任务，更换至少一名联盟成员。从合法候选中选择原R名义最佳代表。

仅交换角色而未改变成员，不属于M。

各代表由原R原始评分选择，而不是由R-CV重新生成。

保留：

```text
R
R_common
K
S
M
```

其中R_common由原R已保存的完整候选目录在共同K/S/M集合中选择，不需要重复运行原R或Assignment。

R_EXTRA：

如果原R完整推荐不属于共同K/S/M集合，则只作为额外ACTUAL基线。

R_EXTRA不进入N0、N1或R-CV事前评价矩阵。

R_EXTRA可能是合法全空闲动作，不应将其认定为非法。

所有候选按完整Assignment身份去重。

并列规则继续采用确定性完整身份顺序；机器人ID顺序、idle哨兵及角色身份保持一致。

不存在合法候选类别时记录缺失，不制造候选。

## 11. 五种正式比较方法及共同原R基线

正式方法：

```text
R
R-CV
N0
N1
K
```

同时报告派生共同候选基线R_common。

### R

原完整目录推荐。

### R_common

利用原R已保存评分，从共同K/S/M集合选择。

### N0

```text
argmax_a V(a, W0)
```

采用BLVF闭环评价。

### N1

```text
argmax_a V(a, W1)
```

采用BLVF闭环评价。

### R-CV

采用与N1相同参考物理CV轨迹的确定性等效评价。

具体实施见第12节。

### K

直接保持现有合法联盟。

不计算CCVD保守增量，不设置额外风险权重或人为保持阈值。

N0、N1及R-CV按各自全任务净值最大化选择；价值并列时采用确定性Assignment身份顺序。

## 12. R-CV任务局部实现

本轮最重要的新增比较对象。

R-CV不需要重新实现确定性等效价值评价器。

通过任务局部作用域替换`research.non_oracle.policy`实际引用的`trajectory`函数，复用原`policy.evaluate()`。

局部轨迹定义：

```text
p_j(k) = p_hat_j_at_D60 + (k - 60) * DT * v_hat_j
v_j(k) = v_hat_j
```

其中位置、速度完全来自共同W1。

通过真实belief的`target_id`识别对应参考轨迹。

要求：

1. 不修改真实belief记录。
2. 不伪造`PRIOR_ONLY`等belief身份。
3. 不修改生产`belief.py`或`policy.py`。
4. 不直接修改速度字段以规避原传播截断。
5. 局部预测轨迹覆盖D60—D120，不受原1秒传播截断影响。
6. 保留原G/Q、控制、服务历史继承及经济评分机制。
7. 保留D60合法观测及已有服务端点。
8. 不模拟动作相关未来反馈。
9. 不重新运行Assignment。
10. 正常或异常退出后恢复原trajectory函数引用。

R-CV作用域不能影响：

- 原R基线评价。
- N0/N1 MODEL执行。
- ACTUAL实际控制。
- 合法控制belief及观测历史。

其科学含义为：预测物理轨迹与预测控制信息共享同一公开参考运动。

因此R-CV是简单确定性等效参考方法，而不是N1的严格单因素反馈消融。

### 12.1 全任务经济价值

`policy.evaluate()`提供候选被服务任务价值及未服务基准。

将其重组为：

```text
V_RCV(a)
    = served_target_absolute_value
    + other_unserved_target_value
```

或：

```text
V_RCV(a)
    = common_reference_unserved_baseline
    + candidate_incremental_value
```

共同未服务基准必须采用W1参考世界和同一D60—D120经济口径。

使用原经济公式及停止规则。

本轮目标远离逃逸边界，原未服务基准的传播有效期差异预计不会影响结果；实际实现仍需核对该条件。

不得将单任务收益直接与N1全任务收益进行比较。

不增加额外候选评分来构造未服务基准，可以直接按原经济公式计算。

### 12.2 R-CV调用计数

每个案例最多调用三次`policy.evaluate()`：

```text
K
S
M
```

两个案例累计最多6次。

每次评分的WLS及底层solver调用计入实际资源账本。

R-CV评分不计作BLVF MODEL格，但必须独立计数。

## 13. BLVF闭环评价与统一Hold

复用冻结BLVF解析估计及Attempt 002成功的MODEL Branch固定动作执行路径。

不得直接使用会在D80、D100调用原R的默认`Branch.run()`。

对每个合法K/S/M候选执行：

```text
W0
W1
```

每个案例最多6个MODEL单元。

每个MODEL单元：

- 从相同合法D60状态初始化。
- 使用共同consumer历史。
- 提交冻结首动作。
- 由候选自身假设物理世界生成未来观测。
- 执行原反馈、控制、G/Q及连续服务规则。
- D80、D100合法消费反馈。
- 保持当前有效分配，不主动重新分配。
- 自然完成或逃逸后按原规则释放资源。
- D120统一终止。

禁止未来R及Assignment优化调用。

禁止使用ACTUAL未来观测回放。

禁止使用其他候选未来观测。

不得为了结果更好修改BLVF或原consumer数学。

本轮不授权HF备选矩阵或额外HF参考检查。

## 14. 事前决策冻结

在执行ACTUAL候选未来之前，必须保存：

```text
PUBLIC_D60
CANDIDATES
R_CATALOGUE
R_common
T0_WITNESS
WORLDS
MODEL_VALUES
R_CV_VALUES
DECISION_FREEZE
```

DECISION_FREEZE至少记录：

- 公开状态身份。
- 候选完整Assignment身份。
- W0/W1参考物理世界。
- 原R及R_common选择。
- N0选择。
- N1选择。
- R-CV选择。
- KEEP选择。
- 数值并列处理方式。

每个案例独立完成事前冻结后，方可执行其ACTUAL候选。

案例II的参考规则及全部物理参数必须在案例I产生科学结果之前已经冻结。

不允许利用案例I真实结果调整案例II。

## 15. ACTUAL实际执行

ACTUAL候选集合为：

```text
unique(K, S, M, R)
```

每个案例最多4次。

相同Assignment身份在不同方法之间复用同一实际结果，不按方法名称重复运行。

ACTUAL必须使用相同案例真实物理世界、共同前缀及合法初始控制信息。

可以复用Attempt 002成功的从D0重建共同前缀路径。

每次重建后核对：

- 合法D60公开状态一致。
- 当前Assignment一致。
- 连续服务历史一致。
- 共同前缀经济账本一致。

D60提交对应冻结候选。

D80、D100仅合法反馈消费及Hold。

不得继续调用原R，不得运行新的Assignment优化。

自然释放按原机制处理。

ACTUAL控制器不因为R-CV或N1的方法名称获得额外参考速度信息。

主要评价窗口为D60—D120。

统一计算全任务净价值，排除D60以前共同前缀沉没收益。

保留各ACTUAL候选自己的原始轨迹、反馈、G/Q服务及经济分项。

## 16. 科学计算规模硬上限

本任务独立授权规模：

| 计算类型 | 每个案例上限 | 累计硬上限 |
|---|---:|---:|
| 独立前缀启动 | 1 | 2 |
| N0 MODEL | 3 | 6 |
| N1 MODEL | 3 | 6 |
| MODEL合计 | 6 | 12 |
| R-CV候选评分 | 3 | 6 |
| ACTUAL候选 | 4 | 8 |

原R：

每个有效案例D60最多调用一次。

受控前缀及Hold不得调用原R。

ACTUAL内部共同前缀重建：

最多8次，包含在相应ACTUAL候选执行内，不是额外独立科学前缀。

分别记录：

```text
INDEPENDENT_PREFIX_RUNS_STARTED
ACTUAL_PREFIX_RECONSTRUCTIONS_STARTED
MODEL_CELLS_STARTED
MODEL_CELLS_VALID
RCV_SCORES_STARTED
RCV_SCORES_VALID
ACTUAL_RUNS_STARTED
ACTUAL_RUNS_VALID
```

失败启动计入对应上限。

不自动重试。

不使用剩余额度开展额外诊断。

明确禁止：

```text
MATCHED_WORLD_EXTRA = 0
HF_EXTRA = 0
W2_EXTRA = 0
PARAMETER_SWEEP = 0
EXTRA_CASES = 0
HISTORICAL_RERUN = 0
```

## 17. 独立资源预算

负责人已批准：

```text
CUMULATIVE_CPU_LIMIT_SECONDS = 2400
CUMULATIVE_WALL_LIMIT_SECONDS = 5400
CUMULATIVE_CONTROLLED_LOGICAL_WRITE_LIMIT_BYTES = 2147483648
```

这是本任务独立累计预算，不与历史CCVD预算混用。

资源范围包括：

- 必要实施准备及接口检查。
- 独立前缀。
- ACTUAL内部前缀重建。
- 原R及R-CV评分。
- MODEL及ACTUAL执行。
- 失败调用。
- 原始结果保存。
- 分析及报告生成。

采用必要的任务级资源计量。

尽可能从本任务准备阶段开始记录资源，并记录实际覆盖范围。

实际调用统计至少区分：

- 原R调用。
- Assignment优化调用。
- R-CV候选评分。
- BLVF解析估计。
- MODEL观测WLS。
- ACTUAL观测WLS。
- 原R评分WLS。
- R-CV评分WLS。
- 底层非线性solver调用。

不得将R-CV评分WLS归入ACTUAL WLS。

不得以最终目录大小替代累计逻辑写入。

为终止、失败保存及最终报告预留必要资源余量。

任何已监测预算触限时停止新的科学计算。

无法完整计量的资源项登记为UNKNOWN或INCOMPLETE，并注明覆盖范围。

不得将未知资源消耗记为零，不得因资源记录不完整而重跑科研单元。

不要求开发复杂的通用资源监督系统。

## 18. 执行顺序及停止规则

固定顺序：

```text
必要局部实施及接口核查
    ↓
案例I共同前缀
    ↓
案例I候选及参考世界
    ↓
案例I原R / R-CV / N0 / N1评价与选择冻结
    ↓
案例I ACTUAL候选执行
    ↓
案例II共同前缀
    ↓
案例II候选及参考世界
    ↓
案例II原R / R-CV / N0 / N1评价与选择冻结
    ↓
案例II ACTUAL候选执行
    ↓
联合科学分析及最终报告
    ↓
停止
```

如果案例I未形成正进度、没有有价值的成员重构机会，或科学结果不利于N1，仍按冻结规范开展案例II。

如果出现共有实施错误、关键科学不变量被破坏、信息隔离失败或资源触限，停止新的科学计算。

个别案例存在明确的适用范围不足时，应与共有实施阻断区分；只在不影响其他案例科学有效性的情况下继续。

保存已经取得的全部有效证据和失败证据。

不自动修改算法，不自动启动Attempt 002。

## 19. 必须报告的实际科学结果

逐案例报告：

### 19.1 决策初态

- 当前联盟身份。
- D60实际已有连续服务进度。
- T0合法参考运动见证。
- 合法K/S/M代表身份。
- 当前控制belief。
- 原R完整及共同集合推荐。

### 19.2 事前预测矩阵

| 动作 | 原R | R-CV | N0/W0 | N1/W1 |
|---|---:|---:|---:|---:|
| K |  |  |  |  |
| S |  |  |  |  |
| M |  |  |  |  |

全部统一为D60—D120全任务经济口径。

R_EXTRA如存在，仅报告原R评分及ACTUAL结果。

缺失单元不得虚构数据。

### 19.3 ACTUAL价值矩阵

| 动作 | 实际净值 | T0完成 | T1完成 | 完成时间 | 进度损失 |
|---|---:|---|---|---|---:|
| K |  |  |  |  |  |
| S |  |  |  |  |  |
| M |  |  |  |  |  |
| R_EXTRA |  |  |  |  |  |

同时保存实际经济分项、G/Q中断及恢复、连续服务进度及反馈更新。

### 19.4 方法实际选择

分别报告：

```text
R
R_common
R-CV
N0
N1
K
```

每种方法所选动作及对应ACTUAL结果。

不得将方法名称数量等同于独立物理执行次数。

## 20. 科学收益指标

逐案例计算：

```text
G_total       = J(N1) - J(R)
G_common      = J(N1) - J(R_common)
G_motion      = J(N1) - J(N0)
G_closed      = J(N1) - J(R-CV)
G_active      = J(N1) - J(K)
G_eval_common = J(N0) - J(R_common)
G_RCV         = J(R-CV) - J(R_common)
G_M           = J(M) - J(K)
```

这些均由同一案例已保存ACTUAL结果计算，不增加科学单元。

上述差值属于方法之间实际收益比较，不是严格独立因果效应。

重点指标：

```text
G_closed
```

用于判断闭环价值评价相对于简单R-CV是否产生额外实际决策价值。

同时报告共同K/S/M候选内实际最优及有限候选遗憾。

若R_EXTRA存在，再报告共同候选与R_EXTRA并集的实际最优及遗憾。

不得将有限候选最优称为全目录最优或全局最优。

原R若选择共同集合之外的R_EXTRA，不得把其相对于共同集合最优的差值描述为共同集合内部非负遗憾。

## 21. H3正服务进度分析

正服务进度本身不足以建立完整H3。

区分：

1. 零进度下成员重构恢复服务。
2. 正进度下KEEP持续合格并完成任务。
3. 正进度下KEEP随后中断并丢失进度。
4. 正进度下M重置已有进度但恢复完成机会。
5. 正进度下SWITCH放弃原任务并获得更高实际收益。

若D60已有连续服务进度q，KEEP随后始终合格，且K/M均完成T0、T1贡献相同，则参考此前已接受的条件性解析界：

```text
J(K) - J(M) >= q/60 - 0.0018
```

当：

```text
q > 0.108秒
```

上述限定条件成立时，KEEP具有严格经济优势。

离散时间下q达到0.15秒满足该充分条件。

该尺度仅用于科学结果解释。

不得将0.108或0.15设置为算法决策阈值。

若KEEP发生进度重置，则不适用上述保持进度推论。

两个案例均未形成正进度时，登记：

```text
POSITIVE_PROGRESS_TRADEOFF = NOT_ESTABLISHED
```

不改变案例，不追加实验。

## 22. 科研方向判断

最终报告按照以下预声明原则解释结果：

| 实际结果 | 科研判断 |
|---|---|
| N1有效，R-CV错误 | 支持闭环评价具有额外价值 |
| N1与R-CV均有效且改善原R | 支持优先考虑简单R-CV |
| N1与R-CV均错误 | 两种机制均缺乏有效性支持 |
| 所有方法均正确且结果相同 | 案例不足以区分方法必要性 |
| 所有方法均错误 | 预测或候选机制仍可能不足 |
| 两种方法各有优势 | 保留不确定判断，比较实际机制及成本 |
| N1拒绝实际有价值的SWITCH | 记录运动参考导致的反向决策偏差 |
| N1产生实质负收益 | 记录负面结果，考虑暂停路线 |

不要求两个案例均成功。

不要求三个动作分别获胜。

不要求MEMBER_CHANGE一定优于KEEP。

R-CV与N1结果相同，不自动解释为R-CV已经足够；必须同时判断两者是否取得真实有效决策结果。

本轮不进行额外matched-world检查。

若无法区分参考世界误差与评价器残余误差，登记：

```text
ATTRIBUTION_UNRESOLVED
```

不自动启动新的诊断任务。

最终科研方向由主研员分析、独立审查及负责人决定。

Codex不得自行宣布采用新的最终算法。

## 23. 输出及证据保存

建议保存：

```text
FINAL_SPECIFICATION.md
OWNER_AUTHORIZATION.md
EXPERIMENT_CONFIG.json
SOURCE_IDENTITIES.json
SCHEMA_ADAPTATION.json
EXECUTION_STATUS.json
RESOURCE_RECEIPT.json
SCIENTIFIC_ANALYSIS.json
N1_INDEPENDENT_RESEARCH_REPORT.md
```

每个案例分别保存必要的：

```text
PREFIX_RECEIPT.json
PUBLIC_D60.json
MAPPING_RECEIPT.json
R_CATALOGUE.json
CANDIDATES.json
T0_WITNESS.json
WORLDS.json
R_CV_VALUES.json
MODEL_VALUES.json
DECISION_FREEZE.json
ACTUAL_VALUES.json
```

及MODEL、ACTUAL原始科学轨迹。

不要求严格遵循文件名形式，也不要求重复保存大量相同数据，但必须能够追溯科学结论及事前冻结证据。

失败时保留具体异常及已经产生的科学结果。

最终资源回执明确说明完整计量范围及限制。

## 24. 最终报告必须明确区分

```text
IMPLEMENTATION_STATUS
SCIENTIFIC_RESULT_STATUS
REFERENCE_MOTION_APPLICABILITY
CLOSED_LOOP_ADDITIONAL_VALUE
ACTIVE_MEMBER_RECONFIGURATION
POSITIVE_PROGRESS_TRADEOFF
RESOURCE_ACCOUNTING
RESOURCE_COMPLIANCE
INDEPENDENT_ACCEPTANCE
GENERALIZATION
PAPER_NOVELTY
PRODUCTION_ADMISSION
```

可能的任务执行状态：

```text
COMPLETED
COMPLETED_WITH_LIMITATIONS
PARTIAL
BLOCKED_NO_VALID_CELLS
RESOURCE_STOP
```

具体状态根据实际执行决定。

没有有效科学单元时不得评价算法有效性。

资源合规未建立时不得宣称完整工程合规。

两个受控新案例即使取得正面结果，也不能直接宣称统计显著性、普遍泛化能力或生产可用性。

独立验收保持PENDING，生产准入保持BLOCKED。

## 25. 最终执行要求

本指令已获得负责人正式授权。

请首先进行必要的只读源码及输入核查，然后直接实施本任务局部入口并执行冻结的两个案例。

不需要为已经批准的科研设计再次提交总体方案审核。

如果发现真实且无法在已授权规范内处理的关键科学问题，报告具体阻断，不擅自改变科研设计。

不要为了追求完整工程体系而增加无明确科研用途的前置项目。

不要为了取得正面结果而更改运动、位置、经济、候选或算法规则。

完成后保存实际结果及资源回执，明确报告局限，并停止。

最终向负责人提供：

1. 实际执行状态及有效科学单元数量。
2. 两个案例的预测及ACTUAL价值矩阵。
3. 六种方法记录（含R_common）的实际选择。
4. H1、H2、H3对应的具体科学证据。
5. N1相对于R-CV的实际收益差。
6. 任务完成及连续服务机制解释。
7. 实际资源消耗、计量覆盖范围及任何实施限制。
8. 新增文件位置、实际提交身份及历史资产保护情况。

不追加任何未经授权的科研计算。

本轮唯一目的，是通过有限真实科学证据确定单运动情景闭环价值决策是否值得保留，以及更简单的R-CV是否已经足够。

立即按授权范围执行。
