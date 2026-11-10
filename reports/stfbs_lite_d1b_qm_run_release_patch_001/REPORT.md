# D1-B-QM-1B-RUN-RELEASE-PATCH V1.1 + A1 验收报告

## 最终裁定

**`D1_B_QM_1B_RUN_RELEASE_PATCH_READY_FOR_REVIEW`**。

本补丁只证明最终资源验收和三类早停结果表达符合限定工程契约，不证明真实换员修复或任何科研收益。没有升级历史RUN-RELEASE结论；原`D1_B_QM_1B_RUN_RELEASE_PARTIAL`及61份历史证据逐字节保留。未运行原12项Release测试。

八项补丁方法各执行一次、全部PASS，正式受保护启动1次，无重试。真实estimate、least_squares、融合、MODEL物理推进、ACTUAL STEP及真实授权调用均0，禁止调用尝试0。G1两个正式main未调用；仅导入无启动副作用的纯校验函数并对main接线作AST检查。

## 基准、范围和差异

本地HEAD `a175734551a9e259b62d3c93c41f94b463108d02`，分支main，起始工作树干净，与用户指定GitHub基准字符串一致。未fetch或查询远端实时状态，不把本地引用当作额外的远端同步证明。

仅修改两个原文件：

- `scripts/stfbs_d1b_qm_run_g1_watchdog.py`：新增纯资源校验和共用最终判定，将其直接接入main的PASS/BLOCKED。
- `research/non_oracle/stfbs_d1b_qm_run_evidence.py`：新增早停结果辅助函数，在原三个早停return处补齐科学字段、disposition、scope与原始结果引用。

仅新增三个允许文件：`tests/test_stfbs_d1b_qm_run_release_patch.py`、`scripts/stfbs_d1b_qm_run_release_patch_test_entry.py`、`scripts/stfbs_d1b_qm_run_release_patch_watchdog.py`。其他新增产物均在本补丁报告目录。

G1主程序、授权验证器、预算记账、G/Q/控制/运动/服务/经济、F2/F3、原测试和旧报告均未改。实际diff在SOURCE_DIFF.patch，新旧摘要和路径在PATCH_SCOPE_AND_SOURCE_DIFF、PATCH_SOURCE_SHA256与POSTRUN_PROTECTION_AUDIT。未commit/push、未reset/checkout/pull/clean。

## PATCH-001：资源校验确实控制最终结果

新增`validate_final_resource_receipt(receipt, approved_cpu_limit, approved_wall_limit)`，从真正授权参数取上限，不从receipt自认上限取得授权。明确检查：

- 测量及两类上限字段存在、数值类型正确；拒绝bool、字符串、None、NaN、±Infinity。
- 测量非负、批准限额严格正；零测量可通过。
- receipt限额与批准限额严格相等，实测CPU/wall严格≤批准上限。
- attempts必须为真正int且恰好1。
- EXITED、真正整数退出码0、cpu_complete is True、真正整数活动进程数0。

失败原因区分INVALID_RESOURCE_MEASUREMENT、INVALID_APPROVED_LIMIT、APPROVED_LIMIT_MISMATCH、TREE_CPU_LIMIT_EXCEEDED、WALL_LIMIT_EXCEEDED、INVALID_ATTEMPT_COUNT，并保留退出、计量不完整和残留进程原因。

正式main不再使用旧valid表达式，而是：

```python
audit = final_resource_audit(receipt, permit.bindings['cpu_limit'],
    permit.bindings['wall_limit'], ledger, unchanged)
valid = audit['status'] == 'PASS'
```

最终输出直接写入这个audit，返回码也由valid控制。共用`final_resource_audit()`除纯资源PASS外仍要求账本COMPLETE及source pins确认为True，不放松原有条件。

