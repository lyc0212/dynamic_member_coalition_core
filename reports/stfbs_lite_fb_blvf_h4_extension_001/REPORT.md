# BLVF V0.1 H4瞬时转向四格最小验证

PARTIAL_RESULTS

本报告为本次实际计算结果，独立科学验收待完成。

| 动作 | 历史CAP | FB-OFF | FB-ON | 历史HF |
|---|---|---|---|---|

## 结论边界

本次仅H4固定候选动作条件世界。KEEP有真实ON/OFF配对；SWITCH和MEMBER_CHANGE仅有ON，不声称独立反馈增量效应。模型转向只进入模拟物理、观测和离线真值审计，BLVF仍只有五字段输入，控制器仅使用合法belief。保持原一秒传播截断。

服务变化分别按G/GQ区间、连续进度、完成及价值判断，不把Q分类或成本字典变化解释为服务能力改善。共同预测误差按目标—tick去重，完成后不补造预测记录。

HF KEEP来源为ATTEMPT_002已保存RAW及ATTEMPT_003离线验收，保留终端内存及部分历史对象缺失限制。没有重跑HF、H3、NoCap或新世界。端到端加速未建立；未知宿主CPU、写入及计量入口尾部未记零。

{
  "task": "STFBS_LITE_FB_BLVF_H4_EXTENSION_001",
  "git_head": "a8524133c849e9e071693c6a9045af6479df64dc",
  "entry_sha256": "354d416d3e24da6ee661f532db9c8a4aec5643e4c32705bf5c2ecf364c59fe61",
  "blvf_sha256": "204fc231bf78004c33daf151983d751685666da75ed9e9b911abb83854c7365e",
  "status": "PARTIAL_RESULTS",
  "started": 4,
  "valid": 4,
  "analytic_counts": {
    "total": 205,
    "science": 205,
    "direct": 0,
    "historical": 0,
    "synthetic": 0,
    "success": 205,
    "rejected": 0,
    "per_cell": {
      "BLVF_OFF_KEEP": 60,
      "BLVF_ON_KEEP": 33,
      "BLVF_ON_SWITCH": 51,
      "BLVF_ON_MEMBER_CHANGE": 61
    }
  },
  "forbidden_entry_counts": {
    "WLS": 0,
    "SOLVER": 0,
    "R": 0,
    "ASSIGNMENT_OPTIMIZER": 0
  },
  "failure": {
    "type": "RuntimeError",
    "message": "KEEP_PRE_FEEDBACK_OBSERVATION_SERVICE_DIFFERENCE",
    "traceback": "Traceback (most recent call last):\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h4_extension_001\\h4_entry.py\", line 189, in worker\n    a=analyze(ctx,base);audit=base.resource_audit(ctx);protection={p:sha(p)==h for p,h in ctx['protected'].items()};w.json('PROTECTION_CHECK.json',dict(files=protection,unchanged=all(protection.values())));require(all(protection.values()),'HISTORICAL_FILE_CHANGED');w.json('RUNTIME_PROJECT_IMPORTS.json',dict(modules=ctx['guard'].audit(),namespace_paths=ctx['guard'].namespace_paths,lazy_imports='NOT_VERIFIED',task_local_H4_sources='explicit source bindings in EXPERIMENT_CONFIG'))\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h4_extension_001\\h4_entry.py\", line 152, in analyze\n    require(early(off['result'])==early(on['result']) and off['service']['P0']==on['service']['P0'],'KEEP_PRE_FEEDBACK_OBSERVATION_SERVICE_DIFFERENCE')\n    ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\l3_b_stage_a_minimal_remediation_execution_001_20261114121457\\recovery.py\", line 23, in require\n    raise RuntimeError(code)\nRuntimeError: KEEP_PRE_FEEDBACK_OBSERVATION_SERVICE_DIFFERENCE\n"
  },
  "resource_call_audit": null,
  "matrix": null,
  "H4_FEEDBACK_ADAPTATION_FINDINGS": "NOT_IDENTIFIABLE",
  "H4_CONDITIONAL_VALUE_PREDICTION_FINDINGS": "NOT_IDENTIFIABLE",
  "H4_COMPUTATIONAL_SIMPLIFICATION_FINDINGS": "NOT_IDENTIFIABLE",
  "completion": {
    "OFF/KEEP": null,
    "ON/KEEP": 93,
    "ON/SWITCH": 110,
    "ON/MEMBER_CHANGE": null
  },
  "RESOURCE_ACCOUNTING": "INCOMPLETE",
  "RESOURCE_COMPLIANCE": "NOT_ESTABLISHED",
  "END_TO_END_SPEEDUP": "NOT_ESTABLISHED",
  "INDEPENDENT_SCIENTIFIC_ACCEPTANCE": "PENDING",
  "H3_BLVF_INITIAL_VALIDATION": "CLOSED",
  "H4_TARGET_TURN_EXPLORATION": "CLOSED",
  "BLVF_ALGORITHM_VERSION": "V0.1",
  "H5_ARC_EXECUTION_AUTHORIZATION": "NOT_GRANTED",
  "L3_C_EXECUTION_AUTHORIZATION": "NOT_GRANTED",
  "PRODUCTION_ADMISSION": "BLOCKED",
  "PAPER_NOVELTY": "NOT_ESTABLISHED"
}