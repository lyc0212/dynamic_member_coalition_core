# PSF-001：公开信息未来情景基础及价值筛选机制研究

任务：`STFBS_LITE_FB_PUBLIC_SCENARIO_FOUNDATION_001`。正式规范：PSF-001 V1.1。

执行状态：`STATIC_ANALYSIS_COMPLETED_WITH_LIMITATIONS`。独立科学验收：`PENDING`，本报告不登记ACCEPTED或CLOSED。

本轮已经获得静态科研分析授权。工作范围为五个工作包、一份报告、零新科学执行。BLVF V0.1、H3—H5结果、原L3-B状态及所有历史失败记录保持不变。

## 1. 主要结论及证据口径

1. **原世界库的坐标合法性不等于历史相容性。** 实际100世界中，T0位置不变且速度不变10个，仅速度变化10个，仅位置变化40个，位置及速度同时变化40个。严格继承冻结D60的可信`G=true`服务端点时，80个T0位置扰动世界均违反当前服务几何必要条件。此结论不撤销其原有条件压力测试结果。
2. **其余20个世界不能自动认证为完整历史相容。** 它们通过当前G几何必要检查，但速度历史、观测误差语义、公告模型的约束强度仍需声明。T0速度增至约0.8若被解释为贯穿出生至D60的匀速状态，还与公告出生位置误差假设发生明确冲突。
3. **原MEMBER_CHANGE候选缺少完成任务的基本进入时间。** 新加入的U2距T0标称位置约10.7629，成员变更后服务重置，必须在0.75秒内建立可持续2.25秒的服务。即使允许机器人和目标以最大速度相向运动，其必要距离上界也仅约3.60。这里否定的是这一冻结候选在固定动作及所列速度约束下的连续服务机会，不是否定成员重构这一动作类别。
4. **已有ACTUAL证据支持研究动机，但不是统一鲁棒矩阵。** H3 MODEL HF最优为SWITCH，历史ACTUAL反事实保存结果最优为KEEP，名义SWITCH事后遗憾为0.4175267270800314。但二者外生世界和后续执行语义不同，不能把排序反转直接解释为BLVF误差或作为新的在线Minimax Regret结果。
5. **下一步建议是有限的联合科研设计，并先声明最小假设。** 将“有成员竞争机会的合法决策状态”“统一MODEL—ACTUAL评价语义”“合法有限情景支持”联合设计。当前不建议恢复A1或默认扫描100世界；不把C-Lite作为基础稳健决策验证的强制前置。

### 1.1 状态、版本及现有工作区

本轮只读取得的HEAD为`a30fac2db40aceec58671b3033da3574289c4714`。开始时已有一个未跟踪文件：

`reports/stfbs_lite_fb_blvf_h5_arc_extension_001/BLVF_H5_ARC_FINAL_INDEPENDENT_SCIENTIFIC_ACCEPTANCE.md`

这是此前获准生成的H5关闭登记，本轮保持原样。不能把它描述为已提交的最新关闭commit，也不能把开始时工作区描述为完全干净。H3—H5关闭状态依据负责人裁定及现有关闭文本，不重新开展其科学审核。

本报告采用以下区分：

- **保存事实 / CONFIRMED**：从现有源码或保存字段直接读取。
- **静态推导**：只对保存数据作计数、几何及算术推导，不生成新轨迹、观测或价值。
- **条件结论**：明确列出历史继承、速度或误差假设后才成立。
- **UNRESOLVED / NOT_IDENTIFIABLE**：现有证据或语义不足，不强行认证。
- **科研建议**：未来研究对象，不是执行授权。

### 1.2 主要来源索引

下列链接为实际本地来源；JSON结论另标明字段。源码行号对应本轮读取版本。

| 编号 | 实际来源与核查内容 |
|---|---|
| S01 | [stfbs_lite_worlds.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/stfbs_lite_worlds.py:15)：公开投影；81行`generate_worlds()`；148行`screen_worlds()` |
| S02 | [belief.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/belief.py:7)：`trajectory()`；35行`freeze()`、47行历史参考选择、51行限速 |
| S03 | [environment.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/environment.py:25)：ACTUAL合法决策视图、公告及反馈冻结 |
| S04 | [stfbs_lite_public_adapter.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/stfbs_lite_public_adapter.py:47)：公开Config、belief、服务端点及profile水位投影 |
| S05 | [stfbs_d1a_state.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/stfbs_d1a_state.py:6)：MODEL consumer种子恢复；23行历史raw缓存 |
| S06 | [stfbs_d1a_model.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/stfbs_d1a_model.py:68)：合法MODEL观测、fuse、assign及policy_view |
| S07 | [stfbs_lite_real_cut_to_model.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/stfbs_lite_real_cut_to_model.py:79)：真实cut至MODEL种子及待决依赖 |
| S08 | [config.py](D:/1st/dynamic_member_coalition_core/pursuit_v2/config.py:9)、[observation_geometry.py](D:/1st/dynamic_member_coalition_core/pursuit_v2/observation_geometry.py:35)：Config、角色偏移及G容差 |
| S09 | [pursuit_v2/environment.py](D:/1st/dynamic_member_coalition_core/pursuit_v2/environment.py:50)：ACTUAL连续转向场景的速率/航向约束验证 |
| S10 | [public_quality.py](D:/1st/dynamic_member_coalition_core/research/information_service/public_quality.py:198)：质量评估；254行局部半径proxy公式 |
| S11 | [PUBLIC_INPUT.json](D:/1st/dynamic_member_coalition_core/runs/a2_switch_episode_001/PUBLIC_INPUT.json)、[A1_INFORMATION_BOUNDARY.md](D:/1st/dynamic_member_coalition_core/docs/A1_INFORMATION_BOUNDARY.md:15)：预声明公告及信息边界解释 |
| S12 | [PUBLIC_INPUT_FREEZE.json](D:/1st/dynamic_member_coalition_core/reports/stfbs_lite_h2_h3_extension_005/PUBLIC_INPUT_FREEZE.json)、[WORLD_LIBRARY.json](D:/1st/dynamic_member_coalition_core/reports/stfbs_lite_h2_h3_extension_005/WORLD_LIBRARY.json)、[CANDIDATE_FREEZE.json](D:/1st/dynamic_member_coalition_core/reports/stfbs_lite_h2_h3_extension_005/CANDIDATE_FREEZE.json)、[PROXY_VALUE_TABLE.json](D:/1st/dynamic_member_coalition_core/reports/stfbs_lite_h2_h3_extension_005/PROXY_VALUE_TABLE.json) |
| S13 | [stfbs_lite_candidates.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/stfbs_lite_candidates.py:70)、[a0_plans.py](D:/1st/dynamic_member_coalition_core/scripts/gq_windows/a0_plans.py:8)、[policy.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/policy.py:89)：分类、候选目录、实际A2评分 |
| S14 | [L3-A报告](D:/1st/dynamic_member_coalition_core/reports/stfbs_lite_l3_a_proxy_screening_diagnosis_001/REPORT.md)、同目录`FINAL_REPORT.json`：原筛选及代理风险保存证据 |
| S15 | [SW3后验报告](D:/1st/dynamic_member_coalition_core/reports/a2_prediction_sw3_posthoc_readonly_audit_001/REPORT.md)、同目录`POSTHOC_STATISTICAL_AUDIT.json`；[sw3_public_hypotheses.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/sw3_public_hypotheses.py:134) |
| S16 | [ACTUAL三动作矩阵](D:/1st/dynamic_member_coalition_core/reports/stfbs_lite_actual_full_episode_counterfactual_001_continuation_001/ACTUAL_THREE_ACTION_VALUE_MATRIX.json)、同目录`FINAL_SCIENTIFIC_RECEIPT.md`、`SCIENTIFIC_SUMMARY.md`、`FINAL_REPORT.json` |
| S17 | [MODEL校准比较](D:/1st/dynamic_member_coalition_core/reports/stfbs_lite_actual_counterfactual_001_continuation_001/SWITCH_REPLAY_EQUIVALENCE.json)、同目录`SCIENTIFIC_SUMMARY.md`及`task_support.py` |
| S18 | [stfbs_lite_proxy.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/stfbs_lite_proxy.py:64)、[stfbs_lite_selector.py](D:/1st/dynamic_member_coalition_core/research/non_oracle/stfbs_lite_selector.py:19)：旧proxy和独立有限表选择器的实际契约 |

