# H4独立目标转向探索实验（ATTEMPT_003）
HF KEEP来源为ATTEMPT_002保存RAW的本次离线核验；其余单元来源为ATTEMPT_003。KEEP未重新计算。

VALID_SEVEN_CELL_EXPLORATORY_RESULT

参数：H3基础世界，T0于D75逆时针转向0.5 rad；使用原始双精度速度，D75位置连续、速度右连续；T1与D60公共信息不变。

| 动作 | H3 HF | H3 CAP | H4 HF | H4 CAP |
|---|---|---|---|---|
| KEEP | -0.3150141073101529 | -0.7125094014320741 | -0.31501434886780705 | -0.7125094014320741 |
| SWITCH | -0.157503491576509 | -0.7325026216050797 | -0.157503491576509 | -0.7325026216050797 |
| MEMBER_CHANGE | -0.7331120450139224 | -0.7330898517001428 | -0.7331122523628949 | -0.7330898517001428 |

H4 CAP完整三格MAE：0.3241721944185299。有效HF/CAP配对子集：{'actions': ['KEEP', 'MEMBER_CHANGE', 'SWITCH'], 'denominator': 3, 'mean_AE': 0.3241721944185299, 'status': 'COMPLETE'}。
H4 HF排序：{'status': 'VALID', 'values': {'KEEP': -0.31501434886780705, 'SWITCH': -0.157503491576509, 'MEMBER_CHANGE': -0.7331122523628949}, 'strict_order': ['SWITCH', 'KEEP', 'MEMBER_CHANGE'], 'exact_best': ['SWITCH'], 'epsilon_best': ['SWITCH'], 'pairwise': {'KEEP-SWITCH': -0.15751085729129805, 'KEEP-MEMBER_CHANGE': 0.41809790349508785, 'SWITCH-MEMBER_CHANGE': 0.5756087607863859}}。
H4 CAP排序与HF regret：{'status': 'VALID', 'values': {'KEEP': -0.7125094014320741, 'SWITCH': -0.7325026216050797, 'MEMBER_CHANGE': -0.7330898517001428}, 'strict_order': ['KEEP', 'SWITCH', 'MEMBER_CHANGE'], 'exact_best': ['KEEP'], 'epsilon_best': ['KEEP'], 'pairwise': {'KEEP-SWITCH': 0.019993220173005644, 'KEEP-MEMBER_CHANGE': 0.020580450268068762, 'SWITCH-MEMBER_CHANGE': 0.0005872300950631182}}；{'KEEP': 0.15751085729129805}。
H3/H4 HF近似最优集合是否冲突：False。

## KEEP专项及共同控制区间

{
  "H3_CAP": -0.7125094014320741,
  "H3_NOCAP": -0.3150141073101529,
  "H3_HF": -0.3150141073101529,
  "NoCapEffect_H3": 0.3974952941219212,
  "NoCapEffect_H4": -1.4688595770584456e-05,
  "EffectDifference": -0.3975099827176918,
  "HF_value_error_status": "VALID_KEEP_PAIR",
  "H4_CAP": -0.7125094014320741,
  "H4_NOCAP": -0.7125240900278447,
  "H4_HF": -0.31501434886780705,
  "H4_CAP_AE": 0.39749505256426704,
  "H4_NOCAP_AE": 0.3975097411600376,
  "H4_Delta_AE": 1.4688595770584456e-05,
  "H3_CAP_AE": 0.3974952941219212,
  "H3_NOCAP_AE": 0.0
}

