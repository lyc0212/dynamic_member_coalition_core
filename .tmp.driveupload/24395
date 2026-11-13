"""Frozen online public schema, identities and pure state metadata.
No filesystem, private environment, estimator or controller dependency.
The embedded schema is registered as source at runtime seal I.
"""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations, permutations
import json
import math
import re
from .common import ContractError, DT, digest

SCHEMA_SOURCE_SHA256 = 'ed5b3f5e36ac04ae66469496ce3b066f6d47e1ceb9ec48b6a94f726cc914ae34'
SCHEMA = json.loads('{"$schema":"https://json-schema.org/draft/2020-12/schema","$id":"urn:dynamic-member-coalition:gq-online:v1:schema","title":"GQ online v1 public/scoped interface documents","description":"Prepared interface schema only; no implementation, execution, scientific validation or runtime seal is claimed.","x-status":"PREPARED_NOT_IMPLEMENTED_NOT_EXECUTED","x-approved-draft":{"path":"docs/STAGE2A5B_GQ_ONLINE_INTERFACE_DRAFT.md","sha256":"190a96b1d1af261c0d8a115b813978eacc95ef07cb08e2b7679e0dbec5f9a71b"},"x-contract-ids":{"protocol":"STAGE2A5B-GQ-ONLINE-v1.0","checkpoint":"gq_online_checkpoint_v1","task_history":"gq_online_task_history_v1","service_segment":"gq_online_service_segment_v1","measurement_slot":"gq_online_measurement_slot_v1","actual_sampling":"gq_online_actual_sampling_v1","evaluation_request":"gq_online_evaluation_request_v1","current_prediction_endpoint":"gq_mixed_observed_model_left_v1","future_forecast":"public_cv_sigma_hold_zero_noise_v1","action_transaction":"gq_online_action_transaction_v1","execution_advance":"gq_online_execution_advance_v1","public_binding":"gq_online_public_history_binding_v1","flow_registration":"gq_online_flow_registration_v1","private_resume":"gq_online_private_resume_state_v1","clock":"gq_two_endpoint_reset_v1","quality":"local_wls_radius_proxy_v1","measurement_payload":"STAGE2A5B-A-MINIMAL-v0.2"},"x-canonical-roles":{"2":["dual_neg45","dual_pos45"],"3":["tri_0","tri_120","tri_240"]},"x-first-round-rejected-slot-states":["INVALID"],"x-semantic-rules":[{"id":"S001","rule":"Only the API-specific $defs is accepted for each role. Root oneOf is a document catalogue, not permission for an evaluator to accept audit/private document kinds."},{"id":"S002","rule":"All numbers are finite; bool is never a numeric field. Normalize declared float fields to binary64 floats and integer fields to integers before canonical JSON. No tolerance rounding."},{"id":"S003","rule":"Canonical JSON is UTF-8, ensure_ascii=false, sort_keys=true, separators=(comma,colon), allow_nan=false. Content digests omit only their own digest field and bind child digests. Stable segment_id/action_commit_id/candidate/world identities use the separately fixed identity recipes in SCHEMA_NOTES, not a mutable whole-record hash. No tolerance rounding."},{"id":"S004","rule":"Checkpoint tick is one actual committed decision cut. episode_end_tick=config.stage_dt*config.max_stages/.05. DECISION_READY requires tick<T_tick; TERMINAL requires tick=T_tick and no new evaluation/action."},{"id":"S005","rule":"positions/assignment/sensor_profiles each contain exactly global X entries, stable Uk order. Visible target IDs and histories are unique, sorted, below original Y, and match exactly. Full X/Y normalization never changes per candidate."},{"id":"S006","rule":"current_slots contains exactly X*len(targets) rows sorted by (target_id,robot_id), all slot_key.tick=checkpoint.tick. Initially/unqueried rows have no packet/value/digest. Empty targets implies empty histories/slots; no early episode stop."},{"id":"S007","rule":"A VALID packet uses sensor_id=U{robot_id}; measurement_tick=available_tick=slot_key.tick and packet position/sigma match its actual current acquisition context. MISSING means a request was attempted; UNQUERIED is not missing."},{"id":"S008","rule":"Raw actual identity=(outer physical_environment_id,target_id,robot_id,tick). Role, candidate, segment, fusion stream, request and work identity never alter this key. Repeated accesses preserve identical VALID packet or MISSING result."},{"id":"S009","rule":"Only execution endpoint settlement or selected-action preparation can acquire UNQUERIED actual slots. Public observation and candidate evaluation make zero actual acquisition calls. A complete logical slot matrix is not an observation capability."},{"id":"S010","rule":"INVALID and malformed/conflicting data are rejected in v1. IPC/numerical errors are not downgraded to INVALID, MISSING or UNKNOWN. Known missing is never resampled in search of success."},{"id":"S011","rule":"Main actual perturbation is zero. Fixed nonzero probes use predeclared per-key outcomes; no shared sequential RNG consumption. Paired environments have separate raw caches even when perturbation-source rules are paired."},{"id":"S012","rule":"Task history covers actual time from birth through cutoff using ordered service segments and unassigned intervals, without filling gaps with measurements. An open segment or open unassigned interval, exactly one, represents each active task at cut."},{"id":"S013","rule":"New service segment starts only on a legal boundary, with zero initial clock and a complete q=2/3 team. KEEP retains segment/clock/endpoint. G/Q interruption clears progress inside the same segment; withdrawal/member/role change closes the old segment; reassign starts new segment and cannot restore lost progress."},{"id":"S014","rule":"Active assigned target latest endpoint tick equals checkpoint.tick and its team equals clock/current Assignment. Positive progress requires G=true and Q=PASS. Unassigned target has no active segment and current clock is zero; its previous segments remain historical evidence."},{"id":"S015","rule":"Task terminal segments are archived outside active targets/histories after unique completion/escape/episode-end settlement. Their accounting remains in the actual total ledger, including escaped unfinished terminal penalties."},{"id":"S016","rule":"At physical endpoint: settle old motion to exact stop, escape priority; current declarations/old-team actual measurements then G/Q and the preceding whole interval; terminal release; legal births; immutable checkpoint. Observation never repeats endpoint settlement."},{"id":"S017","rule":"events_since_previous_checkpoint aggregates the whole interval since the previous decision, including nongrid/mid-second terminal events; no event is lost by inspecting only the last .05 frame."},{"id":"S018","rule":"prediction_end_tick=min(episode_end_tick,checkpoint.tick+60). All candidates share it. Each actual action advances only min(20,remaining) ticks. deadline remains soft; tau<T has no terminal penalty or terminal lifecycle release."},{"id":"S019","rule":"KEEP current prediction endpoint uses the already settled actual endpoint, zero new fusion, and zero interval credit. service_start_tick is the current branch clock origin k, never the original segment start; first_new_fusion_tick is k+1 when endpoint k is retained. The same k/k+1 distinction applies to serial actual restart with already settled endpoint k. A newly prepared actual/nonKEEP predicted left endpoint starts new fusion at k."},{"id":"S020","rule":"NonKEEP current prediction clears the clock. Each VALID or MISSING checkpoint slot becomes OBSERVED unchanged; only UNQUERIED becomes MODEL using public position/current sigma/health and zero-angle perturbation. Recompute joint Q/G for the candidate; the mixed result is always PREDICTION_ONLY."},{"id":"S021","rule":"Future prediction endpoints are all MODEL, public CV plus held sigma/health and zero perturbation. No target private future, future fault/recovery/birth schedule or source SHA is input. Predictions never write the actual slot cache or execution state."},{"id":"S022","rule":"Selected actual action prepares only needed UNQUERIED current slots; existing packets/missing results are reused. Form the real new-team left endpoint. FAIL/UNKNOWN is a valid outcome and does not trigger another selection/query trial at the same boundary."},{"id":"S023","rule":"Request handling order: successful-request replay cache first; identical replay returns original CommittedAction without side effects even after its checkpoint is stale; same-ID conflict rejects; in-flight same request returns IN_PROGRESS without starting work or renewing its deadline; only new requests check current checkpoint/tick."},{"id":"S024","rule":"A new action request requires the exact current public checkpoint, legal boundary and complete resource-disjoint teams. One successful action commit per boundary. Prepare without moving robots/time or partially charging/occupying; all successful preparation results commit Assignment/segments/endpoints/direct change fee once."},{"id":"S025","rule":"On failed preparation stop the attempt and retain the last committed physical state plus every actual sampling attempt/resolved slot/CPU. No assignment/fee partial commit and no hidden retry. Actual sampling does not roll back merely because an action failed."},{"id":"S026","rule":"Change count is direct old-to-new per-robot Assignment inequality. A-to-B in one boundary costs once; A-to-IDLE then later IDLE-to-B costs at each boundary. Automatic terminal release has no additional change cost."},{"id":"S027","rule":"Physical advance consumes an already committed action; it does not select a second action. Intermediate completion/escape immediately stops that task and releases members, but reuse waits for the next legal boundary."},{"id":"S028","rule":"PublicHistoryBinding must be pinned by the external trusted execution/admission channel, not supplied through scientific request fields. Same payload/self digest/trusted=true is not source proof; no unit_only bypass in main cases."},{"id":"S029","rule":"Scientific identities bind only canonical public content. Exclude physical_environment_id, operation/request/stream/work IDs, paths, private scene/source hashes and future schedules. Runtime provenance and registered files remain external."},{"id":"S030","rule":"Flow registration binds purpose/target/team/checkpoint and segment identity for each work instance. ACTUAL_EXECUTION uses its prepared or committed actual segment_id; KEEP prediction/reference uses the retained actual segment_id; nonKEEP prediction/reference has segment_id=null and is isolated by candidate/world identities. Any foreign/old segment fusion reply rejects even if target, Uk and tick match; actual raw slot reuse remains segment-independent."},{"id":"S031","rule":"Each task segment/endpoint/history digest is derived from public team/clock/events/slot references actually established through its cutoff. Origin 0 and fixed F4 membership are never requirements. Raw operational IDs are canonicalized outside scientific content."},{"id":"S032","rule":"Checkpoint/public request does not contain cumulative monetary costs. Histories provide current state, not extra reward; compute future O from current time only. Actual ledger retains all past costs; never sum overlapping forecast J as episode return."},{"id":"S033","rule":"Candidates enumerate target ascending, robot combinations ascending and fixed role catalogue permutation order. Restore this index/value order before old exact DP even if computation order differs. Reuse its existing tie handling, no new KEEP preference."},{"id":"S034","rule":"Serial job resume restores exact private state including actual slot cache, sensor declarations, segment history, action replay cache, committed action/boundary stage, cumulative ledger and terminal-settlement flags. Do not reconstruct it from a public checkpoint or reset identity/fees. No resume of an in-flight/failed transaction."},{"id":"S035","rule":"Each resume/checkpoint publication is an infrastructure save at a committed cut, not another observation, sampling event or scientific action. Shared overall CPU/wall budgets persist across all jobs, imports, seals and audits."},{"id":"S036","rule":"PrivateResumeArtifactDescriptor paths/hashes are accepted only by registered executor/audit loaders and are never nested inside public messages. Use only necessary pre-registered files and precheck encoded IPC size; retain the 2 MiB frame cap."},{"id":"S037","rule":"Fusion request/response context must echo the complete registered purpose, segment_id and scientific/work identities. segment_id is assigned by the execution preparation/committed-state registry or copied from the admitted KEEP history, not asserted by the reply. service_start_tick is a branch time and must never stand in for segment identity. first_new_fusion_tick is checked against actual endpoint reuse and need not equal the service segment start_tick."}],"oneOf":[{"$ref":"#/$defs/Checkpoint"},{"$ref":"#/$defs/EvaluationRequest"},{"$ref":"#/$defs/CandidateDescriptor"},{"$ref":"#/$defs/PredictionEndpoint"},{"$ref":"#/$defs/ActualSampleRequest"},{"$ref":"#/$defs/ActualSampleResult"},{"$ref":"#/$defs/ActionRequest"},{"$ref":"#/$defs/ActionResult"},{"$ref":"#/$defs/AdvanceRequest"},{"$ref":"#/$defs/AdvanceResult"},{"$ref":"#/$defs/PublicHistoryBinding"},{"$ref":"#/$defs/FlowRegistration"},{"$ref":"#/$defs/TaskArchive"},{"$ref":"#/$defs/PrivateResumeArtifactDescriptor"}],"$defs":{"Sha256":{"type":"string","pattern":"^[0-9a-f]{64}$"},"Tick":{"type":"integer","minimum":0},"DecisionTick":{"type":"integer","minimum":0,"multipleOf":20},"RobotId":{"type":"integer","minimum":0,"maximum":15},"TargetId":{"type":"integer","minimum":0},"SensorId":{"type":"string","pattern":"^U(?:0|[1-9][0-9]*)$"},"Vector2":{"type":"array","items":{"type":"number"},"minItems":2,"maxItems":2},"Role":{"enum":["dual_neg45","dual_pos45","tri_0","tri_120","tri_240"]},"QualityStatus":{"enum":["PASS","FAIL","UNKNOWN"]},"Assignment":{"type":"object","properties":{"target":{"anyOf":[{"$ref":"#/$defs/TargetId"},{"type":"null"}]},"role":{"enum":["none","dual_neg45","dual_pos45","tri_0","tri_120","tri_240"]}},"required":["target","role"],"additionalProperties":false,"allOf":[{"if":{"properties":{"target":{"const":null}},"required":["target"]},"then":{"properties":{"role":{"const":"none"}}}},{"if":{"properties":{"target":{"type":"integer"}},"required":["target"]},"then":{"properties":{"role":{"$ref":"#/$defs/Role"}}}}]},"TeamMember":{"type":"object","properties":{"robot_id":{"$ref":"#/$defs/RobotId"},"role":{"$ref":"#/$defs/Role"}},"required":["robot_id","role"],"additionalProperties":false},"Team":{"type":"array","items":{"$ref":"#/$defs/TeamMember"},"minItems":2,"maxItems":3,"uniqueItems":true},"ClockState":{"type":"object","properties":{"base":{"type":"number","minimum":0},"intervals":{"type":"integer","minimum":0},"team":{"type":"array","items":{"$ref":"#/$defs/TeamMember"},"maxItems":3,"uniqueItems":true}},"required":["base","intervals","team"],"additionalProperties":false},"Config":{"type":"object","properties":{"robots":{"type":"integer","minimum":2,"maximum":16},"task_count":{"type":"integer","minimum":1},"side":{"type":"number"},"stage_dt":{"const":3.0},"capture_check":{"type":"number"},"step_dt":{"const":0.05},"max_stages":{"type":"integer","minimum":1},"prediction_stages":{"const":1},"max_plan_age":{"type":"integer","minimum":1},"max_speed":{"const":3.0},"travel_gain":{"const":1.0},"capture_radius":{"type":"number"},"anchor_offset":{"type":"number"},"time_gain":{"type":"number"},"singularity_epsilon":{"type":"number"},"hold_gain":{"type":"number"},"target_speed_min":{"type":"number"},"target_speed_max":{"type":"number"},"turn_interval":{"const":1.0},"turn_max_angle":{"type":"number"},"turn_hold_ticks":{"type":"integer","minimum":1},"speed_delta_max":{"type":"number"},"motion_model":{"const":"continuous_turn"},"risk_samples":{"type":"integer","minimum":1},"risk_trigger_samples":{"type":"integer","minimum":1},"risk_prediction_dt":{"const":0.05},"risk_threshold":{"type":"number"},"local_substitutes":{"type":"integer","minimum":0},"initial_fraction":{"type":"number"},"two_robot_probability":{"type":"number"},"flow_weight":{"const":0.1},"late_weight":{"const":0.3},"control_weight":{"const":0.02},"unfinished_weight":{"const":2.0},"control_reference":{"const":10.0},"change_cost":{"const":0.01},"capture_mode":{"const":"stepwise_service"},"geometry_mode":{"const":"angular_standoff_v1"},"observation_radius":{"const":0.6},"observation_tolerance":{"const":0.15}},"required":["robots","task_count","side","stage_dt","capture_check","step_dt","max_stages","prediction_stages","max_plan_age","max_speed","travel_gain","capture_radius","anchor_offset","time_gain","singularity_epsilon","hold_gain","target_speed_min","target_speed_max","turn_interval","turn_max_angle","turn_hold_ticks","speed_delta_max","motion_model","risk_samples","risk_trigger_samples","risk_prediction_dt","risk_threshold","local_substitutes","initial_fraction","two_robot_probability","flow_weight","late_weight","control_weight","unfinished_weight","control_reference","change_cost","capture_mode","geometry_mode","observation_radius","observation_tolerance"],"additionalProperties":false,"description":"Complete existing Config. X/Y remain global; no per-candidate shrink. Case manifests freeze all remaining concrete values."},"TargetPublicState":{"type":"object","properties":{"id":{"$ref":"#/$defs/TargetId"},"birth":{"type":"number","minimum":0,"multipleOf":3},"position_now":{"$ref":"#/$defs/Vector2"},"velocity_now":{"$ref":"#/$defs/Vector2"},"required_robots":{"enum":[2,3]},"weight":{"type":"number","exclusiveMinimum":0},"deadline":{"type":"number","minimum":0},"service_duration":{"type":"number","exclusiveMinimum":0}},"required":["id","birth","position_now","velocity_now","required_robots","weight","deadline","service_duration"],"additionalProperties":false},"SensorProfile":{"type":"object","properties":{"sensor_id":{"$ref":"#/$defs/SensorId"},"sigma":{"type":"number","exclusiveMinimum":0},"health":{"enum":["available","missing"]},"observed_tick":{"$ref":"#/$defs/Tick"}},"required":["sensor_id","sigma","health","observed_tick"],"additionalProperties":false},"SlotKey":{"type":"object","properties":{"target_id":{"$ref":"#/$defs/TargetId"},"robot_id":{"$ref":"#/$defs/RobotId"},"tick":{"$ref":"#/$defs/Tick"}},"required":["target_id","robot_id","tick"],"additionalProperties":false,"description":"Public canonical key only. The raw cache key additionally contains outer physical_environment_id; no role, candidate, segment, flow or decision ID."},"CurrentPacket":{"type":"object","properties":{"sensor_id":{"$ref":"#/$defs/SensorId"},"position":{"$ref":"#/$defs/Vector2"},"bearing":{"type":"number"},"sigma":{"type":"number","exclusiveMinimum":0},"measurement_tick":{"$ref":"#/$defs/Tick"},"available_tick":{"$ref":"#/$defs/Tick"},"status":{"const":"ok"}},"required":["sensor_id","position","bearing","sigma","measurement_tick","available_tick","status"],"additionalProperties":false},"MeasurementSlot":{"type":"object","properties":{"contract_id":{"const":"gq_online_measurement_slot_v1"},"slot_key":{"$ref":"#/$defs/SlotKey"},"state":{"enum":["UNQUERIED","VALID","MISSING"]},"packet":{"anyOf":[{"$ref":"#/$defs/CurrentPacket"},{"type":"null"}]},"slot_digest":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]}},"required":["contract_id","slot_key","state","packet","slot_digest"],"additionalProperties":false,"allOf":[{"if":{"properties":{"state":{"const":"UNQUERIED"}},"required":["state"]},"then":{"properties":{"packet":{"type":"null"},"slot_digest":{"type":"null"}}}},{"if":{"properties":{"state":{"const":"VALID"}},"required":["state"]},"then":{"properties":{"packet":{"$ref":"#/$defs/CurrentPacket"},"slot_digest":{"$ref":"#/$defs/Sha256"}}}},{"if":{"properties":{"state":{"const":"MISSING"}},"required":["state"]},"then":{"properties":{"packet":{"type":"null"},"slot_digest":{"$ref":"#/$defs/Sha256"}}}}],"description":"INVALID is deliberately not a legal value in v1. An explicit UNQUERIED row is bookkeeping, not a sampling attempt."},"QueriedMeasurementSlot":{"allOf":[{"$ref":"#/$defs/MeasurementSlot"},{"properties":{"state":{"enum":["VALID","MISSING"]}}}]},"SlotReference":{"type":"object","properties":{"slot_key":{"$ref":"#/$defs/SlotKey"},"slot_digest":{"$ref":"#/$defs/Sha256"},"state":{"enum":["VALID","MISSING"]}},"required":["slot_key","slot_digest","state"],"additionalProperties":false},"QualitySummary":{"type":"object","properties":{"contract_id":{"const":"local_wls_radius_proxy_v1"},"status":{"$ref":"#/$defs/QualityStatus"},"payload_digest":{"$ref":"#/$defs/Sha256"},"radius_proxy":{"anyOf":[{"type":"number","minimum":0},{"type":"null"}]}},"required":["contract_id","status","payload_digest","radius_proxy"],"additionalProperties":false,"allOf":[{"if":{"properties":{"status":{"enum":["PASS","FAIL"]}},"required":["status"]},"then":{"properties":{"radius_proxy":{"type":"number","minimum":0}}}}]},"ActualEndpoint":{"type":"object","properties":{"endpoint_digest":{"$ref":"#/$defs/Sha256"},"target_id":{"$ref":"#/$defs/TargetId"},"tick":{"$ref":"#/$defs/Tick"},"source_kind":{"const":"ACTUAL"},"team":{"$ref":"#/$defs/Team"},"G":{"type":"boolean"},"quality":{"$ref":"#/$defs/QualitySummary"},"slots":{"type":"array","items":{"$ref":"#/$defs/SlotReference"},"minItems":2,"maxItems":3,"uniqueItems":true}},"required":["endpoint_digest","target_id","tick","source_kind","team","G","quality","slots"],"additionalProperties":false,"description":"Already sampled/fused actual endpoint. Its creation adds no interval by itself; clock credit requires the preceding complete interval."},"TimedEventPoint":{"type":"object","properties":{"time_seconds":{"type":"number","minimum":0},"event_tick":{"anyOf":[{"$ref":"#/$defs/Tick"},{"type":"null"}]}},"required":["time_seconds","event_tick"],"additionalProperties":false,"description":"event_tick is null for a genuinely nongrid escape; time_seconds remains its exact recorded float."},"PublicEvent":{"type":"object","properties":{"event_index":{"type":"integer","minimum":0},"kind":{"enum":["BIRTH","ASSIGNED","INTERRUPTED","WITHDRAWN","TEAM_CHANGED","ROLE_CHANGED","COMPLETED","ESCAPED","EPISODE_ENDED"]},"target_id":{"$ref":"#/$defs/TargetId"},"at":{"$ref":"#/$defs/TimedEventPoint"},"segment_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"progress_before":{"type":"number","minimum":0},"progress_after":{"type":"number","minimum":0},"reasons":{"type":"array","items":{"enum":["BIRTH","INITIAL_ASSIGNMENT","REASSIGNMENT","MEMBER_CHANGE","ROLE_CHANGE","WITHDRAWAL","GEOMETRY_INVALID","QUALITY_FAIL","QUALITY_UNKNOWN","SERVICE_COMPLETE","ESCAPE","EPISODE_END"]},"uniqueItems":true}},"required":["event_index","kind","target_id","at","segment_id","progress_before","progress_after","reasons"],"additionalProperties":false},"SegmentClosure":{"type":"object","properties":{"reason":{"enum":["WITHDRAWN","TEAM_CHANGED","ROLE_CHANGED","COMPLETED","ESCAPED","EPISODE_END"]},"at":{"$ref":"#/$defs/TimedEventPoint"},"closing_event_index":{"type":"integer","minimum":0}},"required":["reason","at","closing_event_index"],"additionalProperties":false},"ServiceSegment":{"type":"object","properties":{"contract_id":{"const":"gq_online_service_segment_v1"},"target_id":{"$ref":"#/$defs/TargetId"},"segment_index":{"type":"integer","minimum":0},"segment_id":{"$ref":"#/$defs/Sha256"},"previous_segment_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"start_tick":{"$ref":"#/$defs/DecisionTick"},"team":{"$ref":"#/$defs/Team"},"opened_by":{"enum":["INITIAL_ASSIGNMENT","REASSIGNMENT","MEMBER_CHANGE","ROLE_CHANGE"]},"initial_clock":{"$ref":"#/$defs/ClockState"},"latest_clock":{"$ref":"#/$defs/ClockState"},"latest_endpoint":{"$ref":"#/$defs/ActualEndpoint"},"closure":{"anyOf":[{"$ref":"#/$defs/SegmentClosure"},{"type":"null"}]},"events":{"type":"array","items":{"$ref":"#/$defs/PublicEvent"}},"segment_history_digest":{"$ref":"#/$defs/Sha256"}},"required":["contract_id","target_id","segment_index","segment_id","previous_segment_id","start_tick","team","opened_by","initial_clock","latest_clock","latest_endpoint","closure","events","segment_history_digest"],"additionalProperties":false,"description":"A fixed member/role assignment segment. G/Q interruption resets progress inside the same segment; reassignment creates a new segment without changing task identity."},"UnassignedInterval":{"type":"object","properties":{"start_tick":{"$ref":"#/$defs/DecisionTick"},"opened_by":{"enum":["BIRTH","WITHDRAWAL"]},"opening_event_index":{"type":"integer","minimum":0},"closing_event_index":{"anyOf":[{"type":"integer","minimum":0},{"type":"null"}]},"end_at":{"anyOf":[{"$ref":"#/$defs/TimedEventPoint"},{"type":"null"}]}},"required":["start_tick","end_at","opened_by","opening_event_index","closing_event_index"],"additionalProperties":false,"description":"End time is an exact TimedEventPoint so an unassigned nongrid escape can close its interval without rounding to a decision boundary."},"TaskHistory":{"type":"object","properties":{"contract_id":{"const":"gq_online_task_history_v1"},"target_id":{"$ref":"#/$defs/TargetId"},"birth_tick":{"$ref":"#/$defs/Tick"},"cutoff_tick":{"$ref":"#/$defs/Tick"},"active_segment_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"segments":{"type":"array","items":{"$ref":"#/$defs/ServiceSegment"}},"unassigned_intervals":{"type":"array","items":{"$ref":"#/$defs/UnassignedInterval"}},"events":{"type":"array","items":{"$ref":"#/$defs/PublicEvent"}},"history_digest":{"$ref":"#/$defs/Sha256"}},"required":["contract_id","target_id","birth_tick","cutoff_tick","active_segment_id","segments","unassigned_intervals","events","history_digest"],"additionalProperties":false,"description":"Per-task actual history supports delayed assignment and unassigned gaps. No past monetary cost is supplied to candidate scoring. Terminal task histories are archived outside the active checkpoint."},"Checkpoint":{"type":"object","properties":{"message_kind":{"const":"public_checkpoint"},"contract_id":{"const":"gq_online_checkpoint_v1"},"checkpoint_id":{"$ref":"#/$defs/Sha256"},"previous_checkpoint_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"phase":{"enum":["DECISION_READY","TERMINAL"]},"tick":{"$ref":"#/$defs/DecisionTick"},"episode_end_tick":{"$ref":"#/$defs/Tick"},"config":{"$ref":"#/$defs/Config"},"positions":{"type":"array","items":{"$ref":"#/$defs/Vector2"},"minItems":2,"maxItems":16},"assignment":{"type":"array","items":{"$ref":"#/$defs/Assignment"},"minItems":2,"maxItems":16},"targets":{"type":"array","items":{"$ref":"#/$defs/TargetPublicState"}},"sensor_profiles":{"type":"array","items":{"$ref":"#/$defs/SensorProfile"},"minItems":2,"maxItems":16},"task_histories":{"type":"array","items":{"$ref":"#/$defs/TaskHistory"}},"current_slots":{"type":"array","items":{"$ref":"#/$defs/MeasurementSlot"}},"events_since_previous_checkpoint":{"type":"array","items":{"$ref":"#/$defs/PublicEvent"}}},"required":["message_kind","contract_id","checkpoint_id","previous_checkpoint_id","phase","tick","episode_end_tick","config","positions","assignment","targets","sensor_profiles","task_histories","current_slots","events_since_previous_checkpoint"],"additionalProperties":false,"description":"Complete immutable public cut. current_slots is the full visible-active-target x stable-robot logical matrix, sorted by target then robot, all at tick. It never creates measurements."},"CandidateKey":{"type":"object","properties":{"target":{"$ref":"#/$defs/TargetId"},"robots":{"type":"array","items":{"$ref":"#/$defs/RobotId"},"minItems":2,"maxItems":3,"uniqueItems":true},"roles":{"type":"array","items":{"$ref":"#/$defs/Role"},"minItems":2,"maxItems":3,"uniqueItems":true}},"required":["target","robots","roles"],"additionalProperties":false},"EvaluationRequest":{"type":"object","properties":{"message_kind":{"const":"evaluation_request"},"contract_id":{"const":"gq_online_evaluation_request_v1"},"evaluation_request_id":{"$ref":"#/$defs/Sha256"},"checkpoint":{"$ref":"#/$defs/Checkpoint"},"prediction_end_tick":{"$ref":"#/$defs/Tick"},"forecast_contract_id":{"const":"public_cv_sigma_hold_zero_noise_v1"},"current_endpoint_contract_id":{"const":"gq_mixed_observed_model_left_v1"},"manifest_order":{"const":"target_then_robot_combination_then_frozen_role_permutation"}},"required":["message_kind","contract_id","evaluation_request_id","checkpoint","prediction_end_tick","forecast_contract_id","current_endpoint_contract_id","manifest_order"],"additionalProperties":false},"CandidateDescriptor":{"type":"object","properties":{"message_kind":{"const":"candidate_descriptor"},"candidate_id":{"$ref":"#/$defs/Sha256"},"evaluation_request_id":{"$ref":"#/$defs/Sha256"},"world_id":{"$ref":"#/$defs/Sha256"},"index":{"type":"integer","minimum":0},"key":{"$ref":"#/$defs/CandidateKey"},"resource_mask":{"type":"integer","minimum":1}},"required":["message_kind","candidate_id","evaluation_request_id","world_id","index","key","resource_mask"],"additionalProperties":false},"PredictedSourceSlot":{"type":"object","properties":{"slot_key":{"$ref":"#/$defs/SlotKey"},"source":{"enum":["OBSERVED","MODEL"]},"outcome":{"enum":["VALID","MISSING"]},"packet":{"anyOf":[{"$ref":"#/$defs/CurrentPacket"},{"type":"null"}]},"observed_slot_digest":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]}},"required":["slot_key","source","outcome","packet","observed_slot_digest"],"additionalProperties":false,"allOf":[{"if":{"properties":{"source":{"const":"OBSERVED"}},"required":["source"]},"then":{"properties":{"observed_slot_digest":{"$ref":"#/$defs/Sha256"}}}},{"if":{"properties":{"source":{"const":"MODEL"}},"required":["source"]},"then":{"properties":{"observed_slot_digest":{"type":"null"}}}},{"if":{"properties":{"outcome":{"const":"VALID"}},"required":["outcome"]},"then":{"properties":{"packet":{"$ref":"#/$defs/CurrentPacket"}}}},{"if":{"properties":{"outcome":{"const":"MISSING"}},"required":["outcome"]},"then":{"properties":{"packet":{"type":"null"}}}}]},"PredictionEndpoint":{"type":"object","properties":{"message_kind":{"const":"prediction_endpoint"},"contract_id":{"const":"gq_mixed_observed_model_left_v1"},"result_scope":{"const":"PREDICTION_ONLY"},"checkpoint_id":{"$ref":"#/$defs/Sha256"},"evaluation_request_id":{"$ref":"#/$defs/Sha256"},"world_id":{"$ref":"#/$defs/Sha256"},"candidate_id":{"$ref":"#/$defs/Sha256"},"target_id":{"$ref":"#/$defs/TargetId"},"tick":{"$ref":"#/$defs/Tick"},"endpoint_phase":{"enum":["CURRENT","FUTURE"]},"team":{"$ref":"#/$defs/Team"},"reused_actual_endpoint":{"type":"boolean"},"actual_endpoint_digest":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"source_slots":{"type":"array","items":{"$ref":"#/$defs/PredictedSourceSlot"},"minItems":2,"maxItems":3},"G":{"type":"boolean"},"quality":{"$ref":"#/$defs/QualitySummary"},"fusion_performed":{"type":"boolean"}},"required":["message_kind","contract_id","result_scope","checkpoint_id","evaluation_request_id","world_id","candidate_id","target_id","tick","endpoint_phase","team","reused_actual_endpoint","actual_endpoint_digest","source_slots","G","quality","fusion_performed"],"additionalProperties":false,"allOf":[{"if":{"properties":{"reused_actual_endpoint":{"const":true}},"required":["reused_actual_endpoint"]},"then":{"properties":{"endpoint_phase":{"const":"CURRENT"},"actual_endpoint_digest":{"$ref":"#/$defs/Sha256"},"fusion_performed":{"const":false}}}},{"if":{"properties":{"reused_actual_endpoint":{"const":false}},"required":["reused_actual_endpoint"]},"then":{"properties":{"actual_endpoint_digest":{"type":"null"},"fusion_performed":{"const":true}}}},{"if":{"properties":{"endpoint_phase":{"const":"FUTURE"}},"required":["endpoint_phase"]},"then":{"properties":{"reused_actual_endpoint":{"const":false},"source_slots":{"items":{"properties":{"source":{"const":"MODEL"}}}}}}}]},"OperationIdentity":{"type":"object","properties":{"physical_environment_id":{"type":"string","minLength":1,"maxLength":200},"request_id":{"type":"string","minLength":1,"maxLength":200}},"required":["physical_environment_id","request_id"],"additionalProperties":false,"description":"Outer operational scope only; never included in a scientific checkpoint/history/request digest."},"SampleRequestPayload":{"type":"object","properties":{"contract_id":{"const":"gq_online_actual_sampling_v1"},"slot_key":{"$ref":"#/$defs/SlotKey"},"phase":{"enum":["EXECUTION_ENDPOINT","ACTION_PREPARATION"]},"sensor_profile":{"$ref":"#/$defs/SensorProfile"},"sensor_position":{"$ref":"#/$defs/Vector2"},"checkpoint_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]}},"required":["contract_id","slot_key","phase","sensor_profile","sensor_position","checkpoint_id"],"additionalProperties":false,"description":"Actual execution-owned acquisition only. Target true point and private future are not carried into sensing/fusion. The actual sampler owns its private present-state generator."},"ActualSampleRequest":{"type":"object","properties":{"message_kind":{"const":"actual_sample_request"},"operation":{"$ref":"#/$defs/SamplingOperationIdentity"},"payload":{"$ref":"#/$defs/SampleRequestPayload"}},"required":["message_kind","operation","payload"],"additionalProperties":false},"ActualSampleResult":{"type":"object","properties":{"message_kind":{"const":"actual_sample_result"},"operation":{"$ref":"#/$defs/SamplingOperationIdentity"},"contract_id":{"const":"gq_online_actual_sampling_v1"},"slot":{"$ref":"#/$defs/QueriedMeasurementSlot"},"disposition":{"enum":["FIRST_QUERY","CACHE_REUSE"]},"unique_query_delta":{"enum":[0,1]},"sampling_attempt_delta":{"enum":[0,1]}},"required":["message_kind","operation","contract_id","slot","disposition","unique_query_delta","sampling_attempt_delta"],"additionalProperties":false,"allOf":[{"if":{"properties":{"disposition":{"const":"FIRST_QUERY"}},"required":["disposition"]},"then":{"properties":{"unique_query_delta":{"const":1},"sampling_attempt_delta":{"const":1}}}},{"if":{"properties":{"disposition":{"const":"CACHE_REUSE"}},"required":["disposition"]},"then":{"properties":{"unique_query_delta":{"const":0},"sampling_attempt_delta":{"const":0}}}}]},"ActionRequest":{"type":"object","properties":{"message_kind":{"const":"action_request"},"operation":{"$ref":"#/$defs/OperationIdentity"},"payload":{"type":"object","properties":{"contract_id":{"const":"gq_online_action_transaction_v1"},"checkpoint_id":{"$ref":"#/$defs/Sha256"},"expected_start_tick":{"$ref":"#/$defs/DecisionTick"},"assignment":{"type":"array","items":{"$ref":"#/$defs/Assignment"},"minItems":2,"maxItems":16}},"required":["contract_id","checkpoint_id","expected_start_tick","assignment"],"additionalProperties":false}},"required":["message_kind","operation","payload"],"additionalProperties":false},"ActionTransition":{"type":"object","properties":{"target_id":{"$ref":"#/$defs/TargetId"},"kind":{"enum":["KEEP","FIRST_ASSIGNMENT","WITHDRAW","REASSIGN","MEMBER_CHANGE","ROLE_CHANGE","UNCHANGED_UNASSIGNED"]},"old_segment_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"new_segment_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"clock_after":{"$ref":"#/$defs/ClockState"},"actual_left_endpoint":{"anyOf":[{"$ref":"#/$defs/ActualEndpoint"},{"type":"null"}]}},"required":["target_id","kind","old_segment_id","new_segment_id","clock_after","actual_left_endpoint"],"additionalProperties":false},"CommittedAction":{"type":"object","properties":{"contract_id":{"const":"gq_online_action_transaction_v1"},"status":{"const":"COMMITTED"},"action_commit_id":{"$ref":"#/$defs/Sha256"},"checkpoint_id":{"$ref":"#/$defs/Sha256"},"start_tick":{"$ref":"#/$defs/DecisionTick"},"assignment":{"type":"array","items":{"$ref":"#/$defs/Assignment"},"minItems":2,"maxItems":16},"transitions":{"type":"array","items":{"$ref":"#/$defs/ActionTransition"}},"assignment_change_count":{"type":"integer","minimum":0,"maximum":16},"change_cost":{"type":"number","minimum":0},"simulated_time_advance":{"const":0.0},"prepared_actual_slots":{"type":"array","items":{"$ref":"#/$defs/QueriedMeasurementSlot"}}},"required":["contract_id","status","action_commit_id","checkpoint_id","start_tick","assignment","transitions","assignment_change_count","change_cost","simulated_time_advance","prepared_actual_slots"],"additionalProperties":false},"ActionInProgress":{"type":"object","properties":{"contract_id":{"const":"gq_online_action_transaction_v1"},"status":{"const":"IN_PROGRESS"},"request_fingerprint":{"$ref":"#/$defs/Sha256"},"new_transaction_started":{"const":false},"deadline_extended":{"const":false}},"required":["contract_id","status","request_fingerprint","new_transaction_started","deadline_extended"],"additionalProperties":false},"ActionRejection":{"type":"object","properties":{"contract_id":{"const":"gq_online_action_transaction_v1"},"status":{"const":"REJECTED"},"reason":{"enum":["REQUEST_ID_CONFLICT","BUSY","STALE_CHECKPOINT","WRONG_START_TICK","NONDECISION_BOUNDARY","PARTIAL_TEAM","INVALID_ROLE","RESOURCE_CONFLICT","HIDDEN_OR_ENDED_TARGET","TERMINAL_ENVIRONMENT","BOUNDARY_ALREADY_COMMITTED","MALFORMED_INPUT"]},"committed_assignment_or_fees_changed":{"const":false},"new_sampling_attempts":{"const":0}},"required":["contract_id","status","reason","committed_assignment_or_fees_changed","new_sampling_attempts"],"additionalProperties":false},"ActionFailure":{"type":"object","properties":{"contract_id":{"const":"gq_online_action_transaction_v1"},"status":{"const":"FAILED"},"reason":{"enum":["IPC_ERROR","IDENTITY_CONFLICT","INPUT_MUTATION","NUMERIC_CONTRACT_ERROR","SOLVER_ERROR","RESOURCE_LIMIT"]},"last_committed_checkpoint_id":{"$ref":"#/$defs/Sha256"},"partial_assignment_commit":{"const":false},"partial_change_fee_commit":{"const":false},"simulation_time_advance":{"const":0.0},"sampling_attempts_retained":{"type":"integer","minimum":0},"resolved_actual_slots_retained":{"type":"array","items":{"$ref":"#/$defs/QueriedMeasurementSlot"}},"automatic_retry_allowed":{"const":false}},"required":["contract_id","status","reason","last_committed_checkpoint_id","partial_assignment_commit","partial_change_fee_commit","simulation_time_advance","sampling_attempts_retained","resolved_actual_slots_retained","automatic_retry_allowed"],"additionalProperties":false},"ActionResult":{"type":"object","properties":{"message_kind":{"const":"action_result"},"operation":{"$ref":"#/$defs/OperationIdentity"},"replayed":{"type":"boolean"},"result":{"oneOf":[{"$ref":"#/$defs/CommittedAction"},{"$ref":"#/$defs/ActionInProgress"},{"$ref":"#/$defs/ActionRejection"},{"$ref":"#/$defs/ActionFailure"}]}},"required":["message_kind","operation","replayed","result"],"additionalProperties":false,"allOf":[{"if":{"properties":{"replayed":{"const":true}},"required":["replayed"]},"then":{"properties":{"result":{"$ref":"#/$defs/CommittedAction"}}}}],"description":"Successful replay wraps the original immutable CommittedAction. No second sampling, charge, commit or physical advancement."},"AdvanceRequest":{"type":"object","properties":{"message_kind":{"const":"advance_request"},"operation":{"$ref":"#/$defs/OperationIdentity"},"payload":{"type":"object","properties":{"contract_id":{"const":"gq_online_execution_advance_v1"},"action_commit_id":{"$ref":"#/$defs/Sha256"},"expected_start_tick":{"$ref":"#/$defs/DecisionTick"},"end_tick":{"$ref":"#/$defs/DecisionTick"}},"required":["contract_id","action_commit_id","expected_start_tick","end_tick"],"additionalProperties":false}},"required":["message_kind","operation","payload"],"additionalProperties":false},"AdvanceResult":{"type":"object","properties":{"message_kind":{"const":"advance_result"},"operation":{"$ref":"#/$defs/OperationIdentity"},"contract_id":{"const":"gq_online_execution_advance_v1"},"action_commit_id":{"$ref":"#/$defs/Sha256"},"start_tick":{"$ref":"#/$defs/DecisionTick"},"end_tick":{"$ref":"#/$defs/DecisionTick"},"checkpoint_after":{"$ref":"#/$defs/Checkpoint"},"events":{"type":"array","items":{"$ref":"#/$defs/PublicEvent"}},"physical_intervals_committed":{"type":"integer","minimum":1,"maximum":20}},"required":["message_kind","operation","contract_id","action_commit_id","start_tick","end_tick","checkpoint_after","events","physical_intervals_committed"],"additionalProperties":false},"PublicHistoryBinding":{"type":"object","properties":{"message_kind":{"const":"public_history_binding"},"contract_id":{"const":"gq_online_public_history_binding_v1"},"checkpoint_id":{"$ref":"#/$defs/Sha256"},"previous_checkpoint_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"public_checkpoint":{"$ref":"#/$defs/Checkpoint"},"target_history_digests":{"type":"array","items":{"type":"object","properties":{"target_id":{"$ref":"#/$defs/TargetId"},"history_digest":{"$ref":"#/$defs/Sha256"}},"required":["target_id","history_digest"],"additionalProperties":false}}},"required":["message_kind","contract_id","checkpoint_id","previous_checkpoint_id","public_checkpoint","target_history_digests"],"additionalProperties":false,"description":"Only public content. External execution/admission pins these bytes independently. No trusted/verified boolean or self-computed digest establishes authority."},"FlowOperationIdentity":{"type":"object","properties":{"physical_environment_id":{"type":"string","minLength":1,"maxLength":200},"work_instance_id":{"type":"string","minLength":1,"maxLength":200},"stream_id":{"type":"string","minLength":1,"maxLength":300}},"required":["physical_environment_id","work_instance_id","stream_id"],"additionalProperties":false},"FlowRegistration":{"type":"object","properties":{"message_kind":{"const":"flow_registration"},"contract_id":{"const":"gq_online_flow_registration_v1"},"operation":{"$ref":"#/$defs/FlowOperationIdentity"},"purpose":{"enum":["ACTUAL_EXECUTION","CANDIDATE_PREDICTION","INDEPENDENT_REFERENCE"]},"checkpoint_id":{"$ref":"#/$defs/Sha256"},"evaluation_request_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"world_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"candidate_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"target_id":{"$ref":"#/$defs/TargetId"},"team":{"$ref":"#/$defs/Team"},"service_start_tick":{"$ref":"#/$defs/Tick","description":"Current execution/prediction branch clock origin, not the persistent service segment start_tick."},"actual_endpoint_reused_at_start":{"type":"boolean"},"source_contract_id":{"enum":["gq_online_actual_sampling_v1","gq_mixed_observed_model_left_v1"]},"allowed_sensor_ids":{"type":"array","items":{"$ref":"#/$defs/SensorId"},"minItems":2,"maxItems":3,"uniqueItems":true},"segment_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}],"description":"Actual prepared/committed segment for actual flows; retained actual segment for KEEP prediction/reference; null for nonKEEP hypothetical branches. Never part of a raw slot key."},"first_new_fusion_tick":{"$ref":"#/$defs/Tick","description":"First newly acquired/fused endpoint in this flow. KEEP or resumed settled endpoint k gives k+1 while branch clock origin remains k."}},"required":["message_kind","contract_id","operation","purpose","checkpoint_id","evaluation_request_id","world_id","candidate_id","target_id","team","service_start_tick","first_new_fusion_tick","actual_endpoint_reused_at_start","source_contract_id","allowed_sensor_ids","segment_id"],"additionalProperties":false,"allOf":[{"if":{"properties":{"purpose":{"const":"ACTUAL_EXECUTION"}},"required":["purpose"]},"then":{"properties":{"evaluation_request_id":{"type":"null"},"world_id":{"type":"null"},"candidate_id":{"type":"null"},"source_contract_id":{"const":"gq_online_actual_sampling_v1"},"segment_id":{"$ref":"#/$defs/Sha256"}}}},{"if":{"properties":{"purpose":{"enum":["CANDIDATE_PREDICTION","INDEPENDENT_REFERENCE"]}},"required":["purpose"]},"then":{"properties":{"evaluation_request_id":{"$ref":"#/$defs/Sha256"},"world_id":{"$ref":"#/$defs/Sha256"},"candidate_id":{"$ref":"#/$defs/Sha256"},"source_contract_id":{"const":"gq_mixed_observed_model_left_v1"}}}},{"if":{"properties":{"purpose":{"enum":["CANDIDATE_PREDICTION","INDEPENDENT_REFERENCE"]},"actual_endpoint_reused_at_start":{"const":true}},"required":["purpose","actual_endpoint_reused_at_start"]},"then":{"properties":{"segment_id":{"$ref":"#/$defs/Sha256"}}}},{"if":{"properties":{"purpose":{"enum":["CANDIDATE_PREDICTION","INDEPENDENT_REFERENCE"]},"actual_endpoint_reused_at_start":{"const":false}},"required":["purpose","actual_endpoint_reused_at_start"]},"then":{"properties":{"segment_id":{"type":"null"}}}}]},"TaskArchive":{"type":"object","properties":{"message_kind":{"const":"task_archive"},"visibility":{"const":"AUDIT_ONLY"},"target_id":{"$ref":"#/$defs/TargetId"},"terminal_status":{"enum":["COMPLETED","ESCAPED","UNFINISHED_AT_EPISODE_END"]},"terminal_at":{"$ref":"#/$defs/TimedEventPoint"},"task_history":{"$ref":"#/$defs/TaskHistory"}},"required":["message_kind","visibility","target_id","terminal_status","terminal_at","task_history"],"additionalProperties":false,"description":"Actual finished-task history stays available for whole-episode accounting; it is not an active scoring task and is not inserted in Checkpoint.targets."},"PrivateResumeArtifactDescriptor":{"type":"object","properties":{"message_kind":{"const":"private_resume_artifact_descriptor"},"visibility":{"const":"EXECUTOR_AND_AUDIT_ONLY"},"contract_id":{"const":"gq_online_private_resume_state_v1"},"physical_environment_id":{"type":"string","minLength":1,"maxLength":200},"registered_artifact_id":{"type":"string","minLength":1,"maxLength":200},"path":{"type":"string","minLength":1},"file_sha256":{"$ref":"#/$defs/Sha256"},"size_bytes":{"type":"integer","minimum":0},"committed_tick":{"$ref":"#/$defs/DecisionTick"},"boundary_stage":{"enum":["READY_TO_OBSERVE","READY_TO_EXECUTE","EPISODE_TERMINAL"]},"public_checkpoint_id":{"$ref":"#/$defs/Sha256"},"action_commit_id":{"anyOf":[{"$ref":"#/$defs/Sha256"},{"type":"null"}]},"inflight_transaction":{"type":"null"}},"required":["message_kind","visibility","contract_id","physical_environment_id","registered_artifact_id","path","file_sha256","size_bytes","committed_tick","boundary_stage","public_checkpoint_id","action_commit_id","inflight_transaction"],"additionalProperties":false,"description":"Out-of-band registered artifact descriptor only. Never a field of public checkpoint/request/binding. Persistence is infrastructure, not an additional scientific decision."},"SamplingOperationIdentity":{"type":"object","properties":{"physical_environment_id":{"type":"string","minLength":1,"maxLength":200},"request_id":{"type":"string","minLength":1,"maxLength":200},"action_request_id":{"anyOf":[{"type":"string","minLength":1,"maxLength":200},{"type":"null"}]}},"required":["physical_environment_id","request_id","action_request_id"],"additionalProperties":false}},"x-identity-recipes":{"checkpoint_id":"digest(Checkpoint object minus checkpoint_id)","slot_digest":"for VALID/MISSING, digest(MeasurementSlot minus slot_digest); UNQUERIED has null digest","endpoint_digest":"digest(ActualEndpoint minus endpoint_digest)","segment_id":"digest({contract_id,target_id,segment_index,previous_segment_id,start_tick,team,opened_by}) at its creation; immutable thereafter","segment_history_digest":"digest(ServiceSegment minus segment_history_digest)","history_digest":"digest(TaskHistory minus history_digest)","evaluation_request_id":"digest(EvaluationRequest minus evaluation_request_id)","world_id":"digest({forecast_contract_id,current_endpoint_contract_id,evaluation_request_id})","candidate_id":"digest({evaluation_request_id,world_id,key})","action_commit_id":"digest(CommittedAction minus action_commit_id); record immutable once committed; operational request/environment IDs excluded"}}')

