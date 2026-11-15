# STFBS_LITE_FB_BLVF_H5_ARC_EXTENSION_001 最终独立科学验收及关闭

## 一、正式裁定

独立科学验收：ACCEPTED_WITH_LIMITATIONS

主研员确认：ACCEPTED

科学阻断项：NONE

任务关闭状态：CLOSED

依据负责人提供的独立科学验收报告，独立审查员已经实际核查H5 V1.0及R1—R5执行澄清、两次科学入口、最小接口修复、实际运动定义、六格完整RAW、五格完整TRACE、六个HF/ON TIMING、完整资源日志、完整离线机器可读结果及离线核验脚本。

主研员正式接收七格有效科学结果及全部非阻断性限制。

不重跑、不整改、不追加H5诊断、不修改BLVF算法。

## 二、独立科学验收结果

| 验收项目 | 裁定 |
|---|---|
| C1 实验身份及失败恢复 | PASS |
| C2 HF及BLVF科学可比性 | PASS_WITH_LIMITATIONS |
| C3 KEEP反馈主动干预对照 | PASS |
| C4 连续转向机制 | PASS |
| C5 服务及价值预测结果 | PASS |
| C6 计算机制及计时 | PASS_WITH_LIMITATIONS |
| C7 离线恢复、资源及证据限制 | PASS_WITH_LIMITATIONS |

## 三、原执行及离线恢复历史

ATTEMPT_001：

- 原状态：BLOCKED_NO_ACCEPTED_CELLS。
- 启动1格，有效0格。
- 资源包装器method参数与下游least_squares的method='trf'冲突。
- WLS启动1次，FAILED且已闭合。
- Solver及BLVF解析调用为0。

该失败属于实施错误，不构成H5科学负面结果。

ATTEMPT_002：

- 使用仅限位置参数标记的最小接口修复。
- 原运动模型及BLVF算法未修改。
- 科学启动7格，有效单元内结果7格。
- 四类单元内科学审计全部PASS。
- 原后置汇总因递归比较函数无法处理整数键而失败。
- 原状态PARTIAL_RESULTS永久保留。

离线恢复：

- OFFLINE_FINALIZATION_STATUS = PASS。
- 使用标准库读取及核验保存JSON。
- 未导入科学项目模块。
- 未新增科学计算、估计器调用、consumer执行或测试。
- 原文件清单44项全部通过。
- 冻结源码及输入保护12项全部通过。

整个H5任务累计科学启动8次，有效科学单元7格。

## 四、冻结实验身份

H5世界摘要：

6d23db4be70d86ad95c95de8cb4022de9a3617c38e7f7a4f2c085b56b488bf5f

物理定义摘要：

e3730bdbc45a6ccc6ede9ced9dc5089963dd8a080817455967971a79af0796d6

BLVF V0.1源码SHA256：

204fc231bf78004c33daf151983d751685666da75ed9e9b911abb83854c7365e

H5运动源码SHA256：

ef05b290837b60761ccd209c03d6b2af07a2c7648e1af017044aa2ac63fb82bd

D60公开输入、consumer seed及候选动作保持冻结。

H5真实运动为D75—D85恒定转向率圆弧，总转角0.5 rad，转向率1 rad/s。

HF使用原九起点WLS，启用反馈。

FB-ON使用BLVF解析估计，启用反馈。

FB-OFF使用BLVF解析估计，反馈不进入实际控制。

原consumer、控制、服务及经济规则保持一致。

## 五、KEEP主动干预对照

D61—D80：

- 科学观测20对一致。
- 物理帧20对一致。
- 允许的身份字段及关联摘要差异300处。
- 实际科学字段差异0处。

独立重新比较所得具体tick、字段路径及差异值与离线保存记录一致。

实际估计payload摘要未被忽略。

OFF实际控制继续使用D60冻结belief。

ON实际控制使用D80合法消费的反馈belief。

KEEP对照能够识别反馈进入实际控制后的条件闭环总增量效应。

仅KEEP具有ON/OFF配对，不推导其他两个动作的独立反馈效应。

## 六、H5-A运动估计及传播机制

HF和ON KEEP在D80均实际使用D75—D80合法接受位置差分。

参考间隔5 tick，即0.25秒。

D75参考位置：

(9.499999999999998, 10.0)

D80实际接受位置：

(9.598961583701808, 10.012435031315743)

实际差分速度：

(0.3958463348072385, 0.049740125262971446)

实际瞬时速度：

(0.3875649686842565, 0.09896158370180883)

实际位置估计误差：0。

差分速度与真实历史区间平均速度误差：0。

速度裁剪影响：0。

瞬时速度向量误差：

