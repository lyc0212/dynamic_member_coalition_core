# H5-ARC ATTEMPT_002最小离线汇总恢复

OFFLINE_FINALIZATION_STATUS = PASS
SCIENTIFIC_RESULT_STATUS = READY_FOR_INDEPENDENT_ACCEPTANCE
INDEPENDENT_SCIENTIFIC_ACCEPTANCE = PENDING

原科学提交：7558e2aaa2286e3c4e65d81c21948820fd4de4c4。原PARTIAL_RESULTS及失败堆栈保持不变。本次只用Python标准库核验保存数据，不导入项目模块，不执行consumer、估计器、运动推进或测试。

七格完整结果及原单元内审计PASS得到保存证据核对。KEEP早期20对观测及20对物理帧科学内容一致；300处差异仅为明确身份字段及派生摘要。

| 动作 | HF | FB-ON | FB-OFF |
|---|---|---|---|
| KEEP | -0.31501410413014613 | -0.31501410413014613 | -0.712509401432074 |
| SWITCH | -0.157503491576509 | -0.157503491576509 | NOT_RUN |
| MEMBER_CHANGE | -0.7331125696046304 | -0.7331125696046304 | NOT_RUN |

## H5-A：区间平均速度、瞬时速度及传播失配

{
  "HF": {
    "status": "IDENTIFIABLE",
    "actual_event": {
      "freeze_tick": 80,
      "freeze_ordinal": 19,
      "target": 0,
      "frame_id": "H5_HF_KEEP:T0:first61:tick80",
      "measurement_tick": 80,
      "available_tick": 80,
      "consumed_tick": 80,
      "accepted": true,
      "rejection_reasons": [],
      "Q": "PASS",
      "reference_tick": 75,
      "reference_interval": 5,
      "estimator_method": null,
      "observation_origin": "MODEL",
      "provenance": "SIMULATED",
      "accepted_evidence": "actual appended consumer position history; original rule checked without extra freeze",
      "reference_position": [
        9.499999999999998,
        10.0
      ],
      "accepted_position": [
        9.598961583701808,
        10.012435031315743
      ],
      "unclipped_difference_velocity": [
        0.3958463348072385,
        0.049740125262971446
      ],
      "actual_estimator": "NINE_START_WLS"
    },
    "actual_control_belief": {
      "available_tick": 80,
      "diagnostics": {
        "starts": [
          {
            "start_id": 0,
            "start": [
              4.0,
              4.0
            ],
            "accepted": true,
            "guard": null,
            "status": 1,
            "success": true,
            "optimality": 1.3323132785976551e-11,
            "nfev": 11,
            "njev": 10,
            "active_mask": [
              0,
              0
            ],
            "cost": 2.465190328815662e-28,
            "Q": 4.930380657631324e-28,
            "x": [
              9.598961583701808,
              10.012435031315743
            ],
            "evaluation_calls": {
              "fun": 11,
              "jac": 10
            }
          },
          {
            "start_id": 1,
            "start": [
              4.0,
              10.0
            ],
            "accepted": true,
            "guard": null,
            "status": 1,
            "success": true,
            "optimality": 1.3323132785976551e-11,
            "nfev": 14,
            "njev": 10,
            "active_mask": [
              0,
              0
            ],
            "cost": 2.465190328815662e-28,
            "Q": 4.930380657631324e-28,
            "x": [
              9.598961583701808,
              10.012435031315743
            ],
            "evaluation_calls": {
              "fun": 14,
              "jac": 10
            }
          },
          {
            "start_id": 2,
            "start": [
              4.0,
              16.0
            ],
            "accepted": true,
            "guard": null,
            "status": 1,
            "success": true,
            "optimality": 1.3323132785976551e-11,
            "nfev": 15,
            "njev": 11,
            "active_mask": [
              0,
              0
            ],
            "cost": 2.465190328815662e-28,
            "Q": 4.930380657631324e-28,
            "x": [
              9.598961583701808,
              10.012435031315743
            ],
            "evaluation_calls": {
              "fun": 15,
              "jac": 11
            }
          },
          {
            "start_id": 3,
            "start": [
              10.0,
              4.0
            ],
            "accepted": true,
            "guard": null,
            "status": 1,
            "success": true,
            "optimality": 1.3323132785976551e-11,
            "nfev": 17,
            "njev": 13,
            "active_mask": [
              0,
              0
            ],
            "cost": 2.465190328815662e-28,
            "Q": 4.930380657631324e-28,
            "x": [
              9.598961583701808,
              10.012435031315743
            ],
            "evaluation_calls": {
              "fun": 17,
              "jac": 13
            }
          },
          {
            "start_id": 4,
            "start": [
              10.0,
              10.0
            ],
            "accepted": true,
            "guard": null,
            "status": 1,
            "success": true,
            "optimality": 1.3323132785976551e-11,
            "nfev": 8,
            "njev": 7,
            "active_mask": [
              0,
              0
            ],
            "cost": 2.465190328815662e-28,
            "Q": 4.930380657631324e-28,
            "x": [
              9.598961583701808,
              10.012435031315743
            ],
            "evaluation_calls": {
              "fun": 8,
              "jac": 7
            }
          },
          {
            "start_id": 5,
            "start": [
              10.0,
              16.0
            ],
            "accepted": true,
            "guard": null,
            "status": 1,
            "success": true,
            "optimality": 1.3323132785976551e-11,
            "nfev": 17,
            "njev": 13,
            "active_mask": [
              0,
              0
            ],
            "cost": 2.465190328815662e-28,
            "Q": 4.930380657631324e-28,
            "x": [
              9.598961583701808,
              10.012435031315743
            ],
            "evaluation_calls": {
              "fun": 17,
              "jac": 13
            }
          },
          {
            "start_id": 6,
            "start": [
              16.0,
              4.0
            ],
            "accepted": true,
            "guard": null,
            "status": 1,
            "success": true,
            "optimality": 1.3323132785976551e-11,
            "nfev": 14,
            "njev": 11,
            "active_mask": [
              0,
              0
            ],
            "cost": 2.465190328815662e-28,
            "Q": 4.930380657631324e-28,
            "x": [
              9.598961583701808,
              10.012435031315743
            ],
            "evaluation_calls": {
              "fun": 14,
              "jac": 11
            }
          },
          {
            "start_id": 7,
            "start": [
              16.0,
              10.0
            ],
            "accepted": true,
            "guard": null,
            "status": 1,
            "success": true,
            "optimality": 1.3323132785976551e-11,
            "nfev": 14,
            "njev": 11,
            "active_mask": [
              0,
              0
            ],
            "cost": 2.465190328815662e-28,
            "Q": 4.930380657631324e-28,
            "x": [
              9.598961583701808,
              10.012435031315743
            ],
            "evaluation_calls": {
              "fun": 14,
              "jac": 11
            }
          },
          {
            "start_id": 8,
            "start": [
              16.0,
              16.0
            ],
            "accepted": true,
            "guard": null,
            "status": 1,
            "success": true,
            "optimality": 1.3323132785976551e-11,
            "nfev": 13,
            "njev": 10,
            "active_mask": [
              0,
              0
            ],
            "cost": 2.465190328815662e-28,
            "Q": 4.930380657631324e-28,
            "x": [
              9.598961583701808,
              10.012435031315743
            ],
            "evaluation_calls": {
              "fun": 13,
              "jac": 10
            }
          }
        ],
        "has_accepted_estimate": true,
        "estimate": [
          9.598961583701808,
          10.012435031315743
        ],
        "optimizer_converged": true,
        "numerical_ill_conditioned": false,
        "ambiguity_detected": false,
        "boundary_active": false,
        "branch_guard_triggered": false,
        "numeric_contract_violation": false,
        "selected_start": 0,
        "Q": 4.930380657631324e-28,
        "singular_values": [
          89.34663892233614,
          82.58829781674048
        ]
      },
      "estimate_tick": 80,
      "last_observation_tick": 80,
      "position_estimate": [
        9.598961583701808,
        10.012435031315743
      ],
      "source": "ACTUAL_WLS",
      "status": "OBSERVED",
      "target_id": 0,
      "velocity_estimate": [
        0.3958463348072385,
        0.049740125262971446
      ],
      "velocity_source": "ACTUAL_POSITION_DIFFERENCE"
    },
    "reference_true_position": [
      9.499999999999998,
      10.0
    ],
    "accepted_true_position": [
      9.598961583701808,
      10.012435031315743
    ],
    "position_estimation_error": [
      0.0,
      0.0
    ],
    "true_interval_mean_velocity": [
      0.3958463348072385,
      0.049740125262971446
    ],
    "actual_difference_velocity": [
      0.3958463348072385,
      0.049740125262971446
    ],
    "final_belief_velocity": [
      0.3958463348072385,
      0.049740125262971446
    ],
    "true_velocity_at_estimate_tick": [
      0.3875649686842565,
      0.09896158370180883
    ],
    "true_velocity_at_control_tick": [
      0.3875649686842565,
      0.09896158370180883
    ],
    "velocity_vector_error_at_estimate_tick": 0.049913254709636694,
    "velocity_vector_error_at_control_tick": 0.049913254709636694,
    "speed_error": -0.001040853167267708,
    "direction_error_rad": -0.1249999999999929,
    "estimate_minus_true_mean": [
      0.0,
      0.0
    ],
    "true_mean_minus_anchor_velocity": [
      0.008281366122982026,
      -0.04922145843883738
    ],
    "clipping_or_retention_effect": [
      0.0,
      0.0
    ],
    "actual_difference_direction": 0.12500000000000713,
    "actual_instantaneous_direction": 0.25000000000000006,
    "D100_control_status": "TERMINAL_BELIEF_NOT_ACTIVE_CONTROL",
    "interpretation": "actual reference interval; no theoretical value used as acceptance gate"
  },
  "ON": {
    "status": "IDENTIFIABLE",
    "actual_event": {
      "freeze_tick": 80,
      "freeze_ordinal": 19,
      "target": 0,
      "frame_id": "H5_ON_KEEP:T0:first61:tick80",
      "measurement_tick": 80,
      "available_tick": 80,
      "consumed_tick": 80,
      "accepted": true,
      "rejection_reasons": [],
      "Q": "PASS",
      "reference_tick": 75,
      "reference_interval": 5,
      "estimator_method": "ANALYTIC_BEARING_INTERSECTION",
      "observation_origin": "MODEL",
      "provenance": "SIMULATED",
      "accepted_evidence": "actual appended consumer position history; original rule checked without extra freeze",
      "reference_position": [
        9.499999999999998,
        10.0
      ],
      "accepted_position": [
        9.598961583701808,
        10.012435031315743
      ],
      "unclipped_difference_velocity": [
        0.3958463348072385,
        0.049740125262971446
      ],
      "actual_estimator": "ANALYTIC_BEARING_INTERSECTION"
    },
    "actual_control_belief": {
      "available_tick": 80,
      "diagnostics": {
        "estimator_method": "ANALYTIC_BEARING_INTERSECTION",
        "analytic_solution_success": true,
        "nonlinear_solver_starts": 0,
        "observation_origin": "MODEL",
        "provenance": "SIMULATED",
        "starts": [],
        "has_accepted_estimate": true,
        "estimate": [
          9.598961583701808,
          10.012435031315743
        ],
        "optimizer_converged": true,
        "numerical_ill_conditioned": false,
        "ambiguity_detected": false,
        "boundary_active": false,
        "branch_guard_triggered": false,
        "numeric_contract_violation": false,
        "selected_start": null,
        "Q": 4.930380657631324e-28,
        "rejection_reason": null,
        "compatibility_note": "optimizer_converged means analytic success, not nonlinear optimization; starts empty; uniqueness is geometric, not nine-start ambiguity testing",
        "direction_determinant": 0.9979706568769389,
        "determinant_machine_safety_threshold": 1.4210854715202004e-14,
        "forward_distances": [
          0.5950105511973318,
          0.5682459887846109
        ],
        "singular_values": [
          89.34663892233614,
          82.58829781674048
        ],
        "standardized_residual": [
          2.220446049250313e-14,
          0.0
        ],
        "numeric_condition_ratio": 0.9243581942520491,
        "boundary_machine_tolerance": 2.8421709430404007e-13
      },
      "estimate_tick": 80,
      "last_observation_tick": 80,
      "position_estimate": [
        9.598961583701808,
        10.012435031315743
      ],
      "source": "ACTUAL_WLS",
      "status": "OBSERVED",
      "target_id": 0,
      "velocity_estimate": [
        0.3958463348072385,
        0.049740125262971446
      ],
      "velocity_source": "ACTUAL_POSITION_DIFFERENCE"
    },
    "reference_true_position": [
      9.499999999999998,
      10.0
    ],
    "accepted_true_position": [
      9.598961583701808,
      10.012435031315743
    ],
    "position_estimation_error": [
      0.0,
      0.0
    ],
    "true_interval_mean_velocity": [
      0.3958463348072385,
      0.049740125262971446
    ],
    "actual_difference_velocity": [
      0.3958463348072385,
      0.049740125262971446
    ],
    "final_belief_velocity": [
      0.3958463348072385,
      0.049740125262971446
    ],
    "true_velocity_at_estimate_tick": [
      0.3875649686842565,
      0.09896158370180883
    ],
    "true_velocity_at_control_tick": [
      0.3875649686842565,
      0.09896158370180883
    ],
    "velocity_vector_error_at_estimate_tick": 0.049913254709636694,
    "velocity_vector_error_at_control_tick": 0.049913254709636694,
    "speed_error": -0.001040853167267708,
    "direction_error_rad": -0.1249999999999929,
    "estimate_minus_true_mean": [
      0.0,
      0.0
    ],
    "true_mean_minus_anchor_velocity": [
      0.008281366122982026,
      -0.04922145843883738
    ],
    "clipping_or_retention_effect": [
      0.0,
      0.0
    ],
    "actual_difference_direction": 0.12500000000000713,
    "actual_instantaneous_direction": 0.25000000000000006,
    "D100_control_status": "TERMINAL_BELIEF_NOT_ACTIVE_CONTROL",
    "interpretation": "actual reference interval; no theoretical value used as acceptance gate"
  }
}