原D60详细候选原件位于本地：

`D:\1st\stfbs_local_dev_actual_d60_002_a8f43e8d95464686b58a55ac7f70eeda\D60_MODEL_CANDIDATE.json`

路径由005的`H3_KEEP/authorization.json.candidate_path`读取，不从文件名推定。实际读取其`candidate.a2_policy_view`、`consumer_seed`、当前slot及服务历史；未执行任何恢复构造器或consumer。原始候选生成准备代码另在本地002目录，见第3.6节，远程可访问性作为限制保留。

## 2. PSF-P1：公开信息与建模语义

### 2.1 公开字段不等于隐藏真值知识

S03的`prepare_decision()`将完整`config`、机器人位置/Assignment、公告、合法belief、服务历史及已有slot复制到A2视图。S04又将完整Config作为公开投影的一部分，S01的公开摘要也包含Config。因此“整个Config私有、不可读”不符合当前实现。

另一方面，**某参数被公开传递，不等于已经确定其作为真实未来约束的科学优先级和适用范围**。本轮按以下边界分类，不新增权限系统。

| 信息或字段 | 实际来源与时间语义 | 科学分类 | 合法用途与限制 |
|---|---|---|---|
| 当前机器人位置、Assignment、角色、公开最大速度 | 冻结D60视图`positions/assignment/config`；当前已知条件 | `PUBLIC_STATE_EVIDENCE`、公开能力为`PUBLIC_MODEL_KNOWLEDGE` | 决策状态、候选几何/运动必要条件；不能把另一个机器人初始位置当同一状态内部的不确定世界 |
| 任务weight、deadline、required_robots、service_duration、birth | 预声明公告及可见任务 | `PUBLIC_STATE_EVIDENCE` | 同一价值矩阵必须固定；deadline为原经济迟到口径，不擅自替换为硬不可服务截止 |
| `coarse_position`、`announcement_tick`、`velocity_prior` | 公告在birth对应tick激活；belief初始锚点为announcement_tick（S02:23） | 公告值为`PUBLIC_STATE_EVIDENCE`；其误差支持为`DECLARED_MODELING_ASSUMPTION` | 提供公开先验；`velocity_prior`不是已测真实速度，0先验不证明静止 |
| `design_error_bound=0.5` | `PUBLIC_INPUT.json.source`明确为scenario design assumption，不是校准WLS置信度 | `DECLARED_MODELING_ASSUMPTION` | 自然对象是公告时刻的真实位置相对公告coarse_position；无证据允许把它无条件重置为D60当前belief周围的误差盘 |
| `speed_limit=0.8` | 公告；consumer对差分速度作裁剪（S02:51） | 公告模型界为`PUBLIC_MODEL_KNOWLEDGE`，真实性/硬约束强度须列入theta | 能作所声明模型的速度上界；不能仅凭未超限就确认与历史相容 |
| TargetAnnouncement `motion_model=constant_velocity` | 当前实现是公告dict中的字段；S04及S01检查该标签 | `PUBLIC_MODEL_KNOWLEDGE`；硬真实规律还是名义模型的强度`UNRESOLVED` | 原代理支持的名义传播类别，不自动证明未来永不转向 |
| Config `motion_model=continuous_turn`及turn参数 | 完整公开Config；ACTUAL场景验证、原物理/风险模块使用 | 字段可达且公开；预测适用优先级为`REACHABLE_BUT_SEMANTICALLY_UNRESOLVED` | 可以讨论为候选公开模型知识，不能偷读真实未来arc_rates/turn schedule或未声明地选用另一套模型 |
| `position_estimate/velocity_estimate`、`estimate_tick/available_tick` | 已合法消费的观测，或尚未观测的公告先验 | `PUBLIC_STATE_EVIDENCE` | 必须满足时间可用性；估计不等于真值，历史差分不等于瞬时速度 |
| `last_observation_tick/velocity_source/status` | 原consumer状态及冻结快照 | `PUBLIC_STATE_EVIDENCE` | 区分先验、接受观测和过期；内部`ACTUAL_WLS`不能单独证明MODEL记录是真ACTUAL来源 |
| 已接受位置历史、receipt、已消费/待消费记录 | 详细D60 consumer种子及合法观测链 | 合法历史部分为`PUBLIC_STATE_EVIDENCE` | 正确继承或检验历史；不是任意算法入口天然已有的字段，未来B1须明确通过哪种公开接口提供；pending未消费不能提前作为已知估计 |
| 已查询slot的bearing、测量tick、可用tick、sensor_id、sigma | D60 `current_slots`；合法测量及发布顺序 | `PUBLIC_STATE_EVIDENCE` | 已发生事实不能覆盖或重新生成；历史原始数据可约束候选状态，但需要明确测量误差模型 |
| 当前服务进度、团队、G/Q端点 | 公开快照`service_states/current_endpoints/current_q`及原历史 | `PUBLIC_STATE_EVIDENCE` | 实际可用于历史继承及必要几何限制。G的真值几何生成不使已公开服务反馈自动变成非法信息 |
| sensor sigma/health/observed_tick | 已发布profile及公开水位（S04:107） | `PUBLIC_STATE_EVIDENCE` | 当前声明可用；不自动证明未来永久不变，声明年龄可影响未来信息策略 |
| Q、radius_proxy、J/I、估计诊断 | 由公开payload及代表估计计算（S10） | `PUBLIC_STATE_EVIDENCE`，解释模型属`DECLARED_MODELING_ASSUMPTION` | 可预测服务质量；不能未经标定解释为严格误差界或真实95%覆盖区域 |
| 真实出生状态、目标私有当前状态、未来运动schedule、未来HF观测/完成结果 | 私有世界及揭晓后档案 | `PROHIBITED_FUTURE_INFORMATION`（在线） | 仅本次离线相容性和历史描述性比较可读，不得注入B1或BLVF控制belief |
| 私有服务审计中的target_position等完整物理证据 | 原RAW/物理审计 | 仅离线参照 | 能支持核查，不意味着这些真值字段获准进入在线公开信息集 |

