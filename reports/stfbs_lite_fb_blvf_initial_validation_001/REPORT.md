# STFBS-Lite-FB / BLVF V0.1 首次验证

VALID_SIX_CELL_INITIAL_PROTOTYPE_RESULT

| 动作 | 历史CAP | FB-OFF | FB-ON | 历史HF |
|---|---|---|---|---|
| KEEP | -0.7125094014320741 | -0.712509401432074 | -0.3150141073101529 | -0.3150141073101529 |
| SWITCH | -0.7325026216050797 | -0.7325026216050797 | -0.157503491576509 | -0.157503491576509 |
| MEMBER_CHANGE | -0.7330898517001428 | -0.7330898517001428 | -0.7331120450139224 | -0.7331120450139224 |

| 方法 | 三格MAE | 最优集合 | HF regret（分别报告） |
|---|---|---|---|
| CAP | 0.3241722058214238 | ['KEEP'] | {'KEEP': 0.1575106157336439} |
| OFF | 0.32417220582142375 | ['KEEP'] | {'KEEP': 0.1575106157336439} |
| ON | 0.0 | ['SWITCH'] | {'SWITCH': 0.0} |

## 价值效应、相对价值与服务

{
  "KEEP": {
    "structure_value_effect": 1.1102230246251565e-16,
    "feedback_value_effect": 0.3974952941219211,
    "feedback_accuracy_improvement": 0.3974952941219211,
    "interpretation": "structure is total new predictor effect, not isolated Q causality; feedback is endogenous closed-loop total effect"
  },
  "SWITCH": {
    "structure_value_effect": 0.0,
    "feedback_value_effect": 0.5749991300285707,
    "feedback_accuracy_improvement": 0.5749991300285707,
    "interpretation": "structure is total new predictor effect, not isolated Q causality; feedback is endogenous closed-loop total effect"
  },
  "MEMBER_CHANGE": {
    "structure_value_effect": 0.0,
    "feedback_value_effect": -2.2193313779506063e-05,
    "feedback_accuracy_improvement": 2.2193313779506063e-05,
    "interpretation": "structure is total new predictor effect, not isolated Q causality; feedback is endogenous closed-loop total effect"
  }
}

{
  "CAP": {
    "KEEP-SWITCH": 0.17750383590664953,
    "KEEP-MEMBER_CHANGE": -0.3975174874357007,
    "SWITCH-MEMBER_CHANGE": -0.5750213233423502
  },
  "OFF": {
    "KEEP-SWITCH": 0.17750383590664964,
    "KEEP-MEMBER_CHANGE": -0.3975174874357006,
    "SWITCH-MEMBER_CHANGE": -0.5750213233423502
  },
  "ON": {
    "KEEP-SWITCH": 0.0,
    "KEEP-MEMBER_CHANGE": 0.0,
    "SWITCH-MEMBER_CHANGE": 0.0
  }
}

