# D1-A G3 历史事务 P0/P1 补充验证

## 结论

**G3_HISTORY_SUPPLEMENT_READY_FOR_REVIEW**。P0、P1与原8组历史回归均通过。D1-A仍为**D1_A_BLOCKED**，本报告不是独立验收，也不是完整G3或D1-A通过。

起始和结束HEAD均为1105260ab0a811f13ab334d8a00cae300675a13a，起始工作树干净。修改严格限于model、history、history_audit、原repair测试及新增supplement测试；verify仅为接入外部可信审计上下文作必要修改。没有修改冻结生产模块、旧报告或三组H1记录，没有提交、推送或运行新H1。

## 首次复现与失败保留

修改前以实际旧Branch.finish入口、预置融合替身构造T0未分配、T1已分配的tick60状态，再模拟处理tick61。P0_FIRST_FAILURE.json记录左边界终止产生History cutoff mismatch及完整栈，正式状态未部分提交。进一步用保存的原源码隔离加载原MODEL入口，P0_MID_INTERVAL_BASELINE_REPRO.json记录非网格when=3.025、processed_tick=61时因另一任务端点仍为60而抛出Stale current endpoint，证明不仅是时间取整问题。

P1_FIRST_FAILURE.json的第一次篡改未绕过，原因是事件副本未一致修改而触发旧引用检查，原记录保留，没有把它伪装成成功绕过。补做所有事件副本、段ID/引用及端点同步改名后，原快照审计器接受，见P1_CONSISTENT_BASELINE_REPRO.json。该结果是旧审计器实际运行所得，不是测试自行返回PASS。

首次修复回归有1项旧测试失败：它在tick120只终止一个任务后就要求全局完整切口合法。本轮将其改为全部任务处理后调用严格seal_history_cut；没有放宽最终覆盖、端点或事件检查。FIRST_REGRESSION.log及后续日志全部保留。

## P0最小修复

prepare_terminal显式接收when与processed_tick。任务历史终止覆盖按when结算；history.cutoff_tick和事件/外层终止元数据按processed_tick登记，独立审计检查处理区间和两处元数据一致性。不再使用ceil推导处理切口。

finish只对当前任务进行暂存终止、原子提交与局部历史检查，不提前更新尚未结算任务的cutoff。新增seal_history_cut在所有任务完成当前区间处理后统一更新活动历史cutoff并执行原严格完整审计。Branch.advance静态调用链已接入：每任务finish在循环内，seal_history_cut在全体处理后。STATIC_CONNECTION.json记录真实源码位置；本轮未执行advance，不能宣称已做实际MODEL物理端到端验证。

左边界when=3.0、processed_tick=61的真实测试结果为cutoff=61、覆盖终点=3.0；另一任务在局部终止后仍为cutoff=60、端点60。补齐其61端点和一个有效服务区间后，最终审计通过。非网格3.025与右边界3.05同样通过。人为保留过期端点再声明完整切口，必须失败。详情见P0_BOUNDARY_CASES.json。

多任务相反处理顺序分别通过，并比较最终任务状态、Assignment、经济分量和完整语义事件；仅允许顺序依赖的event_index不同，不删除事件、时间、原因、来源等科学字段。覆盖同tick双终止、完成与逃逸混合、继续服务、双episode结束和终止暂存失败原子性。

## P1可信身份与前缀

新增冻结AuditContext，包含外层预期分支和创建时D60前缀JSON登记，独立于可变历史。audit_branch允许外层显式传入原上下文；内部运行使用创建时固定的不可变上下文，而不从事件/段/端点推导身份。完整跨分支篡改测试即使修改branch.name及所有内部字段、重算段和历史摘要，仍用原上下文拒绝。

新事件、新段及新端点统一核对MODEL/SIMULATED来源、目标和可信分支。原D60事件前缀必须逐项保持；继承段的开始身份、前驱、团队、角色和初始时钟不可变；允许其后续时钟、端点和关闭记录合法扩展；原已关闭段、已关闭间隙不能改写。新增记录不能靠改标ACTUAL绕过。

verify新增显式audit_context参数，未提供时fail-closed，避免旧调用静默绕过身份验证。此处不是伪造ACTUAL checkpoint。未来授权的独立审计调用方需要在外层保存并提供创建时上下文；旧H1执行/审计驱动未在本轮运行或整体联调。

## 测试、预算与边界

最终13组测试通过：5组supplement与原8组repair，组内覆盖P0-T1至T10及P1各项身份/来源正负例。测试使用纯状态夹具和确定性融合替身，不调用真实WLS。最后回归受7个可执行禁用哨兵保护：MODEL估计器、policy估计器、核心估计器、融合process、ACTUAL step、Branch.advance和主H1入口，调用计数全部0，见FINAL_ZERO_WLS_STEP_PROOF.json。

旧三组H1及旧九项违反记录只读保留；旧异常仍被拒绝，原D1-A BLOCKED不改写。初始复现使用融合替身，后续完整回归在全套禁用哨兵下执行；不虚报最早复现命令已经装有所有哨兵。

原始上下文的可信性由外层持有方保证；本轮证明的是内部记录及branch.name同步改写不能改变该外部期望，并非对恶意可信调用者替换整个信任根的OS安全证明。

本轮只核验历史事务、时序和身份，不核验真实多任务物理执行、WLS精度、收益改善或完整系统性能。没有重算KEEP/SWITCH收益，没有主H1或ACTUAL执行，没有时变传感器实验、独立科研样本、D1-B/C/D或DEV/TEST。

## 归档与停止

BASELINE、SOURCE_PINS、REPAIR.diff、首失败记录、边界数据、身份审计及完整日志均位于本目录。旧两个报告目录未改。完成后立即停止，等待独立审查；未解除D1_A_BLOCKED，也未授权主H1复验。
