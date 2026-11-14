# A0-Ic implementation and execution-review readiness

A0-I TOOLING READY FOR A0-R REVIEW. This is tool readiness, NOT double-target scientific acceptance or episode authorization.

## Implementation

- a0_plans.py extended with verify_selection() and canonical_choice(). Existing enumeration, binary64 baseline order and Fraction objective retained. Every saved plan is checked bidirectionally against exhaustive legal Assignment enumeration. It verifies count, exact optimum, number of tied optima, canonical selected indices, Assignment, change count and B64.
- Tie priority is independently replayed with Fraction values and mask insertion order, without importing/calling production solve(). Exhaustive enumeration independently checks its optimum. Targets ascending, candidates canonical; nonpositive marginal profit skipped; equal-score same mask retains previous witness; final equal-score mask minimum wins. The replay necessarily shares the frozen algorithmic tie specification, not a separate scientific optimality theorem.
- a0_accept.py calls pair comparison first. On non-PASS, plans and competition stay NOT_EVALUATED. On PASS, both modes and every decision receive independent plan checks. Output keys PAIR_CONSISTENCY, PLAN_OPTIMALITY and COMPETITION are separate. CLI exit0 means pair and plans pass, not competition activation.
- Competition uses exact single-target best minus all-idle objective including actual Assignment changes. Activation requires two positive margins AND no feasible simultaneous two-target plan. Fixture/historical-single/real-multitarget evidence classes remain distinct.

## Tests and independent expectations

Command: python -B -m unittest discover -s tests -p 'test_gq_a0*.py' -v
Log: reports/a0_ic_tests.log.
Manual dual-target fixture: 3 robots, 2 q2 targets, canonical12 rows, 13 plans, no parallel two-team plan. v=.5, B64=0, kappa=.125, initially idle -> each single plan = .5-2*.125=1/4, all12 tie. Minimum robot mask3, first target/role wins candidate0. Zero-profit case v=.25 -> all13 plans tie at0, keep idle. Global mask fixture equal candidates2(mask5)/4(mask6) -> candidate2. Wrong tie must reject.
Negatives cover omitted plan, illegal two-team resource overlap, invalid roles, forged optimum/count, wrong plan fee/change count and wrong canonical tie. Positive/negative competition: both margins1/4 versus one target margin-1/4. Pair rejection prevents any plan acceptance.

## Read-only historical integration

python -B -m scripts.gq_windows.a0_accept D:/1st/gq_windows_release_verification/both_360_validation_001
Report: reports/a0_ic_historical_integration.json.
PAIR_CONSISTENCY=PASS, PLAN_OPTIMALITY=PASS for both modes/all12 decisions. COMPETITION evidence_type=HISTORICAL_SINGLE_TARGET; real_multitarget_episode=NOT_EVALUATED. No episode generated.

## Module status / boundary

Frozen scene, provenance, structure tests: ready. Ia identity links/receipt consistency/fixed mappings: completed within previously accepted scope. Ib strict pair comparison: ready for current worker format. Ic exact plans/tie/competition integration: implemented. No new identity/schema tasks added. Full deep-malformed-JSON diagnostics and trusted execution-origin authentication remain outside the research tooling goal.

Candidate predictions are not independently re-simulated; existing audits and strict R/S comparison apply. Fraction plan checks prove optimality of the admitted finite binary64 candidate table, not multi-period/global physical optimality. Historical single-target and artificial dual-target tests cannot prove real double-target economic competition.

## A0-R review checklist (DO NOT EXECUTE without separate authorization)

Freeze HEAD plus hashes of the uncommitted tool files; freeze input SHA256 ee8045603002d5c0081db91d7de513a9de76349b359095f2d0ccb8aca158a554; verify intended Python/NumPy/SciPy runtime; choose a nonexistent output directory; preserve all failures and do not tune scene/costs/tolerances after results.
Suggested future run:
python -B scripts/run_gq_windows.py --scene configs/gq_windows_two_target_a0.json --output runs/a0_r_both_001 --evaluator both --max-candidates 12 --timeout 360
Suggested future offline acceptance:
python -B -m scripts.gq_windows.a0_accept runs/a0_r_both_001
360 is an explicit proposed whole-run timeout, not a measured runtime claim or current permission. No max-decisions truncation. Timeout is not automatically algorithm failure. Double-target structural12/13 assertions apply only while both targets active. Record pair/plan/competition gates separately, even if competition is not activated. Oracle controller/information architecture remains a later scientific question; do not alter physics during this baseline run.

No tracked scientific code, existing single-target input or frozen dual-target values modified. No experiment, commit or push performed. Files retained uncommitted for review.

Final verification: 85/85 lightweight tests PASS (71 existing +14 Ic), final unittest elapsed 65.440s. Historical integrated acceptance rerun completed exit0: pair PASS, all12 per-mode decision plan checks PASS; real multitarget competition NOT_EVALUATED. This test duration is not an episode/performance measurement. Four-robot synthetic guard also confirms two positive margins alone do not count as exclusive resource competition.
