# A1 first complete non-Oracle episode — 2026-11-05

EXECUTION: COMPLETE.
INFORMATION_BOUNDARY: PASS within source/interface and saved-trace checks.
OBSERVATION_FEEDBACK: EFFECTIVE for serviced target T0; absent for unassigned T1.
R_S_NEW_CONSISTENCY: PASS.
PHYSICAL_OUTCOME: T0 completed late, T1 unserved/unfinished.
A1 first mechanism evidence obtained, not a claim of robust or complete-task superiority. No A2 authorization implied.

## Frozen execution

Local HEAD ba6b6cea2c86bc8a828730eb22e541269a09508c. No remote access. One invocation only:
D:\anaconda3\python.exe -B scripts/run_a1.py --world configs/gq_windows_two_target_a0.json --announcements configs/a1_public_announcements.json --output runs/a1_non_oracle_001 --method both

Launched via approved Start-Process / WaitForExit(1800000) whole-run external guard. Start2026-11-05 18:37:57.571 / end18:40:16.343 Asia/Shanghai. Duration138.7647389 seconds; exit0; no timeout/retry. This is not a performance comparison with A0.

World SHA256 ee8045603002d5c0081db91d7de513a9de76349b359095f2d0ccb8aca158a554; public input994024c75b2fdf70f254b385fff38d999e94016d46eb9adfad35541c87de3021; defined A1 source-range aggregate95b06fc54d8db937eec0a7192fdf63084df76b185060fe31eef731dbc3cee794. BEFORE/AFTER checks identical. No code/input/scenario/A0 evidence edits, tests reruns, Git commit/push or second episode.

## Complete execution and consistency

Both R and S_NEW:6 COMMITTED transactions at ticks0,20,40,60,80,100; final tick120 TERMINAL; full final state/metrics. SUMMARY remains EXECUTION_COMPLETE_NOT_SCIENTIFIC_ACCEPTANCE. PAIR_CHECK PASS verifies exact policy inputs, candidate rows/values/choices and actual STEP with only fixed legitimate runtime mapping. Final net/reward components identical.

|decision time|Assignment|T0 belief|T1 belief|best T0 margin|best T1 margin|actual progress at interval end|
|---|---|---|---|---|---|---|
|0|U0 neg45/U1 pos45 ->T0; U2 idle|PRIOR_ONLY|PRIOR_ONLY|.124374145456|.122706338633|T0=0|
|1|KEEP T0|OBSERVED, tau1.0|PRIOR_ONLY|.155803452303|.139995875199|T0=0|
|2|KEEP T0|OBSERVED, tau2.0|PRIOR_ONLY|.170819809378|.129149955889|T0=.6|
|3|KEEP T0|OBSERVED, tau3.0|PRIOR_ONLY|.437495700875|-.000042080527|T0=1.05, completed3.45|
|4|all IDLE|last observation3.45|PRIOR_ONLY|ended|-.020054728566|T0=1.05;T1=0|
|5|all IDLE|DEGRADED, tau3.45|PRIOR_ONLY|ended|-.020048496213|T1 remains0|

Margins are conditional admitted prediction-table value relative to all-idle, including current Assignment changes. Exact Fraction values retained in ANALYSIS.json. The runtime uses the already frozen production solver; no new independent A1 global-optimality claim.

## Actual observation/feedback

T0 first assignment0s; first actual bearing/WLS0s, first accepted position0s. First valid two-position velocity evidence tick5=.25s; first consumption at tick20=1s. At1s belief changes from prior position(7.8,9.8), velocity(0,0) to observed position(8.4,10), velocity approximately(.4,0). Later updates tau2s,3s,3.45s; last update consumed4s. At5s T0 raw estimate is retained and marked DEGRADED; trajectory accessor clamps extrapolation at tau+1 and returns zero effective velocity, not the raw stored velocity. T0 is already completed at that time.

Each mode consumes70 actual estimates from ticks0..69. All measurement_tick<=available_tick<=consumed_tick; action-preparation tick0 measurements are consumed at1s, not backfilled into D0. T1 never assigned, never measured, remains PRIOR_ONLY with null last_observation_tick. No global initialization deadlock: D0 genuinely allocates T0 from the real prior/model endpoint, not a mocked endpoint.