### KEEP
OFF服务：{"P0": 0.6000000000000001, "Pmax": 1.9500000000000002, "required_duration": 2.25, "M_service": -0.2999999999999998, "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin", "NG": 27, "GQ_valid_intervals": 27, "quality_counts": {"PASS": 49, "FAIL": 11}, "terminal": {"target": 0, "kind": "unfinished", "time": 6.0, "tick": 120, "processed_tick": 120, "release_change_cost": 0.0}, "completion_tick": null, "resets": [{"target": 0, "kind": "reset", "tick": 88, "time": 4.4, "reason": "observation_invalid", "progress_before": 1.9500000000000002}], "natural_release": "original terminal transaction; no optimizer", "positive_cost_ledger": {"completion": 0.0, "flow": 0.03124999999999999, "late": 0.05624999999999998, "effort": 9.40143207405902e-06, "terminal": 0.625, "change": 0.0}}
ON服务：{"P0": 0.6000000000000001, "Pmax": 2.25, "required_duration": 2.25, "M_service": 0.0, "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin", "NG": 33, "GQ_valid_intervals": 33, "quality_counts": {"PASS": 33}, "terminal": {"target": 0, "kind": "completed", "time": 4.65, "tick": 93, "processed_tick": 93, "release_change_cost": 0.0}, "completion_tick": 93, "resets": [], "natural_release": "original terminal transaction; no optimizer", "positive_cost_ledger": {"completion": 0.125, "flow": 0.02562500000000003, "late": 0.039374999999999986, "effort": 1.41073101528698e-05, "terminal": 0.375, "change": 0.0}}
共同有效控制误差：{"common_keys": [{"target": 0, "tick": 60}, {"target": 0, "tick": 61}, {"target": 0, "tick": 62}, {"target": 0, "tick": 63}, {"target": 0, "tick": 64}, {"target": 0, "tick": 65}, {"target": 0, "tick": 66}, {"target": 0, "tick": 67}, {"target": 0, "tick": 68}, {"target": 0, "tick": 69}, {"target": 0, "tick": 70}, {"target": 0, "tick": 71}, {"target": 0, "tick": 72}, {"target": 0, "tick": 73}, {"target": 0, "tick": 74}, {"target": 0, "tick": 75}, {"target": 0, "tick": 76}, {"target": 0, "tick": 77}, {"target": 0, "tick": 78}, {"target": 0, "tick": 79}, {"target": 0, "tick": 80}, {"target": 0, "tick": 81}, {"target": 0, "tick": 82}, {"target": 0, "tick": 83}, {"target": 0, "tick": 84}, {"target": 0, "tick": 85}, {"target": 0, "tick": 86}, {"target": 0, "tick": 87}, {"target": 0, "tick": 88}, {"target": 0, "tick": 89}, {"target": 0, "tick": 90}, {"target": 0, "tick": 91}, {"target": 0, "tick": 92}], "denominator": 33, "OFF_position_error": 0.04727272727272707, "ON_position_error": 0.0, "OFF_velocity_error": 0.14545454545454495, "ON_velocity_error": 0.0, "status": "VALID"}
机制分层：{'actual_control_belief': 'CHANGED', 'actual_control': 'CHANGED', 'robot_trajectory': 'CHANGED', 'endogenous_observation_or_Q': 'CHANGED', 'service': 'CHANGED', 'value': 'CHANGED'}

