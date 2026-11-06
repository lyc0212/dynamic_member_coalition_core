# A0-R first dual-target episode report

One formal run only, 2026-11-05 17:46:47.556 to 17:52:11.993 Asia/Shanghai. Wall duration324.428542 seconds, CLI/worker exit0, SUMMARY PASS. This duration is an observation, not a speedup benchmark.

Command: D:\anaconda3\python.exe -B scripts/run_gq_windows.py --scene configs/gq_windows_two_target_a0.json --output runs/a0_r_both_001 --evaluator both --max-candidates 12 --timeout 1800
Offline acceptance: D:\anaconda3\python.exe -B -m scripts.gq_windows.a0_accept runs/a0_r_both_001

HEAD e628a14dc0a4db6e74197e90b69ab095891549be. Python3.13.5 NumPy2.1.3 SciPy1.15.3. Frozen scene SHA256 ee8045603002d5c0081db91d7de513a9de76349b359095f2d0ccb8aca158a554. All163 source files unchanged against READY aggregate2f345a0b00e8216b74e703a7deae43d8bb1fa6a7c08d95e4c41eb04106156a70; before/after/final checks retained. No scientific source/scenario edits or Git commit/push.

## Results

PAIR_CONSISTENCY PASS; PLAN_OPTIMALITY PASS (both modes, six decisions each); prediction audits36 per mode, decision audits6 per mode, episode audits both PASS. Both reach tick120 TERMINAL; all12 real transactions COMMITTED. No TIMEOUT/truncation. Actual physical and aggregate accounting audited independently by existing episode auditor; no extra independent candidate simulation.

|tick / time(s)|active|candidates|legal plans|best T0 margin|best T1 margin|actual team target|
|---|---|---|---|---|---|---|
|0 / 0|T0,T1|12|13|0.124359214570|0.123941436336|T0|
|20 / 1|T0,T1|12|13|0.181038348744|0.157490547212|T0 KEEP|
|40 / 2|T1|6|7|ended|0.124141774079|T1|
|60 / 3|T1|6|7|ended|0.430824732646|T1 KEEP|
|80 / 4|none|0|1|--|--|IDLE|
|100 / 5|none|0|1|--|--|IDLE|

Margins are exact single-target-plan objective minus all-idle-plan objective, including changes against current Assignment; displayed decimals rounded for readability only. Exact Fractions retained in SCIENCE_OBSERVATIONS.json and ACCEPTANCE.json. At tick0 exact T0 margin=35844103193335981/288230376151711744; T1=35723686815844493/288230376151711744. Thus T1 was deferred despite positive service value because both q2 teams conflict with only3 robots. Same positive competition at tick20. This establishes structural AND actual economic competition in this frozen deterministic example.

U0 dual_neg45 and U1 dual_pos45 serve both targets sequentially; U2 remains idle. Candidate index0 refers to T0 initially and T1 after T0 ends; canonical keys, not repeated index labels, identify targets.

T0 assigned0s, progress0.7 at1s, completed1.35s(tick27), progress1.05. Automatic release, no extra fee. T1 first assigned2s, progress0.2 at3s, completed3.85s(tick77), progress1.05; automatic release. Both deadline2s is soft: T1 is late1.85s, but completed, not timed out/escaped/unfinished. No MEMBER_CHANGE, ROLE_CHANGE, WITHDRAWAL or INTERRUPTED service reset observed. The target switch at2s follows natural completion/release, not service-in-progress member change. Team waits0.65s after T0 completion until next decision; this is a fixed decision-period observation.

Each mode: completed2, escaped0; net return0.16516765531509792; physical return0.20516765531509792; total change fee0.04, four robot Assignment changes (two initial assignments to T0 + two assignments to T1), zero-charge automatic releases. Actual WLS66; occupied6.4 robot-seconds; idle11.6.

Target-attributed rewards (derived from saved physical frames and original reward rules, NOT native per-target ledger output): T0 net approximately0.09935921456963032; T1 approximately0.06580844074546756, including0.02 assignment fee each. T1 lateness penalty0.023125. Derived frame-wise effort summation has tiny rounding differences from native aggregate; native aggregate and strict cross-mode equality are authoritative. Per-target reconstruction metadata/components retained in SCIENCE_OBSERVATIONS.json.

## Interpretation and limits

First frozen deterministic simultaneous-birth dual-target closed loop PASSED with positive resource competition. No claim of dynamic membership superiority, asynchronous-arrival validation, multi-team parallel service, noise robustness, speedup or whole-episode global optimality. Exact optimality is per admitted finite prediction table. The Oracle target-state controller is unchanged. U2 unused and both targets completed sequentially; future asynchronous arrivals and non-Oracle shared prediction remain separately authorized research, not executed here.

Evidence: runs/a0_r_both_001 (raw immutable outputs); reports/a0_r_freeze_001/ACCEPTANCE.json (complete raw acceptance); BEFORE.json, AFTER.json, FINAL_STATE.json (source and Git state); TIMING.json; SCIENCE_OBSERVATIONS.json. Finished and stopped; no second run.
