# D1-B-QM-1B-ENG V1.1 与局部修订：实施验收报告

## 最终裁定

`D1_B_QM_1B_ENGINEERING_READY_FOR_REVIEW`。

十项白名单确定性测试各执行一次，全部PASS；无跳过、失败或自动重试。只证明新增接口、调度、预算及外部注册在非物理测试中的工程性质，不证明真实动态Q失效、G/Q恢复、服务恢复、任务完成或收益。

## 实施基准与文件边界

实际HEAD：`69c862f406fe155351ff1adb78be432131b01564`，main，开始时工作树干净。结束时只有本轮六个新增文件与报告目录未跟踪；已有跟踪文件diff为空。未commit/push、reset/checkout/pull，未清理既有归档。

新增文件：

- `research/non_oracle/stfbs_d1b_qm_execution.py`：受控入口、预算接管、完整科学身份、预设选择器、D60/80/100调度。
- `research/non_oracle/stfbs_d1b_qm_budget.py`：共享批次账本、分支回调身份、类别/总额上限及失败调用记录。
- `research/non_oracle/stfbs_d1b_qm_independent_audit.py`：外部fixture注册、独立历史入口、专用启动与回执核验、持续零科学保护。
- `tests/test_stfbs_d1b_qm1b_eng.py`：十项唯一指定测试与显式合成替身。
- `scripts/stfbs_d1b_qm1b_eng_test_entry.py`：隔离Python子进程入口，核验身份并先安装保护再加载测试。
- `scripts/stfbs_d1b_qm1b_eng_test_watchdog.py`：独占尝试、运行策略、通用Windows Job supervise及专用核验。

启动前固定383项执行文件SHA256，结束后全部一致；另复核377项既有源码与保护归档，全部未改。原D1-A、QM-0、QM-1A来源及结论均保留。

## 调用链与融合所有权

D60：先由fixture在分支之外建立外部注册；构造QMBranch未融合状态；检查无streams/fusions/feedback/raw请求/Assignment/服务段/观测费用后接管共享预算；再允许未来受控调度进入assign。新段左端点只由prepare_assignment内部fuse负责，驱动不显式调用fuse。

D80：原advance负责旧联盟运动、右80融合及服务结算；之后发布到期声明，policy_view冻结一次belief80；预设B0保持、B1调用一次换员assign。新左80在冻结后产生，留在pending。D100执行同样合法冻结后KEEP。

静态核查补充：原KEEP事务虽不创建新段、不融合，但会更新first_fusion_tick。驱动仍提交KEEP事务，保留这个原科学行为；没有为了避免重复融合而跳过原事务。原QMBranch.run仍拒绝，未调用D1-A R策略。

调度测试使用SyntheticPort合成跳至80/100，无积分、实际advance或实际传感器采样。Assignment事务中的融合被严格限定的fake_fuse替代。旧右80与新左80是不同职责，不被错误合并；fake_fuse调用次数不等于WLS次数。

## 十七项工程验收

| 项目 | 结果与证据范围 |
|---|---|
| 1 受控驱动 | 已实现薄调度与原科学方法绑定；真实RUN保持关闭 |
| 2 冻结源码 | 377项保护文件、383项执行指纹复核一致 |
| 3 首次融合前接管 | prepare_branch在返回分支前完成检查/接管；预算身份测试通过 |
| 4 共享及克隆 | Branch._transaction_clone仍指向同一D1BBudget，多分支共享总cap |
| 5 融合回调 | 原fuse仍从self.budget.estimator创建回调；测试替身静态绑定与ledger/branch身份核验通过，未创建真实融合流 |
| 6 无预算拒绝 | ENG无真实估计器绑定，NO_APPROVED_REAL_BUDGET；错误/晚接管拒绝，无D1-A回退 |
| 7 选择器映射 | QM_B0_KEEP→B0，QM_B1_MEMBER_CHANGE→B1；错误映射及probe调用动态选择器拒绝 |
| 8 科学身份隔离 | 完整身份进入cache/历史/端点/回调；合成状态隔离、OLD端点替代拒绝通过 |
| 9 D80顺序 | 合成顺序、单次freeze、LEFT80 pending、100消费及KEEP不额外融合通过 |
| 10 运动权威 | world常速度规则、point/advance/control静态AST一致；无连续转向执行 |
| 11 外部历史上下文 | 外部fixture/prefix/pins注册早于分支；忽略内部_audit_context仍可审计；前缀/跨分支篡改拒绝 |
| 12 授权封锁 | execute_run及真实QMBranch调度在科学方法前拒绝；普通布尔、字典、字符串凭据均无效 |
| 13 测试数量 | 恰好十项，各一次，全部PASS |
| 14 禁止尝试 | 全部0，guard_checks无破坏记录 |
| 15 零科学执行 | 真实WLS、真实融合/采样、MODEL推进、ACTUAL STEP、sigma搜索均0 |
| 16 外部保护 | 实际父子PID/命令/策略/源码/解释器/Windows Job核验PASS，资源完整 |
| 17 原始证据 | 日志、标准流、回执、注册契约、指纹及独立报告保存 |