D80速度滞后是实际差分区间对应的历史平均速度与瞬时速度之差。该分解不等于所有价值变化的单因素因果证明。逐目标—控制tick分解见JSON；超过一秒截断使用真实输出，不套用未截断公式。

## H5-B：反馈与服务

{
  "FEEDBACK_EFFECT_IDENTIFIED": "YES",
  "FEEDBACK_BENEFIT_SUPPORTED": "POSITIVE_NET_VALUE_EFFECT",
  "Delta_V_FB": 0.39749529730192784,
  "I_FB": 0.39749529730192784,
  "mechanism_layers": {
    "G": "CHANGED",
    "GQ": "CHANGED",
    "continuous_service": "CHANGED",
    "completion": "CHANGED",
    "actual_control": "CHANGED",
    "robot_trajectory": "CHANGED",
    "belief": "CHANGED",
    "observations": "CHANGED",
    "Q": "CHANGED",
    "economic_value": "CHANGED"
  },
  "scope": "conditional closed-loop total increment; not a single velocity-update causal effect"
}

{
  "H5_HF_KEEP": {
    "P0": 0.6000000000000001,
    "Pmax": 2.25,
    "required_duration": 2.25,
    "M_service": 0.0,
    "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin",
    "NG": 33,
    "GQ_valid_intervals": 33,
    "quality_counts": {
      "PASS": 33
    },
    "terminal": {
      "target": 0,
      "kind": "completed",
      "time": 4.65,
      "tick": 93,
      "processed_tick": 93,
      "release_change_cost": 0.0
    },
    "completion_tick": 93,
    "resets": [],
    "natural_release": "original terminal transaction; no optimizer",
    "positive_cost_ledger": {
      "completion": 0.125,
      "flow": 0.02562500000000003,
      "late": 0.039374999999999986,
      "effort": 1.4104130146114071e-05,
      "terminal": 0.375,
      "change": 0.0
    },
    "G_intervals": [
      {
        "left_tick": 60,
        "right_tick": 61,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 61,
        "right_tick": 62,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 62,
        "right_tick": 63,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 63,
        "right_tick": 64,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 64,
        "right_tick": 65,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 65,
        "right_tick": 66,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 66,
        "right_tick": 67,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 67,
        "right_tick": 68,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 68,
        "right_tick": 69,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 69,
        "right_tick": 70,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 70,
        "right_tick": 71,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 71,
        "right_tick": 72,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 72,
        "right_tick": 73,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 73,
        "right_tick": 74,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 74,
        "right_tick": 75,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 75,
        "right_tick": 76,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 76,
        "right_tick": 77,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 77,
        "right_tick": 78,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 78,
        "right_tick": 79,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 79,
        "right_tick": 80,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 80,
        "right_tick": 81,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 81,
        "right_tick": 82,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 82,
        "right_tick": 83,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 83,
        "right_tick": 84,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 84,
        "right_tick": 85,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 85,
        "right_tick": 86,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 86,
        "right_tick": 87,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 87,
        "right_tick": 88,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 88,
        "right_tick": 89,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 89,
        "right_tick": 90,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 90,
        "right_tick": 91,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 91,
        "right_tick": 92,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 92,
        "right_tick": 93,
        "G": true,
        "GQ": true
      }
    ],
    "GQ_intervals": [
      {
        "left_tick": 60,
        "right_tick": 61,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 61,
        "right_tick": 62,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 62,
        "right_tick": 63,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 63,
        "right_tick": 64,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 64,
        "right_tick": 65,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 65,
        "right_tick": 66,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 66,
        "right_tick": 67,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 67,
        "right_tick": 68,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 68,
        "right_tick": 69,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 69,
        "right_tick": 70,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 70,
        "right_tick": 71,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 71,
        "right_tick": 72,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 72,
        "right_tick": 73,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 73,
        "right_tick": 74,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 74,
        "right_tick": 75,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 75,
        "right_tick": 76,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 76,
        "right_tick": 77,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 77,
        "right_tick": 78,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 78,
        "right_tick": 79,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 79,
        "right_tick": 80,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 80,
        "right_tick": 81,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 81,
        "right_tick": 82,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 82,
        "right_tick": 83,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 83,
        "right_tick": 84,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 84,
        "right_tick": 85,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 85,
        "right_tick": 86,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 86,
        "right_tick": 87,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 87,
        "right_tick": 88,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 88,
        "right_tick": 89,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 89,
        "right_tick": 90,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 90,
        "right_tick": 91,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 91,
        "right_tick": 92,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 92,
        "right_tick": 93,
        "G": true,
        "GQ": true
      }
    ],
    "terminal_positions": [
      [
        10.266869092871328,
        9.61108431316442
      ],
      [
        10.266869092871328,
        10.459612450588276
      ],
      [
        2.0,
        2.0
      ]
    ],
    "terminal_status": {
      "0": "completed",
      "1": "unfinished"
    },
    "natural_release_events": [
      {
        "target": 0,
        "kind": "completed",
        "time": 4.65,
        "tick": 93,
        "processed_tick": 93,
        "release_change_cost": 0.0
      }
    ]
  },
  "H5_HF_SWITCH": {
    "P0": 0.0,
    "Pmax": 1.05,
    "required_duration": 1.05,
    "M_service": 0.0,
    "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin",
    "NG": 21,
    "GQ_valid_intervals": 21,
    "quality_counts": {
      "PASS": 51
    },
    "terminal": {
      "target": 1,
      "kind": "completed",
      "time": 5.5,
      "tick": 110,
      "processed_tick": 110,
      "release_change_cost": 0.0
    },
    "completion_tick": 110,
    "resets": [],
    "natural_release": "original terminal transaction; no optimizer",
    "positive_cost_ledger": {
      "completion": 0.1875,
      "flow": 0.02812499999999998,
      "late": 0.046875,
      "effort": 3.4915765090263393e-06,
      "terminal": 0.25,
      "change": 0.02
    },
    "G_intervals": [
      {
        "left_tick": 89,
        "right_tick": 90,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 90,
        "right_tick": 91,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 91,
        "right_tick": 92,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 92,
        "right_tick": 93,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 93,
        "right_tick": 94,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 94,
        "right_tick": 95,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 95,
        "right_tick": 96,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 96,
        "right_tick": 97,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 97,
        "right_tick": 98,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 98,
        "right_tick": 99,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 99,
        "right_tick": 100,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 100,
        "right_tick": 101,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 101,
        "right_tick": 102,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 102,
        "right_tick": 103,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 103,
        "right_tick": 104,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 104,
        "right_tick": 105,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 105,
        "right_tick": 106,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 106,
        "right_tick": 107,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 107,
        "right_tick": 108,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 108,
        "right_tick": 109,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 109,
        "right_tick": 110,
        "G": true,
        "GQ": true
      }
    ],
    "GQ_intervals": [
      {
        "left_tick": 89,
        "right_tick": 90,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 90,
        "right_tick": 91,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 91,
        "right_tick": 92,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 92,
        "right_tick": 93,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 93,
        "right_tick": 94,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 94,
        "right_tick": 95,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 95,
        "right_tick": 96,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 96,
        "right_tick": 97,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 97,
        "right_tick": 98,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 98,
        "right_tick": 99,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 99,
        "right_tick": 100,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 100,
        "right_tick": 101,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 101,
        "right_tick": 102,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 102,
        "right_tick": 103,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 103,
        "right_tick": 104,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 104,
        "right_tick": 105,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 105,
        "right_tick": 106,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 106,
        "right_tick": 107,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 107,
        "right_tick": 108,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 108,
        "right_tick": 109,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 109,
        "right_tick": 110,
        "G": true,
        "GQ": true
      }
    ],
    "terminal_positions": [
      [
        9.63006035395574,
        9.85138373367194
      ],
      [
        9.63006035395574,
        10.699911871095795
      ],
      [
        2.0,
        2.0
      ]
    ],
    "terminal_status": {
      "0": "unfinished",
      "1": "completed"
    },
    "natural_release_events": [
      {
        "target": 1,
        "kind": "completed",
        "time": 5.5,
        "tick": 110,
        "processed_tick": 110,
        "release_change_cost": 0.0
      }
    ]
  },
  "H5_HF_MEMBER_CHANGE": {
    "P0": 0.0,
    "Pmax": 0.0,
    "required_duration": 2.25,
    "M_service": -2.25,
    "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin",
    "NG": 0,
    "GQ_valid_intervals": 0,
    "quality_counts": {
      "FAIL": 60,
      "UNKNOWN": 1
    },
    "terminal": {
      "target": 0,
      "kind": "unfinished",
      "time": 6.0,
      "tick": 120,
      "processed_tick": 120,
      "release_change_cost": 0.0
    },
    "completion_tick": null,
    "resets": [],
    "natural_release": "original terminal transaction; no optimizer",
    "positive_cost_ledger": {
      "completion": 0.0,
      "flow": 0.03124999999999999,
      "late": 0.05624999999999998,
      "effort": 0.0006125696046304413,
      "terminal": 0.625,
      "change": 0.02
    },
    "G_intervals": [],
    "GQ_intervals": [],
    "terminal_positions": [
      [
        9.54715677477287,
        9.559247459772442
      ],
      [
        10.741177661315033,
        10.759646002858922
      ],
      [
        8.683524490712959,
        8.026359121115878
      ]
    ],
    "terminal_status": {
      "0": "unfinished",
      "1": "unfinished"
    },
    "natural_release_events": []
  },
  "H5_OFF_KEEP": {
    "P0": 0.6000000000000001,
    "Pmax": 1.9000000000000001,
    "required_duration": 2.25,
    "M_service": -0.34999999999999987,
    "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin",
    "NG": 26,
    "GQ_valid_intervals": 26,
    "quality_counts": {
      "PASS": 49,
      "FAIL": 11
    },
    "terminal": {
      "target": 0,
      "kind": "unfinished",
      "time": 6.0,
      "tick": 120,
      "processed_tick": 120,
      "release_change_cost": 0.0
    },
    "completion_tick": null,
    "resets": [
      {
        "target": 0,
        "kind": "reset",
        "tick": 87,
        "time": 4.3500000000000005,
        "reason": "observation_invalid",
        "progress_before": 1.9000000000000001
      }
    ],
    "natural_release": "original terminal transaction; no optimizer",
    "positive_cost_ledger": {
      "completion": 0.0,
      "flow": 0.03124999999999999,
      "late": 0.05624999999999998,
      "effort": 9.40143207405902e-06,
      "terminal": 0.625,
      "change": 0.0
    },
    "G_intervals": [
      {
        "left_tick": 60,
        "right_tick": 61,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 61,
        "right_tick": 62,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 62,
        "right_tick": 63,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 63,
        "right_tick": 64,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 64,
        "right_tick": 65,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 65,
        "right_tick": 66,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 66,
        "right_tick": 67,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 67,
        "right_tick": 68,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 68,
        "right_tick": 69,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 69,
        "right_tick": 70,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 70,
        "right_tick": 71,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 71,
        "right_tick": 72,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 72,
        "right_tick": 73,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 73,
        "right_tick": 74,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 74,
        "right_tick": 75,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 75,
        "right_tick": 76,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 76,
        "right_tick": 77,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 77,
        "right_tick": 78,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 78,
        "right_tick": 79,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 79,
        "right_tick": 80,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 80,
        "right_tick": 81,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 81,
        "right_tick": 82,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 82,
        "right_tick": 83,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 83,
        "right_tick": 84,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 84,
        "right_tick": 85,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 85,
        "right_tick": 86,
        "G": true,
        "GQ": true
      }
    ],
    "GQ_intervals": [
      {
        "left_tick": 60,
        "right_tick": 61,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 61,
        "right_tick": 62,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 62,
        "right_tick": 63,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 63,
        "right_tick": 64,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 64,
        "right_tick": 65,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 65,
        "right_tick": 66,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 66,
        "right_tick": 67,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 67,
        "right_tick": 68,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 68,
        "right_tick": 69,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 69,
        "right_tick": 70,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 70,
        "right_tick": 71,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 71,
        "right_tick": 72,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 72,
        "right_tick": 73,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 73,
        "right_tick": 74,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 74,
        "right_tick": 75,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 75,
        "right_tick": 76,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 76,
        "right_tick": 77,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 77,
        "right_tick": 78,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 78,
        "right_tick": 79,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 79,
        "right_tick": 80,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 80,
        "right_tick": 81,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 81,
        "right_tick": 82,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 82,
        "right_tick": 83,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 83,
        "right_tick": 84,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 84,
        "right_tick": 85,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 85,
        "right_tick": 86,
        "G": true,
        "GQ": true
      }
    ],
    "terminal_positions": [
      [
        10.023417270265305,
        9.574976310719745
      ],
      [
        10.023417270265305,
        10.4235044481436
      ],
      [
        2.0,
        2.0
      ]
    ],
    "terminal_status": {
      "0": "unfinished",
      "1": "unfinished"
    },
    "natural_release_events": []
  },
  "H5_ON_KEEP": {
    "P0": 0.6000000000000001,
    "Pmax": 2.25,
    "required_duration": 2.25,
    "M_service": 0.0,
    "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin",
    "NG": 33,
    "GQ_valid_intervals": 33,
    "quality_counts": {
      "PASS": 33
    },
    "terminal": {
      "target": 0,
      "kind": "completed",
      "time": 4.65,
      "tick": 93,
      "processed_tick": 93,
      "release_change_cost": 0.0
    },
    "completion_tick": 93,
    "resets": [],
    "natural_release": "original terminal transaction; no optimizer",
    "positive_cost_ledger": {
      "completion": 0.125,
      "flow": 0.02562500000000003,
      "late": 0.039374999999999986,
      "effort": 1.4104130146114071e-05,
      "terminal": 0.375,
      "change": 0.0
    },
    "G_intervals": [
      {
        "left_tick": 60,
        "right_tick": 61,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 61,
        "right_tick": 62,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 62,
        "right_tick": 63,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 63,
        "right_tick": 64,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 64,
        "right_tick": 65,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 65,
        "right_tick": 66,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 66,
        "right_tick": 67,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 67,
        "right_tick": 68,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 68,
        "right_tick": 69,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 69,
        "right_tick": 70,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 70,
        "right_tick": 71,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 71,
        "right_tick": 72,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 72,
        "right_tick": 73,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 73,
        "right_tick": 74,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 74,
        "right_tick": 75,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 75,
        "right_tick": 76,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 76,
        "right_tick": 77,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 77,
        "right_tick": 78,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 78,
        "right_tick": 79,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 79,
        "right_tick": 80,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 80,
        "right_tick": 81,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 81,
        "right_tick": 82,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 82,
        "right_tick": 83,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 83,
        "right_tick": 84,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 84,
        "right_tick": 85,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 85,
        "right_tick": 86,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 86,
        "right_tick": 87,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 87,
        "right_tick": 88,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 88,
        "right_tick": 89,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 89,
        "right_tick": 90,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 90,
        "right_tick": 91,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 91,
        "right_tick": 92,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 92,
        "right_tick": 93,
        "G": true,
        "GQ": true
      }
    ],
    "GQ_intervals": [
      {
        "left_tick": 60,
        "right_tick": 61,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 61,
        "right_tick": 62,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 62,
        "right_tick": 63,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 63,
        "right_tick": 64,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 64,
        "right_tick": 65,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 65,
        "right_tick": 66,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 66,
        "right_tick": 67,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 67,
        "right_tick": 68,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 68,
        "right_tick": 69,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 69,
        "right_tick": 70,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 70,
        "right_tick": 71,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 71,
        "right_tick": 72,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 72,
        "right_tick": 73,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 73,
        "right_tick": 74,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 74,
        "right_tick": 75,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 75,
        "right_tick": 76,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 76,
        "right_tick": 77,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 77,
        "right_tick": 78,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 78,
        "right_tick": 79,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 79,
        "right_tick": 80,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 80,
        "right_tick": 81,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 81,
        "right_tick": 82,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 82,
        "right_tick": 83,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 83,
        "right_tick": 84,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 84,
        "right_tick": 85,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 85,
        "right_tick": 86,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 86,
        "right_tick": 87,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 87,
        "right_tick": 88,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 88,
        "right_tick": 89,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 89,
        "right_tick": 90,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 90,
        "right_tick": 91,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 91,
        "right_tick": 92,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 92,
        "right_tick": 93,
        "G": true,
        "GQ": true
      }
    ],
    "terminal_positions": [
      [
        10.266869092871328,
        9.61108431316442
      ],
      [
        10.266869092871328,
        10.459612450588276
      ],
      [
        2.0,
        2.0
      ]
    ],
    "terminal_status": {
      "0": "completed",
      "1": "unfinished"
    },
    "natural_release_events": [
      {
        "target": 0,
        "kind": "completed",
        "time": 4.65,
        "tick": 93,
        "processed_tick": 93,
        "release_change_cost": 0.0
      }
    ]
  },
  "H5_ON_SWITCH": {
    "P0": 0.0,
    "Pmax": 1.05,
    "required_duration": 1.05,
    "M_service": 0.0,
    "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin",
    "NG": 21,
    "GQ_valid_intervals": 21,
    "quality_counts": {
      "PASS": 51
    },
    "terminal": {
      "target": 1,
      "kind": "completed",
      "time": 5.5,
      "tick": 110,
      "processed_tick": 110,
      "release_change_cost": 0.0
    },
    "completion_tick": 110,
    "resets": [],
    "natural_release": "original terminal transaction; no optimizer",
    "positive_cost_ledger": {
      "completion": 0.1875,
      "flow": 0.02812499999999998,
      "late": 0.046875,
      "effort": 3.4915765090263393e-06,
      "terminal": 0.25,
      "change": 0.02
    },
    "G_intervals": [
      {
        "left_tick": 89,
        "right_tick": 90,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 90,
        "right_tick": 91,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 91,
        "right_tick": 92,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 92,
        "right_tick": 93,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 93,
        "right_tick": 94,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 94,
        "right_tick": 95,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 95,
        "right_tick": 96,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 96,
        "right_tick": 97,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 97,
        "right_tick": 98,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 98,
        "right_tick": 99,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 99,
        "right_tick": 100,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 100,
        "right_tick": 101,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 101,
        "right_tick": 102,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 102,
        "right_tick": 103,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 103,
        "right_tick": 104,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 104,
        "right_tick": 105,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 105,
        "right_tick": 106,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 106,
        "right_tick": 107,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 107,
        "right_tick": 108,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 108,
        "right_tick": 109,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 109,
        "right_tick": 110,
        "G": true,
        "GQ": true
      }
    ],
    "GQ_intervals": [
      {
        "left_tick": 89,
        "right_tick": 90,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 90,
        "right_tick": 91,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 91,
        "right_tick": 92,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 92,
        "right_tick": 93,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 93,
        "right_tick": 94,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 94,
        "right_tick": 95,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 95,
        "right_tick": 96,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 96,
        "right_tick": 97,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 97,
        "right_tick": 98,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 98,
        "right_tick": 99,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 99,
        "right_tick": 100,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 100,
        "right_tick": 101,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 101,
        "right_tick": 102,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 102,
        "right_tick": 103,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 103,
        "right_tick": 104,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 104,
        "right_tick": 105,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 105,
        "right_tick": 106,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 106,
        "right_tick": 107,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 107,
        "right_tick": 108,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 108,
        "right_tick": 109,
        "G": true,
        "GQ": true
      },
      {
        "left_tick": 109,
        "right_tick": 110,
        "G": true,
        "GQ": true
      }
    ],
    "terminal_positions": [
      [
        9.63006035395574,
        9.85138373367194
      ],
      [
        9.63006035395574,
        10.699911871095795
      ],
      [
        2.0,
        2.0
      ]
    ],
    "terminal_status": {
      "0": "unfinished",
      "1": "completed"
    },
    "natural_release_events": [
      {
        "target": 1,
        "kind": "completed",
        "time": 5.5,
        "tick": 110,
        "processed_tick": 110,
        "release_change_cost": 0.0
      }
    ]
  },
  "H5_ON_MEMBER_CHANGE": {
    "P0": 0.0,
    "Pmax": 0.0,
    "required_duration": 2.25,
    "M_service": -2.25,
    "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin",
    "NG": 0,
    "GQ_valid_intervals": 0,
    "quality_counts": {
      "FAIL": 60,
      "UNKNOWN": 1
    },
    "terminal": {
      "target": 0,
      "kind": "unfinished",
      "time": 6.0,
      "tick": 120,
      "processed_tick": 120,
      "release_change_cost": 0.0
    },
    "completion_tick": null,
    "resets": [],
    "natural_release": "original terminal transaction; no optimizer",
    "positive_cost_ledger": {
      "completion": 0.0,
      "flow": 0.03124999999999999,
      "late": 0.05624999999999998,
      "effort": 0.0006125696046304367,
      "terminal": 0.625,
      "change": 0.02
    },
    "G_intervals": [],
    "GQ_intervals": [],
    "terminal_positions": [
      [
        9.54715677477287,
        9.559247459772442
      ],
      [
        10.741177661314495,
        10.759646002858345
      ],
      [
        8.683524490713001,
        8.02635912111583
      ]
    ],
    "terminal_status": {
      "0": "unfinished",
      "1": "unfinished"
    },
    "natural_release_events": []
  }
}

