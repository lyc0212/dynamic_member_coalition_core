# L3-B探索性科学机制诊断最终验收登记及阶段关闭

登记任务：`STFBS_LITE_L3_B_FINAL_SCIENTIFIC_ACCEPTANCE_001`  
被验收科学任务：`STFBS_LITE_L3_B_P2_P4_MECHANISM_DIAGNOSTICS_001`  
被验收实验结果提交：`2bc1bda8063531b547cf43059bc372d654df2286`  
登记日期：2026-11-15

## 一、裁定来源与正式接收声明

主研员正式接受独立科研与工程审查员对P2—P4联合机制消融实验作出的最终裁定：**ACCEPTED_WITH_LIMITATIONS**。

本记录依据项目负责人提供的正式验收登记指令，登记独立审核员已经完成的核验及科学裁定，不是Codex重新开展的独立审核。本次未进行重新计算、反馈回放、工程测试或科学实现修改。

正式接收P2、P3、P4各六格，共18个新增有效科学诊断单元；与已验收、冻结的P1六格组合，形成完整24格科学矩阵。实际执行为P2、P3、P4各6次，P1及REF重跑0次，新增WLS、Assignment、R、高保真计算、条件世界、随机seed和正式高保真attempt均为0。

原始[REPORT.md](REPORT.md)、[FINAL_REPORT.json](FINAL_REPORT.json)、[V05_FINAL_STATUS.json](V05_FINAL_STATUS.json)及全部原始科学证据保持原样。探索性科学接收通过本新增文件表达，不回写原始提交状态或正式门槛裁定。

## 二、已接收的实际结果

以下表格直接引用既有[REPORT.md](REPORT.md)、[VALUE_MATRIX.json](VALUE_MATRIX.json)及[SCIENTIFIC_ANALYSIS.json](SCIENTIFIC_ANALYSIS.json)，本次未重新计算。

### 完整价值矩阵

| 世界 | 动作 | HF | P1 | P2 | P3 | P4 |
|---|---|---:|---:|---:|---:|---:|
| H2 | KEEP | -0.3150141073101529 | -0.7125094014320741 | -0.3150141073101529 | -0.3150141073101529 | -0.3150141073101529 |
| H2 | SWITCH | -0.1687802228561035 | -0.7325026216050797 | -0.7325026216050797 | -0.16878022285610356 | -0.16878022285610356 |
| H2 | MEMBER_CHANGE | -0.7331120450139224 | -0.7330898517001428 | -0.7331120450139224 | -0.7331120450139224 | -0.7331120450139224 |
| H3 | KEEP | -0.3150141073101529 | -0.7125094014320741 | -0.3150141073101529 | -0.3150141073101529 | -0.3150141073101529 |
| H3 | SWITCH | -0.157503491576509 | -0.7325026216050797 | -0.7325026216050797 | -0.157503491576509 | -0.157503491576509 |
| H3 | MEMBER_CHANGE | -0.7331120450139224 | -0.7330898517001428 | -0.7331120450139224 | -0.7331120450139224 | -0.7331120450139224 |

### MAE、动作排序与HF regret

各版本MAE有效分母均为6；H2/H3分别报告，不能将六格解释为六个独立随机样本。近似最优集合沿用epsilon=1e-8。

| 版本 | MAE | H2/H3严格动作排序 | H2/H3近似最优动作 | H2所选动作HF regret | H3所选动作HF regret |
|---|---:|---|---|---:|---:|
| P1 | 0.32229275060815804 | KEEP > SWITCH > MEMBER_CHANGE | KEEP / KEEP | 0.1462338844540494 | 0.1575106157336439 |
| P2 | 0.1897869214629245 | KEEP > SWITCH > MEMBER_CHANGE | KEEP / KEEP | 0.1462338844540494 | 0.1575106157336439 |
| P3 | 9.25185853854297e-18 | SWITCH > KEEP > MEMBER_CHANGE | SWITCH / SWITCH | 0.0 | 0.0 |
| P4 | 9.25185853854297e-18 | SWITCH > KEEP > MEMBER_CHANGE | SWITCH / SWITCH | 0.0 | 0.0 |

