"""Append-only closeout: JSON/AST/hash inspection only, no project imports or tests."""
import ast,json,hashlib,subprocess,sys
from pathlib import Path
ROOT=Path.cwd()
OUT=ROOT/'reports/stfbs_lite_d1a_h1_revalidation_001'
CLOSE=Path(__file__).resolve().parent
HEAD='c75f364bf32e6fc63be6a7080d4f21bc6d75ec55'
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
assert git('rev-parse','HEAD')==HEAD
raw_target=OUT/'RAW_MEASUREMENT_AUDIT.json'
targets=[raw_target,CLOSE/'FINAL_RESEARCH_DECISION.json',CLOSE/'FINAL_REPORT.md',CLOSE/'ADDITIONAL_SHA256.json']
assert not any(p.exists() for p in targets)
inventory=sorted(p.name for p in OUT.iterdir())
original_index=read(OUT/'SHA256.json')
original_index_sha=sha(OUT/'SHA256.json')
assert all(sha(ROOT/p)==s for p,s in original_index.items())
approval=read(ROOT/'reports/stfbs_lite_d1a_h1_authorization_001/APPROVAL.json')
assert len(approval['source_pins'])==45
assert all(sha(ROOT/p)==s for p,s in approval['source_pins'].items())
accept=read(OUT/'ACCEPTANCE.json')
gates=read(OUT/'GATE_ACCEPTANCE_MATRIX.json')
assert all(g['status']=='PASS' for g in gates.values())
independent=read(OUT/'READ_ONLY_INDEPENDENT_REVIEW_002.json')
assert independent['status']=='PASS'
reuse=read(OUT/'REGISTERED_TEST_EVIDENCE_REUSE_002.json')
assert reuse['status']=='PASS'
protocol=ROOT/'reports/stfbs_lite_d1a_h1_revalidation_prep_001/ORIGINAL_D1A_V1_3_REFERENCE.txt'
assert 'RAW_MEASUREMENT_AUDIT.json' in protocol.read_text(encoding='utf-8')
branch_ledgers={n:read(OUT/(n+'_RESOURCE.json')) for n in ('KEEP','SWITCH')}
resource=read(OUT/'RESOURCE_LEDGER.json')
runtime=read(ROOT/'reports/stfbs_lite_d1a_h1_revalidation_001_watchdog/WATCHDOG_RECEIPT.json')
pair=read(OUT/'MODEL_PAIR_RESULT.json')
assert pair['J_KEEP']==-0.3150141073101529 and pair['J_SWITCH']==-0.144065068155969 and pair['delta']==0.17094903915418388
location_cache={}
def locate(path,symbol,mechanism,test=False):
    if path not in location_cache:
        text=(ROOT/path).read_text(encoding='utf-8-sig');tree=ast.parse(text);found={}
        def walk(nodes,prefix=''):
            for node in nodes:
                if isinstance(node,(ast.ClassDef,ast.FunctionDef,ast.AsyncFunctionDef)):
                    full=prefix+node.name
                    found[full]=node
                    walk(node.body,full+'.')
        walk(tree.body)
        location_cache[path]=(text,found)
    text,found=location_cache[path]
    assert symbol in found,(path,symbol)
    node=found[symbol]
    # Check that the referenced function really exists in the specified committed version.
    committed=subprocess.check_output(['git','show',HEAD+':'+path])
    assert hashlib.sha256(committed).hexdigest()==sha(ROOT/path)
    d=dict(path=path,symbol=symbol,line_start=node.lineno,line_end=node.end_lineno,commit=HEAD,sha256=sha(ROOT/path),mechanism=mechanism)
    if test:d['test_symbol']=symbol
    return d