IDS = SCHEMA['x-contract-ids']
ROLES = {2: ('dual_neg45', 'dual_pos45'), 3: ('tri_0', 'tri_120', 'tri_240')}
_TOKEN = object()


def _fail(message):
    raise ContractError(message)


def _plain(value):
    if type(value) is dict:
        if any(type(k) is not str for k in value): _fail('String JSON keys required')
        for v in value.values(): _plain(v)
    elif type(value) is list:
        for v in value: _plain(v)
    elif type(value) is float:
        if not math.isfinite(value): _fail('Nonfinite public number')
    elif value is None or type(value) in (str, bool, int):
        pass
    else:
        _fail('Only plain JSON values; object attributes and closures are forbidden')


def _same(a, b):
    if type(a) is bool or type(b) is bool: return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)): return a == b
    if type(a) is not type(b): return False
    if type(a) is dict: return set(a) == set(b) and all(_same(a[k], b[k]) for k in a)
    if type(a) is list: return len(a) == len(b) and all(_same(x, y) for x, y in zip(a, b))
    return a == b


def _matches(value, schema):
    try:
        _check(value, schema)
        return True
    except ContractError:
        return False


def _check(value, schema, path='$'):
    if '$ref' in schema:
        _check(value, SCHEMA['$defs'][schema['$ref'].split('/')[-1]], path)
    if 'const' in schema and not _same(value, schema['const']): _fail(path+': constant mismatch')
    if 'enum' in schema and not any(_same(value, v) for v in schema['enum']): _fail(path+': enum mismatch')
    for sub in schema.get('allOf', []): _check(value, sub, path)
    for key, minimum, maximum in (('anyOf', 1, None), ('oneOf', 1, 1)):
        if key in schema:
            count = sum(_matches(value, sub) for sub in schema[key])
            if count < minimum or maximum is not None and count > maximum: _fail(path+': '+key+' mismatch')
    if 'if' in schema and _matches(value, schema['if']):
        if 'then' in schema: _check(value, schema['then'], path)
    elif 'if' in schema and 'else' in schema:
        _check(value, schema['else'], path)
    if 'not' in schema and _matches(value, schema['not']): _fail(path+': forbidden shape')
    kind = schema.get('type')
    good = {'object': type(value) is dict, 'array': type(value) is list, 'string': type(value) is str,
            'integer': type(value) is int, 'number': type(value) in (int, float),
            'boolean': type(value) is bool, 'null': value is None}
    if kind is not None and not good.get(kind, False): _fail(path+': typed '+kind+' required')
    if type(value) is dict:
        if any(k not in value for k in schema.get('required', [])): _fail(path+': required field missing')
        if schema.get('additionalProperties') is False and set(value)-set(schema.get('properties', {})):
            _fail(path+': unexpected field')
        for key, sub in schema.get('properties', {}).items():
            if key in value: _check(value[key], sub, path+'.'+key)
    if type(value) is list:
        if len(value) < schema.get('minItems', 0) or len(value) > schema.get('maxItems', math.inf): _fail(path+': array length')
        if schema.get('uniqueItems') and any(_same(value[i], value[j]) for i in range(len(value)) for j in range(i)):
            _fail(path+': duplicate array value')
        if 'items' in schema:
            for i, v in enumerate(value): _check(v, schema['items'], path+'['+str(i)+']')
    if type(value) is str:
        if len(value) < schema.get('minLength', 0) or len(value) > schema.get('maxLength', math.inf): _fail(path+': string length')
        if 'pattern' in schema and re.search(schema['pattern'], value) is None: _fail(path+': string pattern')
    if type(value) in (int, float):
        for key, check in [('minimum', lambda a,b:a>=b), ('maximum',lambda a,b:a<=b),
                           ('exclusiveMinimum',lambda a,b:a>b), ('exclusiveMaximum',lambda a,b:a<b)]:
            if key in schema and not check(value, schema[key]): _fail(path+': '+key)
        if 'multipleOf' in schema and (Fraction(str(value))/Fraction(str(schema['multipleOf']))).denominator != 1:
            _fail(path+': multipleOf')


