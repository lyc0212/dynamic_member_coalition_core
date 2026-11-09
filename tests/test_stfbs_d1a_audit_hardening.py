from unittest import TestCase
from unittest.mock import patch
from copy import deepcopy
from research.non_oracle.stfbs_d1a_audit_registration import verified_registration
from research.non_oracle.stfbs_d1a_model import Branch,Budget,nominal_world
from research.non_oracle.stfbs_d1a_history_audit import audit_branch_independent,audit_histories,register_context,model_segment_id
from research.non_oracle.stfbs_d1a_replay import digest
from tests.test_stfbs_d1a_history_repair import fake_fuse

EVIDENCE=[]
def fixture():
    v,s,contexts,manifest=verified_registration()  # Before Branch construction.
    b=Branch(v,s,nominal_world(v),'KEEP',Budget())
    with patch.object(Branch,'fuse',fake_fuse):
        b.assign(deepcopy(v['assignment']))
        b.tick=80
        for h in b.histories.values():h['cutoff_tick']=80
        b.segment(0)['latest_endpoint']=fake_fuse(b,0,b.segment(0),80)
        a=deepcopy(b.actions);a[0]['role'],a[1]['role']=a[1]['role'],a[0]['role'];b.assign(a)
    context=contexts['KEEP'];audit_branch_independent(b,context=context)
    prefix={int(k):h for k,h in __import__('json').loads(context.prefix_json).items()}
    events=[e for j,h in b.histories.items() for e in h['events'][len(prefix[j]['events']):]]
    segments=[s for j,h in b.histories.items() for s in h['segments'][len(prefix[j]['segments']):]]
    endpoints=[s['latest_endpoint'] for h in b.histories.values() for s in h['segments'] if s['latest_endpoint'].get('observation_origin')=='MODEL']
    assert events and segments and endpoints
    EVIDENCE.append(dict(case='NONEMPTY_BASELINE',events=deepcopy(events),segments=deepcopy(segments),endpoints=deepcopy(endpoints),source=manifest))
    return b,context

def expect_failure(test,b,ctx,name,mutate,pattern):
    bad=b._transaction_clone();mutate(bad)
    try:audit_branch_independent(bad,context=ctx)
    except ValueError as e:
        test.assertRegex(str(e),pattern);EVIDENCE.append(dict(case=name,reason=str(e),pattern=pattern,context_supplied=True))
    else:test.fail('Tamper accepted: '+name)