0.049913254709636694。

实际航向误差：

-0.1249999999999929 rad。

历史速度估计滞后及未来匀速传播失配均得到实际证据支持。

D80、D85、D92实际ON KEEP控制预测误差：

| 时刻 | 位置预测误差 | 速度预测误差 |
|---|---:|---:|
| D80 | 0 | 0.049913 |
| D85 | 0.024870 | 0.148932 |
| D92 | 0.076970 | 0.148932 |

原运动估计机制的限制同时存在于HF与BLVF，不属于本次解析定位替代引入的附加误差。

超过一秒传播截断的记录不套用未截断公式。

D100已经完成目标的终端belief不作为正在发挥作用的控制更新。

## 七、H5-B反馈及连续服务

七格实际服务结果：

| 单元 | 最大连续服务进度 | G/Q有效区间 | 完成结果 |
|---|---:|---:|---|
| HF KEEP | 2.25 s | 33 | D93完成 |
| HF SWITCH | 1.05 s | 21 | D110完成 |
| HF MEMBER_CHANGE | 0 | 0 | 未完成 |
| OFF KEEP | 1.90 s | 26 | D87重置，未完成 |
| ON KEEP | 2.25 s | 33 | D93完成 |
| ON SWITCH | 1.05 s | 21 | D110完成 |
| ON MEMBER_CHANGE | 0 | 0 | 未完成 |

KEEP初始合法连续服务进度为0.60秒。

D60—D92共33个共同有效目标—控制时刻：

- OFF平均位置预测误差：0.0496235450501352。
- ON平均位置预测误差：0.014005290605552456。
- OFF平均速度预测误差：0.15453125872703435。
- ON平均速度预测误差：0.05574148759077401。

HF KEEP与ON KEEP的上述平均预测误差一致。

KEEP反馈净价值增量：

0.39749529730192784。

KEEP反馈绝对误差改善：

0.39749529730192784。

经济贡献：

| 分项 | 对净价值改善的贡献 |
|---|---:|
| 完成收益增加 | +0.125 |
| 流动成本减少 | +0.005625 |
| 延迟成本减少 | +0.016875 |
| 终端成本减少 | +0.25 |
| 控制成本增加 | -0.00000470269807205505 |
| 联盟变化成本 | 0 |

反馈效应主要通过任务完成及终端经济后果产生。

本次识别的是完整反馈机制的条件闭环总增量效应，不单独归因于D80速度更新。

服务完成表明原闭环能够容忍本次实际观察到的状态误差，但不确定普遍允许误差上限。

## 八、H5-C完整价值矩阵

| 动作 | HF | FB-ON | FB-OFF |
|---|---:|---:|---:|
| KEEP | -0.31501410413014613 | -0.31501410413014613 | -0.712509401432074 |
| SWITCH | -0.157503491576509 | -0.157503491576509 | NOT_RUN |
| MEMBER_CHANGE | -0.7331125696046304 | -0.7331125696046304 | NOT_RUN |

三个FB-ON净值均与对应HF保存净值一致。

完整三动作MAE：0。

三组相对价值误差：0。

HF与ON完整排序：

SWITCH > KEEP > MEMBER_CHANGE。

epsilon = 1e-8的ON近似最优候选集合：

{SWITCH}

对应条件HF regret：0。

实际动作选择：NOT_SPECIFIED。

不声称执行了Minimax Regret。

OFF只运行KEEP，不构造完整OFF排序、三动作MAE或regret。

HF和ON MEMBER_CHANGE均未完成服务，属于合法科学结果，BLVF正确预测了失败的服务结果及对应净价值。

## 九、科学假设正式裁定

H5_A_MOTION_ESTIMATION = SUPPORTED_IN_TESTED_CASE

H5_A_VELOCITY_LAG = SUPPORTED

H5_A_PROPAGATION_MISMATCH = SUPPORTED

H5_A_ANALYTIC_POSITION_ERROR_AS_CAUSE = NOT_OBSERVED

H5_B_FEEDBACK_TOTAL_EFFECT = SUPPORTED

H5_B_FEEDBACK_BENEFIT = POSITIVE_NET_VALUE_EFFECT

H5_C_CONDITIONAL_VALUE_PREDICTION = SUPPORTED_WITHIN_H5

H5_VALUE_MAE = 0

H5_CONDITIONAL_HF_REGRET = 0

H5_ACTION_RANKING_RECOVERED = YES

H5_COMPUTATIONAL_SIMPLIFICATION = SUPPORTED

H5_SINGLE_RUN_TIMING_ADVANTAGE = OBSERVED

END_TO_END_SPEEDUP = NOT_ESTABLISHED

