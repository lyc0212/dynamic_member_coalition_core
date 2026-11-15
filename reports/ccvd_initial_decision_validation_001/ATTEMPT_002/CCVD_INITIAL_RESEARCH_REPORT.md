# CCVD Attempt 002 研究报告

状态：COMPLETED_WITH_LIMITATIONS。局部ECON-NOC兼容性修复成功；A适用范围受限；B完成9格事前MODEL、4个ACTUAL候选及2格事后对应检查。无重试。

## 来源与实施

实际HEAD：ab180fb5ae81ef159d691d629fb8c559a4f5c542。启动前工作树干净。原Attempt 001全部文件哈希与保护清单一致。原核心源码、生产配置及冻结BLVF未修改。本次新增仅ATTEMPT_002目录。

局部深拷贝public.SCHEMA，仅将/$defs/Config/properties/change_cost/const从0.01改为0.0；研究身份CCVD_ATTEMPT_002_ECON_NOC_RESEARCH_ONLY。原验证函数、事务、计费机制继续使用，退出with作用域恢复原schema引用，最终恢复断言通过。SCHEMA_ADAPTATION.json记录身份及差异。接口检查允许0，拒绝0.01、-0.01、0.1，仍拒绝robots=99。未修改SCHEMA_SOURCE_SHA256或伪称生产认证。

Checkpoint、Assignment及映射运行在同一进程适配作用域。B实际首次分配2次变化、更换后累计4次变化，费用均0；自然释放不额外计费。生产配置保持原值。

## A：自然原R状态

A/PREFIX_RECEIPT.json显示D0选择U0/U1服务T0，D20选择全空闲，D40仍全空闲；D60 T0/T1均活动，但当前Assignment全空闲。原历史“保持当前双成员联盟并考虑切换”的问题不再以原状态出现。全空闲本身是合法Assignment，但不满足本版K/S/M分类所依赖的当前双成员联盟，因此NO_LEGAL_KEEP应准确理解为NO_CURRENT_Q2_COALITION，而非空闲动作违法。

未强行恢复历史团队，也未为A构建新的算法。A无MODEL/ACTUAL矩阵与matched检查。不能据此认定原R已正确，或者取消费用已经改善原任务收益；本次未执行A全空闲之后的候选未来。

## B：有限候选价值

|动作|W0|W1|W2|保守增量|ACTUAL|完成|
|---|---:|---:|---:|---:|---:|---|
|K|-0.712535252388|-0.712535252388|-0.712535252388|0.000000000000|-0.712535252388|无|
|S|-0.130003727054|-0.712535886665|-0.712628419410|-0.000093167022|-0.712546803638|无|
|M|-0.325017706390|-0.325017706390|-0.325017706390|0.387517545999|-0.325017706390|T0 D105|
|R_EXTRA|未评价|未评价|未评价|未评价|-0.712540256610|无|

K：U0/U1服务T0；S：U0/U1服务T1；M：U1/U2服务T0（U1正角色、U2负角色）；原R：U1/U2服务T1。候选事前冻结，完整身份见B/CANDIDATES.json。R共同K/S/M名义最优为S。

R选择R_EXTRA；N0选择S；N1、CCVD选择M；简单KEEP选择K。有限四候选实际最优M。R、N0、K均未完成任务；M在5.25秒完成T0。

收益差：{"G_eval": -6.547028004177946e-06, "G_eval_common": 0.0, "G_motion": 0.38752909724823087, "G_conservative": 0.0, "G_total": 0.3875225502202267, "G_M": 0.3875175459986045}。恒等分解核对通过。这些是方法实际收益差，不是独立因果效应。共同候选集评价增益为0。

四候选遗憾：{"K": 0.3875175459986045, "S": 0.38752909724823087, "M": 0.0, "R_EXTRA": 0.3875225502202267}。共同K/S/M及四候选并集中最优均M；不能推广为13动作或全局最优。

## 成员重构机制及评价器

