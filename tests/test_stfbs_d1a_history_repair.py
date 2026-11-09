from copy import deepcopy
from unittest import TestCase
from unittest.mock import patch
from pathlib import Path
import pickle
from research.non_oracle.stfbs_d1a_replay import recover,read
from research.non_oracle.stfbs_d1a_model import Branch,Budget,nominal_world
from research.non_oracle.stfbs_d1a_history_audit import audit_histories,audit_branch

def fake_fuse(self,j,s,tick):
    self.fusions+=1
    self.cache.counts['new']+=1
    self.consumer.pending.append(dict(artificial=True))
    return dict(tick=tick,target_id=j,team=deepcopy(s['team']),branch=self.name,G=True,quality=dict(status='PASS'),provenance='SIMULATED',observation_origin='MODEL')

def branch():
    v,s,_=recover('runs/a2_switch_episode_001');return Branch(v,s,nominal_world(v),'REPAIR_TEST',Budget())

def switch():return [dict(target=1,role='dual_neg45'),dict(target=1,role='dual_pos45'),dict(target=None,role='none')]

def snapshot(b):
    return pickle.dumps({k:v for k,v in b.__dict__.items() if k!='budget'})

class HistoryRepairTests(TestCase):
    def test_keep_switch_withdraw_unassigned(self):
        with patch.object(Branch,'fuse',fake_fuse):
            b=branch();before=deepcopy(b.segment(0));b.assign(deepcopy(b.actions))
            self.assertEqual(b.segment(0)['latest_clock'],before['latest_clock']);self.assertEqual(b.fusions,0)
            b.assign(switch());b._history_check();self.assertIsNone(b.segment(0));self.assertIsNotNone(b.segment(1))
            self.assertEqual(b.histories[1]['unassigned_intervals'][-1]['end_at']['time_seconds'],3.)
            b.assign([dict(target=None,role='none')]*3);b._history_check()
            count=len(b.histories[1]['segments']);b.assign(deepcopy(b.actions));self.assertEqual(count,len(b.histories[1]['segments']))
    def test_atomic_validation_and_prepare_failures(self):
        with patch.object(Branch,'fuse',fake_fuse):
            b=branch();before=snapshot(b)
            with self.assertRaises(ValueError):b.assign([dict(target=1,role='bad')]*3)
            self.assertEqual(snapshot(b),before)
            for phase in ('before_prepare','after_fusion','before_commit'):
                def fail(staged,at):
                    if at==phase:raise RuntimeError('injected')
                with self.assertRaises(RuntimeError):b.assign(switch(),prepare_fault=fail)
                self.assertEqual(snapshot(b),before)
            def paid_failure(staged,at):
                if at=='after_fusion':
                    staged.budget.counts['MODEL_OBSERVATION_WLS']+=1  # Artificial cost-ledger token, no estimator.
                    raise RuntimeError('injected after simulated compute')
            with self.assertRaises(RuntimeError):b.assign(switch(),prepare_fault=paid_failure)
            self.assertEqual(snapshot(b),before)
            self.assertEqual(b.budget.counts['MODEL_OBSERVATION_WLS'],1)
    def test_member_role_and_cut_boundaries(self):
        with patch.object(Branch,'fuse',fake_fuse):
            b=branch()
            for tick in (60,80,100):
                b.tick=tick
                for h in b.histories.values():h['cutoff_tick']=tick
                if b.segment(0):b.segment(0)['latest_endpoint']=fake_fuse(b,0,b.segment(0),tick)
                actions=[dict(target=0,role='dual_pos45'),dict(target=0,role='dual_neg45'),dict(target=None,role='none')]
                b.assign(actions);b._history_check()
            b.assign([dict(target=None,role='none'),dict(target=0,role='dual_neg45'),dict(target=0,role='dual_pos45')]);b._history_check()
    def test_terminal_transitions_and_no_fees(self):
        for status in ('completed','escaped','unfinished'):
            b=branch();b.tick=120 if status=='unfinished' else 60;fees=b.change_cost
            if status=='completed':b.segment(0)['latest_clock'].update(base=b.targets[0]['service_duration'],intervals=0)
            if status=='escaped':b.world['motion'][0]['position'][0]=20.
            b.finish(0,status,b.tick*.05);self.assertEqual(fees,b.change_cost)
            if status=='unfinished':b.finish(1,'unfinished',6.)
            b.seal_history_cut()
            audit_branch(b)
            b.change_cost+=.01
            with self.assertRaises(ValueError):audit_branch(b)
            with self.assertRaises(ValueError):b.finish(0,status,b.tick*.05)
        b=branch();b.world['motion'][1]['position'][0]=20.;b.finish(1,'escaped',3.);b._history_check()
        h=deepcopy(b.histories);h[1]['unassigned_intervals'][-1].update(end_at=None,closing_event_index=None)
        with self.assertRaises(ValueError):audit_histories(h,b.actions,b.status,60,{1:3.})
    def test_invalid_terminal_is_atomic(self):
        b=branch();before=snapshot(b)
        for status in ('completed','escaped','unfinished'):
            with self.assertRaises(ValueError):b.finish(0,status,3.)
            self.assertEqual(snapshot(b),before)
    def test_fusion_failure_and_final_staging_corruption(self):
        b=branch();before=snapshot(b)
        def fail_fusion(staged,j,s,tick):
            fake_fuse(staged,j,s,tick)
            raise RuntimeError('fusion preparation failed')
        with patch.object(Branch,'fuse',fail_fusion):
            with self.assertRaises(RuntimeError):b.assign(switch())
        self.assertEqual(snapshot(b),before)
        with patch.object(Branch,'fuse',fake_fuse):
            def corrupt(staged,at):
                if at=='before_commit':staged.histories[1]['unassigned_intervals'][-1].update(end_at=None,closing_event_index=None)
            with self.assertRaises(ValueError):b.assign(switch(),prepare_fault=corrupt)
        self.assertEqual(snapshot(b),before)
    def test_artificial_history_tampering(self):
        with patch.object(Branch,'fuse',fake_fuse):
            b=branch();b.assign(switch())
            def validate(h):return audit_histories(h,b.actions,b.status,60)
            mutations=[
                lambda h:h[0]['unassigned_intervals'].clear(),
                lambda h:h[1]['unassigned_intervals'][-1].update(end_at=None,closing_event_index=None),
                lambda h:h[0]['unassigned_intervals'][-1].update(start_tick=59),
                lambda h:h[0]['unassigned_intervals'][-1].update(start_tick=61),
                lambda h:h[1]['events'][-1].update(event_index=999),
                lambda h:h[1]['unassigned_intervals'][-1].update(closing_event_index=999),
                lambda h:h[1]['segments'][-1].update(segment_id='bad'),
                lambda h:h[1]['segments'][-1].update(previous_segment_id='bad'),
                lambda h:h[1]['segments'][-1]['events'].clear(),
                lambda h:h[0]['segments'][-1]['closure'].update(at=dict(time_seconds=2.,event_tick=40)),
                lambda h:h[0]['segments'][-1]['closure'].update(reason='COMPLETED')]
            for mutate in mutations:
                h=deepcopy(b.histories);mutate(h)
                with self.assertRaises(ValueError):validate(h)
    def test_old_archives_still_fail(self):
        base=Path('reports/stfbs_lite_d1a_001');found=0
        for directory in (base/'engineering_attempt_001',base/'engineering_attempt_002',base):
            r=read(directory/'SWITCH_RAW.json')
            for d in r['decisions']:
                v=d['view'];hist={h['target_id']:h for h in v['histories']}
                with self.assertRaises(ValueError):audit_histories(hist,v['assignment'],{j:'active' for j in hist},v['tick'])
                for h in hist.values():
                    if (h['active_segment_id'] is not None)==bool([g for g in h['unassigned_intervals'] if g['end_at'] is None]):found+=1
        self.assertEqual(found,9)
