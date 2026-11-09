# D1-B-QM-1B-RUN-RELEASE V1.1 工程实施与最终核验报告

## 最终裁定

**`D1_B_QM_1B_RUN_RELEASE_PARTIAL`**。

唯一一次Windows Job保护测试中，十二项指定非物理测试各执行一次，全部PASS，保护回执通过。但最终静态核验发现两项未满足的正式入口工程条件，故不能升级为整体READY。

**最终状态以FINAL_ACCEPTANCE.json为准。** 自动测试入口生成的ACCEPTANCE.json中READY只代表该入口当时核验的测试/保护条件；原证据完整保留，没有将其覆盖改写。最终独立核验覆盖原指令的完整验收范围，明确降为PARTIAL。

未运行G1主程序或watchdog，未设置真实批准SHA、未生成真实批准票据。真实estimate、least_squares、融合、MODEL推进、ACTUAL STEP均0。没有实际泄漏、越权或已发生的正式实验资源超限；下面两项是静态发现的工程缺口。

## 两项剩余缺口及停止纪律

1. **未来G1 watchdog最终资源判定缺少数值比较。** `scripts/stfbs_d1b_qm_run_g1_watchdog.py:22`的valid表达式检查EXITED、退出码0、cpu_complete、活动进程0、日志完整和源码一致，但未明确检查实际tree_cpu_seconds≤批准CPU和wall_seconds≤批准wall，也未核查其有限非负数值。通用supervise已有轮询保护，但进程恰好在轮询间隙退出时，不能以正常退出替代最终实际量与上限比较。此处需要最小补齐，不能宣称正式资源最终验收已完整。
2. **提前准入停止的五层科研输出不完整。** `stfbs_d1b_qm_run_evidence.py:216/222/226`返回SCENARIO_ADMISSION_FAILED、NO_Q_ONLY_FAIL_FOUND或DYNAMIC_Q_ONLY_NOT_REALIZED时，已有正确的阶段NOT_EXECUTED_GATE_NOT_MET映射，但未输出统一的完整五层科研字段。不能要求下游从缺失字段推断状态，也不能把未执行记成实际失败或PASS。应由明确的分层状态表达补齐。

详见FINAL_STATIC_REVIEW_FINDINGS.json。所需修复仅限新增工程逻辑，不需要改科学公式、场景或预算。由于本轮唯一受保护测试已使用，发现后未修改执行源码、未重复测试；保留当前源码和全部证据，停止等待审查。未用“十二项PASS”掩盖这两项遗漏。

## 基准、改动及指纹

本地HEAD：`996c04cd1d6fa103a7e002702a748a02578a9f5b`，分支main，开始时工作树干净。结束时有下列授权工程修改及新文件，未提交或推送；未fetch/pull/reset/checkout/clean。

修改四个授权文件：stfbs_d1b_qm_execution.py、stfbs_d1b_qm_budget.py、stfbs_d1b_qm_run_release.py、stfbs_d1b_qm_run_audit.py。

新增七个授权文件：stfbs_d1b_qm_run_specials.py、stfbs_d1b_qm_run_evidence.py、test_stfbs_d1b_qm_run_release.py、Release test entry/watchdog、未来stfbs_d1b_qm_run_g1.py与stfbs_d1b_qm_run_g1_watchdog.py。

SOURCE_DIFF.patch记录真实跟踪文件差异，新文件SHA与完整清单在SOURCE_DIFF_MANIFEST、RUN_POLICY和冻结回执。四项修改前源码保存在BASE_SOURCE_SNAPSHOTS。

450项既有基线文件中，仅上述四项工程文件获授权修改，其余446项不变。457项本次执行文件在启动后全部SHA一致；29项运行时文件前后SHA一致。D1-A、1A场景/model、原WLS/Q/控制/服务/经济公式及历史归档均未改。

当前工作树是Release工程候选，不是未来已经批准的最终科学执行版本。两项缺口修复后必须重新固定实际版本及SHA；不能沿用当前冻结回执宣称修复版已验收。

## 已实现的受控执行与批准根

