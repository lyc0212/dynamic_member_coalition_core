# ACTUAL_COUNTERFACTUAL_001_V1_2

{
  "task_id": "STFBS_LITE_ACTUAL_COUNTERFACTUAL_001",
  "continuation": "ACTUAL_COUNTERFACTUAL_001_V1_2",
  "status": "LOCAL_DEV_ACTUAL_THREE_ACTION_COUNTERFACTUAL_INCOMPLETE",
  "execution_admission": "NOT_PASSED",
  "valid_new_cells": 0,
  "scientific_attempts_consumed": 0,
  "branches_not_started": 3,
  "branches": [],
  "error": {
    "type": "ModuleNotFoundError",
    "message": "No module named 'numpy'",
    "traceback": "Traceback (most recent call last):\n  File \"D:\\1st\\stfbs_lite_actual_counterfactual_001_db475b139f2c4075a7e59e2ff4f0f1eb\\run_task_impl.py\", line 83, in <module>\n    g0=prepare()\n  File \"D:\\1st\\stfbs_lite_actual_counterfactual_001_db475b139f2c4075a7e59e2ff4f0f1eb\\task_support.py\", line 16, in prepare\n    from research.non_oracle.stfbs_lite_actual_recovery import recover_actual_cut\n  File \"D:\\1st\\dynamic_member_coalition_core\\research\\non_oracle\\stfbs_lite_actual_recovery.py\", line 11, in <module>\n    from pursuit_v2.service import ServiceState\n  File \"D:\\1st\\dynamic_member_coalition_core\\pursuit_v2\\__init__.py\", line 3, in <module>\n    from .types import Assignment, Scenario, Target\n  File \"D:\\1st\\dynamic_member_coalition_core\\pursuit_v2\\types.py\", line 7, in <module>\n    import numpy as np\nModuleNotFoundError: No module named 'numpy'\n"
  },
  "precheck_receipt": null,
  "parent_cpu_ticks": 9843750,
  "aux_cpu_ticks": 156250,
  "wall_seconds": 1.068293199999971,
  "faults": [],
  "final_faults": [
    "EXECUTION_FREEZE_ABSENT"
  ],
  "retry": false,
  "h1_reused_cells": 0,
  "actual_run": false,
  "h1_rerun": false,
  "analysis": null,
  "G0_STATUS": "FAIL",
  "G1_STATUS": "NOT_PASSED",
  "G2_STATUS": "NOT_COMPLETED",
  "G3_STATUS": "NOT_COMPLETED",
  "G4_STATUS": "NOT_COMPLETED",
  "G4_CHANGE_COST_ANALYSIS": "INCOMPLETE",
  "V1_2_DELIVERABLE_COMPLETE": false,
  "SWITCH_REFERENCE_MODE": "MODEL_SWITCH_REPLAY_REQUIRED",
  "ORIGINAL_COUNTERFACTUAL_STATUS": "INCOMPLETE",
  "VALID_ACTUAL_CELLS": 0,
  "STARTED_ATTEMPTS": 0,
  "CONSUMED_ATTEMPTS": 0,
  "calibration_comparison_resource_usage": null,
  "production_admission": "BLOCKED",
  "science_scope": "One historical actual world, fixed D60, three initial actions, same later A2-R; no zero-fee closed-loop",
  "final_summary_resource_usage": {
    "cpu_ticks": 2031250,
    "cpu_seconds": 0.203125,
    "wall_seconds": 0.23074410000117496,
    "total_wall_seconds": 1.1082072000008338,
    "storage_bytes": 1550698
  },
  "all_started_processes_exit_confirmed": true
}