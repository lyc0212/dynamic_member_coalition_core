# SW3-C 正式执行备用族分类契约补充 V1

生效基准为 c97ed0a08df066c386551a53b626e0f617a2f9e9。本补充在正式 TEST 世界、预测和标签生成之前固定，依据用户本轮明确授权澄清整族准入失败。原 V1 评价规范、物理准入补充及其历史证据保留。

## 候选拒绝及耗尽

已登记候选拒绝继续下一个 a，最多32次。固定物理准入白名单为 HEADING_OUT_OF_PHYSICAL_ENVELOPE、VELOCITY_DOMAIN、POSITION_DOMAIN_OR_ESCAPE。NONFINITE 和 DUPLICATE 不属于此白名单。

只有完整记录 a=0至31，且32条拒绝原因全部属于白名单，才形成 FIXED_PHYSICAL_ADMISSION_EXHAUSTED，允许三种白名单原因混合。任一 NONFINITE、DUPLICATE 或其他非白名单原因均禁止据此触发备用。未登记原因、缺失证据及未识别 Target/Environment 异常立即停止。不能把单次候选拒绝当成备用依据。

## 整族失败和备用

任一世界发生上述纯物理耗尽，当前族无法形成四世界，标记 FAMILY_FIXED_PHYSICAL_ADMISSION_FAILURE。标签生成前，仅该情况或已经明确登记的族特定公开 schema、运动适用域不合格可触发备用。公开类失败须先证明共同模板和环境合法，不得将全局配置、环境、数值完整性或未知异常归为可替换失败。

仅替换冻结顺序中首个合格失败的完整族。原族已接受世界及全部尝试保留为失败证据，不混入替代族。备用固定 n=7，TEST 使用 split=test 和 replaces=原族编号，从世界0开始形成完整四世界并采用同样准入、去重和构造守卫。最多使用一次。备用自身失败、后续第二个族失败或任何无法唯一归类的情况均停止，不增加尝试。

## 与冻结条款的关系

原评价规范的备用许可继续有效；耗尽必须留证并报告。正式 TEST 的纯物理耗尽按本补充判断是否构成获准整族失败。物理准入补充中停止当前 DEV 的历史规则及已完成 DEV 记录保持原样。此解释明确正式样本替换边界，会影响异常情况下最终采用的族，必须在抽样之前冻结。禁止根据预测、真实完成、难度或损失选样。

本补充不改变候选公式、SHA256编码、分组、科学算法或指标。出现未覆盖情形报告 BLOCKED_CONTRACT_AMBIGUITY。本轮未实施协调器、未运行测试或WLS，也未生成正式数据。

## 原文件指纹

- docs\A2_PRED_SW3_EVALUATION_SPEC_V1.md  SHA256 3cf14d9ed3c318f8cfc7bbc85837be147296e8757965e1633bdcbfedff8f443d
- docs\A2_PRED_SW3_C_PHYSICAL_ADMISSIBILITY_ADDENDUM_V1.md  SHA256 6978b139071b71d7e7065a4fcc9e54582c820e677b5ed4c7fa453a1b29d411a3
