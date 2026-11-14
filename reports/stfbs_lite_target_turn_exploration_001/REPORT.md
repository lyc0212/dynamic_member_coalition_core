# H4独立目标转向探索实验

BLOCKED_NO_VALID_CELLS

参数：H3基础世界，T0于D75逆时针转向0.5 rad；使用原始双精度速度，D75位置连续、速度右连续；T1与D60公共信息不变。

| 动作 | H3 HF | H3 CAP | H4 HF | H4 CAP |
|---|---|---|---|---|
| KEEP | -0.3150141073101529 | -0.7125094014320741 | None | None |
| SWITCH | -0.157503491576509 | -0.7325026216050797 | None | None |
| MEMBER_CHANGE | -0.7331120450139224 | -0.7330898517001428 | None | None |

H4 CAP完整三格MAE：None。有效HF/CAP配对子集：{'actions': [], 'denominator': 0, 'mean_AE': None, 'status': 'PARTIAL_NOT_FULL_MAE'}。
H4 HF排序：{'status': 'NOT_IDENTIFIABLE', 'available': {}}。
H4 CAP排序与HF regret：{'status': 'NOT_IDENTIFIABLE', 'available': {}}；None。
H3/H4 HF近似最优集合是否冲突：None。

## KEEP专项及共同控制区间

{
  "H3_CAP": -0.7125094014320741,
  "H3_NOCAP": -0.3150141073101529,
  "H3_HF": -0.3150141073101529,
  "NoCapEffect_H3": 0.3974952941219212,
  "NoCapEffect_H4": null,
  "EffectDifference": null,
  "HF_value_error_status": "NOT_IDENTIFIABLE"
}

HF实际冻结响应：{}
运动失配实际证据：{"status": "NOT_IDENTIFIABLE", "pre_turn_position_error_mean": null, "post_turn_position_error_mean": null, "pre_denominator": 0, "post_denominator": 0, "diagnostic_numerical_threshold": 1e-10, "not_statistical_significance": true}

## 对科研问题的回答

1. 运动模型失配：D60正确初始状态不包含未来转向。D75真实瞬时速度已转向，D75位置尚仅包含转向前位移，D76开始包含转向后位移。实际预测误差见TRACE及SCIENTIFIC_ANALYSIS；不能把D75位置观测准确当作转向后速度已识别。
2. NoCap在H4 KEEP中的作用：净价值效应=None，相对HF绝对误差变化=NOT_IDENTIFIABLE；H3/H4效应差=None。结合完成时刻与Pmax评价，不把净价值升高单独解释为改善。
3. HF反馈响应：逐条记录实际生成、可用、消费、接受/拒绝、前后belief及差分参考。PRE_TURN/CROSSES_TURN/POST_TURN分类用于解释速度差分，跨越D75时是两段运动的时间加权平均；无合格参考则保留更新前速度。每个HF TRACE提供第一条measurement>=75及第一条measurement>75的质量有效观测，另有实际冻结误差和后续控制/服务。未新增关闭反馈对照，因此不声称反馈净因果效应已独立识别。
4. 服务及价值变化：逐动作完成、Pmax、重置及终止事件见上表和RAW；HF保留原始带符号账本并提供收益/正成本表达，代理保留原六项账本。各自净价值由原始审计公式核对。
5. H4代理排序误差与HF regret：None；完整排序与误差分别满足R4必要数据时才报告，不插补。
6. H3/H4真实HF最优动作冲突：None。未重跑H3，历史比较不代表本次验证了H4上的动态R策略。
7. 后续研究启示：本次只为运动模型不确定性、反馈估计响应及服务连续性风险提供案例证据；不据单一转向世界宣称新算法、鲁棒策略或普遍计算优势已经得到验证，也不启动后续算法实验。

## 范围、实际执行与资源限制