### 2.2 公告位置界的时间对象

实际T0公告：tick0、coarse_position=(7.8,9.8)；T1公告：tick60、coarse_position=(9.0,10.3)。两者design_error_bound均0.5。S02用announcement_tick激活先验；公告文件说明该界为预声明设计假设。合理的最小解释是：在公告锚点时刻，真实出生/公告位置与coarse_position的偏差受所声明位置界约束。

尚未建立“任意时刻当前位置都在同一0.5盘内”“WLS更新后误差界仍为0.5”或“速度先验有0.5误差界”等契约。T0在D60合法位置估计为(9.2,10)，距原coarse_position约1.4142，这不表示原公告在tick0失效；它说明误差界不能脱离时间对象使用。

### 2.3 历史差分、截断及质量

S02 `freeze()`逆序寻找与当前被接受测量至少相差5 tick的历史位置，以

\[
\widehat v_k=\frac{\widehat p_k-\widehat p_s}{(k-s)0.05}
\]

计算差分，再按公告speed_limit裁剪。没有合格参考时保留已有速度及来源；Q FAIL并不自动拒绝合法位置更新。该速度在理想无误差条件下也是历史区间平均速度，不是普遍瞬时速度证明。

`trajectory()`对已有观测belief采用`span=min(age,1)`外推位置；age>1时输出预测速度0。PUBLIC_PRIOR仍按age全时长外推。**这是原估计/控制输出规则，既不声明目标真静止，也不提供当前位置不确定性消失的证据。** DEGRADED是当前冻结快照的年龄状态，而不是重置历史。

质量半径使用

\[
r_{proxy}=\sqrt{-2\log(1-0.95)}/s_{min}(J),\qquad \delta_Q=0.06.
\]

这是带局部线性信息及数值条件的`local_wls_radius_proxy_v1`。若希望将其提升为置信支持，尚需明确测量噪声、局部近似、估计选择及覆盖校准条件。现有D60 sigma=0.02，而原ACTUAL保存世界的`measurement_model.angle_perturbation=0`，MODEL `raw()`也直接生成精确几何bearing，并不按sigma抽样。因此不能仅凭sigma标签宣称本项目已经验证真实高斯噪声性能。

### 2.4 Config模型知识的具体未决点

冻结Config为continuous_turn、turn_interval=1、turn_max_angle=0.5、speed_delta_max=0，公开公告却为constant_velocity。S09会验证ACTUAL连续转向轨迹的角速度不超过`turn_max_angle/turn_interval`，并检查东向航向包络；但S06的MODEL世界及BLVF任务局部运动不由这个Config字段自动生成。

还须区分生成参数与硬物理界：如Config.target_speed_min=0.4不能直接作为所有真实目标的严格下界，当前保存世界T1允许静止，相关环境验证主要检查最大速度。

一个有实际影响的例子是已关闭H5：其声明转向率1 rad/s，高于上述Config比值0.5 rad/s；H4含瞬时转向。它们是明确声明的条件模型失配测试，并不因此撤销原有限科学验收；但若未来theta将该Config速率界作为真实支持的硬限制，就不能又把H5或H4作为未声明的默认合法未来。**模型优先级、硬/软含义及失配集合必须先声明。** 此处为语义LIMITATION，不重新审计或整改已关闭任务。

P1完成：已形成信息边界表；未来运动模型优先级和误差支持语义保留UNRESOLVED。

## 3. PSF-P2：原100世界历史相容性及候选竞争性

### 3.1 实际世界构成与可复核分组

读取S12 `WORLD_LIBRARY.json.worlds`实际得到100条；`PROXY_VALUE_TABLE.json`为300条保存结果。按world_ordinal及motion字段与H1进行比较，不执行`generate_worlds()`或proxy。

S01:107以当前`trajectory(b,tick)`为中心，位置偏移为0及四个轴向`design_error_bound/2`，速度偏移为0或东向`speed_limit/2`。每目标10个状态，再作笛卡尔积。实际：

| T0分组 | 数量 | 实际ordinal分组 |
|---|---:|---|
| 位置、速度均不扰动 | 10 | 0—9 |
| 仅速度扰动 | 10 | 10—19 |
| 仅位置扰动 | 40 | 20—29、40—49、60—69、80—89 |
| 位置、速度同时扰动 | 40 | 30—39、50—59、70—79、90—99 |

每一连续10条共享同一T0状态，包含10种T1状态。实际T0位置偏移长度0或0.25，速度为(0.3999999999999986,0)或(0.7999999999999986,0)。T1位置为(9,10.3)、(9.25,10.3)、(8.75,10.3)、(9,10.55)、(9,10.05)，速度为(0,0)或(0.4,0)。这些T1位置在其tick60公告中心的0.25以内，速度不超过0.8；这只验证公告位置盘和速度上界，不是完整观测/历史相容性认证。

世界比例只是有限确定性假设库的构成，不是真实未来概率。H1/H2/H3实际ordinal为0/1/2。MODEL与STFBS世界摘要不同，关联通过`MODEL_WORLD_MAPPING.json`，不要求两种digest相等。

### 3.2 D60 G端点的静态必要几何

冻结公开机器人位置：

\[
r_0=(9.54715677477287,9.559247459772442),\quad
r_1=(9.54715677477287,10.407775597196297),\quad r_2=(2,2).
\]

原团队U0/U1分别为dual_neg45/dual_pos45。S08给出半径0.6的固定世界坐标角色偏移；G容差为`rho=0.15+1e-10=0.1500000001`。原端点tick60、G=true、Q=PASS，服务进度12×0.05=0.6000000000000001秒。

对可信G端点，目标当前必要集合为

\[
P_G=\bigcap_{i\in team}B(r_i-o_i,\rho).
\]

