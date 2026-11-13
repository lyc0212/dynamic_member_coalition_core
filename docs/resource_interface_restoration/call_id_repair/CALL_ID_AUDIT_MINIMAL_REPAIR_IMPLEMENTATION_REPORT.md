# CALL_ID_AUDIT_MINIMAL_REPAIR_IMPLEMENTATION_REPORT

状态：IMPLEMENTED_PENDING_ISOLATED_ENGINEERING_VALIDATION

## 1. 基线及范围

分支main，HEAD 098b813a1f8b7a2dd276dd1ed5f8948b0b211119，起始工作树干净。BASELINE.json记录原始SHA256；本次只修改journal.py和resources.py，另新增此报告目录。未修改历史Journal、002/003、B阶段失败证据或消费标记。

## 2. 代码及函数清单

journal.py：
- _Immutable、CallHandle、AllocationRecord、_VerifiedCall、CommitCredential：不可变映射、强引用和内部凭据工厂。
- NestedJournal.allocate：attempt_id:CALL_001格式、正整数序号和对象身份分配。
- _verify、_check_extra、_commit：统一身份预验证、保留字段拒绝、提交后凭据登记。
- require_open、_identity_mutation、_bad_identity：永久POISONED、终态拒绝及诊断。
- audit：实际持久化读取、凭据有序比较、原分配绑定及生命周期审计。
- LocalJournal.__init__/append/seal/close：初始化前attempt验证、封闭写入、幂等close、只读保留。

resources.py：
- AuditedDurableResourceLedger.invoke、IndependentRecorder.invoke：消费前检查NestedJournal状态。
- Budget.check/finalize：执行准入、不可逆最终化和失败封闭。
- initialized_budget：正常yield返回才尝试成功最终化；执行异常走失败最终化并保留原异常。

## 3. 不可变身份和永久失效

CallHandle不暴露可变身份字典，内部为不可变tuple，普通修改接口含setitem/delitem/update/setattr/delattr/clear/pop/popitem/setdefault/ior均在修改前拒绝；再次调用__init__也拒绝。
OPEN/FINALIZING的修改尝试永久POISONED，恢复字段不能解除。终态修改只拒绝，不改变已成立状态。
注册表以原始对象强引用和is判断，不以结构相等或id数值判断。复制或同值对象不能通过正式_verify。
身份、类别和extra验证先于ModelJournal类别映射及写入。保留字段包括身份、状态、预算、ACTUAL/MODEL类别键、sequence和actual_budget_before/after。公开event使用位置专用参数，使重名关键字可在接口层被识别拒绝。

## 4. AllocationRecord与CommitCredential

AllocationRecord持有原始handle及不可变身份快照。_VerifiedCall只由持私有工厂token的内部路径创建，保留原AllocationRecord。
LocalJournal.append成功返回sequence/digest后才登记CommitCredential，包含原AllocationRecord、原快照、实际sequence/digest及预期生命周期状态。登记失败立即POISONED，不补写凭据。
保证限于同一进程生命周期、正常公开接口；不宣称抵御恶意反射，不宣称可由历史JSONL恢复Python对象身份。

## 5. R26身份交换防护及独立审计

audit重新读取实际Journal，筛出RESOURCE_CALL，与内存正式凭据逐条比较长度、顺序、sequence、digest，然后比较事件身份与原始VerifiedCall快照及AllocationRecord。
因此在预验证后、序列化前交换两个合法已分配身份，即使交换后的摘要链正确且凭据保留实际sequence/digest，也会在快照比较处触发ALLOCATED_IDENTITY_MISMATCH。
该说明是静态实现路径，不是已执行R26证明。未来隔离注入应包装真实LocalJournal.append，在序列化前交换事件字段，保留原始allocation和实际返回提交信息；不得通过破坏摘要取得假通过。
普通对象交换及extra交换分别由is身份验证和保留字段拒绝处理。额外RESOURCE_CALL、孤立凭据、顺序或摘要错位均不能通过。非资源事件只受LocalJournal原完整性约束，不要求分配凭据。

## 6. CALL_ID规范

