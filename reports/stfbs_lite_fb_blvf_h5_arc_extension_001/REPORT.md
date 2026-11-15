# H5-ARC BLVF V0.1 七格科学结果

BLOCKED_NO_ACCEPTED_CELLS

本报告是执行及机制证据汇总，独立科学验收待完成。

| 动作 | HF | FB-ON | FB-OFF |
|---|---|---|---|
| KEEP | STARTED_FAILED_OR_NOT_ACCEPTED | NOT_STARTED | NOT_STARTED |
| SWITCH | NOT_STARTED | NOT_STARTED | NOT_RUN |
| MEMBER_CHANGE | NOT_STARTED | NOT_STARTED | NOT_RUN |

## H5-A：实际区间平均速度与瞬时速度

{
  "HF": {
    "status": "NOT_IDENTIFIABLE"
  },
  "ON": {
    "status": "NOT_IDENTIFIABLE"
  }
}

## H5-B：KEEP反馈条件闭环总效应

{
  "FEEDBACK_EFFECT_IDENTIFIED": "NOT_IDENTIFIABLE"
}

## H5-C：价值及排序

{
  "errors": {},
  "MAE": null,
  "relative_errors": {
    "KEEP-SWITCH": null,
    "KEEP-MEMBER_CHANGE": null,
    "SWITCH-MEMBER_CHANGE": null
  },
  "rankings": {
    "HF": {
      "status": "NOT_IDENTIFIABLE",
      "available": []
    },
    "ON": {
      "status": "NOT_IDENTIFIABLE",
      "available": []
    },
    "OFF": {
      "status": "NOT_IDENTIFIABLE",
      "available": []
    }
  },
  "HF_regret": null
}

## 服务和经济账本

{}

## 计算计数及本次单对耗时

{
  "resource_audit": {
    "status": "PASS",
    "started": 1,
    "closed": 1,
    "counts": {
      "WLS": 1,
      "SOLVER": 0,
      "ANALYTIC": 0
    },
    "failed_internal_calls": 1,
    "per_cell": {
      "H5_HF_KEEP": {
        "WLS": 1,
        "SOLVER": 0,
        "ANALYTIC": 0
      }
    },
    "forbidden": {
      "R": 0,
      "ASSIGNMENT_OPTIMIZER": 0,
      "UNROUTED_ESTIMATE": 0
    },
    "direct_estimator_calls": 0
  },
  "timing": {}
}

## 解释及限制

本次H5轨迹是指定条件世界，不是公开信息驱动的未来情景生成。瞬时速度与真实历史平均速度分别记录；超过原一秒截断的记录不套用未截断分解。D100终端belief不等于仍在发挥控制作用。

HF和ON使用相同原consumer及固定动作事务，估计方法不同，D80之前允许合法估计、Q及服务差异。仅KEEP ON/OFF受主动反馈等同性约束。反馈效应是位置、速度、时间锚点及后续观测服务共同改变的总效应，不只归因于一次速度更新。

若HF和BLVF共同未完成而价值一致，应区分原控制能力限制和价值预测成功。真实噪声、跨世界鲁棒决策、论文创新性及一般端到端效率未建立。单次配对计时只描述本次执行，方法专属准备单列，未重复性能实验。

资源会计INCOMPLETE；宿主准备及尾部未知不记零。原科学RAW、TRACE、方法对象、调用日志和保护记录均保存。完成后停止，不追加世界或自动改算法。

