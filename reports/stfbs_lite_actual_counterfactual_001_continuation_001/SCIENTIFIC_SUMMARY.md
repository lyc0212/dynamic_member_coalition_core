# ACTUAL_COUNTERFACTUAL_001_CONTINUATION_001 科研停止报告

FINAL_TASK_STATUS = LOCAL_DEV_ACTUAL_THREE_ACTION_COUNTERFACTUAL_INCOMPLETE

## A. 任务状态
原TASK保持STFBS_LITE_ACTUAL_COUNTERFACTUAL_001，续行ID为STFBS_LITE_ACTUAL_COUNTERFACTUAL_001_CONTINUATION_001。
G0=PASS；G1=SWITCH_DYNAMIC_EQUIVALENCE_FAILED；G2/G3=NOT_STARTED；G4=NOT_EXECUTED。
ORIGINAL_COUNTERFACTUAL_STATUS=INCOMPLETE，G4_CHANGE_COST_ANALYSIS=INCOMPLETE，V1_2_DELIVERABLE_COMPLETE=FALSE。
STARTED_ATTEMPTS=1，CONSUMED_ATTEMPTS=1。ACF001_SWITCH_001永久CONSUMED；KEEP及MEMBER_CHANGE未启动、未消费。任务消费机会为3，没有增加身份或额度。
原任务首次FAILED_BEFORE_RECOVERY归档及所有SHA256保持不变。

## B. 最小入口适配及G0
保留-I -S -B；实际sys.executable、sys.prefix、site-packages目录及numpy/scipy/psutil真实文件来源、版本均通过。版本2.1.3/1.15.3/7.2.2，见ENTRY_IMPORT_VERIFICATION.json。导入通过未被当作G0通过。
真实历史恢复及共同D60检查随后完成：POST_FREEZE_PRE_ASSIGNMENT；机器人、原分配、公开视图、历史、slots、consumer状态/接受记录/待消费记录一致，合法进度0.6000000000000001秒。
已恢复历史D60—D120账本、历史真实外生世界并建立正式执行冻结。实际HEAD41d37449260ccb107fd2d213e1ee7bea04d2efb5；科学冻结HEAD仍1ab69f3508b9e79f8945a5c2feb83e57368a2fbc。相对变化仅为原失败归档，科学源码及资源接口未变。

## C. SWITCH校准及停止
采用MODEL_SWITCH_REPLAY_REQUIRED，真实MODEL完整运行60步至D120，D80/D100真实R及Assignment各一次。该分支自身科学审计、资源对账及调用闭合通过，Budget/NestedJournal为FINALIZED_PASS，保留1个独立MODEL候选，不删除原始证据。
历史SWITCH净价值：-0.7325408343901842。
MODEL复现净价值：-0.7325408343901841。
MODEL减历史：1.1102230246251565e-16。

动态等价性比较中1165项通过，2个分组未通过，共6个字段差异：
- D80，U0/U1/U2 sensor_profiles.observed_tick：历史80，MODEL60。
- D100，U0/U1/U2 sensor_profiles.observed_tick：历史100，MODEL60。

其他已执行的物理/控制/动作/GQ/服务时钟及重置/观测估计/信念/消费时序/终端历史/经济比较项通过。不能将最大差异40误写为位置或收益误差；它是tick字段差。
静态来源：历史execution.py每次公开传感器声明加当前observed_tick；MODEL Branch保留D60 profiles并在policy_view复用。sigma和health没有成为本次不一致项。
本次不据此忽略字段、放宽容差或将失败改标为PASS。现有证据留供独立审核判断该声明时刻字段的科学语义；没有修复后重跑。
G1未通过，因此未将MODEL候选计入有效ACTUAL反事实矩阵：VALID_ACTUAL_CELLS=0。

## D. 未执行分析
KEEP、MEMBER_CHANGE均没有新结果。三动作原始排序、事后遗憾、无固定费用矩阵、四世界辅助矩阵、解析费用交点及建模讨论未执行，逐项见UNCOMPLETED_DELIVERABLES.json。
没有以预期值或其他世界结果填补；没有将历史ACTUAL费用与MODEL费用混用；未执行零费用闭环。不能形成历史名义SWITCH次优性或费用移除后排名的新结论。

## E. 科学分支资源
SWITCH内层Job CPU=69.828125秒，墙钟=74.182053秒。
外层CPU=70.484375秒，墙钟=74.524558秒；外层包含内层，不相加。
Policy WLS=742，Observation WLS=61，Solver=7227，R=2，Assignment=2，物理步=60。
三方资源计数一致，生命周期闭合，所有实际启动进程确认退出。无预算超限、无重试。
G4科学分析调用数为0；累计账本中G4记入的是失败后最终保护/报告/封存资源，不表示科学费用分析已经执行。

## F. 累计资源
历史保守扣减：G0 CPU2.0秒、G0及任务墙钟1.2秒、公共/总存储1,550,702 bytes。公共是总存储子集，不重复相加。
本次G0 CPU=1.859375秒、墙钟=1.974201秒。
SWITCH比较CPU=0.187500秒、墙钟=0.179054秒。
G0/G1累计CPU=4.046875秒、墙钟=3.353256秒。
最终封存CPU=0.453125秒、墙钟=0.500424秒。
累计任务墙钟约79.413535秒；累计公共存储2981583 bytes，累计总存储22606040 bytes。
完整历史扣减、本次、累计及剩余额度见CUMULATIVE_RESOURCE_LEDGER.json。所有实际监督判断均含历史偏移；公共统计排除三个正式分支目录。

## G. 保护、归档及权限
最终历史保护836项无差异。前次失败目录和归档原样保留；本次原始执行目录亦保留。
生产源码没有变化。既有未跟踪node_install.msi及运行期间出现的project-code.txt未触碰。
归档逐文件SHA256见ARCHIVE_VERIFICATION.json；原FINAL_REPORT及证据副本字节不变，本文件为归档内追加中文解读。
EXECUTION_CHANGE_COST=0.01。
ZERO_CHANGE_COST_CLOSED_LOOP_EXECUTED=FALSE。
PRODUCTION_SOURCE_MODIFIED=FALSE。
HISTORICAL_EXPERIMENT_RERUN=FALSE。
ADDITIONAL_SCIENTIFIC_ATTEMPTS=NOT_AUTHORIZED。
AUTOMATIC_RETRY=FALSE。
PRODUCTION_ADMISSION=BLOCKED。