attempt_id仅要求非空字符串，不加字符集限制；LocalJournal在创建文件前拒绝非法attempt_id。
解析采用最后一个:CALL_分隔位置，允许attempt_id本身含冒号或:CALL_。
后缀必须ASCII十进制正整数并满足重新格式化完全相等，因此CALL_01、CALL_0001、CALL_000、非数字及其他attempt均拒绝；999后自然扩展1000。
分配计数明确要求type is int，bool不合法；与事件sequence独立。

## 7. 最终化及Journal状态

Budget与NestedJournal状态和LocalJournal物理invalid分离。
正常上下文返回调用Budget.finalize；已有执行异常不会尝试成功最终化。FINALIZING禁止新allocate/event及资源调用，但允许只读audit和内部封闭。
finalize分别尝试WLS、R、Assignment对账；单项失败纳入failure列表，不跳过后续seal和audit。随后定终态并关闭文件。存在任意失败进入FINALIZED_FAILED并抛错，不可重试恢复PASS。
seal只做物理完整性及持久化检查，不因资源对账失败而设置invalid。健康Journal可形成FINALIZED_FAILED、sealed=True、invalid=False，并在close后继续records只读。
append在sealed检查处返回JOURNAL_SEALED，检查位于使Journal invalid的异常块外；重复close不改变完整性。
正常审计仍拒绝FAILED/REJECTED取得整体PASS；本次未改变该业务语义。

## 8. R36—R39实施对应

| 编号 | 支持路径 | 本轮执行 |
|---|---|---|
| R36 | 不可变记录、原handle强引用、终态修改不变、OPEN/FINALIZING修改POISONED | 未运行 |
| R37 | require_open拒绝FINALIZING操作，audit仅只读实际Journal与凭据 | 未运行 |
| R38 | 独立汇总三类对账，失败也尝试seal/audit/close；语义失败不污染物理invalid | 未运行 |
| R39 | 两种资源invoke、Budget.check在消费和计数前检查NestedJournal | 未运行 |

R01—R39定义采用用户测试设计补充，未删减；本轮没有编写或运行测试运行器，没有实例化任何账本或Branch。

## 9. 静态核查及限制

完整diff已读取；AST仅解析目标文件文本，未导入新模块；git diff --check通过。
保护清单全部未变；原有三类额度744/63/7263及R/Assignment各2次未改，科学算法和共享ResourceLedger未改。
BLOCKER：静态检查未发现必须扩大范围的阻断；不代表动态实现正确性已证实。
LIMITATION：身份篡改、提交凭据登记失败、R26交换、资源异常及终态行为尚未运行验证；内部私有工厂保护不覆盖任意Python反射攻击，凭据不支持跨进程重建。
OPTIONAL：无额外重构纳入本次任务。

## 10. 授权边界与最终状态

R01_R39_EXECUTION = NOT_AUTHORIZED
B_REVALIDATION = NOT_AUTHORIZED
SCIENTIFIC_EXECUTION = NOT_AUTHORIZED
TESTS_EXECUTED = FALSE
SHARED_CORE_MODIFIED = FALSE
SCIENTIFIC_ALGORITHM_MODIFIED = FALSE
RESOURCE_BUDGET_CHANGED = FALSE
ATTEMPT_MARKERS_MODIFIED = FALSE
GIT_COMMIT_PUSH = FALSE
EXTENSION_003 = INCOMPLETE
PRODUCTION_RUN_ADMISSION = BLOCKED

实施到此停止，等待另行授权的隔离工程复验。

## 修改前后指纹

research\non_oracle\local_dev\journal.py

修改前 1e50fa67eb50563ce2ad56465f6a16b3f2cb47816d3b0d2d17f830f1c5ef9949

修改后 37fa08a7658eb4127cb38d79383b5d78756f1a5549d9c1b7c1560ccf46170593

research\non_oracle\local_dev\resources.py

修改前 39d4218ccf4437483b8025ff8f9b9bb6e9cc1a1ccc90e968efbc60c93dc4274a

修改后 a939c9348f0f604463450a7781474e7e94462fb14b6865c87a25ebec3197a501

