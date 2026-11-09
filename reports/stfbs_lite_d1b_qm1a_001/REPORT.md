# D1-B-QM-1A V1.1 实施与确定性验收报告

## 裁定

`D1_B_QM_1A_INTERFACE_READY_FOR_REVIEW`。

方案审查通过后，在原授权范围内新增六个接口、审计、测试与启动文件；仅启动一次受保护测试。12项指定测试各执行一次，全部通过，无跳过、失败或重试。此结论仅为接口与确定性工程验收，不是物理恢复或算法收益证明。

## 基准与变更

实际 HEAD：`8bc076e125838baf91163fd054ef9ce4f076b329`，分支 main。起始工作树干净；结束时仅六个新源码/测试文件及本报告目录未跟踪，已有跟踪文件无 diff。未提交或推送。

- `research/non_oracle/stfbs_d1b_qm_scenario.py`：独立未融合 MODEL fixture、静态结构与来源校验。
- `research/non_oracle/stfbs_d1b_qm_model.py`：物理传感器声明与公开快照分离、公告水位、预设成员替换及候选准入接口。
- `research/non_oracle/stfbs_d1b_qm_audit.py`：启动身份、禁止调用保护、公开对象图与执行回执核验。
- `tests/test_stfbs_d1b_qm1a.py`：12项唯一指定确定性测试。
- `scripts/stfbs_d1b_qm1a_test_entry.py`：受保护子进程入口，安装保护后才加载测试。
- `scripts/stfbs_d1b_qm1a_test_watchdog.py`：冻结策略、唯一尝试登记、调用既有通用 supervise 并核验回执。

启动前固定294项执行源码指纹；执行后全部一致。另外复核350项既有源码、归档及清单，未发现修改。详见 BASELINE、RUN_POLICY、SOURCE_DIFF_MANIFEST、POSTRUN_PRESERVATION。

## 13项最终问题

1. 新 fixture 仅为 `STRUCTURALLY_VALIDATED_UNFUSED_MODEL_FIXTURE`。初始无融合、Q结果或合法服务端点，不声称真实物理状态已验证。
2. `public_profile_at()` 对超出可信公告水位的查询抛出 `PUBLIC_QUERY_REJECTED_AS_FUTURE`，不推进水位、不修改状态。旧快照不会随执行器公告而获得未来信息。
3. 策略输入为独立数据和不可变公开快照。对象图检查拒绝私有 authority、分支、闭包和未批准对象；不同私有未来声明在D60产生相同公开输入。此为规定接口对象图边界，不是针对任意恶意Python反射的安全沙箱。
4. 复用原 ModelRawCache。上下文冲突拒绝时，requests/conflicts增长，缓存内容和new/reuses不被伪造回滚；独立反事实缓存互不污染。
5. fake_fuse 只在登记测试作用域替换 Branch.fuse，退出后恢复保护；全部替身证据标记 `TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE`。
6. 底层估计器、优化器、真实融合、采样、推进、ACTUAL STEP及策略搜索保护持续安装。每项测试前后和替身作用域进出均检查函数身份，未发生保护覆盖。
7. 子进程实际父PID、启动脚本、命令行、创建时间、策略SHA与解释器身份均经入口核验。正式尝试登记为1，无第二次启动。
8. Windows Job实际成员关系通过系统API核验；子进程挂起创建、加入Job后恢复，资源回执含完整进程树CPU，结束时活动进程数0。
9. DETERMINISTIC_TEST_RESULTS保存12个精确test ID与逐项PASS。未进行额外测试发现或扩大测试集。
10. FORBIDDEN_CALL_LEDGER中禁止调用尝试全部0，保护完整。真实WLS、MODEL物理推进、ACTUAL STEP均0。人工端点、缓存包、80/100切口状态均为明确标记的合成数据，不是实际观测或物理执行。
11. 墙钟6.7537174秒，主进程CPU1.171875秒，进程树CPU1.203125秒（含子进程0.03125秒）；限制分别180/120秒。正常退出码0，CPU计量完整，无超时终止。
12. 无未经批准的已有科学源码变更。未执行真实传感器采样、首次融合、WLS、主H1或任何ACTUAL实验。静态准备与归档不计为额外正式测试。
13. 真实Q-only失效、G/Q恢复、服务恢复、任务完成、机器人位移、经济收益和端到端MODEL链路均未验证，仍须1B单独授权。B0/B1是实验预设动作，不是自主决策；B2仅证明公共候选准入拒绝。238次WLS仍只是未来设计估算。

## 核心测试语义

覆盖fixture结构/公开先验/未融合边界；79/80物理声明及公开水位；未来查询拒绝；私有schedule不进入公开可达对象；缓存冲突计数；跨反事实隔离；暂存融合失败的Assignment原子性；两项机器人Assignment变化产生2κ费用；合成80左端点与100切口接口；两机器人替代联盟的公开拒绝。

服务区间与时钟测试采用合成端点及元数据检查，未调用advance_clock或推进任何物理区间，不能据此宣称实际服务连续性成立。

## 资源与证据

唯一命令：`D:\anaconda3\python.exe -B scripts/stfbs_d1b_qm1a_test_watchdog.py --suite interface_v1 --evidence-dir reports/stfbs_lite_d1b_qm1a_001/WATCHDOG_TEST_001`。

RUN_POLICY记录任务、suite、12项白名单、解释器、源码、完整启动参数和护栏；TEST_ATTEMPT在启动前独占登记。LAUNCH_BINDING、WATCHDOG_TEST_001内原始启动/退出/标准流、FORBIDDEN_CALL_LEDGER、TEST_OUTPUT.log和FINAL_SUPERVISION_VERIFICATION保留完整链路。

正式测试无首次失败、修复或重试。执行后仅追加归档，不修改已固定实现和测试。SHA256.json覆盖报告目录内产物（清单自身除外）。

## 停止

本轮完成并停止，等待独立审查。不启动1B、D1-C、DEV/TEST，不改变D1-A结论，不提交或推送Git。