## H5-C：价值、排序及条件regret

{
  "matrix": {
    "KEEP": {
      "HF": {
        "status": "VALID_SAVED_RESULT",
        "value": -0.31501410413014613
      },
      "ON": {
        "status": "VALID_SAVED_RESULT",
        "value": -0.31501410413014613
      },
      "OFF": {
        "status": "VALID_SAVED_RESULT",
        "value": -0.712509401432074
      }
    },
    "SWITCH": {
      "HF": {
        "status": "VALID_SAVED_RESULT",
        "value": -0.157503491576509
      },
      "ON": {
        "status": "VALID_SAVED_RESULT",
        "value": -0.157503491576509
      },
      "OFF": {
        "status": "NOT_RUN",
        "value": null
      }
    },
    "MEMBER_CHANGE": {
      "HF": {
        "status": "VALID_SAVED_RESULT",
        "value": -0.7331125696046304
      },
      "ON": {
        "status": "VALID_SAVED_RESULT",
        "value": -0.7331125696046304
      },
      "OFF": {
        "status": "NOT_RUN",
        "value": null
      }
    }
  },
  "errors": {
    "KEEP": {
      "signed_error": 0.0,
      "AE": 0.0
    },
    "SWITCH": {
      "signed_error": 0.0,
      "AE": 0.0
    },
    "MEMBER_CHANGE": {
      "signed_error": 0.0,
      "AE": 0.0
    }
  },
  "MAE": 0.0,
  "denominator": 3,
  "relative_errors": {
    "KEEP-SWITCH": 0.0,
    "KEEP-MEMBER_CHANGE": 0.0,
    "SWITCH-MEMBER_CHANGE": 0.0
  },
  "rankings": {
    "HF": {
      "strict_order": [
        "SWITCH",
        "KEEP",
        "MEMBER_CHANGE"
      ],
      "exact_ties": [
        [
          "SWITCH"
        ],
        [
          "KEEP"
        ],
        [
          "MEMBER_CHANGE"
        ]
      ],
      "epsilon": 1e-08,
      "epsilon_best": [
        "SWITCH"
      ],
      "actual_selection": "NOT_SPECIFIED",
      "HF_regret": {
        "SWITCH": 0.0
      }
    },
    "ON": {
      "strict_order": [
        "SWITCH",
        "KEEP",
        "MEMBER_CHANGE"
      ],
      "exact_ties": [
        [
          "SWITCH"
        ],
        [
          "KEEP"
        ],
        [
          "MEMBER_CHANGE"
        ]
      ],
      "epsilon": 1e-08,
      "epsilon_best": [
        "SWITCH"
      ],
      "actual_selection": "NOT_SPECIFIED",
      "HF_regret": {
        "SWITCH": 0.0
      }
    }
  },
  "OFF_scope": {
    "actions": [
      "KEEP"
    ],
    "complete_ranking": "NOT_APPLICABLE",
    "three_cell_MAE": "NOT_APPLICABLE",
    "regret": "NOT_APPLICABLE"
  }
}

