# ECON_001 静态经济目标研究报告

任务：STFBS_LITE_FB_ECONOMIC_OBJECTIVE_REVIEW_001；日期：2026-11-15；范围：STATIC_ONLY。

## 版本与证据

本地HEAD为866abfb7859892eb6fa42566b11e88da1cf64728，与指定参考相同。仅使用本地源码及保存汇总。开始时已有大量clean_project目录下受跟踪文件删除，以及未跟踪project_clean_code.txt；本任务未恢复、覆盖或处理这些既有变化。未发现AGENTS.md。目标报告创建前不存在。

主要输入：`reports/stfbs_lite_fb_blvf_initial_validation_001/SCIENTIFIC_ANALYSIS.json`（mechanisms/*/ON_service/positive_cost_ledger）；`reports/stfbs_lite_fb_blvf_h5_arc_extension_001/ATTEMPT_002/OFFLINE_FINALIZATION.json`（seven_cell_integrity/*/service/positive_cost_ledger）；`reports/stfbs_lite_actual_full_episode_counterfactual_001_continuation_001/ASSIGNMENT_CHANGE_COST_LEDGER.json`（cells/*/components、C_future、original_value）。H3及H5最终独立科学验收文件均为ACCEPTED_WITH_LIMITATIONS、ACCEPTED、CLOSED。H5仅采用ATTEMPT_002离线接收结果，保留其原PARTIAL_RESULTS及ATTEMPT_001失败身份。

ACTUAL依据同目录FINAL_SCIENTIFIC_RECEIPT.md：原控制器INCOMPLETE、FULL_DELIVERABLE_COMPLETE=FALSE；三个保存候选有效，不将本次研究解释为历史整体验收升级。

## 共享经济分项表

以下统一为完成正收益、其余列正费用；J=completion-flow-late-effort-terminal-change。全部采用D60—D120未来口径（3—6秒），不重复计入D0首次分配0.02前缀费用。H3/H5为条件MODEL，ACTUAL为原ACTUAL执行器；不同世界和执行器不合并评估鲁棒优势。

|单元|completion|flow|late|effort|terminal|change|收费次数|J_OLD|J_NOC|核对残差|
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|H3 ON KEEP|0.125|0.025625|0.039375|1.41073101529e-05|0.375|0|0|-0.31501410731|-0.31501410731|0（按表分项）|
|H3 ON SWITCH|0.1875|0.028125|0.046875|3.49157650903e-06|0.25|0.02|2|-0.157503491577|-0.137503491577|0（按表分项）|
|H3 ON MEMBER_CHANGE|0|0.03125|0.05625|0.000612045013922|0.625|0.02|2|-0.733112045014|-0.713112045014|0（按表分项）|
|H5_ON_KEEP|0.125|0.025625|0.039375|1.41041301461e-05|0.375|0|0|-0.31501410413|-0.31501410413|0（按表分项）|
|H5_ON_SWITCH|0.1875|0.028125|0.046875|3.49157650903e-06|0.25|0.02|2|-0.157503491577|-0.137503491577|0（按表分项）|
|H5_ON_MEMBER_CHANGE|0|0.03125|0.05625|0.00061256960463|0.625|0.02|2|-0.733112569605|-0.713112569605|0（按表分项）|
|H5_OFF_KEEP|0|0.03125|0.05625|9.40143207406e-06|0.625|0|0|-0.712509401432|-0.712509401432|0（按表分项）|
|ACTUAL SWITCH|0|0.03125|0.05625|4.08343901842e-05|0.625|0.02|2|-0.73254083439|-0.71254083439|0（按表分项）|
|ACTUAL KEEP|0.125|0.025625|0.039375|1.41073101529e-05|0.375|0|0|-0.31501410731|-0.31501410731|0（按表分项）|
|ACTUAL MEMBER_CHANGE|0|0.03125|0.05625|0.000612045013922|0.625|0.02|2|-0.733112045014|-0.713112045014|0（按表分项）|

## E1：完成价值（A：数学及源码事实）

config.py的weight_reference=4×task_count；本研究两任务为8，不能套用默认四任务配置。evaluator.py:125—133中完成奖励系数隐式为1，没有completion_weight字段；终端未完成系数2。固定任务集合及统一终端规则下，完成相关项等于3Σ(wc)/8−2Σw/8。T0权重1的合成完成增益0.375，T1权重1.5为0.5625。任务优先级既影响完成也影响时间成本。

## E2：时间价值

evaluator.components按出生后到完成、逃逸或评价终点的活动时间收费；late只在deadline后增加，deadline是软经济约束。分母为W_ref×stage_dt=24。T0截止前每秒0.0041667，截止后0.0166667；T1分别0.00625及0.025。终端未完成费用仍对逃逸任务生效。同样未完成时，较早逃逸节省后续时间费；是否符合应用取决于是否只计活动任务占用，不能据此证明控制器会主动诱发逃逸获益。

B：保存证据中KEEP的flow+late=0.065，其余ACTUAL候选为0.0875；完成相关项差0.375，时间差0.0225，控制差远小于二者。H3/H5 SWITCH完成T1，完成相关项比KEEP多0.1875，但时间费多0.01及固定费多0.02，仍领先约0.15751。完成主导且时间具有可见影响。

## E3：控制尺度

service.py:196—199对运动指令逐机器人限速3，累计Σ||u||²×elapsed；stfbs_d1a_model.py:180使用逐机器人积分。它是平方速度控制代理，不是焦耳能耗。α_E=0.02/900≈2.22222e-5。三机器人、3秒、范数不超过3条件下E≤81、费用≤0.0018，是条件理论上界。小于T0完成价值约208倍、小于T1约312倍，小于两机器人改派费约11倍。

保存费用约3.49e-6至6.13e-4，主要起轻微运动正则作用，无法表达显著能源约束。可代数反推E=费用×45000，标记DERIVED_FROM_SAVED_COST，不当作原始观测。reference从10改3而权重不变会放大100/9；同时改权重为0.0018则α不变。有限检查config定义及相关经济入口未发现reference=10的应用校准依据：UNRESOLVED，不据此擅自选新权重。

## E4：改派及重构

stfbs_d1a_model.py:125按逐机器人完整分配对象差异收费；a0_plans.py:47、79在候选评分中扣除此费。因此改配置可能改变候选及后续R行为，同轨迹重估不能替代闭环。首次idle到任务收费；ACTUAL ledger中D0两次收费属前缀，D60 SWITCH及MEMBER_CHANGE各两次，KEEP零次；自然完成、逃逸和终端释放不额外收费。

收费机器人次数、联盟重构次数、角色改变次数、服务重置次数及自然释放次数不可互换；一次成员替换可包含两次机器人变化。service.py:87—99按成员与角色团队标识变化清零，几何/质量无效也可重置；不能把每次重置归因于成员替换。ACTUAL KEEP继承0.6秒并D93完成；MEMBER_CHANGE重置0.6秒且新人需实际进入区域；SWITCH撤离T0，T1至终点仅0.7秒服务，不足1.05秒。多因素共同作用，不是重置单因素因果实验。

B：ACTUAL无费排序仍KEEP>SWITCH>MEMBER_CHANGE；SWITCH候选遗憾0.3975267270800314，原费用只解释其中0.02差异。H3/H5静态最优仍SWITCH。本次没有统一世界Minimax Regret计算。

C：固定协调/通信成本可独立于服务损失存在，因此不必然重复收费；但本次有限证据未建立0.01的独立应用依据。建议下一阶段研究采用ECON-NOC，保留服务重置及物理后果，独立报告成员变化及重置；不声称性能提高。

## E5：机会成本及能力边界

经济目标已奖励任意任务后续完成，无需另加资源释放奖或进度奖。Hold固定后续分配不能表达完成后的重新利用；原R周期决策虽有再分配能力，也受合法时刻和候选评分预测范围限制。ACTUAL保存时序D80继续T0、D93完成、D100空闲。D93至120有1.35秒；若只能D100分配、T1无进度且需连续1.05秒，即使零旅行也仅剩1秒，无法完成。D93立即重构只说明时间上可能，不证明几何、质量及旅行可行。三机器人不能同时组成两个互斥双成员团队。

局限归属：经济目标是完成及时间主导、控制很弱、固定费用未校准；任务设置是短剩余时域、服务持续时间及资源不足；动作空间限制同时组队组合；后续策略限制Hold及周期再分配；预测能力限制对未来观测、服务连续性与再分配后果的表达。H3/H5反馈结果与ACTUAL不同，不能仅调整经济权重来修复预测或策略范围。

## 参数建议与四项结论

|参数|当前值/含义|建议及未决依据|
|---|---|---|
|隐式完成系数|1，完成收益|保留，无独立Config字段|
|unfinished_weight|2，终端失败|保留，有效完成权重3；应用标定仍未决|
|flow_weight|0.1，活动时间|保留；逃逸后停费是否符合应用待确认|
|late_weight|0.3，超期附加|保留；deadline软约束|
|control_weight/reference|0.02/10，平方运动代理|暂保留；真实资源模型及参考尺度依据未决|
|change_cost|0.01，逐机器人改派|未来建议0，独立协调成本未建立|
|服务重置|团队变化/无效服务清零|保留，体现连续服务约束|

四项结论：①原目标最大化归一化完成净值并扣除活动、超期、微弱控制及固定改派费用。②尺度明显偏重完成，时间次之、控制很小；是否适用依应用任务价值与资源含义决定。③主要科学局限同时来自任务时域/资源、可选动作、后续策略及预测范围，不能归咎单一经济参数。④推荐未来ECON-NOC作为有条件建模选择，其他经济值暂沿用；尚无闭环性能优势证据。

## R1—R6落实与限制

R1 SATISFIED：隐式系数与等价条件已说明。R2 SATISFIED：逃逸停费及终端惩罚已区分。R3 SATISFIED：速度代理和条件上界已说明。R4 SATISFIED：五类事件不混计。R5 SATISFIED：D100不可完成结论显式依赖条件。R6 SATISFIED_WITH_LIMITATIONS：使用10单元可靠汇总，不恢复RAW/TRACE；完整逐事件次数、原始积分及部分后续策略逐单元字段NOT_AVAILABLE于本次提取表，不作为零。表中分项加总完成，但未将所有事件恢复设为验收门槛。历史参数应用设计依据未解决，限制配置校准结论。

## 最终状态与停止

E1_E5_STATIC_RESEARCH = COMPLETED_WITH_LIMITATIONS

ECONOMIC_CONFIGURATION_RECOMMENDATION = REPORTED

RECOMMENDED_CONFIGURATION = ECON-NOC

FIXED_CHANGE_COST_INDEPENDENT_JUSTIFICATION = NOT_ESTABLISHED

ZERO_CHANGE_COST_CLOSED_LOOP_EXECUTED = FALSE

NEW_PHYSICAL_SIMULATION = 0；NEW_HF_EXECUTION = 0；NEW_BLVF_EXECUTION = 0；NEW_ACTUAL_EXECUTION = 0；NEW_WLS_CALLS = 0；NEW_SOLVER_CALLS = 0；NEW_R_CALLS = 0；NEW_ASSIGNMENT_OPTIMIZATION_CALLS = 0；NEW_PROJECT_TESTS = 0。

PROJECT_SOURCE_MODIFIED = FALSE；ECONOMIC_CONFIGURATION_MODIFIED = FALSE；BLVF_V0.1_MODIFIED = FALSE；HISTORICAL_RESULTS_MODIFIED = FALSE。

MINIMAX_REGRET_EFFECTIVENESS = NOT_ESTABLISHED；NEXT_STAGE_EXECUTION_AUTHORIZATION = NOT_GRANTED；PRODUCTION_ADMISSION = BLOCKED。

仅以标准库读取JSON和代数计算生成本报告，未导入项目入口。本任务唯一新增为本报告；保留既有删除及未跟踪文件。未提交、推送或执行后续研究。完成后停止，等待科学分析及下一步决定。