state='research/non_oracle/stfbs_d1a_state.py'
model='research/non_oracle/stfbs_d1a_model.py'
history='research/non_oracle/stfbs_d1a_history.py'
audit='research/non_oracle/stfbs_d1a_history_audit.py'
teststate='tests/test_stfbs_d1a_state.py'
testrepair='tests/test_stfbs_d1a_history_repair.py'
testhard='tests/test_stfbs_d1a_audit_hardening.py'
testprep='tests/test_stfbs_d1a_h1_revalidation_prep.py'
state_log='reports/stfbs_lite_d1a_001/STATE_TESTS_FIRST.log'
assert 'Ran 4 tests' in (ROOT/state_log).read_text() and 'OK' in (ROOT/state_log).read_text()
testpins=read(ROOT/'reports/stfbs_lite_d1a_001/PRE_MAIN_SOURCE_PINS.json')
assert sha(ROOT/teststate)==testpins['tests\\test_stfbs_d1a_state.py']
assert sha(ROOT/state)==testpins['research\\non_oracle\\stfbs_d1a_state.py']
mechanisms=[]
def mechanism(name,sources,tests,why,refs,evidence_class='REUSED_HISTORICAL_NEGATIVE_TEST',observed=False,limit=None):
    row=dict(mechanism=name,source_locations=[locate(p,s,name) for p,s in sources],
        test_locations=[locate(p,s,name,True) for p,s in tests],proves=why,
        evidence_refs=refs,evidence_class=evidence_class,observed_in_this_H1=observed)
    if limit:row['verification_boundary']=limit
    mechanisms.append(row)
cache_src=[(state,'ModelRawCache.query'),(model,'Branch.raw')]
cache_test=[(teststate,'StateTests.test_raw_identity_matrix')]
mechanism('raw_measurement_cache_identity',cache_src,cache_test,
    'Cache key is exactly (branch,target,robot,tick); position/sigma/health are separately checked context. Formal feedback slots retain target/robot/tick with outer branch identity.',
    ['KEEP_RAW.json#/feedback','SWITCH_RAW.json#/feedback','READ_ONLY_INDEPENDENT_REVIEW_002.json#/branches'], 'OBSERVED_IN_FORMAL_H1',True)
mechanism('same_key_same_context_reuse',cache_src,cache_test,
    'Historical unit test requests the same key/context repeatedly and asserts producer count remains one. This H1 recorded zero cache reuse.',
    [state_log,'REGISTERED_TEST_EVIDENCE_REUSE_002.json','KEEP_RESOURCE.json#/raw','SWITCH_RESOURCE.json#/raw'],
    limit='Cache-interface test evidence only; not an observed reuse event in the formal H1.')
mechanism('same_key_changed_context_rejected',cache_src,cache_test,
    'Historical test separately changes position, sigma and health and expects rejection; current H1 conflicts=0.',
    [state_log,'REGISTERED_TEST_EVIDENCE_REUSE_002.json'],
    limit='Formal H1 did not exercise any conflict rejection.')
mechanism('service_segment_role_stream_changes_do_not_change_raw_key',
    cache_src+[(model,'Branch.fuse'),(history,'prepare_assignment')],
    cache_test+[(testrepair,'HistoryRepairTests.test_member_role_and_cut_boundaries')],
    'Raw-key schema omits role/team/segment/stream. Cache unit test repeats identical queries under four nominal labels; transaction test verifies real role/team historical boundaries with a fusion substitute.',
    [state_log,'reports/stfbs_lite_d1a_g3_history_repair_001/FINAL_IDENTITY_GUARDED_TESTS.log',
     'reports/stfbs_lite_d1a_g3_audit_hardening_001/FINAL_REGRESSION.log'],
    limit=dict(cache_interface='SUPPORTED_BY_SOURCE_AND_HISTORICAL_TEST',
        actual_segment_change_then_real_fusion_cache_reuse='NOT_VERIFIED',
        reason='The stream loop label is not passed into query; this is repeated-query API evidence, not an end-to-end stream-change/fusion test. The transaction fixture uses fake_fuse. No such reuse is observed in this H1.'))