### SWITCH
OFF服务：{"P0": 0.0, "Pmax": 0.0, "required_duration": 1.05, "M_service": -1.05, "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin", "NG": 0, "GQ_valid_intervals": 0, "quality_counts": {"PASS": 61}, "terminal": {"target": 1, "kind": "unfinished", "time": 6.0, "tick": 120, "processed_tick": 120, "release_change_cost": 0.0}, "completion_tick": null, "resets": [], "natural_release": "original terminal transaction; no optimizer", "positive_cost_ledger": {"completion": 0.0, "flow": 0.03124999999999999, "late": 0.05624999999999998, "effort": 2.6216050797610967e-06, "terminal": 0.625, "change": 0.02}}
ON服务：{"P0": 0.0, "Pmax": 1.05, "required_duration": 1.05, "M_service": 0.0, "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin", "NG": 21, "GQ_valid_intervals": 21, "quality_counts": {"PASS": 51}, "terminal": {"target": 1, "kind": "completed", "time": 5.5, "tick": 110, "processed_tick": 110, "release_change_cost": 0.0}, "completion_tick": 110, "resets": [], "natural_release": "original terminal transaction; no optimizer", "positive_cost_ledger": {"completion": 0.1875, "flow": 0.02812499999999998, "late": 0.046875, "effort": 3.4915765090263393e-06, "terminal": 0.25, "change": 0.02}}
共同有效控制误差：{"common_keys": [{"target": 1, "tick": 60}, {"target": 1, "tick": 61}, {"target": 1, "tick": 62}, {"target": 1, "tick": 63}, {"target": 1, "tick": 64}, {"target": 1, "tick": 65}, {"target": 1, "tick": 66}, {"target": 1, "tick": 67}, {"target": 1, "tick": 68}, {"target": 1, "tick": 69}, {"target": 1, "tick": 70}, {"target": 1, "tick": 71}, {"target": 1, "tick": 72}, {"target": 1, "tick": 73}, {"target": 1, "tick": 74}, {"target": 1, "tick": 75}, {"target": 1, "tick": 76}, {"target": 1, "tick": 77}, {"target": 1, "tick": 78}, {"target": 1, "tick": 79}, {"target": 1, "tick": 80}, {"target": 1, "tick": 81}, {"target": 1, "tick": 82}, {"target": 1, "tick": 83}, {"target": 1, "tick": 84}, {"target": 1, "tick": 85}, {"target": 1, "tick": 86}, {"target": 1, "tick": 87}, {"target": 1, "tick": 88}, {"target": 1, "tick": 89}, {"target": 1, "tick": 90}, {"target": 1, "tick": 91}, {"target": 1, "tick": 92}, {"target": 1, "tick": 93}, {"target": 1, "tick": 94}, {"target": 1, "tick": 95}, {"target": 1, "tick": 96}, {"target": 1, "tick": 97}, {"target": 1, "tick": 98}, {"target": 1, "tick": 99}, {"target": 1, "tick": 100}, {"target": 1, "tick": 101}, {"target": 1, "tick": 102}, {"target": 1, "tick": 103}, {"target": 1, "tick": 104}, {"target": 1, "tick": 105}, {"target": 1, "tick": 106}, {"target": 1, "tick": 107}, {"target": 1, "tick": 108}, {"target": 1, "tick": 109}], "denominator": 50, "OFF_position_error": 0.25, "ON_position_error": 0.1, "OFF_velocity_error": 0.0, "ON_velocity_error": 0.0, "status": "VALID"}
机制分层：{'actual_control_belief': 'CHANGED', 'actual_control': 'CHANGED', 'robot_trajectory': 'CHANGED', 'endogenous_observation_or_Q': 'CHANGED', 'service': 'CHANGED', 'value': 'CHANGED'}