## 共享预算与事务

五类分别登记：MODEL_OBSERVATION_WLS、MODEL_POLICY_EVALUATION_WLS、MODEL_SPECIAL_TEST_WLS、MODEL_INDEPENDENT_AUDIT_WLS、ACTUAL_WLS。ACTUAL类别在本驱动禁止。批次共享cap在调用替身前检查；超限拒绝不调用替身。失败替身调用保留在账本，不随科学事务状态回滚。ContextVar分支作用域在创建回调时固定完整科学身份，随后回调不依赖另一个分支的当前作用域。

本ENG没有可执行的真实估计器或正式预算批准。测试中的计数属于标记替身，不是WLS实耗。238仍仅设计估算；未来正式预算及真实求解器绑定必须在1B-RUN独立冻结。既有Branch与1A模块均未修改。

## 身份、运动及外部审计

OLD参考固定normal .02；四个DEGRADED身份分别对应固定声明.04/.08/.16/.32，仅做静态映射，不搜索或计算sigma结果。动态B0/B1使用各自完整身份，不能拿OLD右80端点替代。B3只建立独立身份与KEEP动作映射，missing/UNKNOWN真实专项尚未实施。

Config仍为continuous_turn、turn_max_angle=.5；本MODEL目标真值由world.motion_rule与point的常速度公式决定。Branch.advance读取world速度，机器人控制读取self.frozen公开belief，不调用真实Environment的连续转向机制。没有修改配置或H1。

ExternalRegistration保存冻结fixture摘要、完整分支、不可变prefix_json及source pins。audit_registered从该外部注册构造AuditContext，调用audit_branch_independent，不拿运行中的Branch._audit_context反向创建信任根。它仍复用既有独立历史审计，不新增物理或经济公式。

本轮只核验未融合历史及合成Assignment/TEAM_CHANGED历史。真实raw/stream/packet、合法融合反馈、实际生命周期与经济账本仍需未来独立检查，不能把历史审计PASS提升成全面物理证明。F1/F2/F3真实组合尚未执行。

## 唯一正式测试与资源

命令：`D:\anaconda3\python.exe -B scripts/stfbs_d1b_qm1b_eng_test_watchdog.py --suite eng_interface_v1 --evidence-dir reports/stfbs_lite_d1b_qm1b_eng_001/WATCHDOG_TEST_001`。

父进程PID27936，子进程PID27120，隔离Python -I -B，实际Windows Job成员关系核验通过，挂起创建并加入Job后恢复。退出码0；墙钟5.0307717秒，主进程CPU1.15625秒，进程树CPU1.21875秒（后代0.0625秒），计量完整。上限CPU120秒/wall180秒，结束时活动进程0，无超时，无自动重试。通用supervise使用approval_path=None，未调用H1专用批准/回执规则。

RUN_POLICY、TEST_ATTEMPT、LAUNCH_BINDING、FORBIDDEN_CALL_LEDGER、DETERMINISTIC_TEST_RESULTS、FINAL_SUPERVISION_VERIFICATION及WATCHDOG_TEST_001保留原始记录。没有首次正式失败或失败修复重跑。启动前只做源码/AST/语法/SHA检查。

## 限制与停止

真实RUN入口是明确fail-closed的ENG版本，未来单独授权仍需受控Release接线，不能仅传入approved=True开放。本封锁只针对新增受控路径，不宣称整个仓库任意直接Python调用均被授权系统控制。

未运行1A十二项旧测试，也未进入1B-RUN、MODEL/ACTUAL实验、Q-only FAIL准入、F1/F2/F3端到端、服务恢复、完成或收益比较。所有合成端点/反馈统一标记TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE。后续必须分别判断EXECUTION_VALID、Q_ONLY_FAILURE_OBSERVED、GQ_RESTORED、SERVICE_RESUMED、TASK_COMPLETED。

本轮完成后停止，等待独立审查；不自动启动1B-RUN，不提交或推送。
