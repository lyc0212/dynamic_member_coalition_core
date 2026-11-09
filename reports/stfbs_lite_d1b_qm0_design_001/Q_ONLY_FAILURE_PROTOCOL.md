# 有限Q-only FAIL协议（未来执行，本轮零WLS）

## 独立新MODEL场景而非修改D1A

拟议单T0、q2、三机器人；birth tick60，prior p0=(9,10)、CV=(0.40,0)，weight=1，service_duration=1.05，软deadline=5秒，episode H=120(6秒)。Config robots=3/task_count=1，其他G/Q、控制和成本公式不变，kappa=0.01。
U0/U1初始位置为p0加原dual_neg45/dual_pos45偏移；U2为p0+正角色偏移+(0.70,0)的预登记待命位置。位置仅是新场景设计，不生成物理数据；不预言修复成功，不在换员时传送U2。
新fixture必须合法构造PUBLIC_PRIOR种子、MODEL出生/未分配历史、外部上下文；D60真实MODEL首次分配/融合后，旧团队进度从0开始。不能篡改旧ACTUAL D60坐标、任务或来源标签来冒充合法checkpoint。合法fixture builder是首轮实现依赖。
原H1 T0时长2.25秒，D80重置到D120仅2秒，且原U2在(2,2)。不得机械沿用它并假定可完成；D1B独立任务/场景差异必须明确登记，不回改原验收。

## 同几何探针与有限参数

未来先用normal profiles形成一个合法MODEL参考前缀60→80，保留每端点和服务；观察截断80不收episode终止罚。它只做场景准入，不当成B0结果，不把高保真反馈共享给B0/B1。
冻结同一tick80目标条件位置、U0/U1位置、角色、几何、测量方向/零扰动、其他传感器、算法及阈值。若目标已终止、G不合法或OLD原WLS/Q不是PASS，SCENARIO_ADMISSION_FAILED并停止，不移动几何/改时刻寻找成功。
OLD独立QM_PROBE_OLD；DEGRADED独立QM_PROBE_DEGRADED_i。U1 sigma按[2,4,8,16]×0.02，即[0.04,0.08,0.16,0.32]严格升序；最多1个OLD加4个DEGRADED。每项独立生成packet/cache并真实WLS/assess_quality，只改sigma；不能复制旧packet后改字段，不能同branch/key覆盖上下文。
选择第一个两侧G PASS、OLD Q PASS、DEGRADED Q FAIL的因子；不读B0/B1净收益或恢复结果。PASS为退化不足；UNKNOWN单列并按原固定列表继续；契约/未知异常立即BLOCKED，不能宽泛except后跳过。耗尽记NO_Q_ONLY_FAIL_FOUND，不加候选、不调阈值/容差。

## 与动态执行区别

探针是同几何下两种外生条件，不是同一物理历史重复测量。实际场景不同tick用不同sigma，原始key也不同；sigma80必须在tick80第一次采样前确定。
选定因子后固定版本、身份、schedule与时序，再分别独立运行B0/B1。两者到80的几何应逐字段与探针一致（60→79声明相同，控制到80仍用冻结belief60）；原端点Q必须由真实计算确认。若动态80未实现G PASS/Q FAIL，记DYNAMIC_Q_ONLY_NOT_REALIZED，不重调参数、时刻或初态，不发布修复成功比较。
当前没有sigma候选计算、质量半径或Q-only FAIL实验结果。即使未来找不到明确FAIL，也允许完整记录为场景构造未成功，不等于方法被证明有效或无效。