## 配对预测误差

{
  "HF/ON/KEEP": {
    "common_target_ticks": [
      [
        0,
        60
      ],
      [
        0,
        61
      ],
      [
        0,
        62
      ],
      [
        0,
        63
      ],
      [
        0,
        64
      ],
      [
        0,
        65
      ],
      [
        0,
        66
      ],
      [
        0,
        67
      ],
      [
        0,
        68
      ],
      [
        0,
        69
      ],
      [
        0,
        70
      ],
      [
        0,
        71
      ],
      [
        0,
        72
      ],
      [
        0,
        73
      ],
      [
        0,
        74
      ],
      [
        0,
        75
      ],
      [
        0,
        76
      ],
      [
        0,
        77
      ],
      [
        0,
        78
      ],
      [
        0,
        79
      ],
      [
        0,
        80
      ],
      [
        0,
        81
      ],
      [
        0,
        82
      ],
      [
        0,
        83
      ],
      [
        0,
        84
      ],
      [
        0,
        85
      ],
      [
        0,
        86
      ],
      [
        0,
        87
      ],
      [
        0,
        88
      ],
      [
        0,
        89
      ],
      [
        0,
        90
      ],
      [
        0,
        91
      ],
      [
        0,
        92
      ]
    ],
    "denominator": 33,
    "left_valid_count": 33,
    "right_valid_count": 33,
    "left_position_error": 0.014005290605552456,
    "left_velocity_error": 0.05574148759077401,
    "right_position_error": 0.014005290605552456,
    "right_velocity_error": 0.05574148759077401
  },
  "HF/ON/SWITCH": {
    "common_target_ticks": [
      [
        1,
        60
      ],
      [
        1,
        61
      ],
      [
        1,
        62
      ],
      [
        1,
        63
      ],
      [
        1,
        64
      ],
      [
        1,
        65
      ],
      [
        1,
        66
      ],
      [
        1,
        67
      ],
      [
        1,
        68
      ],
      [
        1,
        69
      ],
      [
        1,
        70
      ],
      [
        1,
        71
      ],
      [
        1,
        72
      ],
      [
        1,
        73
      ],
      [
        1,
        74
      ],
      [
        1,
        75
      ],
      [
        1,
        76
      ],
      [
        1,
        77
      ],
      [
        1,
        78
      ],
      [
        1,
        79
      ],
      [
        1,
        80
      ],
      [
        1,
        81
      ],
      [
        1,
        82
      ],
      [
        1,
        83
      ],
      [
        1,
        84
      ],
      [
        1,
        85
      ],
      [
        1,
        86
      ],
      [
        1,
        87
      ],
      [
        1,
        88
      ],
      [
        1,
        89
      ],
      [
        1,
        90
      ],
      [
        1,
        91
      ],
      [
        1,
        92
      ],
      [
        1,
        93
      ],
      [
        1,
        94
      ],
      [
        1,
        95
      ],
      [
        1,
        96
      ],
      [
        1,
        97
      ],
      [
        1,
        98
      ],
      [
        1,
        99
      ],
      [
        1,
        100
      ],
      [
        1,
        101
      ],
      [
        1,
        102
      ],
      [
        1,
        103
      ],
      [
        1,
        104
      ],
      [
        1,
        105
      ],
      [
        1,
        106
      ],
      [
        1,
        107
      ],
      [
        1,
        108
      ],
      [
        1,
        109
      ]
    ],
    "denominator": 50,
    "left_valid_count": 50,
    "right_valid_count": 50,
    "left_position_error": 0.1,
    "left_velocity_error": 0.0,
    "right_position_error": 0.1,
    "right_velocity_error": 0.0
  },
  "HF/ON/MEMBER_CHANGE": {
    "common_target_ticks": [
      [
        0,
        60
      ],
      [
        0,
        61
      ],
      [
        0,
        62
      ],
      [
        0,
        63
      ],
      [
        0,
        64
      ],
      [
        0,
        65
      ],
      [
        0,
        66
      ],
      [
        0,
        67
      ],
      [
        0,
        68
      ],
      [
        0,
        69
      ],
      [
        0,
        70
      ],
      [
        0,
        71
      ],
      [
        0,
        72
      ],
      [
        0,
        73
      ],
      [
        0,
        74
      ],
      [
        0,
        75
      ],
      [
        0,
        76
      ],
      [
        0,
        77
      ],
      [
        0,
        78
      ],
      [
        0,
        79
      ],
      [
        0,
        80
      ],
      [
        0,
        81
      ],
      [
        0,
        82
      ],
      [
        0,
        83
      ],
      [
        0,
        84
      ],
      [
        0,
        85
      ],
      [
        0,
        86
      ],
      [
        0,
        87
      ],
      [
        0,
        88
      ],
      [
        0,
        89
      ],
      [
        0,
        90
      ],
      [
        0,
        91
      ],
      [
        0,
        92
      ],
      [
        0,
        93
      ],
      [
        0,
        94
      ],
      [
        0,
        95
      ],
      [
        0,
        96
      ],
      [
        0,
        97
      ],
      [
        0,
        98
      ],
      [
        0,
        99
      ],
      [
        0,
        100
      ],
      [
        0,
        101
      ],
      [
        0,
        102
      ],
      [
        0,
        103
      ],
      [
        0,
        104
      ],
      [
        0,
        105
      ],
      [
        0,
        106
      ],
      [
        0,
        107
      ],
      [
        0,
        108
      ],
      [
        0,
        109
      ],
      [
        0,
        110
      ],
      [
        0,
        111
      ],
      [
        0,
        112
      ],
      [
        0,
        113
      ],
      [
        0,
        114
      ],
      [
        0,
        115
      ],
      [
        0,
        116
      ],
      [
        0,
        117
      ],
      [
        0,
        118
      ],
      [
        0,
        119
      ]
    ],
    "denominator": 60,
    "left_valid_count": 60,
    "right_valid_count": 60,
    "left_position_error": 0.02015747249540044,
    "left_velocity_error": 0.048033233312875796,
    "right_position_error": 0.02015747249557314,
    "right_velocity_error": 0.04803323331325698
  },
  "OFF/ON/KEEP": {
    "common_target_ticks": [
      [
        0,
        60
      ],
      [
        0,
        61
      ],
      [
        0,
        62
      ],
      [
        0,
        63
      ],
      [
        0,
        64
      ],
      [
        0,
        65
      ],
      [
        0,
        66
      ],
      [
        0,
        67
      ],
      [
        0,
        68
      ],
      [
        0,
        69
      ],
      [
        0,
        70
      ],
      [
        0,
        71
      ],
      [
        0,
        72
      ],
      [
        0,
        73
      ],
      [
        0,
        74
      ],
      [
        0,
        75
      ],
      [
        0,
        76
      ],
      [
        0,
        77
      ],
      [
        0,
        78
      ],
      [
        0,
        79
      ],
      [
        0,
        80
      ],
      [
        0,
        81
      ],
      [
        0,
        82
      ],
      [
        0,
        83
      ],
      [
        0,
        84
      ],
      [
        0,
        85
      ],
      [
        0,
        86
      ],
      [
        0,
        87
      ],
      [
        0,
        88
      ],
      [
        0,
        89
      ],
      [
        0,
        90
      ],
      [
        0,
        91
      ],
      [
        0,
        92
      ]
    ],
    "denominator": 33,
    "left_valid_count": 60,
    "right_valid_count": 33,
    "left_position_error": 0.0496235450501352,
    "left_velocity_error": 0.15453125872703435,
    "right_position_error": 0.014005290605552456,
    "right_velocity_error": 0.05574148759077401
  }
}

