# 任务停止报告

{
  "task_id": "STFBS_LITE_ACTUAL_FULL_EPISODE_COUNTERFACTUAL_001",
  "FINAL_TASK_STATUS": "LOCAL_DEV_ACTUAL_FULL_EPISODE_THREE_ACTION_INCOMPLETE",
  "G0_STATUS": "PASS",
  "FULL_SWITCH_STATUS": "FAILED_OR_INCOMPLETE",
  "FULL_KEEP_STATUS": "NOT_STARTED",
  "FULL_MEMBER_CHANGE_STATUS": "NOT_STARTED",
  "G4_STATUS": "NOT_EXECUTED",
  "HISTORICAL_CASE_REPRODUCTION": "NOT_EXECUTED",
  "COMMON_D60_PREFIX_EQUIVALENCE": "NOT_COMPLETED",
  "NEW_ACTUAL_MATRIX_INTERNAL_VALIDITY": "INCOMPLETE",
  "ORIGINAL_COUNTERFACTUAL_STATUS": "INCOMPLETE",
  "NO_CHANGE_COST_REVALUATION_STATUS": "INCOMPLETE",
  "FOUR_WORLD_AUXILIARY_MATRIX_STATUS": "INCOMPLETE",
  "FEE_SENSITIVITY_STATUS": "INCOMPLETE",
  "FULL_DELIVERABLE_COMPLETE": false,
  "VALID_ACTUAL_CELLS": 0,
  "STARTED_ATTEMPTS": 0,
  "CONSUMED_ATTEMPTS": 0,
  "UNSTARTED_BRANCHES": 3,
  "branches": [
    {
      "name": "FULL_SWITCH",
      "action": "SWITCH",
      "attempt_id": "AFC001_SWITCH_001",
      "valid": false,
      "status": "FAILED_OR_INCOMPLETE",
      "returncode": 1,
      "stdout": "",
      "stderr": "Traceback (most recent call last):\n  File \"D:\\1st\\stfbs_lite_actual_full_episode_counterfactual_001_0a5e0ff09fee4d0396baf445aa47bc58\\FULL_SWITCH\\outer_controller.py\", line 1, in <module>\n    from common import *\nModuleNotFoundError: No module named 'common'\n",
      "inner": null,
      "outer": null,
      "counts": null,
      "economic": null
    }
  ],
  "error": {
    "type": "RuntimeError",
    "message": "BRANCH_FAILED/FULL_SWITCH",
    "traceback": "Traceback (most recent call last):\n  File \"D:\\1st\\stfbs_lite_actual_full_episode_counterfactual_001_0a5e0ff09fee4d0396baf445aa47bc58\\run_task.py\", line 123, in <module>\n    rows.append(report);print('SCIENCE_FINISH',b['name'],report['status'],flush=True);need(ok,'BRANCH_FAILED/'+b['name'])\n                                                                                      ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"D:\\1st\\stfbs_lite_actual_full_episode_counterfactual_001_0a5e0ff09fee4d0396baf445aa47bc58\\run_task.py\", line 11, in need\n    if not v:raise RuntimeError(m)\n             ^^^^^^^^^^^^^^^^^^^^^\nRuntimeError: BRANCH_FAILED/FULL_SWITCH\n",
    "stage": "SCIENCE"
  },
  "faults": [],
  "final_faults": [],
  "PROCESS_EXIT_STATUS": "NOT_CONFIRMED",
  "PRODUCTION_SOURCE_MODIFIED": false,
  "OLD_ACTUAL_MODEL_CALIBRATION_RESUMED": false,
  "OLD_CONSUMED_ATTEMPT_RETRIED": false,
  "EXECUTION_CHANGE_COST": 0.01,
  "ZERO_CHANGE_COST_CLOSED_LOOP_EXECUTED": false,
  "H1_H2_H3_RERUN": false,
  "ADDITIONAL_SCIENTIFIC_ATTEMPTS": 0,
  "AUTOMATIC_RETRY": false,
  "PRODUCTION_ADMISSION": "BLOCKED",
  "RESOURCE_USAGE": {
    "controller_cpu": 2.9375,
    "auxiliary_cpu": 0.0,
    "wall": 5.2028285000014876,
    "work_storage": 2003351,
    "archive_storage": 0,
    "total_storage": 2003351,
    "public_storage": 953944,
    "G4_cpu": 0.640625,
    "G4_wall": 0.640991699998267
  },
  "RESOURCE_ACCEPTANCE": "PASS"
}