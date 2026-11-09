"""Exactly ten nonphysical tests; synthetic endpoints are not scientific evidence."""
from unittest import TestCase
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import ast,json
from research.non_oracle.stfbs_d1b_qm_scenario import build_fixture,TEST_DOUBLE
from research.non_oracle.stfbs_d1b_qm_model import initial_team,changed_team,PublicQueryRejected
from research.non_oracle.stfbs_d1b_qm_budget import D1BBudget,CATEGORIES
from research.non_oracle.stfbs_d1b_qm_execution import prepare_branch,DynamicSchedule,selector,execute_run,bind_shared_budget,validate_dynamic_endpoint
from research.non_oracle.stfbs_d1b_qm_independent_audit import active_registry,register_fixture,audit_registered,verify_registration,assert_public_surface

ROOT=Path(__file__).resolve().parents[1]
FUSIONS=[]

def fake_estimator(payload):return dict(evidence_kind=TEST_DOUBLE,payload=deepcopy(payload))
fake_estimator.evidence_kind=TEST_DOUBLE

def fake_fuse(branch,j,segment,tick):
    active_registry().note_double('transaction-owned synthetic endpoint and pending feedback; zero solver calls')
    callback=branch.budget.estimator('MODEL_OBSERVATION_WLS')  # Create only, never call.
    if callback.ledger_id!=branch.budget.ledger_id or callback.branch_id!=branch.name:raise ValueError('Wrong callback budget')
    label='LEFT'+str(tick)
    FUSIONS.append(dict(branch=branch.name,tick=tick,label=label,ledger=callback.ledger_id,team=deepcopy(segment['team'])))
    branch.consumer.enqueue(dict(target_id=j,measurement_tick=tick,available_tick=tick,estimate=None,
                                 provenance='SIMULATED',observation_origin='MODEL',evidence_kind=TEST_DOUBLE,label=label))
    return dict(tick=tick,target_id=j,team=deepcopy(segment['team']),branch=branch.name,G=True,
                quality=dict(status='PASS',evidence_kind=TEST_DOUBLE),provenance='SIMULATED',observation_origin='MODEL',evidence_kind=TEST_DOUBLE)
fake_fuse.evidence_kind=TEST_DOUBLE

def make(branch_id='QM_B0_KEEP',budget=None):
    f=build_fixture();pins=json.loads((ROOT/'reports/stfbs_lite_d1b_qm1b_eng_001/RUN_POLICY.json').read_bytes())['source_pins']
    reg=register_fixture(f,branch_id,pins)
    budget=D1BBudget() if budget is None else budget
    return prepare_branch(f,branch_id,budget,reg),reg,f

class SyntheticPort:
    evidence_kind=TEST_DOUBLE
    def __init__(self,b):
        self.b=b;self.trace=[];self.freezes=[];self.consumed_at={}
        self._sensor_authority=SimpleNamespace(publish_from_executor=lambda tick:self.publish(tick))
    def __getattr__(self,n):return getattr(self.b,n)
    def publish(self,tick):
        self.trace.append(('PUBLIC',tick));self.b._sensor_authority.publish_from_executor(tick)
    def policy_view(self):
        tick=self.b.tick
        if tick!=self.b._last_public_cut:
            self.consumed_at[tick]=[x['label'] for x in self.b.consumer.pending]
            self.freezes.append(tick);self.trace.append(('FREEZE',tick))
        return self.b.policy_view()
    def assign(self,actions):
        self.trace.append(('ASSIGN',self.b.tick));self.b.assign(actions)
    def advance(self):
        # Synthetic jump to decision cuts, never invokes Branch.advance or movement.
        b=self.b;b.tick=80 if b.tick==60 else 100
        for h in b.histories.values():h['cutoff_tick']=b.tick
        self.trace.extend([('OLD_MOTION_SYNTHETIC',b.tick),('RIGHT',b.tick),('SETTLE',b.tick)])
        profile=b._sensor_authority.physical_profile_at(b.tick)
        self.right_sigma=profile[1]['sigma']
        s=b.segment(0)
        s['latest_endpoint']=dict(tick=b.tick,target_id=0,team=deepcopy(s['team']),branch=b.name,G=True,
                                  quality=dict(status='PASS',evidence_kind=TEST_DOUBLE),provenance='SIMULATED',observation_origin='MODEL',evidence_kind=TEST_DOUBLE)
        b.consumer.enqueue(dict(target_id=0,measurement_tick=b.tick,available_tick=b.tick,estimate=None,
                                provenance='SIMULATED',observation_origin='MODEL',label='RIGHT'+str(b.tick),evidence_kind=TEST_DOUBLE))