Finite causal counterfactual uses actual D1 robot U0 position(8.224264068711928,9.447433115769785), fixed role/config, and only stored public beliefs. Prior-only prediction at1s=(7.8,9.8), velocity0 -> control(0,-.07169718448171203). Actual-observation-updated prediction=(8.4,10), velocity about(.4,0) -> control(.9999999999999982,.12830281551828016). Control difference norm1.0198039027185537. No new physical rollout or true-state input is used in this comparison. Actual D1 controls also match the updated snapshot, establishing more than temporal logging correlation.

## Limited independent physical/content checks

Ad hoc read-only scalar reconstruction from saved views/frames, not a new audit framework: every executed control recomputed from frozen belief with the agreed expiry rule; every robot position increment checked against saved control and actual elapsed interval. Maximum control/position residual both0; derived control energy2.0855799331305884 equals native ledger exactly.

Existing audit_fusion reused on all70 actual fusions per mode without rerunning WLS. Independently reconstructed zero-noise bearings from world+robot states: maximum error0. Actual G reconstructed from world, role offsets and observer positions:0 mismatches. Independent Fraction two-endpoint clock first credits interval ending tick49=2.45s, reaches1.05s at tick69=3.45s. Actual Q endpoints49 PASS/21 FAIL; no positive-progress reset event observed. Invalid initial endpoints before progress accumulation are not reported as service resets.

Ledger derived from completion3.45 and unfinished6s: completion+.125, flow-.039375, lateness-.068125, effort-.00004634622073623528, terminal-.25, changes-.02 -> net-.25254634622073624 (native equality within independent arithmetic rounding). No A0 Oracle-control auditor claimed for A1.

Policy-input key scan found no position_now/velocity_now/position_at_birth/turns/arc_rates/private_execution_input. This supplements the source-level separated interfaces, not a universal proof against arbitrary hidden channels. Permitted actual service feedback and self positions remain available. MODEL endpoints cannot enter the actual enqueue path; observed belief diagnostics match actual fusion estimates rather than hypothetical candidates.

## Physical outcomes and interpretation

T0 assigned0, actual G first true2.4s, continuous effective service2.4..3.45s, completes3.45s (deadline2:late1.45). T1 never receives service, is UNFINISHED at6s; no escape. No MEMBER_CHANGE/ROLE_CHANGE/WITHDRAWAL/positive-progress reset or target switch. U0/U1 each occupied3.45s; U2 never assigned. Two initial Assignment changes cost.02 total; automatic completion release adds no fee.

Initial T0 candidate predicted completion1.35s, actual completion3.45s. D1 predicts3.35; D2/D3 predict3.45. Thus nominal belief geometry/quality can be optimistic; predicted and actual G/Q are intentionally not forced equal. T1 initially has positive predicted value but loses resource competition; after T0 completion its stale prior and remaining horizon make its best predicted allocation value negative. This is selective information starvation and lack of active sensing, NOT global initialization deadlock. No experiment determines its true counterfactual service value under another policy.

Net return-.25254634622073624 versus A0+.16516765531509792, descriptive delta-.41771400153583416. Completion1/2 versus A0 2/2. One deterministic idealized zero-noise scenario, not a statistical algorithm superiority comparison. No exploration, asynchronous arrivals, nonzero noise robustness, probabilistic uncertainty calibration or general multi-target coverage verified. Same policy/source audits reused; no independent full WLS implementation, full independent end-to-end A1 auditor, or trusted execution-origin proof.

Evidence: runs/a1_non_oracle_001/{R.json,S_NEW.json,R_D*.json,S_NEW_D*.json,PAIR_CHECK.json,SUMMARY.json,WORLD_INPUT.json,PUBLIC_INPUT.json}; reports/a1_episode_001_guard/{BEFORE.json,AFTER.json,TIMING.json,ANALYSIS.json,PHYSICAL_RECHECK.json,BOUNDARY_AND_LEDGER.json,stdout.log,stderr.log}. Finished and stopped without parameter changes or additional runs.
