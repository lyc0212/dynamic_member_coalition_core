# 动态传感器契约（设计，未实现）

sigma是bearing不确定性声明，改变WLS残差/Jacobian权重及JᵀJ半径代理，不改变首轮真实bearing扰动（恒零，无RNG）。单个sigma增大不保证FAIL，不是统计噪声鲁棒性研究。主因子只有U1 sigma，health仍available；U0/U2始终normal。B3 missing是单独UNKNOWN负例。

assess_quality先验证输入、接受估计、代表点、诊断和信息矩阵：测量不足、无接受估计、代表点不可评价、病态/歧义/边界等可为UNKNOWN；数值契约违规可抛错并必须停止。仅可评价时classify_radius严格r≤0.06 PASS/r>0.06 FAIL，p_ref=0.95，不加容差。不将missing改写为FAIL，也不将数值异常吞成UNKNOWN。
FAIL和UNKNOWN均禁止有效服务区间，有既存进度才产生原时钟reset事件；无进度仍记录invalid interval。Q FAIL仍可能有可接受位置估计，belief不能新增Q=PASS接受门槛。

## 实际、公开、决策三个时间

首版k_effective=80、k_public=80、k_decision=80，分别保存tick和秒(k×0.05)。一般未提前公告时effective≤public≤decision，decision为下一合法20tick切口。公开事件不触发额外中途belief冻结。
环境独立持有PrivateSensorSchedule（有序tick/声明/事件id/摘要），不放入A2_POLICY_INPUT、Config、seed、候选输入或可供策略读取的闭包。公开侧持有到期notice与当前profile快照，含observed_tick/版本，但不含未来行。
physical_profile_at(measurement_tick)供采样，public_profile_at(cut)供view；首版值一致而接口/身份分离。原D1A固定profiles不能直接宣称已支持。版本id放独立审计账本，通过slot/frame/endpoint关联；不修改冻结schema和摘要，不把sigma/version塞入raw key规避冲突。

## tick80唯一顺序

1. 区间开始保留belief60、旧Assignment和左79；登记effective80（只影响80及以后采样）。
2. 按旧团队及冻结belief移动79→80，遵守原速度；右80在到达位置上使用新sigma采样、融合，MODEL反馈入pending。
3. 原左79/右80结算(79,80]；G合法/Q FAIL则清零。完成/逃逸及自然释放按原优先级。
4. public80 notice在view冻结前合法发布；期间没有策略回调。消费本次冻结前已到达观测，冻结belief80并投影当前公开profiles，只冻结一次。
5. B0 KEEP，B1完整换员事务；新左80在freeze80之后生成，反馈留到100，不得倒灌冻结belief80。到100若同measurement tick重复，遵原非递增时间拒绝，不更改数学消费器。
6. (80,81]才按新团队相邻双端点结算；D100更新belief后KEEP当前团队，不做自主搜索。

若质量事件在非决策tick，采样/公开均按该tick，策略到下一合法cut才利用；不为方便改变20tick决策周期。

## 延迟公开不在首版

原_profiles同时供采样、checkpoint；packet.sigma、slot摘要、Q半径/诊断及belief都可能提前泄漏。只隐藏profile列表不够。未来public>effective须另定原包/质量/历史/缓存可见性及消息available_tick，不能改packet.sigma伪装旧声明。本轮不建延迟系统，也不宣称支持。
