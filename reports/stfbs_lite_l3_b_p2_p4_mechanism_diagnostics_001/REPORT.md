# P2—P4 联合机制诊断结果

VALID_COMPLETE_24_CELL_DIAGNOSTIC_MATRIX

| 世界 | 动作 | HF | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|---|
| H2 | KEEP | -0.3150141073101529 | -0.7125094014320741 | -0.3150141073101529 | -0.3150141073101529 | -0.3150141073101529 |
| H2 | SWITCH | -0.1687802228561035 | -0.7325026216050797 | -0.7325026216050797 | -0.16878022285610356 | -0.16878022285610356 |
| H2 | MEMBER_CHANGE | -0.7331120450139224 | -0.7330898517001428 | -0.7331120450139224 | -0.7331120450139224 | -0.7331120450139224 |
| H3 | KEEP | -0.3150141073101529 | -0.7125094014320741 | -0.3150141073101529 | -0.3150141073101529 | -0.3150141073101529 |
| H3 | SWITCH | -0.157503491576509 | -0.7325026216050797 | -0.7325026216050797 | -0.157503491576509 | -0.157503491576509 |
| H3 | MEMBER_CHANGE | -0.7331120450139224 | -0.7330898517001428 | -0.7331120450139224 | -0.7331120450139224 | -0.7331120450139224 |

| 版本 | MAE（有效分母） | H2最优动作 | H3最优动作 | H2 HF regret | H3 HF regret |
|---|---|---|---|---|---|
| P1 | 0.32229275060815804 (n=6) | ['KEEP'] | ['KEEP'] | {'KEEP': 0.1462338844540494} | {'KEEP': 0.1575106157336439} |
| P2 | 0.1897869214629245 (n=6) | ['KEEP'] | ['KEEP'] | {'KEEP': 0.1462338844540494} | {'KEEP': 0.1575106157336439} |
| P3 | 9.25185853854297e-18 (n=6) | ['SWITCH'] | ['SWITCH'] | {'SWITCH': 0.0} | {'SWITCH': 0.0} |
| P4 | 9.25185853854297e-18 (n=6) | ['SWITCH'] | ['SWITCH'] | {'SWITCH': 0.0} | {'SWITCH': 0.0} |

| 世界 | 动作 | 传播效应A0 | 反馈效应B0 | 交互效应 |
|---|---|---|---|---|
| H2 | KEEP | 0.3974952941219212 | 0.3974952941219212 | -0.3974952941219212 |
| H2 | SWITCH | 0.0 | 0.5637223987489761 | 0.0 |
| H2 | MEMBER_CHANGE | -2.2193313779506063e-05 | -2.2193313779506063e-05 | 2.2193313779506063e-05 |
| H3 | KEEP | 0.3974952941219212 | 0.3974952941219212 | -0.3974952941219212 |
| H3 | SWITCH | 0.0 | 0.5749991300285707 | 0.0 |
| H3 | MEMBER_CHANGE | -2.2193313779506063e-05 | -2.2193313779506063e-05 | 2.2193313779506063e-05 |

## 配对误差与决策质量

- P2/P1：共同有效单元 ['H2_KEEP', 'H2_MEMBER_CHANGE', 'H2_SWITCH', 'H3_KEEP', 'H3_MEMBER_CHANGE', 'H3_SWITCH']；n=6；基准MAE=0.32229275060815804；处理MAE=0.1897869214629245；配对Delta_MAE=-0.13250582914523357。
- P3/P1：共同有效单元 ['H2_KEEP', 'H2_MEMBER_CHANGE', 'H2_SWITCH', 'H3_KEEP', 'H3_MEMBER_CHANGE', 'H3_SWITCH']；n=6；基准MAE=0.32229275060815804；处理MAE=9.25185853854297e-18；配对Delta_MAE=-0.32229275060815804。
- P4/P3：共同有效单元 ['H2_KEEP', 'H2_MEMBER_CHANGE', 'H2_SWITCH', 'H3_KEEP', 'H3_MEMBER_CHANGE', 'H3_SWITCH']；n=6；基准MAE=9.25185853854297e-18；处理MAE=9.25185853854297e-18；配对Delta_MAE=0.0。
- P4/P2：共同有效单元 ['H2_KEEP', 'H2_MEMBER_CHANGE', 'H2_SWITCH', 'H3_KEEP', 'H3_MEMBER_CHANGE', 'H3_SWITCH']；n=6；基准MAE=0.1897869214629245；处理MAE=9.25185853854297e-18；配对Delta_MAE=-0.1897869214629245。

