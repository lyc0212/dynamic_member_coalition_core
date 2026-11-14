# P1最终有限独立验收结论登记及阶段关闭

登记任务：`STFBS_LITE_L3_B_P1_FINAL_ACCEPTANCE_001`  
登记日期：2026-11-14  
被审核Git commit：`0ba1daf8cd9e1f34064d0b654bf33619738e9ea8`

## 裁定来源与正式声明

项目负责人及主研员接受独立科研与工程审核员已经完成的P1最终有限独立验收结论，正式接收六格科学复现结果并关闭P1阶段。本记录依据项目负责人提供的正式任务指令登记，属于既有独立裁定的记录，不是Codex重新开展的独立审核，也不构成新的计算或后续执行授权。

科学依据为L3-B V0.5、P1 V1.0及P1最终有限独立验收意见。原始报告中的`P1_PASS_CANDIDATE`保留为当时提交状态；本文件新增正式接收结论，不回写任何历史报告或原始证据。

## 六格复现验收

六格历史输入身份、原代理与MODEL世界映射通过验收。P0、REF、P1的三组三方十字段比较共180/180通过，六格净价值复现误差均为0；D80/D100空操作边界共12/12通过。固定D60 belief、原始传播截断规则及经济账本重构得到确认。实际REF调用6次、P1调用6次；新增WLS、Assignment、R、高保真计算及生产源码修改均为0。

| 世界 | 动作 | P0＝REF＝P1 |
|---|---|---:|
| H2 | KEEP | -0.7125094014320741 |
| H2 | SWITCH | -0.7325026216050797 |
| H2 | MEMBER_CHANGE | -0.7330898517001428 |
| H3 | KEEP | -0.7125094014320741 |
| H3 | SWITCH | -0.7325026216050797 |
| H3 | MEMBER_CHANGE | -0.7330898517001428 |

上述结果冻结为后续P2—P4的基准。后续直接读取已验收实际归档，不重新计算P1，也不把表中数值硬编码为程序预期输出。

原始证据引用：[输入绑定](INPUT_BINDINGS.json)、[执行配置](EXECUTION_CONFIG.json)、[REF输出](REFERENCE_RESULTS.json)、[P1输出](P1_RESULTS.json)、[三方比较](P1_COMPARISON.json)、[科学指标](P1_METRICS.json)、[原始中文报告](REPORT.md)、[原始最终报告](FINAL_REPORT.json)、[执行入口](p1_entry.py)、[资源回执](RESOURCE_RECEIPT.json)，以及`RAW/`、`CELL/`、`TRACE/`。所有文件和目录保持原状，不重新生成。

## 已正式接收的科学发现

### 动作依赖的预测误差

| 指标 | 数值 |
|---|---:|
| 六格MAE | 0.32229275060815804 |
| 总体signed bias | -0.3222779550656384 |
| KEEP signed bias | -0.3974952941219212 |
| SWITCH signed bias | -0.5693607643887735 |
| MEMBER_CHANGE signed bias | +0.000022193313779506063 |

H2/H3的代理最优动作均为KEEP，历史HF最优动作均为SWITCH。

| 世界 | P1 KEEP−SWITCH | HF KEEP−SWITCH | P1所选动作的HF regret |
|---|---:|---:|---:|
| H2 | +0.019993220173005644 | -0.1462338844540494 | 0.1462338844540494 |
| H3 | +0.019993220173005644 | -0.1575106157336439 | 0.1575106157336439 |

### KEEP传播截断与服务重置

独立验收确认H2/H3 KEEP均具有以下过程：D60初始位置和速度估计正确，继承0.60秒服务进度；D80传播年龄达到1秒，服务进度达到1.60秒；D81触发一秒传播截断，预测位置停止外推、预测速度归零；D87最大服务进度达到1.95秒；D88的G变为false，服务进度清零；D120任务未完成。

完成阈值为2.25秒，最大进度尚差0.30秒，即6个有效服务区间。已确认传播截断造成预测误差增长，服务重置发生在其后；取消截断是否避免重置并完成任务尚未确认，留待P2验证。`observation_invalid`是代理服务时钟重置原因，不是实际传感器观测失败或实际WLS质量检测失败的证据。

### SWITCH先验失配

两个世界的T1均沿用固定D60 PUBLIC_PRIOR。H2初始位置正确、初始速度错误，位置预测误差随时间增长；H3初始位置偏差为0.25、初始速度正确，位置预测误差持续存在。一秒传播截断对这些PUBLIC_PRIOR不适用，两类失配是后续反馈诊断的重要对照。

### 排序反转的经济机制

