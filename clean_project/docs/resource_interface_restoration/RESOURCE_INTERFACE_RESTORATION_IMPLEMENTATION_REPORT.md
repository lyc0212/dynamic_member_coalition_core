# RESOURCE_INTERFACE_RESTORATION_IMPLEMENTATION_REPORT

RESOURCE_INTERFACE_RESTORATION_IMPLEMENTATION_A = IMPLEMENTED_PENDING_ENGINEERING_VALIDATION

DESIGN_REVIEW_REFERENCE = V1.2.1_ACCEPTED (用户提供的审查依据；未独立读取审核全文)
IMPLEMENTATION_BASELINE = A_V1.0_PLUS_ADDENDUM_V1.0
V1_2_1_FULLTEXT_VERIFIED = FALSE

## 基线与修改范围

实际仓库 D:/1st/dynamic_member_coalition_core，分支main，HEAD 8a957d8a438a900b6f52e9a0e94e31c0464395f1。
原始Git状态与保护文件SHA256见BASELINE.json。实测已有6个未跟踪迁移材料，比授权文字列举多1个；全部保留，未纳入本次实施源码。
Git曾要求safe.directory，所有查询使用命令级-c参数，未修改全局或仓库配置。
本次只新增research/non_oracle/local_dev/和本报告目录；未改已有跟踪文件、历史002/003或marker。历史参考源码以TXT副本保存，不移动原件。

| 新文件 | 内容 | 共享核心 |
|---|---|---|
| research/non_oracle/local_dev/__init__.py | 包声明，无启动入口 | 否 |
| research/non_oracle/local_dev/journal.py | LocalJournal、NestedJournal、ModelJournal、调用图及闭合审计 | 否 |
| research/non_oracle/local_dev/resources.py | 核心ResourceLedger外置适配、独立R/Assignment、Budget及初始化保护 | 否 |
| research/non_oracle/local_dev/diagnostics.py | stderr专用诊断、并发日志读取、独立可靠回执、监督调用包装 | 否 |

## 已实施接口

AuditedDurableResourceLedger直接继承冻结ResourceLedger，不叠加旧DurableResourceLedger。
固定ACTUAL_POLICY_WLS=744、ACTUAL_OBSERVATION_WLS=63、ACTUAL_SOLVER_START=7263。MODEL_MAP及逆映射来自002。ModelJournal映射类别和预算键，另保留明确的actual_budget_before/after及scientific_execution。
RRecorder与AssignmentRecorder各额度2，不进入WLS账本；所有组件共享唯一LocalJournal、NestedJournal和ModelJournal。
CALL_GRAPH_ALLOWLIST据Branch:79/209、policy:38/98、estimator:71恢复：根R或观测WLS；R内policy WLS或Assignment；WLS内solver。未知类型拒绝。
call_id使用attempt_id:ordinal，sequence只由LocalJournal分配。记录actual/model类别、父关系、预算和生命周期状态。
LocalJournal独占新文件，序列化完整行，处理部分写入、flush/fsync并核对尺寸；异常立即invalid。历史链、PID/thread及文件身份受核验。没有事件重写或attempt恢复。
WLS核心扣减后才进入expensive，STARTED成功落盘才调用fn；RETURNED在super.invoke返回及其执行后完整性检查之后。系统完整性异常不归为逻辑REJECTED；已经启动的异常为FAILED，保留原异常传播。SolverFatal保留保守包装。
R/Assignment权威JOURNAL_COMMITTED_USAGE每次从持久化、摘要校验后的STARTED重建；RUNTIME_COUNTER单独核对，不以另一个内存变量替代权威。WLS计数同样核对持久化STARTED。不退款。
R保存provenance后才写STARTED，绑定文件路径、SHA256和tick；STARTED失败时provenance仅是未绑定材料。
initialized_budget保护全部初始化并在尚无Journal时使用stderr诊断。调用者只能在该上下文内创建Branch；本库不创建Branch、attempt或marker。

## 合并日志与独立回执

既有Windows API.create:133使用CreateFileW share=3 (READ|WRITE)，stdout/stderr共享同一写句柄。
新shared_reader显式用CreateFileW GENERIC_READ、share=7和OPEN_EXISTING，在Win32共享模式上与写句柄兼容；不假设Python默认分享行为。
DiagnosticReceiver在监控启动前开始，运行期间按20ms轮询，保留原始文件，专用前缀为@@STFBS_RESOURCE_DIAG_V1@@；接收身份和schema校验后独立写diagnostic_NNNNNN.json。
Worker输出单行紧凑JSON，核对字符写入结果并flush；保存失败不重写同一Journal事件。
回执使用独占创建、完整写入循环、fsync和尺寸确认；最终回执补真实worker_exit_code或UNKNOWN。
monitor_supervised显式将receiver接入run_monitored外围，未替换共享Job API；未来调用者必须显式采用此包装，本A阶段没有改写历史控制器。
若读取、解析或回执保存失败，状态为UNRECONCILED且禁止审计PASS。外层回执不是Journal闭合证明。

## 静态审查与未验证项

已静态核查：
- 三类ACTUAL与两类独立额度不变，无共享核心修改。
- 唯一组件构造关系无循环，Budget核对对象身份。
- 只有LocalJournal落盘和分配sequence；包装器单次委托。
- REJECTED限于启动前逻辑边界/额度/核心已确认逻辑拒绝；不以异常类型宽捕获把已启动失败再次标成REJECTED。
- Journal失效时不补终结事件，不继续科学调用；未闭合状态保留。
- WLS RETURNED不先于核心执行后检查。
- 新文件通过AST语法解析（只解析文本，不导入或执行模块）；git diff --check无跟踪文件空白错误。新文件另以文本审查，不将未跟踪文件误称为已受git diff完整覆盖。
- BASELINE.json列出的原始源码、历史证据和marker哈希复核相同。

尚未验证：实际Windows并发读取、部分写入/磁盘故障行为、诊断发送失败、嵌套闭合、solver异常、权威计数对账、初始化失败及既有真实执行链的集成行为。
所有这些都需要另行授权的B阶段工程验证；没有测试PASS、工程验收或可科研执行声明。
未安装包，未导入新适配模块，未运行pytest/smoke/M3或科学函数。
通道共享模式的确认是源码依据，不是实测并发验收。

## 科研与权限状态

SHARED_CORE_MODIFIED = FALSE
SCIENTIFIC_ALGORITHM_MODIFIED = FALSE
RESOURCE_BUDGET_CHANGED = FALSE
ENGINEERING_TESTS_EXECUTED = FALSE
SCIENTIFIC_COMPUTATION_EXECUTED = FALSE
GIT_COMMIT_PUSH = FALSE
EXTENSION_002 = FAILED_FREEZE_PROTOCOL
EXTENSION_003 = INCOMPLETE
H1_VALID_CELLS = 3
NEW_VALID_CELLS = 0
H2_KEEP_ATTEMPT = CONSUMED
OTHER_FIVE_ATTEMPTS = NOT_STARTED
MINIMAX_REGRET = NOT_COMPLETED
SCIENTIFIC_EXECUTION_STARTED = FALSE (仅指本A阶段)
PRODUCTION_RUN_ADMISSION = BLOCKED

本阶段到此停止，等待用户针对B阶段工程测试的独立授权。
