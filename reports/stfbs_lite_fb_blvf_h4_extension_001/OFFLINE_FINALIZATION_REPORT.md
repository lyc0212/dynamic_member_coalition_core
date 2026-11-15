# H4 BLVF四格结果最小离线汇总核验

OFFLINE_FINALIZATION_STATUS = PASS
SCIENTIFIC_RESULT_STATUS = READY_FOR_INDEPENDENT_ACCEPTANCE
INDEPENDENT_SCIENTIFIC_ACCEPTANCE = PENDING

原科学提交：4a831fc734e88aad0e88d508ae902a61a13a2b28。原PARTIAL_RESULTS及失败记录保持不变。本次仅核验保存JSON，不导入项目模块，不执行consumer、解析估计或仿真。

## 科学内容及身份

D61—D80共20对反馈、20个物理帧科学内容一致。递归差异300处均位于明确身份白名单；分支内frame、packet、quality、payload和frame摘要关联分别核验。未删除传感器ID、目标ID、tick或payload摘要。

| 动作 | CAP | FB-OFF | FB-ON | HF |
|---|---|---|---|---|
| KEEP | -0.7125094014320741 | -0.712509401432074 | -0.31501434886780705 | -0.31501434886780705 |
| SWITCH | -0.7325026216050797 | NOT_RUN | -0.157503491576509 | -0.157503491576509 |
| MEMBER_CHANGE | -0.7330898517001428 | NOT_RUN | -0.7331122523628949 | -0.7331122523628949 |

## 完整ON分析及KEEP反馈效应

{
  "methods": {
    "CAP": {
      "errors": {
        "KEEP": {
          "signed_error": -0.39749505256426704,
          "AE": 0.39749505256426704
        },
        "SWITCH": {
          "signed_error": -0.5749991300285707,
          "AE": 0.5749991300285707
        },
        "MEMBER_CHANGE": {
          "signed_error": 2.2400662752053435e-05,
          "AE": 2.2400662752053435e-05
        }
      },
      "MAE": 0.3241721944185299,
      "denominator": 3,
      "strict_order": [
        "KEEP",
        "SWITCH",
        "MEMBER_CHANGE"
      ],
      "epsilon_best": [
        "KEEP"
      ],
      "HF_regret": {
        "KEEP": 0.15751085729129805
      },
      "actual_selection": "NOT_SPECIFIED",
      "relative_errors": {
        "KEEP-SWITCH": 0.1775040774643037,
        "KEEP-MEMBER_CHANGE": -0.3975174532270191,
        "SWITCH-MEMBER_CHANGE": -0.5750215306913228
      }
    },
    "FB_ON": {
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
      "strict_order": [
        "SWITCH",
        "KEEP",
        "MEMBER_CHANGE"
      ],
      "epsilon_best": [
        "SWITCH"
      ],
      "HF_regret": {
        "SWITCH": 0.0
      },
      "actual_selection": "NOT_SPECIFIED",
      "relative_errors": {
        "KEEP-SWITCH": 0.0,
        "KEEP-MEMBER_CHANGE": 0.0,
        "SWITCH-MEMBER_CHANGE": 0.0
      }
    }
  },
  "KEEP_effect": {
    "structure_value_effect": 1.1102230246251565e-16,
    "feedback_value_effect": 0.3974950525642669,
    "feedback_accuracy_improvement": 0.3974950525642669
  },
  "mechanism_layers": {
    "belief": "CHANGED",
    "actual_control": "CHANGED",
    "robot_trajectory": "CHANGED",
    "observations_and_Q": "CHANGED",
    "G_intervals": "CHANGED",
    "GQ_intervals": "CHANGED",
    "continuous_progress": "CHANGED",
    "completion": "CHANGED",
    "economic_value": "CHANGED"
  },
  "paired_prediction": {
    "denominator": 33,
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
    "OFF_position_error": 0.05995504176842401,
    "OFF_velocity_error": 0.1814405758915663,
    "ON_position_error": 0.0029988358697523145,
    "ON_velocity_error": 0.02998835869751857
  }
}

## D80合法转向适应

{
  "freeze_tick": 80,
  "accepted_event": {
    "freeze_tick": 80,
    "freeze_ordinal": 19,
    "target": 0,
    "frame_id": "BLVF_ON_KEEP:T0:first61:tick80",
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
      9.587758256189035,
      10.04794255386042
    ],
    "reference_class": "POST_TURN",
    "unclipped_difference_velocity": [
      0.3510330247561484,
      0.19177021544167872
    ]
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
        9.587758256189035,
        10.04794255386042
      ],
      "optimizer_converged": true,
      "numerical_ill_conditioned": false,
      "ambiguity_detected": false,
      "boundary_active": false,
      "branch_guard_triggered": false,
      "numeric_contract_violation": false,
      "selected_start": null,
      "Q": 0.0,
      "rejection_reason": null,
      "compatibility_note": "optimizer_converged means analytic success, not nonlinear optimization; starts empty; uniqueness is geometric, not nine-start ambiguity testing",
      "direction_determinant": 0.9995906265795702,
      "determinant_machine_safety_threshold": 1.4210854715202004e-14,
      "forward_distances": [
        0.6290994093036385,
        0.5517007799351868
      ],
      "singular_values": [
        90.75086609410859,
        79.33933022001814
      ],
      "standardized_residual": [
        0.0,
        0.0
      ],
      "numeric_condition_ratio": 0.8742542483037385,
      "boundary_machine_tolerance": 2.8421709430404007e-13
    },
    "estimate_tick": 80,
    "last_observation_tick": 80,
    "position_estimate": [
      9.587758256189035,
      10.04794255386042
    ],
    "source": "ACTUAL_WLS",
    "status": "OBSERVED",
    "target_id": 0,
    "velocity_estimate": [
      0.3510330247561484,
      0.19177021544167872
    ],
    "velocity_source": "ACTUAL_POSITION_DIFFERENCE"
  },
  "velocity_difference": [
    0.3510330247561484,
    0.19177021544167872
  ],
  "reference_position_error": 0.0,
  "accepted_position_error": 0.0,
  "true_velocity_at_control_tick": [
    0.35103302475614784,
    0.19177021544168052
  ],
  "true_velocity_at_estimate_tick": [
    0.35103302475614784,
    0.19177021544168052
  ],
  "velocity_error_at_control_tick": 1.8875832159447663e-15,
  "velocity_error_at_estimate_tick": 1.8875832159447663e-15,
  "reference_class": "POST_TURN"
}