def _normalize(value, schema):
    if '$ref' in schema: return _normalize(value, SCHEMA['$defs'][schema['$ref'].split('/')[-1]])
    for kind in ('anyOf', 'oneOf'):
        if kind in schema:
            chosen = next(s for s in schema[kind] if _matches(value, s))
            return _normalize(value, chosen)
    if schema.get('type') == 'number' or type(schema.get('const')) is float:
        return float(value)
    if schema.get('type') == 'integer' or type(schema.get('const')) is int:
        if type(value) is not int: _fail('Integer fields cannot be supplied as floats/bools')
        return value
    if type(value) is dict:
        return {k: _normalize(v, schema.get('properties', {}).get(k, {})) for k, v in value.items()}
    if type(value) is list:
        return [_normalize(v, schema.get('items', {})) for v in value]
    return deepcopy(value)


def validate_schema(payload, definition):
    """Validate one role-specific definition, never the permissive root catalogue."""
    if definition not in SCHEMA['$defs']: _fail('Unknown schema definition')
    _plain(payload)
    schema = SCHEMA['$defs'][definition]
    _check(payload, schema)
    result = _normalize(payload, schema)
    _check(result, schema)
    return result


def _content_digest(value, field):
    return digest({k:v for k,v in value.items() if k != field})


def _require_digest(value, field):
    if value[field] != _content_digest(value, field): _fail(field+' mismatch')


