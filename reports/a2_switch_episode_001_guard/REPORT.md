# A2-S2 双目标自主改派完整实验

R 与 S_NEW 均在 tick120 正常结束。两模式都在 tick60 主动撤离已积累 0.60 秒服务的 T0，转派 U0/U1 至 T1。两次后续决策均保持 T1。T1 最终积累 0.70 秒有效服务，未达到 1.05 秒的要求。T0 未重新获派，两目标均未完成或逃逸，最终净收益为 **−0.7775828814863254**。

## 版本与执行

| 项目 | 记录 |
|---|---|
| 本地 HEAD | `5fc7a2bc95ea30083e355d9b452879793acca7bf` |
| 运行环境 | Python 3.13.5、NumPy 2.1.3、SciPy 1.15.3 |
| SWITCH 世界 SHA256 | `b23661dcb927f814dadc033df37d2aa142a63960ddf4cb60083041c56f3a37b6` |
| SWITCH 公告 SHA256 | `80853bbd59c1f06b1864819a98c9fae7090cbca99bbedfc9ab9198d07b5daed0` |
| 执行 | 从 tick0 启动一次，R 后接 S_NEW，整轮 241.386 秒，退出码 0，外部上限 1800 秒 |
| 冻结检查 | `BEFORE.json` 与 `AFTER.json` 中 HEAD 和逐文件摘要一致，并与 A2-S1 保存的摘要匹配 |

```powershell
& 'D:\anaconda3\python.exe' -B scripts/run_a2.py --world configs/a2_switch_two_target_v1.json --announcements configs/a2_switch_public_announcements_v1.json --output runs/a2_switch_episode_001
```

命令由 PowerShell `Start-Process` 启动，并以 `WaitForExit(1800000)` 保护整次运行。原始记录位于项目内的 `runs/a2_switch_episode_001`，复核结果和日志与本报告同目录。工作树仅列出 A2-S1 的两份未跟踪配置、协议和测试。A2-S2 产物保留在实验输出和报告目录。

## 两模式各六轮决策

两模式在每个 tick 的记录完全一致，R/S_NEW 两列分别对应原始 `R_D{tick}.json` 和 `S_NEW_D{tick}.json`。表中的净边际均以该轮全空闲计划为基准，计入 Assignment 变化费。每轮由规范候选目录独立生成完整计划，复算精确目标值、最优候选及平局规则。

| tick | R | S_NEW | 候选 / 计划 | T0 最佳净边际 | T1 最佳净边际 | 该轮结束实际进度 T0 / T1 |
|---:|---|---|---:|---:|---:|---|
| 0 | C0，首次分配 T0 | C0，首次分配 T0 | 6 / 7 | +0.112499093 | 未公告 | 0 / 未出生 |
| 20 | C0，KEEP T0 | C0，KEEP T0 | 6 / 7 | +0.019970077 | 未公告 | 0 / 未出生 |
| 40 | C0，KEEP T0 | C0，KEEP T0 | 6 / 7 | +0.150819781 | 未公告 | 0.60 / 0 |
| 60 | C6，SWITCH 至 T1 | C6，SWITCH 至 T1 | 12 / 13 | +0.417490599 | +0.588434932 | 0 / 0 |
| 80 | C6，KEEP T1 | C6，KEEP T1 | 12 / 13 | −0.000008588 | +0.019972543 | 0 / 0 |
| 100 | C6，KEEP T1 | C6，KEEP T1 | 12 / 13 | −0.000001141 | +0.019987535 | 0 / 0.70 |

证据字段为每轮 `/choice`、`/evidence` 和 `/step/frames`。完整排序、逐计划精确值和费用见 `ANALYSIS.json` 的 `/decisions/{mode}/{轮号}/ranked`。

## tick60 自主改派

