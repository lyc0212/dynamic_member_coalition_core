# N1_INDEPENDENT_DECISION_VALIDATION_001 科研报告

执行日期：2026-11-16。EXECUTION_STATUS=COMPLETED_WITH_LIMITATIONS。12个BLVF MODEL、6次R-CV评分、8个ACTUAL候选全部完成，无重试，无额外科学检查。

## 身份、范围及实施

HEAD=d32a6c73c7447ea9708614ea9265e9e0840658ab，分支main，开始时工作树干净。未提交、推送或改变分支，故无新的Git提交身份；实际运行入口为本目录n1_entry.py，配置与案例II参数在首个前缀前保存。FINAL_SPECIFICATION.md保存完整授权规范。

核心文件身份见SOURCE_IDENTITIES.json。原schema、生产默认配置及冻结BLVF未修改；进程with作用域只替换change_cost常量为0，其余验证保留，正常退出恢复断言通过。R-CV只临时替换policy.trajectory，按belief.target_id读取W1，恢复断言通过；未修改belief身份或写入真实速度。未运行旧入口。

两案例均D0空闲、D20/D40受控分配U0/U1给T0。前缀及Hold未调用R；两个D60各调用一次R和一次Assignment。MODEL在D80/D100仅消费反馈及Hold。每个ACTUAL从D0重建并核对D60公开digest（包括分配和服务历史）及前缀经济账本。

R-CV复用policy.evaluate，每个代表仅一次，全任务值为被服务任务absolute_O加其他未服务任务原公式基准。参考轨迹到D120远离逃逸边界，未服务基准的传播期限不改变结算。R-CV不模拟动作内生反馈；它是确定性等效比较，并非严格单因素消融。

事前见证只检查合法接受位置、公开出生支持、速度及公开测量packet/G端点，不用隐藏目标位置补齐。WITNESS.json标明必要检查及未证明项，不宣称通用历史逆解。未来物理情景与原控制belief分离。公开已有端点继续继承，无未来观测回放。

## 逐案例结果

### 案例I

D60 T0进度q=0.15秒。当前团队U0负角色/U1正角色；M为U1正角色/U2负角色；S为U0/U1切换T1；R_EXTRA为U1/U2切换T1。完整belief及身份见PUBLIC_D60.json、CANDIDATES.json。T0见证：{"position": [9.2, 10.0], "velocity": [0.3999999999999986, 0.0], "bearing_checks": 82, "conditions": "public birth support, speed, all sampled bearings and G endpoints; inherited service history remains unchanged", "not_established": "unqueried observations; general historical inverse solution"}

|动作|原R全任务评分|R-CV|N0/W0|N1/W1|ACTUAL|
|---|---:|---:|---:|---:|---:|
|K|-0.322510736129|-0.322519231059|-0.322519231059|-0.322519231059|-0.322519231059|
|S|-0.124690654369|-0.124716065143|-0.124690654369|-0.712539994057|-0.142544315007|
|M|-0.325009400045|-0.325018588153|-0.325018588153|-0.325018588153|-0.325018588153|
|R_EXTRA|-0.124689925301|NOT_EVALUATED|NOT_EVALUATED|NOT_EVALUATED|-0.142542656670|

|动作|T0完成时刻|T1完成时刻|D60改派进度损失|
|---|---:|---:|---:|
|K|5.1000000000000005|None|0|
|S|None|5.7|0.15|
|M|5.25|None|0.15|
|R_EXTRA|None|5.7|0.15|

方法选择：{"R": "R_EXTRA", "R_common": "S", "N0": "S", "N1": "K", "RCV": "S", "K": "K"}。各方法实际值按上表所选动作直接复用。

收益指标：{"G_total": -0.17997657438930825, "G_common": -0.17997491605161234, "G_motion": -0.17997491605161234, "G_closed": -0.17997491605161234, "G_active": 0.0, "G_eval_common": 0.0, "G_RCV": 0.0, "G_M": -0.002499357093860788}。这些是方法收益差，不是独立因果效应。

共同K/S/M最优=S，并集最优=R_EXTRA。共同集合遗憾：{"K": 0.17997491605161234, "S": 0.0, "M": 0.18247427314547313}；并集遗憾：{"K": 0.17997657438930825, "S": 1.6583376959145024e-06, "M": 0.18247593148316904, "R_EXTRA": 0.0}。原R仅登记并集遗憾，不将其视为共同集合内部非负遗憾。

实际G/Q状态变更tick、重置/释放事件、D80/D100反馈belief及经济分项见本案例SERVICE_ANALYSIS.json；原始完整轨迹保留。

### 案例II

D60 T0进度q=0秒。当前团队U0负角色/U1正角色；M为U1正角色/U2负角色；S为U0/U1切换T1；R_EXTRA为U1/U2切换T1。完整belief及身份见PUBLIC_D60.json、CANDIDATES.json。T0见证：{"position": [9.2, 10.0], "velocity": [0.3999999999999986, 0.0], "bearing_checks": 82, "conditions": "public birth support, speed, all sampled bearings and G endpoints; inherited service history remains unchanged", "not_established": "unqueried observations; general historical inverse solution"}

