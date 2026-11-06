# A2-VALUE-1P 实施准备报告

**READY，等待 VALUE-1E 单独授权。** 本轮完成协议预登记、LOCKED 策略和入口实现、OPEN 只读复核及测试。未执行新的物理 episode。LOCKED 真实收益与 ΔJ 仍未知。

## 冻结和修改范围

本地 HEAD 为 `b78f6a82444b0b4b6b84fc7ab803c7e99d4951f7`。与 OPEN 运行时的 `5fc7a2bc95ea30083e355d9b452879793acca7bf` 相比，提交间差异只含 A2-SWITCH 两份配置、协议及测试。OPEN 保存的科学源码和输入摘要逐文件匹配本地。原预测、WLS、G/Q、执行器、收益和精确求解器没有修改，原 OPEN 文件及其复核报告在本轮只读复核前后摘要一致。

| 新文件 | 职责 |
|---|---|
| `docs/A2_VALUE1_PROTOCOL_V1.md` | 预登记锁定规则、可比性、ΔJ、判定和正式执行护栏 |
| `research/non_oracle/a2_value_lock.py` | 按已结算正进度识别保护团队，求出唯一锁定计划，独立穷举核对 |
| `scripts/run_a2_value_locked.py` | 用原环境、原感知和原候选评价执行 LOCKED，保存无约束与约束两套证据 |
| `tests/test_a2_value_lock.py` | 锁定、时钟、精确最优、平局、配对与拒绝测试 |
| 本报告目录的 `recheck_open.py` | 用既有物理核算函数只读复核 OPEN，计算冻结切口对照排名和摘要 |

协议 SHA256 为 `0e1c401a755d8d194f87c86d5283802070501c8d4497866b13f3a10e447e7d94`。世界为 `b23661dcb927f814dadc033df37d2aa142a63960ddf4cb60083041c56f3a37b6`，公告为 `80853bbd59c1f06b1864819a98c9fae7090cbca99bbedfc9ab9198d07b5daed0`。新文件、旧输入、科学源码及 OPEN 逐文件摘要见 `PREFLIGHT.json`。

## OPEN 及冻结 tick60 核验

OPEN 两模式均六轮、每轮 COMMITTED，tick120 正常结算，原生 PAIR_CHECK 为 PASS。准备阶段重新核验了完整候选计划、已保存物理证据、观测消费和账本，并重新逐轮比较两模式。OPEN 净收益仍为 **−0.7775828814863254**。

| 项目 | OPEN 无约束 | 将 LOCKED 规则应用于已保存的同一输入 |
|---|---:|---:|
| 候选与原合法完整计划 | 12 / 13 | 12 / 13 |
| 可行完整计划 | 13 | 1 |
| 选择 | C6，SWITCH T1 | C0，KEEP T0 |
| 精确目标值 | `-41523928784916923/288230376151711744` | `-354669055230257/1125899906842624` |
| 此切口分配变化费用 | 0.02 | 0 |

两模式的冻结输入均识别到 T0 的 U0/U1 原角色、实际进度 0.60 秒。十三个计划的原值、动作、变化次数、精确费用和排除原因均在 `PREFLIGHT.json /tick60/{mode}/constrained/original_legal_plans`。这是从既有 OPEN 输入重建的约束排序。

受保护的 q2 团队占用三架机器人中的两架，剩余一架无法组成第二支 q2 团队。因此锁定可行集合为单元素，包含原 KEEP，即使该计划预测价值非正也保留。无锁时采用原求解器，再用独立 Fraction 枚举与规范平局回放核验。人工同值测试覆盖同 mask 的首选候选与跨 mask 最小值优先，替换为同值非规范候选会被拒绝。

## 分叉比较和测试

入口在 tick0、20、40 比较保存的公开输入、候选、无约束决策、观测消费及已提交 STEP，在 tick60 提交前比较同类决策证据及消费序列。不同运行只接受固定 STEP 路径上的名称替换和可重算帧摘要。若不一致，已有记录保留且停止。分叉后每个 LOCKED 模式独立创建环境和感知实例。配对逐轮比较实际 STEP、冻结输入、两套选择证据和最终账本。

- 针对性测试命令为 `D:\anaconda3\python.exe -B -m unittest discover -s tests -p test_a2_value_lock.py -v`。10 项通过，见 `targeted.log`。测试使用本地冻结 OPEN 证据。
- 全量回归命令为 `D:\anaconda3\python.exe -B -m unittest discover -s tests -v`。136 项通过，见 `regression_final.log`。
- OPEN 复核命令为 `D:\anaconda3\python.exe -B -c "import runpy; runpy.run_path('reports/a2_value1_preflight_001/recheck_open.py',run_name='__main__')"`。见 `open_recheck.log`。

正式 LOCKED 输出目录和护栏目录尚不存在。进入 VALUE-1E 前再次核对指纹，并按协议一次执行。分叉前可比性和分叉后真实演化尚待正式记录验证。本轮无提交或推送。