mechanism('D60_historical_slot_reference',
    [(model,'Branch.__init__'),(state,'ModelRawCache.__init__'),(state,'ModelRawCache.query')],
    [(teststate,'StateTests.test_inherited_slots'),(teststate,'StateTests.test_historical_replay')],
    'Constructor checks historical slot digest/position/sigma and prepares copied history; query checks context and returns a deep copy without producer execution. Historical test uses MISSING and a forbidden producer.',
    [state_log,'EXTERNAL_REGISTRATION.json','H1_COMPATIBILITY.json','KEEP_RESOURCE.json#/raw/inherited_reuses','SWITCH_RESOURCE.json#/raw/inherited_reuses'],
    limit='Unit inherited-slot fixture is MISSING, not a new VALID-slot experiment. Formal H1 inherited_reuses=0; do not claim an actual inherited-cache hit.')
mechanism('cross_branch_cache_isolation',
    [(state,'ModelRawCache.__init__'),(state,'ModelRawCache.query'),(model,'Branch.__init__')],
    cache_test,
    'Historical test creates separate KEEP/SWITCH caches, invokes each producer and checks a mutation of one cached slot leaves the other MISSING. Actual H1 branch/stream/endpoint identities are separately verified.',
    [state_log,'KEEP_RAW.json#/branch','SWITCH_RAW.json#/branch','READ_ONLY_INDEPENDENT_REVIEW_002.json'],
    limit='Cache isolation mutation test does not itself exercise every possible pending/fusion-result mutation. New formal H1 does not intentionally inject cross-branch pollution.')
mechanism('wrong_measurement_identity_rejected',
    cache_src+[(audit,'audit_branch_independent')],
    cache_test+[(testhard,'HardeningTests.test_separate_record_identity'),(testhard,'HardeningTests.test_full_relabel_and_internal_context')],
    'Unit test rejects foreign branch and tampered cached slot digest; hardening tests reject event/segment/endpoint branch relabel against independently fixed context.',
    [state_log,'reports/stfbs_lite_d1a_g3_audit_hardening_001/FINAL_REGRESSION.log',
     'reports/stfbs_lite_d1a_g3_audit_hardening_001/MODEL_EVENT_SEGMENT_ENDPOINT_NEGATIVES.json',
     'KEEP_AUDITS.json#/history','SWITCH_AUDITS.json#/history'],
    limit='Do not infer a separately executed wrong-stream BridgeFrameProcessor test from a cache test.')
mechanism('endpoint_fusion_and_model_feedback',
    [(model,'Branch.fuse'),(state,'ModelBeliefConsumer.enqueue'),(history,'prepare_assignment')],
    [(teststate,'StateTests.test_model_belief_differential'),(testprep,'PreparationTests.test_real_pure_state')],
    'Formal per-endpoint records bind team, stream/frame, MODEL endpoint and consumed feedback. Observation fusion is counted separately from raw requests and policy WLS.',
    ['KEEP_RAW.json#/feedback','SWITCH_RAW.json#/feedback','KEEP_AUDITS.json','SWITCH_AUDITS.json','READ_ONLY_INDEPENDENT_REVIEW_002.json'],
    'OBSERVED_IN_FORMAL_H1',True,
    'Pure-state fixture substitutes fusion; actual observation/WLS execution evidence comes from this H1, not from that fixture.')
mechanism('assignment_history_endpoint_transaction',
    [(model,'Branch.assign'),(history,'prepare_assignment')],
    [(testrepair,'HistoryRepairTests.test_atomic_validation_and_prepare_failures'),
     (testrepair,'HistoryRepairTests.test_fusion_failure_and_final_staging_corruption'),
     (testrepair,'HistoryRepairTests.test_keep_switch_withdraw_unassigned')],
    'Validated staged assignment commit maintains service/unassigned intervals and endpoint identity; historical failure injection checks state remains unchanged. New H1 directly audited completed Branch objects.',
    ['reports/stfbs_lite_d1a_g3_history_repair_001/FINAL_IDENTITY_GUARDED_TESTS.log',
     'KEEP_AUDITS.json#/history','SWITCH_AUDITS.json#/history','READ_ONLY_INDEPENDENT_REVIEW_002.json#/branches'],
    'RUNTIME_INDEPENDENT_AUDIT',True)