## 科学调用闭合

{
  "status": "PASS",
  "started": 1655,
  "closed": 1655,
  "failed_internal_calls": 0,
  "totals": {
    "WLS": 145,
    "SOLVER": 1305,
    "ANALYTIC": 205
  },
  "per_cell": {
    "H5_HF_KEEP": {
      "WLS": 33,
      "SOLVER": 297
    },
    "H5_HF_SWITCH": {
      "WLS": 51,
      "SOLVER": 459
    },
    "H5_HF_MEMBER_CHANGE": {
      "WLS": 61,
      "SOLVER": 549
    },
    "H5_OFF_KEEP": {
      "ANALYTIC": 60
    },
    "H5_ON_KEEP": {
      "ANALYTIC": 33
    },
    "H5_ON_SWITCH": {
      "ANALYTIC": 51
    },
    "H5_ON_MEMBER_CHANGE": {
      "ANALYTIC": 61
    }
  },
  "analytic_log_counted_as_subset": true,
  "direct_scientific_estimate_calls": 0,
  "forbidden_original_evidence": {
    "records_before_science": "D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_fb_blvf_h5_arc_extension_001\\ATTEMPT_002\\RUNTIME_BINDINGS_BEFORE_SCIENCE.json",
    "original_estimator_routes": "preserved RAW diagnostics and per-cell counters matched",
    "limitation": "original per-call payload hashes absent; no nonexistent digest binding or new runtime monitor claimed"
  }
}