### MEMBER_CHANGE
OFF服务：{"P0": 0.0, "Pmax": 0.0, "required_duration": 2.25, "M_service": -2.25, "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin", "NG": 0, "GQ_valid_intervals": 0, "quality_counts": {"FAIL": 59, "UNKNOWN": 2}, "terminal": {"target": 0, "kind": "unfinished", "time": 6.0, "tick": 120, "processed_tick": 120, "release_change_cost": 0.0}, "completion_tick": null, "resets": [], "natural_release": "original terminal transaction; no optimizer", "positive_cost_ledger": {"completion": 0.0, "flow": 0.03124999999999999, "late": 0.05624999999999998, "effort": 0.0005898517001428377, "terminal": 0.625, "change": 0.02}}
ON服务：{"P0": 0.0, "Pmax": 0.0, "required_duration": 2.25, "M_service": -2.25, "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin", "NG": 0, "GQ_valid_intervals": 0, "quality_counts": {"FAIL": 60, "UNKNOWN": 1}, "terminal": {"target": 0, "kind": "unfinished", "time": 6.0, "tick": 120, "processed_tick": 120, "release_change_cost": 0.0}, "completion_tick": null, "resets": [], "natural_release": "original terminal transaction; no optimizer", "positive_cost_ledger": {"completion": 0.0, "flow": 0.03124999999999999, "late": 0.05624999999999998, "effort": 0.0006120450139223133, "terminal": 0.625, "change": 0.02}}
共同有效控制误差：{"common_keys": [{"target": 0, "tick": 60}, {"target": 0, "tick": 61}, {"target": 0, "tick": 62}, {"target": 0, "tick": 63}, {"target": 0, "tick": 64}, {"target": 0, "tick": 65}, {"target": 0, "tick": 66}, {"target": 0, "tick": 67}, {"target": 0, "tick": 68}, {"target": 0, "tick": 69}, {"target": 0, "tick": 70}, {"target": 0, "tick": 71}, {"target": 0, "tick": 72}, {"target": 0, "tick": 73}, {"target": 0, "tick": 74}, {"target": 0, "tick": 75}, {"target": 0, "tick": 76}, {"target": 0, "tick": 77}, {"target": 0, "tick": 78}, {"target": 0, "tick": 79}, {"target": 0, "tick": 80}, {"target": 0, "tick": 81}, {"target": 0, "tick": 82}, {"target": 0, "tick": 83}, {"target": 0, "tick": 84}, {"target": 0, "tick": 85}, {"target": 0, "tick": 86}, {"target": 0, "tick": 87}, {"target": 0, "tick": 88}, {"target": 0, "tick": 89}, {"target": 0, "tick": 90}, {"target": 0, "tick": 91}, {"target": 0, "tick": 92}, {"target": 0, "tick": 93}, {"target": 0, "tick": 94}, {"target": 0, "tick": 95}, {"target": 0, "tick": 96}, {"target": 0, "tick": 97}, {"target": 0, "tick": 98}, {"target": 0, "tick": 99}, {"target": 0, "tick": 100}, {"target": 0, "tick": 101}, {"target": 0, "tick": 102}, {"target": 0, "tick": 103}, {"target": 0, "tick": 104}, {"target": 0, "tick": 105}, {"target": 0, "tick": 106}, {"target": 0, "tick": 107}, {"target": 0, "tick": 108}, {"target": 0, "tick": 109}, {"target": 0, "tick": 110}, {"target": 0, "tick": 111}, {"target": 0, "tick": 112}, {"target": 0, "tick": 113}, {"target": 0, "tick": 114}, {"target": 0, "tick": 115}, {"target": 0, "tick": 116}, {"target": 0, "tick": 117}, {"target": 0, "tick": 118}, {"target": 0, "tick": 119}], "denominator": 60, "OFF_position_error": 0.25999999999999907, "ON_position_error": 4.159109434027458e-14, "OFF_velocity_error": 0.25999999999999907, "ON_velocity_error": 8.383123529771692e-14, "status": "VALID"}
机制分层：{'actual_control_belief': 'CHANGED', 'actual_control': 'CHANGED', 'robot_trajectory': 'CHANGED', 'endogenous_observation_or_Q': 'CHANGED', 'service': 'CHANGED', 'value': 'CHANGED'}

## 科学问题结论

1. H-A解析替代性：SUPPORTED。历史样本逐项位置差、Q、病态及接受行为见BLVF_COMPATIBILITY_CHECK；合法差异保留，有限样本不能证明全部WLS行为等价。
2. H-B未来反馈：SUPPORTED。ON/OFF唯一主动因素为是否允许新增模拟反馈进入实际self.frozen；OFF在每次advance前强制检查D60控制belief，shadow只用于诊断。配对效应包含观测、质量及轨迹的自然下游变化，不是单次反馈净直接效应。
3. H-C完整预测器：SUPPORTED。按三动作价值误差、相对价值、排序与HF regret共同判断，不以KEEP完成或总体MAE单独判断。
4. SWITCH先验纠正：实际估计/控制belief及服务记录见TRACE，反馈价值及精度效应={'structure_value_effect': 0.0, 'feedback_value_effect': 0.5749991300285707, 'feedback_accuracy_improvement': 0.5749991300285707, 'interpretation': 'structure is total new predictor effect, not isolated Q causality; feedback is endogenous closed-loop total effect'}。KEEP—SWITCH相对价值误差见上表，未省略SWITCH低估或失败。
5. MEMBER_CHANGE的继承损失、几何及可能病态：原initial assign与服务规则保持不变，初始P0、Q及拒绝、重置、完成/失败均保存，不为改善分数新增部分服务奖励。
6. 状态、服务、价值、决策不等价：逐动作同时报告共同目标tick误差、Pmax及阈值裕度、价值分项、排序与regret；零服务裕度仅说明达到被截停的完成阈值，不说明额外安全余量。
7. 计算成本：解析调用及其成功/拒绝、无足够传感器而跳过的帧独立计数。实际非线性入口计数见资源审计。单元核心计时包含初始化、事务、每次解析记录及监测开销，完整单元计时另含审计与RAW/TRACE写入；与历史HF窗口口径不同，END_TO_END_SPEEDUP=NOT_ESTABLISHED，不重跑HF追求加速比。
8. 后续H4：只根据本次有限H3证据判断是否值得另行验证。若H-B/H-C得到支持，可考虑在单独授权后检验运动模型失配；本次不启动H4、H2或L3-C。