HF实际冻结响应：{"KEEP": [{"freeze_tick": 80, "target": 0, "assigned": true, "estimate_tick": 80, "last_observation_tick": 80, "belief_velocity": [0.3510330247561484, 0.19177021544167872], "true_velocity": [0.35103302475614784, 0.19177021544168052], "velocity_error": 1.8875832159447663e-15, "control_time_position_prediction_error": 0.0, "propagation_age": 0.0}, {"freeze_tick": 80, "target": 1, "assigned": false, "estimate_tick": 60, "last_observation_tick": null, "belief_velocity": [0.0, 0.0], "true_velocity": [0.0, 0.0], "velocity_error": 0.0, "control_time_position_prediction_error": 0.25, "propagation_age": 1.0}, {"freeze_tick": 100, "target": 0, "assigned": false, "estimate_tick": 93, "last_observation_tick": 93, "belief_velocity": [0.3510330247561484, 0.19177021544167872], "true_velocity": [0.35103302475614784, 0.19177021544168052], "velocity_error": 1.8875832159447663e-15, "control_time_position_prediction_error": 0.0, "propagation_age": 0.35000000000000003}, {"freeze_tick": 100, "target": 1, "assigned": false, "estimate_tick": 60, "last_observation_tick": null, "belief_velocity": [0.0, 0.0], "true_velocity": [0.0, 0.0], "velocity_error": 0.0, "control_time_position_prediction_error": 0.25, "propagation_age": 2.0}], "SWITCH": [{"freeze_tick": 80, "target": 0, "assigned": false, "estimate_tick": 60, "last_observation_tick": 60, "belief_velocity": [0.3999999999999986, 0.0], "true_velocity": [0.35103302475614784, 0.19177021544168052], "velocity_error": 0.19792316740361765, "control_time_position_prediction_error": 0.04948079185090394, "propagation_age": 1.0}, {"freeze_tick": 80, "target": 1, "assigned": true, "estimate_tick": 80, "last_observation_tick": 80, "belief_velocity": [0.0, 0.0], "true_velocity": [0.0, 0.0], "velocity_error": 0.0, "control_time_position_prediction_error": 0.0, "propagation_age": 0.0}, {"freeze_tick": 100, "target": 0, "assigned": false, "estimate_tick": 60, "last_observation_tick": 60, "belief_velocity": [0.3999999999999986, 0.0], "true_velocity": [0.35103302475614784, 0.19177021544168052], "velocity_error": 0.19792316740361765, "control_time_position_prediction_error": 0.41502017277592873, "propagation_age": 2.0}, {"freeze_tick": 100, "target": 1, "assigned": true, "estimate_tick": 100, "last_observation_tick": 100, "belief_velocity": [0.0, 0.0], "true_velocity": [0.0, 0.0], "velocity_error": 0.0, "control_time_position_prediction_error": 0.0, "propagation_age": 0.0}], "MEMBER_CHANGE": [{"freeze_tick": 80, "target": 0, "assigned": true, "estimate_tick": 80, "last_observation_tick": 80, "belief_velocity": [0.3510330247577187, 0.1917702154433485], "true_velocity": [0.35103302475614784, 0.19177021544168052], "velocity_error": 2.2912250771196658e-12, "control_time_position_prediction_error": 6.4047456679787536e-15, "propagation_age": 0.0}, {"freeze_tick": 80, "target": 1, "assigned": false, "estimate_tick": 60, "last_observation_tick": null, "belief_velocity": [0.0, 0.0], "true_velocity": [0.0, 0.0], "velocity_error": 0.0, "control_time_position_prediction_error": 0.25, "propagation_age": 1.0}, {"freeze_tick": 100, "target": 0, "assigned": true, "estimate_tick": 100, "last_observation_tick": 100, "belief_velocity": [0.3510330247563189, 0.19177021544183503], "true_velocity": [0.35103302475614784, 0.19177021544168052], "velocity_error": 2.305323791804756e-13, "control_time_position_prediction_error": 1.2560739669470201e-14, "propagation_age": 0.0}, {"freeze_tick": 100, "target": 1, "assigned": false, "estimate_tick": 60, "last_observation_tick": null, "belief_velocity": [0.0, 0.0], "true_velocity": [0.0, 0.0], "velocity_error": 0.0, "control_time_position_prediction_error": 0.25, "propagation_age": 2.0}]}
运动失配实际证据：{"status": "SUPPORTED_IN_TESTED_CASE", "pre_turn_position_error_mean": 0.0, "post_turn_position_error_mean": 0.36473488657931097, "pre_denominator": 15, "post_denominator": 45, "diagnostic_numerical_threshold": 1e-10, "not_statistical_significance": true}
- H4_HF_KEEP：{"P0": 0.6000000000000001, "Pmax": 2.25, "NG": 33, "effective_service_intervals": 33, "completion_tick": 93, "terminal": {"target": 0, "kind": "completed", "time": 4.65, "tick": 93, "processed_tick": 93, "release_change_cost": 0.0}, "net": -0.31501434886780705, "raw_signed_components": {"completion": 0.125, "flow": -0.02562500000000003, "late": -0.039374999999999986, "effort": -1.4348867807052806e-05, "terminal": -0.375}, "change_cost": 0.0, "positive_cost_ledger": {"completion": 0.125, "flow": 0.02562500000000003, "late": 0.039374999999999986, "effort": 1.4348867807052806e-05, "terminal": 0.375, "change": 0.0}, "resets": [], "assignment_transactions": [{"tick": 60, "before": [{"role": "dual_neg45", "target": 0}, {"role": "dual_pos45", "target": 0}, {"role": "none", "target": null}], "after": [{"role": "dual_neg45", "target": 0}, {"role": "dual_pos45", "target": 0}, {"role": "none", "target": null}], "changes": 0, "cost": 0.0}, {"tick": 80, "before": [{"role": "dual_neg45", "target": 0}, {"role": "dual_pos45", "target": 0}, {"role": "none", "target": null}], "after": [{"role": "dual_neg45", "target": 0}, {"role": "dual_pos45", "target": 0}, {"role": "none", "target": null}], "changes": 0, "cost": 0.0}, {"tick": 100, "before": [{"target": null, "role": "none"}, {"target": null, "role": "none"}, {"role": "none", "target": null}], "after": [{"target": null, "role": "none"}, {"target": null, "role": "none"}, {"role": "none", "target": null}], "changes": 0, "cost": 0.0}], "freeze_mode": "FIXED_ACTION_HOLD"}
- H4_HF_SWITCH：{"P0": 0.0, "Pmax": 1.05, "NG": 21, "effective_service_intervals": 21, "completion_tick": 110, "terminal": {"target": 1, "kind": "completed", "time": 5.5, "tick": 110, "processed_tick": 110, "release_change_cost": 0.0}, "net": -0.157503491576509, "raw_signed_components": {"completion": 0.1875, "flow": -0.02812499999999998, "late": -0.046875, "effort": -3.4915765090263393e-06, "terminal": -0.25}, "change_cost": 0.02, "positive_cost_ledger": {"completion": 0.1875, "flow": 0.02812499999999998, "late": 0.046875, "effort": 3.4915765090263393e-06, "terminal": 0.25, "change": 0.02}, "resets": [], "assignment_transactions": [{"tick": 60, "before": [{"role": "dual_neg45", "target": 0}, {"role": "dual_pos45", "target": 0}, {"role": "none", "target": null}], "after": [{"role": "dual_neg45", "target": 1}, {"role": "dual_pos45", "target": 1}, {"role": "none", "target": null}], "changes": 2, "cost": 0.02}, {"tick": 80, "before": [{"role": "dual_neg45", "target": 1}, {"role": "dual_pos45", "target": 1}, {"role": "none", "target": null}], "after": [{"role": "dual_neg45", "target": 1}, {"role": "dual_pos45", "target": 1}, {"role": "none", "target": null}], "changes": 0, "cost": 0.0}, {"tick": 100, "before": [{"role": "dual_neg45", "target": 1}, {"role": "dual_pos45", "target": 1}, {"role": "none", "target": null}], "after": [{"role": "dual_neg45", "target": 1}, {"role": "dual_pos45", "target": 1}, {"role": "none", "target": null}], "changes": 0, "cost": 0.0}], "freeze_mode": "FIXED_ACTION_HOLD"}
- H4_HF_MEMBER_CHANGE：{"P0": 0.0, "Pmax": 0.0, "NG": 0, "effective_service_intervals": 0, "completion_tick": null, "terminal": {"target": 0, "kind": "unfinished", "time": 6.0, "tick": 120, "processed_tick": 120, "release_change_cost": 0.0}, "net": -0.7331122523628949, "raw_signed_components": {"completion": 0.0, "flow": -0.03124999999999999, "late": -0.05624999999999998, "effort": -0.0006122523628948909, "terminal": -0.625}, "change_cost": 0.02, "positive_cost_ledger": {"completion": 0.0, "flow": 0.03124999999999999, "late": 0.05624999999999998, "effort": 0.0006122523628948909, "terminal": 0.625, "change": 0.02}, "resets": [], "assignment_transactions": [{"tick": 60, "before": [{"role": "dual_neg45", "target": 0}, {"role": "dual_pos45", "target": 0}, {"role": "none", "target": null}], "after": [{"role": "none", "target": null}, {"role": "dual_pos45", "target": 0}, {"role": "dual_neg45", "target": 0}], "changes": 2, "cost": 0.02}, {"tick": 80, "before": [{"role": "none", "target": null}, {"role": "dual_pos45", "target": 0}, {"role": "dual_neg45", "target": 0}], "after": [{"role": "none", "target": null}, {"role": "dual_pos45", "target": 0}, {"role": "dual_neg45", "target": 0}], "changes": 0, "cost": 0.0}, {"tick": 100, "before": [{"role": "none", "target": null}, {"role": "dual_pos45", "target": 0}, {"role": "dual_neg45", "target": 0}], "after": [{"role": "none", "target": null}, {"role": "dual_pos45", "target": 0}, {"role": "dual_neg45", "target": 0}], "changes": 0, "cost": 0.0}], "freeze_mode": "FIXED_ACTION_HOLD"}
- H4_CAP_KEEP：{"P0": 0.6000000000000001, "Pmax": 1.9000000000000001, "NG": 26, "completion_tick": null, "stop_time": 6.0, "value": -0.7125094014320741, "economics": {"completion": 0.0, "flow": 0.03125, "late": 0.056249999999999994, "effort": 9.401432074059017e-06, "terminal": 0.625, "change": 0.0}, "release": "NOT_APPLICABLE: proxy control stop is not Assignment release"}
- H4_CAP_SWITCH：{"P0": 0.0, "Pmax": 0.0, "NG": 0, "completion_tick": null, "stop_time": 6.0, "value": -0.7325026216050797, "economics": {"completion": 0.0, "flow": 0.03125, "late": 0.056249999999999994, "effort": 2.6216050797610976e-06, "terminal": 0.625, "change": 0.02}, "release": "NOT_APPLICABLE: proxy control stop is not Assignment release"}
- H4_CAP_MEMBER_CHANGE：{"P0": 0.0, "Pmax": 0.0, "NG": 0, "completion_tick": null, "stop_time": 6.0, "value": -0.7330898517001428, "economics": {"completion": 0.0, "flow": 0.03125, "late": 0.056249999999999994, "effort": 0.0005898517001428379, "terminal": 0.625, "change": 0.02}, "release": "NOT_APPLICABLE: proxy control stop is not Assignment release"}
- H4_NOCAP_KEEP：{"P0": 0.6000000000000001, "Pmax": 2.1, "NG": 30, "completion_tick": null, "stop_time": 6.0, "value": -0.7125240900278447, "economics": {"completion": 0.0, "flow": 0.03125, "late": 0.056249999999999994, "effort": 2.409002784462572e-05, "terminal": 0.625, "change": 0.0}, "release": "NOT_APPLICABLE: proxy control stop is not Assignment release"}
- H4_H3_HF_KEEP：共同目标tick分母=33；区间=[60, 92]；A/B位置误差=(0.0029988358697523145, 0.0)；A/B速度误差=(0.02998835869751857, 0.0)。
- H4_H3_HF_SWITCH：共同目标tick分母=50；区间=[60, 109]；A/B位置误差=(0.1, 0.1)；A/B速度误差=(0.0, 0.0)。
- H4_H3_HF_MEMBER_CHANGE：共同目标tick分母=60；区间=[60, 119]；A/B位置误差=(0.0016493597287611068, 4.0307282511523643e-13)；A/B速度误差=(0.01649359728447539, 8.411687818281808e-13)。
- H4_H3_CAP_KEEP：共同目标tick分母=60；区间=[60, 119]；A/B位置误差=(0.2735511649344832, 0.25999999999999907)；A/B速度误差=(0.2797923167403608, 0.25999999999999907)。
- H4_H3_CAP_SWITCH：共同目标tick分母=60；区间=[60, 119]；A/B位置误差=(0.25, 0.25)；A/B速度误差=(0.0, 0.0)。
- H4_H3_CAP_MEMBER_CHANGE：共同目标tick分母=60；区间=[60, 119]；A/B位置误差=(0.2735511649344832, 0.25999999999999907)；A/B速度误差=(0.2797923167403608, 0.25999999999999907)。
- H4_H3_NOCAP_KEEP：共同目标tick分母=33；区间=[60, 92]；A/B位置误差=(0.04588218880720227, 0.0)；A/B速度误差=(0.10795809131106418, 0.0)。
- H4_NOCAP_CAP_KEEP：共同目标tick分母=60；区间=[60, 119]；A/B位置误差=(0.16328661310798456, 0.2735511649344832)；A/B速度误差=(0.14844237555271322, 0.2797923167403608)。

