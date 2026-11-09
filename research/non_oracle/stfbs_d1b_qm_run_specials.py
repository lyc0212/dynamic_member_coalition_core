"""F2/F3 fixed-source inheritance streams, without new sensor sampling."""
from copy import deepcopy
from dataclasses import dataclass
import json
from .stfbs_d1a_replay import digest
from .stfbs_d1a_state import ModelRawCache
from .stfbs_d1b_qm_run_evidence import read_verified_source,independent_gq
from .stfbs_d1b_qm_model import changed_team

LABEL='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'
SPECS={'QM_F2_VALID_HISTORY':('QM_B1_MEMBER_CHANGE','LEFT',(0,2)),
       'QM_F3_STREAM_A':('QM_B0_KEEP','RIGHT',(0,1)),
       'QM_F3_STREAM_B':('QM_B1_MEMBER_CHANGE','LEFT',(0,2))}
_SLOT_SEAL=object()

@dataclass(frozen=True)
class VerifiedSlots:
    special_id: str
    source_json: str
    slots_json: str
    evidence_kind: str
    seal: object

def verify_special_source(special_id,source,*,test=False):
    if special_id not in SPECS:raise ValueError('Unregistered special identity')
    expected,side,robots=SPECS[special_id]
    reason='F2_SOURCE_NOT_AVAILABLE' if special_id=='QM_F2_VALID_HISTORY' else 'F3_SOURCE_NOT_AVAILABLE'
    if source.branch_id!=expected:raise ValueError(reason+': fixed branch mismatch')
    payload,result,records=read_verified_source(source,test=test)
    team=[dict(robot_id=i,role='dual_neg45' if i==0 else 'dual_pos45') for i in robots]
    segments=[s for s in records['histories'][0]['segments'] if s['team']==team and (s['start_tick']==80 if side=='LEFT' else s['start_tick']<80)]
    rows=[f for f in records['feedback'] if f['endpoint']['tick']==80 and f['endpoint']['team']==team]
    if len(segments)!=1 or len(rows)!=1:raise ValueError(reason+': required endpoint/segment missing')
    segment=segments[0];row=rows[0]
    if side=='LEFT':
        boundaries=[b for b in result['boundaries'] if b['tick']==80 and b['after']==changed_team()]
        events=records['histories'][0]['events']
        if len(boundaries)!=1 or not any(e['kind']=='TEAM_CHANGED' and e['at']['event_tick']==80 for e in events) or segment['start_tick']!=80:raise ValueError(reason+': member change not committed')
    audit=independent_gq(row['endpoint'],records,result['world'],result['view']['config'],source.registration,segment_id=segment['segment_id'],side=side)
    slots=[]
    for i in robots:
        key=(expected,0,i,80)
        if key not in records['cache']:raise ValueError(reason+': raw source key')
        raw=records['cache'][key];slot=raw['slot']
        if slot['state']!='VALID' or slot['packet'] is None or slot['packet']['measurement_tick']!=80:raise ValueError(reason+': VALID source required')
        context=dict(position=records['positions'][80][i],sigma=records['physical_profiles'][80][i]['sigma'],health=records['physical_profiles'][80][i]['health'])
        if raw['context_digest']!=digest(context):raise ValueError(reason+': source context mismatch')
        slots.append(dict(slot=deepcopy(slot),context_digest=raw['context_digest'],context=context))
    link=dict(source_run_identity=source.batch_id,source_branch=source.branch_id,source_file=source.path,source_file_sha256=source.file_sha256,
              target_id=0,measurement_tick=80,robots=list(robots),segment_id=segment['segment_id'],frame_id=row['frame']['frame_id'],external_audit=audit,
              source_verification='BEFORE_HISTORY_CACHE_INITIALIZATION',special_id=special_id)
    return VerifiedSlots(special_id,json.dumps(link,sort_keys=True),json.dumps(slots,sort_keys=True),source.evidence_kind,_SLOT_SEAL)