原代理预测三个动作均不能完成任务，completion、flow、late、terminal相同。KEEP与SWITCH的价值差主要来自change成本，另有较小的effort成本差。因此，在当前固定条件案例中，任务完成能力的预测误差可能使长期动作价值评价退化为局部改派成本比较，导致错误的联盟重构选择。本结论不宣称普遍规律。

## 科学解释边界

P1通过确认历史结果可复现、任务本地诊断实现与历史原代理在六格核心输出上等价，以及D80/D100空操作不改变原有科学状态。

本次验收不证明代理预测准确、取消截断必然有效、反馈回放已验证、真实反馈操作的边界连续性成立，或Minimax Regret及生产算法具有性能优势。

D60以前部分历史观测来源仍未完整识别，保留该限制。HF参照来自历史价值矩阵及对应分支报告，本次未重跑HF，亦未开展全部大型HF原始轨迹逐事件审计。H2/H3为确定性冻结世界，六格不是六个独立随机样本。

## 资源限制

| 资源 | 已记录消费 | 批准上限 |
|---|---:|---:|
| CPU小计 | 1.15625秒 | 120秒 |
| 墙钟 | 480.379秒 | 900秒 |
| 累计逻辑写入 | 2,082,842 bytes | 134,217,728 bytes |

未观察到上限触发。初始只读操作、部分宿主资源及入口退出尾部未完整计量，因此资源会计仍为INCOMPLETE、整体资源合规仍为NOT_ESTABLISHED。项目负责人明确接受探索阶段的这一限制。未知消费不记零，不重新核算历史余额，不宣称整体资源合规；此前Stage A历史超时及不完整资源记录继续保留。

## 后续研究要求（仅登记，不执行）

后续采用一次联合窗口顺序执行P2—P4的研究策略，不重新开启完整Stage A整改，不额外重跑P1或工程测试。后续执行仍须有明确的任务与资源授权，本次登记不启动任何后续计算。

P2仅取消已观测belief的一秒传播截断，保持固定D60 belief及其他规则，并读取已验收P1作为基准。KEEP重点检查D81以后预测和控制变化及D88重置是否避免；SWITCH利用原定六格中的PUBLIC_PRIOR作为NoCap负对照，不新增计算；MEMBER_CHANGE检查传播改善是否转化为服务进度。若SWITCH出现无法解释的变化，应先检查NoCap之外的规则是否被改变。不预设KEEP改善或MEMBER_CHANGE不变，同时分析价值误差、动作排序及HF regret，不能仅凭MAE降低判断决策改善。

P3/P4须在未来获准的联合任务中完成最小必要反馈验证：

| 要求 | 内容 |
|---|---|
| F1 | 正确绑定历史frame、receipt、事务和pending，防止重复消费。 |
| F2 | D80/D100仅消费当时已入队且可用的历史事件，保持原队列顺序。 |
| F3 | 仅改变批准的belief及consumer字段，保持物理与服务状态连续。 |
| F4 | 分别记录反馈接受、belief、预测、控制、服务五层变化。 |

同一世界—动作下P3/P4使用同一份冻结历史MODEL反馈流。保留内部ACTUAL_WLS等算法描述，通过原始输入、provenance及receipt关联判断实际来源。D120只保留终端状态及历史实际剩余pending，不新增反馈生成或消费。允许反馈不接受、状态不变或机制不可识别，不要求恢复D60以前全部身份。某单元反馈无法唯一绑定时，停止该单元反馈比较，保留有效P2及其他独立结果。

## 最终登记状态

```text
P1_FINAL_INDEPENDENT_ACCEPTANCE = ACCEPTED
P1_INDEPENDENT_ACCEPTANCE = ACCEPTED
P1_SCIENTIFIC_REPRODUCTION = PASS
P1_STAGE = CLOSED
P1_VALID_CELLS = 6
P1_CORE_FIELD_COMPARISONS = 180/180
P1_BASELINE = FROZEN
P1_REEXECUTION_REQUIRED = NO

STAGE_A_TECHNICAL = ACCEPTED_WITH_LIMITATIONS
NEW_STAGE_A_REMEDIATION = NOT_REQUIRED
ADDITIONAL_ENGINEERING_TESTS = NOT_REQUIRED

RESOURCE_ACCOUNTING = INCOMPLETE
RESOURCE_COMPLIANCE = NOT_ESTABLISHED

P2_TECHNICAL_ELIGIBILITY = READY
P3_P4_FEEDBACK_VALIDATION = REQUIRED
P3_P4_REMAINING_REQUIREMENTS = MINIMAL_FEEDBACK_IDENTITY_AND_CONSISTENCY_VALIDATION
P2_P3_P4_EXECUTION = NOT_STARTED
PRODUCTION_ADMISSION = BLOCKED
```

本次仅新增本验收登记文件；不重新执行独立审核、REF、P1、合成测试、历史反馈回放或任何科学计算，不修改原始科学证据。