本例两个圆心实际相同，均为(9.122892706060941,9.98351152848437)。标称T0=(9.2,10)到圆心距离为0.07885051979236427。任意长度0.25的位置扰动，由反三角不等式有

\[
\|p+\Delta p-(r_i-o_i)\|\ge0.25-0.07885051979236427
=0.17114948020763573>\rho.
\]

对实际80条逐个静态代入，角色锚点误差范围为0.17367716459568636—0.32752259684036295，全部违反至少一个、实际本例全部两个角色约束。20个位置未扰动世界通过这项检查。

**条件结论：** 若同时要求机器人D60位置、角色及可信G=true端点严格继承同一物理历史，80个位置扰动世界为`HISTORY_CONFLICT / STRESS_TEST_ONLY`。不必运行仿真即可得出这一必要条件冲突。P_G不是完整历史集合、全部观测相容区域或统计置信区域；G必要条件通过不构成充分条件。

### 3.3 相容性分类：不能把剩余20条认证为完整合法未来

| 适用假设/分类口径 | ordinal 0—9 | ordinal 10—19 | 其余80条 |
|---|---|---|---|
| 仅核验D60可信G、当前位置及公开速度上界 | 通过已检查必要条件；整体`UNRESOLVED` | 通过已检查必要条件；整体`UNRESOLVED` | `HISTORY_CONFLICT / STRESS_TEST_ONLY` |
| theta-A：公告0.5为出生位置硬界，T0该速度在D60以前已是匀速真实速度，保存位置历史按理想无误差解释 | 可作`CONDITIONALLY_COMPATIBLE`，限已检查约束；完整历史未认证 | `HISTORY_CONFLICT`，见下述出生及位置历史冲突 | 仍有D60 G冲突 |
| theta-C：固定全部历史，仅允许D60之后发生新速度变化；明确允许边界速度跳变且仍限速 | 原状态延续可作`CONDITIONALLY_COMPATIBLE` | 仅在这个新变化模型下`CONDITIONALLY_COMPATIBLE` | 不能靠未来变化修复既有位置冲突 |

全100条的主要报告分类是：**80条明确历史冲突，20条完整历史相容性未决**。没有把任何一条升级为“完整历史已经证明”。`HISTORY_COMPATIBLE`只能用于明确列出的已检查约束范围，不能省略其条件；本报告不使用该标签宣称全历史认证。

三种速度解释分别为：

**A：过去已存在的真实匀速速度。** 对T0位置9.2、速度约0.8，按该假设反推tick0位置为(6.800000000000003,10)，距公告(7.8,9.8)为1.0198039027185533，超过声明0.5。保存接受位置历史也从tick0的(8,10)逐步到tick60的(9.2,10)，与全程0.8的理想无误差轨迹不符。这里是时间、位置和运动假设联合冲突，不是“速度不同于belief所以拒绝”。

**B：D60瞬时速度不确定。** 历史差分为0.4不单独证明瞬时速度必为0.4；若存在观测误差或未建模运动，其瞬时支持需要历史及动力学约束。反之，未超0.8也不充分。若theta规定连续速度及有界转向/固定速率，又采用精确位置历史，必须核查其与0.8的联合相容性，不能直接接收。现有材料不足以无条件认证这10条，保持`UNRESOLVED`。

**C：D60之后的新变化。** 可以保持当前真实位置和全部历史不动，单独假设未来速度变化；但原世界常速度从D60即生效，若把0.4变成0.8，实际引入速度跳变。它并不属于公开Config中固定速率连续转向的自然结论，须显式声明新模型。若要求速度连续，应采用相应的连续未来过程，不能把原常速度表改名后冒充该过程。本轮不创建新过程。

T1在tick60刚公告且未被观察，0.25位置偏移具有与T0不同的时间语义；可作为公告盘内部的候选假设，但其速度先验不是硬真值。不能把两个目标一律按同一种当前位置扰动解释。

### 3.4 已有slot、consumer及服务继承

原详细D60种子实际具有T0接受位置历史tick0—60、最后receipt tick60、T1空位置历史及空pending。D60 slot中U0/T0与U1/T0为VALID，U2/T0及所有T1 slot为UNQUERIED。原已测bearing分别为2.237958535281127及−2.276069376804723，sigma为0.02。

S05 `ModelRawCache.query()`优先复用同target/robot/tick的历史slot，并检查机器人位置、sigma、health组成的context；它不通过这个context检查世界目标位置与旧bearing的物理相容性。新slot则由S06的当前条件世界几何生成。

因此MEMBER_CHANGE在D60保留U1、加入U2时，可能混用U1已发生的旧slot和U2新MODEL slot。要使混合有科学意义，二者必须描述同一目标、同一时刻、同一真实物理状态，并遵守同一明确测量误差模型。在理想无扰动模型下，历史两条bearing有共同交点；不能一边保留它们，一边任意平移T0当前真实位置，再把产生的定位异常归因于BLVF。

旧proxy对KEEP明确保留公开左端点，独立于条件世界当前几何（S18 docstring）；这作为冻结压力测试规则可复核，但并不证明所有情景都能严格继承同一物理历史。当前MODEL转换也是种子/历史的语义映射，不是世界历史相容性求解器：S07列出尚未认证的profile发布水位及MODEL世界适配依赖，不能把转换schema通过理解为所有未来世界可信。

后续不可采用的“修复”包括覆盖旧bearing、重生成已查询slot、重写D60 G端点、清空KEEP合法进度，或修改consumer历史。相容性必须通过限制候选世界及声明误差模型处理，不通过改历史获得。

### 3.5 MEMBER_CHANGE的合法性、可达性、服务与经济竞争

实际冻结候选为：

| 动作 | 联盟/目标 | D60服务处理 | 直接改派变化数/费用 |
|---|---|---|---|
| KEEP | U0 neg45 + U1 pos45，T0 | 保留0.60秒合法进度 | 0 / 0 |
| SWITCH | U0 neg45 + U1 pos45，T1 | 新团队服务从0起 | 2 / 0.02 |
| MEMBER_CHANGE | U1 pos45 + U2 neg45，T0 | 团队变化，关闭原段，从0起 | 2 / 0.02 |

角色和成员满足原q2分配语法，所以MEMBER_CHANGE是**合法动作**。合法不等于可及时建立服务。

静态必要条件使用实际参数：U2=(2,2)，T0标称=(9.2,10)，距离10.762899237658967；机器人max_speed=3，目标speed_limit=0.8，角色偏移长度0.6，G容差0.1500000001；剩余D60—D120为3秒，成员变更后连续服务要求2.25秒。

从0进度完成，至少需要45个有效0.05秒区间；最迟必须在D75左端点建立服务，进入时间至多0.75秒。在最有利的相向运动假设下：

