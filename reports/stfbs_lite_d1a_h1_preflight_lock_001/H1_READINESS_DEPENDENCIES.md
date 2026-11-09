# 后续授权边界

本轮有限补强完成，不另起准备性研究阶段。本工作树尚未提交，因此真实source/worktree预检现在应拒绝，这是正确保护，不是新的科学阻断。

独立审查后，如负责人正式批准一次原H1复验，应固定包含本轮修改的实际执行版本，确认必需科学源码已受版本管理且无未批准修改/未跟踪可执行代码。源目录中现存未跟踪/忽略的.pyc/.pyd等也会拒绝，不会自动清理。外部批准文件保留原experiment/status/authorized_by/head/output_dir/limits，并登记完整45项及必要额外源码的source_pins、与输出同级的新watchdog_evidence_dir=<output>_watchdog。当前SCIENCE_DEPENDENCY_PINS仅是待审查快照，不是批准记录。

未来只经watchdog CLI显式执行：--execute-frozen-h1 --approval-manifest <外部批准> --output-dir <独立新目录> --evidence-dir <同级新目录_watchdog>。本轮没有创建有效批准记录，也没有调用这条正式命令。脚本主入口直接执行无法提供合法父进程绑定，因此不能绕过外部墙钟。

D60/世界/计划、D80/D100 R、外部上下文、原Branch独立G3与verify/service/audit、共享Budget和失败阻断保持原实现。实际D60—D120完整联合物理、belief、服务、生命周期与经济正确性仍须一次获授权的MODEL复验；原三组正差额不升级为有效结果。未来G0—G5沿用已归档协议，G5追加使用本次外部计量证据的必要性，不改变科学阈值。此次准备不代表ACTUAL收益或算法有效性。