资源前四项包含91个合成输入案例；正常、零值、精确上限通过；nextafter得到的最小严格超限值也被拒绝，没有round、isclose或额外容差。还测试缺字段、非法批准限额、限额不一致、非法尝试次数、异常退出/不完整CPU/残留进程、账本不完整和源码不一致。每例断言的是共用最终判定，而不只是孤立校验函数；AST同时证明main直接使用该判定及批准许可参数。实际案例和输出见RESOURCE_RECEIPT_ACCEPTANCE.json，非有限输入以显式类型/表示记录，未伪造为有效数值。

这些91例是八个方法内的合成案例，不是额外91次正式测试。测试没有调用G1 main、真实批准或科学子进程。

## PATCH-002 + A1：保守的五层早停语义

三个早停均包含完整五层science、逐字段science_disposition、science_evidence_scope，且不在辅助函数内执行任何科学审计。

| 早停 | EXECUTION_VALID | Q_ONLY_FAILURE_OBSERVED | 修复/恢复/完成三字段 | 执行事实与范围 |
|---|---|---|---|---|
| SCENARIO_ADMISSION_FAILED | null | null | 均null | OLD已执行；四DEG、B0/B1/B3和专项未执行 |
| NO_Q_ONLY_FAIL_FOUND | null | False | 均null | OLD和固定四sigma已检查；False仅限FIXED_FOUR_SIGMA_PROBES，NOT_OBSERVED_IN_TESTED_PROBES |
| DYNAMIC_Q_ONLY_NOT_REALIZED | null | null | 均null | probe_q_only_failure_observed=True；formal_dynamic_q_only_gate=NOT_CONFIRMED；B0/B1保留EXECUTED及原始结果引用 |

动态C路径严格采用A1：联合准入失败不能推成没有发生任何动态失效。B0/B1指标标为EXECUTED_AWAITING_FINAL_AUDIT；B3、F1、F2、F3A、F3B仍NOT_EXECUTED_GATE_NOT_MET。即使合成原始B0/B1返回包含完成观察，也不自动提升为经过协议审计的TASK_COMPLETED结论。

A/B/C的实际合成返回完整保存于EARLY_STOP_SCIENCE_ACCEPTANCE.json。None/False/True没有互换：正常参考失败不等于执行非法，正常返回、来源/GQ检查PASS、账本COMPLETE均不自动产生EXECUTION_VALID=True。

正常完成路径没有改变：保留sigma升序、首个FAIL、Admission、B0/B1、B3及F1/F2/F3时机和次数。测试校验了完整成功调用轨迹、旧/新coordinate_batch所有ops调用AST、最后成功return AST，以及模块其他原节点完全相同。原RealBatchOps.final_science及所有科学数学未修改。

## 八项测试与真实工程监督

| 测试 | 次数 | 结果 |
|---|---:|---|
| accepts_valid_and_exact_limit | 1 | PASS |
| rejects_cpu_and_wall_excess | 1 | PASS |
| rejects_nonfinite_negative_missing_and_bool | 1 | PASS |
| rejects_approved_limit_mismatch | 1 | PASS |
| scenario_admission_early_stop_has_complete_science | 1 | PASS |
| no_q_only_fail_early_stop_has_complete_science | 1 | PASS |
| dynamic_not_realized_preserves_executed_b0_b1 | 1 | PASS |
| early_stop_science_semantics_and_no_scientific_execution | 1 | PASS |

完整精确ID、各项开始/结束、次数、PASS及替身标签在DETERMINISTIC_TEST_RESULTS.json。没有静态预检失败、正式测试失败或修复重跑。所有合成输入/操作端口标记TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE。

唯一命令：`D:\anaconda3\python.exe -B scripts/stfbs_d1b_qm_run_release_patch_watchdog.py --suite release_patch_v1 --evidence-dir reports/stfbs_lite_d1b_qm_run_release_patch_001/WATCHDOG_TEST_001`。

父PID12904、子PID1664，-I -B隔离解释器。运行策略SHA `800ecaec81e1d9aad672324f7ff147a77450b46798d364dada3e7110f624afec`。实际Windows Job绑定、挂起创建后先绑定再恢复、父子身份/命令/源码均核验通过。通用supervise使用CPU120秒、wall180秒、approval_path=None，没有使用H1专用批准规则。