mechanism('shared_WLS_budget_and_resource_accounting',
    [(model,'Budget.estimator'),(model,'Budget.choose'),('scripts/stfbs_d1a_run.py','run_pair')],
    [('tests/test_stfbs_d1a_acceptance.py','AcceptanceTests.test_budget_guards_before_solver'),(testprep,'PreparationTests.test_stub_orchestration')],
    'Both branch ledgers share continuous cumulative counts; formal watchdog and read-only audit separately bind model observation/policy WLS and CPU/wall evidence.',
    ['KEEP_RESOURCE.json','SWITCH_RESOURCE.json','COST.json','RESOURCE_LEDGER.json',
     'READ_ONLY_INDEPENDENT_REVIEW_002.json#/resource','../stfbs_lite_d1a_h1_revalidation_001_watchdog/WATCHDOG_RECEIPT.json'],
    'READ_ONLY_REAUDIT',True)
# Extract identity indices only. No trajectory, geometry, economics or prediction is evaluated.
formal={}
for name in ('KEEP','SWITCH'):
    raw=read(OUT/(name+'_RAW.json'));ledger=branch_ledgers[name]
    expected=dict(KEEP=(66,33,590),SWITCH=(76,38,594))[name]
    assert raw['raw_counts']['requests']==raw['raw_counts']['new']==expected[0]
    assert raw['raw_counts']['reuses']==raw['raw_counts']['conflicts']==raw['raw_counts']['inherited_reuses']==0
    assert raw['endpoint_fusions']==len(raw['feedback'])==expected[1]
    assert ledger['delta']['MODEL_OBSERVATION_WLS']==expected[1] and ledger['delta']['MODEL_POLICY_EVALUATION_WLS']==expected[2]
    snapshots=[]
    for d in raw['decisions']:
        for h in d['view']['histories']:
            for s in h['segments']:
                snapshots.append(dict(cut=d['view']['tick'],target=h['target_id'],segment=s))
    identities=[];fusions=[]
    for number,f in enumerate(raw['feedback']):
        frame=f['frame'];endpoint=f['endpoint']
        candidates=sorted({s['segment']['segment_id'] for s in snapshots if s['target']==frame['target_id'] and s['segment']['team']==endpoint['team'] and s['segment']['start_tick']<=frame['tick']})
        fusions.append(dict(evidence_class='OBSERVED_IN_FORMAL_H1',branch=name,target=frame['target_id'],tick=frame['tick'],stream_id=frame['stream_id'],frame_id=frame['frame_id'],team=endpoint['team'],service_segment_candidates=candidates,
            segment_join_scope='References team/target/start-matching saved D80/D100 histories, not a new final Branch reconstruction.',
            raw_record_ref=name+'_RAW.json#/feedback/'+str(number),runtime_audit_ref=name+'_AUDITS.json',
            MODEL_origin=endpoint['observation_origin'],provenance=endpoint['provenance']))
        for slotno,slot in enumerate(f['slots']):
            k=slot['slot_key']
            identities.append(dict(evidence_class='OBSERVED_IN_FORMAL_H1',branch=name,target=k['target_id'],robot=k['robot_id'],tick=k['tick'],state=slot['state'],slot_digest=slot['slot_digest'],
                packet_context=dict(position=slot['packet']['position'],sigma=slot['packet']['sigma']) if slot['packet'] else None,
                ref=name+'_RAW.json#/feedback/'+str(number)+'/slots/'+str(slotno),stream_id=frame['stream_id'],frame_id=frame['frame_id']))
    formal[name]=dict(evidence_class='OBSERVED_IN_FORMAL_H1',environment_identity=dict(kind='independent_MODEL_branch',run_path=OUT.relative_to(ROOT).as_posix(),branch=name,world_digest=raw['world']['world_digest'],public_digest=raw['world']['public_digest'],scientific_execution_commit=approval['head'],new_ACTUAL_environment=False),
        raw_counts=raw['raw_counts'],raw_request_identities=identities,fusion_count=raw['endpoint_fusions'],fusion_identities=fusions,WLS=ledger['delta'],resource_ref=name+'_RESOURCE.json',
        actual_reuse_observation=dict(evidence_class='NOT_OBSERVED_IN_THIS_H1',cache_reuse=0,context_conflict=0,inherited_hit=0))