## 接口、资源及限制

解析定位只接收sensor_ids、positions、bearings、sigmas、domain。机器精度级叉积阈值仅保障可计算性，原Jacobian病态比1e-4和Q半径0.06保持不变。非法交点不裁剪、不回退WLS。optimizer_converged仅为兼容成功标志，starts为空，没有伪造求解过程。

解析成功、belief接受、服务Q PASS是不同判断；直接检查已贯通同一解析结果、真实BridgeFrameProcessor、原质量接口和MODEL consumer，覆盖Q FAIL但belief合法接受与五tick速度差分。

历史HF含R和Assignment优化调用，本次固定候选动作保持实际有效团队；只核对历史同动作边界及原科学规则，不宣称完整程序严格等价。结构效应不单独归因于Q。

{
  "TASK": "STFBS_LITE_FB_BLVF_INITIAL_VALIDATION_001",
  "git_head": "496abe824544e3602cda6136bdfc630bacdea629",
  "entry_sha256": "75226d448a454d8b6f711b52f7395ce844d03258dcdf4747e1d935c20b599117",
  "analytic_source_sha256": "204fc231bf78004c33daf151983d751685666da75ed9e9b911abb83854c7365e",
  "EXECUTION_STATUS": "VALID_SIX_CELL_INITIAL_PROTOTYPE_RESULT",
  "BLVF_IMPLEMENTATION_STATUS": "IMPLEMENTED_TASK_LOCAL",
  "HISTORICAL_COMPATIBILITY_CHECK_STATUS": "COMPLETED_WITH_FINITE_SAMPLE_LIMITS",
  "NON_ORACLE_INFORMATION_ISOLATION": "VERIFIED_PUBLIC_FIVE_FIELD_ESTIMATOR_AND_BELIEF_ONLY_CONTROL_PATH",
  "ON_OFF_TREATMENT_VALIDITY": "VERIFIED",
  "HISTORICAL_HF_COMPARABILITY": "CONDITIONALLY_COMPARABLE_WITH_LIMITATIONS",
  "STARTED_PROXY_CELLS": 6,
  "VALID_PROXY_CELLS": 6,
  "VALID_FB_OFF_CELLS": 3,
  "VALID_FB_ON_CELLS": 3,
  "ANALYTIC_ESTIMATE_CALLS": 336,
  "SCIENCE_ANALYTIC_CALLS": 327,
  "DIRECT_CHECK_ANALYTIC_CALLS": 9,
  "analytic_counts": {
    "total": 336,
    "science": 327,
    "direct": 9,
    "historical": 5,
    "synthetic": 4,
    "success": 334,
    "rejected": 2,
    "per_cell": {
      "BLVF_OFF_KEEP": 60,
      "BLVF_ON_KEEP": 33,
      "BLVF_OFF_SWITCH": 61,
      "BLVF_ON_SWITCH": 51,
      "BLVF_OFF_MEMBER_CHANGE": 61,
      "BLVF_ON_MEMBER_CHANGE": 61
    }
  },
  "NONLINEAR_WLS_CALLS": 0,
  "NONLINEAR_SOLVER_STARTS": 0,
  "R_CALLS": 0,
  "ASSIGNMENT_OPTIMIZATION_CALLS": 0,
  "ACTUAL_STEP_CALLS": 0,
  "ACTUAL_WLS_CALLS": 0,
  "H_A_FINDINGS": "SUPPORTED",
  "H_B_FINDINGS": "SUPPORTED",
  "H_C_FINDINGS": "SUPPORTED",
  "SWITCH_VALUE_PREDICTION_FINDINGS": {
    "structure_value_effect": 0.0,
    "feedback_value_effect": 0.5749991300285707,
    "feedback_accuracy_improvement": 0.5749991300285707,
    "interpretation": "structure is total new predictor effect, not isolated Q causality; feedback is endogenous closed-loop total effect"
  },
  "COMPLETION_PREDICTION_FINDINGS": {
    "KEEP": {
      "OFF": null,
      "ON": 93
    },
    "SWITCH": {
      "OFF": null,
      "ON": 110
    },
    "MEMBER_CHANGE": {
      "OFF": null,
      "ON": null
    }
  },
  "RELATIVE_ACTION_VALUE_FINDINGS": {
    "CAP": {
      "KEEP-SWITCH": 0.17750383590664953,
      "KEEP-MEMBER_CHANGE": -0.3975174874357007,
      "SWITCH-MEMBER_CHANGE": -0.5750213233423502
    },
    "OFF": {
      "KEEP-SWITCH": 0.17750383590664964,
      "KEEP-MEMBER_CHANGE": -0.3975174874357006,
      "SWITCH-MEMBER_CHANGE": -0.5750213233423502
    },
    "ON": {
      "KEEP-SWITCH": 0.0,
      "KEEP-MEMBER_CHANGE": 0.0,
      "SWITCH-MEMBER_CHANGE": 0.0
    }
  },
  "resource_call_audit": {
    "status": "PASS",
    "starts": 336,
    "closed": 336,
    "counts": {
      "total": 336,
      "science": 327,
      "direct": 9,
      "historical": 5,
      "synthetic": 4,
      "success": 334,
      "rejected": 2,
      "per_cell": {
        "BLVF_OFF_KEEP": 60,
        "BLVF_ON_KEEP": 33,
        "BLVF_OFF_SWITCH": 61,
        "BLVF_ON_SWITCH": 51,
        "BLVF_OFF_MEMBER_CHANGE": 61,
        "BLVF_ON_MEMBER_CHANGE": 61
      }
    },
    "forbidden_entry_counts": {
      "WLS": 0,
      "SOLVER": 0,
      "R": 0,
      "ASSIGNMENT_OPTIMIZER": 0
    }
  },
  "RESOURCE_ACCOUNTING": "INCOMPLETE",
  "RESOURCE_COMPLIANCE": "NOT_ESTABLISHED",
  "END_TO_END_SPEEDUP": "NOT_ESTABLISHED",
  "SCIENTIFIC_VALIDITY": "VALID_SIX_CELL_INITIAL_PROTOTYPE_RESULT",
  "INDEPENDENT_ACCEPTANCE": "PENDING",
  "PAPER_NOVELTY": "NOT_ESTABLISHED",
  "L3_B_EXPLORATORY_STAGE": "CLOSED",
  "L3_B_FORMAL_STATUS": "L3_B_BLOCKED",
  "H4_TARGET_TURN_EXPLORATION": "CLOSED",
  "L3_C_EXECUTION_AUTHORIZATION": "NOT_GRANTED",
  "PRODUCTION_ADMISSION": "BLOCKED",
  "failure": null,
  "H_A_interpretation": "classification only for checked samples; 1e-8 position comparison is reporting precision, not an estimator acceptance threshold; not universal WLS-equivalence",
  "INSUFFICIENT_SENSOR_FRAMES_IN_VALID_CELLS": 0
}

资源会计INCOMPLETE；宿主准备及入口尾部未知不记零，不宣称整体资源合规。最终退出回执见RESOURCE_RECEIPT.json。结果仅属于一个指定H3条件世界，不证明真实噪声传感器性能、跨世界鲁棒优势或定位理论创新。完成后停止。