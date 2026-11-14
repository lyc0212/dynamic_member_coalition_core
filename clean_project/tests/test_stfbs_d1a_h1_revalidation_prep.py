"""Preparation only: real pure states, data adapters and stub orchestration."""
import json
import inspect
import subprocess
import sys
import importlib
import tempfile
import time
from pathlib import Path
from copy import deepcopy
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
from contextlib import ExitStack
from scripts import stfbs_d1a_run as driver
from research.non_oracle.stfbs_d1a_audit_input import audit_input
from research.non_oracle.stfbs_d1a_model import Branch, Budget, nominal_world
from research.non_oracle.stfbs_d1a_history_audit import audit_branch_independent
from tests.test_stfbs_d1a_history_repair import fake_fuse, switch

EVIDENCE=[]


class PreparationTests(TestCase):
    def test_type_contract(self):
        view={'targets':[{'id':0},{'id':1}]}
        raw={'world':{'motion':{0:{'position':[1.,2.],'velocity':[.1,0.]},1:{'position':[3.,4.],'velocity':[0.,0.]}},'world_digest':'unchanged'}}
        before=deepcopy(raw)
        normalized=audit_input(raw,view)
        loaded=json.loads(json.dumps(raw));adapted=audit_input(loaded,view)
        self.assertEqual(normalized,adapted);self.assertEqual(raw,before)
        self.assertEqual(adapted['world']['world_digest'],'unchanged')
        adapted['world']['motion'][0]['position'][0]=999
        self.assertEqual(raw,before)
        for keys in ({0:{},'0':{},1:{}},{'00':{},'1':{}},{False:{},1:{}},{0:{}},{0:{},2:{}},{'-1':{},1:{}},{'１':{},1:{}}):
            bad=deepcopy(raw);bad['world']['motion']=keys
            with self.assertRaises(ValueError):audit_input(bad,view)
        # Both auditors consume the same integer-key contract, not independent coercions.
        self.assertIn("['motion'][j]",inspect.getsource(driver.verify))
        self.assertIn("['motion'][j]",inspect.getsource(driver.service_audit))
        EVIDENCE.append(dict(group='TYPE',cases='TYPE-1..7',status='PASS',scope='motion access contract; no complete physical verifier claim'))

    def test_real_pure_state(self):
        view,seed,contexts,manifest=driver.verified_registration()
        for name,actions in [('KEEP',view['assignment']),('SWITCH',switch())]:
            b=Branch(view,seed,nominal_world(view),name,Budget())
            with patch.object(Branch,'fuse',fake_fuse):b.assign(deepcopy(actions))
            result=audit_branch_independent(b,context=contexts[name]);self.assertEqual(result['status'],'PASS')
            with self.assertRaises(ValueError):audit_branch_independent(b,context=contexts['SWITCH' if name=='KEEP' else 'KEEP'])
            with self.assertRaises(ValueError):audit_branch_independent(b,context=None)
            b.histories[0]['events'][0]['kind']='TAMPER'
            with self.assertRaisesRegex(ValueError,'prefix'):audit_branch_independent(b,context=contexts[name])
            EVIDENCE.append(dict(group='C2',branch=name,status='PASS',real_auditor=True,source=manifest['public_digest']))

    def test_frozen_registration(self):
        v,s,c,m,w,p,f=driver.frozen_registration()
        self.assertEqual(set(c),{'KEEP','SWITCH'})
        self.assertEqual(w['world_digest'],driver.read('reports/stfbs_lite_d1a_001/H1_CONTRACT.json')['world']['world_digest'])
        bad=deepcopy(w);bad['public_digest']='wrong_source'
        with patch.object(driver,'nominal_world',return_value=bad),self.assertRaisesRegex(ValueError,'Frozen H1 source mismatch'):
            driver.frozen_registration()
        EVIDENCE.append(dict(group='FROZEN',status='PASS',world_digest=w['world_digest'],public_digest=m['public_digest'],plan=f))

    def test_entry_subprocess(self):
        for args,code in [([],1),(['--help'],0),(['--execute-frozen-h1'],1)]:
            result=subprocess.run([sys.executable,'-B','scripts/stfbs_d1a_run.py',*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,code)
            EVIDENCE.append(dict(group='ENTRY subprocess',args=args,exit=result.returncode,stdout=result.stdout,stderr=result.stderr))

    def test_entry_missing(self):
        with patch.object(driver,'frozen_registration',side_effect=AssertionError('Unauthorized registration')) as register, patch.object(driver,'Budget',side_effect=AssertionError('Unauthorized budget')):
            for args in ([],['--execute-frozen-h1'],['--execute-frozen-h1','--approval-manifest','absent.json'],['--approval-manifest','absent.json','--output-dir','reports/new']):
                with self.assertRaises(ValueError):driver.main(args)
            register.assert_not_called()
        EVIDENCE.append(dict(group='ENTRY missing',status='PASS'))

    def test_import_and_failure_journal(self):
        with patch.object(Branch,'__init__',side_effect=AssertionError('Unexpected Branch construction')):
            importlib.reload(driver)
        registered=driver.frozen_registration()
        # Deliberately NOT a valid approval manifest; authorize itself is the mock seam.
        with tempfile.TemporaryDirectory(dir='reports/stfbs_lite_d1a_h1_revalidation_prep_001') as temp:
            output=Path(temp)/'artificial_entry10'
            with patch.object(driver,'authorize',return_value=(output,{'stub_only':True})),patch.object(driver,'frozen_registration',return_value=registered),patch.object(driver,'execute_registered',side_effect=ValueError('injected audit failure')):
                with self.assertRaisesRegex(ValueError,'injected audit'):driver.main([])
            failure=json.loads((output/'MAIN_FAILURE.json').read_text())
            self.assertEqual(failure['status'],'BLOCKED');self.assertFalse((output/'MODEL_PAIR_RESULT.json').exists())
            EVIDENCE.append(dict(group='ENTRY-2/10',status='PASS',failure=failure,artifact_scope='temporary artificial test only'))

    def test_authorization_negatives(self):
        args=SimpleNamespace(execute_frozen_h1=True,approval_manifest='synthetic-not-written',output_dir=str(driver.ROOT/'reports'/'hypothetical_future_pair'))
        # No valid approval record is created on disk. Synthetic authorization stays in mocks.
        pins={str(p.relative_to(driver.ROOT)).replace('\\','/'):driver.hashlib.sha256(p.read_bytes()).hexdigest() for pattern in ('research/non_oracle/stfbs_d1a_*.py','scripts/stfbs_d1a_run.py') for p in driver.ROOT.glob(pattern)}
        approval=dict(status='APPROVED_FOR_ONE_H1_REVALIDATION',experiment='D1_A_FROZEN_H1',authorized_by='TEST_STUB_ONLY',limits=driver.LIMITS,head='synthetic',source_pins=pins,output_dir=args.output_dir)
        with patch.object(driver,'read',return_value=approval),patch.object(driver.subprocess,'check_output',return_value='synthetic\n'):
            self.assertEqual(driver.authorize(args)[0],Path(args.output_dir))
            for field,value in [('status','INVALID'),('head','wrong'),('limits',{}),('source_pins',{})]:
                bad=deepcopy(approval);bad[field]=value
                with patch.object(driver,'read',return_value=bad),self.assertRaises(ValueError):driver.authorize(args)
            for destination in ('reports/stfbs_lite_d1a_001','reports/stfbs_lite_d1a_001/new','reports/stfbs_lite_d1a_h1_revalidation_prep_001'):
                args.output_dir=str(driver.ROOT/destination)
                with self.assertRaises(ValueError):driver.authorize(args)
        EVIDENCE.append(dict(group='ENTRY approval/directory',status='PASS',valid_record_written=False))

    def test_stub_orchestration(self):
        for failure in (None,'history','verify','service','physical_economic','budget','context','source'):
            calls=[];instances=[];saved={};progress={};budget=SimpleNamespace(counts={'MODEL':0},check=lambda:None)
            contexts={'KEEP':object(),'SWITCH':object()}
            class StubBranch:
                def __init__(self,v,s,w,name,b):
                    self.name=name;self.budget=b;instances.append(self);calls.append('construct:'+name)
                def run(self,plan):
                    calls.append('stub_run:'+self.name);self.budget.counts['MODEL']+=1
                    return dict(world={'motion':{0:{}}},net=0.,components={'flow':0.},change_cost=0.)
            def check(label,obj=None,**kwargs):
                calls.append(label)
                if label=='history':
                    self.assertIs(obj,instances[-1]);self.assertIs(kwargs['context'],contexts[obj.name])
                if label==failure:raise ValueError('injected '+label)
                return {'status':'PASS'}
            with ExitStack() as stack:
                stack.enter_context(patch.object(driver,'Branch',StubBranch))
                stack.enter_context(patch.object(driver,'audit_branch_independent',lambda obj,**kw:check('history',obj,**kw)))
                stack.enter_context(patch.object(driver,'verify',lambda *a,**k:check('verify')))
                stack.enter_context(patch.object(driver,'service_audit',lambda *a:check('service')))
                stack.enter_context(patch.object(driver,'audit',lambda *a:check('physical_economic')))
                if failure=='budget':budget.check=lambda:check('budget')
                if failure=='context':contexts.pop('KEEP')
                if failure=='source':
                    stack.enter_context(patch.object(driver,'audit_input',side_effect=ValueError('source mismatch')))
                def run():return driver.run_pair({'targets':[{'id':0}]},{},contexts,{},dict(KEEP=[],SWITCH=[]),budget,lambda k,v:saved.update({k:v}),progress)
                if failure:
                    with self.assertRaises(ValueError):run()
                    self.assertLessEqual(len(instances),1);self.assertNotIn('MODEL_PAIR_RESULT.json',saved)
                else:
                    pair,checks=run();self.assertEqual(pair['status'],'PAIR_AUDITS_PASS_PENDING_G0_G5_REVIEW')
                    self.assertEqual(calls,['construct:KEEP','stub_run:KEEP','history','verify','service','physical_economic','construct:SWITCH','stub_run:SWITCH','history','verify','service','physical_economic'])
                    self.assertIs(instances[0].budget,instances[1].budget)
            EVIDENCE.append(dict(group='C1',failure=failure,status='PASS',calls=calls,progress=deepcopy(progress),shared_budget=True,stub_only=True))