批准文件实际SHA、独立用户预期SHA、源码/运行策略摘要分别处理。独立预期只从固定且与实验目录分离的用户授权渠道读取：`C:\Users\14738\.codex\authorizations\D1_B_QM_1B_RUN_G1_EXPECTED.json`。本轮该文件不存在，未创建它。运行策略或票据内部自带摘要不能成为预期，CLI和环境变量不提供解锁开关。

纯ApprovalExpectation测试可验证合成票据，但不产生RunPermit，也不安装真实runtime_scope；测试标签不能转为真实批准票据。真实能力需独立根、完整票据绑定、实际source/runtime/fixture验证及真实Job启动证据。保证范围不包含能修改可信启动器或独立授权渠道的恶意攻击者。

票据绑定任务/批次、源码与两个G1入口、fixture/world、分支和专项、双层与分类额度、CPU/wall、输出/尝试、审计版本及停止规则。真实上下文在首次assign、advance、fuse和估计器前检查，不回退为测试预算。G1两个入口已实现固定批次流程，**本轮仅AST/静态调用链检查，未启动或导入这两个脚本**。真实正向进程路径未进行实际验收，这是本轮禁止真实执行的边界。

未来启动合同使用绝对watchdog脚本路径，与子进程父身份核验一致；不得把任意不同命令自动视为等价受控启动。

## 调度、F2/F3与来源证明

共用coordinate_batch内核固定执行OLD、顺序DEG候选、准入、B0/B1、动态失效复现、B3、F1、F2、F3-A/B。五探针独立计算，OLD即正常参考，不增加第六前缀。首个合格FAIL后停止探针，不按下游收益调参。

D60新段融合只属于assign事务；80旧右端点先结算，公开和freeze80后才换员创建新左80；KEEP保留原事务窗口语义，不重复开段融合。动态分支在自然完成后仍沿原advance保留至H120以结算完整episode，不额外对已完成目标采样。探针只观察至80，不提前收H120终止罚。

F2固定为真实执行时B1已成功提交MEMBER_CHANGE的新左80、U0/U2 VALID来源。接口先验证批次/文件SHA/原始branch、外部历史根、TEAM_CHANGED与边界提交、服务段、raw key/slot seal/context/位置/sigma/health以及frame/WLS/Q关联，再发行VerifiedSlots，之后才建立独立历史缓存。缓存命中仅是继承行为，不是验真根。测试用完整合成文件验证此顺序，不声称已有真实B1来源。

F3-A固定B0右80 U0/U1，F3-B固定B1左80 U0/U2；各有独立专项ID/cache/frame/stream/来源账本，与F2共用同一批次预算。原测量内容保持不变，新frame使用新packet_id。错误来源、缓存branch、原始测量内容、packet/frame及pending身份有拒绝接口和负例；不增加求解器来执行这些负例。

F2一个独立processor一帧，F3两个processor各一帧；均使用原BridgeFrameProcessor的未来真实路径，专项类别MODEL_SPECIAL_TEST_WLS。测试中只调用FakeProcessor和假估计器；各1/1/1次是替身外层调用契约，不是真实WLS结果。F1只复核B1已有记录，不重算WLS。F2/F3成功也不代表服务恢复。

## 双层预算、持久日志及独立审计

外层以estimate入口计一次，底层以least_squares实际启动计一次，不将九个start/nfev/njev重复加到外层。真实候选292/2628，观察类别289、专项3、policy/audit重算/ACTUAL为0，均PROPOSED_NOT_AUTHORIZED。

真实预算在未融合窗口接管，回调通过real backend而非_double；事务克隆共享同一账本。外层及每个底层调用前检查额度并持久写STARTED；预算拒绝另记、不记已开始。开始后失败保留FAILED，不随事务回滚。账本独占创建，JSONL追加，STARTED flush+fsync在函数调用之前，保留frame身份、payload、序号和错误。未配对STARTED或损坏的尾行不能自动补RETURNED。