class HardeningTests(TestCase):
    def test_source_and_nonempty(self):
        b,c=fixture();self.assertEqual(audit_branch_independent(b,context=c)['status'],'PASS')
        with self.assertRaises(TypeError):audit_branch_independent(b)
        with self.assertRaisesRegex(ValueError,'External trusted'):audit_branch_independent(b,context=None)
    def test_old_false_positive(self):
        b,c=fixture();h=deepcopy(b.histories)
        for label in ('legal_without_context','tampered_without_context'):
            if label.startswith('tampered'):h[0]['segments'][-1]['events'].clear()
            with self.assertRaisesRegex(ValueError,'External trusted audit context required') as caught:
                audit_histories(h,b.actions,b.status,b.tick)
            EVIDENCE.append(dict(case=label,reason=str(caught.exception),semantic_test=False))
    def test_separate_record_identity(self):
        b,c=fixture()
        expect_failure(self,b,c,'ID-EVENT',lambda x:x.histories[0]['events'][-1].update(model_branch_id='SWITCH'),'Untrusted new event identity')
        expect_failure(self,b,c,'ID-SEGMENT',lambda x:x.segment(0).update(model_branch_id='SWITCH'),'Untrusted new segment identity')
        expect_failure(self,b,c,'ID-ENDPOINT',lambda x:x.segment(0)['latest_endpoint'].update(branch='SWITCH'),'Untrusted endpoint identity')
    def test_full_relabel_and_internal_context(self):
        b,c=fixture()
        def relabel(x):
            x.name='SWITCH';x._audit_context=register_context('SWITCH',x.histories)
            for h in x.histories.values():
                mapping={}
                for s in h['segments']:
                    if s.get('contract_id')=='D1A_MODEL_SERVICE_SEGMENT_V1':
                        old=s['segment_id'];s['model_branch_id']='SWITCH';s['segment_id']=model_segment_id(s);mapping[old]=s['segment_id']
                    if s['latest_endpoint'].get('observation_origin')=='MODEL':s['latest_endpoint']['branch']='SWITCH'
                h['active_segment_id']=mapping.get(h['active_segment_id'],h['active_segment_id'])
                for s in h['segments']:
                    s['previous_segment_id']=mapping.get(s['previous_segment_id'],s['previous_segment_id'])
                    for e in s['events']:
                        if e.get('observation_origin')=='MODEL':e['model_branch_id']='SWITCH'
                        e['segment_id']=mapping.get(e.get('segment_id'),e.get('segment_id'))
                    s.pop('segment_history_digest',None);s['segment_history_digest']=digest(s)
                for e in h['events']:
                    if e.get('observation_origin')=='MODEL':e['model_branch_id']='SWITCH'
                    e['segment_id']=mapping.get(e.get('segment_id'),e.get('segment_id'))
                h.pop('history_digest',None);h['history_digest']=digest(h)
        expect_failure(self,b,c,'FULL_RELABEL',relabel,'Trusted branch mismatch')
        def replace_context(x):
            x._audit_context=register_context('KEEP',x.histories)
            x.histories[0]['events'][0]['kind']='SPOOF'
            x._audit_context=register_context('KEEP',x.histories)
        expect_failure(self,b,c,'INTERNAL_CONTEXT_REPLACED',replace_context,'D60 event prefix modified')
    def test_semantic_negatives(self):
        b,c=fixture()
        with patch.object(Branch,'fuse',fake_fuse):
            b.tick=100
            for h in b.histories.values():h['cutoff_tick']=100
            b.segment(0)['latest_endpoint']=fake_fuse(b,0,b.segment(0),100)
            b.assign([dict(target=None,role='none')]*3)
        # Preset a complete unassigned state one interval later, without motion
        # execution. This makes deletion/overlap a positive-duration defect.
        b.tick=101
        for h in b.histories.values():h['cutoff_tick']=101
        audit_branch_independent(b,context=c)
        cases=[
            ('PREFIX',lambda x:x.histories[0]['events'][0].update(kind='SPOOF'),'D60 event prefix modified'),
            ('COVERAGE_GAP',lambda x:x.histories[0]['unassigned_intervals'].pop(),'History incomplete coverage'),
            ('MUTEX',lambda x:x.histories[0]['segments'][-1].update(closure=None),'Current state not unique|History coverage overlap/gap'),
            ('EVENT_INDEX',lambda x:x.histories[0]['events'][-1].update(event_index=999),'Segment event reference|Missing segment event link'),
            ('EVENT_REFERENCE',lambda x:x.histories[0]['unassigned_intervals'][-1].update(opening_event_index=999),'Gap opening reference/time'),
            ('SEGMENT_ID',lambda x:x.histories[0]['segments'][-1].update(segment_id='bad'),'MODEL segment identity'),
            ('PREDECESSOR',lambda x:x.histories[0]['segments'][-1].update(previous_segment_id='bad'),'Segment predecessor/order'),
            ('CLOSE_TIME',lambda x:x.histories[0]['segments'][-1]['closure'].update(at=dict(time_seconds=4.,event_tick=80)),'Closure event/time'),
            ('CLOSE_REASON',lambda x:x.histories[0]['segments'][-1]['closure'].update(reason='ESCAPED'),'Closure event reason'),
            ('ACTUAL_SPOOF',lambda x:x.histories[0]['events'][-1].update(observation_origin='ACTUAL'),'Untrusted new event identity')]
        for name,change,reason in cases:expect_failure(self,b,c,name,change,reason)
