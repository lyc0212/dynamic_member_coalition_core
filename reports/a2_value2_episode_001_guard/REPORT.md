# A2-VALUE-2E 双窗口场景收益对照

## 版本、执行与证据

专用 LOCKED 入口及其动态分叉测试通过。新增 4 项入口测试，全量 146 项通过，见 `reports/a2_value2e_entry_preflight_001` 下的测试日志及入口审查报告。入口 SHA256 为 `fec8fdafb0092ad8a326f01f7b1587a546431f982bbe9a52b5ec75542b06d438`。

| 冻结对象 | SHA256 |
|---|---|
| 新世界 | `d5bc8f31cc889773936cdce9af43655fa8733b0e7f4ed2cf030e302119d944a5` |
| 公开公告 | `80853bbd59c1f06b1864819a98c9fae7090cbca99bbedfc9ab9198d07b5daed0` |
| 预登记协议 | `6edfc587c03c7202808be2c1241119e0196d14bf669f802ef431cde8df211494` |

执行顺序为新 OPEN、OPEN 独立验收、冻结复核、新 LOCKED。两个配对调用分别由 PowerShell 外部进程实施 1800 秒整轮上限。命令、时间、退出码见同目录命令文件、`TIMING.json` 和 `status.txt`。历史 255 项、冻结输入和新增入口逐文件指纹见 `BEFORE.json /pins` 与 `AFTER.json /pins`。新 OPEN 原始输出在 LOCKED 开始前计算摘要，复核时再次检查。原算法与既有实验均保留。

## 首次分叉与逐轮决策

首次实际动作分叉为 **tick60，3 秒**。此前逐模式严格核对 tick0、20、40 的完整公开状态、观测消费、候选表及 STEP。tick60 先比较相同科学状态和原无约束表，再识别动作差异。只接纳固定路径上的实例、流、帧、包和可重算摘要差异。见 `PRE_FORK_COMPARISON.json /cuts`、`/forks`，以及两组原始 `{mode}_D{tick}.json /policy_input`、`/choice`、`/step`。

| 决策 tick | OPEN 无约束 / 实际 | LOCKED 无约束 / 实际 | OPEN 候选 / 合法 | LOCKED 候选 / 合法 / 可行 | LOCKED 保护 |
|---:|---|---|---|---|---|
| 0 | C0 / C0，首次分配 T0 | C0 / C0 | 6 / 7 | 6 / 7 / 7 | 无 |
| 20 | C0 / C0，KEEP T0 | C0 / C0 | 6 / 7 | 6 / 7 / 7 | 无 |
| 40 | C0 / C0，KEEP T0 | C0 / C0 | 6 / 7 | 6 / 7 / 7 | 无 |
| 60 | C6 / C6，转派 T1 | C6 / C0，KEEP T0 | 12 / 13 | 12 / 13 / 1 | T0，0.60 秒 |
| 80 | C6 / C6，KEEP T1 | C0 / C0，KEEP T0 | 12 / 13 | 12 / 13 / 1 | T0，1.60 秒 |
| 100 | 空闲 / 空闲 | 空闲 / 空闲 | 6 / 7 | 6 / 7 / 7 | 无，T0 已完成 |

每行在 R 与 S_NEW 一致。两组一直使用 U0/U1 的原角色，U2 空闲。tick60 T1 首次合法可见，均为 PRIOR_ONLY。OPEN 的 C6 预测净边际约 **+0.588435**，C0 KEEP 约 **+0.417491**，相差 **+0.170944333**。C6 的精确目标值为 `-41523928784916923/288230376151711744`，C0 为 `-354669055230257/1125899906842624`。OPEN 撤离 T0，0.60 秒清零，T1 首次分配，费用 0.02。LOCKED 的约束只排除 12 个不保留原团队的计划，候选价值均保持。见两组原始 `R_D60.json /choice`、`/evidence`、`/step/action_commit` 与 LOCKED `/locked`。各轮完整可见目标、精确目标值、实际进度、事件及费用汇总在 `WINDOW_ANALYSIS.json /groups/*/rows`，锁定有限计划逐项复核在 `PLAN_AUDIT.json /modes`。

## 双窗口与实际观测

| 检查 | 条件式预算 | 实际结果 |
|---|---|---|
| OPEN T1 第一个持续合格端点 | tick74，3.70 秒 | tick74 首次 G/Q 同时合格，此后连续 |
| OPEN T1 实际连续区间 | 21 个 | tick74–95 共 21 个，无重置 |
| OPEN T1 完成和余量 | tick95，4.75 秒，余 1.25 秒 | tick95 完成，25 个物理步余量，超过四步目标 |
| LOCKED T0 保持及完成 | tick80 进度 1.60 秒，tick93 完成 | 相符，持续合格，未提前解锁 |
| LOCKED 再分配 | tick93 自然释放，tick100 最早再分配 | 相符，释放不收费。到终点至多 20 个区间，少于 T1 所需 21 个 |