d60=read(ROOT/'runs/a2_switch_episode_001/R_D60.json')['policy_input']
historic_slots=[dict(slot_key=s['slot_key'],state=s['state'],slot_digest=s['slot_digest']) for s in d60['current_slots']]
original_files={p:sha(ROOT/p) for p in original_index}
audit_payload=dict(task='D1-A-FINAL-CLOSEOUT-0',index_commit=HEAD,scientific_execution_commit=approval['head'],scope='Append-only source/test/evidence index; no new scientific calculations or tests',
    target_directory=OUT.relative_to(ROOT).as_posix(),files_before_append=inventory,original_SHA256_manifest=original_index_sha,
    evidence_classes=['OBSERVED_IN_FORMAL_H1','RUNTIME_INDEPENDENT_AUDIT','READ_ONLY_REAUDIT','REUSED_HISTORICAL_NEGATIVE_TEST','NOT_OBSERVED_IN_THIS_H1','NOT_VERIFIED'],
    identity_layers=dict(exogenous_MODEL_world='Original frozen H1 public/world digest; shared zero disturbance, independent MODEL branches',raw='(branch,target,robot,tick); position/sigma/health are context, not key',fusion_and_service='team/role/segment and stream/frame bind a fusion to raw slots; fusion identity is not a new raw-sampling key'),
    formal_observations=formal,historical_D60_slots=dict(evidence_class='READ_ONLY_REAUDIT',source='runs/a2_switch_episode_001/R_D60.json#/policy_input/current_slots',provenance='Inherited legal ACTUAL past from the archived D60, not relabeled as new MODEL samples',slots=historic_slots,formal_inherited_cache_hits=dict(KEEP=0,SWITCH=0),mechanism_refs=['D60_historical_slot_reference'],no_new_history_test=True),
    mechanisms=mechanisms,WLS_ledger=dict(KEEP=branch_ledgers['KEEP'],SWITCH=branch_ledgers['SWITCH'],total=read(OUT/'COST.json'),
        ACTUAL_WLS=0,ACTUAL_STEP=0,shared_continuity=branch_ledgers['KEEP']['after']==branch_ledgers['SWITCH']['before'],endpoint_fusions=71,new_raw_measurements=142,
        independent_review_ref='READ_ONLY_INDEPENDENT_REVIEW_002.json#/resource',watchdog=dict(path='reports/stfbs_lite_d1a_h1_revalidation_001_watchdog/WATCHDOG_RECEIPT.json',sha256=sha(ROOT/'reports/stfbs_lite_d1a_h1_revalidation_001_watchdog/WATCHDOG_RECEIPT.json'),record=runtime)),
    verification_boundaries=['Historical repeated-query test stream labels are not real service/stream transitions. End-to-end same-tick segment-change plus real-fusion cache-reuse test is NOT_VERIFIED by those unit fixtures.',
       'Historical inherited-slot fixture uses MISSING. Formal H1 has no inherited cache hit/reuse/conflict rejection; do not report such an event.',
       'Cache mutation isolation test is not a claim of having separately injected every possible pending/fusion mutation or wrong-stream request.'],
    this_task_operations=dict(Branch_run=0,Branch_advance=0,OnlineEnvironment_step=0,WLS=0,new_scientific_results=0,tests_run=0,method='Standard-library JSON reads, AST location, hash comparison and Git read-only queries only; no project imports'),
    source_versions_unchanged=True)