## 四格服务与经济

{
  "BLVF_OFF_KEEP": {
    "service": {
      "P0": 0.6000000000000001,
      "Pmax": 1.9000000000000001,
      "required_duration": 2.25,
      "M_service": -0.34999999999999987,
      "margin_note": "zero means reached clipped completion threshold, not positive extra safety margin",
      "NG": 26,
      "GQ_valid_intervals": 26,
      "quality_counts": {
        "PASS": 51,
        "FAIL": 9
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
      "terminal_statuses": {
        "0": "unfinished",
        "1": "unfinished"
      },
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
      "natural_release_boundaries": []
    },
    "components": {
      "completion": 0.0,
      "flow": -0.03124999999999999,
      "late": -0.05624999999999998,
      "effort": -9.40143207405902e-06,
      "terminal": -0.625
    },
    "change": 0.0,
    "net": -0.712509401432074
  },
  "BLVF_ON_KEEP": {
    "service": {
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
        "effort": 1.4348867807052806e-05,
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
      "terminal_statuses": {
        "0": "completed",
        "1": "unfinished"
      },
      "terminal_positions": [
        [
          10.232288253310417,
          9.720683888730079
        ],
        [
          10.232288253310417,
          10.569212026153934
        ],
        [
          2.0,
          2.0
        ]
      ],
      "natural_release_boundaries": []
    },
    "components": {
      "completion": 0.125,
      "flow": -0.02562500000000003,
      "late": -0.039374999999999986,
      "effort": -1.4348867807052806e-05,
      "terminal": -0.375
    },
    "change": 0.0,
    "net": -0.31501434886780705
  },
  "BLVF_ON_SWITCH": {
    "service": {
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
      "terminal_statuses": {
        "0": "unfinished",
        "1": "completed"
      },
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
      "natural_release_boundaries": []
    },
    "components": {
      "completion": 0.1875,
      "flow": -0.02812499999999998,
      "late": -0.046875,
      "effort": -3.4915765090263393e-06,
      "terminal": -0.25
    },
    "change": 0.02,
    "net": -0.157503491576509
  },
  "BLVF_ON_MEMBER_CHANGE": {
    "service": {
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
        "effort": 0.0006122523628948681,
        "terminal": 0.625,
        "change": 0.02
      },
      "G_intervals": [],
      "GQ_intervals": [],
      "terminal_statuses": {
        "0": "unfinished",
        "1": "unfinished"
      },
      "terminal_positions": [
        [
          9.54715677477287,
          9.559247459772442
        ],
        [
          10.712109269778237,
          10.848826231899451
        ],
        [
          8.63979324522924,
          8.075018151318691
        ]
      ],
      "natural_release_boundaries": []
    },
    "components": {
      "completion": 0.0,
      "flow": -0.03124999999999999,
      "late": -0.05624999999999998,
      "effort": -0.0006122523628948681,
      "terminal": -0.625
    },
    "change": 0.02,
    "net": -0.7331122523628949
  }
}

## 调用闭合及证据范围

{
  "status": "PASS",
  "starts": 205,
  "closed": 205,
  "per_cell": {
    "BLVF_OFF_KEEP": 60,
    "BLVF_ON_KEEP": 33,
    "BLVF_ON_SWITCH": 51,
    "BLVF_ON_MEMBER_CHANGE": 61
  },
  "direct": 0,
  "actual_rerun": false
}

原单元内四类审计PASS为历史保存回执引用，未重新执行其科学函数。205次解析记录根据日志重新核对闭合；禁止调用依据原回执、源码路由和保存方法字段，未伪造动态监测回执。

## 解释限制

Original worker complete runtime module-import receipt was never saved: NOT_VERIFIED; no replacement runtime receipt fabricated.
HF KEEP is ATTEMPT_002 RAW accepted offline with missing original terminal memory and some historical objects.
Single deterministic H4 world, fixed-action conditional value evaluation, only KEEP paired; no claim of general unknown-future prediction.
Resource accounting INCOMPLETE, resource compliance NOT_ESTABLISHED, end-to-end speedup NOT_ESTABLISHED.
Original PARTIAL_RESULTS, failure and all original data retained unchanged.

离线CPU、墙钟及计入原8334160 bytes后的受控累计写入见OFFLINE_FINALIZATION.json。未知宿主开销及进程退出尾部不记零；不宣称完整资源合规。完成后停止，不启动后续实验。