## 机制证据及解释边界

- H2_KEEP：P1: completion_tick=None, Pmax=1.9500000000000002, NG=27, stop_time=6.0；P2: completion_tick=93, Pmax=2.25, NG=33, stop_time=4.65；P3: completion_tick=93, Pmax=2.25, NG=33, stop_time=4.65；P4: completion_tick=93, Pmax=2.25, NG=33, stop_time=4.65。
- H2_SWITCH：P1: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0；P2: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0；P3: completion_tick=119, Pmax=1.05, NG=21, stop_time=5.95；P4: completion_tick=119, Pmax=1.05, NG=21, stop_time=5.95。
- H2_MEMBER_CHANGE：P1: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0；P2: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0；P3: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0；P4: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0。
- H3_KEEP：P1: completion_tick=None, Pmax=1.9500000000000002, NG=27, stop_time=6.0；P2: completion_tick=93, Pmax=2.25, NG=33, stop_time=4.65；P3: completion_tick=93, Pmax=2.25, NG=33, stop_time=4.65；P4: completion_tick=93, Pmax=2.25, NG=33, stop_time=4.65。
- H3_SWITCH：P1: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0；P2: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0；P3: completion_tick=110, Pmax=1.05, NG=21, stop_time=5.5；P4: completion_tick=110, Pmax=1.05, NG=21, stop_time=5.5。
- H3_MEMBER_CHANGE：P1: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0；P2: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0；P3: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0；P4: completion_tick=None, Pmax=0.0, NG=0, stop_time=6.0。

所有NoCap prediction_changed仅用于机制A。反馈预测变化由同一freeze时刻、同一目标、相同传播规则下的前后belief计算；控制及服务归因来自实际配对轨迹，以批次描述，不向单个事件分摊因果效果。无合格五tick历史参考时保留更新前速度及来源，不强制回退D60先验。

P2负对照直接检查PUBLIC_PRIOR传播不变，整体单元是否完全相同另行如实记录；不能仅以整体差异判实现失败。

代理价值升高、相对HF误差减小、动作选择正确是三个不同结果。应联合阅读MAE、KEEP−SWITCH、完整排序与HF regret；不只选择有利指标。

P3/P4固定历史观测流不随代理运动重新生成或筛选，结果不证明其在自身轨迹上能够获得同样的信息，不可直接部署为生产自主感知预测算法。

RAW保存原始输出；TRACE保存控制、G、代理Q、服务时钟和reset、D80/D100前后快照以及D120状态；FEEDBACK保存种子/事件身份、消费回执、pending与反馈批次；ANALYSIS保存规定比较对的逐拍误差和分层机制。代理stop_time不等于HF真实释放事务，未创造新的Assignment或收费。

## 正式门槛与资源

V0.5最终状态：L3_B_BLOCKED。实际科学诊断有效性单列为VALID_COMPLETE_24_CELL_DIAGNOSTIC_MATRIX。资源会计仍为INCOMPLETE，资源合规NOT_ESTABLISHED；完整依赖闭包与退出后的最终封存不伪装VERIFIED。正式门槛文件见V05_FINAL_STATUS.json。

历史Stage A墙钟334.8579769秒超时和历史CPU/累计写入未知保持原状。当前窗口为新批准的120 CPU秒、1800连续墙钟秒、134217728逻辑写入字节；最终资源数据见RESOURCE_RECEIPT.json。

只使用现有18个以内新增诊断单元，没有重跑P1/REF、WLS、Assignment、R或HF，没有修改生产源码。完成后停止，不启动L3-C。