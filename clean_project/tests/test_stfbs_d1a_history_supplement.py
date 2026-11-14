from unittest import TestCase
from unittest.mock import patch
from copy import deepcopy
from tests import test_stfbs_d1a_history_repair as fixtures
from research.non_oracle.stfbs_d1a_model import Branch
from research.non_oracle.stfbs_d1a_history_audit import audit_branch,model_segment_id
from research.non_oracle.stfbs_d1a_replay import digest

def setup():
    with patch.object(Branch,'fuse',fixtures.fake_fuse):
        b=fixtures.branch();b.assign(fixtures.switch())
    b.world['motion'][0]['position']=[20.,10.];return b

class SupplementTests(TestCase):
    def test_P0_boundaries_and_stale_final(self):
        for when in (3.,3.025,3.05):
            b=setup();b.world['motion'][0]['position']=[20.-.4*(when-3.),10.];b.world['motion'][0]['velocity']=[.4,0.];b.tick=61
            b.finish(0,'escaped',when,processed_tick=61)
            self.assertEqual(b.histories[0]['cutoff_tick'],61)
            self.assertEqual(b.histories[1]['cutoff_tick'],60)
            with self.assertRaises(ValueError):b.seal_history_cut()
            b.segment(1)['latest_endpoint']=fixtures.fake_fuse(b,1,b.segment(1),61)
            b.segment(1)['latest_clock']['intervals']=1
            b.seal_history_cut();audit_branch(b,b._audit_context)
            self.assertEqual(b.segment(1)['latest_clock']['intervals'],1)
    def test_P0_orders_both_terminal_and_mixed(self):
        summaries={False:[],True:[]}
        for reverse in (False,True):
            for both in (False,True):
                b=setup();b.tick=61;b.world['motion'][1]['position']=[20.,10.]
                def settle_other():
                    if both:b.finish(1,'escaped',3.,processed_tick=61)
                    else:
                        b.segment(1)['latest_endpoint']=fixtures.fake_fuse(b,1,b.segment(1),61)
                        b.segment(1)['latest_clock']['intervals']=1
                if reverse:settle_other()
                b.finish(0,'escaped',3.,processed_tick=61)
                if not reverse:settle_other()
                b.seal_history_cut();audit_branch(b,b._audit_context)
                semantic_events=[]
                for h in b.histories.values():
                    for e in h['events']:
                        value=deepcopy(e);value.pop('event_index');semantic_events.append(value)
                summaries[both].append(dict(status=deepcopy(b.status),actions=deepcopy(b.actions),components=deepcopy(b.components),events=sorted(semantic_events,key=lambda e:(e['target_id'],e['at']['time_seconds'],e['kind']))))
        self.assertEqual(summaries[False][0],summaries[False][1]);self.assertEqual(summaries[True][0],summaries[True][1])
        b=setup();b.tick=61;b.targets[1]['service_duration']=.05;b.segment(1)['latest_clock'].update(base=.05,intervals=0)
        b.segment(1)['latest_endpoint']=fixtures.fake_fuse(b,1,b.segment(1),61)
        b.finish(0,'escaped',3.,61);b.finish(1,'completed',3.05,61);b.seal_history_cut();audit_branch(b)
    def test_P0_episode_and_atomic_failure(self):
        b=setup();b.tick=120
        b.finish(0,'unfinished',6.,120);b.finish(1,'unfinished',6.,120);b.seal_history_cut();audit_branch(b)
        b=setup();b.tick=61;before=fixtures.snapshot(b)
        def fail(staged):raise RuntimeError('terminal preparation injected')
        with self.assertRaises(RuntimeError):b.finish(0,'escaped',3.,61,prepare_fault=fail)
        self.assertEqual(before,fixtures.snapshot(b))
    def test_P1_full_relabel_and_prefix_tamper(self):
        b=setup();context=b._audit_context;b.name='SWITCH'
        for h in b.histories.values():
            for e in h['events']:
                if e.get('observation_origin')=='MODEL':e['model_branch_id']='SWITCH'
            for s in h['segments']:
                for e in s['events']:
                    if e.get('observation_origin')=='MODEL':e['model_branch_id']='SWITCH'
                if s.get('contract_id')=='D1A_MODEL_SERVICE_SEGMENT_V1':
                    old=s['segment_id'];s['model_branch_id']='SWITCH';s['segment_id']=model_segment_id(s)
                    if h['active_segment_id']==old:h['active_segment_id']=s['segment_id']
                    for e in h['events']+s['events']:
                        if e.get('segment_id')==old:e['segment_id']=s['segment_id']
                if s['latest_endpoint'].get('observation_origin')=='MODEL':s['latest_endpoint']['branch']='SWITCH'
                s.pop('segment_history_digest',None);s['segment_history_digest']=digest(s)
            h.pop('history_digest',None);h['history_digest']=digest(h)
        with self.assertRaises(ValueError):audit_branch(b,context)
        b=setup();context=b._audit_context;b.histories[0]['events'][0]['kind']='SPOOF'
        for h in b.histories.values():
            h.pop('history_digest',None);h['history_digest']=digest(h)
        with self.assertRaises(ValueError):audit_branch(b,context)
    def test_P1_individual_sources(self):
        for kind in ('event_branch','event_actual','segment_branch','segment_actual','endpoint_branch','endpoint_actual','prefix'):
            b=setup();context=b._audit_context;h=b.histories[1];s=b.segment(1)
            if kind=='event_branch':h['events'][-1]['model_branch_id']='OTHER'
            if kind=='event_actual':h['events'][-1]['observation_origin']='ACTUAL'
            if kind=='segment_branch':s['model_branch_id']='OTHER'
            if kind=='segment_actual':s['observation_origin']='ACTUAL'
            if kind=='endpoint_branch':s['latest_endpoint']['branch']='OTHER'
            if kind=='endpoint_actual':s['latest_endpoint']['observation_origin']='ACTUAL'
            if kind=='prefix':b.histories[0]['segments'][0]['start_tick']=1
            with self.assertRaises(ValueError):audit_branch(b,context)
        audit_branch(setup())