{
  "task": "STFBS_LITE_FB_BLVF_H5_ARC_EXTENSION_001",
  "git_head": "d1c062f34f69b93f26827a1972a21b7916da4e5f",
  "status": "BLOCKED_NO_ACCEPTED_CELLS",
  "started": 1,
  "valid": 0,
  "world_digest": "6d23db4be70d86ad95c95de8cb4022de9a3617c38e7f7a4f2c085b56b488bf5f",
  "counts": {
    "WLS": 1,
    "SOLVER": 0,
    "ANALYTIC": 0
  },
  "starts_by_method": {
    "HF": 1,
    "BLVF": 0
  },
  "failure": {
    "type": "TypeError",
    "message": "Calls.invoke() got multiple values for argument 'method'",
    "traceback": "Traceback (most recent call last):\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h5_arc_extension_001\\h5_entry.py\", line 221, in worker\n    for method,action in MATRIX:run_cell(ctx,method,action)\n                                ~~~~~~~~^^^^^^^^^^^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h5_arc_extension_001\\h5_entry.py\", line 126, in run_cell\n    branch=ctx['Branch'](view,seed,world,name,budget,method!='OFF');r=branch.fixed_run(actions);core_t=dict(wall=time.monotonic()-core,cpu=time.process_time()-core_cpu)\n                                                                      ~~~~~~~~~~~~~~~~^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_initial_validation_001\\fb_entry_attempt_002.py\", line 78, in fixed_run\n    self.advance()\n    ~~~~~~~~~~~~^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\ATTEMPT_003\\model_h4.py\", line 262, in advance\n    right = self.fuse(j, s, self.tick)\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\ATTEMPT_003\\model_h4.py\", line 132, in fuse\n    result = self.streams[stream].process(frame)\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\l3_b_diagnostic_recovery_001_stage_a_20261114\\historical\\research\\information_service_bridge\\public_stream.py\", line 80, in process\n    estimate_result = self.estimator_fn(work)\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h5_arc_extension_001\\h5_entry.py\", line 46, in <lambda>\n    return lambda payload:self.ctx['calls'].invoke(resource,self.method,self.name,self.estimate,payload)\n                          ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h5_arc_extension_001\\h5_entry.py\", line 26, in invoke\n    try:out=fn(*args,**kw)\n            ~~^^^^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\l3_b_diagnostic_recovery_001_stage_a_20261114\\historical\\research\\cooperative_sensing\\estimator.py\", line 71, in estimate\n    r=least_squares(fun,start,jac=jac,bounds=data['domain'],method='trf',tr_solver='exact',\n        loss='linear',x_scale=1.,ftol=1e-10,xtol=1e-10,gtol=1e-10,max_nfev=300,verbose=0)\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h5_arc_extension_001\\h5_entry.py\", line 47, in solver\n    def solver(self,*args,**kw):return self.ctx['calls'].invoke('SOLVER',self.method,self.name,self.original_solver,*args,**kw)\n                                       ~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\nTypeError: Calls.invoke() got multiple values for argument 'method'\n"
  },
  "resource_audit": {
    "status": "PASS",
    "started": 1,
    "closed": 1,
    "counts": {
      "WLS": 1,
      "SOLVER": 0,
      "ANALYTIC": 0
    },
    "failed_internal_calls": 1,
    "per_cell": {
      "H5_HF_KEEP": {
        "WLS": 1,
        "SOLVER": 0,
        "ANALYTIC": 0
      }
    },
    "forbidden": {
      "R": 0,
      "ASSIGNMENT_OPTIMIZER": 0,
      "UNROUTED_ESTIMATE": 0
    },
    "direct_estimator_calls": 0
  },
  "MAE": null,
  "rankings": {
    "HF": {
      "status": "NOT_IDENTIFIABLE",
      "available": []
    },
    "ON": {
      "status": "NOT_IDENTIFIABLE",
      "available": []
    },
    "OFF": {
      "status": "NOT_IDENTIFIABLE",
      "available": []
    }
  },
  "HF_regret": null,
  "H5_A_MOTION_ESTIMATION_FINDINGS": {
    "HF": {
      "status": "NOT_IDENTIFIABLE"
    },
    "ON": {
      "status": "NOT_IDENTIFIABLE"
    }
  },
  "H5_B_FEEDBACK_SERVICE_FINDINGS": {
    "FEEDBACK_EFFECT_IDENTIFIED": "NOT_IDENTIFIABLE"
  },
  "H5_C_CONDITIONAL_VALUE_FINDINGS": "PARTIAL_OR_NOT_IDENTIFIABLE",
  "H5_COMPUTATIONAL_SIMPLIFICATION_FINDINGS": {
    "WLS": 1,
    "SOLVER": 0,
    "ANALYTIC": 0
  },
  "entry_sha256": "bb7f1715c100896b0ce429f9c6413eb714d41a620de2af568af7e3bf58e2255d",
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