attachment=Path(r'C:\Users\14738\.codex\attachments\b9543cf3-b4ee-45a4-a702-3fac9a787b75\已粘贴的文本.txt')
decision=dict(task='D1-A-FINAL-CLOSEOUT-0',status='D1_A_FINAL_CLOSEOUT_READY_FOR_REVIEW',accepted_limited_conclusion='D1_A_MODEL_PAIR_VALIDATED',
    resolved_scope='Prior D1_A_BLOCKED conditions concerning this original frozen H1 MODEL revalidation are resolved by the user-authorized limited acceptance.',
    basis=dict(formal_archive=OUT.relative_to(ROOT).as_posix(),original_gate_statuses={g:v['status'] for g,v in gates.items()},
        review_source='User-provided current instruction states principal and independent reviewer accepted the existing evidence; this task records that decision.',authorization_attachment_sha256=sha(attachment),
        newly_conducted_independent_review=False,signatures_or_personal_approver_identity_invented=False),
    historic_acceptance_files_modified=False,state_code_or_forced_transition_modified=False,
    accepted_results=dict(KEEP=pair['J_KEEP'],SWITCH=pair['J_SWITCH'],MODEL_delta=pair['delta'],MODEL_WLS=1255,ACTUAL_WLS=0,ACTUAL_STEP=0),
    no_new_scientific_blocker_identified_for_this_accepted_H1=True,
    not_established=['complete STFBS-Lite core algorithm','effective autonomous MEMBER_CHANGE','statistical SWITCH advantage across scenarios','ACTUAL net-benefit improvement','real-robot closed-loop validation','independent TEST'],
    evidence_scope_limitations=audit_payload['verification_boundaries'],
    existing_gate_review_unchanged=True,append_only=True,original_files_preserved=len(original_index),
    source_pins_verified=45,closeout_new_execution_counts=audit_payload['this_task_operations'])