def _seal(value, field, definition, defaults=None):
    row = deepcopy(value)
    for k,v in (defaults or {}).items(): row.setdefault(k, v)
    row[field] = '0'*64
    row = validate_schema(row, definition)
    row[field] = _content_digest(row, field)
    return row


def seal_slot(slot):
    row = deepcopy(slot)
    row.setdefault('contract_id', IDS['measurement_slot'])
    row.setdefault('slot_digest', None)
    if row['state'] == 'UNQUERIED': return validate_schema(row, 'MeasurementSlot')
    return _seal(row, 'slot_digest', 'MeasurementSlot')


def seal_endpoint(endpoint):
    return _seal(endpoint, 'endpoint_digest', 'ActualEndpoint', {'source_kind':'ACTUAL'})


def segment_identity(segment):
    keys = ('contract_id','target_id','segment_index','previous_segment_id','start_tick','team','opened_by')
    row = deepcopy(segment)
    row.setdefault('contract_id', IDS['service_segment'])
    return digest({k:row[k] for k in keys})


def seal_segment(segment):
    row = deepcopy(segment)
    row.setdefault('contract_id', IDS['service_segment'])
    row['segment_id'] = segment_identity(row)
    return _seal(row, 'segment_history_digest', 'ServiceSegment')


def seal_history(history):
    return _seal(history, 'history_digest', 'TaskHistory', {'contract_id':IDS['task_history']})


