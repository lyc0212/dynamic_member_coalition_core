# A1 minimal non-Oracle implementation — local report

Status: implementation and targeted tests PASS; full A1 episode NOT EXECUTED. Work uses the existing local checkout only; no GitHub fetch/pull/checkout/commit/push. Local starting HEAD27d923f (A0), checked only to identify local changes.

## Files

- configs/a1_public_announcements.json: independent predeclared public T0(7.8,9.8), T1(7.8,10.3), velocity priors(0,0), design bound0.5, public task metadata/speed bound.
- research/non_oracle/belief.py: actual-only observation queue, accepted-position history, >=5-tick velocity difference, speed cap, copied snapshots, origin/availability/consumption time records, prior/observed/degraded states.
- research/non_oracle/environment.py: private physics subclass, post-fusion observation queue, sanitized policy view, once-per-decision snapshot and actual controller override. Explicitly rejects asynchronous-birth inputs (A2 not implemented).
- research/non_oracle/policy.py: A1-specific belief trajectory inputs; model bearing/WLS/Q; belief geometry/escape/reward prediction; isolated KEEP branch clock; R independent and S_NEW four-candidate batch-local component reuse bound to complete input digest; unchanged objective via existing exact solver/tie rule.
- research/information_service_online/execution.py: only tracked science-file change, 6 lines added/1 replaced. Extracts original Oracle command unchanged into _control_command(); A1 overrides the seam. Physical movement, actual measurement generation, G/Q/service and aggregate ledger stay inherited.
- scripts/run_a1.py: explicit world and separate public-input arguments, new output directory, bounded physical horizon, per-decision outputs, final private audit snapshots, strict same-mode policy/choice/STEP comparison for both. The entry is implemented but has not been executed as an episode.
- tests/test_a1_non_oracle.py: targeted tests, including one1-second actual execution segment, not a complete6-second episode.

## Information boundary and causality

Private truth remains in world movement, actual bearing generation, actual G/service settlement and private audit snapshots. prepare_decision() copies only public announcements, robot self positions/Assignment, sensor declarations, actual acquired slots and service feedback into an A1_POLICY_INPUT. The old Oracle checkpoint remains private to environment/transaction driver; it is never passed to A1 decide(). No estimated values are substituted into fields named position_now/velocity_now. No private Target object enters prediction/control functions.

At tick k, only already queued and available actual WLS results are consumed; the snapshot is copied and cannot be refreshed twice at k. Assignment is decided before action-preparation observations at k. Those results and later actual endpoints stay queued until next decision. MODEL measurements are explicitly rejected by the belief queue. R/S_NEW candidate evaluation does not mutate the actual belief/cache.

Position acceptance requires an accepted finite converged WLS estimate and no flagged ill-conditioning/ambiguity/boundary/numeric violation. Service Q=FAIL is not an automatic location-update rejection. First location update retains public velocity prior; velocity_source remains PUBLIC_PRIOR until two accepted positions >=.25s apart permit ACTUAL_POSITION_DIFFERENCE. Speed is clipped at the public limit. Unknown/unassigned tasks remain PRIOR_ONLY with no invented actual-observation tick.

For last accepted estimate(p,v,tau), both predictors/controller query the same trajectory: p+v*min(t-tau,1), velocity v at age<=1 and0 thereafter. PRIOR_ONLY uses declared prior, no fake observation origin. Expiration applies at every physical/prediction tick, including between decisions; reacquisition replaces stale state. States are frozen by copy, not by forcing constant velocity over the whole interval.

KEEP retains actual settled progress and actual left G/Q. Its first future endpoint is modeled from belief; later intervals use modeled endpoints. A failed predicted interval resets only the local candidate ServiceState. New teams/role permutations do not inherit old progress/endpoint. No requirement that actual G equals predicted G.

## Verification

A1: 23/23 PASS, reports/a1_implementation_tests.log (4.624s final invocation).
Command: D:\anaconda3\python.exe -B -m unittest discover -s tests -p test_a1_non_oracle.py -v

A0 tooling: 85/85 PASS, reports/a1_a0_regression_tests.log.
Command: D:\anaconda3\python.exe -B -m unittest discover -s tests -p test_gq_a0*.py -v
Oracle CLI: 5/5 PASS, reports/a1_oracle_cli_tests.log.
Command: D:\anaconda3\python.exe -B -m unittest discover -s tests -p test_gq_windows_cli.py -v
Total113 test cases across these suites; no newly executed complete Oracle regression or A1 episode.

Tests: private-target perturbation leaves the sanitized input/prediction/selection/control unchanged; legacy input rejected; first assignment from prior; actual WLS feedback after one-second step; single estimate doesn't invent measured velocity; availability and consumption order; no same-tick refreeze; missing/invalid/ill WLS and stale recovery; serviceQFAIL can update valid location; MODEL contamination refusal; KEEP mixed endpoints and local reset; changed team starts zero; real model-endpoint R/S equality; expiry-crossing R/S equality; predictor/controller expiry equality; Oracle hook reproduces original expression.

Lightweight causal comparison fixes robot position/config and compares prior belief to a legally supplied actual-estimate update: both predicted position and control change. It does not read private truth and does not run another episode. Deterministic endpoint stubs are used only in named clock/assignment tests; separate tests use actual WLS and one-second actual execution.

## Preservation and risks

A0 frozen input hash remains ee8045603002d5c0081db91d7de513a9de76349b359095f2d0ccb8aca158a554; original outputs unmodified. Only the extracted control seam changes tracked original code. Uncommitted A1 additions and the user's untracked roadmap are retained.

This is a certainty-equivalent model, not a probabilistic robust planner. Bearing visibility remains idealized/unbounded with zero actual disturbance. WLS speed differencing can be noisy despite speed clipping; the public0.5 prior bound is a design assumption, not calibrated covariance. Unassigned targets can remain prior-only. Public/private separation is explicit call-interface discipline, not a Python security sandbox. Actual physics/truth settlement is inherited; existing A0 independent scalar controller auditor assumes Oracle control and must not be asserted to validate A1 unchanged. Full A1 physical trace/observation-causal acceptance remains for the separately authorized first experiment. No claims of complete-task success or equal Oracle returns.

## First episode suggestion — DO NOT RUN without authorization

D:\anaconda3\python.exe -B scripts/run_a1.py --world configs/gq_windows_two_target_a0.json --announcements configs/a1_public_announcements.json --output runs/a1_non_oracle_001 --method both

Execution preflight must freeze current local source/public-input hashes and runtime, ensure output absent and set an external process timeout/resource budget. The runner itself currently has no timeout flag; do not treat its absence as unbounded experiment authorization. No max-decisions or prior tuning from observed results. Preserve failures and partial per-decision outputs; no automatic rerun.

Acceptance: full tick120/TERMINAL and complete physical settlement; identical A1 policy inputs and R/S predictions/choices/actual steps under mapped actual runtime labels; no target truth in policy inputs; actual observations update next-snapshot belief; recorded source/availability/consumption causality; matched belief trajectory used by actual commands; KEEP/local-reset integrity; truthful completion/failure outcomes. Full stage scientific PASS is not claimed here. Next task is first-episode preflight/authorization, not another architecture review. A2/B/C/A3 not started.