OPEN 在 tick60 生成 T1 首次合格实际 WLS，tick80 才消费，初始动作没有使用这批观测。更新后 T1 位置约为 (9.05, 10.29)，速度约 (0.02, 0)，当时进度 0.30 秒。控制随后跟踪更新后的 belief，优化器仍选择原团队。这个记录显示更新后继续服务，未做反事实消融来判断更新是否是继续服务的必要条件。tick95 T1 完成并免费释放，tick100 OPEN 对剩余 T0 选择空闲。LOCKED 在 tick100 对剩余 T1 也选择空闲，T1 全程无分配及实际观测。见 `R_D60.json /step/fusion_records`、`R_D80.json /policy_input/beliefs`、`/step/frames`、`R_D100.json /choice` 以及两组 `R.json /observations_consumed`、`/final/state/archives`。

## 独立复核方法

从保存候选表重新枚举完整合法计划，以 Fraction 复核目标值、保护可行性及规范平局。利用原始端点、角色和冻结 belief 重算控制与位置积分，并按真实轨迹核查 bearing 和几何。使用保存的 WLS 诊断复核 Q、观测消费和估计更新，逐区间重算双端点服务时钟、自然释放、费用与终端账本。本轮没有重新求解 WLS 优化。两组分别复核原生 PAIR_CHECK 和逐轮严格比对，R/S_NEW 是同一场景的两个计算实现。见 `PLAN_AUDIT.json`、`PHYSICAL_RECHECK.json` 和两组原生 `PAIR_CHECK.json`。

## 真实账本与有效性

两组均到达 tick120，每模式六轮均 COMMITTED。OPEN 耗时 154.330 秒，LOCKED 耗时 170.335 秒，退出码均为 0。HEAD 为 `19f6ed13330907765fb6324f02431b5c0170176e`。OPEN 在 tick80 消费了 T1 的 21 份合格实际估计；每模式全程共 97 份融合收据及 97 条消费记录。LOCKED 对应为 94 份和 94 条，均来自 T0。各组实际观测独立。

| 组 / 目标 | 实际结局 | 计费迟到 | 完成 | Flow | Late | Effort | Terminal | 分配费 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| OPEN T0 | 撤队后未完成，终点进度 0 | 4.00 秒 | 0 | −0.025 | −0.050 | −0.000042047 | −0.25 | −0.02 |
| OPEN T1 | 4.75 秒完成，1.05 秒连续服务 | 0 | +0.1875 | −0.0109375 | 0 | −0.000002501 | 0 | −0.02 |
| LOCKED T0 | 4.65 秒完成，2.25 秒连续服务 | 2.65 秒 | +0.125 | −0.019375 | −0.033125 | −0.000056154 | 0 | −0.02 |
| LOCKED T1 | 未获分配、未完成，进度 0 | 1.00 秒 | 0 | −0.01875 | −0.01875 | 0 | −0.375 | 0 |

分配费按获派目标归属。每架参与机器人在 OPEN 组占用 4.75 秒，LOCKED 组占用 4.65 秒。OPEN T0 的撤队是本场景唯一正进度清零事件。逐任务证据见 `WINDOW_ANALYSIS.json /groups/*/tasks`，原始结局在两组 `R.json /final/state/archives` 及 S_NEW 对应记录。

| 收益项 | OPEN | LOCKED | OPEN − LOCKED |
|---|---:|---:|---:|
| Completion | +0.187500000 | +0.125000000 | +0.062500000 |
| Flow | −0.035937500 | −0.038125000 | +0.002187500 |
| Late | −0.050000000 | −0.051875000 | +0.001875000 |
| Effort | −0.000044547879 | −0.000056154406 | +0.000011606527 |
| Terminal | −0.250000000 | −0.375000000 | +0.125000000 |
| Assignment 费用 | −0.040000000 | −0.020000000 | −0.020000000 |
| **净值** | **−0.18848204787896372** | **−0.36005615440629396** | **+0.17157410652733024** |

保存的 binary64 总账精确差为 `3090804328891641/18014398509481984`。六分项和与总差的舍入残差为 `-1093/73786976294838206464`，符合复算容差。主要优势是较高价值 T1 的完成奖励与终端惩罚差，合计 +0.1875，超过额外分配费。原始总账见两组 `R.json /metrics`，精确分项见 `VALUE_COMPARISON.json /exact_delta`。

条件式 +0.171574107 与实测值在展示精度下一致。本次恰好兑现了该估算所假设的两项完成结局、完成时刻及分配费用。该比较用于核对设计预算，不能充当对未来滚动闭环预测精度的评价。

`ACCEPTANCE.json` 给出全部验收状态。ENTRY_FROZEN、FROZEN_INPUTS、PRE_FORK_COMPARABILITY、OPEN_POLICY_COMPLIANCE、LOCK_POLICY_COMPLIANCE、CONSTRAINED_EXACT_OPTIMUM、PHYSICAL_ACCOUNTING、R_S_NEW_CONSISTENCY、DELTA_J_VERIFIED 均为 PASS。两组 EXECUTION 均 COMPLETE，PHYSICAL_WINDOW 和 AUTONOMOUS_SWITCH 均 OBSERVED，REALIZED_VALUE 为 POSITIVE，VALUE2_VALIDITY 为 **VALID_POSITIVE**。

本次取得了真实改派有利的存在性证据，与 VALUE-1 的负例互补。两个场景之间同时改变了 T1 的真实出生位置和速度，因而只能把两例用于形成有关先验误差、连续服务建立时间及改派收益边界的假设。尚未识别两个改动各自的贡献，两个刻意设计场景也无法估计平均收益或改派有利的频率。本轮在唯一一次新 OPEN 和新 LOCKED 对照完成后停止。