## 十、计算机制及资源

ATTEMPT_002实际分格调用：

| 单元 | WLS | Solver | 解析 |
|---|---:|---:|---:|
| HF KEEP | 33 | 297 | 0 |
| HF SWITCH | 51 | 459 | 0 |
| HF MEMBER_CHANGE | 61 | 549 | 0 |
| OFF KEEP | 0 | 0 | 60 |
| ON KEEP | 0 | 0 | 33 |
| ON SWITCH | 0 | 0 | 51 |
| ON MEMBER_CHANGE | 0 | 0 | 61 |
| 合计 | 145 | 1305 | 205 |

ATTEMPT_002共1655次资源调用，全部正常返回，无重复调用ID、无未闭合调用、无FAILED。

解析日志属于总资源日志子集，不重复计数。

三个HF固定动作单元：

145次WLS，1305次Solver。

三个ON固定动作单元：

145次解析估计，0次非线性WLS及Solver。

接收相同观测估计数量下的计算机制简化证据。

不将取消未来R及Assignment优化错误归因于BLVF。

实际核心运行墙钟：

| 动作 | HF | ON |
|---|---:|---:|
| KEEP | 9.351917 s | 4.543326 s |
| SWITCH | 13.571010 s | 6.175411 s |
| MEMBER_CHANGE | 15.050130 s | 6.313977 s |

三个HF核心墙钟合计：

37.97305709999637秒。

三个ON核心墙钟合计：

17.03271300002234秒。

实际比值：

2.2294191829537997。

接收本次同口径单次运行时间改善。

保留资源日志数量、profile监控开销及固定执行顺序的影响。

不将全部时间差异解释为解析估计器纯计算加速。

不宣称统计意义或一般性端到端加速。

整个H5任务累计：

- 科学启动：8。
- 有效科学单元：7。
- WLS：146。
- Solver：1305。
- 解析：205。
- 资源调用：1656。
- 正常返回：1655。
- 首次WLS失败：1。
- 离线新增科学计算：0。

三个独立窗口：

| 窗口 | 已测CPU小计或快照 | 记录墙钟 |
|---|---:|---:|
| ATTEMPT_001 | 1.046875 s | 397.43556092950166 s |
| ATTEMPT_002 | 63.234375 s | 124.95685481486726 s |
| 离线恢复 | 0.203125 s | 252.28607190729235 s |

首次失败写入：

122024 bytes。

离线恢复前累计写入：

12115003 bytes。

离线新增写入：

477525 bytes。

关闭登记前累计受控逻辑写入：

12592528 bytes。

本次关闭登记的行政性新增写入与原科学资源记录区分，不覆盖原资源回执。

三个窗口分别保留。

未知宿主、只读工具及退出尾部资源不记零。

RESOURCE_ACCOUNTING = INCOMPLETE

RESOURCE_COMPLIANCE = NOT_ESTABLISHED

## 十一、最终保留限制

1. 独立审查未直接取得HF MEMBER_CHANGE完整RAW及TRACE。

2. 独立审查未直接取得OFF KEEP完整TRACE。

3. 原本地D60候选文件未由独立审查直接读取，使用保存摘要、源码检查及绑定回执支持。

4. 原最终动态运行时导入回执缺失，保持NOT_VERIFIED。启动前绑定回执已经保存。

5. 原资源日志未保存逐调用payload摘要，不声称建立完整逐调用哈希绑定。

6. 首次执行失败及全部实际资源消耗永久保留。

7. 第二次执行后置汇总失败及原PARTIAL_RESULTS永久保留。

8. 仅KEEP具有ON/OFF反馈配对。

9. H3—H5属于三个指定确定性条件世界，不进行总体统计泛化。

10. 单次运行时间改善不代表通用加速倍数。

11. 资源会计不完整，整体资源合规未建立。

12. 未知未来自主情景生成、真实含噪观测鲁棒性及多传感器一般性能尚未建立。

13. 跨世界稳健决策优势尚未建立。

14. 论文创新性尚未建立。

以上均为非阻断性LIMITATION，不要求重新计算或工程整改。

## 十二、H3—H5基础验证阶段最终结论

三个BLVF验证任务共取得17个有效科学单元：

- H3：6个BLVF单元。
- H4 BLVF扩展：4个BLVF单元。
- H5：4个BLVF单元及3个新增HF单元。

合计14个BLVF单元及3个新增HF单元。

上述数量不代表17个独立世界或17个独立随机样本。

三个指定条件世界分别支持：

H3：基本内生反馈与条件价值预测。

H4：瞬时目标运动方向变化后的反馈适应。

H5：存在历史速度滞后和未来传播失配时的条件价值预测。