B前缀为预声明受控前缀，不是原R自然失败。D60更换前T0进度为0，MEMBER_CHANGE事件记录0进度丢失。KEEP终点只有1.7秒连续服务，不足2.25秒；替代U2后D105完成2.25秒服务。M的实际优势0.3875175459986045由合成完成价值0.375、时间成本节省0.0125及努力节省约0.000017545999组成，不能解释为仅微小控制费用优势。

W0的S预测完成T1，但两个运动情景均预测未完成；N1因此选择M。M在W1/W2都优于KEEP，CCVD也主动选择M。不是机械保持当前联盟；但CCVD相对N1增益为0，本轮没有保守准则额外收益证据。

B matched K净值误差1.1102230246251565e-16，M误差0，相对误差约-1.11e-16。K均未完成，M均D105完成T0，关键排序一致；各分项保存于MATCHED_WORLD_CHECK.json。只能支持这两个候选、这个实际世界。没有B SWITCH matched检查，不能将其事前误差唯一归因于位置情景。

MODEL继承相同公开D60位置、分配、服务历史及consumer白名单；原始控制belief不写入情景真值，未来反馈独立生成，D80/D100仅freeze+Hold，无后续R。事后真实外生CV定义仅在A/B事前及ACTUAL已冻结后进入MODEL。D60历史不重算。共同前缀公开digest与经济账本在各ACTUAL重建后核对通过。

## 科研结论与后续建议

局部闭环预测在B的KEEP及成员更换上获得对应条件支持。运动情景选择与主动成员替换得到一个有意义的开发机制案例，值得继续原项目，但不能据此称已解决原A历史决策错误。

当前应优先保留较简单的N1作为下一步研究对象；CCVD本轮没有额外收益，不应立即恢复更复杂框架。A显示零费用会改变前缀资源保持行为；该问题需作为后续单独决策对象，本轮不新增实验或恢复固定费用。两个状态均非独立泛化验证。

## 资源、限制与停止

Attempt 002运行进程CPU 61.875秒、墙钟62.8294281秒。任务writer在资源回执快照前累计49,926,106字节；该数不含脚本准备、回执自身和后置报告，不能冒充完整任务累计写入。准备及后置工具调用未统一计量，完整资源会计INCOMPLETE、RESOURCE_COMPLIANCE=NOT_ESTABLISHED。未将未知值记0；Attempt 001已知进程CPU0.40625秒/墙钟3.3911407秒另列，两个Attempt联合完整合规不成立。

Attempt 002独立前缀2次（累计含Attempt001为3次），事前MODEL9格、事后2格，共11格有效；ACTUAL4次均有效。解析591、实际观测WLS554、策略评分WLS2497、非线性Solver27459、R5、Assignment5。MODEL观测非线性WLS0。R5来自A前缀3次及A/B D60各1次；B受控前缀及Hold无R。实际完整轨迹已保存。

限制：阶段调用细分没有独立流水日志；进程资源记录未覆盖全部准备和后置开销。实现中无额外科学重试或预算复用。

IMPLEMENTATION_STATUS=COMPLETED_WITH_LIMITATIONS；PUBLIC_INFORMATION_ISOLATION=ENFORCED_BY_DETACHED_INPUTS；HOLD_SEMANTICS=FIXED_WITH_FEEDBACK；ECON_NOC_CONFIGURATION=LOCAL_STRICT_SCHEMA；ACTUAL_DECISION_ADVANTAGE=B_SUPPORTED_ONLY；MEMBER_RECONFIGURATION_EVIDENCE=B_SERVICE_COMPLETION_SUPPORTED；GENERALIZATION_EVIDENCE=NOT_ESTABLISHED；PAPER_NOVELTY=NOT_ESTABLISHED；INDEPENDENT_ACCEPTANCE=PENDING；PRODUCTION_ADMISSION=BLOCKED。

本轮已结束，不自动修复、追加状态、增加情景或启动下一阶段。