## 单次同口径计时

{
  "per_action": {
    "KEEP": {
      "HF": {
        "method": "HF",
        "action": "KEEP",
        "method_preparation": {
          "wall": 0.0014694000128656626,
          "cpu": 0.0
        },
        "core": {
          "wall": 9.351917199994205,
          "cpu": 9.234375
        },
        "complete_cell": {
          "wall": 9.523260699992534,
          "cpu": 9.40625
        },
        "core_scope": "Branch initialization, original transactions, model loop, estimator/solver wrappers, per-call persistence and profile guard; estimator namespace setup excluded and separately timed",
        "complete_scope": "method preparation, core, RAW write, saved-record history/service/physical/control audit and TRACE write; own timing-record write and task analysis excluded"
      },
      "ON": {
        "method": "ON",
        "action": "KEEP",
        "method_preparation": {
          "wall": 3.3999967854470015e-06,
          "cpu": 0.0
        },
        "core": {
          "wall": 4.543325500009814,
          "cpu": 4.484375
        },
        "complete_cell": {
          "wall": 4.670021600002656,
          "cpu": 4.609375
        },
        "core_scope": "Branch initialization, original transactions, model loop, estimator/solver wrappers, per-call persistence and profile guard; estimator namespace setup excluded and separately timed",
        "complete_scope": "method preparation, core, RAW write, saved-record history/service/physical/control audit and TRACE write; own timing-record write and task analysis excluded"
      },
      "core_wall_ratio_HF_over_ON": 2.0583859113713077,
      "core_CPU_ratio_HF_over_ON": 2.059233449477352,
      "complete_wall_ratio_HF_over_ON": 2.039232687914574
    },
    "SWITCH": {
      "HF": {
        "method": "HF",
        "action": "SWITCH",
        "method_preparation": {
          "wall": 0.001749599992763251,
          "cpu": 0.0
        },
        "core": {
          "wall": 13.571010399988154,
          "cpu": 13.5
        },
        "complete_cell": {
          "wall": 13.780646200000774,
          "cpu": 13.71875
        },
        "core_scope": "Branch initialization, original transactions, model loop, estimator/solver wrappers, per-call persistence and profile guard; estimator namespace setup excluded and separately timed",
        "complete_scope": "method preparation, core, RAW write, saved-record history/service/physical/control audit and TRACE write; own timing-record write and task analysis excluded"
      },
      "ON": {
        "method": "ON",
        "action": "SWITCH",
        "method_preparation": {
          "wall": 3.1999952625483274e-06,
          "cpu": 0.0
        },
        "core": {
          "wall": 6.1754108000022825,
          "cpu": 6.125
        },
        "complete_cell": {
          "wall": 6.31291589999455,
          "cpu": 6.25
        },
        "core_scope": "Branch initialization, original transactions, model loop, estimator/solver wrappers, per-call persistence and profile guard; estimator namespace setup excluded and separately timed",
        "complete_scope": "method preparation, core, RAW write, saved-record history/service/physical/control audit and TRACE write; own timing-record write and task analysis excluded"
      },
      "core_wall_ratio_HF_over_ON": 2.1975882802781537,
      "core_CPU_ratio_HF_over_ON": 2.204081632653061,
      "complete_wall_ratio_HF_over_ON": 2.1829288427575393
    },
    "MEMBER_CHANGE": {
      "HF": {
        "method": "HF",
        "action": "MEMBER_CHANGE",
        "method_preparation": {
          "wall": 0.0019503999792505056,
          "cpu": 0.0
        },
        "core": {
          "wall": 15.050129500014009,
          "cpu": 14.921875
        },
        "complete_cell": {
          "wall": 15.348579699988477,
          "cpu": 15.21875
        },
        "core_scope": "Branch initialization, original transactions, model loop, estimator/solver wrappers, per-call persistence and profile guard; estimator namespace setup excluded and separately timed",
        "complete_scope": "method preparation, core, RAW write, saved-record history/service/physical/control audit and TRACE write; own timing-record write and task analysis excluded"
      },
      "ON": {
        "method": "ON",
        "action": "MEMBER_CHANGE",
        "method_preparation": {
          "wall": 3.200024366378784e-06,
          "cpu": 0.0
        },
        "core": {
          "wall": 6.313976700010244,
          "cpu": 6.265625
        },
        "complete_cell": {
          "wall": 6.490004999999655,
          "cpu": 6.4375
        },
        "core_scope": "Branch initialization, original transactions, model loop, estimator/solver wrappers, per-call persistence and profile guard; estimator namespace setup excluded and separately timed",
        "complete_scope": "method preparation, core, RAW write, saved-record history/service/physical/control audit and TRACE write; own timing-record write and task analysis excluded"
      },
      "core_wall_ratio_HF_over_ON": 2.3836213237830908,
      "core_CPU_ratio_HF_over_ON": 2.3815461346633415,
      "complete_wall_ratio_HF_over_ON": 2.3649565293076495
    }
  },
  "HF_three_core_wall": 37.97305709999637,
  "ON_three_core_wall": 17.03271300002234,
  "ratio_HF_over_ON": 2.2294191829537997,
  "scope": "single paired run, same core boundary; method preparation separately recorded; full cell includes RAW, TRACE and audits; no repeated performance trials; not generic end-to-end advantage"
}

