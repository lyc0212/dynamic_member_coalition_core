# 未来H1复验接口依赖（仅静态登记）

现有scripts/stfbs_d1a_run.py在每支执行后调用audit(result,view)和service_audit(result,view)，没有完整接入独立G3审计及verify(result,view,seed,audit_context=...)。本轮未修改该脚本。

未来获得明确授权后，应在任何Branch构造之前，由外层用已核对的原D60文件、恢复历史和既有来源pins建立外部登记。KEEP与SWITCH共享同一public/seed/prefix摘要，分别固定expected_branch_id。保留外部上下文，不从结果、Branch._audit_context或修改后的历史重建。

在Assignment边界和完整物理结算切口运行严格G3检查；中间任务终止保持局部检查。每支结束前调用audit_branch_independent(branch,context=外层登记)，再调用verify(result,view,seed,audit_context=同一登记)。它们与独立物理控制/服务检查、经济六项账本、belief消费重放共同构成验收，任何缺失都不能只由主脚本成功退出代替。

未来使用用户明确授权的新输出目录，禁止覆盖stfbs_lite_d1a_001及两组修复归档。保持原H1和计划摘要、D80/D100 policy.decide R、原预算及零ACTUAL限制。不以当前纯状态测试代替新MODEL整体验证。本文件不授权创建目录或执行复验。