def seal_checkpoint(checkpoint):
    """Writer helper only: computing an ID is not external source admission."""
    return _seal(checkpoint, 'checkpoint_id', 'Checkpoint',
                 {'message_kind':'public_checkpoint','contract_id':IDS['checkpoint']})


def seal_action_commit(result):
    return _seal(result, 'action_commit_id', 'CommittedAction',
                 {'contract_id':IDS['action_transaction'],'status':'COMMITTED'})


def _team(team, q, x):
    robots = [m['robot_id'] for m in team]
    roles = [m['role'] for m in team]
    if (len(team) != q or robots != sorted(set(robots)) or any(i>=x for i in robots)
            or set(roles) != set(ROLES[q])): _fail('Complete ordered unique q/role team required')


def clock_progress(clock):
    return math.fsum((clock['base'], clock['intervals']*DT))


def _events(events, target=None):
    ids=[e['event_index'] for e in events]
    if ids != sorted(set(ids)): _fail('Events must be ordered and globally unique within this list')
    if target is not None and any(e['target_id']!=target for e in events): _fail('Event target mismatch')
    for e in events:
        point=e['at'];tick=point['event_tick']
        if tick is not None and abs(tick*DT-point['time_seconds'])>1e-10: _fail('Event tick/time mismatch')
        if tick is None and e['kind']!='ESCAPED': _fail('Only nongrid escape has null event tick')