## 证据及科学解释限制

FINAL_RUNTIME_BINDING_RECEIPT = NOT_VERIFIED; original final runtime receipt never generated; no replacement imports performed.
Pre-science binding receipt preserved and checked by source manifest; source hashes are offline protection evidence, not restored dynamic execution evidence.
Per-call payload digest was not saved in original resource log; preserved RAW/TRACE and method/per-cell counts provide cross-evidence, no fabricated per-call hash binding.
One deterministic H5 conditional world, only KEEP has ON/OFF pairing; no unknown-future, statistical robustness or Minimax Regret claims.
Resource accounting INCOMPLETE, overall compliance and generic end-to-end speedup NOT_ESTABLISHED; original two execution windows and failure records retained.

历史审计PASS为原回执引用，没有在本次重新执行科学审计函数。H5与H4的差异仅可解释为不同条件世界整体差异，不能把全部差异归因于单一速度滞后。状态误差与价值预测误差分别判断，完成一致不等于全部状态一致。

## 资源

三个窗口分别保留：首次失败CPU小计1.046875秒、墙钟397.43556092950166秒；第二次科学执行CPU小计63.234375秒、墙钟124.95685481486726秒。本离线窗口资源见JSON，原累计写入12115003 bytes继续计入。不将独立窗口墙钟之和描述为单一连续授权窗口。未知宿主和退出尾部不记零。完成后停止，不登记H5正式关闭，不启动后续研究。
