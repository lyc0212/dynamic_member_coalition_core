# 审计接线

`main → authorize → 一个Budget → frozen_registration → 新目录独占创建 → execute_registered → run_pair`。
来源六份原始文件由已有登记器核验。KEEP/SWITCH 外部上下文在任何 Branch 创建前固定，由主驱动分别持有；不用 Branch 自带的可变上下文替代独立上下文。

每条分支运行后先保存原始结果，直接审计原 Branch，再将同一个只读隔离审计副本交给 verify、service_audit、audit。只有 world.motion 的 ID 映射经过一个边界规范化；verify 仅一处字符串访问改为整数访问，公式未改。类型测试只证明这个映射合同，不宣称所有JSON重载字段或完整物理结果已经验收。

一个必要审计抛错、返回非PASS或预算失败，立即阻止下条分支和收益发布；阶段状态保留FAIL/NOT_RUN。真实运行异常保存部分帧、事件、反馈、历史和成本。最终结果只标 PAIR_AUDITS_PASS_PENDING_G0_G5_REVIEW，不自动签发整个D1-A通过。

默认CLI无任何实验输出；导入与help不执行。未来批准记录必须绑定实际HEAD、逐文件源码SHA、固定H1身份、预算及显式新路径。批准JSON是负责人授权的记录，不是对恶意Python代码的安全沙箱。本轮未创建有效批准记录。