def _endpoint(ep, target, team):
    validate_schema(ep,'ActualEndpoint');_require_digest(ep,'endpoint_digest')
    if ep['target_id']!=target or ep['team']!=team: _fail('Endpoint target/team mismatch')
    expected=[(target,m['robot_id'],ep['tick']) for m in team]
    actual=[(r['slot_key']['target_id'],r['slot_key']['robot_id'],r['slot_key']['tick']) for r in ep['slots']]
    if actual!=expected: _fail('Endpoint must bind every team member slot once')
    q=ep['quality'];radius=q['radius_proxy']
    if q['status']=='PASS' and radius>.06 or q['status']=='FAIL' and radius<=.06: _fail('Q threshold classification inconsistent')


def _history(history, target, cp, assigned):
    _require_digest(history,'history_digest')
    j=target['id'];cut=cp['tick'];x=cp['config']['robots'];q=target['required_robots']
    birth=round(target['birth']/DT)
    if history['target_id']!=j or history['cutoff_tick']!=cut or history['birth_tick']!=birth: _fail('History current cut/birth mismatch')
    _events(history['events'],j)
    event_map={e['event_index']:e for e in history['events']}
    intervals=[];previous=None;open_segments=[]
    for index,s in enumerate(history['segments']):
        _require_digest(s,'segment_history_digest')
        if (s['target_id']!=j or s['segment_index']!=index or s['previous_segment_id']!=previous
                or s['segment_id']!=segment_identity(s)): _fail('Segment order/link/identity mismatch')
        previous=s['segment_id'];_team(s['team'],q,x)
        if s['start_tick']<birth or s['start_tick']>cut: _fail('Segment start outside actual history')
        if (s['initial_clock']['base']!=0. or s['initial_clock']['intervals']!=0
                or s['initial_clock']['team']!=s['team'] or s['latest_clock']['team']!=s['team']): _fail('Segment clock/team mismatch')
        _endpoint(s['latest_endpoint'],j,s['team'])
        if not s['start_tick']<=s['latest_endpoint']['tick']<=cut: _fail('Endpoint outside segment/cut')
        _events(s['events'],j)
        if any(e['event_index'] not in event_map or event_map[e['event_index']]!=e for e in s['events']): _fail('Segment events not in task history')
        close=s['closure']
        if close is None:
            open_segments.append(s);end=cut*DT
        else:
            end=close['at']['time_seconds']
            if close['closing_event_index'] not in event_map: _fail('Segment closing event missing')
            if close['reason'] in ('COMPLETED','ESCAPED','EPISODE_END'): _fail('Terminal task cannot remain in active history')
        if end<s['start_tick']*DT-1e-10 or end>cut*DT+1e-10: _fail('Segment closure outside history')
        intervals.append((s['start_tick']*DT,end))
    open_gaps=[]
    for gap in history['unassigned_intervals']:
        if gap['start_tick']<birth or gap['start_tick']>cut: _fail('Unassigned interval start outside history')
        if gap['opening_event_index'] not in event_map: _fail('Unassigned opening event missing')
        if gap['end_at'] is None:
            end=cut*DT;open_gaps.append(gap)
            if gap['closing_event_index'] is not None: _fail('Open gap has a closing event')
        else:
            end=gap['end_at']['time_seconds']
            if gap['closing_event_index'] not in event_map: _fail('Unassigned closing event missing')
        if end<gap['start_tick']*DT-1e-10 or end>cut*DT+1e-10: _fail('Unassigned gap outside actual history')
        intervals.append((gap['start_tick']*DT,end))
    cursor=birth*DT
    for a,b in sorted(intervals):
        if abs(a-cursor)>1e-10: _fail('Service segments/unassigned gaps overlap or leave an unexplained gap')
        cursor=b
    if abs(cursor-cut*DT)>1e-10 or len(open_segments)+len(open_gaps)!=1: _fail('Active history must have exactly one current assigned/unassigned state')
    if assigned:
        if len(open_segments)!=1 or open_gaps: _fail('Assigned task has no unique active segment')
        s=open_segments[0]
        if history['active_segment_id']!=s['segment_id'] or s['team']!=assigned: _fail('Active segment/Assignment mismatch')
        ep=s['latest_endpoint'];progress=clock_progress(s['latest_clock'])
        if ep['tick']!=cut or progress>=target['service_duration'] or progress>(cut-s['start_tick'])*DT+1e-10: _fail('Invalid current endpoint/progress')
        if progress>0 and (not ep['G'] or ep['quality']['status']!='PASS'): _fail('Bad current endpoint retains progress')
    elif open_segments or len(open_gaps)!=1 or history['active_segment_id'] is not None:
        _fail('Unassigned task still has an active segment')


