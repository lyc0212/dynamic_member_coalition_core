# EXTENSION_004_CONTINUATION_001

{
  "task_id": "STFBS_LITE_LOCAL_DEV_H2_H3_EXTENSION_004",
  "continuation": "EXTENSION_004_CONTINUATION_001",
  "status": "LOCAL_DEV_D60_H2_H3_VALUE_MATRIX_INCOMPLETE",
  "S1_S4": "PASS",
  "valid_new_cells": 0,
  "scientific_attempts_consumed": 1,
  "branches_not_started": 5,
  "branches": [
    {
      "name": "H2_KEEP",
      "run_id": "EXT004_H2_KEEP_RUN_001",
      "attempt_id": "EXT004_H2_KEEP_001",
      "branch_id": "EXT004_H2_KEEP_BRANCH_001",
      "valid_cell_candidate": false,
      "status": "FAILED_OR_INCOMPLETE",
      "returncode": 1,
      "stdout": "{\"status\": \"FAIL_OR_INCOMPLETE\", \"parent_start_calls\": 1, \"parent_exit\": 1}\n",
      "stderr": "",
      "outer": {
        "actions": [
          {
            "elapsed": 1269.3477347000007,
            "fallback": false,
            "kind": "JOB_CLOSE",
            "result": "SUCCEEDED"
          }
        ],
        "approval_sha256": "9794dbdd384ff4d68fd0d818a22d370ff10f592f3d7d9db7e045bac0e8457558",
        "attempt_id": "EXT004_H2_KEEP_001",
        "elapsed_seconds": 1269.3477625000005,
        "ended_utc": "2026-11-13T10:02:43.302344+00:00",
        "errors": [],
        "final_outer_accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 609218750,
          "ThisPeriodTotalUserTime": 11486718750,
          "TotalKernelTime": 609218750,
          "TotalPageFaultCount": 10905538,
          "TotalProcesses": 8,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 11486718750,
          "cpu": 1209.59375
        },
        "handle_waits": [
          {
            "pid": 16652,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 28828,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 18120,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 26256,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 29636,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 18952,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 13500,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 28348,
            "remedial_termination_attempted": false,
            "wait_status": 0
          }
        ],
        "identities": [
          {
            "creation_ticks": 134390364939574259,
            "member": true,
            "pid": 16652,
            "role": "LOCAL_DEV_PARENT_SUSPENDED"
          },
          {
            "creation_ticks": 134390364939574259,
            "member": true,
            "pid": 16652,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390364939615856,
            "member": true,
            "pid": 28828,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390364942479139,
            "member": true,
            "pid": 18120,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390364942551985,
            "member": true,
            "pid": 26256,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390364942756242,
            "member": true,
            "pid": 29636,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390364942812979,
            "member": true,
            "pid": 18952,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390364945563340,
            "member": true,
            "pid": 13500,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390364945635965,
            "member": true,
            "pid": 28348,
            "role": "RETAINED_OUTER_MEMBER"
          }
        ],
        "job_handle_diagnostic": 496,
        "job_handle_state": "CLOSED",
        "outer_wall_seconds": 1560,
        "parent_exit_code": 1,
        "parent_start_calls": 1,
        "parent_wait_status": 0,
        "process_tree_exit_confirmed": true,
        "production_admission": "RUN_ADMISSION_BLOCKED",
        "run_id": "EXT004_H2_KEEP_RUN_001",
        "started_utc": "2026-11-13T09:41:33.954586+00:00",
        "status": "FAIL_OR_INCOMPLETE",
        "timed_out": false
      },
      "inner": {
        "accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 555312500,
          "ThisPeriodTotalUserTime": 11444687500,
          "TotalKernelTime": 555312500,
          "TotalPageFaultCount": 10859043,
          "TotalProcesses": 4,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 11444687500,
          "cpu": 1200.0
        },
        "accounting_status": "FINAL_VALID",
        "active_processes_final": 0,
        "attempt_identity": "EXT004_H2_KEEP_001",
        "cpu_limit_ticks": 12000000000,
        "cpu_overshoot_ticks": 0,
        "cpu_scope": "WHOLE_JOB",
        "cpu_semantics": "TOTAL_CPU_SECONDS",
        "cpu_ticks_at_trigger": 12000000000,
        "errors": [],
        "events": [
          "GUARD_CONFIGURED",
          "WORKER_CONTAINED",
          "WORKER_RESUMED",
          "RUNNING_MONITORED",
          "STOP_REQUESTED",
          "TERMINATE_JOB_RESULT",
          "PROCESS_TREE_EXIT_CONFIRMED",
          "FINAL_ACCOUNTING"
        ],
        "evidence_completeness_status": "COMPLETE_IN_MEMORY",
        "execution_entry": "RUN_MONITORED",
        "fallback_close_attempted": false,
        "fallback_close_error_if_any": null,
        "fallback_close_result": null,
        "final_cpu_ticks": 12000000000,
        "job_cleanup_status": "PASS",
        "job_handle_state": "JOB_HANDLE_CLOSED",
        "last_valid_cpu_sample": {
          "accounting": {
            "ActiveProcesses": 0,
            "ThisPeriodTotalKernelTime": 555312500,
            "ThisPeriodTotalUserTime": 11444687500,
            "TotalKernelTime": 555312500,
            "TotalPageFaultCount": 10859043,
            "TotalProcesses": 4,
            "TotalTerminatedProcesses": 0,
            "TotalUserTime": 11444687500,
            "cpu": 1200.0
          },
          "active_processes": 0,
          "cpu_ticks": 12000000000,
          "wall_elapsed": 1269.0051583000004
        },
        "last_valid_cpu_ticks": 12000000000,
        "last_valid_wall_sample": 1269.0054136999997,
        "original_termination_error": null,
        "os_termination_cause": "OS_TERMINATION_CAUSE_UNVERIFIED",
        "overshoot_bound": "NOT_PROVEN",
        "process_tree_status": "PROCESS_TREE_EXIT_CONFIRMED",
        "production_run_admission": "BLOCKED",
        "receipt_integrity_status": "NOT_PERSISTED",
        "remaining_active_processes_if_known": 0,
        "samples": [
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11438281250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10854422,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11438281250,
              "cpu": 1199.359375
            },
            "active_processes": 2,
            "cpu_ticks": 11993593750,
            "wall_elapsed": 1268.3623932
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11438437500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10854422,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11438437500,
              "cpu": 1199.375
            },
            "active_processes": 2,
            "cpu_ticks": 11993750000,
            "wall_elapsed": 1268.3730895999997
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11438593750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10854422,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11438593750,
              "cpu": 1199.390625
            },
            "active_processes": 2,
            "cpu_ticks": 11993906250,
            "wall_elapsed": 1268.3833882999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11438750000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10854422,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11438750000,
              "cpu": 1199.40625
            },
            "active_processes": 2,
            "cpu_ticks": 11994062500,
            "wall_elapsed": 1268.3941308000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11438750000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11438750000,
              "cpu": 1199.40625
            },
            "active_processes": 2,
            "cpu_ticks": 11994062500,
            "wall_elapsed": 1268.4045588
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11438906250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11438906250,
              "cpu": 1199.421875
            },
            "active_processes": 2,
            "cpu_ticks": 11994218750,
            "wall_elapsed": 1268.4150712
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11439062500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11439062500,
              "cpu": 1199.4375
            },
            "active_processes": 2,
            "cpu_ticks": 11994375000,
            "wall_elapsed": 1268.4256782000002
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11439062500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11439062500,
              "cpu": 1199.4375
            },
            "active_processes": 2,
            "cpu_ticks": 11994375000,
            "wall_elapsed": 1268.4359798000005
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11439218750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11439218750,
              "cpu": 1199.453125
            },
            "active_processes": 2,
            "cpu_ticks": 11994531250,
            "wall_elapsed": 1268.4466067000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11439375000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11439375000,
              "cpu": 1199.46875
            },
            "active_processes": 2,
            "cpu_ticks": 11994687500,
            "wall_elapsed": 1268.4570865000005
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11439375000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11439375000,
              "cpu": 1199.46875
            },
            "active_processes": 2,
            "cpu_ticks": 11994687500,
            "wall_elapsed": 1268.4676600000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11439531250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11439531250,
              "cpu": 1199.484375
            },
            "active_processes": 2,
            "cpu_ticks": 11994843750,
            "wall_elapsed": 1268.4784323000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11439687500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11439687500,
              "cpu": 1199.5
            },
            "active_processes": 2,
            "cpu_ticks": 11995000000,
            "wall_elapsed": 1268.4893122000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11439687500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11439687500,
              "cpu": 1199.5
            },
            "active_processes": 2,
            "cpu_ticks": 11995000000,
            "wall_elapsed": 1268.4999994999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11439843750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11439843750,
              "cpu": 1199.515625
            },
            "active_processes": 2,
            "cpu_ticks": 11995156250,
            "wall_elapsed": 1268.5104118
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440000000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855192,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440000000,
              "cpu": 1199.53125
            },
            "active_processes": 2,
            "cpu_ticks": 11995312500,
            "wall_elapsed": 1268.5211000999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440000000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855962,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440000000,
              "cpu": 1199.53125
            },
            "active_processes": 2,
            "cpu_ticks": 11995312500,
            "wall_elapsed": 1268.5318108000001
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440156250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855962,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440156250,
              "cpu": 1199.546875
            },
            "active_processes": 2,
            "cpu_ticks": 11995468750,
            "wall_elapsed": 1268.5423454000002
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440312500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855962,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440312500,
              "cpu": 1199.5625
            },
            "active_processes": 2,
            "cpu_ticks": 11995625000,
            "wall_elapsed": 1268.5531668000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440312500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855962,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440312500,
              "cpu": 1199.5625
            },
            "active_processes": 2,
            "cpu_ticks": 11995625000,
            "wall_elapsed": 1268.5638358000006
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440468750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855962,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440468750,
              "cpu": 1199.578125
            },
            "active_processes": 2,
            "cpu_ticks": 11995781250,
            "wall_elapsed": 1268.5742602999999
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440625000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855962,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440625000,
              "cpu": 1199.59375
            },
            "active_processes": 2,
            "cpu_ticks": 11995937500,
            "wall_elapsed": 1268.5849856000004
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440625000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855962,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440625000,
              "cpu": 1199.59375
            },
            "active_processes": 2,
            "cpu_ticks": 11995937500,
            "wall_elapsed": 1268.5955396
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440781250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855962,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440781250,
              "cpu": 1199.609375
            },
            "active_processes": 2,
            "cpu_ticks": 11996093750,
            "wall_elapsed": 1268.6059850000001
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440937500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855962,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440937500,
              "cpu": 1199.625
            },
            "active_processes": 2,
            "cpu_ticks": 11996250000,
            "wall_elapsed": 1268.616462
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440937500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10855962,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440937500,
              "cpu": 1199.625
            },
            "active_processes": 2,
            "cpu_ticks": 11996250000,
            "wall_elapsed": 1268.6271484
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11440937500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10856732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11440937500,
              "cpu": 1199.625
            },
            "active_processes": 2,
            "cpu_ticks": 11996250000,
            "wall_elapsed": 1268.6375355999999
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11441093750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10856732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11441093750,
              "cpu": 1199.640625
            },
            "active_processes": 2,
            "cpu_ticks": 11996406250,
            "wall_elapsed": 1268.648045
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11441093750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10856732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11441093750,
              "cpu": 1199.640625
            },
            "active_processes": 2,
            "cpu_ticks": 11996406250,
            "wall_elapsed": 1268.6589949
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11441250000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10856732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11441250000,
              "cpu": 1199.65625
            },
            "active_processes": 2,
            "cpu_ticks": 11996562500,
            "wall_elapsed": 1268.6696807999997
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11441406250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10856732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11441406250,
              "cpu": 1199.671875
            },
            "active_processes": 2,
            "cpu_ticks": 11996718750,
            "wall_elapsed": 1268.6801950999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11441562500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10856732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11441562500,
              "cpu": 1199.6875
            },
            "active_processes": 2,
            "cpu_ticks": 11996875000,
            "wall_elapsed": 1268.6908416000006
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11441562500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10856732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11441562500,
              "cpu": 1199.6875
            },
            "active_processes": 2,
            "cpu_ticks": 11996875000,
            "wall_elapsed": 1268.7013023
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11441718750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10856732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11441718750,
              "cpu": 1199.703125
            },
            "active_processes": 2,
            "cpu_ticks": 11997031250,
            "wall_elapsed": 1268.7117392999999
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11441718750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10856732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11441718750,
              "cpu": 1199.703125
            },
            "active_processes": 2,
            "cpu_ticks": 11997031250,
            "wall_elapsed": 1268.7222031000001
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11441875000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10856732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11441875000,
              "cpu": 1199.71875
            },
            "active_processes": 2,
            "cpu_ticks": 11997187500,
            "wall_elapsed": 1268.7327348
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11442031250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11442031250,
              "cpu": 1199.734375
            },
            "active_processes": 2,
            "cpu_ticks": 11997343750,
            "wall_elapsed": 1268.7432858000002
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11442031250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11442031250,
              "cpu": 1199.734375
            },
            "active_processes": 2,
            "cpu_ticks": 11997343750,
            "wall_elapsed": 1268.7537985
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11442187500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11442187500,
              "cpu": 1199.75
            },
            "active_processes": 2,
            "cpu_ticks": 11997500000,
            "wall_elapsed": 1268.7642765
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11442343750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11442343750,
              "cpu": 1199.765625
            },
            "active_processes": 2,
            "cpu_ticks": 11997656250,
            "wall_elapsed": 1268.7748017000004
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11442500000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11442500000,
              "cpu": 1199.78125
            },
            "active_processes": 2,
            "cpu_ticks": 11997812500,
            "wall_elapsed": 1268.7855338
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11442500000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11442500000,
              "cpu": 1199.78125
            },
            "active_processes": 2,
            "cpu_ticks": 11997812500,
            "wall_elapsed": 1268.7958402000004
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11442656250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11442656250,
              "cpu": 1199.796875
            },
            "active_processes": 2,
            "cpu_ticks": 11997968750,
            "wall_elapsed": 1268.8065287
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11442812500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11442812500,
              "cpu": 1199.8125
            },
            "active_processes": 2,
            "cpu_ticks": 11998125000,
            "wall_elapsed": 1268.8169067999997
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11442812500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11442812500,
              "cpu": 1199.8125
            },
            "active_processes": 2,
            "cpu_ticks": 11998125000,
            "wall_elapsed": 1268.8272083000002
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11442968750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11442968750,
              "cpu": 1199.828125
            },
            "active_processes": 2,
            "cpu_ticks": 11998281250,
            "wall_elapsed": 1268.8377111999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11443125000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10857502,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11443125000,
              "cpu": 1199.84375
            },
            "active_processes": 2,
            "cpu_ticks": 11998437500,
            "wall_elapsed": 1268.8482562
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11443125000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10858273,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11443125000,
              "cpu": 1199.84375
            },
            "active_processes": 2,
            "cpu_ticks": 11998437500,
            "wall_elapsed": 1268.8586018000005
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11443281250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10858273,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11443281250,
              "cpu": 1199.859375
            },
            "active_processes": 2,
            "cpu_ticks": 11998593750,
            "wall_elapsed": 1268.8691759000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11443437500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10858273,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11443437500,
              "cpu": 1199.875
            },
            "active_processes": 2,
            "cpu_ticks": 11998750000,
            "wall_elapsed": 1268.8795762999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11443437500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10858273,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11443437500,
              "cpu": 1199.875
            },
            "active_processes": 2,
            "cpu_ticks": 11998750000,
            "wall_elapsed": 1268.8900472000005
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11443593750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10858273,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11443593750,
              "cpu": 1199.890625
            },
            "active_processes": 2,
            "cpu_ticks": 11998906250,
            "wall_elapsed": 1268.9004645000005
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11443750000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10858273,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11443750000,
              "cpu": 1199.90625
            },
            "active_processes": 2,
            "cpu_ticks": 11999062500,
            "wall_elapsed": 1268.9106700000002
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11443750000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10858273,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11443750000,
              "cpu": 1199.90625
            },
            "active_processes": 2,
            "cpu_ticks": 11999062500,
            "wall_elapsed": 1268.9211694000005
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11443906250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10858273,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11443906250,
              "cpu": 1199.921875
            },
            "active_processes": 2,
            "cpu_ticks": 11999218750,
            "wall_elapsed": 1268.9316349
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11444062500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10859043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11444062500,
              "cpu": 1199.9375
            },
            "active_processes": 2,
            "cpu_ticks": 11999375000,
            "wall_elapsed": 1268.9420547999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11444062500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10859043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11444062500,
              "cpu": 1199.9375
            },
            "active_processes": 2,
            "cpu_ticks": 11999375000,
            "wall_elapsed": 1268.9527016000002
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11444218750,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10859043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11444218750,
              "cpu": 1199.953125
            },
            "active_processes": 2,
            "cpu_ticks": 11999531250,
            "wall_elapsed": 1268.9632418
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11444375000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10859043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11444375000,
              "cpu": 1199.96875
            },
            "active_processes": 2,
            "cpu_ticks": 11999687500,
            "wall_elapsed": 1268.9736266
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11444375000,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10859043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11444375000,
              "cpu": 1199.96875
            },
            "active_processes": 2,
            "cpu_ticks": 11999687500,
            "wall_elapsed": 1268.9838184
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11444531250,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10859043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11444531250,
              "cpu": 1199.984375
            },
            "active_processes": 2,
            "cpu_ticks": 11999843750,
            "wall_elapsed": 1268.9943138999997
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11444687500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10859043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11444687500,
              "cpu": 1200.0
            },
            "active_processes": 2,
            "cpu_ticks": 12000000000,
            "wall_elapsed": 1269.0049133000002
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11444687500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10859043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11444687500,
              "cpu": 1200.0
            },
            "active_processes": 0,
            "cpu_ticks": 12000000000,
            "wall_elapsed": 1269.0051442000004
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 555312500,
              "ThisPeriodTotalUserTime": 11444687500,
              "TotalKernelTime": 555312500,
              "TotalPageFaultCount": 10859043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 11444687500,
              "cpu": 1200.0
            },
            "active_processes": 0,
            "cpu_ticks": 12000000000,
            "wall_elapsed": 1269.0051583000004
          }
        ],
        "stop_reason": "CPU_LIMIT_REACHED",
        "strict_zero_overshoot": "NOT_CLAIMED",
        "supervisor_cpu_scope": "CURRENT_PROCESS_USER_PLUS_KERNEL_WINDOW_EXCLUDED_FROM_JOB; MAY_INCLUDE_OTHER_CONCURRENT_WORK",
        "supervisor_cpu_ticks": 92968750,
        "supervisor_cpu_window_end": "RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE",
        "supervisor_cpu_window_start": "BEFORE_WORKER_CREATION",
        "termination_attempted": true,
        "termination_error": null,
        "termination_latency": 0.0002221000004283269,
        "termination_reason": "CPU_LIMIT_REACHED",
        "termination_requested": true,
        "termination_result": "SUCCEEDED",
        "total_cpu_hard_limit": "RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY",
        "total_cpu_ticks": 12000000000,
        "total_kernel_ticks": 555312500,
        "total_user_ticks": 11444687500,
        "user_cpu_limit_ticks": null,
        "wall_elapsed": 1269.0054132000005,
        "wall_elapsed_at_stop_request": 1269.0049221,
        "wall_elapsed_at_tree_exit": 1269.0051442000004,
        "wall_limit_seconds": 1500.0,
        "worker_exit_code": 99,
        "worker_exit_status": 99
      },
      "counts": null,
      "raw_net": null
    }
  ],
  "error": {
    "type": "RuntimeError",
    "message": "BRANCH_FAILED/H2_KEEP",
    "traceback": "Traceback (most recent call last):\n  File \"D:\\1st\\stfbs_lite_h2_h3_extension_004_continuation_001_4031c1f393534d67a3b5595b6f633b66\\run_task_impl.py\", line 108, in <module>\n    rows.append(report);print('SCIENCE_FINISH',b['name'],report['status'],flush=True);need(ok,'BRANCH_FAILED/'+b['name'])\n                                                                                      ~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File \"D:\\1st\\stfbs_lite_h2_h3_extension_004_continuation_001_4031c1f393534d67a3b5595b6f633b66\\run_task_impl.py\", line 13, in need\n    if not v:raise RuntimeError(m)\n             ^^^^^^^^^^^^^^^^^^^^^\nRuntimeError: BRANCH_FAILED/H2_KEEP\n"
  },
  "precheck_receipt": {
    "attempt_identity": "EXT004_SYNTHETIC_PRECHECK",
    "termination_reason": "WORKER_EXITED",
    "stop_reason": "NATURAL_EXIT",
    "worker_exit_status": 0,
    "worker_exit_code": 0,
    "job_cleanup_status": "PASS",
    "process_tree_status": "PROCESS_TREE_EXIT_CONFIRMED",
    "execution_entry": "RUN_MONITORED",
    "job_handle_state": "JOB_HANDLE_CLOSED",
    "fallback_close_attempted": false,
    "fallback_close_result": null,
    "fallback_close_error_if_any": null,
    "original_termination_error": null,
    "accounting": {
      "TotalUserTime": 1093750,
      "TotalKernelTime": 156250,
      "ThisPeriodTotalUserTime": 1093750,
      "ThisPeriodTotalKernelTime": 156250,
      "TotalPageFaultCount": 10615,
      "TotalProcesses": 2,
      "ActiveProcesses": 0,
      "TotalTerminatedProcesses": 0,
      "cpu": 0.125
    },
    "cpu_semantics": "TOTAL_CPU_SECONDS",
    "cpu_scope": "WHOLE_JOB",
    "cpu_limit_ticks": 1190625000,
    "user_cpu_limit_ticks": null,
    "wall_limit_seconds": 168.0787949000005,
    "total_user_ticks": 1093750,
    "total_kernel_ticks": 156250,
    "total_cpu_ticks": 1250000,
    "final_cpu_ticks": 1250000,
    "cpu_ticks_at_trigger": null,
    "last_valid_cpu_ticks": 1250000,
    "last_valid_cpu_sample": {
      "wall_elapsed": 0.25379640000028303,
      "cpu_ticks": 1250000,
      "active_processes": 0,
      "accounting": {
        "TotalUserTime": 1093750,
        "TotalKernelTime": 156250,
        "ThisPeriodTotalUserTime": 1093750,
        "ThisPeriodTotalKernelTime": 156250,
        "TotalPageFaultCount": 10615,
        "TotalProcesses": 2,
        "ActiveProcesses": 0,
        "TotalTerminatedProcesses": 0,
        "cpu": 0.125
      }
    },
    "cpu_overshoot_ticks": 0,
    "wall_elapsed": 0.25389520000044286,
    "last_valid_wall_sample": 0.25389540000014676,
    "wall_elapsed_at_stop_request": null,
    "wall_elapsed_at_tree_exit": 0.2537830000001122,
    "termination_latency": null,
    "termination_requested": false,
    "termination_attempted": false,
    "termination_result": null,
    "termination_error": null,
    "remaining_active_processes_if_known": 0,
    "active_processes_final": 0,
    "supervisor_cpu_ticks": 0,
    "supervisor_cpu_scope": "CURRENT_PROCESS_USER_PLUS_KERNEL_WINDOW_EXCLUDED_FROM_JOB; MAY_INCLUDE_OTHER_CONCURRENT_WORK",
    "supervisor_cpu_window_start": "BEFORE_WORKER_CREATION",
    "supervisor_cpu_window_end": "RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE",
    "accounting_status": "FINAL_VALID",
    "receipt_integrity_status": "NOT_PERSISTED",
    "evidence_completeness_status": "COMPLETE_IN_MEMORY",
    "os_termination_cause": "OS_TERMINATION_CAUSE_UNVERIFIED",
    "samples": [
      {
        "wall_elapsed": 0.004310700000132783,
        "cpu_ticks": 0,
        "active_processes": 1,
        "accounting": {
          "TotalUserTime": 0,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 0,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 509,
          "TotalProcesses": 1,
          "ActiveProcesses": 1,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.0
        }
      },
      {
        "wall_elapsed": 0.014848400000119,
        "cpu_ticks": 156250,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 156250,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 156250,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 2975,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.015625
        }
      },
      {
        "wall_elapsed": 0.025337500000205182,
        "cpu_ticks": 312500,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 312500,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 312500,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 4960,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.03125
        }
      },
      {
        "wall_elapsed": 0.035803600000690494,
        "cpu_ticks": 312500,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 312500,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 312500,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 5444,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.03125
        }
      },
      {
        "wall_elapsed": 0.04589650000070833,
        "cpu_ticks": 468750,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 468750,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 468750,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 5791,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.046875
        }
      },
      {
        "wall_elapsed": 0.05627640000056999,
        "cpu_ticks": 625000,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 625000,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 625000,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 6387,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.0625
        }
      },
      {
        "wall_elapsed": 0.06665789999988192,
        "cpu_ticks": 625000,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 625000,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 625000,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 7262,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.0625
        }
      },
      {
        "wall_elapsed": 0.0768593000002511,
        "cpu_ticks": 781250,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 781250,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 781250,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 7778,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.078125
        }
      },
      {
        "wall_elapsed": 0.08736649999991641,
        "cpu_ticks": 937500,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 8232,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.09375
        }
      },
      {
        "wall_elapsed": 0.09797900000012305,
        "cpu_ticks": 937500,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 8629,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.09375
        }
      },
      {
        "wall_elapsed": 0.10859570000047825,
        "cpu_ticks": 937500,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 8857,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.09375
        }
      },
      {
        "wall_elapsed": 0.11894200000006094,
        "cpu_ticks": 937500,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 9580,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.09375
        }
      },
      {
        "wall_elapsed": 0.12943260000065493,
        "cpu_ticks": 937500,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 10285,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.09375
        }
      },
      {
        "wall_elapsed": 0.1397200999999768,
        "cpu_ticks": 937500,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 0,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 0,
          "TotalPageFaultCount": 10285,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.09375
        }
      },
      {
        "wall_elapsed": 0.15016890000060812,
        "cpu_ticks": 1093750,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10288,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.109375
        }
      },
      {
        "wall_elapsed": 0.16066370000044117,
        "cpu_ticks": 1093750,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10288,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.109375
        }
      },
      {
        "wall_elapsed": 0.17105400000036752,
        "cpu_ticks": 1093750,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10303,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.109375
        }
      },
      {
        "wall_elapsed": 0.18163619999995717,
        "cpu_ticks": 1093750,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10303,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.109375
        }
      },
      {
        "wall_elapsed": 0.19206920000033278,
        "cpu_ticks": 1093750,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10303,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.109375
        }
      },
      {
        "wall_elapsed": 0.202419799999916,
        "cpu_ticks": 1093750,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10313,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.109375
        }
      },
      {
        "wall_elapsed": 0.21257500000047003,
        "cpu_ticks": 1093750,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10315,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.109375
        }
      },
      {
        "wall_elapsed": 0.22296929999993154,
        "cpu_ticks": 1093750,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10319,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.109375
        }
      },
      {
        "wall_elapsed": 0.23320270000021992,
        "cpu_ticks": 1093750,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 937500,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 937500,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10323,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.109375
        }
      },
      {
        "wall_elapsed": 0.24331359999996494,
        "cpu_ticks": 1250000,
        "active_processes": 2,
        "accounting": {
          "TotalUserTime": 1093750,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 1093750,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10615,
          "TotalProcesses": 2,
          "ActiveProcesses": 2,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.125
        }
      },
      {
        "wall_elapsed": 0.2537830000001122,
        "cpu_ticks": 1250000,
        "active_processes": 0,
        "accounting": {
          "TotalUserTime": 1093750,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 1093750,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10615,
          "TotalProcesses": 2,
          "ActiveProcesses": 0,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.125
        }
      },
      {
        "wall_elapsed": 0.25379640000028303,
        "cpu_ticks": 1250000,
        "active_processes": 0,
        "accounting": {
          "TotalUserTime": 1093750,
          "TotalKernelTime": 156250,
          "ThisPeriodTotalUserTime": 1093750,
          "ThisPeriodTotalKernelTime": 156250,
          "TotalPageFaultCount": 10615,
          "TotalProcesses": 2,
          "ActiveProcesses": 0,
          "TotalTerminatedProcesses": 0,
          "cpu": 0.125
        }
      }
    ],
    "events": [
      "GUARD_CONFIGURED",
      "WORKER_CONTAINED",
      "WORKER_RESUMED",
      "RUNNING_MONITORED",
      "PROCESS_TREE_EXIT_CONFIRMED",
      "FINAL_ACCOUNTING"
    ],
    "errors": [],
    "strict_zero_overshoot": "NOT_CLAIMED",
    "overshoot_bound": "NOT_PROVEN",
    "total_cpu_hard_limit": "RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY",
    "production_run_admission": "BLOCKED"
  },
  "parent_cpu_ticks": 234218750,
  "aux_cpu_ticks": 156250,
  "wall_seconds": 1282.8957486999998,
  "faults": [],
  "final_faults": [],
  "retry": false,
  "h1_reused_cells": 3,
  "actual_run": false,
  "h1_rerun": false,
  "minimax_regret": "NOT_COMPLETED",
  "production_admission": "BLOCKED",
  "science_scope": "Exploratory finite three-world three-action single-D60 offline MODEL; no statistical or full uncertainty-set guarantee",
  "final_summary_resource_usage": {
    "cpu_ticks": 5312500,
    "cpu_seconds": 0.53125,
    "wall_seconds": 0.5579696999993757,
    "total_wall_seconds": 1282.9837128999998,
    "storage_bytes": 7170780
  },
  "all_started_processes_exit_confirmed": true
}