# D1-A G3 MODEL 历史事务有限修复

## 最终结论

**G3_HISTORY_REPAIR_READY_FOR_REVIEW**。D1-A总体仍为**D1_A_BLOCKED**，没有运行主H1复验，也不代表完整G3或G0—G5通过。

起始HEAD为3efee920c4bf9034179a1fbca950c5dd6940bcd9，工作树干净。仅修改授权的stfbs_d1a_model.py和stfbs_d1a_verify.py，新增两个隔离MODEL辅助模块stfbs_d1a_history.py（事务准备）及stfbs_d1a_history_audit.py（只读独立图审计），新增test_stfbs_d1a_history_repair.py。拆分必要性是避免主修改器同时充当自己的历史正确性判据。没有修改冻结科学模块、旧配置或旧报告。源码前后副本、REPAIR.diff与SOURCE_PINS.json保存实际变动。

## 三阶段边界事务

A阶段完整验证动作字段、目标活跃性、人数/角色及原历史，不改变正式分支。B阶段深拷贝分支的历史、事件、缓存、融合流、consumer与pending，在暂存对象中建立历史和必要端点。C阶段重新核验历史、费用及分支端点身份后，统一更新分支字典。

budget使用共享计算账本，不回滚已经发生的计算计数；这与正式状态原子性分开。测试通过一个明确标记为人工的预算令牌证明该账本不随失败消失，该令牌不是一次真实WLS。本轮真实WLS为0。真实估计器副作用不在本轮执行验收范围，但现有实现对可变融合流/缓存/队列采用深拷贝暂存，实际计算账本单独保留。没有声称可以撤销任意外部I/O或恶意回调；生产融合路径不新增此类外部权限。

故障注入覆盖动作验证、准备之前、融合准备过程中、融合之后、最终提交前；正式状态pickle字节在失败前后完全一致，覆盖费用、边界记录、事件、缓存和pending。提交前故意破坏暂存历史，也被最终复核拒绝。

## 生产与MODEL语义映射

| 转移 | 修复后的MODEL行为 | 生产依据 |
|---|---|---|
| KEEP | 原段/时钟/左端点不变，下一融合从下一tick开始 | execution.py:: _prepare_boundary_state 528行起 |
| FIRST_ASSIGNMENT/REASSIGN | 关闭开放未分配区间，关联ASSIGNED事件，开零时钟新段 | execution.py 545—558 |
| WITHDRAW | 关闭原段，关联WITHDRAWN事件，开启未分配区间 | execution.py 534—544 |
| MEMBER_CHANGE/ROLE_CHANGE | 同切口闭旧段开新段，无虚构未分配时间 | execution.py 534—558 |
| UNCHANGED_UNASSIGNED | 保留当前未分配区间，无虚假服务段 | public.py::_history 246—269 |
| COMPLETED/ESCAPED/EPISODE_END | 关闭当前服务段或未分配区间，唯一终止事件，免费自然释放 | execution.py::_finish 577行起 |

新增事件包含SIMULATED/MODEL来源和分支身份，索引在既有全局事件索引之后递增；历史原ACTUAL事件保留。新MODEL段身份摘要绑定分支、任务、团队/角色、索引、前驱和开始tick，不冒充ACTUAL checkpoint。继承段身份仍用原纯身份函数核验，不重新生成ACTUAL端点。

## 独立历史审计

新审计器从段、间隙和事件图独立重建覆盖，验证任务出生至切口/终止时刻连续覆盖且不重叠；活跃状态唯一；团队、时钟、端点、顺序与前驱；段开启/关闭事件的完整引用；关闭原因、时刻与进度；MODEL来源；终止后没有开放区间或占用团队。费用另从完整Assignment边界重算，拒绝额外自然释放收费。

摘要不作为语义正确的替代。原verify.py已接入独立历史审计，而不是只验证摘要、活动团队及端点tick。完整成对执行未复验，该接入仍需后续独立审查和明确授权下的整体验证。

## 确定性验收

最终8个测试组全部通过，组内包含多种转移与人工负例。D60/D80/D100的动作前后历史、费用及审计结果见BOUNDARY_AUDIT.json。这里的切口是人工设置的合法状态夹具，没有生成运动轨迹或执行物理STEP。

正例包含KEEP、首次分配、撤离、角色变化、成员变化、持续未分配、完成、逃逸及episode结束。完成测试提供已结算需求时钟；逃逸测试预置MODEL边界位置；episode结束测试关闭全部任务。提前完成、提前逃逸、提前episode结束和重复终止被拒绝。

负例包含删除间隙、错误保留开放间隙、覆盖重叠/空缺、事件索引/引用丢失、段ID/前驱错误、关闭时间/原因错误、终止后残留间隙、费用多收、融合中断和最终暂存状态破坏。它们不依赖摘要失败才能拒绝。

最终测试使用真实调用禁用哨兵保护model.estimate、policy.estimate、核心estimate、BridgeFrameProcessor.process、OnlineEnvironment.step及Branch.advance；全部调用计数为0，见FINAL_IDENTITY_GUARDED_TESTS.json。没有重跑其他包含WLS/物理推进的旧测试，也没有启动ACTUAL或MODEL主实验。

本轮各次测试没有非预期失败，所有中间日志保留；额外检查属于有限修复的逐步加强，不覆盖历史第一次失败。旧D1-A原有失败与工程修复记录同样未动。

## 旧归档回归与限制

三组旧SWITCH归档的六个决策视图仍被新完整审计拒绝，原九项覆盖/唯一性违反保留于OLD_NINE_REGRESSION.json。完整审计可能先发现旧事件闭合格式或旧MODEL身份缺陷，因此没有把“最先报错路径”强行写成全部覆盖错误。人工覆盖负例另外独立证明覆盖检查有效。

旧D1-A目录52个受Git追踪文件均与HEAD内容一致，见OLD_EVIDENCE_INTEGRITY.json。原三组累计3765次MODEL WLS及描述性差额+0.17094903915418388未更改，仍不是算法有效性或ACTUAL收益改善证据。

本次仅证明历史事务和独立历史验证在规定的纯状态/融合替身测试下成立。真实MODEL融合、完整物理转移、旧全部D1-A测试和主H1成对复验都没有执行，不能由本次READY推断已通过。CPU/WLS护栏与完整系统联动也不在本次新验证结论中。

任务到此停止，不提交、不推送、不自动启动H1复验。只有独立审查和新的明确授权后，才可按原H1、原计划、原继续策略开展新MODEL成对复验。