已导入求解器别名在串行、不可重入作用域中包装，入口检查原绑定、逐底层硬上限、正常及异常finally恢复。测试只操作带标签的假模块和假solver，原真实solver保护一直保留。真正的实时计数完整性尚未在科学运行中验证。

G/Q复核使用保存的机器人位置、world CV、原offset/radius；Q从规范frame与已保存estimate_result调用原assess_quality重新计算，不额外WLS。源码中原Q函数在合成数据上做过纯数学复核，不能将FORBIDDEN_CALL_LEDGER的零真实WLS理解为“未调用过Q数学”。合成G、radius篡改被独立计算拒绝。真实Admission只接受具有真实来源能力且经来源/同几何/GQ审核的候选，UNKNOWN不能当FAIL。

新增记录沿用原科学内核；独立控制、服务区间/时钟/重置、费用与完整经济核算路径已接线。本轮未运行真实轨迹，不证明这些真实组合已科学验收。

## 一次测试、资源与准备失败记录

唯一命令：`D:\anaconda3\python.exe -B scripts/stfbs_d1b_qm_run_release_watchdog.py --suite run_release_contract_v1 --evidence-dir reports/stfbs_lite_d1b_qm_run_release_001/WATCHDOG_TEST_001`。

12项各一次，全PASS，无跳过、无正式失败、无重跑。父PID6348、子PID12676，-I -B，真实Job成员及挂起创建后先绑定再恢复核验PASS。退出0，墙钟2.527697秒，主进程CPU1.265625秒，进程树CPU1.375秒（后代0.109375秒），计量完整，结束时活动进程0。当前工程上限120/180；未来480/600只是未批准候选，不混用。

上述资源为受保护子进程树，不冒充完整工程编写/静态准备的总CPU。真实外层WLS、least_squares、融合、MODEL物理推进、ACTUAL STEP、真实sigma搜索均0；禁止调用尝试0，保护身份未破坏。两个G1脚本从未启动。

准备期仅有一次AST名单检查失败：辅助函数test_expect被静态扫描误计为第13项。正式测试前重命名为expectation_for_bytes并保留STATIC_PREPARATION_FAILURE_001，未执行任何测试。冻结前静态完善记录及首版候选保存在PRETEST_STATIC_REFINEMENTS和FREEZE_STATIC_REVISION_001。唯一正式测试之后，没有修复源码或重新冻结另一个执行版本。

## 30项最终验收分层

| 原要求 | 本轮结论 |
|---|---|
| 1—2 正式主程序/watchdog实现 | 已实现；最终资源判定与早停输出仍有上述两项缺口，不能称完整就绪 |
| 3—5 未运行、无授权拒绝、受控调度 | 静态/替身核验成立；真实入口未运行 |
| 6—13 F2/F3可信来源与预算 | 接口及完整合成正负例通过；真实来源尚未产生 |
| 14—20 实时预算、双层、别名、持久日志 | 同一包装器替身/静态路径通过；真实计量未执行；不完整日志测试正确识别 |
| 21—23 Admission与独立G/Q | 能力与纯数学合成测试通过，未获得真实准入 |
| 24—27 十二项/零科学/当前Job保护 | 全部PASS；未来G1最终资源数值判定缺口另列，未混同 |
| 28—29 冻结保护与回执 | 446项保护文件、457项执行/29项运行时指纹一致；候选冻结完整，但不是修复后的最终批准版本 |
| 30 G1未授权未执行 | 成立，独立批准SHA为空 |

## 冻结候选与停止

RUN_G1_PRE_EXECUTION_FREEZE.json完整登记源码、G1两入口、运行时、未融合fixture/world、F2/F3来源、身份、双层预算、当前/未来资源、日志/尝试规则、批准根和测试结果。它仍为PROPOSED_NOT_AUTHORIZED。RELEASE_FREEZE_REVIEW明确其工程就绪度PARTIAL，不能仅凭文件存在批准G1。

本轮已停止。下一步仅需独立审查这两项有限工程缺口及当前证据，不能直接启动真实实验。是否允许有限修复和新的验收，应由用户另行决定；本轮未擅自执行第二次测试、改变科学规则或申请无限迭代。