\[
d_0\le(v_R^{max}+v_T^{max})T_{reach}+r_{anchor}+\rho
=3.6000000000999997.
\]

实际距离远大于上界。即使忽略控制器转向、其他机器人、观测质量及碰撞等限制，进入时间下界仍约2.6349734835681495秒，大于0.75秒。离散时序还要求服务区间两端G/Q有效，不能用一个最终时刻的接近替代连续服务。

这不只依赖标称位置：若目标位于本例P_G内，其距U2仍至少10.549161501041059，同样远超3.60。该推广仍以可信G和所声明目标速度上界为前提。

四个层次应分别裁定：

1. 动作合法性：通过原分配语法。
2. 在整个3秒内某时刻接近：上述2.635秒必要下界不单独否定，不能写成“整个时域绝不可能接近”。
3. 足够早地建立并完成2.25秒连续服务：在固定该团队、重置进度及上述速度界下违反必要条件。
4. 经济竞争性：不能由可达性必要条件单独完整排序；但该候选没有服务完成机会且有改派、运动成本。原保存世界结果支持其竞争机会贫乏，不证明一般成员重构无价值。

KEEP只需再累积1.65秒，SWITCH的T1服务时长为1.05秒且初始距离较近，所以三动作虽有不同合法身份，并不具有对称的完成机会。不能为了展示稳健决策而强行让不可竞争动作在某世界获胜。

### 3.6 候选目录与实际历史冻结来源

S13 `a0_plans.catalogue()`对2目标、3机器人、每团队2人、两个角色，形成12个团队/角色候选；完整可行分配为这12个单团队动作加全员空闲，共13个。三机器人不能同时承担两个互斥q2完整团队。

按`classify()`：KEEP为原分配1个，SWITCH为另一目标6个，MEMBER_CHANGE为原目标换成员4个；全员空闲及同成员角色互换不属于这三个代表类别，标为EXCLUDED。排除不等于这些动作没有科学价值，只是当前三代表结构的范围。

独立`select_candidates()`确有“每类按注入exact_value最大、再assignment_key确定并列”的机制，但其入口明确要求`SYNTHETIC_PURE_FIXTURE_NOT_SCIENTIFIC_EVIDENCE`，不得把它描述成已执行的真实A2评分器。

**实际005冻结来源与模块能力不同。** 本轮读取本地原002准备文件：

[prepare.py](D:/1st/stfbs_lite_h2_h3_extension_002_451cdb6e266e426692865771edc6a02f/prepare.py:79)

其79—80行显式列出三组`actions`，然后调用`classify/assignment_key`并保存`CANDIDATE_FREEZE.json`；没有调用`select_candidates()`生成三代表。004 `prepare_science.py:103`将这批冻结文件逐字节复用，005 `run_task_impl.py:63`再次用既有摘要锁定它们。

保存的`runs/a2_switch_episode_001/R_D60.json`可补充历史评分来源：`choice.rows`有12条，`evidence.candidate_count=12`、`legal_plan_count=13`；名义R选择row6的SWITCH。冻结MEMBER_CHANGE对应row5（U1 pos45、U2 neg45），其保存`v=-0.0005898517001428627`；KEEP对应row0，SWITCH对应row6。仅查看这些既有分数，不重新评价13动作。

该证据证明代表动作、原有限表评分及原名义选择的联系，但不能用独立fixture候选模块的接口注释替代实际历史生成链。原002准备文件未在当前005归档中作为同名源码完整提供，故报告保留本地来源引用及关键行为说明，远程审查可访问性为LIMITATION。

P2完成：80世界的必要几何冲突、20世界的未决边界、历史slot及冻结候选竞争性均有明确静态依据。

## 4. PSF-P3：历史筛选、ACTUAL证据及统一评价语义

### 4.1 L3-A：筛选信号与高保真未知必须分开

读取S14保存`FINAL_REPORT.json`，本轮未运行其脚本：T0扰动90条，H2精确并列ordinal为1—9共9条；H3精确并列80条；代理KEEP>SWITCH有80世界，SWITCH/T1未完成80世界，MEMBER_CHANGE优于KEEP、优于SWITCH及全体最优的数量均为0；未选97世界的高保真标签未知。

保存报告显示：无T0扰动组的最小H2边界分数为0.2999999998999998，T0扰动组为0.5499999999；两组最大H3敏感度同为0.5884375534491106。H2按边界距离，H3按相对H1动作价值差变化筛选，再用ordinal作精确并列规则。H2未选T0扰动有分数原因，H3又受精确并列和ordinal影响，不能简化为单一“90个世界被故意忽略”。

这些是旧代理标签和确定性库内统计。H2/H3中代理已给出KEEP优于SWITCH的风险信号，后来MODEL HF却反向；所以既存在筛选目标/平局局限，也存在代理排序误差。不能把未选97条的代理风险称作真实高保真风险，更不能从其占比得到实际风险概率。

### 4.2 SW3：固定多情景与几何自适应筛选不是同一贡献

S15实际后验统计保存`mean_D=-1/16`、`improved_families=0`、M1/M2覆盖均32。保存主损失为SW3-M0=11/32、SW3-M1=1/8、SW3-M2=3/16；完成类别覆盖分别21/32、32/32、32/32；MODEL WLS分别303、950、922。冻结结论为`NO_DEMONSTRATED_GAIN`：固定多情景M1改善了该数据上的类别覆盖，但自适应几何筛选M2没有显示相对M1的预定增益。

`sw3_public_hypotheses.py:169/177/184`分别体现M1固定标签选取、M2几何评分高/低情景选择及方法路由。该任务主要研究固定联盟服务完成类别/时间，32世界仅1个完成正例；它不是长期净价值、动态成员联盟或Minimax Regret效益验证。其后验核验状态与原BLOCKED状态并存，本轮不追认原流程成功，也不重新运行。

本节“SW3-M0/M1/M2”与第4.6节“评价对齐M0/M1/M2”含义不同，不混用。

### 4.3 原筛选器不能直接接收部分BLVF矩阵

S01 `screen_worlds()`会根据可信公开视图重新构造完整canonical library，并严格要求提供世界集合/ordinal/digest一致、候选身份正确、完整候选×世界表、无重复/外来/缺失格。

每格还要求`proxy_role='OPTIMISTIC_Q_PROXY'`，正成本六列ledger与value严格重构、全部任务的P0/Pmax/duration/NG/complete_team/completion_tick等字段有效。其H2/H3评分明确依赖这些任务/边界指标。

BLVF是具有实际Q和内生反馈的另一种预测语义，不能把几个BLVF结果改标签成旧OPTIMISTIC_Q_PROXY后直接送入screen_worlds。未来可以研究新合法参考池上的类似评分思想，但那是新方法比较，不是原100世界筛选严格复现。