### 两因素效应与交互

沿用原定义：A0=P2−P1，A1=P4−P3，B0=P3−P1，B1=P4−P2；平均效应及完整数值见既有[SCIENTIFIC_ANALYSIS.json](SCIENTIFIC_ANALYSIS.json)。下表直接引用已保存的A0、B0与交互项I=P4−P3−P2+P1。

| 世界 | 动作 | 传播效应A0 | 反馈效应B0 | 交互效应I |
|---|---|---:|---:|---:|
| H2 | KEEP | 0.3974952941219212 | 0.3974952941219212 | -0.3974952941219212 |
| H2 | SWITCH | 0.0 | 0.5637223987489761 | 0.0 |
| H2 | MEMBER_CHANGE | -2.2193313779506063e-05 | -2.2193313779506063e-05 | 2.2193313779506063e-05 |
| H3 | KEEP | 0.3974952941219212 | 0.3974952941219212 | -0.3974952941219212 |
| H3 | SWITCH | 0.0 | 0.5749991300285707 | 0.0 |
| H3 | MEMBER_CHANGE | -2.2193313779506063e-05 | -2.2193313779506063e-05 | 2.2193313779506063e-05 |

原始输出见[ALL_RESULTS.json](ALL_RESULTS.json)、[P2_RESULTS.json](P2_RESULTS.json)、[P3_RESULTS.json](P3_RESULTS.json)、[P4_RESULTS.json](P4_RESULTS.json)及`RAW/`。反馈与逐拍证据见[FEEDBACK_VALIDATION.json](FEEDBACK_VALIDATION.json)、[FEEDBACK_BATCH_ATTRIBUTION.json](FEEDBACK_BATCH_ATTRIBUTION.json)、`FEEDBACK/`、`TRACE/`和`ANALYSIS/`；实际配置与源码身份见[EXPERIMENT_CONFIG.json](EXPERIMENT_CONFIG.json)及[joint_entry.py](joint_entry.py)。

## 三、独立审核证据登记

以下数量与结论来自独立审核员已经完成的正式核验，由主研员接受，并非Codex在本次登记中新开展的核验：

- 299个历史生成反馈事件的身份及估计内容得到核验。
- P3/P4合计460次实际反馈消费得到核验，其中452次接受、8次拒绝。
- 未发现重复消费、提前消费或无身份绑定消费。
- 六组P3/P4回放同源性得到确认。
- D80/D100历史belief、接受位置历史、receipt及终端consumer状态得到确认。
- 36/36项物理及服务状态连续性检查通过。
- F1—F4、B01—B04及R1—R4通过有限科学验收。
- 24格经济账本、价值误差、动作排序、HF regret及交互项通过独立复核。

这些结论保持其有限科学验收范围，不替代原始证据，不将未验证的资源或依赖门槛提升为VERIFIED。

## 四、正式接收的科学发现

**机制A：** 取消一秒传播截断，使当前H2/H3 KEEP恢复任务完成能力，但未纠正动作选择。

**机制B：** 固定历史MODEL反馈纠正H2 SWITCH的速度先验失配及H3 SWITCH的位置先验失配，恢复任务完成及正确动作排序。

**机制交互：** KEEP存在非加性机制替代与收益重叠。P4相对P3没有额外净价值收益，不代表不存在交互效应；KEEP的非零交互项按实际结果保留。

**预测与决策关系：** 依据已接受的独立科学裁定，P2降低总体MAE约41.11%，但使错误KEEP动作的预测价值优势扩大约20.88倍，实际HF regret保持不变。误差改善不能自动解释为决策改善。

