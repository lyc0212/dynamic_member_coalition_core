# D1-B-QM-1B-RUN-G0 V1.0 执行与独立验收报告

## 裁定与范围

`D1_B_QM_1B_RUN_G0_READY_FOR_REVIEW`。

本轮实施原V1.0及用户两项执行补充（五探针前缀、端点来源、版本权限；外层/内部/底层计数）。唯一一次受保护正式测试中，十项白名单各执行一次、全部通过。没有重试或测试后修复。

这是工程接线与非物理确定性验收，不是真实科学机制验收。RUN-G1未授权，真实入口全程失败关闭，未选择真实sigma、未获得真实Q FAIL/UNKNOWN、未验证换员修复或收益。RUN-G0指纹不代表未来RUN-G1最终冻结版本。

## 基准与源码差异

HEAD `255e306fbfbac0ded5e3a30ab552a975867345d9`，main，起始工作树干净。

最小修改两项授权工程文件：

- `research/non_oracle/stfbs_d1b_qm_execution.py`：RUN-G1封锁接线、独立ProbeSchedule、G0合成端口白名单。
- `research/non_oracle/stfbs_d1b_qm_budget.py`：分层会计、预算拒绝、失败保留、真实计数/估计器候选接线的失败关闭入口。

新增五个授权文件：

- `research/non_oracle/stfbs_d1b_qm_run_release.py`：五探针/动态分支受控接线、显式Admission和selected_sigma、MissingSensorAuthority、真实估计器候选绑定。
- `research/non_oracle/stfbs_d1b_qm_run_audit.py`：G0保护与回执、真实文件字节核验、外部注册包装、只读跨记录端点关联。
- `tests/test_stfbs_d1b_qm_run_g0.py`：十项固定确定性测试及标记替身。
- `scripts/stfbs_d1b_qm_run_g0_test_entry.py`：隔离子进程身份核验、先保护后加载测试。
- `scripts/stfbs_d1b_qm_run_g0_watchdog.py`：独占尝试、外部Job监督及专用回执核验。

允许修改的第三个文件stfbs_d1b_qm_independent_audit.py实际未改。D1-A、1A场景/model、原估计器/Q/控制/服务/经济公式、旧测试及全部历史归档未改。410项基线文件中408项保持原SHA，两项授权工程修改逐项记录before/after SHA；415项本次执行pins在启动后全部未变。SOURCE_DIFF.patch保存真实Git差异，BASE_SOURCE_SNAPSHOTS保存修改前工程源码，POSTRUN_SOURCE_AUDIT保存新旧摘要和工作树。未执行Git提交、推送、同步或回退。

## 接线与时序

### 五探针

ProbeSchedule只接受OLD和四个DEGRADED身份；不进入B0/B1 selector，不换员。每条独立fixture/注册/缓存/consumer/历史，预算共享但状态不共享。OLD本身承担正常参考，不增加第六条参考前缀。未来按原advance推进60..80，80截断不收H120终止罚。

G0测试只用合成切口跳转，不是20个真实物理tick；相同合成位置只能证明接口传递，不能证明未来独立物理前缀的几何一致。RUN-G1必须核对实际80几何、OLD G/Q准入及未提前终止。

### 显式sigma与missing

Admission冻结有序候选、首个合格FAIL、sigma/factor/probe ID、来源run和证据摘要，禁止下游择优及选中后追加探针。B0/B1构造必须显式传selected_sigma，同一冻结记录给两条独立分支；省略或.16准入却传.08均拒绝。测试用.16为合成参数，不是科学选中结果。

MissingSensorAuthority为独立新对象，60..79正常，80起仅U1 missing，sigma仍.02；U0/U2正常。未改原SensorAuthority。未来原QMBranch.raw的health分支生成MISSING；G0只验证纯MISSING结构、packet=None与公开水位，未调用raw。适配不写Q UNKNOWN。

### Assignment所有权

预算和外部上下文在首次Assignment前绑定。D60只调用一次assign，新左端点由prepare_assignment事务内部fuse。80先旧advance/右端点/结算，再公开、freeze80、预设动作；B1新左80只由换员事务生成，其反馈留pending，直到后续冻结。B0/100 KEEP提交原事务以保留first_fusion_tick语义，但无新段/左端点融合。驱动没有显式重复fuse。运动继续由world常速度规则决定，公开belief驱动控制，不改continuous_turn配置名或启用转向。

## 端点跨记录来源审计

只读关联器使用原字段：endpoint.quality.frame_id、feedback.endpoint、frame/frame_id/stream_id、result与归一化payload、历史段team/start/closure、原raw key/slot/context、profile/position/sigma/health、外部注册完整分支身份。

同tick旧右/新左根据team、段、stream、side和反馈顺序区分；歧义拒绝。保留成员的原raw可以复用，frame级packet_id按各自stream生成，不要求不同流的packet_id相等。

合法B0/B1合成证据关联通过。OLD仅改endpoint.branch时，原quality.frame_id和feedback.endpoint仍是OLD；明确抛出ENDPOINT_PROVENANCE_MISMATCH: feedback endpoint scientific identity conflict。负例保留全部字段与完整记录，没有依赖缺失文件、KeyError或无关错误。原端点/改写端点及拒绝原因保存于ENDPOINT_PROVENANCE_NEGATIVE_TESTS。

另验证raw键换成OLD、result stream换成OLD、frame sigma变更、context摘要篡改、team/tick冲突及服务段歧义拒绝。合法B1旧U0/U1右80与新U0/U2左80的原U0 slot一致，frame packet_id不同仍可正确关联。

本关联器依赖外部可信记录与注册，不宣称能识别同时篡改全部信任根的恶意可信端。G0数据全部合成，原始Q值不是实际计算结果。