## 对科研问题的回答

1. 运动模型失配：D60正确初始状态不包含未来转向。D75真实瞬时速度已转向，D75位置尚仅包含转向前位移，D76开始包含转向后位移。实际预测误差见TRACE及SCIENTIFIC_ANALYSIS；不能把D75位置观测准确当作转向后速度已识别。
2. NoCap在H4 KEEP中的作用：净价值效应=-1.4688595770584456e-05，相对HF绝对误差变化=1.4688595770584456e-05；H3/H4效应差=-0.3975099827176918。结合完成时刻与Pmax评价，不把净价值升高单独解释为改善。
3. HF反馈响应：逐条记录实际生成、可用、消费、接受/拒绝、前后belief及差分参考。PRE_TURN/CROSSES_TURN/POST_TURN分类用于解释速度差分，跨越D75时是两段运动的时间加权平均；无合格参考则保留更新前速度。每个HF TRACE提供第一条measurement>=75及第一条measurement>75的质量有效观测，另有实际冻结误差和后续控制/服务。未新增关闭反馈对照，因此不声称反馈净因果效应已独立识别。
4. 服务及价值变化：逐动作完成、Pmax、重置及终止事件见上表和RAW；HF保留原始带符号账本并提供收益/正成本表达，代理保留原六项账本。各自净价值由原始审计公式核对。
5. H4代理排序误差与HF regret：{'KEEP': 0.15751085729129805}；完整排序与误差分别满足R4必要数据时才报告，不插补。
6. H3/H4真实HF最优动作冲突：False。未重跑H3，历史比较不代表本次验证了H4上的动态R策略。
7. 后续研究启示：本次只为运动模型不确定性、反馈估计响应及服务连续性风险提供案例证据；不据单一转向世界宣称新算法、鲁棒策略或普遍计算优势已经得到验证，也不启动后续算法实验。