class QM1BTests(TestCase):
    def test_execution_branch_identity_isolation(self):
        active_registry().note_double('pure independent branch state and synthetic caches/pending')
        budget=D1BBudget();a,_,_=make('QM_B0_KEEP',budget);b,_,_=make('QM_B1_MEMBER_CHANGE',budget)
        self.assertIs(a.budget,b.budget);self.assertIs(a._transaction_clone().budget,budget)
        for attr in ('consumer','streams','histories','cache','feedback'):self.assertIsNot(getattr(a,attr),getattr(b,attr))
        a.consumer.pending.append({'synthetic':TEST_DOUBLE});a.streams['synthetic']={'x':[]}
        self.assertEqual(b.consumer.pending,[]);self.assertEqual(b.streams,{})
        a.histories[0]['events'][0]['reasons'].append('synthetic');self.assertNotEqual(a.histories,b.histories)
        self.assertEqual(selector('QM_B0_KEEP'),'B0');self.assertEqual(selector('QM_B1_MEMBER_CHANGE'),'B1')
        self.assertEqual(selector('QM_B3_UNKNOWN'),'B0')
        for bad in ('QM_PROBE_OLD','QM_PROBE_DEGRADED_1'):
            with self.assertRaisesRegex(ValueError,'Probe'):selector(bad)
        with self.assertRaisesRegex(ValueError,'mismatch'):selector('QM_B1_MEMBER_CHANGE','B0')
        slot={'slot_key':dict(target_id=0,robot_id=0,tick=80),'state':'MISSING','packet':None}
        a.cache.query(a.name,0,0,80,{'synthetic':1},lambda:deepcopy(slot))
        self.assertIn((a.name,0,0,80),a.cache.rows);self.assertEqual(b.cache.rows,{})
        with self.assertRaisesRegex(ValueError,'Foreign MODEL branch'):a.cache.query(b.name,0,0,80,{},lambda:slot)

    def test_old_probe_not_used_as_dynamic_right80(self):
        old=dict(branch='QM_PROBE_OLD',tick=80,observation_origin='MODEL',evidence_kind=TEST_DOUBLE)
        for name in ('QM_B0_KEEP','QM_B1_MEMBER_CHANGE'):
            right=dict(old,branch=name);self.assertTrue(validate_dynamic_endpoint(right,name,80))
            with self.assertRaisesRegex(ValueError,'Foreign endpoint'):validate_dynamic_endpoint(old,name,80)
        probe,_,_=make('QM_PROBE_OLD');dynamic,_,_=make();self.assertIsNot(probe.cache,dynamic.cache)

    def test_tick80_event_order_with_test_doubles(self):
        start=len(FUSIONS)
        with active_registry().fake_scope('D60 assignment and D80 member-change own exactly one left endpoint',fake_fuse):
            for name in ('QM_B0_KEEP','QM_B1_MEMBER_CHANGE'):
                b,reg,_=make(name);port=SyntheticPort(b);schedule=DynamicSchedule(port,name)
                schedule.start();self.assertEqual(b.actions,initial_team());self.assertEqual(b.fusions,0)
                self.assertEqual(len([x for x in FUSIONS[start:] if x['branch']==name and x['tick']==60]),1)
                schedule.advance_one();self.assertEqual(port.right_sigma,.08)
                self.assertEqual(port.trace[:6],[('ASSIGN',60),('OLD_MOTION_SYNTHETIC',80),('RIGHT',80),('SETTLE',80),('PUBLIC',80),('FREEZE',80)])
                self.assertEqual(len([x for x in FUSIONS[start:] if x['branch']==name and x['tick']==80]),int(name=='QM_B1_MEMBER_CHANGE'))
                segments=len(b.histories[0]['segments']);self.assertEqual(segments,2 if name=='QM_B1_MEMBER_CHANGE' else 1)
                self.assertEqual(b.actions,changed_team() if name=='QM_B1_MEMBER_CHANGE' else initial_team())
                schedule.advance_one();self.assertEqual(port.freezes,[80,100]);self.assertEqual(len(b.histories[0]['segments']),segments)
                self.assertFalse(any(x['tick']==100 and x['branch']==name for x in FUSIONS[start:]))
                self.assertEqual(audit_registered(b,reg)['status'],'PASS')
                self.assertEqual(sum(b.budget.counts.values()),0)
        tree=ast.parse((ROOT/'research/non_oracle/stfbs_d1b_qm_execution.py').read_text())
        self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='fuse' for n in ast.walk(tree)))

    def test_left80_feedback_not_consumed_at_freeze80(self):
        with active_registry().fake_scope('new left80 pending remains beyond sole freeze80',fake_fuse):
            b,_,_=make('QM_B1_MEMBER_CHANGE');p=SyntheticPort(b);s=DynamicSchedule(p,b.name)
            s.start();s.advance_one()
            self.assertEqual(p.consumed_at[80],['LEFT60','RIGHT80'])
            self.assertEqual([x['label'] for x in b.consumer.pending],['LEFT80'])
            frozen=deepcopy(b.frozen);self.assertEqual(b.policy_view()['beliefs'],frozen)
            self.assertEqual([x['label'] for x in b.consumer.pending],['LEFT80'])
            self.assertEqual(b.segment(0)['start_tick'],80);self.assertEqual(b.segment(0)['latest_clock']['intervals'],0)
            with self.assertRaisesRegex(ValueError,'Duplicate'):s.decision_cut()
            s.advance_one();self.assertIn('LEFT80',p.consumed_at[100]);self.assertEqual(b.consumer.pending,[])

    def test_dynamic_public_authority_boundary(self):
        b,_,_=make();before=deepcopy(b._sensor_authority.__dict__)
        with self.assertRaisesRegex(PublicQueryRejected,'PUBLIC_QUERY_REJECTED_AS_FUTURE'):b._sensor_authority.public_snapshot().public_profile_at(80)
        self.assertEqual(b._sensor_authority.__dict__,before)
        self.assertEqual(assert_public_surface(b.public_inputs())['status'],'PASS')
        b._sensor_authority.publish_from_executor(80)
        self.assertEqual(b._sensor_authority.public_snapshot().public_profile_at(80)[1]['sigma'],.08)
        self.assertEqual(b.tick,60);self.assertEqual(b.fusions,0)

    def test_motion_rule_authority_static_contract(self):
        f=build_fixture();self.assertEqual(f.world['motion_rule'],'constant_velocity_from_public_D60_v1')
        self.assertEqual(f.view['config']['motion_model'],'continuous_turn');self.assertEqual(f.view['config']['turn_max_angle'],.5)
        tree=ast.parse((ROOT/'research/non_oracle/stfbs_d1a_model.py').read_text())
        point=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='point')
        branch=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Branch')
        advance=next(n for n in branch.body if isinstance(n,ast.FunctionDef) and n.name=='advance')
        for node in (point,advance):
            fields=[n.attr for n in ast.walk(node) if isinstance(n,ast.Attribute)]
            self.assertNotIn('motion_model',fields);self.assertNotIn('turn_max_angle',fields)
        self.assertIn("self.world['motion'][j]['velocity']",ast.unparse(advance))
        self.assertIn('policy.command(self.frozen[j]',ast.unparse(advance))
        source=(ROOT/'research/non_oracle/stfbs_d1b_qm_model.py').read_text();self.assertIn('point(self.world,j,tick)',source)

    def test_d1b_budget_categories_and_shared_cap(self):
        budget=D1BBudget(test_cap=4,test_estimator=fake_estimator);a,_,_=make('QM_B0_KEEP',budget);b,_,_=make('QM_B1_MEMBER_CHANGE',budget)
        self.assertIs(a.budget,budget);self.assertIs(b.budget,budget)
        for kind in CATEGORIES[:-1]:
            with budget.for_branch(a.name):callback=budget.estimator(kind)
            self.assertEqual(callback.ledger_id,budget.ledger_id);self.assertEqual(callback.branch_id,a.name);callback({'synthetic':True})
        with budget.for_branch(b.name):callback=budget.estimator('MODEL_OBSERVATION_WLS')
        with self.assertRaisesRegex(RuntimeError,'SHARED_CAP_EXCEEDED'):callback({})
        self.assertEqual(budget.snapshot()['total'],4);self.assertEqual(budget.counts['ACTUAL_WLS'],0)
        with self.assertRaises(ValueError):budget.estimator('ACTUAL_WLS',branch_id=a.name)
        unapproved=D1BBudget()
        with self.assertRaisesRegex(RuntimeError,'NO_APPROVED_REAL_BUDGET'):unapproved.estimator('MODEL_OBSERVATION_WLS',branch_id=a.name)({})
        with self.assertRaisesRegex(ValueError,'shared budget'):bind_shared_budget(a,object())
        late,_,_=make();late.streams['synthetic']={}
        with self.assertRaisesRegex(ValueError,'Unsafe late'):bind_shared_budget(late,budget)
        no_budget=deepcopy(a);no_budget.budget=object()
        with self.assertRaisesRegex(ValueError,'Budget not bound'):DynamicSchedule(no_budget,no_budget.name)
        source=(ROOT/'research/non_oracle/stfbs_d1a_model.py').read_text()
        self.assertIn("estimator_fn=self.budget.estimator('MODEL_OBSERVATION_WLS')",source)

    def test_budget_failure_not_rolled_back(self):
        def fail(payload):raise ArithmeticError('synthetic estimator failure')
        fail.evidence_kind=TEST_DOUBLE
        budget=D1BBudget(test_cap=2,test_estimator=fail);b,_,_=make(budget=budget);staged=b._transaction_clone()
        self.assertIs(staged.budget,budget)
        with budget.for_branch(b.name):callback=staged.budget.estimator('MODEL_SPECIAL_TEST_WLS')
        with self.assertRaisesRegex(ArithmeticError,'synthetic'):callback({})
        self.assertEqual(budget.counts['MODEL_SPECIAL_TEST_WLS'],1);self.assertEqual(budget.records[0]['status'],'FAILED')
        self.assertEqual(b.boundaries,[]);self.assertEqual(budget.records[0]['branch_id'],b.name)
        active_registry().note_double('failed fake estimator remains charged; not a real WLS call')

    def test_external_history_context_independence(self):
        b,reg,f=make();self.assertEqual(audit_registered(b,reg)['status'],'PASS')
        b._audit_context=None;self.assertEqual(audit_registered(b,reg)['status'],'PASS')
        bad=deepcopy(f);bad.view['histories'][0]['events'][0]['reasons']=['changed prefix']
        with self.assertRaises(ValueError):verify_registration(reg,bad,b.name)
        b.histories[0]['events'][0]['reasons']=['changed prefix']
        with self.assertRaisesRegex(ValueError,'prefix modified'):audit_registered(b,reg)
        c,creg,_=make('QM_B1_MEMBER_CHANGE')
        with self.assertRaisesRegex(ValueError,'identity'):audit_registered(c,reg)
        self.assertNotEqual(creg.branch_id,reg.branch_id)

    def test_real_execution_requires_run_authorization(self):
        b,reg,f=make();before=deepcopy(b.histories)
        for approval in (None,True,{'formal_authorized':True,'task':'D1-B-QM-1B-RUN'},'test-token'):
            with self.assertRaisesRegex(PermissionError,'RUN_NOT_AUTHORIZED'):execute_run(f,b.name,b.budget,reg,approval=approval)
        with self.assertRaisesRegex(PermissionError,'RUN_NOT_AUTHORIZED'):DynamicSchedule(b,b.name).start()
        self.assertEqual(b.histories,before);self.assertEqual(b.boundaries,[]);self.assertEqual(b.fusions,0);self.assertEqual(b.cache.rows,{})
        self.assertEqual(active_registry().calls,[])