| 核验项 | 事实 | 原始证据 |
|---|---|---|
| 旧服务 | T0 活跃，U0/U1 正在服务，进度 0.60 秒 | `R_D40.json /step/frames/末帧`、`R_D60.json /policy_input/assignment` |
| 新任务 | T1 在 tick60 出生并公告，首次公开 belief 为 `PRIOR_ONLY`，观测时刻为 null | `R_D40.json /step/events`、`R_D60.json /policy_input` |
| 全空闲精确值 | `-211128750531128827/288230376151711744`，变化数 2 | `R_D60.json /choice/rows`，从该表独立复算 |
| KEEP C0 | 精确值 `-354669055230257/1125899906842624`，变化数 0 | 同上 |
| SWITCH C6 | 精确值 `-41523928784916923/288230376151711744`，变化数 2，唯一最优 | 同上及 `/choice/selected_indices` |
| 最优差距 | C6 比次优 C0 高 `49271349354028869/288230376151711744`，约 0.170944333 | `ANALYSIS.json /decisions/R/3/ranked` |
| 实际提交 | U0/U1 保持原角色转至 T1，U2 继续空闲。T0 的 `WITHDRAWN` 关闭旧段，0.60 秒清零。T1 的 `FIRST_ASSIGNMENT` 新建服务段，从零开始 | `R_D60.json /step/action_commit/transitions`、`/step/events`、`/step/frames/0/progress`，及 `R.json /final/state/histories` |
| 费用 | 本次增 0.02，累计由 0.02 到 0.04。动作边界的其他收益分项保持相等，清零没有额外罚项 | `R_D40.json /step/metrics`、`R_D60.json /step/action_commit` 与 `/step/frames/0/metrics` |

R/S_NEW 从 D0 至 D60 的冻结输入、候选预测、选择、证据与提交 STEP 均复现 A2-S1。唯一获准的差异来自运行包装 `A2_SWITCH_{mode}` 与 `A2_{mode}`，涉及环境、工作实例、流、帧、测量包标识及由帧重算的摘要。复核逐路径验证了这两种命名及摘要关系，路径类别沿用固定契约。

## T1 观测、预测偏差与后续选择

T1 出生时采用公开位置 (9.0, 10.3)、速度 (0, 0)。私有世界中的出生位置为 (9.2, 10.1)，速度 (0.4, 0)。tick60 的 C6 预测在 tick97（4.85 秒）完成。执行和 C6 在 tick60–80 使用同一冻结 belief，实际控制与选中候选的指令在该窗口数值一致至舍入精度。几何判定分别相对于真实运动和预测位置，因此同一控制轨迹可产生不同服务结果。

| tick | C6 预测 G / Q / 进度 | 实际 G / Q / 进度 | 实际最大角色几何误差 |
|---:|---|---|---:|
| 60 | 决策起点 | true / PASS / 0 | 0.139696 |
| 61 | false / PASS / 0 | true / PASS / 0.05 | 0.144202 |
| 62 | false / PASS / 0 | false / PASS / 0 | 0.154909 |
| 80 | true / PASS / 0.20 | false / PASS / 0 | 0.562640 |

容许误差为 0.15。tick62 的质量 Q 仍通过，实际重置原因为 `GEOMETRY_INVALID`。初期实际几何甚至比预测更早合格，随后恢复更慢。同期真实目标继续向正 x 方向运动，机器人仍追踪冻结的静止先验。例如 U0 在 60→61 的实际控制约为 (−0.122893, 0.316488)。因此这段偏差体现了冻结先验与真实运动的差距，当前实验没有隔离初始位置偏差和速度先验各自的贡献。

- **tick80** 消费 T1 在 tick60–80 产生的全部 21 份合格 WLS，首份估计 (9.2, 10.1) 在 tick60 可用、tick80 才消费。更新后位置为 (9.6, 10.1)，速度约 (0.4, 0)。T0 仍活跃、未分配，保留 tick60 最后观测。C6 的新预测已无完成事件，KEEP T1 仍以约 +0.019973 净边际胜过 T0 和空闲。
- **tick100** 消费 T1 在 tick81–100 产生的 20 份合格 WLS。T1 位置为 (10.0, 10.1)，速度约 (0.4, 0)。T0 仍活跃，其 belief 已退化并停止外推。C6 仍无预测完成事件，KEEP T1 再次最优。tick101–120 的 20 份合格观测已生成，时域内已无下一次决策消费。
- 在 tick80 和 tick100，KEEP 相对于全空闲避免了 0.02 的撤队费，再减去当轮预测的运动努力成本，形成约 0.02 的正净边际。后续 KEEP 与预测无法完成可以同时成立。没有二次跨目标改派、换员、角色变化或完成后的自然释放。

原始证据见 `R_D60.json`、`R_D80.json`、`R_D100.json` 的 `/choice/rows`、`/policy_input/beliefs`、`/step/frames`、`/step/fusion_records`，以及 `R.json /observations_consumed`。逐端点控制、位置、真实目标运动、G/Q 及观测复核见 `PHYSICAL_RECHECK.json /R/trace`、`/R/receipts`。所有已执行候选的同窗预测与实际对齐见 `ANALYSIS.json /selected_prediction_actual_alignment`。tick97 的预测完成发生在 D60 控制窗之后，当时系统已经重新决策。

