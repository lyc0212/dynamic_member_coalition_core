# H5-ARC BLVF V0.1 七格科学结果

PARTIAL_RESULTS

本报告是执行及机制证据汇总，独立科学验收待完成。

| 动作 | HF | FB-ON | FB-OFF |
|---|---|---|---|

## 解释及限制

本次H5轨迹是指定条件世界，不是公开信息驱动的未来情景生成。瞬时速度与真实历史平均速度分别记录；超过原一秒截断的记录不套用未截断分解。D100终端belief不等于仍在发挥控制作用。

HF和ON使用相同原consumer及固定动作事务，估计方法不同，D80之前允许合法估计、Q及服务差异。仅KEEP ON/OFF受主动反馈等同性约束。反馈效应是位置、速度、时间锚点及后续观测服务共同改变的总效应，不只归因于一次速度更新。

若HF和BLVF共同未完成而价值一致，应区分原控制能力限制和价值预测成功。真实噪声、跨世界鲁棒决策、论文创新性及一般端到端效率未建立。单次配对计时只描述本次执行，方法专属准备单列，未重复性能实验。

资源会计INCOMPLETE；宿主准备及尾部未知不记零。原科学RAW、TRACE、方法对象、调用日志和保护记录均保存。完成后停止，不追加世界或自动改算法。

{
  "task": "STFBS_LITE_FB_BLVF_H5_ARC_EXTENSION_001",
  "attempt_id": "ATTEMPT_002",
  "git_head": "5c7e8e5a0c44a5f7f161cc601797937229ce9053",
  "status": "PARTIAL_RESULTS",
  "started": 7,
  "valid": 7,
  "world_digest": "6d23db4be70d86ad95c95de8cb4022de9a3617c38e7f7a4f2c085b56b488bf5f",
  "counts": {
    "WLS": 145,
    "SOLVER": 1305,
    "ANALYTIC": 205
  },
  "starts_by_method": {
    "HF": 3,
    "BLVF": 4
  },
  "failure": {
    "type": "TypeError",
    "message": "can only concatenate str (not \"int\") to str",
    "traceback": "Traceback (most recent call last):\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h5_arc_extension_001\\ATTEMPT_002\\h5_entry.py\", line 226, in worker\n    analysis=analyze(ctx);audit=resource_audit(ctx);checks={p:sha(p)==h for p,h in ctx['protected'].items()};require(all(checks.values()),'HISTORICAL_PROTECTION');w.json('PROTECTION_CHECK.json',checks);w.json('RUNTIME_BINDINGS_FINAL.json',dict(modules=ctx['guard'].audit(),namespace_paths=ctx['guard'].namespace_paths,actual_HF_estimator_code_ids=sorted(ctx['hf_code_ids']),HF_source=str(HIST/'historical/research/cooperative_sensing/estimator.py'),untriggered_lazy_imports='NOT_VERIFIED'))\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h5_arc_extension_001\\ATTEMPT_002\\h5_entry.py\", line 182, in analyze\n    require(not ident['diffs']([f for f in off['raw']['frames'] if f['tick']<=80],[f for f in on['raw']['frames'] if f['tick']<=80]),'KEEP_EARLY_PHYSICAL_DIFFERENCE');require(off['trace']['initial_service']==on['trace']['initial_service'],'KEEP_INITIAL_SERVICE_DIFFERENCE')\n                ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h4_extension_001\\offline_finalize.py\", line 34, in diffs\n    return [r for i,(x,y) in enumerate(zip(a,b)) for r in diffs(x,y,p+'/'+str(i))]\n                                                          ~~~~~^^^^^^^^^^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h4_extension_001\\offline_finalize.py\", line 30, in diffs\n    else:out.extend(diffs(a[k],b[k],p+'/'+k))\n                    ~~~~~^^^^^^^^^^^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h4_extension_001\\offline_finalize.py\", line 30, in diffs\n    else:out.extend(diffs(a[k],b[k],p+'/'+k))\n                                    ~~~~~^~\nTypeError: can only concatenate str (not \"int\") to str\n"
  },
  "resource_audit": null,
  "MAE": null,
  "rankings": null,
  "HF_regret": null,
  "H5_A_MOTION_ESTIMATION_FINDINGS": "NOT_IDENTIFIABLE",
  "H5_B_FEEDBACK_SERVICE_FINDINGS": "NOT_IDENTIFIABLE",
  "H5_C_CONDITIONAL_VALUE_FINDINGS": "NOT_IDENTIFIABLE",
  "H5_COMPUTATIONAL_SIMPLIFICATION_FINDINGS": "NOT_IDENTIFIABLE",
  "entry_sha256": "2adf086deaf2562e743b5e568522d836efdc95bd3c08e663b1a984bf0e63fa37",
  "motion_sha256": "ef05b290837b60761ccd209c03d6b2af07a2c7648e1af017044aa2ac63fb82bd",
  "blvf_sha256": "204fc231bf78004c33daf151983d751685666da75ed9e9b911abb83854c7365e",
  "RESOURCE_ACCOUNTING": "INCOMPLETE",
  "RESOURCE_COMPLIANCE": "NOT_ESTABLISHED",
  "END_TO_END_SPEEDUP": "NOT_ESTABLISHED",
  "INDEPENDENT_SCIENTIFIC_ACCEPTANCE": "PENDING",
  "PAPER_NOVELTY": "NOT_ESTABLISHED",
  "PRODUCTION_ADMISSION": "BLOCKED",
  "L3_C_EXECUTION_AUTHORIZATION": "NOT_GRANTED",
  "H3_BLVF_INITIAL_VALIDATION": "CLOSED",
  "H4_BLVF_EXTENSION": "CLOSED",
  "BLVF_ALGORITHM_VERSION": "V0.1"
}