另外S18独立`stfbs_lite_selector.select()`本身要求三世界完整表、合成fixture来源及context绑定；其存在不证明生产在线稳健选择或任意BLVF表适配已经完成。本轮不调用任何筛选/选择入口。

### 4.4 历史ACTUAL价值及排序反转

从S16实际矩阵`cells.*.original_value`读取D60_PRE_ASSIGNMENT_TO_D120_TERMINAL的未来净值；它由全程净值减共同已结算前缀−0.04504204709614111得到，执行change_cost=0.01：

| 初始动作 | H3保存MODEL HF未来净值 | ACTUAL全时域反事实未来净值 |
|---|---:|---:|
| KEEP | −0.3150141073101529 | −0.31501410731015284 |
| SWITCH | −0.157503491576509 | −0.7325408343901842 |
| MEMBER_CHANGE | −0.7331120450139224 | −0.7331120450139224 |

H3参考由005保存矩阵及L3-A九格误差记录交叉读取；ACTUAL参考直接来自独立D0—D120场次，不来自MODEL校准失败任务的未执行分支。

ACTUAL保存排序为KEEP>SWITCH>MEMBER_CHANGE；实际名义SWITCH的未来遗憾0.4175267270800314。无改派费用固定轨迹重评价仍保持KEEP最优，名义遗憾约0.3975267270800314；这不等于执行了零费用闭环。

S16 `FINAL_REPORT.json`原状态仍为`LOCAL_DEV_ACTUAL_FULL_EPISODE_THREE_ACTION_INCOMPLETE`，三个分支是`VALID_ACTUAL_CELL_CANDIDATE`，内部矩阵为PASS_CANDIDATE，历史复现NOT_CONFIRMED。其原最终失败和待验收边界不由本报告改变。这里仅复用保存的有效候选数值作描述性动机。

### 4.5 世界、策略及profile差异：已有校准能回答什么

实际H3 MODEL的T1为D60位置(9.25,10.3)、速度(0,0)；ACTUAL `runs/a2_switch_episode_001/WORLD_INPUT.json`的T1在D60出生于(9.2,10.1)、速度(0.4,0)。它们不是同一外生世界。原H3 HF包含D80/D100实际R和Assignment优化，而后续BLVF H3—H5使用固定候选保持；保存案例中有效分配没有改变不代表其完整未来策略语义相同。

ACTUAL全时域报告还显示KEEP在完成后D100为空闲，SWITCH及MEMBER_CHANGE在D80/D100继续各自团队。仅凭这些结果相近或不同，不能消去“世界、后续策略、信息可用性”三个维度。

S17是另一项**同历史世界**的MODEL SWITCH校准。实际比较表有1167个分组，1165组PASS，2组FAIL合计6字段：

| 时刻 | 字段 | ACTUAL值 | MODEL值 |
|---|---|---:|---:|
| D80 | U0/U1/U2 `sensor_profiles.observed_tick` | 各80 | 各60 |
| D100 | U0/U1/U2同字段 | 各100 | 各60 |

历史净值−0.7325408343901842，MODEL净值−0.7325408343901841，差1.1102230246251565e−16。最大字段差40是tick差，不是位置、速度或收益误差。其余已执行的物理、控制、动作、G/Q、服务、belief、消费时序及经济比较项通过。

原校准状态仍为FAIL、G1未通过，后两动作未运行，不追认其为完整动态等价。S03/原execution的profile发布行为与S06 `policy_view()`沿用D60 profiles解释了本例差异来源；本次sigma、health不是差异项。但未来若涉及profile更新、健康变化、水位验证或依年龄选取合法信息，observed_tick就可能影响控制/估计/服务，不能因本例净值相等永久删除此字段。

**可复用价值：** 不需要再次用完整逐字段工程等价任务证明“这一历史SWITCH的大多数科学输出已相近”；可以直接将6字段的声明时间语义作为有限对齐问题。**剩余缺口：** 没有普遍MODEL—ACTUAL等价，没有对所有动作/世界/策略的误差界，也没有同一合法情景支持下的真实未知未来决策效益证明。

### 4.6 后续最低统一评价语义

定义

\[
V(a;\pi\mid I_t,w)=J_{(t,H]}\bigl(I_t,w,\text{初始动作 }a,\text{后续策略 }\pi\bigr),
\]

并明确是否包括时刻t的Assignment费用、终端项及已结算前缀。本项目未来值应排除既有结算前缀，保留D60新动作的实际费用。

| 评价对齐层次 | 最小要求 | 本轮结论 |
|---|---|---|
| M0：评价语义统一 | 同合法初始决策状态、同外生世界、同动作、同后续策略、同时域、同服务/观测/经济结算；一致的profile发布时间及观测可用语义 | 后续科学设计必须先写清，不以净值偶合代替 |
| M1：有限同世界比较 | 在上述共同对象中，用少量有科学必要性的共同参照比较BLVF、HF、ACTUAL；分别审计信息、服务、价值，明确残余差异 | 现有校准能复用，只建议补必要科学缺口，不恢复全面字段等价路线 |
| M2：完整动态适用性 | 各自重规划、世界和观测演化下的完整决策效益及适用性 | 尚未建立，不作为B1开发的强制前置 |

特别区分`V(a; pi_hold | w)`与`V(a; pi_replan | w)`。若研究控制器/预测器差异，其他维度应尽量相同；若世界和策略无法统一，报告描述性差异及限制，不能强行归因于某估计器。

同一外生世界允许动作产生不同内生观测：比较不要求各动作共享未来观测流，而要求共同目标运动、外生测量扰动规则和传感器声明条件。它与强行回放另一个分支的未来反馈不是同一件事。

P3完成：筛选、SW3、ACTUAL及校准证据已复用；评价对齐的范围和未建立结论已区分。

## 5. PSF-P4：信息状态感知情景支持与决策问题族

### 5.1 三层约束与一种有限表示

令`I_t`只含截止决策冻结边界合法可用的公开信息。`theta`是预先声明的误差、运动、发布、观测及评价假设，不包含揭晓后的私有未来。

\[
X_j(I_t;\theta)=\{(p_t,v_t):\exists\text{历史前缀与 }I_t\text{及 }\theta\text{相容，终点为 }(p_t,v_t)\}.
\]

“存在历史前缀”限制避免只对一个位置盘和一个速度盘独立采样，再无依据地组合。X可以接受公告锚点、接受位置/原始slot的测量模型、速度约束和可信G几何的限制，但不能把未公开target_position加入在线定义。

\[
U_j(I_t;\theta)
\]

是未来运动过程或输入的假设集合，包含明确的运动模型、变更允许时刻、速率/速度约束等。它不同于X的当前速度不确定。对给定历史及初态，未来演化还必须满足连续性、边界及相应动力学。