def _semantic_checkpoint(cp):
    _require_digest(cp,'checkpoint_id')
    cfg=cp['config'];x=cfg['robots'];cut=cp['tick'];end=cp['episode_end_tick']
    if end!=round(cfg['stage_dt']*cfg['max_stages']/DT): _fail('Episode endpoint inconsistent with full Config')
    if (cp['phase']=='DECISION_READY' and not cut<end) or (cp['phase']=='TERMINAL' and cut!=end): _fail('Checkpoint phase/time mismatch')
    if len(cp['positions'])!=x or len(cp['assignment'])!=x or len(cp['sensor_profiles'])!=x: _fail('One position/action/profile for every stable Uk required')
    ids=[t['id'] for t in cp['targets']]
    if ids!=sorted(set(ids)) or any(j>=cfg['task_count'] for j in ids): _fail('Invalid global visible target set')
    if [h['target_id'] for h in cp['task_histories']]!=ids: _fail('One ordered history per visible target required')
    if [p['sensor_id'] for p in cp['sensor_profiles']]!=['U'+str(i) for i in range(x)]: _fail('Profile order/identity mismatch')
    if any(p['observed_tick']!=cut for p in cp['sensor_profiles']): _fail('Stale sensor profile')
    by={t['id']:t for t in cp['targets']};teams={j:[] for j in ids}
    for i,a in enumerate(cp['assignment']):
        if a['target'] is not None:
            if a['target'] not in by: _fail('Assignment references hidden/ended task')
            teams[a['target']].append({'robot_id':i,'role':a['role']})
    for t,h in zip(cp['targets'],cp['task_histories']):
        if t['birth']>cut*DT+1e-10 or t['deadline']<t['birth'] or t['birth']>=end*DT: _fail('Invalid visible birth/deadline')
        if (t['required_robots']>x or not 0<=t['position_now'][0]<cfg['side'] or t['velocity_now'][0]<0
                or math.hypot(*t['velocity_now'])>cfg['target_speed_max']+1e-10): _fail('Invalid active target state')
        if teams[t['id']]: _team(teams[t['id']],t['required_robots'],x)
        _history(h,t,cp,teams[t['id']])
    wanted=[(j,i,cut) for j in ids for i in range(x)]
    got=[(s['slot_key']['target_id'],s['slot_key']['robot_id'],s['slot_key']['tick']) for s in cp['current_slots']]
    if got!=wanted: _fail('Explicit current slot matrix incomplete, duplicated or out of order')
    slots={}
    for s in cp['current_slots']:
        key=s['slot_key'];i=key['robot_id'];slots[(key['target_id'],i)]=s
        if s['state']!='UNQUERIED': _require_digest(s,'slot_digest')
        if s['state']=='VALID':
            p=s['packet'];profile=cp['sensor_profiles'][i]
            if (p['sensor_id']!='U'+str(i) or p['measurement_tick']!=cut or p['available_tick']!=cut
                    or p['position']!=cp['positions'][i] or p['sigma']!=profile['sigma'] or profile['health']!='available'):
                _fail('Actual packet differs from its current key/position/profile')
    for h in cp['task_histories']:
        if h['active_segment_id'] is not None:
            seg=next(s for s in h['segments'] if s['segment_id']==h['active_segment_id'])
            for r in seg['latest_endpoint']['slots']:
                s=slots[(r['slot_key']['target_id'],r['slot_key']['robot_id'])]
                if s['state']!=r['state'] or s['slot_digest']!=r['slot_digest']: _fail('Current actual endpoint not bound to current observed slots')
    _events(cp['events_since_previous_checkpoint'])
    if any(e['at']['time_seconds']>cut*DT+1e-10 for e in cp['events_since_previous_checkpoint']): _fail('Future event in current checkpoint')
    if cp['phase']=='TERMINAL' and (ids or any(a['target'] is not None for a in cp['assignment'])): _fail('Terminal checkpoint has active tasks/resources')


class HistoryAuthority:
    """Public-only capability. Loader must independently pin binding file bytes."""
    __slots__=('_binding','_checkpoint_digest')
    def __init__(self,binding,*,_token=None):
        if _token is not _TOKEN: _fail('Only externally admitted binding may create authority')
        object.__setattr__(self,'_binding',json.dumps(binding,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False))
        object.__setattr__(self,'_checkpoint_digest',digest(binding['public_checkpoint']))
    def __setattr__(self,key,value): _fail('Immutable public authority')
    def to_public_binding(self): return json.loads(self._binding)
    @classmethod
    def from_public_binding(cls,binding):
        """Trusted-worker hook ONLY after independently pinned file SHA checks."""
        b=validate_schema(binding,'PublicHistoryBinding')
        cp=validate_checkpoint(b['public_checkpoint'],unit_only=True)
        if (b['checkpoint_id']!=cp['checkpoint_id'] or b['previous_checkpoint_id']!=cp['previous_checkpoint_id']
                or b['target_history_digests']!=[{'target_id':h['target_id'],'history_digest':h['history_digest']} for h in cp['task_histories']]):
            _fail('Public binding content mismatch')
        return cls(b,_token=_TOKEN)


def binding_from_checkpoint(checkpoint):
    cp=validate_checkpoint(checkpoint,unit_only=True)
    return {'message_kind':'public_history_binding','contract_id':IDS['public_binding'],
            'checkpoint_id':cp['checkpoint_id'],'previous_checkpoint_id':cp['previous_checkpoint_id'],
            'public_checkpoint':cp,'target_history_digests':[{'target_id':h['target_id'],'history_digest':h['history_digest']} for h in cp['task_histories']]}


def validate_checkpoint(payload,authority=None,unit_only=False):
    if type(unit_only) is not bool: _fail('Explicit unit_only bool required')
    cp=validate_schema(payload,'Checkpoint');_semantic_checkpoint(cp)
    if not unit_only:
        if type(authority) is not HistoryAuthority or authority._checkpoint_digest!=digest(cp):
            _fail('Checkpoint lacks the exact externally admitted actual public binding')
    return cp


validate_public_checkpoint=validate_checkpoint


def request_from_checkpoint(checkpoint,authority=None,unit_only=False):
    cp=validate_checkpoint(checkpoint,authority,unit_only)
    if cp['phase']!='DECISION_READY': _fail('No decision after true episode end')
    result={'message_kind':'evaluation_request','contract_id':IDS['evaluation_request'],
      'evaluation_request_id':'0'*64,'checkpoint':cp,'prediction_end_tick':min(cp['episode_end_tick'],cp['tick']+60),
      'forecast_contract_id':IDS['future_forecast'],'current_endpoint_contract_id':IDS['current_prediction_endpoint'],
      'manifest_order':'target_then_robot_combination_then_frozen_role_permutation'}
    result['evaluation_request_id']=_content_digest(result,'evaluation_request_id')
    return result


def validate_request(request,authority=None,unit_only=False):
    r=validate_schema(request,'EvaluationRequest')
    cp=validate_checkpoint(r['checkpoint'],authority,unit_only)
    if cp['phase']!='DECISION_READY' or r['prediction_end_tick']!=min(cp['episode_end_tick'],cp['tick']+60): _fail('Fixed three-second forecast contract violated')
    _require_digest(r,'evaluation_request_id')
    return r


