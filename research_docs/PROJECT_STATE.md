# PROJECT_STATE — dynamic_member_coalition_core

更新：2026-11-13 | 状态版本：1
性质：当前科研状态快照，不是执行授权或新方案。
长期规则：`PROJECT_RULES.md` V1.0（同目录）。
详细交接依据：`STFBS_Lite_主研员交接档案_20261113_FULL_ACTUAL.md`，尤其 §4–12；用户本轮文档驱动指令。
仓库：https://github.com/lyc0212/dynamic_member_coalition_core

## 1. 当前阶段

- 冻结主线 A0-R → A1 → A2 → B → C → A3；A0-R/A1/A2 有限机制验收已完成。当前先验证 STFBS-Lite 所解决的真实决策问题，不优化代理或重规划主线。
- L1 名义预测失准：历史案例已证明；L2 名义动作真实次优：待本轮反事实验证；L3 事前风险识别、L4 稳定决策改善：未证明。
- 主研员负责研究推进，独立审核员负责独立审查，Codex 本机执行，用户保留所有最终授权。生产准入 BLOCKED。

## 2. 已完成及永久关闭事项

- EXTENSION_005：独立科学验收通过，H1/H2/H3 三动作 9/9 有效。三个世界均 SWITCH C6 最优，Minimax Regret 选择 C6，最大遗憾 0，与 H1 名义选择一致；未证明额外收益。不重跑。
- 历史 ACTUAL：D60 从 T0 切到 T1，清零 0.60s 合法服务进度；预测 T1 于 D97 完成，实际 D120 两目标均未完成。D60–D120 净值 -0.7325408343901842；尚不能据此认定 C6 次优。
- 原 `STFBS_LITE_ACTUAL_COUNTERFACTUAL_001` V1.2：G0 入口失败，0 个正式科学 attempt 消费，0 ACTUAL 有效格。
- `CONTINUATION_001`：G0 PASS，G1 动态等价性 FAIL（6 项 sensor_profiles.observed_tick 差异），`ACF001_SWITCH_001` 永久消费，旧 KEEP/C5 未启动，0 ACTUAL 有效格。停止历史恢复及 ACTUAL→MODEL 校准路线，不修复旧时间戳差异、不重试、不复用旧分支作为新格。
- Journal 增量快路径已验收，不重开全面 M3、取消的工程专项或独立性能测试。

## 3. 唯一优先任务（尚未收到执行回执）

`STFBS_LITE_ACTUAL_FULL_EPISODE_COUNTERFACTUAL_001 V1.0`

| 项目 | 状态 |
|---|---|
| 独立方案审核 | PASS，BLOCKER=0 |
| 用户明确任务级授权 | GRANTED：三场完整 ACTUAL、最小任务本地驱动及资源/日志适配、冻结预算及 G4 |
| 最终 Codex 指令 | 已形成并下发；不重写、不重复授权 |
| 新正式 attempt 实际消费 | 未确认；不推断 0 或 3 |
| 新 ACTUAL 有效格 | 尚无回执可确认 |
| 远端 HEAD（接任时已核对） | `a17627c83444a4c0e2b05903b2272eac5d579191` |
| 新归档 | 接任时远端尚无；不能据此判断本机是否已启动 |

冻结顺序：G0 → FULL_SWITCH → FULL_KEEP → FULL_MEMBER_CHANGE → G4。
三场独立 D0–D120，原 StaggeredEnvironment 执行器，D60 分别强制 C6/C0/C5，其他时刻使用原 A2-R；D60 名义决策单独保留，后续决策用各自观测与信念。三场共同前缀必须可比；历史复现与新矩阵内部有效性分开。

| 分支 | D60动作 | 正式 attempt ID | 消费状态 |
|---|---|---|---|
| FULL_SWITCH | SWITCH C6 | AFC001_SWITCH_001 | 未确认 |
| FULL_KEEP | KEEP C0 | AFC001_KEEP_001 | 未确认 |
| FULL_MEMBER_CHANGE | MEMBER_CHANGE C5 | AFC001_MEMBER_CHANGE_001 | 未确认 |

实际 change_cost=0.01。G4 对实际收费次数、固定轨迹无费用价值、双口径排序/遗憾、解析 lambda 敏感性及四世界描述性对照做分析；禁止零费用闭环、统一四世界鲁棒矩阵、重跑 005 或追加第四场。

冻结环境/预算索引：交接档案 §8–10，实际执行以已审核 V1.0 及最终指令为准。每场上限 Policy WLS 2574、Observation WLS 126、Solver starts 24300、R/Assignment 各6、STEP 6、物理步120、Worker CPU 1800s、Worker 墙钟2400s、外层墙钟2460s、存储256MiB；G0/G4 各180 CPU秒/240墙钟秒，共享存储256MiB；任务总墙钟7860s、总存储1GiB、正式 attempt 3。具体主动停止阈值、计量、审计及失败停止条件不得由本摘要替代。

不授权生产源码修改、额外测试/正式计算、自动重试、预算扩大、Git commit/push 或覆盖本机的 pull/checkout/reset。

## 4. 关键证据索引

以下为仓库根目录相对路径，已存在者可按冻结 HEAD 查阅：

- `reports/stfbs_lite_h2_h3_extension_005/NINE_CELL_VALUE_MATRIX.json`、`MINIMAX_REGRET_RESULT.json`、`CANDIDATE_FREEZE.json`
- `runs/a2_switch_episode_001/`；`reports/a2_switch_episode_001_guard/REPORT.md`
- `reports/stfbs_lite_actual_counterfactual_001/`；`reports/stfbs_lite_actual_counterfactual_001_continuation_001/FINAL_REPORT.json`、`SWITCH_REPLAY_EQUIVALENCE.json`
- 新任务预期归档（实际存在性待回执）：`reports/stfbs_lite_actual_full_episode_counterfactual_001/`，优先 FINAL_REPORT.json、SCIENTIFIC_SUMMARY.md、COMMON_D60_PREFIX_EQUIVALENCE.json、HISTORICAL_CASE_REPRODUCTION.json、ACTUAL_THREE_ACTION_VALUE_MATRIX.json、ASSIGNMENT_CHANGE_COST_LEDGER.json、ACTUAL_NO_CHANGE_COST_VALUE_MATRIX.json、FIXED_TRAJECTORY_CHANGE_COST_SENSITIVITY.json 与资源/归档审计。实际文件名以 manifest 为准。

正式 V1.0 方案、独立审核意见、用户授权原文及最终执行指令的独立文件本机路径：本轮未取得/未核实。已有授权及已下发指令保持不变，不以本状态快照替代；不为补齐文档重新启动当前任务。后续新交接时记录实际可读取路径。

## 5. 下一步

等待用户转发 Codex 实际回执，不重复启动任务。收到后依次判断：

1. 新矩阵及共同前缀是否有效、历史是否复现，消费/资源/证据是否闭合。
2. 原始和无费用口径下名义动作是否次优、遗憾与固定费用直接贡献。
3. 物理服务机制和后续策略如何解释结果；据此提出最小下一步科学研究建议。单例不得外推一般算法优势。

若失败：定位首个实质原因及已消费身份，保存合法证据；按 BLOCKER/LIMITATION/OPTIONAL 分级，必要新授权由用户给出，不自动重试。收到实质结果、独立验收或授权变化后更新本文件。