def inherited_cache(bundle,*,test=False):
    if type(bundle) is not VerifiedSlots or bundle.seal is not _SLOT_SEAL:raise ValueError('Verified source required before cache')
    if bundle.evidence_kind==LABEL:
        if not test:raise PermissionError('Test slots cannot enter real special')
    else:
        from .stfbs_d1b_qm_run_release import require_run_g1
        require_run_g1()
    rows=json.loads(bundle.slots_json)
    return ModelRawCache(bundle.special_id,[dict(slot=x['slot'],context_digest=x['context_digest']) for x in rows])

def special_frame(bundle,cache):
    if cache.branch!=bundle.special_id:raise ValueError('Special cache branch mismatch')
    stream=bundle.special_id+':T0:inherited80';records=[]
    def no_producer():raise RuntimeError('Inherited VALID slot must not be sampled')
    for item in json.loads(bundle.slots_json):
        i=item['slot']['slot_key']['robot_id']
        slot=cache.query(bundle.special_id,0,i,80,item['context'],no_producer)
        if slot!=item['slot']:raise ValueError('Inherited measurement changed')
        packet=deepcopy(slot['packet']);packet['packet_id']=stream+':tick80:U'+str(i);records.append(packet)
    return dict(contract_id='STAGE2A5B-A-MINIMAL-v0.2',stream_id=stream,frame_id=stream+':tick80',target_id=0,tick=80,measurement_time=4.,available_time=4.,records=records)

def validate_special_frame(frame,special_id,bundle=None):
    if special_id not in SPECS or frame['stream_id']!=special_id+':T0:inherited80' or frame['frame_id']!=frame['stream_id']+':tick80':raise ValueError('Special frame identity mismatch')
    if frame['target_id']!=0 or frame['tick']!=80:raise ValueError('Special frame target/tick mismatch')
    expected=['U'+str(i) for i in SPECS[special_id][2]]
    if [r['sensor_id'] for r in frame['records']]!=expected or any(r['packet_id']!=frame['stream_id']+':tick80:'+r['sensor_id'] for r in frame['records']):raise ValueError('Special packet identity mismatch')
    if bundle is not None:
        if bundle.special_id!=special_id:raise ValueError('Special source identity mismatch')
        for item,record in zip(json.loads(bundle.slots_json),frame['records']):
            packet=dict(record);packet.pop('packet_id')
            if packet!=item['slot']['packet']:raise ValueError('Special packet differs from verified raw source')

def run_special(special_id,source,budget,*,test_processor_factory=None):
    test=test_processor_factory is not None
    if test:
        if getattr(test_processor_factory,'evidence_kind',None)!=LABEL or budget.real_ready:raise PermissionError('Invalid special double')
    else:
        from .stfbs_d1b_qm_run_release import require_run_g1
        require_run_g1()
        if not budget.real_ready:raise PermissionError('Real special requires shared real budget')
    # Source verification precedes cache construction, not the other way around.
    bundle=verify_special_source(special_id,source,test=test);cache=inherited_cache(bundle,test=test);frame=special_frame(bundle,cache)
    validate_special_frame(frame,special_id,bundle)
    factory=test_processor_factory
    if factory is None:
        from research.information_service_bridge.public_stream import BridgeFrameProcessor
        factory=BridgeFrameProcessor
    before=budget.snapshot()['total']
    with budget.for_branch(special_id),budget.for_frame(frame['frame_id']):
        processor=factory([r['sensor_id'] for r in frame['records']],80,frame['stream_id'],0,estimator_fn=budget.estimator('MODEL_SPECIAL_TEST_WLS'))
        result=processor.process(frame)
    if budget.snapshot()['total']-before!=1 or not result['estimator_called']:raise ValueError('Special must consume exactly one outer WLS')
    return dict(special_id=special_id,source=json.loads(bundle.source_json),frame=frame,result=result,raw_counts=cache.counts,source_slots=json.loads(bundle.slots_json),
                budget_ledger_id=budget.ledger_id,evidence_kind=LABEL if test else 'MODEL')

def validate_pending_identity(row,special_id):
    if row['branch_id']!=special_id or row['target_id']!=0 or row['stream_id']!=special_id+':T0:inherited80':raise ValueError('Special pending identity mismatch')
    return True