**MEMBER_CHANGE：** 反馈改变belief、预测和控制，但未恢复任务完成能力。该负面结果完整接收，不删除、不重新解释为实现失败。

## 五、科学解释限制

- P3/P4是固定历史MODEL信息流条件下的反事实机制诊断，不证明自主获得同等质量未来观测的能力，也不证明反事实机器人轨迹下的实际可观测性。
- 近零MAE表示净价值在数值精度上与HF一致，不代表全部科学状态或算法严格等价。
- 历史WLS信息的生成成本未计入本次回放诊断，不能据此证明新代理相对于HF的计算效率优势。
- H2/H3是两个确定性冻结世界，不支持总体统计推断。
- 本次结果不证明STFBS-Lite、Minimax Regret或生产算法具有普遍性能优势。
- D60以前部分来源继续保留SOURCE_UNRESOLVED。

## 六、资源及完整正式门槛限制

直接保留[RESOURCE_RECEIPT.json](RESOURCE_RECEIPT.json)的实际记录：

| 指标 | 已记录数值 |
|---|---:|
| CPU已测小计 | 4.671875秒 |
| 已记录墙钟 | 772.2090979009226秒 |
| 累计受控逻辑写入 | 38541580 bytes |

`RESOURCE_ACCOUNTING = INCOMPLETE`，`RESOURCE_COMPLIANCE = NOT_ESTABLISHED`。完整依赖闭包及最终证据封存仍为NOT_VERIFIED。未知资源不记零，不重新计算历史余额；此前Stage A历史334.8579769秒超时及未知资源记录保持原状。

探索性科学接收不等于完整V0.5正式验收通过。原始[V05_FINAL_STATUS.json](V05_FINAL_STATUS.json)保持`L3_B_BLOCKED`，不因本次接收而回写或撤销。

## 七、最终登记状态

```ini
P1_STAGE = CLOSED
P1_BASELINE = FROZEN

P2_SCIENTIFIC_ACCEPTANCE = PASS
P3_SCIENTIFIC_ACCEPTANCE = PASS
P4_SCIENTIFIC_ACCEPTANCE = PASS

NEW_VALID_DIAGNOSTIC_CELLS = 18/18
COMPLETE_VALID_MATRIX = 24/24

F1_FEEDBACK_IDENTITY = VERIFIED
F2_FEEDBACK_QUEUE_AND_TIMING = VERIFIED
F3_PHYSICAL_SERVICE_CONTINUITY = VERIFIED
F4_FEEDBACK_ATTRIBUTION = ACCEPTED

HYPOTHESIS_A = SUPPORTED_IN_TESTED_CASES
HYPOTHESIS_B = SUPPORTED_UNDER_FIXED_FEEDBACK

KEEP_INTERACTION = NON_ADDITIVE_SUBSTITUTION
P4_INCREMENTAL_VALUE_OVER_P3 = ZERO
VALUE_ACCURACY_DECISION_DIVERGENCE = VERIFIED

EXPLORATORY_SCIENTIFIC_ACCEPTANCE = ACCEPTED_WITH_LIMITATIONS
BLOCKERS_TO_EXPLORATORY_ACCEPTANCE = NONE

SCIENTIFIC_REEXECUTION_REQUIRED = NO
ADDITIONAL_ENGINEERING_TESTS = NOT_REQUIRED
NEW_STAGE_A_REMEDIATION = NOT_REQUIRED

RESOURCE_ACCOUNTING = INCOMPLETE
RESOURCE_COMPLIANCE = NOT_ESTABLISHED

L3_B_EXPLORATORY_STAGE = CLOSED
V05_FORMAL_STATUS = L3_B_BLOCKED
PRODUCTION_ADMISSION = BLOCKED

L3_C_EXECUTION_AUTHORIZATION = NOT_GRANTED
```

本次仅新增本验收登记文件，不进行仓库提交或同步操作，不启动L3-C；正式关闭已经通过有限独立科学验收的探索阶段。
