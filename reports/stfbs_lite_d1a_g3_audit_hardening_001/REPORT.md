# D1-A G3 独立审计与负例有效性有限补强

## 结论

**G3_AUDIT_HARDENING_READY_FOR_REVIEW**。A—D四组有限验收条件成立；D1-A仍为**D1_A_BLOCKED**。没有主H1复验、物理推进或WLS。这个结论是待独立审查，不是G3完整通过或算法收益证明。

起始与结束HEAD均为66d83e030bbdcae79ef1e92b0afc5d94c49d7ae5，起始工作树干净。只修改历史审计器及原repair测试，新增轻量来源登记模块和hardening测试。没有修改Branch.advance、finish、prepare_terminal、原主脚本、冻结科学内核或旧报告。SOURCE_PINS和REPAIR.diff记录实际变更。

## A：可信D60来源

R_D60.json真实字节SHA256为0241dd3c5075c35348b00dc3170fed0c288d7d8f7471321e37f64dc5801f8c46，与既有BELIEF_REPLAY_SEED.source_files登记相等。不是把本轮新摘要当成历史正确值。其他前缀R_D0/20/40、R.json和PUBLIC_INPUT分别与既有seed或BASELINE.tracked_fingerprints核对，六项全部相等。

D60_SOURCE_VERIFICATION保存每个文件的实际路径、大小、当前文件ID、当前和预存SHA及锚点文件。文件ID为本次读取观察，不冒称历史文件ID已独立锚定。来源锚点是原归档固定字节SHA及仓库中已有登记。

恢复视图与原R_D60.policy_input规范摘要相等，与原seed.public_D60_digest相等。规范公开摘要为a37cde42a2c4c147f4abc9289e5de693790218d17bcafcbe7fe3cfb49a9d6602；它不同于原文件SHA。两个任务历史还通过原纯seal_history重算核验。Assignment摘要、每任务保存历史摘要和对象摘要另行记录，未将不同身份混为一个摘要。

verified_registration顺序固定为：先核对预存来源pins，后recover和历史摘要，再登记KEEP/SWITCH外部上下文，最后测试才构造Branch。两个上下文有相同D60/seed/前缀，不同expected_branch_id。不会从修改后的Branch重新登记正式信任根。

初次登记实现因Windows反斜杠与Git来源pin正斜杠键格式不同而找不到R.json预存值；修复仅将查找键改为Path.as_posix，没有修改源文件或预期SHA。SOURCE_LOOKUP_FIRST_FAILURE保存该普通工程缺陷。未将其解释为真实来源已损坏。

## 独立入口与运行时自检

新增audit_branch_independent(branch,*,context)，省略参数为TypeError，context=None明确拒绝，不回退branch._audit_context。原audit_branch缺省形式保留为运行时自检，已有事务检查不受影响。独立验收使用调用方事先登记的外部上下文；其可信性仍由调用方及来源登记保证，不声称抵抗恶意可信调用者主动另造信任根。

## B：非空身份负例

KEEP夹具先提交原D60 KEEP，未改冻结首次动作。随后在人工预置D80合法切口，通过实际Branch.assign进行角色变化，使用融合替身，不调用advance。实际新增MODEL事件2条、新段1个、新/更新MODEL端点2个，三类集合均非空，保存目标、时刻、来源和分支。合法状态先经外部KEEP审计PASS，见NONEMPTY_MODEL_IDENTITY_FIXTURE。

ID-EVENT保持Branch.name和外部KEEP不变，仅改新事件分支，实际报Untrusted new event identity；ID-SEGMENT实际报Untrusted new segment identity；ID-ENDPOINT实际报Untrusted endpoint identity。这三项不是凭顶层Branch.name不匹配凑数，也没有先因缺少context或文件错误拒绝。

完整同步篡改另行修改Branch.name、内部_context、新事件、新段、新端点，重算段ID、引用与内部摘要；原外部KEEP仍拒绝。另一个负例保持Branch.name=KEEP，只替换内部上下文并自洽篡改前缀；外部原登记仍以D60 event prefix modified拒绝。

## C：消除旧负例假阳性

实际复现显示，合法历史和篡改历史在省略context时均先报External trusted audit context required，原assertRaises(ValueError)确实不能证明目标语义检查执行。两项作为配置fail-closed证据单列，不计入历史语义负例。

原test_artificial_history_tampering已改为：先核对D60来源、在Branch构造前登记外部上下文、合法基线先PASS、每个单项篡改沿用同一上下文并匹配具体错误来源。旧九项的完整审计回归也显式传context并检查实际原因。

新语义负例覆盖前缀篡改、正时长覆盖缺口、正时长互斥重叠、事件索引/引用、段ID/前驱、关闭时刻/原因及ACTUAL伪装。正时长缺口/重叠使用预置的未分配tick101状态，没有物理推进；删除其当前间隙实际触发History incomplete coverage，重新开放服务段实际触发History coverage overlap/gap。前缀错误单列为D60 event prefix modified，不把所有负例归为前缀失败。每项真实拒绝文本及对应模式见SEMANTIC_NEGATIVE_TESTS。

## D：旧九项与零调用

当前完整审计对旧三组的六个SWITCH决策视图均首先以Closure reason拒绝，原因是旧格式关闭记录不符合当前完整契约。这里没有把该错误描述为直接发现九项覆盖问题。

另从原记录独立读取active_segment_id、开放间隙、Assignment和cut，按互斥及唯一活动状态识别九项原违反，逐项文件/tick/target/字段/类型保存在OLD_NINE_SEMANTIC_REGRESSION。原三组数据及两个旧修复报告目录未改。

18个测试组全量回归通过（5组新增、8组repair、5组supplement）；最后针对正时长缺口和来源摘要加强的5组定向测试亦通过。7个可执行禁用哨兵覆盖MODEL、policy和核心估计器、融合process、ACTUAL step、Branch.advance及主H1入口，全部调用计数0。没有将原始采样次数、融合次数或人工预算令牌误算为真实WLS。

格式检查发现原测试文件写入CRLF造成无关整文件差异，已统一回仓库LF并通过git diff --check；不是科学修改。旧失败、首次测试、后续回归及修复说明均保留。

## 后续依赖与停止

H1_REVALIDATION_INTERFACE_DEPENDENCY.md仅静态登记未来主脚本需要在分支建模前建立外部来源登记，分别保留KEEP/SWITCH上下文，在适当阶段调用严格独立历史入口及verify(...,audit_context=...)，并与物理、belief和六项经济审计组成完整验收。原主脚本本轮未修改，也未运行。

当前结论限于来源核对、独立审计入口、非空身份篡改和负例证明力。没有独立复验实际MODEL物理链路，没有新增样本，没有预测或净收益改善结论，没有解除D1_A_BLOCKED。

本轮到此停止，不自动扩展来源安全系统、运行H1、开发D1-B/C/D或提交推送。
