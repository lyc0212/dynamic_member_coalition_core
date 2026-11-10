# B3 重复预算绑定最小修复：工程验收报告

最终状态：`B3_MINIMAL_PATCH_READY_FOR_INDEPENDENT_REVIEW`。

## A. 基准与边界

实施HEAD：`d0b164b54048b6a15d45c3f8fadfad4e690ed9c7`，实施前工作树干净。原正式执行冻结HEAD为89f7c091c2bb203ec933c96af70eaf51d69f658e。原批次D1B_QM1B_RUN_G1_20261110_001、尝试A01已消耗，原始完整实验永久保留BLOCKED。

本轮仅修改一个业务文件，新增一个四组测试模块、独立测试入口和watchdog。未启动RUN-G1；未操作批准票据、用户控制记录及授权根；没有Git提交或推送。

## B. 精确业务补丁

文件：research/non_oracle/stfbs_d1b_qm_run_release.py。

```diff
-    from .stfbs_d1b_qm_execution import prepare_branch,bind_shared_budget
+    from .stfbs_d1b_qm_execution import prepare_branch
-    bind_shared_budget(branch,budget)  # Recheck the untouched pre-sampling takeover window.
```

修改前SHA256：`bce3ca0b99ade4543bcc6bc7c84e3bcb6d81ef836041df36beca9346265e9c3e`。
修改后SHA256：`79c626836cb11c574170ed1b7b2faab1179d015ed33cc82028acbb00f132799e`。

PATCH_DIFF.diff保存实际差异。静态预检以规范化换行的原始Git内容重建精确补丁，并作AST结构比较。prepare_branch首次绑定、bind_shared_budget所有拒绝条件、来源校验、MissingSensorAuthority、科学公式和参数均保持原样。

## C. A1：真实生产B3准备路径

T1_EVIDENCE.json记录受保护进程中的实际Python调用链：
prepare_b3_branch（release.py:172）→ verify_verified_registration（run_audit.py:263）→ verify_source_pins（:243）→ prepare_branch（execution.py:80）→ bind_shared_budget（:22）。

未用mock替代这些函数。通过真实D1BBudget.estimator接口先产生一次带TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE标签的合成调用，STARTED/RETURNED闭合、共享计数为1。B3创建前后预算快照相等，预算对象相同，首次绑定恰好一次，创建不增加调用。

返回分支tick60、未分配、未融合、未推进，缓存、反馈、streams、pending、模型测量、服务段、边界均为空。MissingSensorAuthority已配置；79时刻U1可用，80时刻missing；初始公开水位60禁止查询未来80，纯声明发布80后可见missing；MISSING slot无packet。这些均为结构性检查，没有采样。

## D. A2：启动前冻结

保留旧正式票据和冻结清单。SOURCE_PINS_V2.json为本轮独立工程清单，包含524项源码指纹（原521项中更新唯一业务文件，并新增三个工程执行文件）及29项运行时指纹。

来源映射规范化摘要：`aa1feac3f0bbc8895edbb92b0034464dcf49f50f7ea9cb54d94730d32babd54f`。
规范：UTF-8 JSON，sort_keys=True，separators=(',',':')，allow_nan=False；摘要对象是source_pins映射。

冻结先于正式启动。父进程静态预检使用该清单；RUN_POLICY.json绑定同一映射，SHA256由启动命令传入子进程。子进程先验证政策摘要、实际源码、解释器、运行时、父子PID/命令和Windows Job，再安装保护、加载测试。真实注册与verify_source_pins读取冻结映射并核对实际字节，未用现场重新计算值作为预期值。执行后524/29项再次一致。

## E. 四组测试及补充A1/A2/T2核对

四个固定ID，各一次，无SKIP/FAIL/ERROR：
- test_T1_real_b3_used_budget：PASS，证明见C。
- test_T2_polluted_branch_rejected：PASS，12子案例：tick、cache_rows、cache_requests、feedback、pending、assignment、segments、streams、boundaries、model_measurements、fusions、local_budget。
- test_T3_repeat_takeover_rejected：PASS，合法绑定到已有历史共享预算的B3再次接管，仍抛出原Unsafe late budget takeover。
- test_T4_static_and_guards：PASS，静态绑定、B3→F1→F2→F3A→F3B→final_science顺序、专项来源与预算类别、其他源码未变、保护完整。

T2本地预算污染使用独立D1BBudget和带标签合成估计器，经合法分支/frame/类别上下文产生完整记账后设为测试分支当前预算；未调用生产本地Budget.estimator。其他污染结构使用同schema历史结构或明确合成状态，不运行状态机。所有拒绝均匹配原ValueError文本，原预算身份、目标共享账本和状态不变。T2验证污染时首次接管拒绝；T3验证已绑定时再次接管拒绝，两者独立。

工程测试合计四次合成外层历史调用（T1、T2_shared、T2_local、T3），全部闭合。不是四次真实WLS。

## F. 保护与资源

仅一次正式watchdog启动。既有Windows Job supervise创建挂起子进程、入Job后恢复；子进程实际核查Job成员关系和父进程身份。51项保护入口、12次完整性检查均通过；安装发生在测试模块加载之前，覆盖估计器及别名、least_squares及别名、融合、Assignment、MODEL推进、raw采样、ACTUAL step和正式入口。没有恢复或绕过保护。

进程树CPU：7.390625秒（上限120）；wall：9.022783099997469秒（上限180）；退出码0；CPU计量完整；结束活动进程0；正式尝试1；自动重试0。

禁止调用尝试0。已保护可达调用范围内，真实WLS、least_squares、融合、MODEL推进、ACTUAL STEP均为0。保护证据不代表对任意恶意进程或未列入调用图代码的全域安全声明。

FINAL_TEST_AUDIT.json以只读文件/摘要/调用记录核验15项条件全部成立；未重放测试。最终资源验收直接受退出状态、数值上限、Job清理、账本、源码一致性约束。

## G. 首次失败与历史保护

正式启动前静态预检一次因辅助程序CRLF/LF匹配错误报EXACT_PATCH_MISMATCH；不是业务补丁错误，也未执行测试。PRESTART_FAILURE_001.json保留原因，SOURCE_PINS.json保留当时冻结。仅修正新增辅助程序的换行规范化后，以SOURCE_PINS_V2.json重新冻结；STATIC_PREFLIGHT.json通过后才登记唯一正式尝试。

正式测试启动后没有修改源码或重跑。原25项运行归档及登记的用户控制记录、预留标记、旧票据摘要全部不变；原授权根固定路径仍不存在。原实验BLOCKED、181次外层WLS、1629次底层启动及部分科学结果不变。

## H. 裁定与限制

B3_MINIMAL_PATCH_READY_FOR_INDEPENDENT_REVIEW。

本轮只证明B3结构性准备路径可接入已有历史共享预算，且原不安全接管拒绝仍有效；不证明B3物理调度成功，不证明F1/F2/F3真实科学验证通过，不修改原实验BLOCKED结论，也不授权任何新RUN-G1。

本轮完成后停止，等待独立验收。没有创建新科学批次或批准票据。