\[
\Omega(I_t;\theta)=\{\text{联合历史—未来轨迹}:\text{历史与 }I_t\text{相容，初态/未来输入联合合法}\},
\qquad W(I_t;\theta)\subseteq\Omega(I_t;\theta).
\]

W是有限代表情景，不是完整覆盖证明，不保证真实未来必在其中。不对W赋未经标定的真实概率；均匀计算权重即使未来用于平均指标，也只表示研究者计算约定。

这不是要求本轮求解闭式集合、开发约束求解器或实现生成器。保留集合式定义即可为B1确定语义。

### 5.2 信息状态对应不同约束

| 状态 | 可用证据与约束 | 需要声明的未来假设 | 不允许的推断 |
|---|---|---|---|
| PRIOR_ONLY | 公告时刻、公告位置/速度先验及其声明支持；当前机器人与任务条件；合法无观测事实 | 从公告时刻至当前的可能状态，以及从当前起的未来运动；速度先验的软/硬含义 | 零速度先验=真静止；当前未观测位置必等于coarse_position |
| OBSERVED | 有来源的接受位置、estimate/available/consumed tick、合法历史参考、当前可信G/Q及服务进度 | 测量误差模型、历史平均速度至瞬时速度的关系、未来运动变化范围 | 位置估计=精确真值；Q PASS=严格置信盘；任意平移仍继承历史G |
| DEGRADED | 最后合法估计、观测年龄、历史及仍合法公开服务反馈；原控制输出本身 | 从最后估计至当前的不确定性演化，以及未来允许变化 | 控制传播速度0=目标真停；过期导致历史作废或不确定性自动收缩 |

同一数值belief在不同信息来源/时间语义下可能对应不同支持；不确定性不能仅由状态名或一个固定半径决定。B1若需要原始slot或接受历史，应明确其公开投影路径，不允许从私有consumer内部偷取尚未可用的未来记录。

### 5.3 两层决策问题族

第一层是不同的合法公开决策状态`I_1,...,I_n`；每个状态内部再形成自己的`W(I_k;theta)`及`A(I_k)`。价值表为

\[
\{V(a;\pi\mid I_k,w):a\in A(I_k),w\in W(I_k;\theta)\}.
\]

不能把不同任务权重、不同机器人初始位置或不同服务进度直接作为同一固定决策状态内部的未知未来世界，也不能将不同I_k的价值混入一个Minimax Regret矩阵。

后续状态设计应覆盖：已有联盟的合法服务继承、不同任务间的竞争、真正有替代成员进入机会的重构竞争。新状态需由合法历史过程形成，而不是改写本次D60的机器人位置、slot或0.60秒服务进度。设计目标是提供合理竞争机会，不保证每类动作在某情景获胜，不以制造候选冲突作为成功标准。

本轮没有证明某个新状态已经存在，也没有创建它；这不影响概念设计有效性。

P4完成：X、U、Omega、W及两层问题族已区分，未实施算法。

## 6. PSF-P5：下一步有限科研路线

### 6.1 路线裁定建议

```text
A1_RECOMMENDED = NO_AT_PRESENT
MINIMAL_ASSUMPTION_DEFINITION_RECOMMENDED = YES
JOINT_FOLLOW_UP_DESIGN_RECOMMENDED = YES
B1_RECOMMENDED = CONDITIONAL_ON_DECLARED_SUPPORT_AND_EVALUATION_SEMANTICS
C_LITE = DEFER_UNTIL_COST_OR_COVERAGE_IS_AN_ACTUAL_PROBLEM
C_CERTIFIED = DEFERRED
NEXT_SCIENTIFIC_EXECUTION_AUTHORIZATION = NOT_GRANTED
```

建议下一项首先形成**一个有限联合科学设计**，共同确定合法决策状态族、评价对齐M0及B1最小支持假设，而不是恢复三个大型串行整改/验收任务。

具体需要回答：在不改写历史、不过度依赖旧不可竞争MEMBER_CHANGE、且同世界同动作同后续策略的条件下，公开信息生成的有限未来情景能否为候选价值和基础稳健选择提供有意义的支持？这仍是设计问题，本报告不冻结后续实验矩阵、单元数或资源预算。

### 6.2 最小假设定义应解决什么

仅需预先声明以下对科学解释有直接影响的事项：

1. 公告CV与Config continuous_turn何者是名义传播、何者是硬真实支持；适用速度/转向界及变更时刻。
2. 公告误差界的锚点与度量；历史测量是当前理想无扰动、确定性有界误差，还是其他已声明模型。不能把现有sigma/Q自动升级为置信保证。
3. G端点作为合法服务反馈的可信约束范围，KEEP进度及历史slot不可变的继承语义。
4. 未来传感器health/sigma及发布水位的保持/变化假设，以及观测生成和合法消费的共同规则。
5. 条件价值采用pi_hold还是pi_replan，是否与ACTUAL参照保持一致，费用/终端/时域口径。

这些声明不需要引入新滤波器。适用性可在后续有限研究中评价；不能依据已揭晓H4/H5/ACTUAL的真实未来反向选择一个必然“覆盖成功”的先验，再将该数据当独立未知未来测试。

### 6.3 为什么当前跳过A1

原24格A1不恢复。默认完整100世界BLVF扫描也不推荐：80世界存在严格历史继承冲突；20世界的速度/误差语义尚未统一；已验收H3—H5回答了条件预测反馈的重要问题，现有证据并未提出一个必须通过旧池大扫描才能回答的新问题。

只有后续同时具备有科学解释的参考池、现有证据未回答的具体问题、公平BLVF/HF比较以及可改变研究设计的用途，才重新考虑有限A1。不能只为得到更完整的表格而启动计算。

### 6.4 共同参考比较与未知未来效益分开

可优先考虑共享合法历史前缀和参考状态，以减少重复恢复成本；在同世界、同动作、同策略下作有限预测器/执行器比较。已有MODEL SWITCH校准的大量通过证据应复用，不恢复全面工程等价路线，也不要求M2先完成才准研究B1。

共同参考实验只检验条件值预测或执行语义，不能替代独立未知未来中的实际决策效益评价。后续基础稳健研究应尽量固定候选、BLVF及后续执行策略，以标称情景决策作为清楚的基础对照，避免把预测器、候选空间和策略同时变化产生的收益归为Minimax Regret。

当前三代表中的MEMBER_CHANGE机会不足，应在合法状态族设计时优先改善这一研究覆盖；不人为让其获胜，也不把新状态间差异当成一个状态的情景不确定性。

### 6.5 C-Lite与理论性质的保留范围

对统一有限动作集A及有限情景集W，令

\[
r_V(a,w)=\max_{b\in A}V(b,w)-V(a,w),\qquad R_{V,W}(a)=\max_{w\in W}r_V(a,w).
\]

