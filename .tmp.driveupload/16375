# A2 V1.1 首次完整科学实验报告

本轮在 tick60 观察到正进度服务重叠和双方正净边际竞争。优化器选择 KEEP，T0 继续服务并完成，T1 未获分配。本轮验证了服务中的竞争与保持决策，实际服务中改派和同目标换员均未观察到。

## 执行与冻结

本地 HEAD 为 5fc7a2bc95ea30083e355d9b452879793acca7bf。按授权命令执行 scripts/run_a2.py，读取冻结的 A2 世界和公告，输出 runs/a2_staggered_001。唯一一次调用依次运行 R、S_NEW，使用 1800 秒整轮外部护栏。北京时间 2026-11-06 11:28:38.739 开始，11:33:09.459 结束，实测 270.658 秒，退出码 0。前后源码及两份输入逐文件 SHA256 一致，详见 BEFORE.json、AFTER.json 和 TIMING.json。

| 验收项 | 结果 |
|---|---|
| EXECUTION | COMPLETE，两模式各六个 COMMITTED 决策并到达 tick120／TERMINAL |
| INFORMATION_BOUNDARY | PASS，限本轮保存视图、观测来源和控制复核 |
| ASYNC_BIRTH | PASS，T1 在 tick60 出生并首次公告，初始 PRIOR_ONLY |
| IN_SERVICE_OVERLAP | OBSERVED，T0 在 tick60 前已有 0.6 秒真实进度 |
| STRUCTURAL_RESOURCE_COMPETITION | OBSERVED，双目标 12 候选、13 合法计划，三机不能同时组成两个 q2 队 |
| POSITIVE_MARGIN_COMPETITION | OBSERVED，双方最佳单目标完整计划相对空闲均严格为正 |
| ACTUAL_IN_SERVICE_REASSIGNMENT | NOT_OBSERVED |
| ACTUAL_MEMBER_CHANGE | NOT_OBSERVED |
| SERVICE_ACCOUNTING | PASS，有限独立复核控制、积分、bearing、实际 G/Q、时钟和账本 |
| R_S_NEW_CONSISTENCY | PASS，严格比较及两模式复核一致 |
| INFORMATION_STARVATION | T0 获得并消费实际观测；T1 始终 PRIOR_ONLY，无实际 bearing |

## tick60 证据表

路径均相对 runs/a2_staggered_001。S_NEW 对应文件提供相同科学结果。

| 核查 | 实际结果 | 原始文件与字段 |
|---|---|---|
| 决策前 T0 | 活跃，U0／U1 已提交，进度 0.6000000000000001 秒 | R_D40.json 的 step.frames[-1].progress、assignment、statuses |
| 出生及首次可见 | T1 在 tick60 出生并公告，首次可见与 belief 初始 tick 均为 60 | R_D40.json 的 step.events；R_D60.json 的 policy_input.first_policy_visible_ticks、evidence.targets |
| 合法信息 | T0 为 OBSERVED，冻结位置 (9.2,10)、速度约 (0.4,0)，最近观测在 tick60 消费；T1 先验 (9.0,10.3)、速度零、公告年龄零、观测年龄为空 | R_D60.json 的 policy_input.beliefs、evidence.targets |
| 候选覆盖 | 12 候选、13 合法计划 | R_D60.json 的 choice.rows、evidence.legal_plan_count |
| T0 最佳计划 | C0，净边际 126099550428074699/288230376151711744，约 0.437495701；改派费零 | R_D60.json 的 evidence.targets[0].best_single_target_plan、net_margin |
| T1 最佳计划 | C6，同样占用 U0/U1，净边际 434641385050805/1125899906842624，约 0.386039099；两次 Assignment 变化，费用 0.02 | R_D60.json 的 evidence.targets[1].best_single_target_plan、net_margin |
| 最优与次优 | 最优 C0，预测目标值 −2724755220702849/18014398509481984；次优 C6，预测目标值 −58427439386314203/288230376151711744。差为 14831355855068619/288230376151711744，约 0.051456602，最优处无需平局规则破局 | R_D60.json 的 choice.rows、choice.exact_value、evidence.selected_plan；完整独立穷举见 ANALYSIS.json |
| 实际选择与后果 | KEEP T0，T1 保持未分配，进度继承，无费用或重置；T0 于 tick69 完成并免费释放 | R_D60.json 的 step.action_commit.transitions、step.frames、step.events；R.json 的 final.state.archives |

## 两模式逐轮决策

R 与 S_NEW 各自的六轮结果相同。服务 T0 时均为 U0 任 dual_neg45、U1 任 dual_pos45、U2 空闲。下列净边际相对完整全空闲计划并含改派费。

