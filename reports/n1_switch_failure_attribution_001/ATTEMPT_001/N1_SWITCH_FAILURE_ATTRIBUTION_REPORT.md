# N1_SWITCH_FAILURE_ATTRIBUTION_001 科研报告

执行状态：COMPLETED_WITH_LIMITATIONS。结果分类A：基本恢复。日期2026-11-16。实际HEAD为69fee291885f354978ba3ed7b873579b1ba87c34；开始时工作树干净。新建本任务目录，未提交/推送，无新commit。

## 审查与范围

方案通过：仅检查已关闭案例I原S，不修改原算法，不用真值重选候选。只启动1格MODEL，未执行ACTUAL未来、R、Assignment、R-CV、K/M matched或其他案例。

## 状态恢复

使用路径B，前缀仅启动一次。历史PUBLIC_D60、MAPPING_RECEIPT不足以构成完整consumer种子，历史终点快照没有被人工拼装成D60状态。

按冻结案例I配置D0空闲、D20/D40 U0/U1服务T0，至D60只freeze一次。公开状态digest与原PUBLIC_D60完全一致，包含位置、Assignment、belief、服务历史及当前端点；前缀经济账本逐字段相同。原映射返回REAL_CUT_TO_MODEL_SCHEMA_MAPPING_PASS，种子由白名单映射恢复并单独保存。T0服务进度0.15秒。完整依据见STATE_RECOVERY_RECEIPT.json。

物理目标按冻结EXPERIMENT_CONFIG.json传播到D60：T0 [9.2,10]、[0.4,0]；T1 [9,10]、[0.6,0]。仅进入MODEL外生世界，未修改公告、belief或consumer历史。原冻结S完整身份核对通过；未重新生成候选。MODEL未来观测由自身状态生成，不读取原ACTUAL未来观测。

复用原Branch和冻结BLVF，D80/D100仅freeze+Hold。任务局部严格零费用schema在with作用域生效，保留其他验证，退出后恢复断言通过。未修改生产文件或冻结核心。

## 价值归因

|评价来源|SWITCH净值|
|---|---:|
|原N1 W1|-0.71253999405727086|
|本次matched世界|-0.14254431500738046|
|原ACTUAL|-0.14254431500738049|

E_total=0.56999567904989035；E_world=0.56999567904989035；E_residual=-2.7755575615628914e-17。有符号恒等式核对通过。world_contribution_ratio=1，约100%。此比值是固定评价器下两世界的联合变化比例，不是位置或速度的独立因果份额。

|分项|MODEL|ACTUAL|ACTUAL−MODEL|
|---|---:|---:|---:|
|completion|0.1875|0.1875|0|
|flow|-0.029374999999999984|-0.029374999999999998|-1.388e-17|
|late|-0.050624999999999996|-0.050625000000000017|-2.082e-17|
|effort|-4.431500738047353e-05|-4.4315007380473523e-05|6.776e-21|
|terminal|-0.25|-0.25|0|
|change_cost|0|0|0|

误差均在浮点尺度，没有相反经济误差抵消造成的假一致。口径统一D60—D120全任务净值，未重复计入已结算前缀。

## 服务机制与决策意义

T0在D60撤回并丢失原0.15秒；本次MODEL继承原历史后按原assign处理，未人为保留。T1早期服务、D74中断（进度0.65秒）、D93恢复G/Q合格及D114完成均恢复。D74 Q为PASS而G为false，MODEL通用observation_invalid事件语义对应ACTUAL GEOMETRY_INVALID，不应按字符串误判机制差异。T0未完成。完成后自然释放，未将释放后的时钟当作最大进度零。

本次MODEL G/Q变更：[{"tick": 60, "G": true, "Q": "PASS"}, {"tick": 74, "G": false, "Q": "PASS"}, {"tick": 93, "G": true, "Q": "PASS"}]。

机器人轨迹最大坐标差=0；D80/D100合法反馈更新及关键时钟、重置证据见SERVICE_COMPARISON.json及I/MATCHED_S_RAW.json。累计21个合格区间完成T1，最大进度至少达到要求1.05秒，无服务不足。原ACTUAL服务汇总用于事后比较，未作为运行输入。

D_K=0.17997491605161237；D_M=0.1824742731454731。本次S超过原冻结K/M评分，也超过原ACTUAL K净值。仅替换S一格即可恢复此有限比较的排序；K/M未在新世界重评，不是完整同世界N1决策验证。

## 科研解释

本案例的关键完成与经济误差可以由外生世界失配解释；未发现具有实质决策意义的同世界残差。冻结BLVF及局部闭环评价路径获得特定案例条件支持，可以保留为研究工具。

这不证明原N1能够事前选择正确世界。真实T1位置和速度原本未知，事后提供真值不是可部署修复。位置、速度及内生反馈交互无法独立分离；不宣称位置单独解释100%。后续若继续，问题应转向信息条件和参考世界适用性，而非再调整选择规则。本轮不实施后续算法或新研究。

## 资源、保护与停止

运行进程CPU2.484375秒、墙钟2.6683158秒，任务save函数截至资源快照累计逻辑写入800650字节。该值不含准备脚本、规范保存、回执自身及后置报告；不是完整预算累计写入，更不是以最终目录大小替代。准备/后置CPU及完整累计逻辑写入UNKNOWN，RESOURCE_ACCOUNTING=INCOMPLETE，RESOURCE_COMPLIANCE=NOT_ESTABLISHED。监测部分未触限，不将未知记0。

前缀重建1次，MODEL启动1/有效1；前缀ACTUAL观测WLS41、底层solver369、MODEL解析55；MODEL观测非线性WLS0、R0、Assignment0、R-CV0、ACTUAL未来0、重试0。

INPUT_IDENTITY.json列出的全部原任务文件执行后哈希一致。历史结果、生产源码及配置均未修改；仅新增本任务目录。

IMPLEMENTATION_STATUS=COMPLETED；SCIENTIFIC_RESULT_STATUS=BASIC_RECOVERY；SERVICE_MECHANISM_RECOVERY=SUPPORTED_THIS_CELL；ECONOMIC_VALUE_RECOVERY=FLOATING_POINT_AGREEMENT；SINGLE_CELL_RANKING_RECOVERY=YES；REFERENCE_WORLD_CONTRIBUTION≈100%；MATCHED_WORLD_RESIDUAL≈−2.78e−17；INDEPENDENT_ACCEPTANCE=PENDING；PRODUCTION_ADMISSION=BLOCKED。

任务停止，不启动Attempt002、不恢复BLVF修复、不扩大N1验证、不开发混合算法或信息获取研究。