|动作|原R全任务评分|R-CV|N0/W0|N1/W1|ACTUAL|
|---|---:|---:|---:|---:|---:|
|K|-0.712515195991|-0.712531790524|-0.712531790524|-0.712531790524|-0.712531790524|
|S|-0.148769004797|-0.148818873909|-0.148769004797|-0.712564188384|-0.712666537346|
|M|-0.325009400045|-0.325018588153|-0.325018588153|-0.325018588153|-0.325018588153|
|R_EXTRA|-0.142512282538|NOT_EVALUATED|NOT_EVALUATED|NOT_EVALUATED|-0.712653679834|

|动作|T0完成时刻|T1完成时刻|D60改派进度损失|
|---|---:|---:|---:|
|K|None|None|0|
|S|None|None|0|
|M|5.25|None|0|
|R_EXTRA|None|None|0|

方法选择：{"R": "R_EXTRA", "R_common": "S", "N0": "S", "N1": "M", "RCV": "S", "K": "K"}。各方法实际值按上表所选动作直接复用。

收益指标：{"G_total": 0.38763509168106725, "G_common": 0.3876479491934206, "G_motion": 0.3876479491934206, "G_closed": 0.3876479491934206, "G_active": 0.38751320237156284, "G_eval_common": 0.0, "G_RCV": 0.0, "G_M": 0.38751320237156284}。这些是方法收益差，不是独立因果效应。

共同K/S/M最优=M，并集最优=M。共同集合遗憾：{"K": 0.38751320237156284, "S": 0.3876479491934206, "M": 0.0}；并集遗憾：{"K": 0.38751320237156284, "S": 0.3876479491934206, "M": 0.0, "R_EXTRA": 0.38763509168106725}。原R仅登记并集遗憾，不将其视为共同集合内部非负遗憾。

实际G/Q状态变更tick、重置/释放事件、D80/D100反馈belief及经济分项见本案例SERVICE_ANALYSIS.json；原始完整轨迹保留。

## H1、H2、H3与科研判断

H1：参考速度均为0.4东向，真实I为0.6东向，II为0.8且初始航向0.25，真实位置也与公告不同。N1在I错误拒绝了有价值SWITCH，选择KEEP，较R-CV损失约0.179974916；II选择M，较R-CV提高约0.387647949。不是一致改善，不支持参考失配下普遍可靠。

H2：I中R-CV选择S并完成T1，N1对W1的S预测未完成，实际却在D114完成；II中R-CV的S预测完成但实际未完成，N1选择M并D105完成T0。闭环额外价值是条件性的，两方法各有优势，不能宣布R-CV足够或N1全面优越。禁止用两例简单平均掩盖反向决策偏差。

H3：I形成0.15秒正进度，KEEP D102完成T0，M重置进度后D105完成，KEEP比M约好0.002499357。若KEEP全程合格且其他条件满足，q/60−0.0018=0.0007充分界与结果一致；它仅作解释，未作决策阈值。更重要的是SWITCH虽放弃已有T0进度，却完成更高权重T1，实际优于KEEP约0.179974916，N1未识别。II零进度下M恢复服务完成，而KEEP未完成。已有正进度处理及主动成员选择的具体证据，但完整合理三动作选择未建立。

本轮不做matched-world检查，无法唯一判定I的反向偏差来自位置/速度参考不足、剩余评价器误差或二者组合：ATTRIBUTION_UNRESOLVED。既有II正面结果不抵消I反例，不应继续以更复杂选择规则覆盖错误。建议保留两种方法及保存证据，收缩“单一参考世界可普遍可靠决策”的主张；是否追加针对机制研究由主研员及负责人决定，不自动修复、调参或追加计算。

## 资源与历史保护

运行进程CPU52.75秒、墙钟53.2697146秒；save函数截至原资源回执快照累计逻辑写入74,351,667字节。该累计值不是最终目录大小，但不覆盖准备脚本/规范保存、回执自身和后置分析报告；完整准备及后置CPU/累计写入UNKNOWN。RESOURCE_ACCOUNTING=INCOMPLETE，RESOURCE_COMPLIANCE=NOT_ESTABLISHED，未将未知消耗记0。监测部分远低于额度，不能冒充全流程合规。

独立前缀2、ACTUAL内部前缀重建8、MODEL12/12有效、R-CV6/6有效、ACTUAL8/8有效；原R2、Assignment2、解析610、MODEL观测非线性WLS0、ACTUAL观测WLS836、原R评分WLS1352、R-CV评分WLS294、底层solver22338。没有未来R、额外HF、W2、matched-world、扫描、第三案例或历史重跑。

IMPLEMENTATION_STATUS=COMPLETED；SCIENTIFIC_RESULT_STATUS=MIXED；REFERENCE_MOTION_APPLICABILITY=CASE_DEPENDENT；CLOSED_LOOP_ADDITIONAL_VALUE=MIXED；ACTIVE_MEMBER_RECONFIGURATION=SUPPORTED_IN_II；POSITIVE_PROGRESS_TRADEOFF=OBSERVED_IN_I_BUT_N1_SWITCH_FAILURE；INDEPENDENT_ACCEPTANCE=PENDING；GENERALIZATION=NOT_ESTABLISHED；PAPER_NOVELTY=NOT_ESTABLISHED；PRODUCTION_ADMISSION=BLOCKED。

执行结束，停止。