| tick | 候选／合法计划 | T0 净边际 | T1 净边际 | 实际动作 | 区间末进度 |
|---:|---:|---:|---:|---|---|
| 0 | 6／7 | 0.124374145 | 未出生 | FIRST_ASSIGNMENT T0，费用 0.02 | T0 0 |
| 20 | 6／7 | 0.155803452 | 未出生 | KEEP T0 | T0 0 |
| 40 | 6／7 | 0.170819809 | 未出生 | KEEP T0 | T0 0.6，T1 刚出生 |
| 60 | 12／13 | 0.437495701 | 0.386039099 | KEEP T0；T1 UNCHANGED_UNASSIGNED | T0 完成，T1 0 |
| 80 | 6／7 | 已结束 | −0.020004621 | 全空闲，T1 UNCHANGED_UNASSIGNED | T1 0 |
| 100 | 6／7 | 已结束 | −0.020004095 | 全空闲，T1 UNCHANGED_UNASSIGNED | T1 未完成 |

本轮没有 WITHDRAW、跨目标重新分配、MEMBER_CHANGE、ROLE_CHANGE 或正进度重置。唯一非零费用来自 tick0 初次分配。各轮独立穷举复核了完整计划数、精确最优值、规范 tie rule、所选 Assignment 和变化费。

## 任务时间线、信息与收益

T0 在 0 秒出生、公告、分配，并取得首帧实际 bearing 与合格 WLS。tick0 观测在 tick20 消费，未回填 D0。tick20、40、60 的已观测 belief 均采用当前切口已可用的实际观测，观测年龄为零。首个合格服务区间在 tick49 记账，其左端点为 tick48（2.4 秒）。连续积累至 tick60 的 0.6 秒，tick69（3.45 秒）达到 1.05 秒并完成。相对 deadline 2 秒迟到 1.45 秒。U0、U1 各占用 3.45 秒，U2 始终空闲。

T1 在 3 秒出生并公告，至 6 秒未分配、未观测、未服务。tick60、80、100 的公告年龄分别为 0、1、2 秒，观测年龄始终为空。相对 deadline 5.5 秒的未完成逾期时间为 0.5 秒。tick60 是正边际却因较优互斥方案未被选择，tick80、100 则是 PRIOR_ONLY 下预测边际为负。剩余时域、改派费用和其他信息条件下的可服务性仍是未排除的解释，未评估反事实实际收益。

| 目标 | 完成奖励 | flow | late | effort | terminal | 费用 | 归因净收益 |
|---|---:|---:|---:|---:|---:|---:|---:|
| T0 | 0.125 | −0.014375 | −0.018125 | −0.000046346221 | 0 | 0.02 | 0.072453653779 |
| T1 | 0 | −0.0125 | −0.00625 | 0 | −0.25 | 0 | −0.26875 |

两模式原生最终净收益均为 −0.19629634622073616。A1 为 −0.25254634622073624，本轮约高 0.05625，可由 T1 的出生及 deadline 改变造成的 flow 和 late 变化解释。完成情况和总控制努力与 A1 相同，该差值不作为算法改进证据。

## 有限独立物理复核

从保存的冻结 belief 按过期轨迹、角色偏置和限速公式重算全部实际控制及积分。每模式最大控制、位置、bearing 残差为零。每模式复核 70 次实际融合，复用已有质量复核函数而不重跑 WLS。以世界坐标和服务角色独立复算实际 G，用 Fraction 两端点时钟核对各保存帧进度。重算净收益 −0.19629634622073622，与原生账本仅有浮点舍入差异。未套用 Oracle 控制审计。

已选择且时间对齐的 69 个未来预测／实际端点对中，G 有 15 个差异，Q 有 11 个差异。此统计仅针对所执行联盟及实际可对齐端点，未为未选候选虚构结局。两模式 PAIR_CHECK 为 PASS，原始逐轮记录、精确计划与最终科学结算一致。信息边界检查覆盖各切口策略可见字段、观测消费时序及实际控制输入，不构成对任意未来场景的完整审计。

本轮为 A2 阶段收尾和后续阶段审查提供了依据。真实服务中改派、成员更替和对未服务任务的反事实信息收益没有取得本轮证据。仅保留本次运行和复核结果，等待下一次独立决策。

原始输出在 runs/a2_staggered_001。护栏和复核记录在 reports/a2_episode_001_guard，包含 BEFORE.json、AFTER.json、TIMING.json、ANALYSIS.json、PHYSICAL_RECHECK.json、stdout.log 和 stderr.log。
