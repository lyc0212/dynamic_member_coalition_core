# ACTUAL全时域三动作反事实科研报告

三个独立D0—D120 ACTUAL场次，D60是唯一初始干预，后续继续真实A2-R。共同前缀及历史复现分别裁定。

| 动作 | 全程净值 | D60前缀 | 未来净值 | 未来变化次数 | 费用 | 无费用同轨迹值 |
|---|---:|---:|---:|---:|---:|---:|
| KEEP | -0.36005615440629396 | -0.04504204709614111 | -0.31501410731015284 | 0 | 0.0 | -0.31501410731015284 |
| SWITCH | -0.7775828814863254 | -0.04504204709614111 | -0.7325408343901842 | 2 | 0.02 | -0.7125408343901842 |
| MEMBER_CHANGE | -0.7781540921100635 | -0.04504204709614111 | -0.7331120450139224 | 2 | 0.02 | -0.7131120450139223 |

实际名义动作：SWITCH；原始排序：['KEEP', 'SWITCH', 'MEMBER_CHANGE']；无费用排序：['KEEP', 'SWITCH', 'MEMBER_CHANGE']。
原始遗憾：{'KEEP': {'numerator': 0, 'denominator': 1, 'display': 0.0}, 'SWITCH': {'numerator': 7521492849979409, 'denominator': 18014398509481984, 'display': 0.4175267270800314}, 'MEMBER_CHANGE': {'numerator': 7531782865788277, 'denominator': 18014398509481984, 'display': 0.4180979377037695}}；无费用遗憾：{'KEEP': {'numerator': 0, 'denominator': 1, 'display': 0.0}, 'SWITCH': {'numerator': 7161204879789769, 'denominator': 18014398509481984, 'display': 0.3975267270800314}, 'MEMBER_CHANGE': {'numerator': 7171494895598637, 'denominator': 18014398509481984, 'display': 0.3980979377037695}}。
费用移除最优集合改变：False；严格反转：[]。

## SWITCH
D60原进度：{'0': 0.6000000000000001, '1': 0.0}；干预后进度：{'0': 0.0, '1': 0.0}。
状态：['unfinished', 'unfinished']；完成时间：[None, None]；最大进度：{'0': 0.6000000000000001, '1': 0.7000000000000001}。
未来分量：{'completion': 0.0, 'effort': -4.0834390184182906e-05, 'flow': -0.03125000000000001, 'late': -0.05625000000000001, 'terminal': -0.625}；费用：0.02。
D80/D100实际分配：[{'tick': 80, 'actions': [{'role': 'dual_neg45', 'target': 1}, {'role': 'dual_pos45', 'target': 1}, {'role': 'none', 'target': None}]}, {'tick': 100, 'actions': [{'role': 'dual_neg45', 'target': 1}, {'role': 'dual_pos45', 'target': 1}, {'role': 'none', 'target': None}]}]。
完整服务事件、合格G/Q区间、观测和信念见分支物理审计及SCIENTIFIC_MECHANISM_DETAILS.json。

## KEEP
D60原进度：{'0': 0.6000000000000001, '1': 0.0}；干预后进度：{'0': 0.6000000000000001, '1': 0.0}。
状态：['completed', 'unfinished']；完成时间：[4.65, None]；最大进度：{'0': 2.25, '1': 0.0}。
未来分量：{'completion': 0.125, 'effort': -1.410731015286985e-05, 'flow': -0.02562500000000003, 'late': -0.03937499999999996, 'terminal': -0.375}；费用：0.0。
D80/D100实际分配：[{'tick': 80, 'actions': [{'role': 'dual_neg45', 'target': 0}, {'role': 'dual_pos45', 'target': 0}, {'role': 'none', 'target': None}]}, {'tick': 100, 'actions': [{'role': 'none', 'target': None}, {'role': 'none', 'target': None}, {'role': 'none', 'target': None}]}]。
完整服务事件、合格G/Q区间、观测和信念见分支物理审计及SCIENTIFIC_MECHANISM_DETAILS.json。

## MEMBER_CHANGE
D60原进度：{'0': 0.6000000000000001, '1': 0.0}；干预后进度：{'0': 0.0, '1': 0.0}。
状态：['unfinished', 'unfinished']；完成时间：[None, None]；最大进度：{'0': 0.6000000000000001, '1': 0.0}。
未来分量：{'completion': 0.0, 'effort': -0.0006120450139223276, 'flow': -0.03125000000000001, 'late': -0.05625000000000001, 'terminal': -0.625}；费用：0.02。
D80/D100实际分配：[{'tick': 80, 'actions': [{'role': 'none', 'target': None}, {'role': 'dual_pos45', 'target': 0}, {'role': 'dual_neg45', 'target': 0}]}, {'tick': 100, 'actions': [{'role': 'none', 'target': None}, {'role': 'dual_pos45', 'target': 0}, {'role': 'dual_neg45', 'target': 0}]}]。
完整服务事件、合格G/Q区间、观测和信念见分支物理审计及SCIENTIFIC_MECHANISM_DETAILS.json。

## 费用敏感性及四世界描述性对照
lambda=0、0.01端点、两两交点及第三动作上包络核验见对应JSON；不重新求解策略。H1/H2/H3与新ACTUAL的执行器及世界同时变化，不把排序变化全部归因于不确定性，不重算005 Minimax。

## 建模与科学限制
实际执行change_cost=0.01；无费用值仅为FIXED_TRAJECTORY_REVALUATION，ZERO_CHANGE_COST_CLOSED_LOOP_EXECUTED=FALSE。
移除固定费用仍保留服务进度损失、几何恢复、运动努力、完成时间和终端损失；KEEP与成员变化的差异涉及多因素，不能作单因素因果证明。
固定费用可能代表未建模通信、协调、组织和模式切换成本或重构正则化，均为待验证解释。不能认定重复计费，也不能宣称0.01具已验证独立经济意义。
历史D80/D100维持T1可避免撤队0.02的候选证据见HISTORICAL_DECISION_INERTIA.json，新运行的实际选择单独记录；不能推导零费用闭环策略。
后续可研究不含固定费用任务收益并独立报告变化次数，但本任务不改变收益函数，不安排后续实验。
H1/H2/H3为MODEL，新ACTUAL为原仿真执行器，仅描述性对照，不是统一鲁棒决策矩阵，也不代表一般算法优势或生产准入。

## 资源及证据
三个新身份各一次，旧ACF路线未恢复，生产源码未改。分支资源三方对账、调用闭合、6个STEP及120物理步、Job退出见回执。G0/G4及工作目录和归档实际新增存储均计量；最终结果见FINAL_REPORT、AGGREGATE_RESOURCE_LEDGER及ARCHIVE_VERIFICATION。