每个动作a取一个实现其最大遗憾的见证世界w_a，则至多m=|A|个见证世界即可保留全部候选的最坏遗憾向量；附加标称世界后至多m+1个。前提是有限完整矩阵、相同动作/价值语义及真正的最大值。该性质不等于保留所有轨迹机制、平均性能或完整不确定性支持。

若在同一A×W上具有统一真实价值误差界

\[
|\widehat V(a,w)-V(a,w)|\le\delta,
\]

则单情景遗憾、最坏遗憾的预测误差至多2delta，预测Minimax动作的真实决策损失满足

\[
R_{V,W}(\widehat a)-R_{V,W}(a^*)\le4\delta.
\]

对压缩W'⊆W，若还对所有动作有统一遗漏界

\[
0\le R_{\widehat V,W}(a)-R_{\widehat V,W'}(a)\le\varepsilon,
\]

且在W'上精确最小化预测遗憾，则

\[
R_{V,W}(\widehat a_{W'})-R_{V,W}(a^*)\le4\delta+\varepsilon.
\]

这里的epsilon是压缩遗漏界，不是此前数值最优集合容差1e−8。两者不能混用。若算法还允许近似最小化误差，须另计其误差项，不能继续无条件使用上述精确选择界。

当前没有全局delta或前瞻epsilon保证。H3—H5零MAE是有限条件平均/逐格结果，不是统一未见情景误差界；旧OPTIMISTIC_Q_PROXY也不是已认证价值上界。完整矩阵事后见证压缩不能宣称节省了获得完整矩阵的前瞻计算。理论不自动覆盖真实未来遗漏、MODEL—ACTUAL执行差异或pi_hold/pi_replan差异。

因此基础D1可以先研究合法小型完整矩阵及基础Minimax Regret，无需把C-Lite当强制前置。只有实际出现计算成本或有限预算风险覆盖问题，再研究压缩/筛选的科学收益；C-Certified继续暂缓。本轮不新增理论工作包或计算。

P5完成：已提出有限联合设计及最小假设路线，并给出跳过A1、暂缓C-Lite/C-Certified的证据依据。

## 7. S1—S5完成情况、阻断及限制

| 判据 | 本轮完成情况 | 核心交付 |
|---|---|---|
| S1 | COMPLETED_WITH_LIMITATIONS | 公开字段、模型知识、未决语义、假设及禁止未来信息分开；没有将整个Config私有化 |
| S2 | COMPLETED_WITH_LIMITATIONS | 100世界分组、80条G冲突、20条未决、三种速度解释及MEMBER_CHANGE必要界 |
| S3 | COMPLETED_WITH_LIMITATIONS | slot/consumer/进度继承、ACTUAL描述性反转及1165/6校准证据、M0—M2评价语义 |
| S4 | COMPLETED | X/U/Omega/W及不同公开状态内外两层问题结构 |
| S5 | COMPLETED_WITH_LIMITATIONS | 最小假设与联合后续设计；不默认恢复A1，不先验要求筛选/鲁棒性取得正结果 |

**本轮静态分析BLOCKER：NONE。** 以下为LIMITATION：

1. 公告误差支持、Config与公告运动模型的优先级及sigma/Q的真实统计语义尚未完整定义。这限制未来情景合法性保证，不阻断本轮指出该缺口。
2. 20个位置未扰动世界没有完整历史相容性认证；本轮未运行WLS、物理轨迹或consumer来补证，也不声称它们均不相容。
3. 部分详细D60候选及原002准备源码为本地项目外归档，远程可访问性有限。报告记录了实际路径、字段及关键来源行为，没有因可访问性不足重跑或补造。
4. ACTUAL全时域及校准任务原INCOMPLETE/FAIL、NOT_CONFIRMED或待独立接收边界保持原样；其保存有效候选只作有限复用，不新增验收。
5. SW3完成正例仅1个、97个未选世界高保真未知；已有世界及已揭晓真实未来不能作为后续独立测试。
6. 原BLVF有限验证不建立含噪鲁棒性、统一价值误差界、完整动态执行等价、跨世界稳健优势或论文创新性。

没有为消除上述限制新增工程系统、完整历史重放、支持集合求解或科研单元。OPTIONAL扩展不纳入本轮。

## 8. 实际操作、文件范围及停止状态

本轮实际操作为Git只读检查、源码/报告/JSON读取，以及通过`python -I -S -B`执行内联标准库静态统计。辅助代码仅使用json、pathlib、math、collections等标准库，未导入项目模块；用途为世界分组、保存字段提取、G必要几何、距离/时间界和现有比较表统计。没有运行历史诊断脚本，也没有将临时统计工具写入仓库。

本轮唯一新增正式文件：

`reports/stfbs_lite_fb_public_scenario_foundation_001/PSF_001_RESEARCH_REPORT.md`

开始时已有的H5关闭登记保持不变，已有跟踪文件未修改。报告完成后的Git只读范围核对用于确认这项文件边界，不作科学测试或重新验收。

```text
TASK_STATUS = STATIC_ANALYSIS_COMPLETED_WITH_LIMITATIONS
PSF_P1 = COMPLETED_WITH_LIMITATIONS
PSF_P2 = COMPLETED_WITH_LIMITATIONS
PSF_P3 = COMPLETED_WITH_LIMITATIONS
PSF_P4 = COMPLETED
PSF_P5 = COMPLETED_WITH_LIMITATIONS
BLOCKERS = NONE
INDEPENDENT_SCIENTIFIC_ACCEPTANCE = PENDING

NEW_HF_SCIENTIFIC_CELLS = 0
NEW_BLVF_SCIENTIFIC_CELLS = 0
NEW_WLS_CALLS = 0
NEW_SOLVER_CALLS = 0
NEW_CONSUMER_EXECUTIONS = 0
NEW_PROXY_VALUE_EVALUATIONS = 0
NEW_PHYSICAL_SIMULATIONS = 0
NEW_OBSERVATION_GENERATIONS = 0
NEW_R_OPTIMIZATIONS = 0
NEW_ASSIGNMENT_OPTIMIZATIONS = 0
NEW_PROJECT_TESTS = 0

BLVF_ALGORITHM_VERSION = V0.1
ALGORITHM_IMPLEMENTATION = NOT_PERFORMED
H3_H4_H5_REEXECUTION = NO
L3_B_FORMAL_STATUS = L3_B_BLOCKED
NEXT_STAGE_EXECUTION_AUTHORIZATION = NOT_GRANTED
PRODUCTION_ADMISSION = BLOCKED
```

本报告提交后停止。下一阶段只作为主研员及独立审核员的设计建议，不自动启动A1、B1、MODEL—ACTUAL实验、C-Lite、D1、L3-C或任何新世界计算。
