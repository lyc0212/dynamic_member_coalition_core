# A0-Ib implementation acceptance

Status: PASS within current Windows worker / historical single-target integration scope. A0-I overall INCOMPLETE; A0-Ic pending. No A0-R run.

## Files

- scripts/gq_windows/a0_compare.py: offline CLI, Ia inventory and per-mode identity admission, canonical candidate key pairing, typed binary64 traversal, first-difference context, admitted runtime mapping.
- scripts/gq_windows/a0_mapping.py: explicitly authorized minimal supplement to fixed rules; selection action_metadata transitions/flows runtime references, STEP actual fusion runtime references.
- tests/test_gq_a0_compare.py: 10 strict traversal checks.
- tests/test_gq_a0_compare_integration.py: 10 fixture integration/mapping/injection tests.
- tests/fixtures/a0_ib_both.zip: labelled historical single-target fixture, no generated episode.
- docs/A0_IA_IDENTITY_CONTRACT.md: prior interface contract; supplemental rules described below.

## Scientific versus runtime identities

REQUEST/checkpoint/manifest/candidate scientific identities must compare exactly. Candidate matching uses (target, ordered robots, ordered roles), not filename position. Full candidate objects, TABLE, SELECTION, STEP, AFTER, final checkpoint/events/metrics are traversed without removing identity fields. Float equality uses float.hex, types never coerce. No diagnostic numeric tolerance is used.

Each comparison admits both modes through inventory() and mode_chain() first. Runtime mapping is delayed until all other leaves of the artifact match. Scientific anchors are the actual admitted request checkpoint, decision tick and canonical keys. Scope=(actual run_id, decision tick, artifact kind). All mapped runtime strings must equal RUN_R / RUN_S_NEW or their exact common stream/frame/packet suffix. Frame digests must independently equal each mode's normalized_frame digest; normalized scientific leaves have already compared. Forward/reverse namespace conflicts reject.

## Authorized minimum supplement

public.plan_action_metadata in public.py creates actual streams from work identity; worker uses actual_id=RUN+'_'+mode. The same flow occurs under action_metadata/transitions and flows. Added only these runtime leaves beneath both branches: stream_id; flow_registration/operation/{physical_environment_id,work_instance_id,stream_id}; context/{physical_environment_id,work_instance_id}; registration/stream_id; registration/context/{physical_environment_id,work_instance_id}.

For STEP, existing fusion leaf rules are composed only under /fusion_records/* and only for namespaces work/environment/stream/frame/packet/frame_digest. This includes frame/result/normalized_frame stream and frame IDs, packet IDs, result frame_sha256, quality frame_id and corresponding flow context/registration runtime references. Scientific checkpoint/request/world/action/segment identities are NOT relaxed. Other paths fail closed. No future autonomous expansion is authorized.

## Validation

Command: python -B -m unittest discover -s tests -p 'test_gq_a0*.py' -v
Final result: 71/71 PASS (51 previous + 20 Ib tests), 20.079 seconds. Log: reports/a0_ib_tests.log.

Read-only real historical integration:
python -B -m scripts.gq_windows.a0_compare D:/1st/gq_windows_release_verification/both_360_validation_001
Result saved in reports/a0_ib_historical_integration.json: PASS; 568 explicit runtime mapping records. This is SINGLE TARGET evidence, not a new episode or double-target acceptance. The earlier log records the policy refusal before the user's explicit minimal-supplement authorization.

Fixture test expectations retain manual anchors: six decisions, terminal tick120, initial candidate0 with U0/U1, known historical net return. Full positive fixture passes. Whole-entry negatives cover missing mode, exchanged candidate, changed predicted position, changed actual STEP, final metrics and unknown runtime string; focused negatives cover bearing/Q/progress/v/Assignment/control and mapping recipe/conflict. Failures assert status/path or first-artifact context. Fixture results are explicitly source_type=FIXTURE; CLI integration is source_type=RUN_ARTIFACTS and never asserts multitarget acceptance.

## Boundaries / Ic interface

compare(run_directory, source_type=...) -> report with status, path/reason/context on rejection, or admissions/mappings on PASS. CLI exit0 only for PASS, otherwise1. Reader does not modify evidence. Content consistency and existing audits do not authenticate historical execution. Unknown string differences reject as unsupported rather than automatically being mapped. Unusual future legitimate runtime identities require explicit policy review.

Ia audit recomputation is reused, not a second independent science proof. No independent optimum/plan/competition reconstruction is integrated here: Ic must consume verified manifests, candidate rows, Assignment and saved selection, invoke a0_plans, validate canonical tie rule and report competition separately.

Frozen input SHA256: ee8045603002d5c0081db91d7de513a9de76349b359095f2d0ccb8aca158a554.
Tracked scientific files and existing single-target input unchanged; all task files remain uncommitted. No episode, controller/estimator invocation, performance experiment, commit or push.