{
  "task": "STFBS_LITE_TARGET_TURN_EXPLORATION_001",
  "git_head": "953cc41a5ead22f7f3058ae18126c3b57d7434c7",
  "entry_sha256": "e5874b7ddc290347d57c348f09d2a3ccd652e476f39bf230ff4bd0bbb4a50c67",
  "TURN_WORLD_IDENTITY": "f1760d5f8830d757036eb19dbe0b9e34f82a767fded4a338703d6ea60ab93e05",
  "MINIMAL_VALIDATION_STATUS": "V1_V3_PASS_V4_PARTIAL_OR_FAILED",
  "HF_STARTED_CELLS": 1,
  "HF_VALID_CELLS": 0,
  "PROXY_STARTED_CELLS": 0,
  "PROXY_VALID_CELLS": 0,
  "TOTAL_STARTED_CELLS": 1,
  "TOTAL_VALID_CELLS": 0,
  "resource_counts": {
    "observation_wls": 20,
    "solver": 180
  },
  "OBSERVATION_WLS_CALLS": 20,
  "SOLVER_STARTS": 180,
  "POLICY_WLS_CALLS": 0,
  "R_CALLS": 0,
  "ASSIGNMENT_SOLVER_CALLS": 0,
  "ACTUAL_STEP_CALLS": 0,
  "ACTUAL_WLS_CALLS": 0,
  "RESOURCE_ACCOUNTING": "INCOMPLETE",
  "RESOURCE_COMPLIANCE": "NOT_ESTABLISHED",
  "SCIENTIFIC_DIAGNOSTIC_VALIDITY": "BLOCKED_NO_VALID_CELLS",
  "INDEPENDENT_ACCEPTANCE": "PENDING",
  "fatal": {
    "type": "NameError",
    "message": "name 'DT' is not defined",
    "traceback": "Traceback (most recent call last):\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\turn_entry.py\", line 411, in worker\n    for action in ACTIONS:run_hf(ctx,action)\n                          ~~~~~~^^^^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\turn_entry.py\", line 249, in run_hf\n    branch=ctx['Branch'](copy.deepcopy(ctx['view']),copy.deepcopy(ctx['seed']),copy.deepcopy(ctx['model']),name,budget);actions=copy.deepcopy(next(c['actions'] for c in ctx['candidates'] if c['kind']==action));result=branch.fixed_run(actions);w.json('RAW/'+name+'.json',plain(result))\n                                                                                                                                                                                                                         ~~~~~~~~~~~~~~~~^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\turn_entry.py\", line 153, in fixed_run\n    v=self.policy_view();self.decisions.append(dict(mode='FIXED_ACTION_HOLD',optimization_called=False,view=copy.deepcopy(v)));before=branch_physical(self);hbefore=stripped_history(self);old_first={j:None if self.segment(j) is None else self.segment(j)['first_fusion_tick'] for j in self.targets};current=copy.deepcopy(self.actions);self.assign(current)\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\turn_entry.py\", line 147, in policy_view\n    self.consumer._bindings=bindings;before=branch_physical(self);v=super().policy_view();require(typed(branch_physical(self))==typed(before),'FREEZE_PHYSICAL_SERVICE_CHANGED');return v\n                                                                    ~~~~~~~~~~~~~~~~~~~^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\model_h4.py\", line 290, in policy_view\n    self.frozen = self.consumer.freeze(self.tick)\n                  ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\turn_entry.py\", line 99, in freeze\n    def freeze(self,tick):self._ordinal=0;return freeze_fn(self,tick)\n                                                 ~~~~~~~~~^^^^^^^^^^^\n  File \"D:\\1st\\dynamic_member_coalition_core\\reports\\stfbs_lite_target_turn_exploration_001\\consumer_freeze_observer.py\", line 25, in recorded_freeze\n    velocity = [(x - y) / ((t - s) * DT) for x, y in zip(p, q)]\n                                     ^^\nNameError: name 'DT' is not defined\n"
  },
  "reconciliation": {
    "status": "VERIFIED_CONTROLLED_CALL_ACCOUNTING",
    "disk_starts": {
      "observation_wls": 20,
      "solver": 180
    },
    "runtime_starts": {
      "observation_wls": 20,
      "solver": 180
    },
    "started": 200,
    "closed": 200,
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
  "HF_state_transactions": {},
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
    "status": "NOT_IDENTIFIABLE",
    "pre_turn_position_error_mean": null,
    "post_turn_position_error_mean": null,
    "pre_denominator": 0,
    "post_denominator": 0,
    "diagnostic_numerical_threshold": 1e-10,
    "not_statistical_significance": true
  },
  "NOCAP_EFFECT_FINDINGS": {
    "H3_CAP": -0.7125094014320741,
    "H3_NOCAP": -0.3150141073101529,
    "H3_HF": -0.3150141073101529,
    "NoCapEffect_H3": 0.3974952941219212,
    "NoCapEffect_H4": null,
    "EffectDifference": null,
    "HF_value_error_status": "NOT_IDENTIFIABLE"
  },
  "HF_FEEDBACK_RESPONSE_FINDINGS": {},
  "ACTION_RANKING_FINDINGS": {
    "H4_HF": {
      "status": "NOT_IDENTIFIABLE",
      "available": {}
    },
    "H4_CAP": {
      "status": "NOT_IDENTIFIABLE",
      "available": {}
    },
    "H3_H4_optimum_conflict": null,
    "HF_regret": null
  }
}

所有有效单元原始数据均保留。失败或缺失按指标分别限制解释，不用历史H3冒充H4，不增加单元或自动重试。控制停止后不生成预测记录；配对误差按目标和同tick的共同有效范围去重，完整价值与终端状态不截断至该范围。

本任务仅新增专属目录内容，保留全部历史资产、已关闭L3-B及生产准入限制。资源最终退出回执见RESOURCE_RECEIPT.json；累计逻辑写入包括受控追加、覆盖及最终回执，未测资源不记零。