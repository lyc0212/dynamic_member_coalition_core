# A2-VALUE-1 V1.0 同场景收益对照预登记

## 研究问题与判定

在冻结的确定性 A2-SWITCH 场景中，比较原 OPEN 策略与逐决策切口正进度联盟保护策略 LOCKED。主指标为 ΔJ = J_OPEN − J_LOCKED，使用两组到 tick120 的真实净收益。登记 H+、H0、H−，分别对应 ΔJ 大于、等于和小于零。判定使用已保存 binary64 总账的精确差，展示值可舍入。收益分项以 OPEN 减 LOCKED 计算，改派项采用负费用 `-change_cost`，总差与分项和的核对使用账本复算的舍入容差。

对照有效时分别记为 `VALID_POSITIVE`、`VALID_ZERO`、`VALID_NEGATIVE`。输入或源码变化、分叉前科学差异、锁定选择错误、模式不一致或物理结算无法核验时记为 `INVALID_COMPARISON`，停止收益归因。任务完成、占用、控制努力、进度清零和再分配用于解释差值。结论适用于该场景和此保护规则。

## 冻结内容

- 基础提交 `5fc7a2bc95ea30083e355d9b452879793acca7bf`，科学文件和既有证据逐文件摘要见准备记录。
- 世界 `configs/a2_switch_two_target_v1.json`，SHA256 `b23661dcb927f814dadc033df37d2aa142a63960ddf4cb60083041c56f3a37b6`。
- 公告 `configs/a2_switch_public_announcements_v1.json`，SHA256 `80853bbd59c1f06b1864819a98c9fae7090cbca99bbedfc9ab9198d07b5daed0`。
- OPEN 使用 `runs/a2_switch_episode_001` 及其科学复核，最终净收益 −0.7775828814863254。原结果直接复用。

## 唯一策略差异

每个合法决策切口，仅从公开视图读取活跃目标的服务段、Assignment 和最新实际结算时钟。若 `base + intervals × 0.05 > 0`，约束下一动作保留目标、全体成员及全部角色。分配、服务段和时钟团队必须一致。下一切口重新读取当下进度，曾归零但已重新积累正进度的团队仍受保护。自然完成和终止按原执行协议释放。

原候选评价与 OPEN 最优结果完整保存。LOCKED 只增加完整计划可行性约束。三架机器人和 q2 团队的结构意味着，有锁时保留该团队后只剩一架空闲机器人，保护后的完整计划唯一。无锁时直接沿用原求解器的精确值及平局规则，并由 Fraction 穷举和原规则的独立回放复核。tick60 的受约束 C0 保留原精确值，即使保护候选的预测净边际非正也适用。

## 比较与证据

逐模式比较 tick0、20、40 的公开输入、原评价、无约束选择和完整 STEP，以及 tick60 提交前的公开输入、原评价和原选择。此前实际观测和当前服务端点由已比较的 STEP 和公开历史绑定。STEP 身份变化只允许固定路径上的工作实例、环境、流、帧、包，以及按对应帧重算的摘要。名称只允许从 `A2_{mode}` 变为 `A2_VALUE1_LOCKED_{mode}`，保持相同后缀。

分叉后由各自的世界实例和感知实例产生观测及物理轨迹。R/S_NEW 分别独立演化，用于实现一致性复核，场景实例数为一。最终复核两组动作、服务时钟、物理和收益。可复用 OPEN 物理核算函数，向它提供已审计的 LOCKED 执行动作视图，原始产物完整保留。

## 正式运行与停止条件

以下命令仅在获得 VALUE-1E 单独授权后运行一次。先复核本协议、源码、输入和 OPEN 证据摘要，确认两个新目录不存在。采用 `Start-Process` 与 `WaitForExit(1800000)` 整轮外部护栏，重定向日志至 `reports/a2_value1_locked_001_guard`。超时终止进程树，遇异常、非零退出或审计失败保存证据并停止。

```powershell
& 'D:\anaconda3\python.exe' -B scripts/run_a2_value_locked.py `
  --world configs/a2_switch_two_target_v1.json `
  --announcements configs/a2_switch_public_announcements_v1.json `
  --output runs/a2_value1_locked_001
```

若切口始终合格，T0 从 tick60 的 0.60 秒到 2.25 秒至少还需要 1.65 秒，最早在 4.65 秒完成。这是时间预算推导，实际结局由完整 LOCKED 运行决定。