实际墙钟1.5166819秒，主进程CPU0.984375秒，进程树CPU1.046875秒（后代0.0625秒），计量完整，退出码0，结束活动进程0。该计量只覆盖受保护补丁子进程树，不冒充完整编写/静态准备的总CPU。测试中的480/600是合成G1收据参数，与当前真实120/180工程上限分开。

真实科学入口及已导入别名在测试加载前受保护，额外保护G1两个main及真实authorize_policy。FORBIDDEN_CALL_LEDGER中所有尝试0，保护身份未破坏；ZERO_SCIENCE_SUMMARY记录了零真实科学调用。没有通过触发真实方法再捕获异常来证明拒绝。

## 旧证据保护与完整新冻结

518项基线文件仅两个授权源码变化，其余516项不变。原Release目录61项历史产物及其SHA清单完全不变，保留原12项PASS、一次启动、CPU1.375、wall2.527697、零科学执行和最终PARTIAL，不重写为READY。

521项当前完整执行/依赖指纹和29项既有运行时文件核验通过，覆盖两个补丁、未改G1主程序、授权器、共享预算、F2/F3、来源和G/Q核验、fixture/配置、原科学依赖及三个新执行/测试文件。运行时冻结范围继承原已登记的29项Python/NumPy/SciPy/psutil及关键原生/优化文件，不声称冻结整个操作系统或所有第三方包。

新RUN_G1_PRE_EXECUTION_FREEZE.json明确OLD_RELEASE_HISTORICAL_FREEZE与PATCHED_RELEASE_PROPOSED_FREEZE，保持PROPOSED_NOT_AUTHORIZED，真实批准SHA为空、G1授权False。所有release子清单也已刷新到新source pins，不遗留旧watchdog/evidence SHA混作新版本。清单装配初稿仅有历史字段标签校正，原装配稿和说明保留于FREEZE_ASSEMBLY_001/FREEZE_ASSEMBLY_NOTE；未改源码、未重跑测试。

当前HEAD仍a175...，新补丁处于未提交工作树，逐文件SHA才是本次候选身份；未来正式批准必须固定实际最终版本，不能只沿用旧HEAD或历史冻结。

## DOWNSTREAM_EXECUTION_VALID_SEMANTICS

**状态：UNVERIFIED。**

只读检查确认G1主程序正常返回且账本COMPLETE时仍写外层EXECUTION_VALID=True；本补丁按白名单未修改它。新的`result.science.EXECUTION_VALID`在早停中是null，二者含义不同，不能以外层True代替完整科研审计。

仓库内检索当前只发现相关结果写入点，未发现直接读取外层True并转换为完整科研PASS的下游程序。因此没有证据确认一条现存误读路径，未伪报CONFUSION_CONFIRMED或捏造已发生的阻断。但是外部展示、后处理或人工消费者无法验证，不能标为全域NO_CONFUSION_CONFIRMED。原始检索命令、匹配及范围在DOWNSTREAM_EXECUTION_VALID_SEMANTICS.json。

如果独立审查确认任何下游误用，应登记RUN_G1_PRE_EXECUTION_BLOCKER，再处理授权；本补丁八项PASS不能替代该语义审查。

## 停止与授权边界

两个指定工程缺口已按V1.1+A1修复并通过本补丁合成验收。结论仅为PATCH_READY_FOR_REVIEW，不输出RUN_RELEASE_READY，也不改写历史PARTIAL。

真实RUN-G1仍未授权；预算292/2628及未来CPU480/wall600仍为候选。剩余授权依赖包括独立审查本补丁/新SHA、确认下游使用内部science及证据范围、固定正式运行版本/环境/输出/尝试身份、由用户独立确认批准票据和外部预期摘要。本次未生成或使用真实批准票据。

已完成归档并停止；不启动OLD/DEG、B0/B1/B3或F1/F2/F3科学专项，不消耗真实预算，不自动提交或推送，不追加测试。
