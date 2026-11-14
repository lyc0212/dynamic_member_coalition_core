# A2 最小科学实施记录 V1.1

本轮交付代码、独立输入、短区间测试和运行入口。完整 6 秒 A2 实验尚未执行，正式动态竞争、正收益竞争和实际策略改派均待观察。

## 实现与调用顺序

- `research/non_oracle/environment.py` 增加 `StaggeredEnvironment`。复用世界的物理激活、服务和事务，校验公告与出生必须落在同一合法决策 tick。A1 原入口仍只接受同时出生。
- `belief.py` 增加延迟初始化选项。只有已出生且到达公告时刻的任务才能初始化 belief，未公告任务的实际观测会被拒绝。原 WLS 准入、速度差分、1 秒过期与退化规则保持原样。
- `policy.py` 允许显式 `A2_POLICY_INPUT` 进入现有非 Oracle 预测与求解。目标函数、候选计算、缓存键和 tie rule 保持原样。
- `a2_analysis.py` 对每轮独立穷举合法 Assignment，用 Fraction 检查最优值、实际选择和规范 tie rule。净边际以完整单目标方案减去全空闲方案计算，包含相对当前 Assignment 的改派费用。
- `scripts/run_a2.py` 保存逐轮策略输入、预测、精确计划证据及真实 STEP。两模式完成后，复用现有严格比较和固定运行身份映射。

世界先完成上一物理区间并激活新任务。策略在决策切口发布已到时公告，初始化新 belief，再消费已经可用的实际观测、冻结视图、评价和求解。动作提交后产生的同 tick 观测留到下一个切口。完整世界和公告文件仅供驱动及事后核对，策略接收当时合法可见的任务。

## 输入摘要

| 输入 | SHA256 |
|---|---|
| configs/a2_two_target_staggered_min.json | fba10d9e4bd2a9d2d30ce6ff5c1d6e65fea1ad37aa086dbc112a8348395e35d8 |
| configs/a2_public_announcements.json | ceb4e1854193f90e6fe3028baa52b20b5a8cdf3a4a9659a85e2f241d57821fb6 |

T1 在 3 秒出生，公开先验为 (9.0,10.3)，deadline 5.5 秒。A0 世界及 A1 通告摘要仍与冻结值一致。保留用户原有 `.gitignore` 改动。

## 证据与验收边界

`evidence.targets` 保存出生、公告、首次实际策略可见 tick、初始 belief tick、公告年龄、最近合格观测的年龄及实际接受回执。PRIOR_ONLY 的观测年龄和时间为空。重复或被拒绝的样本不能覆盖当前估计的消费来源。冻结有效位置和速度来自既有轨迹函数，WLS 诊断仍为诊断信息。

`choice.rows` 与 `evidence` 保存候选和计划预测，`step` 保存实际控制、G/Q、时钟、事件、费用及结算。仅在所选联盟、相同端点或相同执行窗口内比较预测和实际。未选候选没有实际收益。结构互斥与正边际分别记录，不以日志推断未服务任务的反事实收益。

针对性测试使用真实物理前缀到 tick60，再以合法注入动作验证 KEEP、跨目标转移、换员、角色变化和完成释放。分支最多推进到 tick80，均未运行完整 120 tick。测试验证公告前的隔离、首次激活、变更私有真值时策略视图和选择不变、同 tick 观测不回填、精确计划计数及缓存隔离。人工注入动作不是实际优化器行为。

测试命令 `D:\anaconda3\python.exe -B -m unittest discover -s tests -v`。最终日志 `reports/a2_final_tests.log`。

## 首次正式运行建议，等待单独授权

```powershell
& 'D:\anaconda3\python.exe' -B scripts/run_a2.py --world configs/a2_two_target_staggered_min.json --announcements configs/a2_public_announcements.json --output runs/a2_staggered_001
```

入口依次运行 R/S_NEW，物理时域 6 秒。执行前冻结源码和输入摘要，确认输出目录不存在，使用与 A1 相同的外部 Start-Process / WaitForExit(1800000) 整轮护栏，单独保存标准输出和错误日志。1800 秒是预算上限；A1 两模式 138.76 秒只作为本地参考。超时保留输出，不自动重试。

正式结果分别判断工程与信息机制、服务中重叠、正边际竞争、实际改派、服务结算、模式一致性和各目标的信息饥饿。尤其在 tick60 核对旧团队是否仍活跃及已结算进度是否为正。当前测试未证明正式场景必然出现这些现象。

全量回归结果为 **123/123 通过**，含 A2 新增 10 项、A1 23 项、A0 工具 85 项和 Oracle CLI 5 项。日志记录的 unittest 用时为 159.374 秒，仅为测试时长。尚无正式 A2 实验结果。

最终核对时本地 HEAD 为 `7055a2a`。工作期间本地已有提交更新，本次执行未调用 Git commit 或 push。最终工作树仍有 A2 证据代码、入口、测试的未提交差异和本实施记录，正式运行前应以当时的实际文件摘要为准。