report='''# D1-A 最终科研归档与限定验收收尾

本轮状态：D1_A_FINAL_CLOSEOUT_READY_FOR_REVIEW。

依据用户本次正式指令转述的主研员复核和独立审查意见，追加记录接受 D1_A_MODEL_PAIR_VALIDATED：原冻结 H1 的联合 MODEL 成对评价已完成限定 G0—G5 验收；此前与这次 H1 正式复验有关的 D1_A_BLOCKED 阻断解除。本任务没有新组织一次独立科学审查，没有编造签字、审批编号或个人身份，也不修改旧ACCEPTANCE、状态机或任何状态代码。

## 原始证据保护

当前索引提交为 c75f364bf32e6fc63be6a7080d4f21bc6d75ec55；科学执行提交仍为 fa42557fd4ee453a27b38ab3644000830246ac42。原H1 SHA256清单登记的40个文件均逐项核验，原清单自身亦保持不变；45项科学源码匹配正式批准记录。RAW_MEASUREMENT_AUDIT.json使用独占创建；其创建前目录文件列表已写入该索引。所有本轮新文件均独占创建，不覆盖、删除或合并既有文件。

## 测量索引与可追溯性

新增RAW_MEASUREMENT_AUDIT.json以静态JSON证据关联原始branch/target/robot/tick、融合stream/frame/team及保存的服务段，以及原H1 MODEL来源身份。每项机制均列出真实源码/测试的类与函数、起止行号、提交和SHA256，不只给出文件名。原执行版本与当前索引版本由45项源码相同的指纹相互关联。

本次正式H1记录为：KEEP原始请求66、新生成66、复用0、冲突0、历史命中0、融合33；SWITCH分别76、76、0、0、0、38。不得据此声称实际发生过缓存复用或冲突拒绝。D60过去的合法ACTUAL slots作为历史来源单列，未改标为新的MODEL样本。

同键复用、不同上下文拒绝、历史slot引用、跨分支隔离和错误身份拒绝均指向已归档测试结果及具体函数；本轮未重跑。特别限定：test_raw_identity_matrix中的stream循环标签未传入query，只证明缓存接口的重复请求行为；历史事务测试使用融合替身。实际服务段/流切换后同tick真实融合的端到端缓存复用验证为NOT_VERIFIED，不能由这些单元测试冒充。历史继承fixture为MISSING，并非新增VALID继承实验；缓存隔离测试也不等于对所有pending/融合污染或错误流注入都有专项结果。这些是已接受H1之外的证据范围限制，不增加本轮实验或重新开展G3设计审查。

索引要求的证据类型、源码与测试定位均已补齐；不把文件存在当作机制通过，不把历史测试当作本次H1观察。

## 仅归档既有科学数值与成本

原结果原样引用：
KEEP=-0.3150141073101529；
SWITCH=-0.144065068155969；
SWITCH−KEEP=+0.17094903915418388。

MODEL观测WLS为KEEP33、SWITCH38，共71；
MODEL策略WLS为590、594，共1184；
分支总数623、632，共1255。
ACTUAL WLS和ACTUAL STEP均为0。
KEEP结束累计计数与SWITCH开始计数相同，共享Budget连续。watchdog和独立复核原账本均以文件及SHA关联，不重新计算结果或调用资源核验代码。

## 科研解释与停止

这一验收只证明原冻结H1下合法MODEL成对评价链路成立。它不证明STFBS-Lite核心算法完整、自主MEMBER_CHANGE有效、SWITCH一般统计优势、ACTUAL收益提升、真实机器人闭环或独立TEST完成。正差额仅属于原H1 MODEL条件世界。

原实验、审计失败记录及后续只读复核均完整保留。本轮仅读取、解析JSON、定位AST、比对SHA与追加记录；未导入项目科学模块，未运行测试、H1、WLS、MODEL推进或ACTUAL STEP。没有发现需要撤销本次用户已认可限定验收的新实质性科学阻断；上述非端到端历史测试范围明确保留为限制。

ADDITIONAL_SHA256.json仅登记本轮新增文件，原SHA256.json绝不更新。收尾完成后立即停止，等待独立归档验收，不启动D1-B-QM-0，不提交或推送。
'''
# Every final scientific source and original artifact must still match before committing new records.
assert all(sha(ROOT/p)==s for p,s in original_index.items())
assert all(sha(ROOT/p)==s for p,s in approval['source_pins'].items())
assert not any(n.startswith(('research.','pursuit_v2.','numpy','scipy')) for n in sys.modules)
write(raw_target,audit_payload)
write(CLOSE/'FINAL_RESEARCH_DECISION.json',decision)
with (CLOSE/'FINAL_REPORT.md').open('x',encoding='utf-8') as f:f.write(report)
new_paths=[raw_target,CLOSE/'FINAL_RESEARCH_DECISION.json',CLOSE/'FINAL_REPORT.md',Path(__file__).resolve()]
write(CLOSE/'ADDITIONAL_SHA256.json',{p.relative_to(ROOT).as_posix():sha(p) for p in new_paths})
assert sha(OUT/'SHA256.json')==original_index_sha
assert all(sha(ROOT/p)==s for p,s in original_index.items())
print('D1_A_FINAL_CLOSEOUT_READY_FOR_REVIEW')
print('Original40/source45 unchanged; static append-only closeout; no new experiment/tests/WLS.')
print('ADDITIONAL_SHA256.json SHA256:',sha(CLOSE/'ADDITIONAL_SHA256.json'))
