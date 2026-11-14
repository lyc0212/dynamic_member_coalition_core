# A2-FACTORIAL 位置与速度 2×2 机制解释协议 V1.0

四格固定公开先验、T0、全部机器人、任务要求、决策周期、感知和物理规则、收益与保护策略。仅交叉 T1 的私有出生位置和速度。公开公告统一使用 `configs/a2_value2_public_announcements_v1.json`，与 VALUE-1 逐字节相同。

| 位置 | FAST (0.40, 0) | SLOW (0.02, 0) |
|---|---|---|
| A (9.20, 10.10) | VALUE-1，ΔJ ≈ −0.417527 | X1，待测 |
| B (9.03, 10.29) | X2，待测 | VALUE-2，ΔJ ≈ +0.171574 |

X1 世界摘要 `581ec60ca6168461f5d00e6a23f4ee39f5111e14753e7ce9977d484541760178`。X2 世界摘要 `17b2a888942f7ac8164c8d7832c3f8240e3676fe411dcc7cb8f59547b4f3cf21`。公告摘要 `80853bbd59c1f06b1864819a98c9fae7090cbca99bbedfc9ab9198d07b5daed0`。

## 指标和估计口径

主物理指标为 T1 最长连续合格区间数，逐个 0.05 秒区间检查左右实际 G/Q、完整团队与同一服务段。区间内或动作边界发生重置时断开计数。同一 tick 的前一物理端点和本轮动作端点分别按所属服务段使用，避免重复计数。未分配记 NOT_OBSERVED，已分配而未获得任何合格区间记 0。首个合格端点和实际最长段起点分别记录，若实际完成再记录促成完成的连续段及完成 tick。未完成的完成余量记 N/A。中断按同一团队服务段中不合格区间的连续长度记录，撤队与无分配另外列出。

逐目标记录服务进度、完成、重置、自然释放、首次 bearing、首次 WLS 接纳和首次消费。保留 tick60 的完整预测表和原无约束最优，记录是否自主改派、T0 是否受保护、tick80/100 的实际选择及最早可重新分配切口。

收益定义为 Y(p,v) = J_OPEN(p,v) − J_LOCKED(p,v)，从 tick120 的保存 binary64 账本求精确差。分解完成、Flow、Late、Effort、Terminal 和负的 Assignment 费用。固定速度下的位置对比为 Y(B,v) − Y(A,v)，固定位置下的速度对比为 Y(p,SLOW) − Y(p,FAST)。交互为 [Y(B,SLOW) − Y(A,SLOW)] − [Y(B,FAST) − Y(A,FAST)]。同步列出四格连续服务、完成状态和完成时间。位置对比包含误差大小与方向变化。两个历史对角案例用于提出机制解释设计；四格只支持这两档位置和速度下的有限对比。R/S_NEW 用于计算一致性复核。

## 正式运行计划，待独立授权

| 场景 | OPEN | LOCKED | 独立审计与护栏 |
|---|---|---|---|
| X1 | `runs/a2_factorial_x1_open_001` | `runs/a2_factorial_x1_locked_001` | `reports/a2_factorial_x1_episode_001_guard` |
| X2 | `runs/a2_factorial_x2_open_001` | `runs/a2_factorial_x2_locked_001` | `reports/a2_factorial_x2_episode_001_guard` |

启动前核对各场景、公告、源码和历史证据指纹及全部目标目录不存在。顺序为 X1 OPEN、独立 OPEN 关口、X1 LOCKED、独立比较，再按同一顺序执行 X2。每个调用是一个 R/S_NEW 配对，分别施加 1800 秒整轮外部超时。异常、超时、配对不一致或独立复核失败时保留已有输出并停止。超时终止进程树。正式结果为正、负、零或没有自主改派均保留，不调参或重跑。

OPEN 使用 `D:\anaconda3\python.exe -B scripts/run_a2.py --world <该格世界> --announcements configs/a2_value2_public_announcements_v1.json --output <该格OPEN目录>`。

LOCKED 入口适配方案已确定。VALUE-2 原入口的硬编码世界摘要拒绝两个交叉场景。正式阶段先在独立入口以显式 X1/X2 清单绑定世界摘要及唯一输入输出路径，复用其 `load_open`、`compare_before_action`、`compare_prefork_step` 及原编排顺序，调用原 `locked_decision`，保留原实例身份规则。原入口保持冻结。逐模式在首次实际不同动作提交前核对全科学切口；共同动作的 STEP 继续核对。若无分叉则比较至终点，发生分叉后独立演化。无保护仍用原精确最优，进度归零和完成释放沿用原规则。

独立审计复用 VALUE-2 的 `audit_plan` 和 SWITCH 的 `verify_physics`、`verify_observation_feedback`，使用该格目录和原始实际执行动作。VALUE-2 复核驱动器的固定路径须由新的编排层绑定。窗口汇总采用本协议的逐区间定义，完成窗口、分叉时刻及 ΔJ 符号均从保存数据求出。正式启动前需实现、测试并冻结该薄编排层。本轮没有调用正式入口或估计 X1/X2 的实验结果。
