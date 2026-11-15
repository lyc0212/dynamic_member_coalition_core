# S1_SERVICE_IDENTIFIABILITY_WITNESS_001 研究报告

日期2026-11-16。EXECUTION_STATUS=COMPLETED_WITH_LIMITATIONS。唯一世界B ACTUAL执行完成，无重试。实际HEAD=d8d3f32e00c65aafd1817073b1c3254c22717ed6；开始工作树干净。未创建新commit、未推送。

## 输入及公开信息核对

世界B深拷贝原案例I，仅更改T1出生位置[9.0,10]→[9.45,10]、速度[0.6,0]→[0.4,0]；其余物理及全部public相同，反向替换后完整配置相等断言通过。T0保留原实际定义。T1零角速度CV，出生至终点从x9.45到10.65，不逃逸；位置误差0、速度0.4、航向0均在冻结研究支持内。世界A位置误差0.45、速度0.6、航向0亦合法。

D0空闲、D20/D40受控T0共同前缀真实执行，D60只freeze一次；完整公开view与原文件及DECISION_FREEZE的digest严格一致：4ca524be946aafaeece4058597433de613cdb29452d18efa63f45d1c2b8441fe。未删除、改写公开字段。机器人位置、团队、服务历史、0.15秒进度及belief因此一致。T1三个slot均UNQUERIED且packet空，接受位置历史为空，仍PRIOR_ONLY。前缀metrics逐字段相同。COMMON_PREFIX_RECEIPT.json保存依据。

同一环境继续提交原冻结S（U0负角色/U1正角色服务T1），D80/D100只freeze+当前有效分配Hold。没有重新启动前缀、没有候选生成或优化、没有MODEL映射。使用原九起点WLS，未使用BLVF。

任务局部严格ECON-NOC schema作用域与既有实现相同，仅换费用常量，其他校验保留，退出后恢复原schema引用断言通过。生产默认和核心源码未修改。

## 价值结果

|量|数值|来源|
|---|---:|---|
|J_A(S)|-0.14254431500738049|历史ACTUAL|
|J_A(K)=J_B(K)|-0.32251923105899283|A为ACTUAL；B为STRUCTURAL_INVARIANCE|
|J_A(M)|-0.32501858815285362|历史ACTUAL|
|J_B(S)|-0.71253999405727086|本次唯一ACTUAL|
|D_A|0.17997491605161234|A的S−K|
|D_B|-0.39002076299827804|B的S−结构性K|

B未来经济分项：{"completion": 0.0, "flow": -0.03125000000000001, "late": -0.05625000000000001, "effort": -3.999405727084995e-05, "terminal": -0.625}，change_cost=0。净值为终端累计收益减D60前缀收益，各分项同样相减，加总核对通过。未重复计入历史前缀。

## 服务结果

A原S在D74中断、D93恢复、D114完成T1，最大进度1.05秒；B中T0/T1均未完成，T1最大连续进度0.75秒，不足1.05秒。G/Q变更为[{"tick": 60, "phase": "decision", "G": false, "Q": "FAIL"}, {"tick": 91, "phase": "physical", "G": false, "Q": "PASS"}, {"tick": 105, "phase": "physical", "G": true, "Q": "PASS"}]。D99状态、D60/D80/D100 belief、事件及原始完整轨迹见SERVICE_ANALYSIS.json和ACTUAL_S_RAW.json。未从终端释放后时钟消失误推最大进度零。T0撤回时丢失原0.15秒。

原W1预测S未完成，净值与本次ACTUAL B相同，MODEL_RESIDUAL_B=0（保存binary64）。该结果不新增MODEL，也不证明其他世界预测准确；T0合法差分见证与真值的浮点差异没有为此修改。

## KEEP不变性及证明范围

execution.py按活动任务循环，只对存在当前服务segment的团队计算控制和观测；NonOracleEnvironment._control_command按该任务frozen belief计算。Sensing按stream处理，各raw key独立且角扰动恒零；K只服务T0直至完成和自然释放。T1不参与T0控制、观测或未来分配，Hold不再分配释放资源。T1在A/B都不逃逸，其未服务flow/late及终端贡献只由相同任务元数据决定，因此K全部任务经济价值不变。未执行B的K或M，未称K为B唯一最优。

在冻结共同K/S/M内，A唯一最优S；B中K比S高0.39002076299827804（显著超过1e-8），故B最优集合不含S。两个最优集合交集为空，无需确定B中K/M谁最好。

因此同一D60公开信息下，确定性共同候选首动作无法在A/B同时达到各自最优Hold收益。服务完成不可辨识性独立成立：相同S在A完成、B未完成。

确定性最坏情况候选遗憾保守下界为min(A中选K损失、A中选M损失、B中选S至少相对K损失)=0.17997491605161234。该下界不是Minimax优化结果，不适用于完整目录、随机策略或任意多阶段自适应策略。未来观测可区分世界，不代表未来一直不可辨识。

## 资源、保护和停止

运行进程CPU3.09375秒、墙钟3.4277116秒。受控save函数截至资源回执快照累计逻辑写入9,533,586字节，非最终目录大小；未涵盖实施准备、规范保存、回执自身及后置分析。全流程CPU及累计逻辑写入INCOMPLETE，RESOURCE_COMPLIANCE=NOT_ESTABLISHED；未知不计0，监测部分未触限。

完整ACTUAL启动1/有效1，前缀1、未来1（同一次完整执行）；前缀WLS41、未来WLS61、solver918；MODEL/BLVF解析/R/R-CV/Assignment均0。没有额外K/M、世界、扫描或重试。

INPUT_IDENTITY.json覆盖原N1全部文件，执行后哈希核对一致。SOURCE_IDENTITIES.json记录核心来源。工作树仅新增本任务目录，原历史、源码及配置未修改。

IMPLEMENTATION_STATUS=COMPLETED；SCIENTIFIC_RESULT_STATUS=VALID_WITNESS；WORLD_LEGALITY=SUPPORTED；PUBLIC_INFORMATION_EQUIVALENCE=EXACT；KEEP_STRUCTURAL_INVARIANCE=SUPPORTED；WORLD_B_SWITCH_COMPLETION=NO；SERVICE_NON_IDENTIFIABILITY=ESTABLISHED_FOR_THIS_WITNESS；DECISION_NON_IDENTIFIABILITY=ESTABLISHED_FOR_THIS_WITNESS；REGRET_LOWER_BOUND=0.17997491605161234；INDEPENDENT_ACCEPTANCE=PENDING；PRODUCTION_ADMISSION=BLOCKED。

唯一执行结束，停止。不自动启动Attempt002、其他反例、信息获取或后续算法研究。