## 范围、实际执行与资源限制

{
  "offline_KEEP_acceptance": {
    "status": "ACCEPTED_WITH_LIMITATIONS",
    "SOURCE_EXECUTION": "ATTEMPT_002",
    "SOURCE_COMMIT": "ad719bb0b7d6618878ecea6e6c2682cf38d7e66a",
    "SCIENTIFIC_REEXECUTION": "NO",
    "ORIGINAL_ATTEMPT_STATUS": "BLOCKED_NO_VALID_CELLS",
    "source_files": {
      "D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\ATTEMPT_002\\RAW\\H4_HF_KEEP.json": "f5cdd45b57cd1339d31f79f92bc327114e4b265b8d7bd069258f4c99564541dc",
      "D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\ATTEMPT_002\\RAW\\H4_HF_KEEP_PARTIAL.json": "64c0484f67b2c80e53513d26526c863ed831eec417b5a9fddbd7cb0fab00f31b",
      "D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\ATTEMPT_002\\WORLD_H4.json": "8664163a7b3d1f4f0bf2a7fec6741b33ac62b8cdbfda0da71c137e41a1b8e510",
      "D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\ATTEMPT_002\\EXPERIMENT_CONFIG.json": "04b19c5d0578243174c8c0c81e16d8e09f5e74f2a5db1ec4fb0185ea9883dd3b",
      "D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\ATTEMPT_002\\RESOURCE_EVENTS.jsonl": "0b2c62a20b713d19d8eb2fc022393c9041590613d724eadcfda3af2a619bf538",
      "D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\ATTEMPT_002\\RESOURCE_RECEIPT.json": "8d72362777e1c1a2346b0f64813c004e5fae8e90f7c3484261a019505d18a7d1"
    },
    "world_digest": "6e5d3f2944a8090f5da218420787ebfccbfedd5190d6511e57f299a00ebd8d76",
    "audits": {
      "control_stop_freeze_history_beliefs": {
        "status": "PASS",
        "control_stop_checks": 180,
        "decision_views": [
          {
            "tick": 80,
            "positions": true,
            "assignment": true,
            "active_tasks": true,
            "history_digest": true,
            "belief_replay": true
          },
          {
            "tick": 100,
            "positions": true,
            "assignment": true,
            "active_tasks": true,
            "history_digest": true,
            "belief_replay": true
          }
        ],
        "first_model_endpoint_tick": {
          "0": 61
        }
      },
      "service_geometry_clock_completion": {
        "status": "PASS",
        "checked_intervals": 33
      },
      "physical_economic": {
        "status": "PASS",
        "physical_steps": 60,
        "components": {
          "completion": 0.125,
          "flow": -0.02562500000000003,
          "late": -0.039374999999999986,
          "effort": -1.4348867807052806e-05,
          "terminal": -0.375
        },
        "change_cost": 0.0,
        "net": -0.31501434886780705,
        "exact_sum_of_binary64_increments": "-1487613202716337422611/4722366482869645213696",
        "rounding_residual": "49427/4722366482869645213696",
        "physics_scope": "Displacement, speed and control integral from records; service/feedback separately tested"
      }
    },
    "actual_feedback_consumed": 33,
    "accepted": 33,
    "rejected": 0,
    "terminal_queue": {
      "status": "DERIVED_EMPTY_FROM_ALL_GENERATED_AND_SAVED_CONSUMED_IDENTITIES",
      "remaining_frame_ids": [],
      "no_D120_freeze": true
    },
    "original_resource_counts": {
      "observation_wls": 33,
      "solver": 297
    },
    "resource_calls_started": 330,
    "resource_calls_closed": 330,
    "new_scientific_calls": 0,
    "net": -0.31501434886780705,
    "limitations": [
      "original terminal Branch memory and full terminal histories were not saved; not fabricated",
      "original audit_branch_independent success receipt was not saved; no retrospective claim of that original receipt",
      "core geometry, service clocks, terminal completion/release, controls and economy checked directly from RAW/events/frames and frozen views",
      "terminal pending emptiness derived from generated/consumed identity conservation, not asserted from an absent memory object",
      "prior resource accounting remains INCOMPLETE"
    ]
  },
  "second_attempt": {
    "identity": "STFBS_LITE_TARGET_TURN_EXPLORATION_001_ATTEMPT_002",
    "status": "BLOCKED_NO_VALID_CELLS",
    "receipt_path": "D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\ATTEMPT_002\\RESOURCE_RECEIPT.json",
    "receipt_sha256": "8d72362777e1c1a2346b0f64813c004e5fae8e90f7c3484261a019505d18a7d1",
    "known_cpu_subtotal": 3.578125,
    "recorded_wall_seconds": 309.9345066485257,
    "controlled_logical_write_bytes": 1832855,
    "actual_calls": {
      "observation_wls": 33,
      "solver": 297
    },
    "resource_accounting": "INCOMPLETE"
  },
  "prior_attempt": {
    "identity": "STFBS_LITE_TARGET_TURN_EXPLORATION_001",
    "status": "FAILED_IMPLEMENTATION",
    "resource_receipt_path": "D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\RESOURCE_RECEIPT.json",
    "resource_receipt_sha256": "2b31687008f1b486887757d694af398f191e2c79ce6559f3ff3643b7e12eea18",
    "known_cpu_subtotal": 2.0625,
    "recorded_wall_seconds": 1202.40336491559,
    "controlled_logical_write_bytes": 770866,
    "actual_calls": {
      "observation_wls": 20,
      "solver": 180
    },
    "resource_accounting": "INCOMPLETE"
  },
  "combined_started_cells": 8,
  "combined_valid_cells": 7,
  "combined_actual_calls": {
    "observation_wls": 165,
    "solver": 1485
  },
  "task": "STFBS_LITE_TARGET_TURN_EXPLORATION_001_ATTEMPT_003",
  "CONTINUATION_OF": "STFBS_LITE_TARGET_TURN_EXPLORATION_001",
  "git_head": "ad719bb0b7d6618878ecea6e6c2682cf38d7e66a",
  "entry_sha256": "57514341bed431d0e61f449d61665f3f099e951f8e17088ea5868ec753bab5b2",
  "TURN_WORLD_IDENTITY": "f1760d5f8830d757036eb19dbe0b9e34f82a767fded4a338703d6ea60ab93e05",
  "MINIMAL_VALIDATION_STATUS": "V1_V3_PASS_AND_V4_PASS",
  "HF_STARTED_CELLS": 2,
  "HF_VALID_CELLS": 3,
  "NEW_VALID_HF_CELLS": 2,
  "OFFLINE_ACCEPTED_HF_CELLS": 1,
  "PROXY_STARTED_CELLS": 4,
  "PROXY_VALID_CELLS": 4,
  "TOTAL_STARTED_CELLS": 6,
  "TOTAL_VALID_CELLS": 7,
  "resource_counts": {
    "observation_wls": 112,
    "solver": 1008
  },
  "OBSERVATION_WLS_CALLS": 112,
  "SOLVER_STARTS": 1008,
  "POLICY_WLS_CALLS": 0,
  "R_CALLS": 0,
  "ASSIGNMENT_SOLVER_CALLS": 0,
  "ACTUAL_STEP_CALLS": 0,
  "ACTUAL_WLS_CALLS": 0,
  "RESOURCE_ACCOUNTING": "INCOMPLETE",
  "RESOURCE_COMPLIANCE": "NOT_ESTABLISHED",
  "SCIENTIFIC_DIAGNOSTIC_VALIDITY": "VALID_SEVEN_CELL_EXPLORATORY_RESULT",
  "INDEPENDENT_ACCEPTANCE": "PENDING",
  "fatal": null,
  "reconciliation": {
    "status": "VERIFIED_CONTROLLED_CALL_ACCOUNTING",
    "disk_starts": {
      "observation_wls": 112,
      "solver": 1008
    },
    "runtime_starts": {
      "observation_wls": 112,
      "solver": 1008
    },
    "started": 1120,
    "closed": 1120,
    "failed_calls": 0,
    "source": "MODEL",
    "legacy_ACTUAL_SOLVER_START_used": false,
    "policy_wls_calls": 0,
    "R_calls": 0,
    "assignment_optimization_calls": 0,
    "ACTUAL_STEP_calls": 0,
    "ACTUAL_WLS_calls": 0
  },
  "figures": "GENERATED_FROM_EXISTING_DATA",
  "L3_B_EXPLORATORY_STAGE": "CLOSED",
  "L3_C_EXECUTION_AUTHORIZATION": "NOT_GRANTED",
  "PRODUCTION_ADMISSION": "BLOCKED",
  "HF_state_transactions": {
    "KEEP": {
      "initial_and_hold_transactions": 3,
      "hold_count": 2,
      "terminal_state_transitions": 2,
      "optimization_calls": 0
    },
    "SWITCH": {
      "initial_and_hold_transactions": 3,
      "hold_count": 2,
      "terminal_state_transitions": 2,
      "optimization_calls": 0
    },
    "MEMBER_CHANGE": {
      "initial_and_hold_transactions": 3,
      "hold_count": 2,
      "terminal_state_transitions": 2,
      "optimization_calls": 0
    }
  },
  "limitations": [
    "one deterministic instantaneous direction change, not bounded acceleration",
    "public constant-velocity model intentionally mismatched",
    "HF uses endogenous MODEL observations; proxy control receives fixed D60 beliefs",
    "fixed candidate holds, not dynamic R policy assessment",
    "existing audit-only consumer consistency checks are not additional rollout cells",
    "control prediction errors conditional on actual valid control intervals",
    "NoCap is KEEP only; no full NoCap ranking or regret",
    "host preparation, subprocess and meter tail accounting INCOMPLETE; unknown not zero"
  ],
  "MOTION_MODEL_MISMATCH_FINDINGS": {
    "status": "SUPPORTED_IN_TESTED_CASE",
    "pre_turn_position_error_mean": 0.0,
    "post_turn_position_error_mean": 0.36473488657931097,
    "pre_denominator": 15,
    "post_denominator": 45,
    "diagnostic_numerical_threshold": 1e-10,
    "not_statistical_significance": true
  },
  "NOCAP_EFFECT_FINDINGS": {
    "H3_CAP": -0.7125094014320741,
    "H3_NOCAP": -0.3150141073101529,
    "H3_HF": -0.3150141073101529,
    "NoCapEffect_H3": 0.3974952941219212,
    "NoCapEffect_H4": -1.4688595770584456e-05,
    "EffectDifference": -0.3975099827176918,
    "HF_value_error_status": "VALID_KEEP_PAIR",
    "H4_CAP": -0.7125094014320741,
    "H4_NOCAP": -0.7125240900278447,
    "H4_HF": -0.31501434886780705,
    "H4_CAP_AE": 0.39749505256426704,
    "H4_NOCAP_AE": 0.3975097411600376,
    "H4_Delta_AE": 1.4688595770584456e-05,
    "H3_CAP_AE": 0.3974952941219212,
    "H3_NOCAP_AE": 0.0
  },
  "HF_FEEDBACK_RESPONSE_FINDINGS": {
    "KEEP": [
      {
        "freeze_tick": 80,
        "target": 0,
        "assigned": true,
        "estimate_tick": 80,
        "last_observation_tick": 80,
        "belief_velocity": [
          0.3510330247561484,
          0.19177021544167872
        ],
        "true_velocity": [
          0.35103302475614784,
          0.19177021544168052
        ],
        "velocity_error": 1.8875832159447663e-15,
        "control_time_position_prediction_error": 0.0,
        "propagation_age": 0.0
      },
      {
        "freeze_tick": 80,
        "target": 1,
        "assigned": false,
        "estimate_tick": 60,
        "last_observation_tick": null,
        "belief_velocity": [
          0.0,
          0.0
        ],
        "true_velocity": [
          0.0,
          0.0
        ],
        "velocity_error": 0.0,
        "control_time_position_prediction_error": 0.25,
        "propagation_age": 1.0
      },
      {
        "freeze_tick": 100,
        "target": 0,
        "assigned": false,
        "estimate_tick": 93,
        "last_observation_tick": 93,
        "belief_velocity": [
          0.3510330247561484,
          0.19177021544167872
        ],
        "true_velocity": [
          0.35103302475614784,
          0.19177021544168052
        ],
        "velocity_error": 1.8875832159447663e-15,
        "control_time_position_prediction_error": 0.0,
        "propagation_age": 0.35000000000000003
      },
      {
        "freeze_tick": 100,
        "target": 1,
        "assigned": false,
        "estimate_tick": 60,
        "last_observation_tick": null,
        "belief_velocity": [
          0.0,
          0.0
        ],
        "true_velocity": [
          0.0,
          0.0
        ],
        "velocity_error": 0.0,
        "control_time_position_prediction_error": 0.25,
        "propagation_age": 2.0
      }
    ],
    "SWITCH": [
      {
        "freeze_tick": 80,
        "target": 0,
        "assigned": false,
        "estimate_tick": 60,
        "last_observation_tick": 60,
        "belief_velocity": [
          0.3999999999999986,
          0.0
        ],
        "true_velocity": [
          0.35103302475614784,
          0.19177021544168052
        ],
        "velocity_error": 0.19792316740361765,
        "control_time_position_prediction_error": 0.04948079185090394,
        "propagation_age": 1.0
      },
      {
        "freeze_tick": 80,
        "target": 1,
        "assigned": true,
        "estimate_tick": 80,
        "last_observation_tick": 80,
        "belief_velocity": [
          0.0,
          0.0
        ],
        "true_velocity": [
          0.0,
          0.0
        ],
        "velocity_error": 0.0,
        "control_time_position_prediction_error": 0.0,
        "propagation_age": 0.0
      },
      {
        "freeze_tick": 100,
        "target": 0,
        "assigned": false,
        "estimate_tick": 60,
        "last_observation_tick": 60,
        "belief_velocity": [
          0.3999999999999986,
          0.0
        ],
        "true_velocity": [
          0.35103302475614784,
          0.19177021544168052
        ],
        "velocity_error": 0.19792316740361765,
        "control_time_position_prediction_error": 0.41502017277592873,
        "propagation_age": 2.0
      },
      {
        "freeze_tick": 100,
        "target": 1,
        "assigned": true,
        "estimate_tick": 100,
        "last_observation_tick": 100,
        "belief_velocity": [
          0.0,
          0.0
        ],
        "true_velocity": [
          0.0,
          0.0
        ],
        "velocity_error": 0.0,
        "control_time_position_prediction_error": 0.0,
        "propagation_age": 0.0
      }
    ],
    "MEMBER_CHANGE": [
      {
        "freeze_tick": 80,
        "target": 0,
        "assigned": true,
        "estimate_tick": 80,
        "last_observation_tick": 80,
        "belief_velocity": [
          0.3510330247577187,
          0.1917702154433485
        ],
        "true_velocity": [
          0.35103302475614784,
          0.19177021544168052
        ],
        "velocity_error": 2.2912250771196658e-12,
        "control_time_position_prediction_error": 6.4047456679787536e-15,
        "propagation_age": 0.0
      },
      {
        "freeze_tick": 80,
        "target": 1,
        "assigned": false,
        "estimate_tick": 60,
        "last_observation_tick": null,
        "belief_velocity": [
          0.0,
          0.0
        ],
        "true_velocity": [
          0.0,
          0.0
        ],
        "velocity_error": 0.0,
        "control_time_position_prediction_error": 0.25,
        "propagation_age": 1.0
      },
      {
        "freeze_tick": 100,
        "target": 0,
        "assigned": true,
        "estimate_tick": 100,
        "last_observation_tick": 100,
        "belief_velocity": [
          0.3510330247563189,
          0.19177021544183503
        ],
        "true_velocity": [
          0.35103302475614784,
          0.19177021544168052
        ],
        "velocity_error": 2.305323791804756e-13,
        "control_time_position_prediction_error": 1.2560739669470201e-14,
        "propagation_age": 0.0
      },
      {
        "freeze_tick": 100,
        "target": 1,
        "assigned": false,
        "estimate_tick": 60,
        "last_observation_tick": null,
        "belief_velocity": [
          0.0,
          0.0
        ],
        "true_velocity": [
          0.0,
          0.0
        ],
        "velocity_error": 0.0,
        "control_time_position_prediction_error": 0.25,
        "propagation_age": 2.0
      }
    ]
  },
  "ACTION_RANKING_FINDINGS": {
    "H4_HF": {
      "status": "VALID",
      "values": {
        "KEEP": -0.31501434886780705,
        "SWITCH": -0.157503491576509,
        "MEMBER_CHANGE": -0.7331122523628949
      },
      "strict_order": [
        "SWITCH",
        "KEEP",
        "MEMBER_CHANGE"
      ],
      "exact_best": [
        "SWITCH"
      ],
      "epsilon_best": [
        "SWITCH"
      ],
      "pairwise": {
        "KEEP-SWITCH": -0.15751085729129805,
        "KEEP-MEMBER_CHANGE": 0.41809790349508785,
        "SWITCH-MEMBER_CHANGE": 0.5756087607863859
      }
    },
    "H4_CAP": {
      "status": "VALID",
      "values": {
        "KEEP": -0.7125094014320741,
        "SWITCH": -0.7325026216050797,
        "MEMBER_CHANGE": -0.7330898517001428
      },
      "strict_order": [
        "KEEP",
        "SWITCH",
        "MEMBER_CHANGE"
      ],
      "exact_best": [
        "KEEP"
      ],
      "epsilon_best": [
        "KEEP"
      ],
      "pairwise": {
        "KEEP-SWITCH": 0.019993220173005644,
        "KEEP-MEMBER_CHANGE": 0.020580450268068762,
        "SWITCH-MEMBER_CHANGE": 0.0005872300950631182
      }
    },
    "H3_H4_optimum_conflict": false,
    "HF_regret": {
      "KEEP": 0.15751085729129805
    }
  },
  "HF_source_execution": {
    "KEEP": "ATTEMPT_002_OFFLINE_ACCEPTED",
    "SWITCH": "ATTEMPT_003",
    "MEMBER_CHANGE": "ATTEMPT_003"
  }
}

所有有效单元原始数据均保留。失败或缺失按指标分别限制解释，不用历史H3冒充H4，不增加单元或自动重试。控制停止后不生成预测记录；配对误差按目标和同tick的共同有效范围去重，完整价值与终端状态不截断至该范围。

本任务仅新增专属目录内容，保留全部历史资产、已关闭L3-B及生产准入限制。资源最终退出回执见RESOURCE_RECEIPT.json；累计逻辑写入包括受控追加、覆盖及最终回执，未测资源不记零。