def world_identity(request):
    return digest({'forecast_contract_id':request['forecast_contract_id'],
      'current_endpoint_contract_id':request['current_endpoint_contract_id'],
      'evaluation_request_id':request['evaluation_request_id']})


def request_identity(request): return request['evaluation_request_id']


def build_manifest(request,authority=None,unit_only=False):
    if request.get('message_kind')=='public_checkpoint': request=request_from_checkpoint(request,authority,unit_only)
    r=validate_request(request,authority,unit_only);cp=r['checkpoint'];world=world_identity(r)
    if sum(math.perm(cp['config']['robots'],t['required_robots']) for t in cp['targets'])>1500: _fail('Candidate limit exceeded')
    specs=[]
    for t in cp['targets']:
        for robots in combinations(range(cp['config']['robots']),t['required_robots']):
            for roles in permutations(ROLES[t['required_robots']]):
                key={'target':t['id'],'robots':list(robots),'roles':list(roles)}
                identity={'evaluation_request_id':r['evaluation_request_id'],'world_id':world,'key':key}
                specs.append({'message_kind':'candidate_descriptor','candidate_id':digest(identity),
                  **identity,'index':len(specs),'resource_mask':sum(1<<i for i in robots)})
    return {'payload':r,'request_identity':r['evaluation_request_id'],'world_identity':world,
            'candidate_count':len(specs),'candidates':specs}


def enumerate_candidates(request,authority=None,unit_only=False):
    return build_manifest(request,authority,unit_only)['candidates']


def validate_candidate(request,spec,authority=None,unit_only=False):
    clean=validate_schema(spec,'CandidateDescriptor')
    known=enumerate_candidates(request,authority,unit_only)
    if clean not in known: _fail('Candidate identity/key/index is not in the exact canonical manifest')
    return deepcopy(clean)


def _validate_actions(cp,actions):
    _plain(actions)
    if type(actions) is not list or len(actions)!=cp['config']['robots']: _fail('Exactly one action per stable Uk required')
    acts=[validate_schema(a,'Assignment') for a in actions]
    targets={t['id']:t for t in cp['targets']};groups={j:[] for j in targets}
    for i,a in enumerate(acts):
        if a['target'] is not None:
            if a['target'] not in targets: _fail('Hidden/ended target in action')
            groups[a['target']].append({'robot_id':i,'role':a['role']})
    for j,team in groups.items():
        if team: _team(team,targets[j]['required_robots'],cp['config']['robots'])
    return acts,groups


def validate_action_request(envelope,checkpoint):
    e=validate_schema(envelope,'ActionRequest');cp=validate_checkpoint(checkpoint,unit_only=True)
    if cp['phase']!='DECISION_READY' or e['payload']['checkpoint_id']!=cp['checkpoint_id'] or e['payload']['expected_start_tick']!=cp['tick']:
        _fail('Stale/wrong/terminal action boundary')
    _validate_actions(cp,e['payload']['assignment'])
    return e


def plan_action_metadata(checkpoint,actions,work_identity,*,physical_environment_id=None):
    """Pure metadata, not admission/commit. Caller first validates actual authority."""
    cp=validate_checkpoint(checkpoint,unit_only=True);actions,groups=_validate_actions(cp,actions)
    if cp['phase']!='DECISION_READY' or type(work_identity) is not str or not work_identity: _fail('Invalid action metadata context')
    transitions=[];flows=[]
    for h in cp['task_histories']:
        j=h['target_id'];team=groups[j]
        old=next((s for s in h['segments'] if s['segment_id']==h['active_segment_id']),None)
        old_team=[] if old is None else old['team'];same=bool(team) and team==old_team
        if same:
            kind='KEEP';segment_id=old['segment_id'];clock=deepcopy(old['latest_clock']);endpoint=deepcopy(old['latest_endpoint'])
            opened_by=None;index=old['segment_index'];previous=old['previous_segment_id']
        else:
            endpoint=None;clock={'base':0.,'intervals':0,'team':deepcopy(team)}
            index=len(h['segments']);previous=h['segments'][-1]['segment_id'] if h['segments'] else None
            if not team: kind='WITHDRAW' if old is not None else 'UNCHANGED_UNASSIGNED';opened_by=None;segment_id=None
            else:
                if old is None: kind='REASSIGN' if h['segments'] else 'FIRST_ASSIGNMENT';opened_by='REASSIGNMENT' if h['segments'] else 'INITIAL_ASSIGNMENT'
                else:
                    kind='ROLE_CHANGE' if [m['robot_id'] for m in team]==[m['robot_id'] for m in old_team] else 'MEMBER_CHANGE';opened_by=kind
                segment_id=segment_identity({'target_id':j,'segment_index':index,'previous_segment_id':previous,
                    'start_tick':cp['tick'],'team':team,'opened_by':opened_by})
        row={'target_id':j,'kind':kind,'old_segment_id':None if old is None else old['segment_id'],
             'new_segment_id':segment_id,'segment_id':segment_id,'team':deepcopy(team),'clock_state':clock,
             'actual_endpoint':endpoint,'segment_index':index,'previous_segment_id':previous,'opened_by':opened_by,
             'service_start_tick':cp['tick'],'first_new_fusion_tick':cp['tick']+1 if same else cp['tick'],
             'allowed_sensor_ids':['U'+str(m['robot_id']) for m in team],
             'stream_id':f'{work_identity}:T{j}:first{cp["tick"]+1 if same else cp["tick"]}' if team else None,
             'actual_endpoint_reused_at_start':same}
        transitions.append(row)
        if team:
            if type(physical_environment_id) is not str or not physical_environment_id:
                _fail('Stable physical_environment_id must be supplied for actual flow metadata')
            flow=make_flow_registration(cp,team,j,work_identity,physical_environment_id,
                purpose='ACTUAL_EXECUTION',segment_id=segment_id,reused=same)
            row['flow_registration']=flow
            row['context']=flow_context(flow)
            row['registration']=sensing_registration(flow)
            flows.append(deepcopy(row))
    changes=sum(a!=b for a,b in zip(cp['assignment'],actions))
    return {'actions':actions,'assignment_change_count':changes,'change_count':changes,
            'change_cost':float(cp['config']['change_cost']*changes),'transitions':transitions,'flows':flows}


def make_flow_registration(checkpoint,team,target_id,work_identity,physical_environment_id,*,
                           purpose,segment_id,reused,request=None,candidate=None):
    start=checkpoint['tick'];first=start+int(reused)
    stream=f'{work_identity}:T{target_id}:first{first}'
    actual=purpose=='ACTUAL_EXECUTION'
    flow={'message_kind':'flow_registration','contract_id':IDS['flow_registration'],
      'operation':{'physical_environment_id':physical_environment_id,'work_instance_id':work_identity,'stream_id':stream},
      'purpose':purpose,'checkpoint_id':checkpoint['checkpoint_id'],
      'evaluation_request_id':None if actual else request['evaluation_request_id'],
      'world_id':None if actual else world_identity(request),
      'candidate_id':None if actual else candidate['candidate_id'],
      'target_id':target_id,'team':deepcopy(team),'service_start_tick':start,'first_new_fusion_tick':first,
      'actual_endpoint_reused_at_start':reused,'source_contract_id':IDS['actual_sampling'] if actual else IDS['current_prediction_endpoint'],
      'allowed_sensor_ids':['U'+str(m['robot_id']) for m in team],'segment_id':segment_id}
    return validate_schema(flow,'FlowRegistration')


def flow_context(flow):
    f=validate_schema(flow,'FlowRegistration');op=f['operation'];actual=f['purpose']=='ACTUAL_EXECUTION'
    if f['first_new_fusion_tick']!=f['service_start_tick']+int(f['actual_endpoint_reused_at_start']): _fail('Flow first endpoint mismatch')
    return {'work_instance_id':op['work_instance_id'],'physical_environment_id':op['physical_environment_id'],
      'purpose':f['purpose'],'checkpoint_id':f['checkpoint_id'],
      'request_identity':f['checkpoint_id'] if actual else f['evaluation_request_id'],
      'world_identity':f['world_id'],'action_identity':f['segment_id'] if actual else f['candidate_id'],
      'segment_id':f['segment_id'],'service_start_tick':f['service_start_tick'],
      'first_new_fusion_tick':f['first_new_fusion_tick']}


def sensing_registration(flow):
    f=validate_schema(flow,'FlowRegistration')
    return {'stream_id':f['operation']['stream_id'],'target_id':f['target_id'],
      'start_tick':f['first_new_fusion_tick'],'allowed_sensor_ids':deepcopy(f['allowed_sensor_ids']),
      'context':flow_context(f)}


def prediction_metadata(request,candidate,work_identity,authority=None,unit_only=False,*,
                        physical_environment_id='prediction-context',purpose='CANDIDATE_PREDICTION'):
    r=validate_request(request,authority,unit_only);s=validate_candidate(r,candidate,authority,unit_only)
    cp=r['checkpoint'];j=s['key']['target'];team=[{'robot_id':i,'role':role} for i,role in zip(s['key']['robots'],s['key']['roles'])]
    h=next(h for h in cp['task_histories'] if h['target_id']==j)
    segment=next((g for g in h['segments'] if g['segment_id']==h['active_segment_id']),None)
    keep=segment is not None and segment['team']==team
    flow=make_flow_registration(cp,team,j,work_identity,physical_environment_id,purpose=purpose,
      segment_id=segment['segment_id'] if keep else None,reused=keep,request=r,candidate=s)
    return {'flow_registration':flow,'registration':sensing_registration(flow),'context':flow_context(flow),
      'stream_id':flow['operation']['stream_id'],'team':team,'target_id':j,'reused_actual_endpoint':keep,
      'actual_endpoint':deepcopy(segment['latest_endpoint']) if keep else None,
      'clock_state':deepcopy(segment['latest_clock']) if keep else {'base':0.,'intervals':0,'team':team},
      'first_new_fusion_tick':flow['first_new_fusion_tick'],'service_start_tick':cp['tick'],
      'allowed_sensor_ids':deepcopy(flow['allowed_sensor_ids'])}


def validate_assignment(checkpoint, actions):
    cp=validate_checkpoint(checkpoint,unit_only=True)
    return _validate_actions(cp,actions)[0]
