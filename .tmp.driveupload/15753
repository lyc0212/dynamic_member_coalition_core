# STFBS-Lite D1-A 中断恢复与收尾验收

## 结论

**D1_A_BLOCKED：G3 完整任务历史语义不成立。** 不是以“实现未完成”代替阻断，也不是认为 MODEL 正差额无效便重新调参。原授权要求完整 A2 状态语义，但现有记录直接违反服务历史覆盖与互斥约束，不能签发 D1_A_MODEL_PAIR_VALIDATED。

本地HEAD为b2a544ae9edabbc2c620236f0f154a0942169b48，起始工作树干净；GitHub连接器compare确认main与本地一致。已读取现有源码、测试、原V1.3授权及已有全部运行归档。本轮仅新增只读核验材料和本报告，不改运行内核、不执行测试中的物理步骤、不运行主H1、不调用估计器、不提交或推送。

## 实际执行状态及历史

上一轮已实现MODEL原型和审计辅助，并产生三组完整MODEL运行，不是只做过早期G0。本轮不采用早期进度描述覆盖后续事实。两次早期失败分别涉及JSON目标键与Fraction测试解析；对应FIRST/RETRY日志均保留。之后又补充MODEL历史摘要及CPU记录，三组工程尝试原样保留。

## 三组运行身份与成本

engineering_attempt_001、engineering_attempt_002和根目录的H1_CONTRACT.json字节SHA256相同，PLAN_SELECTION.json亦相同，MODEL_PAIR_RESULT.json亦相同。H1绑定公开D60及恢复seed摘要，三组没有选择不同的世界或计划。详细原值、摘要、运行时间在closeout_001/RUN_COMPARISON.json。

每组成对运行MODEL_OBSERVATION_WLS=71、MODEL_POLICY_EVALUATION_WLS=1184、MODEL_TOTAL_WLS=1255，ACTUAL_WLS=0。三组累计分别为213、3552、3765、0。三组墙钟记录合计68.6162626秒，单次最终外部墙钟22.3904867秒、进程CPU21.0625秒；COST中算法范围CPU20.140625秒、墙钟20.7298557秒。这些范围不同，不混用。前两组没有保存实际CPU数值，不能重建精确累计CPU；不能把CPU上限当实测。早期合成测试和探索命令也没有完整全局估计器计数账本，不虚报“总研发成本精确已知”。

三组描述性MODEL收益相同：KEEP=-0.3150141073101529；SWITCH=-0.144065068155969；差额+0.17094903915418388。它们不是三个独立科学样本，也不是ACTUAL收益结论。三组结果一致不能替代状态语义验收。

## 实质性G3差异与源码证据

以根目录SWITCH_RAW.json为例：decisions[0].view为D80。T1 histories中active_segment_id=SWITCH:1:60，同时unassigned_intervals保留start_tick=60、end_at=null的出生未分配区间，等于声称D60-D80既在服务又未分配。T0在D60撤离后active_segment_id=null，却没有当前开放的未分配区间；D100同样缺失。三组记录共找到9项同类违反，逐项字段路径及原值见closeout_001/G3_HISTORY_FAILURE.json。

原public.py::_history（217行起，尤其246-269行）要求服务段与未分配区间无重叠、无未解释空缺，且活跃任务恰好有一个当前分配/未分配状态。原execution.py::_prepare_boundary_state（534-558行）在WITHDRAW时增加未分配区间，分配新团队时关闭开放区间并登记关联事件。

新增stfbs_d1a_model.py::Branch.assign（91行起）只关闭旧服务段、改变active_segment_id和建立新段，没有对应维护unassigned_intervals及事件链接。现有stfbs_d1a_verify.py::verify只核对活动团队、端点和历史摘要，没有验证完整区间覆盖。因此摘要正确并不能证明历史内容合法，原局部PASS漏掉了这项契约。

这是执行状态语义差异，不能以policy.decide恰好能消费某几个字段、或者账本分量相加一致为由忽略。它可能不改变本例保存的选择数值，但不能据此声称满足原完整A2视图要求。

本轮授权只允许审计辅助，不允许改变已保存运行结果；发现实质差异后按停止规则不修改内核、不重写历史、不自动重跑。修复必须涉及MODEL历史事务和独立完整历史验证，不能只重算摘要或放宽验收；本报告不授权该后续工作。

## G0—G5真实状态

详细矩阵见GATE_MATRIX.json。G0已证明历史belief重放和消费顺序，H1最低当前事实检查有局限通过；G1已有消费器及合成差分测试；G2已有受约束选择与独立计划表对照。这些均有有效局部证据。G3完整历史语义FAIL。G4已有算术账本和局部物理检查，但G3前置失败，完整链路NOT_VALIDATED。G5已有单次和累计WLS核对，累计CPU及全部辅助测试成本未完整记录。没有把G1-G5误写为“全部未执行”，也没有把局部通过扩大为总体通过。

已有模型控制、位移、停止时间、时钟、D60左右端点和D80/D100belief核验结果继续保留；本轮没有通过重新模拟来补足它们。ACTUAL WLS保持0。H1仍是公开条件世界，不能作为私有实际未来的恢复，也不证明STFBS-Lite提高真实系统收益。

## 新增材料及停止

本轮新增REPORT.md、ACCEPTANCE.json、GATE_MATRIX.json、TEST_RESULTS.json，以及closeout_001中的身份/成本对比、具体历史违反和源码指纹。原失败日志、三组原运行、已有源码与测试不覆盖。最终指纹见closeout_001/SHA256.json。

本任务至此停止，无活跃主运行，无新H1或新计划，无D1-B/C/D、DEV/TEST、ACTUAL实验或B/C/A3开发。
