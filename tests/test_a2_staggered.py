import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from research.non_oracle.a2_analysis import decision_evidence
from research.non_oracle.environment import StaggeredEnvironment
from research.non_oracle.policy import decide, evaluate
from scripts.run_a1 import Sensing

ROOT = Path(__file__).resolve().parents[1]

def actions(target, robots=(0, 1), roles=('dual_neg45', 'dual_pos45')):
    result = [dict(target=None, role='none') for _ in range(3)]
    for robot, role in zip(robots, roles):
        result[robot] = dict(target=target, role=role)
    return result

class A2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = json.loads((ROOT/'configs/a2_two_target_staggered_min.json').read_text())
        cls.ann = json.loads((ROOT/'configs/a2_public_announcements.json').read_text())['announcements']
        cls.prefix = cls.build(cls.world)
        cls.views = []
        for tick in (0, 20, 40):
            cls.views.append(cls.prefix.prepare_decision())
            result = cls.step(cls.prefix, actions(0))
            assert result['status'] == 'COMMITTED'
        assert cls.prefix.tick == 60 and not cls.prefix.done

    @classmethod
    def build(cls, world):
        return StaggeredEnvironment(copy.deepcopy(world), Sensing(), 'A2_TEST', cls.ann)

    @staticmethod
    def step(env, choice):
        return env.step(choice, env.observe_public()['checkpoint_id'], env.tick, f'test_{env.tick}')

    def at_birth(self):
        env = copy.deepcopy(self.prefix)
        return env, env.prepare_decision()

    def test_birth_and_hidden_observations(self):
        for view in self.views:
            self.assertEqual([t['id'] for t in view['targets']], [0])
            self.assertEqual(set(view['beliefs']), {0})
            self.assertTrue(all(s['slot_key']['target_id']==0 for s in view['current_slots']))
        self.assertTrue(all(f['frame']['target_id']==0 for f in self.prefix.fusions))
        env, view = self.at_birth()
        self.assertEqual([t['id'] for t in view['targets']], [0, 1])
        self.assertEqual(view['beliefs'][1]['status'], 'PRIOR_ONLY')
        self.assertIsNone(view['beliefs'][1]['last_observation_tick'])
        self.assertEqual(view['beliefs'][1]['estimate_tick'], 60)

    def test_unannounced_assignment_rejected(self):
        env = self.build(self.world)
        env.prepare_decision()
        self.assertEqual(self.step(env, actions(1))['status'], 'REJECTED')

    def test_invalid_announcement(self):
        ann = copy.deepcopy(self.ann)
        ann[1]['announcement_tick'] = 40
        with self.assertRaisesRegex(ValueError, 'coincide'):
            StaggeredEnvironment(self.world, Sensing(), 'BAD', ann)

    def test_truth_isolation_before_and_after_birth(self):
        world = copy.deepcopy(self.world)
        world['targets'][1]['position_at_birth'] = [12., 11.]
        other = self.build(world)
        for original in self.views:
            self.assertEqual(other.prepare_decision(), original)
            self.step(other, actions(0))
        _, baseline = self.at_birth()
        changed = other.prepare_decision()
        self.assertEqual(baseline, changed)
        baseline['end_tick'] = changed['end_tick'] = 61
        self.assertEqual(decide(baseline), decide(changed))

    def test_cross_target_change_and_no_backfill(self):
        env, view = self.at_birth()
        result = self.step(env, actions(1))
        commit = result['action_commit']; transitions = commit['transitions']
        self.assertEqual([x['kind'] for x in transitions], ['WITHDRAW', 'FIRST_ASSIGNMENT'])
        self.assertEqual(commit['assignment_change_count'], 2)
        self.assertAlmostEqual(commit['change_cost'], .02)
        self.assertEqual(result['frames'][0]['progress']['1'], 0.)
        self.assertTrue(any(x['target_id']==1 and x['measurement_tick']==60 for x in env.beliefs.pending))
        self.assertEqual(view['beliefs'][1]['status'], 'PRIOR_ONLY')
        env.prepare_decision()
        self.assertTrue(any(x['target_id']==1 and x['measurement_tick']==60 and x['consumed_tick']==80 for x in env.beliefs.consumed))

    def test_team_and_role_resets(self):
        for label, choice in [('MEMBER_CHANGE', actions(0,(0,2))), ('ROLE_CHANGE', actions(0,roles=('dual_pos45','dual_neg45')))]:
            with self.subTest(label=label):
                env, _ = self.at_birth(); result = self.step(env, choice)
                t = result['action_commit']['transitions'][0]
                self.assertEqual(t['kind'], label)
                self.assertEqual(t['clock_after']['intervals'], 0)
                self.assertEqual(t['clock_after']['base'], 0.)

    def test_keep_prediction_and_natural_release(self):
        env, view = self.at_birth(); original = copy.deepcopy(view)
        view['end_tick'] = 61
        key = dict(target=0, robots=[0,1], roles=['dual_neg45','dual_pos45'])
        with patch('research.non_oracle.policy.endpoint', return_value=(False,'PASS')):
            row = evaluate(view, key)
        self.assertTrue(row['kept_history']); self.assertEqual(row['frames'][0]['progress'], 0.)
        self.assertEqual(view['histories'], original['histories'])
        result = self.step(env, actions(0)); self.assertEqual(result['action_commit']['transitions'][0]['kind'], 'KEEP')
        self.assertEqual(result['action_commit']['change_cost'], 0.)
        archive = env.private_snapshot()['state']['archives']['0']
        self.assertEqual(archive['release_change_cost'], 0.)
        self.assertEqual([t['id'] for t in env.prepare_decision()['targets']], [1])

    def test_modes_candidate_coverage_and_plan_evidence(self):
        env, born = self.at_birth()
        for view, count, legal in [(copy.deepcopy(self.views[0]),6,7),(born,12,13)]:
            view['end_tick'] = view['tick']+1
            a=decide(view,'R'); b=decide(view,'S_NEW')
            self.assertEqual(a,b); self.assertEqual(len(a['rows']),count)
            evidence=decision_evidence(view,a,env.beliefs.accepted_receipts)
            self.assertEqual(evidence['legal_plan_count'],legal)
            prior=evidence['targets'][-1];self.assertIsNone(prior['observation_age_ticks'])
            self.assertEqual(prior['announcement_age_ticks'],0)
            if count==12:
                observed=evidence['targets'][0]
                self.assertEqual(observed['corresponding_consumed_tick'],60)
                self.assertEqual(observed['observation_age_ticks'],0)

    def test_cache_cannot_cross_birth(self):
        _, after=self.at_birth()
        before=copy.deepcopy(self.views[0]);cache={}
        key=dict(target=0,robots=[0,1],roles=['dual_neg45','dual_pos45'])
        before['end_tick']=1;after['end_tick']=61
        evaluate(before,key,cache);old=set(cache)
        self.assertEqual(evaluate(after,key,cache),evaluate(after,key))
        self.assertTrue(set(cache)-old)
        self.assertTrue({k[0] for k in old}.isdisjoint({k[0] for k in set(cache)-old}))

    def test_rejected_duplicate_does_not_change_observation_provenance(self):
        env, view = self.at_birth()
        receipt = env.beliefs.accepted_receipts[0].copy()
        tick = receipt['measurement_tick']
        env.beliefs.enqueue(dict(source='ACTUAL', target_id=0, measurement_tick=tick,
                                 available_tick=tick, estimate=view['beliefs'][0]['diagnostics']))
        env.beliefs.freeze(80)
        self.assertEqual(env.beliefs.consumed[-1]['consumed_tick'], 80)
        self.assertEqual(env.beliefs.accepted_receipts[0], receipt)

if __name__=='__main__': unittest.main()
