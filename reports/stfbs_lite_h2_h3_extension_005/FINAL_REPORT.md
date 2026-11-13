# EXTENSION_005

{
  "task_id": "STFBS_LITE_LOCAL_DEV_H2_H3_EXTENSION_005",
  "continuation": "EXTENSION_005",
  "status": "LOCAL_DEV_D60_H2_H3_VALUE_MATRIX_PASS_CANDIDATE",
  "execution_admission": "PASS",
  "valid_new_cells": 6,
  "scientific_attempts_consumed": 6,
  "branches_not_started": 0,
  "branches": [
    {
      "name": "H2_KEEP",
      "run_id": "EXT005_H2_KEEP_RUN_001",
      "attempt_id": "EXT005_H2_KEEP_001",
      "branch_id": "EXT005_H2_KEEP_BRANCH_001",
      "valid_cell_candidate": true,
      "status": "VALID_CELL_CANDIDATE",
      "returncode": 0,
      "stdout": "{\"status\": \"OUTER_CONTROL_COMPLETE\", \"parent_start_calls\": 1, \"parent_exit\": 0}\n",
      "stderr": "",
      "outer": {
        "actions": [
          {
            "elapsed": 55.002304300000105,
            "fallback": false,
            "kind": "JOB_CLOSE",
            "result": "SUCCEEDED"
          }
        ],
        "approval_sha256": "5482780af02dbd8b4d7abaa76c6574ffc79ff150bb196250f1d49479bf0befde",
        "attempt_id": "EXT005_H2_KEEP_001",
        "elapsed_seconds": 55.00232369999867,
        "ended_utc": "2026-11-13T11:01:57.379380+00:00",
        "errors": [],
        "final_outer_accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 84062500,
          "ThisPeriodTotalUserTime": 426875000,
          "TotalKernelTime": 84062500,
          "TotalPageFaultCount": 256492,
          "TotalProcesses": 10,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 426875000,
          "cpu": 51.09375
        },
        "handle_waits": [
          {
            "pid": 31288,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 12004,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 30360,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 12864,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 26776,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 28540,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 10904,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 8956,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 21968,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 17584,
            "remedial_termination_attempted": false,
            "wait_status": 0
          }
        ],
        "identities": [
          {
            "creation_ticks": 134390412623799354,
            "member": true,
            "pid": 31288,
            "role": "LOCAL_DEV_PARENT_SUSPENDED"
          },
          {
            "creation_ticks": 134390412623799354,
            "member": true,
            "pid": 31288,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390412623839324,
            "member": true,
            "pid": 12004,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390412626556046,
            "member": true,
            "pid": 30360,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390412626631275,
            "member": true,
            "pid": 12864,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390412626817454,
            "member": true,
            "pid": 26776,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390412626870765,
            "member": true,
            "pid": 28540,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390412629569352,
            "member": true,
            "pid": 10904,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390412629639313,
            "member": true,
            "pid": 8956,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390413172232553,
            "member": true,
            "pid": 21968,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390413172300615,
            "member": true,
            "pid": 17584,
            "role": "RETAINED_OUTER_MEMBER"
          }
        ],
        "job_handle_diagnostic": 296,
        "job_handle_state": "CLOSED",
        "outer_wall_seconds": 1560,
        "parent_exit_code": 0,
        "parent_start_calls": 1,
        "parent_wait_status": 0,
        "process_tree_exit_confirmed": true,
        "production_admission": "RUN_ADMISSION_BLOCKED",
        "run_id": "EXT005_H2_KEEP_RUN_001",
        "started_utc": "2026-11-13T11:01:02.377052+00:00",
        "status": "OUTER_CONTROL_COMPLETE",
        "timed_out": false
      },
      "inner": {
        "accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 80781250,
          "ThisPeriodTotalUserTime": 424687500,
          "TotalKernelTime": 80781250,
          "TotalPageFaultCount": 209137,
          "TotalProcesses": 6,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 424687500,
          "cpu": 50.546875
        },
        "accounting_status": "FINAL_VALID",
        "active_processes_final": 0,
        "attempt_identity": "EXT005_H2_KEEP_001",
        "cpu_limit_ticks": 12000000000,
        "cpu_overshoot_ticks": 0,
        "cpu_scope": "WHOLE_JOB",
        "cpu_semantics": "TOTAL_CPU_SECONDS",
        "cpu_ticks_at_trigger": null,
        "errors": [],
        "events": [
          "GUARD_CONFIGURED",
          "WORKER_CONTAINED",
          "WORKER_RESUMED",
          "RUNNING_MONITORED",
          "PROCESS_TREE_EXIT_CONFIRMED",
          "FINAL_ACCOUNTING"
        ],
        "evidence_completeness_status": "COMPLETE_IN_MEMORY",
        "execution_entry": "RUN_MONITORED",
        "fallback_close_attempted": false,
        "fallback_close_error_if_any": null,
        "fallback_close_result": null,
        "final_cpu_ticks": 505468750,
        "job_cleanup_status": "PASS",
        "job_handle_state": "JOB_HANDLE_CLOSED",
        "last_valid_cpu_sample": {
          "accounting": {
            "ActiveProcesses": 0,
            "ThisPeriodTotalKernelTime": 80781250,
            "ThisPeriodTotalUserTime": 424687500,
            "TotalKernelTime": 80781250,
            "TotalPageFaultCount": 209137,
            "TotalProcesses": 6,
            "TotalTerminatedProcesses": 0,
            "TotalUserTime": 424687500,
            "cpu": 50.546875
          },
          "active_processes": 0,
          "cpu_ticks": 505468750,
          "wall_elapsed": 54.67768840000099
        },
        "last_valid_cpu_ticks": 505468750,
        "last_valid_wall_sample": 54.67781040000045,
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
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 420781250,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 176699,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 420781250,
              "cpu": 50.0
            },
            "active_processes": 2,
            "cpu_ticks": 500000000,
            "wall_elapsed": 54.02046540000083
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 420781250,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 176997,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 420781250,
              "cpu": 50.0
            },
            "active_processes": 2,
            "cpu_ticks": 500000000,
            "wall_elapsed": 54.03124160000152
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 420937500,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 177331,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 420937500,
              "cpu": 50.015625
            },
            "active_processes": 2,
            "cpu_ticks": 500156250,
            "wall_elapsed": 54.04164860000128
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 421093750,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 177704,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 421093750,
              "cpu": 50.03125
            },
            "active_processes": 2,
            "cpu_ticks": 500312500,
            "wall_elapsed": 54.05235690000154
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 421093750,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 178062,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 421093750,
              "cpu": 50.03125
            },
            "active_processes": 2,
            "cpu_ticks": 500312500,
            "wall_elapsed": 54.06258290000005
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 421250000,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 178444,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 421250000,
              "cpu": 50.046875
            },
            "active_processes": 2,
            "cpu_ticks": 500468750,
            "wall_elapsed": 54.0732351000006
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 421406250,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 178815,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 421406250,
              "cpu": 50.0625
            },
            "active_processes": 2,
            "cpu_ticks": 500625000,
            "wall_elapsed": 54.08393260000048
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 421406250,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179229,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 421406250,
              "cpu": 50.0625
            },
            "active_processes": 2,
            "cpu_ticks": 500625000,
            "wall_elapsed": 54.09457570000086
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 421562500,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179395,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 421562500,
              "cpu": 50.078125
            },
            "active_processes": 2,
            "cpu_ticks": 500781250,
            "wall_elapsed": 54.105075400000715
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 421718750,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179435,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 421718750,
              "cpu": 50.09375
            },
            "active_processes": 2,
            "cpu_ticks": 500937500,
            "wall_elapsed": 54.11590320000141
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 421718750,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179435,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 421718750,
              "cpu": 50.09375
            },
            "active_processes": 2,
            "cpu_ticks": 500937500,
            "wall_elapsed": 54.12634910000088
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 421875000,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179535,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 421875000,
              "cpu": 50.109375
            },
            "active_processes": 2,
            "cpu_ticks": 501093750,
            "wall_elapsed": 54.137015500000416
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 422031250,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179535,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422031250,
              "cpu": 50.125
            },
            "active_processes": 2,
            "cpu_ticks": 501250000,
            "wall_elapsed": 54.14756950000083
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 422031250,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179535,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422031250,
              "cpu": 50.125
            },
            "active_processes": 2,
            "cpu_ticks": 501250000,
            "wall_elapsed": 54.15791530000024
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 422187500,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179535,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422187500,
              "cpu": 50.140625
            },
            "active_processes": 2,
            "cpu_ticks": 501406250,
            "wall_elapsed": 54.168408100000306
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 422343750,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179668,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422343750,
              "cpu": 50.15625
            },
            "active_processes": 2,
            "cpu_ticks": 501562500,
            "wall_elapsed": 54.17897940000148
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 422343750,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179856,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422343750,
              "cpu": 50.15625
            },
            "active_processes": 2,
            "cpu_ticks": 501562500,
            "wall_elapsed": 54.189948500001265
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 422500000,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179857,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422500000,
              "cpu": 50.171875
            },
            "active_processes": 2,
            "cpu_ticks": 501718750,
            "wall_elapsed": 54.20018590000109
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 422656250,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179861,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422656250,
              "cpu": 50.1875
            },
            "active_processes": 2,
            "cpu_ticks": 501875000,
            "wall_elapsed": 54.21112859999994
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 422812500,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179871,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422812500,
              "cpu": 50.203125
            },
            "active_processes": 2,
            "cpu_ticks": 502031250,
            "wall_elapsed": 54.22181900000032
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79218750,
              "ThisPeriodTotalUserTime": 422812500,
              "TotalKernelTime": 79218750,
              "TotalPageFaultCount": 179904,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422812500,
              "cpu": 50.203125
            },
            "active_processes": 2,
            "cpu_ticks": 502031250,
            "wall_elapsed": 54.23258540000097
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79375000,
              "ThisPeriodTotalUserTime": 422812500,
              "TotalKernelTime": 79375000,
              "TotalPageFaultCount": 184643,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422812500,
              "cpu": 50.21875
            },
            "active_processes": 2,
            "cpu_ticks": 502187500,
            "wall_elapsed": 54.24319650000143
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79531250,
              "ThisPeriodTotalUserTime": 422812500,
              "TotalKernelTime": 79531250,
              "TotalPageFaultCount": 184883,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422812500,
              "cpu": 50.234375
            },
            "active_processes": 2,
            "cpu_ticks": 502343750,
            "wall_elapsed": 54.25390320000042
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79531250,
              "ThisPeriodTotalUserTime": 422812500,
              "TotalKernelTime": 79531250,
              "TotalPageFaultCount": 184883,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422812500,
              "cpu": 50.234375
            },
            "active_processes": 2,
            "cpu_ticks": 502343750,
            "wall_elapsed": 54.26438710000002
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79531250,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 79531250,
              "TotalPageFaultCount": 186582,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.25
            },
            "active_processes": 2,
            "cpu_ticks": 502500000,
            "wall_elapsed": 54.274553000001106
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79687500,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 79687500,
              "TotalPageFaultCount": 186596,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.265625
            },
            "active_processes": 2,
            "cpu_ticks": 502656250,
            "wall_elapsed": 54.284832900000765
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79687500,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 79687500,
              "TotalPageFaultCount": 186596,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.265625
            },
            "active_processes": 2,
            "cpu_ticks": 502656250,
            "wall_elapsed": 54.295037600000796
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79843750,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 79843750,
              "TotalPageFaultCount": 186611,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.28125
            },
            "active_processes": 2,
            "cpu_ticks": 502812500,
            "wall_elapsed": 54.305191400000695
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 79843750,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 79843750,
              "TotalPageFaultCount": 186793,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.28125
            },
            "active_processes": 2,
            "cpu_ticks": 502812500,
            "wall_elapsed": 54.31537300000127
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80000000,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 80000000,
              "TotalPageFaultCount": 187576,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.296875
            },
            "active_processes": 2,
            "cpu_ticks": 502968750,
            "wall_elapsed": 54.325810100001036
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80000000,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 80000000,
              "TotalPageFaultCount": 191725,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.296875
            },
            "active_processes": 2,
            "cpu_ticks": 502968750,
            "wall_elapsed": 54.3365569000016
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80000000,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 80000000,
              "TotalPageFaultCount": 191725,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.296875
            },
            "active_processes": 2,
            "cpu_ticks": 502968750,
            "wall_elapsed": 54.3466810000009
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80156250,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 80156250,
              "TotalPageFaultCount": 191733,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.3125
            },
            "active_processes": 2,
            "cpu_ticks": 503125000,
            "wall_elapsed": 54.35697580000124
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80156250,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 80156250,
              "TotalPageFaultCount": 192021,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.3125
            },
            "active_processes": 2,
            "cpu_ticks": 503125000,
            "wall_elapsed": 54.3674074999999
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80156250,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 80156250,
              "TotalPageFaultCount": 192584,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.3125
            },
            "active_processes": 2,
            "cpu_ticks": 503125000,
            "wall_elapsed": 54.37791540000035
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80156250,
              "ThisPeriodTotalUserTime": 422968750,
              "TotalKernelTime": 80156250,
              "TotalPageFaultCount": 193547,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 422968750,
              "cpu": 50.3125
            },
            "active_processes": 2,
            "cpu_ticks": 503125000,
            "wall_elapsed": 54.388273200000185
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80156250,
              "ThisPeriodTotalUserTime": 423125000,
              "TotalKernelTime": 80156250,
              "TotalPageFaultCount": 194445,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423125000,
              "cpu": 50.328125
            },
            "active_processes": 2,
            "cpu_ticks": 503281250,
            "wall_elapsed": 54.399559800000134
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80312500,
              "ThisPeriodTotalUserTime": 423125000,
              "TotalKernelTime": 80312500,
              "TotalPageFaultCount": 194445,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423125000,
              "cpu": 50.34375
            },
            "active_processes": 2,
            "cpu_ticks": 503437500,
            "wall_elapsed": 54.409968600000866
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80312500,
              "ThisPeriodTotalUserTime": 423125000,
              "TotalKernelTime": 80312500,
              "TotalPageFaultCount": 196112,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423125000,
              "cpu": 50.34375
            },
            "active_processes": 2,
            "cpu_ticks": 503437500,
            "wall_elapsed": 54.42028620000019
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80312500,
              "ThisPeriodTotalUserTime": 423125000,
              "TotalKernelTime": 80312500,
              "TotalPageFaultCount": 196412,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423125000,
              "cpu": 50.34375
            },
            "active_processes": 2,
            "cpu_ticks": 503437500,
            "wall_elapsed": 54.43052760000137
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80468750,
              "ThisPeriodTotalUserTime": 423125000,
              "TotalKernelTime": 80468750,
              "TotalPageFaultCount": 196665,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423125000,
              "cpu": 50.359375
            },
            "active_processes": 2,
            "cpu_ticks": 503593750,
            "wall_elapsed": 54.441109100000176
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80468750,
              "ThisPeriodTotalUserTime": 423125000,
              "TotalKernelTime": 80468750,
              "TotalPageFaultCount": 197711,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423125000,
              "cpu": 50.359375
            },
            "active_processes": 2,
            "cpu_ticks": 503593750,
            "wall_elapsed": 54.45136100000127
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80468750,
              "ThisPeriodTotalUserTime": 423281250,
              "TotalKernelTime": 80468750,
              "TotalPageFaultCount": 197937,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423281250,
              "cpu": 50.375
            },
            "active_processes": 2,
            "cpu_ticks": 503750000,
            "wall_elapsed": 54.46176600000035
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80468750,
              "ThisPeriodTotalUserTime": 423281250,
              "TotalKernelTime": 80468750,
              "TotalPageFaultCount": 198350,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423281250,
              "cpu": 50.375
            },
            "active_processes": 2,
            "cpu_ticks": 503750000,
            "wall_elapsed": 54.47213270000066
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80625000,
              "ThisPeriodTotalUserTime": 423281250,
              "TotalKernelTime": 80625000,
              "TotalPageFaultCount": 199558,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423281250,
              "cpu": 50.390625
            },
            "active_processes": 2,
            "cpu_ticks": 503906250,
            "wall_elapsed": 54.48243150000053
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80625000,
              "ThisPeriodTotalUserTime": 423437500,
              "TotalKernelTime": 80625000,
              "TotalPageFaultCount": 201041,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423437500,
              "cpu": 50.40625
            },
            "active_processes": 2,
            "cpu_ticks": 504062500,
            "wall_elapsed": 54.49281610000071
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80625000,
              "ThisPeriodTotalUserTime": 423593750,
              "TotalKernelTime": 80625000,
              "TotalPageFaultCount": 201803,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423593750,
              "cpu": 50.421875
            },
            "active_processes": 2,
            "cpu_ticks": 504218750,
            "wall_elapsed": 54.5033852000015
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80625000,
              "ThisPeriodTotalUserTime": 423593750,
              "TotalKernelTime": 80625000,
              "TotalPageFaultCount": 202426,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423593750,
              "cpu": 50.421875
            },
            "active_processes": 2,
            "cpu_ticks": 504218750,
            "wall_elapsed": 54.51379690000067
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 423593750,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 202426,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423593750,
              "cpu": 50.4375
            },
            "active_processes": 2,
            "cpu_ticks": 504375000,
            "wall_elapsed": 54.52451590000055
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 423750000,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 204209,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423750000,
              "cpu": 50.453125
            },
            "active_processes": 2,
            "cpu_ticks": 504531250,
            "wall_elapsed": 54.53621210000165
          },
          {
            "accounting": {
              "ActiveProcesses": 3,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 423750000,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 205675,
              "TotalProcesses": 5,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423750000,
              "cpu": 50.453125
            },
            "active_processes": 3,
            "cpu_ticks": 504531250,
            "wall_elapsed": 54.54691790000106
          },
          {
            "accounting": {
              "ActiveProcesses": 4,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 423750000,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 207926,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423750000,
              "cpu": 50.453125
            },
            "active_processes": 4,
            "cpu_ticks": 504531250,
            "wall_elapsed": 54.55701450000015
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 423750000,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 208379,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423750000,
              "cpu": 50.453125
            },
            "active_processes": 2,
            "cpu_ticks": 504531250,
            "wall_elapsed": 54.567315600001166
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 423750000,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 208689,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423750000,
              "cpu": 50.453125
            },
            "active_processes": 2,
            "cpu_ticks": 504531250,
            "wall_elapsed": 54.577676100001554
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 423906250,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 208689,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 423906250,
              "cpu": 50.46875
            },
            "active_processes": 2,
            "cpu_ticks": 504687500,
            "wall_elapsed": 54.58995290000166
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 424062500,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 208689,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 424062500,
              "cpu": 50.484375
            },
            "active_processes": 2,
            "cpu_ticks": 504843750,
            "wall_elapsed": 54.600301800001034
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 424062500,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 208689,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 424062500,
              "cpu": 50.484375
            },
            "active_processes": 2,
            "cpu_ticks": 504843750,
            "wall_elapsed": 54.6118647000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 424218750,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 208690,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 424218750,
              "cpu": 50.5
            },
            "active_processes": 2,
            "cpu_ticks": 505000000,
            "wall_elapsed": 54.623669900000095
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 424375000,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 208690,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 424375000,
              "cpu": 50.515625
            },
            "active_processes": 2,
            "cpu_ticks": 505156250,
            "wall_elapsed": 54.63464810000005
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 424531250,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 208695,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 424531250,
              "cpu": 50.53125
            },
            "active_processes": 2,
            "cpu_ticks": 505312500,
            "wall_elapsed": 54.64508660000138
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 424531250,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 208702,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 424531250,
              "cpu": 50.53125
            },
            "active_processes": 2,
            "cpu_ticks": 505312500,
            "wall_elapsed": 54.656874100001005
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 424687500,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 209137,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 424687500,
              "cpu": 50.546875
            },
            "active_processes": 2,
            "cpu_ticks": 505468750,
            "wall_elapsed": 54.66717130000143
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 424687500,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 209137,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 424687500,
              "cpu": 50.546875
            },
            "active_processes": 0,
            "cpu_ticks": 505468750,
            "wall_elapsed": 54.6776718000001
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 80781250,
              "ThisPeriodTotalUserTime": 424687500,
              "TotalKernelTime": 80781250,
              "TotalPageFaultCount": 209137,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 424687500,
              "cpu": 50.546875
            },
            "active_processes": 0,
            "cpu_ticks": 505468750,
            "wall_elapsed": 54.67768840000099
          }
        ],
        "stop_reason": "NATURAL_EXIT",
        "strict_zero_overshoot": "NOT_CLAIMED",
        "supervisor_cpu_scope": "CURRENT_PROCESS_USER_PLUS_KERNEL_WINDOW_EXCLUDED_FROM_JOB; MAY_INCLUDE_OTHER_CONCURRENT_WORK",
        "supervisor_cpu_ticks": 2343750,
        "supervisor_cpu_window_end": "RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE",
        "supervisor_cpu_window_start": "BEFORE_WORKER_CREATION",
        "termination_attempted": false,
        "termination_error": null,
        "termination_latency": null,
        "termination_reason": "WORKER_EXITED",
        "termination_requested": false,
        "termination_result": null,
        "total_cpu_hard_limit": "RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY",
        "total_cpu_ticks": 505468750,
        "total_kernel_ticks": 80781250,
        "total_user_ticks": 424687500,
        "user_cpu_limit_ticks": null,
        "wall_elapsed": 54.67781030000151,
        "wall_elapsed_at_stop_request": null,
        "wall_elapsed_at_tree_exit": 54.6776718000001,
        "wall_limit_seconds": 1500.0,
        "worker_exit_code": 0,
        "worker_exit_status": 0
      },
      "counts": {
        "ACTUAL_STEP": 0,
        "ACTUAL_WLS": 0,
        "ASSIGNMENT_EXACT_SOLVER": 2,
        "MODEL_OBSERVATION_WLS": 33,
        "MODEL_POLICY_EVALUATION_WLS": 590,
        "MODEL_SOLVER_START": 5607,
        "R_CALLS": 2
      },
      "raw_net": -0.3150141073101529
    },
    {
      "name": "H2_SWITCH",
      "run_id": "EXT005_H2_SWITCH_RUN_001",
      "attempt_id": "EXT005_H2_SWITCH_001",
      "branch_id": "EXT005_H2_SWITCH_BRANCH_001",
      "valid_cell_candidate": true,
      "status": "VALID_CELL_CANDIDATE",
      "returncode": 0,
      "stdout": "{\"status\": \"OUTER_CONTROL_COMPLETE\", \"parent_start_calls\": 1, \"parent_exit\": 0}\n",
      "stderr": "",
      "outer": {
        "actions": [
          {
            "elapsed": 81.68191600000137,
            "fallback": false,
            "kind": "JOB_CLOSE",
            "result": "SUCCEEDED"
          }
        ],
        "approval_sha256": "9740548c6c461ae686fd380928af806e63ec2593b0f76506801af3eed242a1ac",
        "attempt_id": "EXT005_H2_SWITCH_001",
        "elapsed_seconds": 81.68193400000018,
        "ended_utc": "2026-11-13T11:03:20.300745+00:00",
        "errors": [],
        "final_outer_accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 122656250,
          "ThisPeriodTotalUserTime": 641718750,
          "TotalKernelTime": 122656250,
          "TotalPageFaultCount": 290885,
          "TotalProcesses": 10,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 641718750,
          "cpu": 76.4375
        },
        "handle_waits": [
          {
            "pid": 31064,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 31480,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 24272,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 6872,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 23692,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 29920,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 24312,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 26824,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 26184,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 30996,
            "remedial_termination_attempted": false,
            "wait_status": 0
          }
        ],
        "identities": [
          {
            "creation_ticks": 134390413186216607,
            "member": true,
            "pid": 31064,
            "role": "LOCAL_DEV_PARENT_SUSPENDED"
          },
          {
            "creation_ticks": 134390413186216607,
            "member": true,
            "pid": 31064,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390413186261180,
            "member": true,
            "pid": 31480,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390413188972655,
            "member": true,
            "pid": 24272,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390413189040282,
            "member": true,
            "pid": 6872,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390413189230895,
            "member": true,
            "pid": 23692,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390413189289176,
            "member": true,
            "pid": 29920,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390413192110801,
            "member": true,
            "pid": 24312,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390413192182098,
            "member": true,
            "pid": 26824,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414001646029,
            "member": true,
            "pid": 26184,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414001713870,
            "member": true,
            "pid": 30996,
            "role": "RETAINED_OUTER_MEMBER"
          }
        ],
        "job_handle_diagnostic": 480,
        "job_handle_state": "CLOSED",
        "outer_wall_seconds": 1560,
        "parent_exit_code": 0,
        "parent_start_calls": 1,
        "parent_wait_status": 0,
        "process_tree_exit_confirmed": true,
        "production_admission": "RUN_ADMISSION_BLOCKED",
        "run_id": "EXT005_H2_SWITCH_RUN_001",
        "started_utc": "2026-11-13T11:01:58.618806+00:00",
        "status": "OUTER_CONTROL_COMPLETE",
        "timed_out": false
      },
      "inner": {
        "accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 117968750,
          "ThisPeriodTotalUserTime": 640000000,
          "TotalKernelTime": 117968750,
          "TotalPageFaultCount": 244861,
          "TotalProcesses": 6,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 640000000,
          "cpu": 75.796875
        },
        "accounting_status": "FINAL_VALID",
        "active_processes_final": 0,
        "attempt_identity": "EXT005_H2_SWITCH_001",
        "cpu_limit_ticks": 12000000000,
        "cpu_overshoot_ticks": 0,
        "cpu_scope": "WHOLE_JOB",
        "cpu_semantics": "TOTAL_CPU_SECONDS",
        "cpu_ticks_at_trigger": null,
        "errors": [],
        "events": [
          "GUARD_CONFIGURED",
          "WORKER_CONTAINED",
          "WORKER_RESUMED",
          "RUNNING_MONITORED",
          "PROCESS_TREE_EXIT_CONFIRMED",
          "FINAL_ACCOUNTING"
        ],
        "evidence_completeness_status": "COMPLETE_IN_MEMORY",
        "execution_entry": "RUN_MONITORED",
        "fallback_close_attempted": false,
        "fallback_close_error_if_any": null,
        "fallback_close_result": null,
        "final_cpu_ticks": 757968750,
        "job_cleanup_status": "PASS",
        "job_handle_state": "JOB_HANDLE_CLOSED",
        "last_valid_cpu_sample": {
          "accounting": {
            "ActiveProcesses": 0,
            "ThisPeriodTotalKernelTime": 117968750,
            "ThisPeriodTotalUserTime": 640000000,
            "TotalKernelTime": 117968750,
            "TotalPageFaultCount": 244861,
            "TotalProcesses": 6,
            "TotalTerminatedProcesses": 0,
            "TotalUserTime": 640000000,
            "cpu": 75.796875
          },
          "active_processes": 0,
          "cpu_ticks": 757968750,
          "wall_elapsed": 81.36180989999957
        },
        "last_valid_cpu_ticks": 757968750,
        "last_valid_wall_sample": 81.36193139999887,
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
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 635625000,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 211348,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 635625000,
              "cpu": 75.171875
            },
            "active_processes": 2,
            "cpu_ticks": 751718750,
            "wall_elapsed": 80.70148309999968
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 635625000,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 211662,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 635625000,
              "cpu": 75.171875
            },
            "active_processes": 2,
            "cpu_ticks": 751718750,
            "wall_elapsed": 80.71226169999863
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 635781250,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 212015,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 635781250,
              "cpu": 75.1875
            },
            "active_processes": 2,
            "cpu_ticks": 751875000,
            "wall_elapsed": 80.72358799999893
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 635937500,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 212367,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 635937500,
              "cpu": 75.203125
            },
            "active_processes": 2,
            "cpu_ticks": 752031250,
            "wall_elapsed": 80.73427119999906
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 636093750,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 212785,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 636093750,
              "cpu": 75.21875
            },
            "active_processes": 2,
            "cpu_ticks": 752187500,
            "wall_elapsed": 80.74642929999936
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 636093750,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 213179,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 636093750,
              "cpu": 75.21875
            },
            "active_processes": 2,
            "cpu_ticks": 752187500,
            "wall_elapsed": 80.75797349999993
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 636250000,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 213550,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 636250000,
              "cpu": 75.234375
            },
            "active_processes": 2,
            "cpu_ticks": 752343750,
            "wall_elapsed": 80.76848160000009
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 636406250,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 213991,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 636406250,
              "cpu": 75.25
            },
            "active_processes": 2,
            "cpu_ticks": 752500000,
            "wall_elapsed": 80.78057679999984
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 636406250,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214393,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 636406250,
              "cpu": 75.25
            },
            "active_processes": 2,
            "cpu_ticks": 752500000,
            "wall_elapsed": 80.79228150000017
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 636562500,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214703,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 636562500,
              "cpu": 75.265625
            },
            "active_processes": 2,
            "cpu_ticks": 752656250,
            "wall_elapsed": 80.80280119999952
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 636718750,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214731,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 636718750,
              "cpu": 75.28125
            },
            "active_processes": 2,
            "cpu_ticks": 752812500,
            "wall_elapsed": 80.81328329999997
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 636718750,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214755,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 636718750,
              "cpu": 75.28125
            },
            "active_processes": 2,
            "cpu_ticks": 752812500,
            "wall_elapsed": 80.82384289999936
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 636875000,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214857,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 636875000,
              "cpu": 75.296875
            },
            "active_processes": 2,
            "cpu_ticks": 752968750,
            "wall_elapsed": 80.83485929999915
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 637031250,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214857,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637031250,
              "cpu": 75.3125
            },
            "active_processes": 2,
            "cpu_ticks": 753125000,
            "wall_elapsed": 80.84553659999983
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 637187500,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214857,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637187500,
              "cpu": 75.328125
            },
            "active_processes": 2,
            "cpu_ticks": 753281250,
            "wall_elapsed": 80.85606840000037
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 637187500,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214857,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637187500,
              "cpu": 75.328125
            },
            "active_processes": 2,
            "cpu_ticks": 753281250,
            "wall_elapsed": 80.86653850000039
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 637343750,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214857,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637343750,
              "cpu": 75.34375
            },
            "active_processes": 2,
            "cpu_ticks": 753437500,
            "wall_elapsed": 80.87755149999975
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 637500000,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214857,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637500000,
              "cpu": 75.359375
            },
            "active_processes": 2,
            "cpu_ticks": 753593750,
            "wall_elapsed": 80.88865199999964
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 637500000,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 214969,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637500000,
              "cpu": 75.359375
            },
            "active_processes": 2,
            "cpu_ticks": 753593750,
            "wall_elapsed": 80.8990589999994
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 637656250,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 215141,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637656250,
              "cpu": 75.375
            },
            "active_processes": 2,
            "cpu_ticks": 753750000,
            "wall_elapsed": 80.90930929999922
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 637812500,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 215146,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637812500,
              "cpu": 75.390625
            },
            "active_processes": 2,
            "cpu_ticks": 753906250,
            "wall_elapsed": 80.91985349999959
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116093750,
              "ThisPeriodTotalUserTime": 637812500,
              "TotalKernelTime": 116093750,
              "TotalPageFaultCount": 215162,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637812500,
              "cpu": 75.390625
            },
            "active_processes": 2,
            "cpu_ticks": 753906250,
            "wall_elapsed": 80.92997979999927
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116250000,
              "ThisPeriodTotalUserTime": 637812500,
              "TotalKernelTime": 116250000,
              "TotalPageFaultCount": 215168,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637812500,
              "cpu": 75.40625
            },
            "active_processes": 2,
            "cpu_ticks": 754062500,
            "wall_elapsed": 80.94018469999901
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116250000,
              "ThisPeriodTotalUserTime": 637968750,
              "TotalKernelTime": 116250000,
              "TotalPageFaultCount": 220596,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637968750,
              "cpu": 75.421875
            },
            "active_processes": 2,
            "cpu_ticks": 754218750,
            "wall_elapsed": 80.95177729999887
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116250000,
              "ThisPeriodTotalUserTime": 637968750,
              "TotalKernelTime": 116250000,
              "TotalPageFaultCount": 220596,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637968750,
              "cpu": 75.421875
            },
            "active_processes": 2,
            "cpu_ticks": 754218750,
            "wall_elapsed": 80.96235969999907
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116406250,
              "ThisPeriodTotalUserTime": 637968750,
              "TotalKernelTime": 116406250,
              "TotalPageFaultCount": 220793,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 637968750,
              "cpu": 75.4375
            },
            "active_processes": 2,
            "cpu_ticks": 754375000,
            "wall_elapsed": 80.97246649999943
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116406250,
              "ThisPeriodTotalUserTime": 638125000,
              "TotalKernelTime": 116406250,
              "TotalPageFaultCount": 222402,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638125000,
              "cpu": 75.453125
            },
            "active_processes": 2,
            "cpu_ticks": 754531250,
            "wall_elapsed": 80.98298259999865
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116406250,
              "ThisPeriodTotalUserTime": 638125000,
              "TotalKernelTime": 116406250,
              "TotalPageFaultCount": 222529,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638125000,
              "cpu": 75.453125
            },
            "active_processes": 2,
            "cpu_ticks": 754531250,
            "wall_elapsed": 80.99347599999965
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116406250,
              "ThisPeriodTotalUserTime": 638281250,
              "TotalKernelTime": 116406250,
              "TotalPageFaultCount": 222534,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638281250,
              "cpu": 75.46875
            },
            "active_processes": 2,
            "cpu_ticks": 754687500,
            "wall_elapsed": 81.00361259999954
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116406250,
              "ThisPeriodTotalUserTime": 638437500,
              "TotalKernelTime": 116406250,
              "TotalPageFaultCount": 222604,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638437500,
              "cpu": 75.484375
            },
            "active_processes": 2,
            "cpu_ticks": 754843750,
            "wall_elapsed": 81.01392479999959
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116406250,
              "ThisPeriodTotalUserTime": 638437500,
              "TotalKernelTime": 116406250,
              "TotalPageFaultCount": 222629,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638437500,
              "cpu": 75.484375
            },
            "active_processes": 2,
            "cpu_ticks": 754843750,
            "wall_elapsed": 81.02423239999916
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116562500,
              "ThisPeriodTotalUserTime": 638437500,
              "TotalKernelTime": 116562500,
              "TotalPageFaultCount": 227561,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638437500,
              "cpu": 75.5
            },
            "active_processes": 2,
            "cpu_ticks": 755000000,
            "wall_elapsed": 81.0350342999991
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116562500,
              "ThisPeriodTotalUserTime": 638437500,
              "TotalKernelTime": 116562500,
              "TotalPageFaultCount": 227561,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638437500,
              "cpu": 75.5
            },
            "active_processes": 2,
            "cpu_ticks": 755000000,
            "wall_elapsed": 81.04673550000007
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116562500,
              "ThisPeriodTotalUserTime": 638437500,
              "TotalKernelTime": 116562500,
              "TotalPageFaultCount": 227566,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638437500,
              "cpu": 75.5
            },
            "active_processes": 2,
            "cpu_ticks": 755000000,
            "wall_elapsed": 81.05717269999877
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116718750,
              "ThisPeriodTotalUserTime": 638437500,
              "TotalKernelTime": 116718750,
              "TotalPageFaultCount": 227852,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638437500,
              "cpu": 75.515625
            },
            "active_processes": 2,
            "cpu_ticks": 755156250,
            "wall_elapsed": 81.06762849999905
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116718750,
              "ThisPeriodTotalUserTime": 638593750,
              "TotalKernelTime": 116718750,
              "TotalPageFaultCount": 228286,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638593750,
              "cpu": 75.53125
            },
            "active_processes": 2,
            "cpu_ticks": 755312500,
            "wall_elapsed": 81.0779521000004
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116718750,
              "ThisPeriodTotalUserTime": 638593750,
              "TotalKernelTime": 116718750,
              "TotalPageFaultCount": 229488,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638593750,
              "cpu": 75.53125
            },
            "active_processes": 2,
            "cpu_ticks": 755312500,
            "wall_elapsed": 81.08852859999934
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116718750,
              "ThisPeriodTotalUserTime": 638750000,
              "TotalKernelTime": 116718750,
              "TotalPageFaultCount": 229585,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638750000,
              "cpu": 75.546875
            },
            "active_processes": 2,
            "cpu_ticks": 755468750,
            "wall_elapsed": 81.09901009999885
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116875000,
              "ThisPeriodTotalUserTime": 638750000,
              "TotalKernelTime": 116875000,
              "TotalPageFaultCount": 230348,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638750000,
              "cpu": 75.5625
            },
            "active_processes": 2,
            "cpu_ticks": 755625000,
            "wall_elapsed": 81.10932680000042
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 116875000,
              "ThisPeriodTotalUserTime": 638750000,
              "TotalKernelTime": 116875000,
              "TotalPageFaultCount": 232013,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638750000,
              "cpu": 75.5625
            },
            "active_processes": 2,
            "cpu_ticks": 755625000,
            "wall_elapsed": 81.11970709999878
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117031250,
              "ThisPeriodTotalUserTime": 638750000,
              "TotalKernelTime": 117031250,
              "TotalPageFaultCount": 232312,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638750000,
              "cpu": 75.578125
            },
            "active_processes": 2,
            "cpu_ticks": 755781250,
            "wall_elapsed": 81.1298439000002
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117187500,
              "ThisPeriodTotalUserTime": 638750000,
              "TotalKernelTime": 117187500,
              "TotalPageFaultCount": 232316,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638750000,
              "cpu": 75.59375
            },
            "active_processes": 2,
            "cpu_ticks": 755937500,
            "wall_elapsed": 81.14013999999952
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117187500,
              "ThisPeriodTotalUserTime": 638750000,
              "TotalKernelTime": 117187500,
              "TotalPageFaultCount": 232562,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638750000,
              "cpu": 75.59375
            },
            "active_processes": 2,
            "cpu_ticks": 755937500,
            "wall_elapsed": 81.15052859999923
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117343750,
              "ThisPeriodTotalUserTime": 638750000,
              "TotalKernelTime": 117343750,
              "TotalPageFaultCount": 233609,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638750000,
              "cpu": 75.609375
            },
            "active_processes": 2,
            "cpu_ticks": 756093750,
            "wall_elapsed": 81.16082019999885
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117343750,
              "ThisPeriodTotalUserTime": 638906250,
              "TotalKernelTime": 117343750,
              "TotalPageFaultCount": 233743,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638906250,
              "cpu": 75.625
            },
            "active_processes": 2,
            "cpu_ticks": 756250000,
            "wall_elapsed": 81.17112699999961
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117343750,
              "ThisPeriodTotalUserTime": 638906250,
              "TotalKernelTime": 117343750,
              "TotalPageFaultCount": 234761,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 638906250,
              "cpu": 75.625
            },
            "active_processes": 2,
            "cpu_ticks": 756250000,
            "wall_elapsed": 81.18143810000038
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117343750,
              "ThisPeriodTotalUserTime": 639062500,
              "TotalKernelTime": 117343750,
              "TotalPageFaultCount": 235669,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639062500,
              "cpu": 75.640625
            },
            "active_processes": 2,
            "cpu_ticks": 756406250,
            "wall_elapsed": 81.1917257999994
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117343750,
              "ThisPeriodTotalUserTime": 639218750,
              "TotalKernelTime": 117343750,
              "TotalPageFaultCount": 237375,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639218750,
              "cpu": 75.65625
            },
            "active_processes": 2,
            "cpu_ticks": 756562500,
            "wall_elapsed": 81.20240099999864
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117343750,
              "ThisPeriodTotalUserTime": 639218750,
              "TotalKernelTime": 117343750,
              "TotalPageFaultCount": 237375,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639218750,
              "cpu": 75.65625
            },
            "active_processes": 2,
            "cpu_ticks": 756562500,
            "wall_elapsed": 81.21299840000029
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117343750,
              "ThisPeriodTotalUserTime": 639375000,
              "TotalKernelTime": 117343750,
              "TotalPageFaultCount": 237997,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639375000,
              "cpu": 75.671875
            },
            "active_processes": 2,
            "cpu_ticks": 756718750,
            "wall_elapsed": 81.22343179999916
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117343750,
              "ThisPeriodTotalUserTime": 639531250,
              "TotalKernelTime": 117343750,
              "TotalPageFaultCount": 239779,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639531250,
              "cpu": 75.6875
            },
            "active_processes": 2,
            "cpu_ticks": 756875000,
            "wall_elapsed": 81.23443159999988
          },
          {
            "accounting": {
              "ActiveProcesses": 3,
              "ThisPeriodTotalKernelTime": 117343750,
              "ThisPeriodTotalUserTime": 639531250,
              "TotalKernelTime": 117343750,
              "TotalPageFaultCount": 240684,
              "TotalProcesses": 5,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639531250,
              "cpu": 75.6875
            },
            "active_processes": 3,
            "cpu_ticks": 756875000,
            "wall_elapsed": 81.24477119999938
          },
          {
            "accounting": {
              "ActiveProcesses": 4,
              "ThisPeriodTotalKernelTime": 117500000,
              "ThisPeriodTotalUserTime": 639531250,
              "TotalKernelTime": 117500000,
              "TotalPageFaultCount": 242780,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639531250,
              "cpu": 75.703125
            },
            "active_processes": 4,
            "cpu_ticks": 757031250,
            "wall_elapsed": 81.25526030000037
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117656250,
              "ThisPeriodTotalUserTime": 639531250,
              "TotalKernelTime": 117656250,
              "TotalPageFaultCount": 243954,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639531250,
              "cpu": 75.71875
            },
            "active_processes": 2,
            "cpu_ticks": 757187500,
            "wall_elapsed": 81.2654351000001
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117656250,
              "ThisPeriodTotalUserTime": 639531250,
              "TotalKernelTime": 117656250,
              "TotalPageFaultCount": 244412,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639531250,
              "cpu": 75.71875
            },
            "active_processes": 2,
            "cpu_ticks": 757187500,
            "wall_elapsed": 81.27597579999929
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117656250,
              "ThisPeriodTotalUserTime": 639687500,
              "TotalKernelTime": 117656250,
              "TotalPageFaultCount": 244412,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639687500,
              "cpu": 75.734375
            },
            "active_processes": 2,
            "cpu_ticks": 757343750,
            "wall_elapsed": 81.28620140000021
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117812500,
              "ThisPeriodTotalUserTime": 639687500,
              "TotalKernelTime": 117812500,
              "TotalPageFaultCount": 244412,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639687500,
              "cpu": 75.75
            },
            "active_processes": 2,
            "cpu_ticks": 757500000,
            "wall_elapsed": 81.2965621000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117812500,
              "ThisPeriodTotalUserTime": 639687500,
              "TotalKernelTime": 117812500,
              "TotalPageFaultCount": 244412,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639687500,
              "cpu": 75.75
            },
            "active_processes": 2,
            "cpu_ticks": 757500000,
            "wall_elapsed": 81.30704429999969
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117812500,
              "ThisPeriodTotalUserTime": 639843750,
              "TotalKernelTime": 117812500,
              "TotalPageFaultCount": 244413,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639843750,
              "cpu": 75.765625
            },
            "active_processes": 2,
            "cpu_ticks": 757656250,
            "wall_elapsed": 81.31878030000007
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117968750,
              "ThisPeriodTotalUserTime": 639843750,
              "TotalKernelTime": 117968750,
              "TotalPageFaultCount": 244416,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 639843750,
              "cpu": 75.78125
            },
            "active_processes": 2,
            "cpu_ticks": 757812500,
            "wall_elapsed": 81.32936770000015
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 117968750,
              "ThisPeriodTotalUserTime": 640000000,
              "TotalKernelTime": 117968750,
              "TotalPageFaultCount": 244426,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 640000000,
              "cpu": 75.796875
            },
            "active_processes": 2,
            "cpu_ticks": 757968750,
            "wall_elapsed": 81.34105350000027
          },
          {
            "accounting": {
              "ActiveProcesses": 1,
              "ThisPeriodTotalKernelTime": 117968750,
              "ThisPeriodTotalUserTime": 640000000,
              "TotalKernelTime": 117968750,
              "TotalPageFaultCount": 244861,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 640000000,
              "cpu": 75.796875
            },
            "active_processes": 1,
            "cpu_ticks": 757968750,
            "wall_elapsed": 81.35141529999964
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 117968750,
              "ThisPeriodTotalUserTime": 640000000,
              "TotalKernelTime": 117968750,
              "TotalPageFaultCount": 244861,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 640000000,
              "cpu": 75.796875
            },
            "active_processes": 0,
            "cpu_ticks": 757968750,
            "wall_elapsed": 81.36179149999953
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 117968750,
              "ThisPeriodTotalUserTime": 640000000,
              "TotalKernelTime": 117968750,
              "TotalPageFaultCount": 244861,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 640000000,
              "cpu": 75.796875
            },
            "active_processes": 0,
            "cpu_ticks": 757968750,
            "wall_elapsed": 81.36180989999957
          }
        ],
        "stop_reason": "NATURAL_EXIT",
        "strict_zero_overshoot": "NOT_CLAIMED",
        "supervisor_cpu_scope": "CURRENT_PROCESS_USER_PLUS_KERNEL_WINDOW_EXCLUDED_FROM_JOB; MAY_INCLUDE_OTHER_CONCURRENT_WORK",
        "supervisor_cpu_ticks": 3593750,
        "supervisor_cpu_window_end": "RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE",
        "supervisor_cpu_window_start": "BEFORE_WORKER_CREATION",
        "termination_attempted": false,
        "termination_error": null,
        "termination_latency": null,
        "termination_reason": "WORKER_EXITED",
        "termination_requested": false,
        "termination_result": null,
        "total_cpu_hard_limit": "RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY",
        "total_cpu_ticks": 757968750,
        "total_kernel_ticks": 117968750,
        "total_user_ticks": 640000000,
        "user_cpu_limit_ticks": null,
        "wall_elapsed": 81.36193119999916,
        "wall_elapsed_at_stop_request": null,
        "wall_elapsed_at_tree_exit": 81.36179149999953,
        "wall_limit_seconds": 1500.0,
        "worker_exit_code": 0,
        "worker_exit_status": 0
      },
      "counts": {
        "ACTUAL_STEP": 0,
        "ACTUAL_WLS": 0,
        "ASSIGNMENT_EXACT_SOLVER": 2,
        "MODEL_OBSERVATION_WLS": 60,
        "MODEL_POLICY_EVALUATION_WLS": 740,
        "MODEL_SOLVER_START": 7200,
        "R_CALLS": 2
      },
      "raw_net": -0.1687802228561035
    },
    {
      "name": "H2_MEMBER_CHANGE",
      "run_id": "EXT005_H2_MEMBER_CHANGE_RUN_001",
      "attempt_id": "EXT005_H2_MEMBER_CHANGE_001",
      "branch_id": "EXT005_H2_MEMBER_CHANGE_BRANCH_001",
      "valid_cell_candidate": true,
      "status": "VALID_CELL_CANDIDATE",
      "returncode": 0,
      "stdout": "{\"status\": \"OUTER_CONTROL_COMPLETE\", \"parent_start_calls\": 1, \"parent_exit\": 0}\n",
      "stderr": "",
      "outer": {
        "actions": [
          {
            "elapsed": 85.0158948999997,
            "fallback": false,
            "kind": "JOB_CLOSE",
            "result": "SUCCEEDED"
          }
        ],
        "approval_sha256": "a391d2d45a10a179ec27869b9f6fdb040a09cf70a9e29d04c7822fb1bca08499",
        "attempt_id": "EXT005_H2_MEMBER_CHANGE_001",
        "elapsed_seconds": 85.01595859999907,
        "ended_utc": "2026-11-13T11:04:46.660167+00:00",
        "errors": [],
        "final_outer_accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 126718750,
          "ThisPeriodTotalUserTime": 668125000,
          "TotalKernelTime": 126718750,
          "TotalPageFaultCount": 293551,
          "TotalProcesses": 10,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 668125000,
          "cpu": 79.484375
        },
        "handle_waits": [
          {
            "pid": 23456,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 9356,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 28916,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 3312,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 708,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 25108,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 7296,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 27200,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 28660,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 20896,
            "remedial_termination_attempted": false,
            "wait_status": 0
          }
        ],
        "identities": [
          {
            "creation_ticks": 134390414016473060,
            "member": true,
            "pid": 23456,
            "role": "LOCAL_DEV_PARENT_SUSPENDED"
          },
          {
            "creation_ticks": 134390414016473060,
            "member": true,
            "pid": 23456,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414016527737,
            "member": true,
            "pid": 9356,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414019282952,
            "member": true,
            "pid": 28916,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414019354706,
            "member": true,
            "pid": 3312,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414019609838,
            "member": true,
            "pid": 708,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414019667700,
            "member": true,
            "pid": 25108,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414022488351,
            "member": true,
            "pid": 7296,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414022556858,
            "member": true,
            "pid": 27200,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414864472226,
            "member": true,
            "pid": 28660,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414864533763,
            "member": true,
            "pid": 20896,
            "role": "RETAINED_OUTER_MEMBER"
          }
        ],
        "job_handle_diagnostic": 496,
        "job_handle_state": "CLOSED",
        "outer_wall_seconds": 1560,
        "parent_exit_code": 0,
        "parent_start_calls": 1,
        "parent_wait_status": 0,
        "process_tree_exit_confirmed": true,
        "production_admission": "RUN_ADMISSION_BLOCKED",
        "run_id": "EXT005_H2_MEMBER_CHANGE_RUN_001",
        "started_utc": "2026-11-13T11:03:21.644226+00:00",
        "status": "OUTER_CONTROL_COMPLETE",
        "timed_out": false
      },
      "inner": {
        "accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 120312500,
          "ThisPeriodTotalUserTime": 665468750,
          "TotalKernelTime": 120312500,
          "TotalPageFaultCount": 247608,
          "TotalProcesses": 6,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 665468750,
          "cpu": 78.578125
        },
        "accounting_status": "FINAL_VALID",
        "active_processes_final": 0,
        "attempt_identity": "EXT005_H2_MEMBER_CHANGE_001",
        "cpu_limit_ticks": 12000000000,
        "cpu_overshoot_ticks": 0,
        "cpu_scope": "WHOLE_JOB",
        "cpu_semantics": "TOTAL_CPU_SECONDS",
        "cpu_ticks_at_trigger": null,
        "errors": [],
        "events": [
          "GUARD_CONFIGURED",
          "WORKER_CONTAINED",
          "WORKER_RESUMED",
          "RUNNING_MONITORED",
          "PROCESS_TREE_EXIT_CONFIRMED",
          "FINAL_ACCOUNTING"
        ],
        "evidence_completeness_status": "COMPLETE_IN_MEMORY",
        "execution_entry": "RUN_MONITORED",
        "fallback_close_attempted": false,
        "fallback_close_error_if_any": null,
        "fallback_close_result": null,
        "final_cpu_ticks": 785781250,
        "job_cleanup_status": "PASS",
        "job_handle_state": "JOB_HANDLE_CLOSED",
        "last_valid_cpu_sample": {
          "accounting": {
            "ActiveProcesses": 0,
            "ThisPeriodTotalKernelTime": 120312500,
            "ThisPeriodTotalUserTime": 665468750,
            "TotalKernelTime": 120312500,
            "TotalPageFaultCount": 247608,
            "TotalProcesses": 6,
            "TotalTerminatedProcesses": 0,
            "TotalUserTime": 665468750,
            "cpu": 78.578125
          },
          "active_processes": 0,
          "cpu_ticks": 785781250,
          "wall_elapsed": 84.67706859999998
        },
        "last_valid_cpu_ticks": 785781250,
        "last_valid_wall_sample": 84.67722049999975,
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
              "ThisPeriodTotalKernelTime": 118125000,
              "ThisPeriodTotalUserTime": 661562500,
              "TotalKernelTime": 118125000,
              "TotalPageFaultCount": 218423,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 661562500,
              "cpu": 77.96875
            },
            "active_processes": 2,
            "cpu_ticks": 779687500,
            "wall_elapsed": 84.02426999999989
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118125000,
              "ThisPeriodTotalUserTime": 661562500,
              "TotalKernelTime": 118125000,
              "TotalPageFaultCount": 218423,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 661562500,
              "cpu": 77.96875
            },
            "active_processes": 2,
            "cpu_ticks": 779687500,
            "wall_elapsed": 84.03494769999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118125000,
              "ThisPeriodTotalUserTime": 661718750,
              "TotalKernelTime": 118125000,
              "TotalPageFaultCount": 218423,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 661718750,
              "cpu": 77.984375
            },
            "active_processes": 2,
            "cpu_ticks": 779843750,
            "wall_elapsed": 84.04546499999924
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118125000,
              "ThisPeriodTotalUserTime": 661875000,
              "TotalKernelTime": 118125000,
              "TotalPageFaultCount": 218510,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 661875000,
              "cpu": 78.0
            },
            "active_processes": 2,
            "cpu_ticks": 780000000,
            "wall_elapsed": 84.0556861999994
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118125000,
              "ThisPeriodTotalUserTime": 661875000,
              "TotalKernelTime": 118125000,
              "TotalPageFaultCount": 218697,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 661875000,
              "cpu": 78.0
            },
            "active_processes": 2,
            "cpu_ticks": 780000000,
            "wall_elapsed": 84.06606169999941
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118125000,
              "ThisPeriodTotalUserTime": 662031250,
              "TotalKernelTime": 118125000,
              "TotalPageFaultCount": 218698,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662031250,
              "cpu": 78.015625
            },
            "active_processes": 2,
            "cpu_ticks": 780156250,
            "wall_elapsed": 84.07654699999875
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118125000,
              "ThisPeriodTotalUserTime": 662187500,
              "TotalKernelTime": 118125000,
              "TotalPageFaultCount": 218700,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662187500,
              "cpu": 78.03125
            },
            "active_processes": 2,
            "cpu_ticks": 780312500,
            "wall_elapsed": 84.08681109999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118125000,
              "ThisPeriodTotalUserTime": 662187500,
              "TotalKernelTime": 118125000,
              "TotalPageFaultCount": 218705,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662187500,
              "cpu": 78.03125
            },
            "active_processes": 2,
            "cpu_ticks": 780312500,
            "wall_elapsed": 84.0969427
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118125000,
              "ThisPeriodTotalUserTime": 662343750,
              "TotalKernelTime": 118125000,
              "TotalPageFaultCount": 223704,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662343750,
              "cpu": 78.046875
            },
            "active_processes": 2,
            "cpu_ticks": 780468750,
            "wall_elapsed": 84.10725089999869
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118281250,
              "ThisPeriodTotalUserTime": 662343750,
              "TotalKernelTime": 118281250,
              "TotalPageFaultCount": 223704,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662343750,
              "cpu": 78.0625
            },
            "active_processes": 2,
            "cpu_ticks": 780625000,
            "wall_elapsed": 84.11801479999849
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118281250,
              "ThisPeriodTotalUserTime": 662343750,
              "TotalKernelTime": 118281250,
              "TotalPageFaultCount": 224722,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662343750,
              "cpu": 78.0625
            },
            "active_processes": 2,
            "cpu_ticks": 780625000,
            "wall_elapsed": 84.12865879999845
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118437500,
              "ThisPeriodTotalUserTime": 662343750,
              "TotalKernelTime": 118437500,
              "TotalPageFaultCount": 225273,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662343750,
              "cpu": 78.078125
            },
            "active_processes": 2,
            "cpu_ticks": 780781250,
            "wall_elapsed": 84.13892999999916
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118437500,
              "ThisPeriodTotalUserTime": 662500000,
              "TotalKernelTime": 118437500,
              "TotalPageFaultCount": 225273,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662500000,
              "cpu": 78.09375
            },
            "active_processes": 2,
            "cpu_ticks": 780937500,
            "wall_elapsed": 84.14946029999919
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118437500,
              "ThisPeriodTotalUserTime": 662500000,
              "TotalKernelTime": 118437500,
              "TotalPageFaultCount": 225276,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662500000,
              "cpu": 78.09375
            },
            "active_processes": 2,
            "cpu_ticks": 780937500,
            "wall_elapsed": 84.16026619999866
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118593750,
              "ThisPeriodTotalUserTime": 662500000,
              "TotalKernelTime": 118593750,
              "TotalPageFaultCount": 225288,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662500000,
              "cpu": 78.109375
            },
            "active_processes": 2,
            "cpu_ticks": 781093750,
            "wall_elapsed": 84.17090999999891
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118750000,
              "ThisPeriodTotalUserTime": 662500000,
              "TotalKernelTime": 118750000,
              "TotalPageFaultCount": 225292,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662500000,
              "cpu": 78.125
            },
            "active_processes": 2,
            "cpu_ticks": 781250000,
            "wall_elapsed": 84.18156929999896
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118750000,
              "ThisPeriodTotalUserTime": 662500000,
              "TotalKernelTime": 118750000,
              "TotalPageFaultCount": 225305,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662500000,
              "cpu": 78.125
            },
            "active_processes": 2,
            "cpu_ticks": 781250000,
            "wall_elapsed": 84.1922713999993
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118750000,
              "ThisPeriodTotalUserTime": 662656250,
              "TotalKernelTime": 118750000,
              "TotalPageFaultCount": 225306,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662656250,
              "cpu": 78.140625
            },
            "active_processes": 2,
            "cpu_ticks": 781406250,
            "wall_elapsed": 84.20293289999972
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118750000,
              "ThisPeriodTotalUserTime": 662812500,
              "TotalKernelTime": 118750000,
              "TotalPageFaultCount": 230237,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662812500,
              "cpu": 78.15625
            },
            "active_processes": 2,
            "cpu_ticks": 781562500,
            "wall_elapsed": 84.21328029999859
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118750000,
              "ThisPeriodTotalUserTime": 662812500,
              "TotalKernelTime": 118750000,
              "TotalPageFaultCount": 230237,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662812500,
              "cpu": 78.15625
            },
            "active_processes": 2,
            "cpu_ticks": 781562500,
            "wall_elapsed": 84.22365039999931
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118750000,
              "ThisPeriodTotalUserTime": 662968750,
              "TotalKernelTime": 118750000,
              "TotalPageFaultCount": 230237,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 662968750,
              "cpu": 78.171875
            },
            "active_processes": 2,
            "cpu_ticks": 781718750,
            "wall_elapsed": 84.23416749999888
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118750000,
              "ThisPeriodTotalUserTime": 663125000,
              "TotalKernelTime": 118750000,
              "TotalPageFaultCount": 230237,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663125000,
              "cpu": 78.1875
            },
            "active_processes": 2,
            "cpu_ticks": 781875000,
            "wall_elapsed": 84.24473359999865
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118750000,
              "ThisPeriodTotalUserTime": 663281250,
              "TotalKernelTime": 118750000,
              "TotalPageFaultCount": 230247,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663281250,
              "cpu": 78.203125
            },
            "active_processes": 2,
            "cpu_ticks": 782031250,
            "wall_elapsed": 84.25518639999973
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118750000,
              "ThisPeriodTotalUserTime": 663281250,
              "TotalKernelTime": 118750000,
              "TotalPageFaultCount": 230618,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663281250,
              "cpu": 78.203125
            },
            "active_processes": 2,
            "cpu_ticks": 782031250,
            "wall_elapsed": 84.26597599999877
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118906250,
              "ThisPeriodTotalUserTime": 663281250,
              "TotalKernelTime": 118906250,
              "TotalPageFaultCount": 231105,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663281250,
              "cpu": 78.21875
            },
            "active_processes": 2,
            "cpu_ticks": 782187500,
            "wall_elapsed": 84.27646279999863
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 118906250,
              "ThisPeriodTotalUserTime": 663281250,
              "TotalKernelTime": 118906250,
              "TotalPageFaultCount": 231499,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663281250,
              "cpu": 78.21875
            },
            "active_processes": 2,
            "cpu_ticks": 782187500,
            "wall_elapsed": 84.28683219999948
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119062500,
              "ThisPeriodTotalUserTime": 663281250,
              "TotalKernelTime": 119062500,
              "TotalPageFaultCount": 232190,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663281250,
              "cpu": 78.234375
            },
            "active_processes": 2,
            "cpu_ticks": 782343750,
            "wall_elapsed": 84.29755099999966
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119062500,
              "ThisPeriodTotalUserTime": 663281250,
              "TotalKernelTime": 119062500,
              "TotalPageFaultCount": 232248,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663281250,
              "cpu": 78.234375
            },
            "active_processes": 2,
            "cpu_ticks": 782343750,
            "wall_elapsed": 84.30796969999938
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119062500,
              "ThisPeriodTotalUserTime": 663281250,
              "TotalKernelTime": 119062500,
              "TotalPageFaultCount": 233188,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663281250,
              "cpu": 78.234375
            },
            "active_processes": 2,
            "cpu_ticks": 782343750,
            "wall_elapsed": 84.3184870999994
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119062500,
              "ThisPeriodTotalUserTime": 663437500,
              "TotalKernelTime": 119062500,
              "TotalPageFaultCount": 233188,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663437500,
              "cpu": 78.25
            },
            "active_processes": 2,
            "cpu_ticks": 782500000,
            "wall_elapsed": 84.3291991999995
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119218750,
              "ThisPeriodTotalUserTime": 663437500,
              "TotalKernelTime": 119218750,
              "TotalPageFaultCount": 233188,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663437500,
              "cpu": 78.265625
            },
            "active_processes": 2,
            "cpu_ticks": 782656250,
            "wall_elapsed": 84.33971939999901
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119218750,
              "ThisPeriodTotalUserTime": 663593750,
              "TotalKernelTime": 119218750,
              "TotalPageFaultCount": 234856,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663593750,
              "cpu": 78.28125
            },
            "active_processes": 2,
            "cpu_ticks": 782812500,
            "wall_elapsed": 84.35013299999991
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119218750,
              "ThisPeriodTotalUserTime": 663593750,
              "TotalKernelTime": 119218750,
              "TotalPageFaultCount": 235156,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663593750,
              "cpu": 78.28125
            },
            "active_processes": 2,
            "cpu_ticks": 782812500,
            "wall_elapsed": 84.36027389999981
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119218750,
              "ThisPeriodTotalUserTime": 663750000,
              "TotalKernelTime": 119218750,
              "TotalPageFaultCount": 235162,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663750000,
              "cpu": 78.296875
            },
            "active_processes": 2,
            "cpu_ticks": 782968750,
            "wall_elapsed": 84.37097679999897
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119375000,
              "ThisPeriodTotalUserTime": 663750000,
              "TotalKernelTime": 119375000,
              "TotalPageFaultCount": 235162,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663750000,
              "cpu": 78.3125
            },
            "active_processes": 2,
            "cpu_ticks": 783125000,
            "wall_elapsed": 84.38147249999929
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119375000,
              "ThisPeriodTotalUserTime": 663750000,
              "TotalKernelTime": 119375000,
              "TotalPageFaultCount": 236216,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663750000,
              "cpu": 78.3125
            },
            "active_processes": 2,
            "cpu_ticks": 783125000,
            "wall_elapsed": 84.39189169999918
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119531250,
              "ThisPeriodTotalUserTime": 663750000,
              "TotalKernelTime": 119531250,
              "TotalPageFaultCount": 236235,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663750000,
              "cpu": 78.328125
            },
            "active_processes": 2,
            "cpu_ticks": 783281250,
            "wall_elapsed": 84.40225809999902
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119531250,
              "ThisPeriodTotalUserTime": 663906250,
              "TotalKernelTime": 119531250,
              "TotalPageFaultCount": 236460,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663906250,
              "cpu": 78.34375
            },
            "active_processes": 2,
            "cpu_ticks": 783437500,
            "wall_elapsed": 84.41286679999939
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119531250,
              "ThisPeriodTotalUserTime": 663906250,
              "TotalKernelTime": 119531250,
              "TotalPageFaultCount": 237482,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 663906250,
              "cpu": 78.34375
            },
            "active_processes": 2,
            "cpu_ticks": 783437500,
            "wall_elapsed": 84.42330159999983
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119531250,
              "ThisPeriodTotalUserTime": 664062500,
              "TotalKernelTime": 119531250,
              "TotalPageFaultCount": 238396,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664062500,
              "cpu": 78.359375
            },
            "active_processes": 2,
            "cpu_ticks": 783593750,
            "wall_elapsed": 84.43400269999984
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119531250,
              "ThisPeriodTotalUserTime": 664218750,
              "TotalKernelTime": 119531250,
              "TotalPageFaultCount": 240107,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664218750,
              "cpu": 78.375
            },
            "active_processes": 2,
            "cpu_ticks": 783750000,
            "wall_elapsed": 84.44433239999853
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119531250,
              "ThisPeriodTotalUserTime": 664218750,
              "TotalKernelTime": 119531250,
              "TotalPageFaultCount": 240107,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664218750,
              "cpu": 78.375
            },
            "active_processes": 2,
            "cpu_ticks": 783750000,
            "wall_elapsed": 84.45480719999978
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119687500,
              "ThisPeriodTotalUserTime": 664218750,
              "TotalKernelTime": 119687500,
              "TotalPageFaultCount": 240732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664218750,
              "cpu": 78.390625
            },
            "active_processes": 2,
            "cpu_ticks": 783906250,
            "wall_elapsed": 84.46519439999975
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119843750,
              "ThisPeriodTotalUserTime": 664218750,
              "TotalKernelTime": 119843750,
              "TotalPageFaultCount": 240732,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664218750,
              "cpu": 78.40625
            },
            "active_processes": 2,
            "cpu_ticks": 784062500,
            "wall_elapsed": 84.47574629999872
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 119843750,
              "ThisPeriodTotalUserTime": 664218750,
              "TotalKernelTime": 119843750,
              "TotalPageFaultCount": 242851,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664218750,
              "cpu": 78.40625
            },
            "active_processes": 2,
            "cpu_ticks": 784062500,
            "wall_elapsed": 84.48607559999982
          },
          {
            "accounting": {
              "ActiveProcesses": 4,
              "ThisPeriodTotalKernelTime": 120000000,
              "ThisPeriodTotalUserTime": 664218750,
              "TotalKernelTime": 120000000,
              "TotalPageFaultCount": 245215,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664218750,
              "cpu": 78.421875
            },
            "active_processes": 4,
            "cpu_ticks": 784218750,
            "wall_elapsed": 84.49659549999888
          },
          {
            "accounting": {
              "ActiveProcesses": 4,
              "ThisPeriodTotalKernelTime": 120156250,
              "ThisPeriodTotalUserTime": 664218750,
              "TotalKernelTime": 120156250,
              "TotalPageFaultCount": 246547,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664218750,
              "cpu": 78.4375
            },
            "active_processes": 4,
            "cpu_ticks": 784375000,
            "wall_elapsed": 84.50673889999962
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120156250,
              "ThisPeriodTotalUserTime": 664218750,
              "TotalKernelTime": 120156250,
              "TotalPageFaultCount": 247158,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664218750,
              "cpu": 78.4375
            },
            "active_processes": 2,
            "cpu_ticks": 784375000,
            "wall_elapsed": 84.51713139999993
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 664218750,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247160,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664218750,
              "cpu": 78.453125
            },
            "active_processes": 2,
            "cpu_ticks": 784531250,
            "wall_elapsed": 84.52918709999904
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 664375000,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247160,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664375000,
              "cpu": 78.46875
            },
            "active_processes": 2,
            "cpu_ticks": 784687500,
            "wall_elapsed": 84.5394467999995
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 664375000,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247160,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664375000,
              "cpu": 78.46875
            },
            "active_processes": 2,
            "cpu_ticks": 784687500,
            "wall_elapsed": 84.5500878999992
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 664531250,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247160,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664531250,
              "cpu": 78.484375
            },
            "active_processes": 2,
            "cpu_ticks": 784843750,
            "wall_elapsed": 84.56075659999988
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 664687500,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247160,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664687500,
              "cpu": 78.5
            },
            "active_processes": 2,
            "cpu_ticks": 785000000,
            "wall_elapsed": 84.57132309999906
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 664687500,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247160,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664687500,
              "cpu": 78.5
            },
            "active_processes": 2,
            "cpu_ticks": 785000000,
            "wall_elapsed": 84.58198849999826
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 664843750,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247160,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664843750,
              "cpu": 78.515625
            },
            "active_processes": 2,
            "cpu_ticks": 785156250,
            "wall_elapsed": 84.59250939999947
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 664843750,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247160,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664843750,
              "cpu": 78.515625
            },
            "active_processes": 2,
            "cpu_ticks": 785156250,
            "wall_elapsed": 84.60313029999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 664843750,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247160,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 664843750,
              "cpu": 78.515625
            },
            "active_processes": 2,
            "cpu_ticks": 785156250,
            "wall_elapsed": 84.61377619999985
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 665000000,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247160,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 665000000,
              "cpu": 78.53125
            },
            "active_processes": 2,
            "cpu_ticks": 785312500,
            "wall_elapsed": 84.62394889999996
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 665156250,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247161,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 665156250,
              "cpu": 78.546875
            },
            "active_processes": 2,
            "cpu_ticks": 785468750,
            "wall_elapsed": 84.6344500999985
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 665156250,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247166,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 665156250,
              "cpu": 78.546875
            },
            "active_processes": 2,
            "cpu_ticks": 785468750,
            "wall_elapsed": 84.6455707999994
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 665312500,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247173,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 665312500,
              "cpu": 78.5625
            },
            "active_processes": 2,
            "cpu_ticks": 785625000,
            "wall_elapsed": 84.65608949999842
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 665468750,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247608,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 665468750,
              "cpu": 78.578125
            },
            "active_processes": 2,
            "cpu_ticks": 785781250,
            "wall_elapsed": 84.66656739999962
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 665468750,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247608,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 665468750,
              "cpu": 78.578125
            },
            "active_processes": 0,
            "cpu_ticks": 785781250,
            "wall_elapsed": 84.6770491999996
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 120312500,
              "ThisPeriodTotalUserTime": 665468750,
              "TotalKernelTime": 120312500,
              "TotalPageFaultCount": 247608,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 665468750,
              "cpu": 78.578125
            },
            "active_processes": 0,
            "cpu_ticks": 785781250,
            "wall_elapsed": 84.67706859999998
          }
        ],
        "stop_reason": "NATURAL_EXIT",
        "strict_zero_overshoot": "NOT_CLAIMED",
        "supervisor_cpu_scope": "CURRENT_PROCESS_USER_PLUS_KERNEL_WINDOW_EXCLUDED_FROM_JOB; MAY_INCLUDE_OTHER_CONCURRENT_WORK",
        "supervisor_cpu_ticks": 5937500,
        "supervisor_cpu_window_end": "RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE",
        "supervisor_cpu_window_start": "BEFORE_WORKER_CREATION",
        "termination_attempted": false,
        "termination_error": null,
        "termination_latency": null,
        "termination_reason": "WORKER_EXITED",
        "termination_requested": false,
        "termination_result": null,
        "total_cpu_hard_limit": "RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY",
        "total_cpu_ticks": 785781250,
        "total_kernel_ticks": 120312500,
        "total_user_ticks": 665468750,
        "user_cpu_limit_ticks": null,
        "wall_elapsed": 84.67722019999928,
        "wall_elapsed_at_stop_request": null,
        "wall_elapsed_at_tree_exit": 84.6770491999996,
        "wall_limit_seconds": 1500.0,
        "worker_exit_code": 0,
        "worker_exit_status": 0
      },
      "counts": {
        "ACTUAL_STEP": 0,
        "ACTUAL_WLS": 0,
        "ASSIGNMENT_EXACT_SOLVER": 2,
        "MODEL_OBSERVATION_WLS": 61,
        "MODEL_POLICY_EVALUATION_WLS": 742,
        "MODEL_SOLVER_START": 7227,
        "R_CALLS": 2
      },
      "raw_net": -0.7331120450139224
    },
    {
      "name": "H3_KEEP",
      "run_id": "EXT005_H3_KEEP_RUN_001",
      "attempt_id": "EXT005_H3_KEEP_001",
      "branch_id": "EXT005_H3_KEEP_BRANCH_001",
      "valid_cell_candidate": true,
      "status": "VALID_CELL_CANDIDATE",
      "returncode": 0,
      "stdout": "{\"status\": \"OUTER_CONTROL_COMPLETE\", \"parent_start_calls\": 1, \"parent_exit\": 0}\n",
      "stderr": "",
      "outer": {
        "actions": [
          {
            "elapsed": 54.15896590000011,
            "fallback": false,
            "kind": "JOB_CLOSE",
            "result": "SUCCEEDED"
          }
        ],
        "approval_sha256": "f81b338b3e40ed25c1dfdeb2fc0e67a47e84ed460b332fdf3acf43328b2725cc",
        "attempt_id": "EXT005_H3_KEEP_001",
        "elapsed_seconds": 54.158989100000326,
        "ended_utc": "2026-11-13T11:05:42.222264+00:00",
        "errors": [],
        "final_outer_accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 89531250,
          "ThisPeriodTotalUserTime": 421562500,
          "TotalKernelTime": 89531250,
          "TotalPageFaultCount": 255424,
          "TotalProcesses": 10,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 421562500,
          "cpu": 51.109375
        },
        "handle_waits": [
          {
            "pid": 24956,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 20324,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 28136,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 15972,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 29760,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 28060,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 21336,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 31088,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 19432,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 22964,
            "remedial_termination_attempted": false,
            "wait_status": 0
          }
        ],
        "identities": [
          {
            "creation_ticks": 134390414880664851,
            "member": true,
            "pid": 24956,
            "role": "LOCAL_DEV_PARENT_SUSPENDED"
          },
          {
            "creation_ticks": 134390414880664851,
            "member": true,
            "pid": 24956,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414880704776,
            "member": true,
            "pid": 20324,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414884146643,
            "member": true,
            "pid": 28136,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414884215828,
            "member": true,
            "pid": 15972,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414884410399,
            "member": true,
            "pid": 29760,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414884464350,
            "member": true,
            "pid": 28060,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414887223048,
            "member": true,
            "pid": 21336,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390414887307603,
            "member": true,
            "pid": 31088,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390415420869697,
            "member": true,
            "pid": 19432,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390415420936795,
            "member": true,
            "pid": 22964,
            "role": "RETAINED_OUTER_MEMBER"
          }
        ],
        "job_handle_diagnostic": 352,
        "job_handle_state": "CLOSED",
        "outer_wall_seconds": 1560,
        "parent_exit_code": 0,
        "parent_start_calls": 1,
        "parent_wait_status": 0,
        "process_tree_exit_confirmed": true,
        "production_admission": "RUN_ADMISSION_BLOCKED",
        "run_id": "EXT005_H3_KEEP_RUN_001",
        "started_utc": "2026-11-13T11:04:48.063275+00:00",
        "status": "OUTER_CONTROL_COMPLETE",
        "timed_out": false
      },
      "inner": {
        "accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 85625000,
          "ThisPeriodTotalUserTime": 419843750,
          "TotalKernelTime": 85625000,
          "TotalPageFaultCount": 209375,
          "TotalProcesses": 6,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 419843750,
          "cpu": 50.546875
        },
        "accounting_status": "FINAL_VALID",
        "active_processes_final": 0,
        "attempt_identity": "EXT005_H3_KEEP_001",
        "cpu_limit_ticks": 12000000000,
        "cpu_overshoot_ticks": 0,
        "cpu_scope": "WHOLE_JOB",
        "cpu_semantics": "TOTAL_CPU_SECONDS",
        "cpu_ticks_at_trigger": null,
        "errors": [],
        "events": [
          "GUARD_CONFIGURED",
          "WORKER_CONTAINED",
          "WORKER_RESUMED",
          "RUNNING_MONITORED",
          "PROCESS_TREE_EXIT_CONFIRMED",
          "FINAL_ACCOUNTING"
        ],
        "evidence_completeness_status": "COMPLETE_IN_MEMORY",
        "execution_entry": "RUN_MONITORED",
        "fallback_close_attempted": false,
        "fallback_close_error_if_any": null,
        "fallback_close_result": null,
        "final_cpu_ticks": 505468750,
        "job_cleanup_status": "PASS",
        "job_handle_state": "JOB_HANDLE_CLOSED",
        "last_valid_cpu_sample": {
          "accounting": {
            "ActiveProcesses": 0,
            "ThisPeriodTotalKernelTime": 85625000,
            "ThisPeriodTotalUserTime": 419843750,
            "TotalKernelTime": 85625000,
            "TotalPageFaultCount": 209375,
            "TotalProcesses": 6,
            "TotalTerminatedProcesses": 0,
            "TotalUserTime": 419843750,
            "cpu": 50.546875
          },
          "active_processes": 0,
          "cpu_ticks": 505468750,
          "wall_elapsed": 53.76576170000044
        },
        "last_valid_cpu_ticks": 505468750,
        "last_valid_wall_sample": 53.765871999999945,
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
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 416718750,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 176173,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 416718750,
              "cpu": 49.9375
            },
            "active_processes": 2,
            "cpu_ticks": 499375000,
            "wall_elapsed": 53.106138799999826
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 416718750,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 176557,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 416718750,
              "cpu": 49.9375
            },
            "active_processes": 2,
            "cpu_ticks": 499375000,
            "wall_elapsed": 53.11638959999982
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 416875000,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 176930,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 416875000,
              "cpu": 49.953125
            },
            "active_processes": 2,
            "cpu_ticks": 499531250,
            "wall_elapsed": 53.12692059999972
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 417031250,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 177314,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 417031250,
              "cpu": 49.96875
            },
            "active_processes": 2,
            "cpu_ticks": 499687500,
            "wall_elapsed": 53.137404200000674
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 417031250,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 177616,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 417031250,
              "cpu": 49.96875
            },
            "active_processes": 2,
            "cpu_ticks": 499687500,
            "wall_elapsed": 53.14806250000038
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 417187500,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 177963,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 417187500,
              "cpu": 49.984375
            },
            "active_processes": 2,
            "cpu_ticks": 499843750,
            "wall_elapsed": 53.158513099999254
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 417343750,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 178316,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 417343750,
              "cpu": 50.0
            },
            "active_processes": 2,
            "cpu_ticks": 500000000,
            "wall_elapsed": 53.16877360000035
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 417343750,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 178749,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 417343750,
              "cpu": 50.0
            },
            "active_processes": 2,
            "cpu_ticks": 500000000,
            "wall_elapsed": 53.18059979999998
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 417500000,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 179166,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 417500000,
              "cpu": 50.015625
            },
            "active_processes": 2,
            "cpu_ticks": 500156250,
            "wall_elapsed": 53.19257839999955
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 417656250,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 179554,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 417656250,
              "cpu": 50.03125
            },
            "active_processes": 2,
            "cpu_ticks": 500312500,
            "wall_elapsed": 53.203133799999705
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 417812500,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 179940,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 417812500,
              "cpu": 50.046875
            },
            "active_processes": 2,
            "cpu_ticks": 500468750,
            "wall_elapsed": 53.213794499999494
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 417812500,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 180151,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 417812500,
              "cpu": 50.046875
            },
            "active_processes": 2,
            "cpu_ticks": 500468750,
            "wall_elapsed": 53.2241154000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 417968750,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 180186,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 417968750,
              "cpu": 50.0625
            },
            "active_processes": 2,
            "cpu_ticks": 500625000,
            "wall_elapsed": 53.23567220000041
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 418125000,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 180224,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418125000,
              "cpu": 50.078125
            },
            "active_processes": 2,
            "cpu_ticks": 500781250,
            "wall_elapsed": 53.24648139999954
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 418125000,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 180324,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418125000,
              "cpu": 50.078125
            },
            "active_processes": 2,
            "cpu_ticks": 500781250,
            "wall_elapsed": 53.258000300000276
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 418281250,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 180324,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418281250,
              "cpu": 50.09375
            },
            "active_processes": 2,
            "cpu_ticks": 500937500,
            "wall_elapsed": 53.269762800000535
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 418437500,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 180324,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418437500,
              "cpu": 50.109375
            },
            "active_processes": 2,
            "cpu_ticks": 501093750,
            "wall_elapsed": 53.28191440000046
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 418593750,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 180324,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418593750,
              "cpu": 50.125
            },
            "active_processes": 2,
            "cpu_ticks": 501250000,
            "wall_elapsed": 53.29207470000074
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 418593750,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 180498,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418593750,
              "cpu": 50.125
            },
            "active_processes": 2,
            "cpu_ticks": 501250000,
            "wall_elapsed": 53.30219670000042
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82656250,
              "ThisPeriodTotalUserTime": 418750000,
              "TotalKernelTime": 82656250,
              "TotalPageFaultCount": 180673,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418750000,
              "cpu": 50.140625
            },
            "active_processes": 2,
            "cpu_ticks": 501406250,
            "wall_elapsed": 53.31246950000059
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82812500,
              "ThisPeriodTotalUserTime": 418750000,
              "TotalKernelTime": 82812500,
              "TotalPageFaultCount": 180681,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418750000,
              "cpu": 50.15625
            },
            "active_processes": 2,
            "cpu_ticks": 501562500,
            "wall_elapsed": 53.32303460000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82812500,
              "ThisPeriodTotalUserTime": 418750000,
              "TotalKernelTime": 82812500,
              "TotalPageFaultCount": 180690,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418750000,
              "cpu": 50.15625
            },
            "active_processes": 2,
            "cpu_ticks": 501562500,
            "wall_elapsed": 53.333248099999764
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82812500,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 82812500,
              "TotalPageFaultCount": 180728,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.171875
            },
            "active_processes": 2,
            "cpu_ticks": 501718750,
            "wall_elapsed": 53.34361739999986
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82968750,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 82968750,
              "TotalPageFaultCount": 185692,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.1875
            },
            "active_processes": 2,
            "cpu_ticks": 501875000,
            "wall_elapsed": 53.354754399999365
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 82968750,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 82968750,
              "TotalPageFaultCount": 185695,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.1875
            },
            "active_processes": 2,
            "cpu_ticks": 501875000,
            "wall_elapsed": 53.36534030000075
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 83125000,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 83125000,
              "TotalPageFaultCount": 187261,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.203125
            },
            "active_processes": 2,
            "cpu_ticks": 502031250,
            "wall_elapsed": 53.37570919999962
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 83125000,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 83125000,
              "TotalPageFaultCount": 187272,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.203125
            },
            "active_processes": 2,
            "cpu_ticks": 502031250,
            "wall_elapsed": 53.38630709999961
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 83125000,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 83125000,
              "TotalPageFaultCount": 187272,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.203125
            },
            "active_processes": 2,
            "cpu_ticks": 502031250,
            "wall_elapsed": 53.39646840000023
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 83281250,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 83281250,
              "TotalPageFaultCount": 187275,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.21875
            },
            "active_processes": 2,
            "cpu_ticks": 502187500,
            "wall_elapsed": 53.406601099999534
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 83437500,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 83437500,
              "TotalPageFaultCount": 187458,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.234375
            },
            "active_processes": 2,
            "cpu_ticks": 502343750,
            "wall_elapsed": 53.417191900000034
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 83437500,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 83437500,
              "TotalPageFaultCount": 192389,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.234375
            },
            "active_processes": 2,
            "cpu_ticks": 502343750,
            "wall_elapsed": 53.4283802000009
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 83593750,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 83593750,
              "TotalPageFaultCount": 192389,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.25
            },
            "active_processes": 2,
            "cpu_ticks": 502500000,
            "wall_elapsed": 53.44014529999913
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 83750000,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 83750000,
              "TotalPageFaultCount": 192396,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.265625
            },
            "active_processes": 2,
            "cpu_ticks": 502656250,
            "wall_elapsed": 53.45074080000086
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 83750000,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 83750000,
              "TotalPageFaultCount": 192396,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.265625
            },
            "active_processes": 2,
            "cpu_ticks": 502656250,
            "wall_elapsed": 53.46098999999958
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 83906250,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 83906250,
              "TotalPageFaultCount": 192669,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.28125
            },
            "active_processes": 2,
            "cpu_ticks": 502812500,
            "wall_elapsed": 53.471132799999396
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84062500,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 84062500,
              "TotalPageFaultCount": 192956,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.296875
            },
            "active_processes": 2,
            "cpu_ticks": 502968750,
            "wall_elapsed": 53.48152819999996
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84062500,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 84062500,
              "TotalPageFaultCount": 194077,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.296875
            },
            "active_processes": 2,
            "cpu_ticks": 502968750,
            "wall_elapsed": 53.49206570000024
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84218750,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 84218750,
              "TotalPageFaultCount": 194148,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.3125
            },
            "active_processes": 2,
            "cpu_ticks": 503125000,
            "wall_elapsed": 53.50245609999911
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84375000,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 84375000,
              "TotalPageFaultCount": 195085,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.328125
            },
            "active_processes": 2,
            "cpu_ticks": 503281250,
            "wall_elapsed": 53.51264099999935
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84375000,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 84375000,
              "TotalPageFaultCount": 195085,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.328125
            },
            "active_processes": 2,
            "cpu_ticks": 503281250,
            "wall_elapsed": 53.523234300000695
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84531250,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 84531250,
              "TotalPageFaultCount": 197050,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.34375
            },
            "active_processes": 2,
            "cpu_ticks": 503437500,
            "wall_elapsed": 53.53356309999981
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84687500,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 84687500,
              "TotalPageFaultCount": 197055,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.359375
            },
            "active_processes": 2,
            "cpu_ticks": 503593750,
            "wall_elapsed": 53.543891299999814
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84687500,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 84687500,
              "TotalPageFaultCount": 197306,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.359375
            },
            "active_processes": 2,
            "cpu_ticks": 503593750,
            "wall_elapsed": 53.55420910000066
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84843750,
              "ThisPeriodTotalUserTime": 418906250,
              "TotalKernelTime": 84843750,
              "TotalPageFaultCount": 198359,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 418906250,
              "cpu": 50.375
            },
            "active_processes": 2,
            "cpu_ticks": 503750000,
            "wall_elapsed": 53.564560700000584
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84843750,
              "ThisPeriodTotalUserTime": 419062500,
              "TotalKernelTime": 84843750,
              "TotalPageFaultCount": 198404,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419062500,
              "cpu": 50.390625
            },
            "active_processes": 2,
            "cpu_ticks": 503906250,
            "wall_elapsed": 53.57513909999943
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 84843750,
              "ThisPeriodTotalUserTime": 419062500,
              "TotalKernelTime": 84843750,
              "TotalPageFaultCount": 199423,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419062500,
              "cpu": 50.390625
            },
            "active_processes": 2,
            "cpu_ticks": 503906250,
            "wall_elapsed": 53.585458699999435
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85000000,
              "ThisPeriodTotalUserTime": 419062500,
              "TotalKernelTime": 85000000,
              "TotalPageFaultCount": 200334,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419062500,
              "cpu": 50.40625
            },
            "active_processes": 2,
            "cpu_ticks": 504062500,
            "wall_elapsed": 53.59585949999928
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85000000,
              "ThisPeriodTotalUserTime": 419218750,
              "TotalKernelTime": 85000000,
              "TotalPageFaultCount": 202040,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419218750,
              "cpu": 50.421875
            },
            "active_processes": 2,
            "cpu_ticks": 504218750,
            "wall_elapsed": 53.606412799999816
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85000000,
              "ThisPeriodTotalUserTime": 419218750,
              "TotalKernelTime": 85000000,
              "TotalPageFaultCount": 202041,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419218750,
              "cpu": 50.421875
            },
            "active_processes": 2,
            "cpu_ticks": 504218750,
            "wall_elapsed": 53.616935699999885
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85000000,
              "ThisPeriodTotalUserTime": 419375000,
              "TotalKernelTime": 85000000,
              "TotalPageFaultCount": 202663,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419375000,
              "cpu": 50.4375
            },
            "active_processes": 2,
            "cpu_ticks": 504375000,
            "wall_elapsed": 53.62702089999948
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85156250,
              "ThisPeriodTotalUserTime": 419375000,
              "TotalKernelTime": 85156250,
              "TotalPageFaultCount": 204446,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419375000,
              "cpu": 50.453125
            },
            "active_processes": 2,
            "cpu_ticks": 504531250,
            "wall_elapsed": 53.63905049999994
          },
          {
            "accounting": {
              "ActiveProcesses": 3,
              "ThisPeriodTotalKernelTime": 85156250,
              "ThisPeriodTotalUserTime": 419375000,
              "TotalKernelTime": 85156250,
              "TotalPageFaultCount": 205391,
              "TotalProcesses": 5,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419375000,
              "cpu": 50.453125
            },
            "active_processes": 3,
            "cpu_ticks": 504531250,
            "wall_elapsed": 53.64913010000055
          },
          {
            "accounting": {
              "ActiveProcesses": 4,
              "ThisPeriodTotalKernelTime": 85156250,
              "ThisPeriodTotalUserTime": 419531250,
              "TotalKernelTime": 85156250,
              "TotalPageFaultCount": 207960,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419531250,
              "cpu": 50.46875
            },
            "active_processes": 4,
            "cpu_ticks": 504687500,
            "wall_elapsed": 53.65944069999932
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85312500,
              "ThisPeriodTotalUserTime": 419531250,
              "TotalKernelTime": 85312500,
              "TotalPageFaultCount": 208618,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419531250,
              "cpu": 50.484375
            },
            "active_processes": 2,
            "cpu_ticks": 504843750,
            "wall_elapsed": 53.669574999999895
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85312500,
              "ThisPeriodTotalUserTime": 419531250,
              "TotalKernelTime": 85312500,
              "TotalPageFaultCount": 208927,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419531250,
              "cpu": 50.484375
            },
            "active_processes": 2,
            "cpu_ticks": 504843750,
            "wall_elapsed": 53.679901999999856
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85468750,
              "ThisPeriodTotalUserTime": 419531250,
              "TotalKernelTime": 85468750,
              "TotalPageFaultCount": 208927,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419531250,
              "cpu": 50.5
            },
            "active_processes": 2,
            "cpu_ticks": 505000000,
            "wall_elapsed": 53.690228400000706
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85468750,
              "ThisPeriodTotalUserTime": 419687500,
              "TotalKernelTime": 85468750,
              "TotalPageFaultCount": 208927,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419687500,
              "cpu": 50.515625
            },
            "active_processes": 2,
            "cpu_ticks": 505156250,
            "wall_elapsed": 53.70273549999911
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85468750,
              "ThisPeriodTotalUserTime": 419687500,
              "TotalKernelTime": 85468750,
              "TotalPageFaultCount": 208927,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419687500,
              "cpu": 50.515625
            },
            "active_processes": 2,
            "cpu_ticks": 505156250,
            "wall_elapsed": 53.713198999999804
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85625000,
              "ThisPeriodTotalUserTime": 419687500,
              "TotalKernelTime": 85625000,
              "TotalPageFaultCount": 208928,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419687500,
              "cpu": 50.53125
            },
            "active_processes": 2,
            "cpu_ticks": 505312500,
            "wall_elapsed": 53.72370770000089
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85625000,
              "ThisPeriodTotalUserTime": 419687500,
              "TotalKernelTime": 85625000,
              "TotalPageFaultCount": 208933,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419687500,
              "cpu": 50.53125
            },
            "active_processes": 2,
            "cpu_ticks": 505312500,
            "wall_elapsed": 53.73477459999958
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 85625000,
              "ThisPeriodTotalUserTime": 419843750,
              "TotalKernelTime": 85625000,
              "TotalPageFaultCount": 209114,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419843750,
              "cpu": 50.546875
            },
            "active_processes": 2,
            "cpu_ticks": 505468750,
            "wall_elapsed": 53.745188200000484
          },
          {
            "accounting": {
              "ActiveProcesses": 1,
              "ThisPeriodTotalKernelTime": 85625000,
              "ThisPeriodTotalUserTime": 419843750,
              "TotalKernelTime": 85625000,
              "TotalPageFaultCount": 209375,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419843750,
              "cpu": 50.546875
            },
            "active_processes": 1,
            "cpu_ticks": 505468750,
            "wall_elapsed": 53.755435600000055
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 85625000,
              "ThisPeriodTotalUserTime": 419843750,
              "TotalKernelTime": 85625000,
              "TotalPageFaultCount": 209375,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419843750,
              "cpu": 50.546875
            },
            "active_processes": 0,
            "cpu_ticks": 505468750,
            "wall_elapsed": 53.765750200000184
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 85625000,
              "ThisPeriodTotalUserTime": 419843750,
              "TotalKernelTime": 85625000,
              "TotalPageFaultCount": 209375,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 419843750,
              "cpu": 50.546875
            },
            "active_processes": 0,
            "cpu_ticks": 505468750,
            "wall_elapsed": 53.76576170000044
          }
        ],
        "stop_reason": "NATURAL_EXIT",
        "strict_zero_overshoot": "NOT_CLAIMED",
        "supervisor_cpu_scope": "CURRENT_PROCESS_USER_PLUS_KERNEL_WINDOW_EXCLUDED_FROM_JOB; MAY_INCLUDE_OTHER_CONCURRENT_WORK",
        "supervisor_cpu_ticks": 1875000,
        "supervisor_cpu_window_end": "RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE",
        "supervisor_cpu_window_start": "BEFORE_WORKER_CREATION",
        "termination_attempted": false,
        "termination_error": null,
        "termination_latency": null,
        "termination_reason": "WORKER_EXITED",
        "termination_requested": false,
        "termination_result": null,
        "total_cpu_hard_limit": "RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY",
        "total_cpu_ticks": 505468750,
        "total_kernel_ticks": 85625000,
        "total_user_ticks": 419843750,
        "user_cpu_limit_ticks": null,
        "wall_elapsed": 53.76587180000024,
        "wall_elapsed_at_stop_request": null,
        "wall_elapsed_at_tree_exit": 53.765750200000184,
        "wall_limit_seconds": 1500.0,
        "worker_exit_code": 0,
        "worker_exit_status": 0
      },
      "counts": {
        "ACTUAL_STEP": 0,
        "ACTUAL_WLS": 0,
        "ASSIGNMENT_EXACT_SOLVER": 2,
        "MODEL_OBSERVATION_WLS": 33,
        "MODEL_POLICY_EVALUATION_WLS": 590,
        "MODEL_SOLVER_START": 5607,
        "R_CALLS": 2
      },
      "raw_net": -0.3150141073101529
    },
    {
      "name": "H3_SWITCH",
      "run_id": "EXT005_H3_SWITCH_RUN_001",
      "attempt_id": "EXT005_H3_SWITCH_001",
      "branch_id": "EXT005_H3_SWITCH_BRANCH_001",
      "valid_cell_candidate": true,
      "status": "VALID_CELL_CANDIDATE",
      "returncode": 0,
      "stdout": "{\"status\": \"OUTER_CONTROL_COMPLETE\", \"parent_start_calls\": 1, \"parent_exit\": 0}\n",
      "stderr": "",
      "outer": {
        "actions": [
          {
            "elapsed": 76.09204390000014,
            "fallback": false,
            "kind": "JOB_CLOSE",
            "result": "SUCCEEDED"
          }
        ],
        "approval_sha256": "0a59cf125f7e05ffad42079fc55ae10558e2dac0864dae999ef51800e80c7ab2",
        "attempt_id": "EXT005_H3_SWITCH_001",
        "elapsed_seconds": 76.09206379999887,
        "ended_utc": "2026-11-13T11:06:59.511237+00:00",
        "errors": [],
        "final_outer_accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 117343750,
          "ThisPeriodTotalUserTime": 600156250,
          "TotalKernelTime": 117343750,
          "TotalPageFaultCount": 287284,
          "TotalProcesses": 10,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 600156250,
          "cpu": 71.75
        },
        "handle_waits": [
          {
            "pid": 30028,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 30676,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 29440,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 29388,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 30508,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 4440,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 26908,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 15832,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 24568,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 25020,
            "remedial_termination_attempted": false,
            "wait_status": 0
          }
        ],
        "identities": [
          {
            "creation_ticks": 134390415434221917,
            "member": true,
            "pid": 30028,
            "role": "LOCAL_DEV_PARENT_SUSPENDED"
          },
          {
            "creation_ticks": 134390415434221917,
            "member": true,
            "pid": 30028,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390415434262284,
            "member": true,
            "pid": 30676,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390415436971560,
            "member": true,
            "pid": 29440,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390415437038729,
            "member": true,
            "pid": 29388,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390415437228251,
            "member": true,
            "pid": 30508,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390415437282470,
            "member": true,
            "pid": 4440,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390415439982246,
            "member": true,
            "pid": 26908,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390415440050844,
            "member": true,
            "pid": 15832,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390416193561122,
            "member": true,
            "pid": 24568,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390416193637145,
            "member": true,
            "pid": 25020,
            "role": "RETAINED_OUTER_MEMBER"
          }
        ],
        "job_handle_diagnostic": 500,
        "job_handle_state": "CLOSED",
        "outer_wall_seconds": 1560,
        "parent_exit_code": 0,
        "parent_start_calls": 1,
        "parent_wait_status": 0,
        "process_tree_exit_confirmed": true,
        "production_admission": "RUN_ADMISSION_BLOCKED",
        "run_id": "EXT005_H3_SWITCH_RUN_001",
        "started_utc": "2026-11-13T11:05:43.419168+00:00",
        "status": "OUTER_CONTROL_COMPLETE",
        "timed_out": false
      },
      "inner": {
        "accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 111718750,
          "ThisPeriodTotalUserTime": 598750000,
          "TotalKernelTime": 111718750,
          "TotalPageFaultCount": 242233,
          "TotalProcesses": 6,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 598750000,
          "cpu": 71.046875
        },
        "accounting_status": "FINAL_VALID",
        "active_processes_final": 0,
        "attempt_identity": "EXT005_H3_SWITCH_001",
        "cpu_limit_ticks": 12000000000,
        "cpu_overshoot_ticks": 0,
        "cpu_scope": "WHOLE_JOB",
        "cpu_semantics": "TOTAL_CPU_SECONDS",
        "cpu_ticks_at_trigger": null,
        "errors": [],
        "events": [
          "GUARD_CONFIGURED",
          "WORKER_CONTAINED",
          "WORKER_RESUMED",
          "RUNNING_MONITORED",
          "PROCESS_TREE_EXIT_CONFIRMED",
          "FINAL_ACCOUNTING"
        ],
        "evidence_completeness_status": "COMPLETE_IN_MEMORY",
        "execution_entry": "RUN_MONITORED",
        "fallback_close_attempted": false,
        "fallback_close_error_if_any": null,
        "fallback_close_result": null,
        "final_cpu_ticks": 710468750,
        "job_cleanup_status": "PASS",
        "job_handle_state": "JOB_HANDLE_CLOSED",
        "last_valid_cpu_sample": {
          "accounting": {
            "ActiveProcesses": 0,
            "ThisPeriodTotalKernelTime": 111718750,
            "ThisPeriodTotalUserTime": 598750000,
            "TotalKernelTime": 111718750,
            "TotalPageFaultCount": 242233,
            "TotalProcesses": 6,
            "TotalTerminatedProcesses": 0,
            "TotalUserTime": 598750000,
            "cpu": 71.046875
          },
          "active_processes": 0,
          "cpu_ticks": 710468750,
          "wall_elapsed": 75.77149999999892
        },
        "last_valid_cpu_ticks": 710468750,
        "last_valid_wall_sample": 75.77161259999957,
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
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 594218750,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 210124,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 594218750,
              "cpu": 70.421875
            },
            "active_processes": 2,
            "cpu_ticks": 704218750,
            "wall_elapsed": 75.11965469999996
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 594218750,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 210440,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 594218750,
              "cpu": 70.421875
            },
            "active_processes": 2,
            "cpu_ticks": 704218750,
            "wall_elapsed": 75.13037969999823
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 594375000,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 210798,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 594375000,
              "cpu": 70.4375
            },
            "active_processes": 2,
            "cpu_ticks": 704375000,
            "wall_elapsed": 75.14083789999859
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 594531250,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 211171,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 594531250,
              "cpu": 70.453125
            },
            "active_processes": 2,
            "cpu_ticks": 704531250,
            "wall_elapsed": 75.15122259999953
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 594531250,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 211555,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 594531250,
              "cpu": 70.453125
            },
            "active_processes": 2,
            "cpu_ticks": 704531250,
            "wall_elapsed": 75.16155139999864
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 594687500,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 211926,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 594687500,
              "cpu": 70.46875
            },
            "active_processes": 2,
            "cpu_ticks": 704687500,
            "wall_elapsed": 75.17216179999923
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 594843750,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 212290,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 594843750,
              "cpu": 70.484375
            },
            "active_processes": 2,
            "cpu_ticks": 704843750,
            "wall_elapsed": 75.18283419999898
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 594843750,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 212668,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 594843750,
              "cpu": 70.484375
            },
            "active_processes": 2,
            "cpu_ticks": 704843750,
            "wall_elapsed": 75.19310679999944
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 595000000,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 212795,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595000000,
              "cpu": 70.5
            },
            "active_processes": 2,
            "cpu_ticks": 705000000,
            "wall_elapsed": 75.20386289999988
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 595156250,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 212796,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595156250,
              "cpu": 70.515625
            },
            "active_processes": 2,
            "cpu_ticks": 705156250,
            "wall_elapsed": 75.21421279999959
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 595156250,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 212796,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595156250,
              "cpu": 70.515625
            },
            "active_processes": 2,
            "cpu_ticks": 705156250,
            "wall_elapsed": 75.2243256999991
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 595312500,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 212856,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595312500,
              "cpu": 70.53125
            },
            "active_processes": 2,
            "cpu_ticks": 705312500,
            "wall_elapsed": 75.23629509999955
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 595468750,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 212856,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595468750,
              "cpu": 70.546875
            },
            "active_processes": 2,
            "cpu_ticks": 705468750,
            "wall_elapsed": 75.24663969999892
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110000000,
              "ThisPeriodTotalUserTime": 595468750,
              "TotalKernelTime": 110000000,
              "TotalPageFaultCount": 212856,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595468750,
              "cpu": 70.546875
            },
            "active_processes": 2,
            "cpu_ticks": 705468750,
            "wall_elapsed": 75.25708959999974
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110156250,
              "ThisPeriodTotalUserTime": 595468750,
              "TotalKernelTime": 110156250,
              "TotalPageFaultCount": 212856,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595468750,
              "cpu": 70.5625
            },
            "active_processes": 2,
            "cpu_ticks": 705625000,
            "wall_elapsed": 75.2675180999995
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110156250,
              "ThisPeriodTotalUserTime": 595625000,
              "TotalKernelTime": 110156250,
              "TotalPageFaultCount": 212856,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595625000,
              "cpu": 70.578125
            },
            "active_processes": 2,
            "cpu_ticks": 705781250,
            "wall_elapsed": 75.27848799999992
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110156250,
              "ThisPeriodTotalUserTime": 595625000,
              "TotalKernelTime": 110156250,
              "TotalPageFaultCount": 212856,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595625000,
              "cpu": 70.578125
            },
            "active_processes": 2,
            "cpu_ticks": 705781250,
            "wall_elapsed": 75.28909329999988
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110156250,
              "ThisPeriodTotalUserTime": 595625000,
              "TotalKernelTime": 110156250,
              "TotalPageFaultCount": 213070,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595625000,
              "cpu": 70.578125
            },
            "active_processes": 2,
            "cpu_ticks": 705781250,
            "wall_elapsed": 75.29984849999892
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110156250,
              "ThisPeriodTotalUserTime": 595781250,
              "TotalKernelTime": 110156250,
              "TotalPageFaultCount": 213356,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595781250,
              "cpu": 70.59375
            },
            "active_processes": 2,
            "cpu_ticks": 705937500,
            "wall_elapsed": 75.31005919999916
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110156250,
              "ThisPeriodTotalUserTime": 595781250,
              "TotalKernelTime": 110156250,
              "TotalPageFaultCount": 213361,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595781250,
              "cpu": 70.59375
            },
            "active_processes": 2,
            "cpu_ticks": 705937500,
            "wall_elapsed": 75.32066899999882
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110156250,
              "ThisPeriodTotalUserTime": 595937500,
              "TotalKernelTime": 110156250,
              "TotalPageFaultCount": 213377,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 595937500,
              "cpu": 70.609375
            },
            "active_processes": 2,
            "cpu_ticks": 706093750,
            "wall_elapsed": 75.33112529999926
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110156250,
              "ThisPeriodTotalUserTime": 596093750,
              "TotalKernelTime": 110156250,
              "TotalPageFaultCount": 213469,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596093750,
              "cpu": 70.625
            },
            "active_processes": 2,
            "cpu_ticks": 706250000,
            "wall_elapsed": 75.34121409999898
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110156250,
              "ThisPeriodTotalUserTime": 596093750,
              "TotalKernelTime": 110156250,
              "TotalPageFaultCount": 218433,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596093750,
              "cpu": 70.625
            },
            "active_processes": 2,
            "cpu_ticks": 706250000,
            "wall_elapsed": 75.3516172999989
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110312500,
              "ThisPeriodTotalUserTime": 596093750,
              "TotalKernelTime": 110312500,
              "TotalPageFaultCount": 218433,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596093750,
              "cpu": 70.640625
            },
            "active_processes": 2,
            "cpu_ticks": 706406250,
            "wall_elapsed": 75.3619734999993
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110312500,
              "ThisPeriodTotalUserTime": 596250000,
              "TotalKernelTime": 110312500,
              "TotalPageFaultCount": 220003,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596250000,
              "cpu": 70.65625
            },
            "active_processes": 2,
            "cpu_ticks": 706562500,
            "wall_elapsed": 75.37226509999891
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110312500,
              "ThisPeriodTotalUserTime": 596250000,
              "TotalKernelTime": 110312500,
              "TotalPageFaultCount": 220004,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596250000,
              "cpu": 70.65625
            },
            "active_processes": 2,
            "cpu_ticks": 706562500,
            "wall_elapsed": 75.38280939999822
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110312500,
              "ThisPeriodTotalUserTime": 596406250,
              "TotalKernelTime": 110312500,
              "TotalPageFaultCount": 220006,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596406250,
              "cpu": 70.671875
            },
            "active_processes": 2,
            "cpu_ticks": 706718750,
            "wall_elapsed": 75.39349269999911
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110312500,
              "ThisPeriodTotalUserTime": 596562500,
              "TotalKernelTime": 110312500,
              "TotalPageFaultCount": 220006,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596562500,
              "cpu": 70.6875
            },
            "active_processes": 2,
            "cpu_ticks": 706875000,
            "wall_elapsed": 75.40404279999893
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110312500,
              "ThisPeriodTotalUserTime": 596562500,
              "TotalKernelTime": 110312500,
              "TotalPageFaultCount": 220025,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596562500,
              "cpu": 70.6875
            },
            "active_processes": 2,
            "cpu_ticks": 706875000,
            "wall_elapsed": 75.41461919999892
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110312500,
              "ThisPeriodTotalUserTime": 596718750,
              "TotalKernelTime": 110312500,
              "TotalPageFaultCount": 224956,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596718750,
              "cpu": 70.703125
            },
            "active_processes": 2,
            "cpu_ticks": 707031250,
            "wall_elapsed": 75.42637509999986
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110468750,
              "ThisPeriodTotalUserTime": 596718750,
              "TotalKernelTime": 110468750,
              "TotalPageFaultCount": 224956,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596718750,
              "cpu": 70.71875
            },
            "active_processes": 2,
            "cpu_ticks": 707187500,
            "wall_elapsed": 75.43669569999838
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110468750,
              "ThisPeriodTotalUserTime": 596875000,
              "TotalKernelTime": 110468750,
              "TotalPageFaultCount": 224961,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596875000,
              "cpu": 70.734375
            },
            "active_processes": 2,
            "cpu_ticks": 707343750,
            "wall_elapsed": 75.44717309999942
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110468750,
              "ThisPeriodTotalUserTime": 596875000,
              "TotalKernelTime": 110468750,
              "TotalPageFaultCount": 225296,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 596875000,
              "cpu": 70.734375
            },
            "active_processes": 2,
            "cpu_ticks": 707343750,
            "wall_elapsed": 75.45741899999848
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110468750,
              "ThisPeriodTotalUserTime": 597031250,
              "TotalKernelTime": 110468750,
              "TotalPageFaultCount": 225427,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597031250,
              "cpu": 70.75
            },
            "active_processes": 2,
            "cpu_ticks": 707500000,
            "wall_elapsed": 75.46786969999994
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110468750,
              "ThisPeriodTotalUserTime": 597187500,
              "TotalKernelTime": 110468750,
              "TotalPageFaultCount": 226304,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597187500,
              "cpu": 70.765625
            },
            "active_processes": 2,
            "cpu_ticks": 707656250,
            "wall_elapsed": 75.47800789999928
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110468750,
              "ThisPeriodTotalUserTime": 597187500,
              "TotalKernelTime": 110468750,
              "TotalPageFaultCount": 227067,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597187500,
              "cpu": 70.765625
            },
            "active_processes": 2,
            "cpu_ticks": 707656250,
            "wall_elapsed": 75.48835109999891
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110468750,
              "ThisPeriodTotalUserTime": 597343750,
              "TotalKernelTime": 110468750,
              "TotalPageFaultCount": 228064,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597343750,
              "cpu": 70.78125
            },
            "active_processes": 2,
            "cpu_ticks": 707812500,
            "wall_elapsed": 75.49884829999974
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110468750,
              "ThisPeriodTotalUserTime": 597500000,
              "TotalKernelTime": 110468750,
              "TotalPageFaultCount": 228064,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597500000,
              "cpu": 70.796875
            },
            "active_processes": 2,
            "cpu_ticks": 707968750,
            "wall_elapsed": 75.50922289999835
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110468750,
              "ThisPeriodTotalUserTime": 597500000,
              "TotalKernelTime": 110468750,
              "TotalPageFaultCount": 230030,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597500000,
              "cpu": 70.796875
            },
            "active_processes": 2,
            "cpu_ticks": 707968750,
            "wall_elapsed": 75.5195780999984
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110625000,
              "ThisPeriodTotalUserTime": 597500000,
              "TotalKernelTime": 110625000,
              "TotalPageFaultCount": 230037,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597500000,
              "cpu": 70.8125
            },
            "active_processes": 2,
            "cpu_ticks": 708125000,
            "wall_elapsed": 75.53019769999992
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110781250,
              "ThisPeriodTotalUserTime": 597500000,
              "TotalKernelTime": 110781250,
              "TotalPageFaultCount": 230075,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597500000,
              "cpu": 70.828125
            },
            "active_processes": 2,
            "cpu_ticks": 708281250,
            "wall_elapsed": 75.54036499999893
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110781250,
              "ThisPeriodTotalUserTime": 597500000,
              "TotalKernelTime": 110781250,
              "TotalPageFaultCount": 231123,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597500000,
              "cpu": 70.828125
            },
            "active_processes": 2,
            "cpu_ticks": 708281250,
            "wall_elapsed": 75.5509134999993
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110937500,
              "ThisPeriodTotalUserTime": 597500000,
              "TotalKernelTime": 110937500,
              "TotalPageFaultCount": 231123,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597500000,
              "cpu": 70.84375
            },
            "active_processes": 2,
            "cpu_ticks": 708437500,
            "wall_elapsed": 75.56161449999854
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110937500,
              "ThisPeriodTotalUserTime": 597656250,
              "TotalKernelTime": 110937500,
              "TotalPageFaultCount": 232142,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597656250,
              "cpu": 70.859375
            },
            "active_processes": 2,
            "cpu_ticks": 708593750,
            "wall_elapsed": 75.57213709999996
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110937500,
              "ThisPeriodTotalUserTime": 597656250,
              "TotalKernelTime": 110937500,
              "TotalPageFaultCount": 233414,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597656250,
              "cpu": 70.859375
            },
            "active_processes": 2,
            "cpu_ticks": 708593750,
            "wall_elapsed": 75.58253049999985
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110937500,
              "ThisPeriodTotalUserTime": 597812500,
              "TotalKernelTime": 110937500,
              "TotalPageFaultCount": 234759,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597812500,
              "cpu": 70.875
            },
            "active_processes": 2,
            "cpu_ticks": 708750000,
            "wall_elapsed": 75.59306649999962
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110937500,
              "ThisPeriodTotalUserTime": 597968750,
              "TotalKernelTime": 110937500,
              "TotalPageFaultCount": 234759,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597968750,
              "cpu": 70.890625
            },
            "active_processes": 2,
            "cpu_ticks": 708906250,
            "wall_elapsed": 75.60361959999864
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 110937500,
              "ThisPeriodTotalUserTime": 597968750,
              "TotalKernelTime": 110937500,
              "TotalPageFaultCount": 235382,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597968750,
              "cpu": 70.890625
            },
            "active_processes": 2,
            "cpu_ticks": 708906250,
            "wall_elapsed": 75.61400029999822
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111093750,
              "ThisPeriodTotalUserTime": 597968750,
              "TotalKernelTime": 111093750,
              "TotalPageFaultCount": 237165,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597968750,
              "cpu": 70.90625
            },
            "active_processes": 2,
            "cpu_ticks": 709062500,
            "wall_elapsed": 75.6242076999988
          },
          {
            "accounting": {
              "ActiveProcesses": 3,
              "ThisPeriodTotalKernelTime": 111250000,
              "ThisPeriodTotalUserTime": 597968750,
              "TotalKernelTime": 111250000,
              "TotalPageFaultCount": 238022,
              "TotalProcesses": 5,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597968750,
              "cpu": 70.921875
            },
            "active_processes": 3,
            "cpu_ticks": 709218750,
            "wall_elapsed": 75.63482019999901
          },
          {
            "accounting": {
              "ActiveProcesses": 4,
              "ThisPeriodTotalKernelTime": 111250000,
              "ThisPeriodTotalUserTime": 597968750,
              "TotalKernelTime": 111250000,
              "TotalPageFaultCount": 239900,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597968750,
              "cpu": 70.921875
            },
            "active_processes": 4,
            "cpu_ticks": 709218750,
            "wall_elapsed": 75.64538939999875
          },
          {
            "accounting": {
              "ActiveProcesses": 3,
              "ThisPeriodTotalKernelTime": 111406250,
              "ThisPeriodTotalUserTime": 597968750,
              "TotalKernelTime": 111406250,
              "TotalPageFaultCount": 241355,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597968750,
              "cpu": 70.9375
            },
            "active_processes": 3,
            "cpu_ticks": 709375000,
            "wall_elapsed": 75.6555085
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111406250,
              "ThisPeriodTotalUserTime": 597968750,
              "TotalKernelTime": 111406250,
              "TotalPageFaultCount": 241775,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597968750,
              "cpu": 70.9375
            },
            "active_processes": 2,
            "cpu_ticks": 709375000,
            "wall_elapsed": 75.66572439999982
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111562500,
              "ThisPeriodTotalUserTime": 597968750,
              "TotalKernelTime": 111562500,
              "TotalPageFaultCount": 241775,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597968750,
              "cpu": 70.953125
            },
            "active_processes": 2,
            "cpu_ticks": 709531250,
            "wall_elapsed": 75.67620249999891
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111718750,
              "ThisPeriodTotalUserTime": 597968750,
              "TotalKernelTime": 111718750,
              "TotalPageFaultCount": 241775,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 597968750,
              "cpu": 70.96875
            },
            "active_processes": 2,
            "cpu_ticks": 709687500,
            "wall_elapsed": 75.68642589999945
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111718750,
              "ThisPeriodTotalUserTime": 598125000,
              "TotalKernelTime": 111718750,
              "TotalPageFaultCount": 241775,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 598125000,
              "cpu": 70.984375
            },
            "active_processes": 2,
            "cpu_ticks": 709843750,
            "wall_elapsed": 75.69734209999842
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111718750,
              "ThisPeriodTotalUserTime": 598125000,
              "TotalKernelTime": 111718750,
              "TotalPageFaultCount": 241775,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 598125000,
              "cpu": 70.984375
            },
            "active_processes": 2,
            "cpu_ticks": 709843750,
            "wall_elapsed": 75.7080479999986
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111718750,
              "ThisPeriodTotalUserTime": 598281250,
              "TotalKernelTime": 111718750,
              "TotalPageFaultCount": 241775,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 598281250,
              "cpu": 71.0
            },
            "active_processes": 2,
            "cpu_ticks": 710000000,
            "wall_elapsed": 75.71849089999887
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111718750,
              "ThisPeriodTotalUserTime": 598437500,
              "TotalKernelTime": 111718750,
              "TotalPageFaultCount": 241786,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 598437500,
              "cpu": 71.015625
            },
            "active_processes": 2,
            "cpu_ticks": 710156250,
            "wall_elapsed": 75.72896629999923
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111718750,
              "ThisPeriodTotalUserTime": 598437500,
              "TotalKernelTime": 111718750,
              "TotalPageFaultCount": 241789,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 598437500,
              "cpu": 71.015625
            },
            "active_processes": 2,
            "cpu_ticks": 710156250,
            "wall_elapsed": 75.74025759999859
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111718750,
              "ThisPeriodTotalUserTime": 598593750,
              "TotalKernelTime": 111718750,
              "TotalPageFaultCount": 241791,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 598593750,
              "cpu": 71.03125
            },
            "active_processes": 2,
            "cpu_ticks": 710312500,
            "wall_elapsed": 75.75079599999845
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 111718750,
              "ThisPeriodTotalUserTime": 598750000,
              "TotalKernelTime": 111718750,
              "TotalPageFaultCount": 242233,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 598750000,
              "cpu": 71.046875
            },
            "active_processes": 2,
            "cpu_ticks": 710468750,
            "wall_elapsed": 75.76138369999899
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 111718750,
              "ThisPeriodTotalUserTime": 598750000,
              "TotalKernelTime": 111718750,
              "TotalPageFaultCount": 242233,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 598750000,
              "cpu": 71.046875
            },
            "active_processes": 0,
            "cpu_ticks": 710468750,
            "wall_elapsed": 75.77148539999871
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 111718750,
              "ThisPeriodTotalUserTime": 598750000,
              "TotalKernelTime": 111718750,
              "TotalPageFaultCount": 242233,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 598750000,
              "cpu": 71.046875
            },
            "active_processes": 0,
            "cpu_ticks": 710468750,
            "wall_elapsed": 75.77149999999892
          }
        ],
        "stop_reason": "NATURAL_EXIT",
        "strict_zero_overshoot": "NOT_CLAIMED",
        "supervisor_cpu_scope": "CURRENT_PROCESS_USER_PLUS_KERNEL_WINDOW_EXCLUDED_FROM_JOB; MAY_INCLUDE_OTHER_CONCURRENT_WORK",
        "supervisor_cpu_ticks": 4062500,
        "supervisor_cpu_window_end": "RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE",
        "supervisor_cpu_window_start": "BEFORE_WORKER_CREATION",
        "termination_attempted": false,
        "termination_error": null,
        "termination_latency": null,
        "termination_reason": "WORKER_EXITED",
        "termination_requested": false,
        "termination_result": null,
        "total_cpu_hard_limit": "RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY",
        "total_cpu_ticks": 710468750,
        "total_kernel_ticks": 111718750,
        "total_user_ticks": 598750000,
        "user_cpu_limit_ticks": null,
        "wall_elapsed": 75.77161239999987,
        "wall_elapsed_at_stop_request": null,
        "wall_elapsed_at_tree_exit": 75.77148539999871,
        "wall_limit_seconds": 1500.0,
        "worker_exit_code": 0,
        "worker_exit_status": 0
      },
      "counts": {
        "ACTUAL_STEP": 0,
        "ACTUAL_WLS": 0,
        "ASSIGNMENT_EXACT_SOLVER": 2,
        "MODEL_OBSERVATION_WLS": 51,
        "MODEL_POLICY_EVALUATION_WLS": 722,
        "MODEL_SOLVER_START": 6957,
        "R_CALLS": 2
      },
      "raw_net": -0.157503491576509
    },
    {
      "name": "H3_MEMBER_CHANGE",
      "run_id": "EXT005_H3_MEMBER_CHANGE_RUN_001",
      "attempt_id": "EXT005_H3_MEMBER_CHANGE_001",
      "branch_id": "EXT005_H3_MEMBER_CHANGE_BRANCH_001",
      "valid_cell_candidate": true,
      "status": "VALID_CELL_CANDIDATE",
      "returncode": 0,
      "stdout": "{\"status\": \"OUTER_CONTROL_COMPLETE\", \"parent_start_calls\": 1, \"parent_exit\": 0}\n",
      "stderr": "",
      "outer": {
        "actions": [
          {
            "elapsed": 96.17779420000079,
            "fallback": false,
            "kind": "JOB_CLOSE",
            "result": "SUCCEEDED"
          }
        ],
        "approval_sha256": "d0af18164026fa27f89af9bd4b67ff4590810436e7fdd9fc315eab1104e7e5e2",
        "attempt_id": "EXT005_H3_MEMBER_CHANGE_001",
        "elapsed_seconds": 96.17781570000079,
        "ended_utc": "2026-11-13T11:08:36.888466+00:00",
        "errors": [],
        "final_outer_accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 143437500,
          "ThisPeriodTotalUserTime": 765468750,
          "TotalKernelTime": 143437500,
          "TotalPageFaultCount": 294082,
          "TotalProcesses": 10,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 765468750,
          "cpu": 90.890625
        },
        "handle_waits": [
          {
            "pid": 30608,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 29332,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 16960,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 6880,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 24864,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 7944,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 17100,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 30008,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 27728,
            "remedial_termination_attempted": false,
            "wait_status": 0
          },
          {
            "pid": 28256,
            "remedial_termination_attempted": false,
            "wait_status": 0
          }
        ],
        "identities": [
          {
            "creation_ticks": 134390416207132198,
            "member": true,
            "pid": 30608,
            "role": "LOCAL_DEV_PARENT_SUSPENDED"
          },
          {
            "creation_ticks": 134390416207132198,
            "member": true,
            "pid": 30608,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390416207176034,
            "member": true,
            "pid": 29332,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390416210266882,
            "member": true,
            "pid": 16960,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390416210354189,
            "member": true,
            "pid": 6880,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390416210616963,
            "member": true,
            "pid": 24864,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390416210704430,
            "member": true,
            "pid": 7944,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390416214110460,
            "member": true,
            "pid": 17100,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390416214176183,
            "member": true,
            "pid": 30008,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390417167022576,
            "member": true,
            "pid": 27728,
            "role": "RETAINED_OUTER_MEMBER"
          },
          {
            "creation_ticks": 134390417167125976,
            "member": true,
            "pid": 28256,
            "role": "RETAINED_OUTER_MEMBER"
          }
        ],
        "job_handle_diagnostic": 464,
        "job_handle_state": "CLOSED",
        "outer_wall_seconds": 1560,
        "parent_exit_code": 0,
        "parent_start_calls": 1,
        "parent_wait_status": 0,
        "process_tree_exit_confirmed": true,
        "production_admission": "RUN_ADMISSION_BLOCKED",
        "run_id": "EXT005_H3_MEMBER_CHANGE_RUN_001",
        "started_utc": "2026-11-13T11:07:00.710649+00:00",
        "status": "OUTER_CONTROL_COMPLETE",
        "timed_out": false
      },
      "inner": {
        "accounting": {
          "ActiveProcesses": 0,
          "ThisPeriodTotalKernelTime": 134375000,
          "ThisPeriodTotalUserTime": 759687500,
          "TotalKernelTime": 134375000,
          "TotalPageFaultCount": 248766,
          "TotalProcesses": 6,
          "TotalTerminatedProcesses": 0,
          "TotalUserTime": 759687500,
          "cpu": 89.40625
        },
        "accounting_status": "FINAL_VALID",
        "active_processes_final": 0,
        "attempt_identity": "EXT005_H3_MEMBER_CHANGE_001",
        "cpu_limit_ticks": 12000000000,
        "cpu_overshoot_ticks": 0,
        "cpu_scope": "WHOLE_JOB",
        "cpu_semantics": "TOTAL_CPU_SECONDS",
        "cpu_ticks_at_trigger": null,
        "errors": [],
        "events": [
          "GUARD_CONFIGURED",
          "WORKER_CONTAINED",
          "WORKER_RESUMED",
          "RUNNING_MONITORED",
          "PROCESS_TREE_EXIT_CONFIRMED",
          "FINAL_ACCOUNTING"
        ],
        "evidence_completeness_status": "COMPLETE_IN_MEMORY",
        "execution_entry": "RUN_MONITORED",
        "fallback_close_attempted": false,
        "fallback_close_error_if_any": null,
        "fallback_close_result": null,
        "final_cpu_ticks": 894062500,
        "job_cleanup_status": "PASS",
        "job_handle_state": "JOB_HANDLE_CLOSED",
        "last_valid_cpu_sample": {
          "accounting": {
            "ActiveProcesses": 0,
            "ThisPeriodTotalKernelTime": 134375000,
            "ThisPeriodTotalUserTime": 759687500,
            "TotalKernelTime": 134375000,
            "TotalPageFaultCount": 248766,
            "TotalProcesses": 6,
            "TotalTerminatedProcesses": 0,
            "TotalUserTime": 759687500,
            "cpu": 89.40625
          },
          "active_processes": 0,
          "cpu_ticks": 894062500,
          "wall_elapsed": 95.80636100000083
        },
        "last_valid_cpu_ticks": 894062500,
        "last_valid_wall_sample": 95.80647230000068,
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
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 756093750,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219263,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 756093750,
              "cpu": 88.78125
            },
            "active_processes": 2,
            "cpu_ticks": 887812500,
            "wall_elapsed": 95.15486080000119
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 756093750,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219310,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 756093750,
              "cpu": 88.78125
            },
            "active_processes": 2,
            "cpu_ticks": 887812500,
            "wall_elapsed": 95.16533090000121
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 756250000,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219360,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 756250000,
              "cpu": 88.796875
            },
            "active_processes": 2,
            "cpu_ticks": 887968750,
            "wall_elapsed": 95.17584540000098
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 756250000,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219471,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 756250000,
              "cpu": 88.796875
            },
            "active_processes": 2,
            "cpu_ticks": 887968750,
            "wall_elapsed": 95.18644420000055
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 756406250,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219471,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 756406250,
              "cpu": 88.8125
            },
            "active_processes": 2,
            "cpu_ticks": 888125000,
            "wall_elapsed": 95.19697890000134
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 756562500,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219471,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 756562500,
              "cpu": 88.828125
            },
            "active_processes": 2,
            "cpu_ticks": 888281250,
            "wall_elapsed": 95.20740450000085
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 756562500,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219471,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 756562500,
              "cpu": 88.828125
            },
            "active_processes": 2,
            "cpu_ticks": 888281250,
            "wall_elapsed": 95.21794730000147
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 756718750,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219471,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 756718750,
              "cpu": 88.84375
            },
            "active_processes": 2,
            "cpu_ticks": 888437500,
            "wall_elapsed": 95.22849550000137
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 756875000,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219471,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 756875000,
              "cpu": 88.859375
            },
            "active_processes": 2,
            "cpu_ticks": 888593750,
            "wall_elapsed": 95.238916100001
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 757031250,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219606,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757031250,
              "cpu": 88.875
            },
            "active_processes": 2,
            "cpu_ticks": 888750000,
            "wall_elapsed": 95.24941540000145
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 757031250,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219608,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757031250,
              "cpu": 88.875
            },
            "active_processes": 2,
            "cpu_ticks": 888750000,
            "wall_elapsed": 95.26004530000137
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131718750,
              "ThisPeriodTotalUserTime": 757187500,
              "TotalKernelTime": 131718750,
              "TotalPageFaultCount": 219800,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757187500,
              "cpu": 88.890625
            },
            "active_processes": 2,
            "cpu_ticks": 888906250,
            "wall_elapsed": 95.27037800000107
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131875000,
              "ThisPeriodTotalUserTime": 757187500,
              "TotalKernelTime": 131875000,
              "TotalPageFaultCount": 219805,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757187500,
              "cpu": 88.90625
            },
            "active_processes": 2,
            "cpu_ticks": 889062500,
            "wall_elapsed": 95.2805341000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131875000,
              "ThisPeriodTotalUserTime": 757187500,
              "TotalKernelTime": 131875000,
              "TotalPageFaultCount": 219813,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757187500,
              "cpu": 88.90625
            },
            "active_processes": 2,
            "cpu_ticks": 889062500,
            "wall_elapsed": 95.29084030000013
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131875000,
              "ThisPeriodTotalUserTime": 757187500,
              "TotalKernelTime": 131875000,
              "TotalPageFaultCount": 219813,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757187500,
              "cpu": 88.90625
            },
            "active_processes": 2,
            "cpu_ticks": 889062500,
            "wall_elapsed": 95.30132290000074
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131875000,
              "ThisPeriodTotalUserTime": 757343750,
              "TotalKernelTime": 131875000,
              "TotalPageFaultCount": 219870,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757343750,
              "cpu": 88.921875
            },
            "active_processes": 2,
            "cpu_ticks": 889218750,
            "wall_elapsed": 95.31188170000132
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131875000,
              "ThisPeriodTotalUserTime": 757343750,
              "TotalKernelTime": 131875000,
              "TotalPageFaultCount": 224829,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757343750,
              "cpu": 88.921875
            },
            "active_processes": 2,
            "cpu_ticks": 889218750,
            "wall_elapsed": 95.32242020000012
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 131875000,
              "ThisPeriodTotalUserTime": 757500000,
              "TotalKernelTime": 131875000,
              "TotalPageFaultCount": 224829,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757500000,
              "cpu": 88.9375
            },
            "active_processes": 2,
            "cpu_ticks": 889375000,
            "wall_elapsed": 95.33293220000087
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132031250,
              "ThisPeriodTotalUserTime": 757500000,
              "TotalKernelTime": 132031250,
              "TotalPageFaultCount": 226396,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757500000,
              "cpu": 88.953125
            },
            "active_processes": 2,
            "cpu_ticks": 889531250,
            "wall_elapsed": 95.34333490000063
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132031250,
              "ThisPeriodTotalUserTime": 757500000,
              "TotalKernelTime": 132031250,
              "TotalPageFaultCount": 226400,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757500000,
              "cpu": 88.953125
            },
            "active_processes": 2,
            "cpu_ticks": 889531250,
            "wall_elapsed": 95.35389270000087
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132187500,
              "ThisPeriodTotalUserTime": 757500000,
              "TotalKernelTime": 132187500,
              "TotalPageFaultCount": 226418,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757500000,
              "cpu": 88.96875
            },
            "active_processes": 2,
            "cpu_ticks": 889687500,
            "wall_elapsed": 95.36461210000016
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132343750,
              "ThisPeriodTotalUserTime": 757500000,
              "TotalKernelTime": 132343750,
              "TotalPageFaultCount": 226422,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757500000,
              "cpu": 88.984375
            },
            "active_processes": 2,
            "cpu_ticks": 889843750,
            "wall_elapsed": 95.37494090000109
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132343750,
              "ThisPeriodTotalUserTime": 757500000,
              "TotalKernelTime": 132343750,
              "TotalPageFaultCount": 226422,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757500000,
              "cpu": 88.984375
            },
            "active_processes": 2,
            "cpu_ticks": 889843750,
            "wall_elapsed": 95.38544550000006
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132343750,
              "ThisPeriodTotalUserTime": 757656250,
              "TotalKernelTime": 132343750,
              "TotalPageFaultCount": 226434,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757656250,
              "cpu": 89.0
            },
            "active_processes": 2,
            "cpu_ticks": 890000000,
            "wall_elapsed": 95.39560660000097
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132343750,
              "ThisPeriodTotalUserTime": 757812500,
              "TotalKernelTime": 132343750,
              "TotalPageFaultCount": 231365,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757812500,
              "cpu": 89.015625
            },
            "active_processes": 2,
            "cpu_ticks": 890156250,
            "wall_elapsed": 95.40672410000116
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132343750,
              "ThisPeriodTotalUserTime": 757812500,
              "TotalKernelTime": 132343750,
              "TotalPageFaultCount": 231365,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757812500,
              "cpu": 89.015625
            },
            "active_processes": 2,
            "cpu_ticks": 890156250,
            "wall_elapsed": 95.41715960000147
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132500000,
              "ThisPeriodTotalUserTime": 757812500,
              "TotalKernelTime": 132500000,
              "TotalPageFaultCount": 231365,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757812500,
              "cpu": 89.03125
            },
            "active_processes": 2,
            "cpu_ticks": 890312500,
            "wall_elapsed": 95.42756470000131
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132656250,
              "ThisPeriodTotalUserTime": 757812500,
              "TotalKernelTime": 132656250,
              "TotalPageFaultCount": 231365,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757812500,
              "cpu": 89.046875
            },
            "active_processes": 2,
            "cpu_ticks": 890468750,
            "wall_elapsed": 95.43795870000031
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132656250,
              "ThisPeriodTotalUserTime": 757812500,
              "TotalKernelTime": 132656250,
              "TotalPageFaultCount": 231773,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757812500,
              "cpu": 89.046875
            },
            "active_processes": 2,
            "cpu_ticks": 890468750,
            "wall_elapsed": 95.44845330000135
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132656250,
              "ThisPeriodTotalUserTime": 757968750,
              "TotalKernelTime": 132656250,
              "TotalPageFaultCount": 232214,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757968750,
              "cpu": 89.0625
            },
            "active_processes": 2,
            "cpu_ticks": 890625000,
            "wall_elapsed": 95.45901700000104
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132812500,
              "ThisPeriodTotalUserTime": 757968750,
              "TotalKernelTime": 132812500,
              "TotalPageFaultCount": 233195,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757968750,
              "cpu": 89.078125
            },
            "active_processes": 2,
            "cpu_ticks": 890781250,
            "wall_elapsed": 95.4695685000006
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132812500,
              "ThisPeriodTotalUserTime": 757968750,
              "TotalKernelTime": 132812500,
              "TotalPageFaultCount": 233306,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757968750,
              "cpu": 89.078125
            },
            "active_processes": 2,
            "cpu_ticks": 890781250,
            "wall_elapsed": 95.47998150000058
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 132968750,
              "ThisPeriodTotalUserTime": 757968750,
              "TotalKernelTime": 132968750,
              "TotalPageFaultCount": 234092,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757968750,
              "cpu": 89.09375
            },
            "active_processes": 2,
            "cpu_ticks": 890937500,
            "wall_elapsed": 95.49054419999993
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133125000,
              "ThisPeriodTotalUserTime": 757968750,
              "TotalKernelTime": 133125000,
              "TotalPageFaultCount": 234092,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757968750,
              "cpu": 89.109375
            },
            "active_processes": 2,
            "cpu_ticks": 891093750,
            "wall_elapsed": 95.5010938000014
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133125000,
              "ThisPeriodTotalUserTime": 757968750,
              "TotalKernelTime": 133125000,
              "TotalPageFaultCount": 236043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757968750,
              "cpu": 89.109375
            },
            "active_processes": 2,
            "cpu_ticks": 891093750,
            "wall_elapsed": 95.51146020000124
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133281250,
              "ThisPeriodTotalUserTime": 757968750,
              "TotalKernelTime": 133281250,
              "TotalPageFaultCount": 236043,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 757968750,
              "cpu": 89.125
            },
            "active_processes": 2,
            "cpu_ticks": 891250000,
            "wall_elapsed": 95.52182130000074
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133281250,
              "ThisPeriodTotalUserTime": 758125000,
              "TotalKernelTime": 133281250,
              "TotalPageFaultCount": 236354,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758125000,
              "cpu": 89.140625
            },
            "active_processes": 2,
            "cpu_ticks": 891406250,
            "wall_elapsed": 95.5323169000003
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133281250,
              "ThisPeriodTotalUserTime": 758125000,
              "TotalKernelTime": 133281250,
              "TotalPageFaultCount": 237401,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758125000,
              "cpu": 89.140625
            },
            "active_processes": 2,
            "cpu_ticks": 891406250,
            "wall_elapsed": 95.54277110000112
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133437500,
              "ThisPeriodTotalUserTime": 758125000,
              "TotalKernelTime": 133437500,
              "TotalPageFaultCount": 237626,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758125000,
              "cpu": 89.15625
            },
            "active_processes": 2,
            "cpu_ticks": 891562500,
            "wall_elapsed": 95.55328460000055
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133593750,
              "ThisPeriodTotalUserTime": 758125000,
              "TotalKernelTime": 133593750,
              "TotalPageFaultCount": 237626,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758125000,
              "cpu": 89.171875
            },
            "active_processes": 2,
            "cpu_ticks": 891718750,
            "wall_elapsed": 95.56379480000032
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133593750,
              "ThisPeriodTotalUserTime": 758125000,
              "TotalKernelTime": 133593750,
              "TotalPageFaultCount": 238645,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758125000,
              "cpu": 89.171875
            },
            "active_processes": 2,
            "cpu_ticks": 891718750,
            "wall_elapsed": 95.57425030000013
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133593750,
              "ThisPeriodTotalUserTime": 758281250,
              "TotalKernelTime": 133593750,
              "TotalPageFaultCount": 239561,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758281250,
              "cpu": 89.1875
            },
            "active_processes": 2,
            "cpu_ticks": 891875000,
            "wall_elapsed": 95.58486360000097
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133593750,
              "ThisPeriodTotalUserTime": 758437500,
              "TotalKernelTime": 133593750,
              "TotalPageFaultCount": 241269,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758437500,
              "cpu": 89.203125
            },
            "active_processes": 2,
            "cpu_ticks": 892031250,
            "wall_elapsed": 95.59545849999995
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133593750,
              "ThisPeriodTotalUserTime": 758437500,
              "TotalKernelTime": 133593750,
              "TotalPageFaultCount": 241269,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758437500,
              "cpu": 89.203125
            },
            "active_processes": 2,
            "cpu_ticks": 892031250,
            "wall_elapsed": 95.60590180000145
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133593750,
              "ThisPeriodTotalUserTime": 758593750,
              "TotalKernelTime": 133593750,
              "TotalPageFaultCount": 241894,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758593750,
              "cpu": 89.21875
            },
            "active_processes": 2,
            "cpu_ticks": 892187500,
            "wall_elapsed": 95.6164727000014
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133750000,
              "ThisPeriodTotalUserTime": 758593750,
              "TotalKernelTime": 133750000,
              "TotalPageFaultCount": 241894,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758593750,
              "cpu": 89.234375
            },
            "active_processes": 2,
            "cpu_ticks": 892343750,
            "wall_elapsed": 95.62703280000096
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133750000,
              "ThisPeriodTotalUserTime": 758593750,
              "TotalKernelTime": 133750000,
              "TotalPageFaultCount": 244011,
              "TotalProcesses": 4,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758593750,
              "cpu": 89.234375
            },
            "active_processes": 2,
            "cpu_ticks": 892343750,
            "wall_elapsed": 95.63759050000044
          },
          {
            "accounting": {
              "ActiveProcesses": 3,
              "ThisPeriodTotalKernelTime": 133906250,
              "ThisPeriodTotalUserTime": 758593750,
              "TotalKernelTime": 133906250,
              "TotalPageFaultCount": 244633,
              "TotalProcesses": 5,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758593750,
              "cpu": 89.25
            },
            "active_processes": 3,
            "cpu_ticks": 892500000,
            "wall_elapsed": 95.64798130000054
          },
          {
            "accounting": {
              "ActiveProcesses": 4,
              "ThisPeriodTotalKernelTime": 133906250,
              "ThisPeriodTotalUserTime": 758750000,
              "TotalKernelTime": 133906250,
              "TotalPageFaultCount": 246782,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758750000,
              "cpu": 89.265625
            },
            "active_processes": 4,
            "cpu_ticks": 892656250,
            "wall_elapsed": 95.65874990000157
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133906250,
              "ThisPeriodTotalUserTime": 758750000,
              "TotalKernelTime": 133906250,
              "TotalPageFaultCount": 247849,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758750000,
              "cpu": 89.265625
            },
            "active_processes": 2,
            "cpu_ticks": 892656250,
            "wall_elapsed": 95.66899420000118
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 133906250,
              "ThisPeriodTotalUserTime": 758750000,
              "TotalKernelTime": 133906250,
              "TotalPageFaultCount": 248316,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758750000,
              "cpu": 89.265625
            },
            "active_processes": 2,
            "cpu_ticks": 892656250,
            "wall_elapsed": 95.67971810000017
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134062500,
              "ThisPeriodTotalUserTime": 758750000,
              "TotalKernelTime": 134062500,
              "TotalPageFaultCount": 248318,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758750000,
              "cpu": 89.28125
            },
            "active_processes": 2,
            "cpu_ticks": 892812500,
            "wall_elapsed": 95.69038189999992
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134062500,
              "ThisPeriodTotalUserTime": 758750000,
              "TotalKernelTime": 134062500,
              "TotalPageFaultCount": 248318,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758750000,
              "cpu": 89.28125
            },
            "active_processes": 2,
            "cpu_ticks": 892812500,
            "wall_elapsed": 95.7007491000004
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134218750,
              "ThisPeriodTotalUserTime": 758750000,
              "TotalKernelTime": 134218750,
              "TotalPageFaultCount": 248318,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758750000,
              "cpu": 89.296875
            },
            "active_processes": 2,
            "cpu_ticks": 892968750,
            "wall_elapsed": 95.71124980000059
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134375000,
              "ThisPeriodTotalUserTime": 758750000,
              "TotalKernelTime": 134375000,
              "TotalPageFaultCount": 248318,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758750000,
              "cpu": 89.3125
            },
            "active_processes": 2,
            "cpu_ticks": 893125000,
            "wall_elapsed": 95.72192460000042
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134375000,
              "ThisPeriodTotalUserTime": 758750000,
              "TotalKernelTime": 134375000,
              "TotalPageFaultCount": 248318,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758750000,
              "cpu": 89.3125
            },
            "active_processes": 2,
            "cpu_ticks": 893125000,
            "wall_elapsed": 95.73229360000005
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134375000,
              "ThisPeriodTotalUserTime": 758906250,
              "TotalKernelTime": 134375000,
              "TotalPageFaultCount": 248318,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 758906250,
              "cpu": 89.328125
            },
            "active_processes": 2,
            "cpu_ticks": 893281250,
            "wall_elapsed": 95.74338119999993
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134375000,
              "ThisPeriodTotalUserTime": 759062500,
              "TotalKernelTime": 134375000,
              "TotalPageFaultCount": 248318,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 759062500,
              "cpu": 89.34375
            },
            "active_processes": 2,
            "cpu_ticks": 893437500,
            "wall_elapsed": 95.7539940000006
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134375000,
              "ThisPeriodTotalUserTime": 759218750,
              "TotalKernelTime": 134375000,
              "TotalPageFaultCount": 248319,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 759218750,
              "cpu": 89.359375
            },
            "active_processes": 2,
            "cpu_ticks": 893593750,
            "wall_elapsed": 95.76426460000039
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134375000,
              "ThisPeriodTotalUserTime": 759218750,
              "TotalKernelTime": 134375000,
              "TotalPageFaultCount": 248322,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 759218750,
              "cpu": 89.359375
            },
            "active_processes": 2,
            "cpu_ticks": 893593750,
            "wall_elapsed": 95.77486790000148
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134375000,
              "ThisPeriodTotalUserTime": 759375000,
              "TotalKernelTime": 134375000,
              "TotalPageFaultCount": 248330,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 759375000,
              "cpu": 89.375
            },
            "active_processes": 2,
            "cpu_ticks": 893750000,
            "wall_elapsed": 95.78550580000046
          },
          {
            "accounting": {
              "ActiveProcesses": 2,
              "ThisPeriodTotalKernelTime": 134375000,
              "ThisPeriodTotalUserTime": 759531250,
              "TotalKernelTime": 134375000,
              "TotalPageFaultCount": 248766,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 759531250,
              "cpu": 89.390625
            },
            "active_processes": 2,
            "cpu_ticks": 893906250,
            "wall_elapsed": 95.7958980000003
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 134375000,
              "ThisPeriodTotalUserTime": 759687500,
              "TotalKernelTime": 134375000,
              "TotalPageFaultCount": 248766,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 759687500,
              "cpu": 89.40625
            },
            "active_processes": 0,
            "cpu_ticks": 894062500,
            "wall_elapsed": 95.80634540000028
          },
          {
            "accounting": {
              "ActiveProcesses": 0,
              "ThisPeriodTotalKernelTime": 134375000,
              "ThisPeriodTotalUserTime": 759687500,
              "TotalKernelTime": 134375000,
              "TotalPageFaultCount": 248766,
              "TotalProcesses": 6,
              "TotalTerminatedProcesses": 0,
              "TotalUserTime": 759687500,
              "cpu": 89.40625
            },
            "active_processes": 0,
            "cpu_ticks": 894062500,
            "wall_elapsed": 95.80636100000083
          }
        ],
        "stop_reason": "NATURAL_EXIT",
        "strict_zero_overshoot": "NOT_CLAIMED",
        "supervisor_cpu_scope": "CURRENT_PROCESS_USER_PLUS_KERNEL_WINDOW_EXCLUDED_FROM_JOB; MAY_INCLUDE_OTHER_CONCURRENT_WORK",
        "supervisor_cpu_ticks": 11406250,
        "supervisor_cpu_window_end": "RECEIPT_ASSEMBLY_BEFORE_PERSISTENCE",
        "supervisor_cpu_window_start": "BEFORE_WORKER_CREATION",
        "termination_attempted": false,
        "termination_error": null,
        "termination_latency": null,
        "termination_reason": "WORKER_EXITED",
        "termination_requested": false,
        "termination_result": null,
        "total_cpu_hard_limit": "RUN_CPU_TOTAL_HARD_LIMIT_NOT_READY",
        "total_cpu_ticks": 894062500,
        "total_kernel_ticks": 134375000,
        "total_user_ticks": 759687500,
        "user_cpu_limit_ticks": null,
        "wall_elapsed": 95.80647210000097,
        "wall_elapsed_at_stop_request": null,
        "wall_elapsed_at_tree_exit": 95.80634540000028,
        "wall_limit_seconds": 1500.0,
        "worker_exit_code": 0,
        "worker_exit_status": 0
      },
      "counts": {
        "ACTUAL_STEP": 0,
        "ACTUAL_WLS": 0,
        "ASSIGNMENT_EXACT_SOLVER": 2,
        "MODEL_OBSERVATION_WLS": 61,
        "MODEL_POLICY_EVALUATION_WLS": 742,
        "MODEL_SOLVER_START": 7227,
        "R_CALLS": 2
      },
      "raw_net": -0.7331120450139224
    }
  ],
  "error": null,
  "precheck_receipt": {
    "status": "REUSED_ACCEPTED_EVIDENCE_NOT_RERUN",
    "cpu_ticks": 5625000,
    "wall_seconds": 0.8463298999995459
  },
  "parent_cpu_ticks": 128750000,
  "aux_cpu_ticks": 156250,
  "wall_seconds": 457.52700039999945,
  "faults": [],
  "final_faults": [],
  "retry": false,
  "h1_reused_cells": 3,
  "actual_run": false,
  "h1_rerun": false,
  "minimax_regret": "COMPUTED",
  "production_admission": "BLOCKED",
  "science_scope": "Exploratory finite three-world three-action single-D60 offline MODEL; no statistical or full uncertainty-set guarantee",
  "final_summary_resource_usage": {
    "cpu_ticks": 11250000,
    "cpu_seconds": 1.125,
    "wall_seconds": 1.1977615999985574,
    "total_wall_seconds": 457.8830603999995,
    "storage_bytes": 107481014
  },
  "all_started_processes_exit_confirmed": true
}