H3、H4、H5的三个ON动作价值MAE均为0。

条件HF regret均为0。

H5进一步提供单次同口径运行时间改善证据。

当前基础科学认识：

面向长期服务价值评价的轻量预测器，应优先保留动作引起的内生信息反馈、控制、服务及经济耦合，而不必无条件追求全部未来状态的精确重建。

该研究认识只在当前测试条件下获得支持，不宣称普遍理论或已建立论文创新性。

## 十三、正式关闭及后续研究方向

H5科学结果正式接收。

H5任务正式关闭。

H3—H5指定条件世界基础价值预测验证阶段正式关闭。

保留BLVF V0.1作为后续研究中的条件价值预测模块。

不修改运动估计器。

不立即引入EKF、UKF、IMM或转向率估计器。

不追加缺乏明确科学目的的人工H6、H7等运动世界。

下一阶段研究方向：

PUBLIC_INFORMATION_DRIVEN_SCENARIO_GENERATION

首先研究如何依据合法D60公开信息构造有限、可信的未来运动情景。

不依赖隐藏真实未来，不依据预期最优动作反向设计情景，不人为制造跨世界候选冲突。

H3、H4、H5的HF最优动作均为SWITCH，目前未建立跨世界最优动作冲突及Minimax Regret优势。

本次关闭不授权新情景生成科学执行、多世界价值评价实验、Minimax Regret实验、L3-C或生产准入。

## 十四、最终状态

TASK = STFBS_LITE_FB_BLVF_H5_ARC_EXTENSION_001

ATTEMPT_001 = BLOCKED_NO_ACCEPTED_CELLS

ATTEMPT_002 = PARTIAL_RESULTS

OFFLINE_FINALIZATION = PASS

TOTAL_SCIENTIFIC_STARTS = 8

VALID_SCIENTIFIC_CELLS = 7

SCIENTIFIC_REEXECUTION = NO

C1 = PASS

C2 = PASS_WITH_LIMITATIONS

C3 = PASS

C4 = PASS

C5 = PASS

C6 = PASS_WITH_LIMITATIONS

C7 = PASS_WITH_LIMITATIONS

INDEPENDENT_SCIENTIFIC_ACCEPTANCE = ACCEPTED_WITH_LIMITATIONS

RESEARCH_LEAD_CONFIRMATION = ACCEPTED

SCIENTIFIC_BLOCKERS = NONE

H5_A_MOTION_ESTIMATION = SUPPORTED_IN_TESTED_CASE

H5_B_FEEDBACK_TOTAL_EFFECT = SUPPORTED

H5_C_CONDITIONAL_VALUE_PREDICTION = SUPPORTED_WITHIN_H5

H5_VALUE_MAE = 0

H5_CONDITIONAL_HF_REGRET = 0

H5_COMPUTATIONAL_SIMPLIFICATION = SUPPORTED

H5_SINGLE_RUN_TIMING_ADVANTAGE = OBSERVED

BLVF_ALGORITHM_VERSION = V0.1

ALGORITHM_MODIFICATION_REQUIRED = NO

REEXECUTION_REQUIRED = NO

ENGINEERING_REMEDIATION_REQUIRED = NO

ADDITIONAL_H5_DIAGNOSTICS_REQUIRED = NO

FINAL_RUNTIME_BINDING_RECEIPT = NOT_VERIFIED

PER_CALL_PAYLOAD_DIGEST_BINDING = NOT_AVAILABLE

RESOURCE_ACCOUNTING = INCOMPLETE

RESOURCE_COMPLIANCE = NOT_ESTABLISHED

END_TO_END_SPEEDUP = NOT_ESTABLISHED

H3_BLVF_INITIAL_VALIDATION = CLOSED

H4_BLVF_EXTENSION = CLOSED

H5_ARC_EXTENSION = CLOSED

TASK_CLOSURE_STATUS = CLOSED

CONDITIONAL_VALUE_VALIDATION_STAGE = CLOSED

NEXT_RESEARCH_DIRECTION = PUBLIC_INFORMATION_DRIVEN_SCENARIO_GENERATION

NEXT_STAGE_SPECIFICATION = PENDING

NEXT_STAGE_EXECUTION_AUTHORIZATION = NOT_GRANTED

CROSS_WORLD_ROBUST_DECISION_ADVANTAGE = NOT_ESTABLISHED

PAPER_NOVELTY = NOT_ESTABLISHED

L3_B_FORMAL_STATUS = L3_B_BLOCKED

L3_C_EXECUTION_AUTHORIZATION = NOT_GRANTED

PRODUCTION_ADMISSION = BLOCKED
