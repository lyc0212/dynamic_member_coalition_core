# 源码地图与证据分级

当前 cf730a41e2681efdf8880bc6b142b6deb347ac0d；科学参考 c75f364bf32e6fc63be6a7080d4f21bc6d75ec55；原H1执行 fa42557fd4ee453a27b38ab3644000830246ac42。

## Q三态/严格半径

VERIFIED_BY_FORMAL_H1_OR_INDEPENDENT_AUDIT

- research/information_service/public_quality.py:assess_quality:198–273（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/information_service/public_quality.py:classify_radius:174–180（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/information_service/public_quality.py:FrameProcessor.process:296–336（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/information_service_bridge/public_stream.py:BridgeFrameProcessor.process:52–97（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）

已确认：原H1固定sigma真实WLS/quality/服务审计；源码有严格三态与前置守卫。

未验证：动态sigma导致FAIL及其反事实没有实验结果。

## WLS权重和诊断

VERIFIED_BY_FORMAL_H1_OR_INDEPENDENT_AUDIT

- research/cooperative_sensing/estimator.py:values:17–25（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/cooperative_sensing/estimator.py:estimate:50–97（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/cooperative_sensing/estimator.py:condition:38–41（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）

已确认：五字段公开输入，残差及Jacobian按sigma加权；原H1真实调用。

未验证：单成员sigma动态退化的三态响应未实测。

## ACTUAL动态声明参考

REQUIRES_D1B_END_TO_END_VALIDATION

- research/information_service_online/execution.py:OnlineEnvironment.__init__:299–369（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/information_service_online/execution.py:OnlineEnvironment._profiles:395–397（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/information_service_online/execution.py:OnlineEnvironment._sample:468–482（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/information_service_online/execution.py:ActualMeasurementCache.query:84–112（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）

已确认：源码支持effective_tick有序声明、正有限sigma及available/missing；按tick取最后声明。

未验证：不等于D1A MODEL已有动态profile或延迟公告。

## 实际物理与公开边界

REQUIRES_D1B_END_TO_END_VALIDATION

- research/information_service_online/execution.py:OnlineEnvironment._checkpoint:437–454（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/information_service_online/execution.py:OnlineEnvironment._advance_tick:634–721（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/information_service_online/execution.py:OnlineEnvironment._control_command:629–632（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/environment.py:NonOracleEnvironment.prepare_decision:25–32（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/environment.py:NonOracleEnvironment._control_command:33–36（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）

已确认：基类控制为Oracle，checkpoint含真状态；NonOracle层专门清洗并用冻结belief控制。

未验证：不得直接把ACTUAL控制/checkpoint及ACTUAL-only enqueue用于MODEL。

## D1A固定profile和MODEL接线

VERIFIED_BY_FORMAL_H1_OR_INDEPENDENT_AUDIT

- research/non_oracle/stfbs_d1a_model.py:Branch.__init__:45–64（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_model.py:Branch.raw:68–76（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_model.py:Branch.fuse:77–92（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_model.py:Branch.advance:158–186（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_model.py:Branch.policy_view:187–203（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_model.py:Branch.assign:108–133（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_model.py:Branch.run:204–211（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）

已确认：D1A限定固定profile、联合物理与审计链已接受；profiles构造时固定，view沿用初始声明。

未验证：D1B实际/公开profile接口与预设动作驱动需新适配。

## 缓存身份/上下文

SUPPORTED_BY_HISTORICAL_UNIT_OR_NEGATIVE_TEST

- research/non_oracle/stfbs_d1a_state.py:ModelRawCache.__init__:24–26（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_state.py:ModelRawCache.query:27–48（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_model.py:Branch.raw:68–76（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- tests/test_stfbs_d1a_state.py:StateTests.test_raw_identity_matrix:10–25（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- tests/test_stfbs_d1a_state.py:StateTests.test_inherited_slots:26–30（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）

已确认：同键复用、位置/sigma/health冲突、分支与slot摘要拒绝有历史单位证据。

未验证：真实服务段/流切换、VALID继承、pending/融合状态隔离未专项整体通过。

## belief来源与时序

VERIFIED_BY_FORMAL_H1_OR_INDEPENDENT_AUDIT

- research/non_oracle/stfbs_d1a_state.py:ModelBeliefConsumer.__init__:7–12（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_state.py:ModelBeliefConsumer.enqueue:13–18（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/belief.py:Beliefs.freeze:35–60（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- tests/test_stfbs_d1a_state.py:StateTests.test_model_belief_differential:31–41（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）

已确认：原H1 D80/D100独立重放及历史差分；冻结后新增同tick观测延后消费。

未验证：动态profile/notice账本与新场景须再验证。

## 换员/历史/时钟/费用

SUPPORTED_BY_HISTORICAL_UNIT_OR_NEGATIVE_TEST

- research/information_service_online/public.py:_validate_actions:413–424（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/information_service_online/public.py:plan_action_metadata:435–476（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_history.py:prepare_assignment:24–46（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- pursuit_v2/service.py:advance_clock:87–103（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/information_service_online/execution.py:apply_assignment_boundary:229–236（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- tests/test_stfbs_d1a_history_repair.py:HistoryRepairTests.test_member_role_and_cut_boundaries:50–59（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- tests/test_stfbs_d1a_history_repair.py:HistoryRepairTests.test_atomic_validation_and_prepare_failures:33–49（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）

已确认：MEMBER_CHANGE映射TEAM_CHANGED、完整团队变化清零、逐机器人计费、隔离事务。

未验证：动态Q+新成员真实运动+真实融合的组合未验收。

## 独立审计复用

VERIFIED_BY_FORMAL_H1_OR_INDEPENDENT_AUDIT

- research/non_oracle/stfbs_d1a_history_audit.py:audit_branch_independent:159–162（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_verify.py:verify:11–67（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_audit.py:audit:51–94（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）
- research/non_oracle/stfbs_d1a_audit.py:service_audit:10–49（提交cf730a41e2681efdf8880bc6b142b6deb347ac0d）

已确认：原H1原Branch、控制、服务、belief与经济已独立验收。

未验证：D1B需新增声明时序、同几何Q和四时间核验，不能搬旧PASS。

## 三条链路（不可混用）

ACTUAL参考：OnlineEnvironment._advance_tick → _control_command → _fuse/_sample/_profiles → ActualMeasurementCache.query → measurements.assemble_left_state → sense_callback/WLS/quality → advance_clock → _checkpoint。基类为Oracle；NonOracleEnvironment才将控制改为公开belief，并清洗策略view。本轮不执行这条链。

已验收D1A MODEL：Branch.run → assign/prepare_assignment → fuse/raw → ModelRawCache.query → BridgeFrameProcessor.process → estimator.estimate/assess_quality → ModelBeliefConsumer.enqueue；advance按冻结belief控制并结算服务/经济；policy_view冻结80/100；原run调用R。

拟议D1B（未实现）：合法新MODEL fixture → D1B raw按当前物理profile采样 → 复用真实fuse/WLS/quality/advance → 当前public profile的view投影 → FixedQMController预设B0/B1动作 → 原事务/时钟/经济 → 原审计及动态Q专项。
MODEL条件位置可用于采样和G，不可用作Oracle控制belief。私有schedule不能经公开view/closure泄漏。没有可直接宣称动态Q端到端已经通过的历史证据。
