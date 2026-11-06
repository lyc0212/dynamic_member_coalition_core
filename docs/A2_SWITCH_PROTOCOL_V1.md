# A2-SWITCH V1.0 受控验证协议

本轮采用用户给定的单一冻结候选，比较正进度服务中的 KEEP 与跨目标 SWITCH。完整 episode 和锁定联盟对照另行授权。

| 参数 | A2-KEEP | A2-SWITCH V1.0 | 设计依据 |
|---|---:|---:|---|
| T0 服务时长 | 1.05 秒 | 2.25 秒 | 旧任务需要更长连续服务 |
| T1 权重 | 1.0 | 1.5 | 新任务优先级更高 |
| T1 deadline | 5.5 秒 | 5.0 秒 | 新任务的时间要求更紧 |

两份输入在运行前生成并计算摘要。独立配置保留三机器人、两个 q2、0 和 3 秒出生、6 秒物理时域、原始控制与观测条件。T1 的 deadline 为软期限，可能降低其预测价值。若旧任务在 3 秒有 0.6 秒进度，T0 还需 1.65 秒有效服务，T1 需要重新建立几何并服务 1.05 秒。两者都有理论时间机会，实际预测和执行由程序计算。

- 世界 `configs/a2_switch_two_target_v1.json` SHA256 `b23661dcb927f814dadc033df37d2aa142a63960ddf4cb60083041c56f3a37b6`
- 公告 `configs/a2_switch_public_announcements_v1.json` SHA256 `80853bbd59c1f06b1864819a98c9fae7090cbca99bbedfc9ab9198d07b5daed0`

一次配对前缀使用现有 StaggeredEnvironment、decide、decision_evidence 和 STEP 比较。D0、D20、D40 的提交动作均来自原优化器。保存 tick60 完整冻结输入、穷举计划和精确目标值。KEEP 保持已有成员和角色，SWITCH 的候选全集为服务 T1 的所有合法角色化方案。仅当正进度条件成立、SWITCH 严格唯一最优且两模式一致，才提交 D60 动作并推进至 tick80。

F1 表示正进度场景条件未满足；F2 表示 SWITCH 严格唯一最优未建立；F3 表示独立计划、选择或实际事务出现差异。F1/F2 保留负例并结束。完整物理结算、实际收益优势和同目标换员属于本轮之外的证据问题。

本地科学源码及输入摘要见 `reports/a2_switch_preflight_001/BEFORE.json`。同目录 `RUN_PREFIX.py` 保存本轮有限取证入口。实施结果单列于同目录 `REPORT.md`。