## 全程物理与收益账本

| 项目 | T0 | T1 |
|---|---|---|
| 出生、公告、首次分配 | tick0 | tick60 |
| 首次实际 bearing、合格 WLS | tick0，估计 (8, 10) | tick60，估计 (9.2, 10.1) |
| 首次实际估计消费 | tick20 | tick80 |
| 首次实际 G/Q 同时合格 | tick48，2.40 秒 | tick60，3.00 秒 |
| 服务段和正进度 | U0/U1，tick0–60。tick48 后积累至 0.60 秒，撤队清零 | U0/U1，tick60–120。tick61 到 0.05 秒，tick62 重置。tick106 重新达到双端点积累所需的首个合格端点，到 tick120 积累 0.70 秒 |
| 结局 | 未完成，无完成时间，tick120 归档 | 未完成，无完成时间，tick120 归档 |
| deadline、计费超期 | 2.0 秒、4.0 秒 | 5.0 秒、1.0 秒 |
| 占用 | U0 3 秒、U1 3 秒 | U0 3 秒、U1 3 秒 |
| 原始控制努力积分 | 1.892119326 | 1.837547558 |

U2 全程空闲。每模式逐点复核了 120 个实际物理区间、6 个动作边界、122 份融合收据和 102 条观测消费记录。复核使用冻结 belief 重建控制，按真实轨迹核算 bearing 和角色几何，复查保存的 WLS 诊断和 Q，再以两端点规则重算进度与收益。WLS 优化器未被重新执行。各任务服务段和结束原因见 `R.json /final/state/histories`、`/final/state/archives`。

| 收益项 | T0 | T1 | 合计 |
|---|---:|---:|---:|
| 完成奖励 | 0 | 0 | 0 |
| flow | −0.025000000 | −0.018750000 | −0.043750000 |
| late | −0.050000000 | −0.018750000 | −0.068750000 |
| effort | −0.000042047 | −0.000040834 | −0.000082881 |
| terminal | −0.250000000 | −0.375000000 | −0.625000000 |
| Assignment 变化费 | −0.020000000 | −0.020000000 | −0.040000000 |
| 净值 | −0.345042047 | −0.432540834 | **−0.7775828814863254** |

按新获派任务归属 tick0、tick60 的变化费。逐任务拆分见 `PHYSICAL_RECHECK.json /R/ledger` 及费用归因字段，总账与 `R.json /metrics` 一致。

## 科学验收与边界

| 验收项 | 结果 |
|---|---|
| EXECUTION | COMPLETE，两模式各六轮、全部 COMMITTED、tick120 TERMINAL |
| FROZEN_INPUTS | PASS |
| PREFIX_REPRODUCIBILITY | PASS |
| INFORMATION_BOUNDARY | PASS，公开目标字段与公告一致，冻结 belief 可由实际收据及合法先验重建，无 T1 提前可见或同 tick 回填 |
| POSITIVE_PROGRESS_AT_SWITCH | OBSERVED |
| SWITCH_STRICTLY_OPTIMAL | PASS |
| AUTONOMOUS_SWITCH | OBSERVED |
| WITHDRAWAL_ACCOUNTING | PASS |
| T1_POST_SWITCH_GQ | tick62 几何失效，tick106 恢复，期间质量也曾失效，逐端点见物理复核 |
| T1_COMPLETION | UNFINISHED |
| T0_AFTER_WITHDRAWAL | tick80、100 均活跃、未获派，tick120 未完成 |
| FINAL_SERVICE_ACCOUNTING | PASS |
| R_S_NEW_CONSISTENCY | PASS，逐轮严格比对及物理账本复核通过，原生 `PAIR_CHECK.json` 保留 |

A2 已具备阶段性收尾审查的证据基础。已有场景分别观察到正进度竞争下自主 KEEP 和自主 SWITCH，本次确认了 SWITCH 的真实中断、转移和完整结算。任务层结果是 T1 未完成。两场景的 T0 服务时长、T1 权重和期限不同，真实改派收益优势仍需同场景策略对照。同目标换员、噪声下机制和多目标观测覆盖仍缺独立证据。本轮只执行了授权的一次完整双模式实验。