## Source pins与外部历史根

SourceAnchor来自测试前冻结的外部RUN_POLICY清单；逐项核对规范相对路径、root内解析、存在性、真实SHA、外部预期SHA、字节数、版本与检查时刻。运行时不能用重算的自身hash替代外部预期。测试副本内容篡改、自身重算hash、缺失副本和路径穿越分别拒绝，未修改真实旧归档。

VerifiedRegistration在分支构造前包装原外部fixture/prefix注册。真实接线准备函数先验证source pins及fixture/branch一致性，再构造未融合分支并接管预算。历史审计仍显式使用外部context；即使Branch内部_audit_context=None，外部审计仍成立；历史前缀和来源/分支篡改拒绝。

## 分层会计与整数预算提案

外层MODEL_*_WLS计一次estimate入口；内部九初始点与底层least_squares单独记，不把nfev/njev或九个start重复加到外层账本。

七项字段单列：outer_wls_started/returned/failed、budget_rejected、least_squares_started/returned/failed。预算拒绝发生在外层执行前；已执行失败不随事务回滚。测试中一次外层替身产生9个内层替身启动；失败例外层已开始1次、内层启动2次（返回1/失败1）；共享账本与分类账一致。所有这些是标记替身调用，真实外层与底层均0。

主链保守上限：五探针105+B0 61+B1 62+B3 61=289外层。B3不足两测量时可能少于此上限。原28次专项无逐项调用依据，不能因此核定317。

本次最小提案：F1只复核B1已有记录0次；F2规划一条新融合流一帧合法VALID继承组合正例1次；F3规划两个隔离流各一正例2次；其余篡改/文件/历史/经济/Q代数审计不重算WLS。提案292外层、最多2628底层。旧317/2853保留为未采纳的条件性算例，不伪称已批准。

上述专项数量是未来RUN-G1最小协议提案，尚未实施真实专项；必须在第一次WLS前核定专项实际实现、真实计量回调完整性、科学版本与资源上限。若实现需要更多融合或额外前缀，必须在RUN-G1前修订提案，而不是运行后加预算。

RUN_G1_BUDGET_PROPOSAL明确PROPOSED_NOT_AUTHORIZED，外层/内层分别OUTER_WLS_BUDGET_PROPOSED_NOT_AUTHORIZED、INNER_SOLVER_BUDGET_PROPOSED_NOT_AUTHORIZED；没有任何批准预算。本轮真实估计器绑定与底层计数接线都在require_run_g1之前失败关闭，不能凭合成测试声称真实埋点已验证。

## 十项测试与外部资源

十项精确白名单结果见DETERMINISTIC_TEST_RESULTS和TEST_OUTPUT.log，无增加第11项、未运行旧1A/ENG测试集。每项一次，全PASS，原始标准流与LAUNCH/RECEIPT保留。

唯一命令：`D:\anaconda3\python.exe -B scripts/stfbs_d1b_qm_run_g0_watchdog.py --suite run_g0_preflight_v1 --evidence-dir reports/stfbs_lite_d1b_qm_run_g0_001/WATCHDOG_TEST_001`。

父PID28660，子PID27272，-I -B隔离解释器。实际Windows Job核验通过，挂起创建、先入Job后恢复。退出0；墙钟13.9441225秒，主进程CPU13.203125秒，进程树CPU13.25秒（后代.046875秒），计量完整；上限120/180秒。结束活动进程0，无超时/重试。supervise approval_path=None，未调用H1批准/回执规则。

持续保护在测试加载前安装，含底层WLS别名、真实融合/采样/advance/run、ACTUAL和R搜索。PROBE及动态真实入口的许可拒绝先于任何科学调用；普通布尔/字典凭据不能解锁。替身不能恢复底层求解器，guard_checks无破坏，禁止尝试0。

## 原指令23项验收结论

| 序号 | 工程结论 |
|---|---|
| 1—4 | 独立PROBE、选择器分离、五前缀方案及状态隔离通过非物理测试 |
| 5—6 | 显式sigma与合成profile/raw/frame/Q来源关联通过；真实准入未执行 |
| 7—8 | B3 missing接口及结构通过，不直接设置UNKNOWN |
| 9—11 | 真实schema字段关联、OLD改branch拒绝、合法合成链正例通过 |
| 12—14 | 实际文件字节对外部冻结预期、重登记拒绝、外部历史context通过 |
| 15—16 | 有整数最小预算提案及调用路径；专项实现与真实计数留待RUN-G1核定，未批准预算 |
| 17—18 | D60/80所有权及公开时序通过合成检查，运动权威静态保持 |
| 19—21 | 十项各一次PASS、零禁止尝试与零真实科学执行、真实Job资源保护PASS |
| 22 | D1-A/1A/旧归档不变；仅修改明确授权的两个D1-B工程文件，作为新G0版本独立登记 |
| 23 | 真实RUN入口保持关闭，需要独立RUN-G1授权与受控版本冻结 |

## 停止与剩余边界

没有真实sigma选择、真实物理前缀、B0/B1/B3实验、F1/F2/F3端到端、Q恢复、服务恢复、任务完成或经济收益结果。未来门槛未满足的阶段必须记NOT_EXECUTED_GATE_NOT_MET，不能记PASS。

G0工程接线已建立，不等于RUN-G1已经具备无条件启动许可。后续仍须独立审查本轮源码与预算提案，核定专项实现/真实计数，固定最终科学源/fixture/schedule/source pins，批准CPU/wall/次数和整数预算。不得把本报告或当前源码SHA冒充未来最终授权。

完成归档后停止，不自动RUN-G1，不提交或推送。
