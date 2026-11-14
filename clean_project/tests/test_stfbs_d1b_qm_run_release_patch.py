"""Exactly eight synthetic patch methods; no real G1 entry is invoked."""
from unittest import TestCase
from copy import deepcopy
from pathlib import Path
import ast,json,math
from scripts.stfbs_d1b_qm_run_g1_watchdog import validate_final_resource_receipt,final_resource_audit
from research.non_oracle.stfbs_d1b_qm_run_evidence import coordinate_batch
from scripts.stfbs_d1b_qm_run_release_patch_test_entry import ROOT,REPORT,LABEL,save,active_registry

RESOURCE_CASES=[];EARLY_RESULTS={}
SCIENCE_KEYS={'EXECUTION_VALID','Q_ONLY_FAILURE_OBSERVED','GQ_RESTORED','SERVICE_RESUMED','TASK_COMPLETED'}

def receipt_fixture():
    return dict(status='EXITED',exit_code=0,cpu_complete=True,active_processes=0,attempts=1,
                cpu_limit=480,wall_limit=600,tree_cpu_seconds=1.25,wall_seconds=2.5,evidence_kind=LABEL)

def json_safe(value):
    if type(value) is float and not math.isfinite(value):return dict(original_type='float',representation=repr(value))
    if isinstance(value,dict):return {k:json_safe(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [json_safe(v) for v in value]
    return value

def resource_case(case,identifier,receipt,expected,*,cpu=480,wall=600,reason=None,ledger=None,sources=True):
    result=final_resource_audit(receipt,cpu,wall,dict(status='COMPLETE') if ledger is None else ledger,sources)
    case.assertEqual(result['status'],expected)
    if reason:case.assertIn(reason,result['failure_reasons'])
    RESOURCE_CASES.append(dict(id=identifier,input=json_safe(receipt),approved_cpu=json_safe(cpu),approved_wall=json_safe(wall),result=json_safe(result),evidence_kind=LABEL))
    return result

class SyntheticOps:
    evidence_kind=LABEL
    def __init__(self,mode):self.mode=mode;self.calls=[];self.dynamic_results={};self.final_result=dict(EXECUTION_VALID=True,Q_ONLY_FAILURE_OBSERVED=True,GQ_RESTORED=False,SERVICE_RESUMED=False,TASK_COMPLETED=False,evidence_kind=LABEL)
    def probe(self,name):self.calls.append('probe:'+name);return dict(branch_id=name,evidence_kind=LABEL)
    def old_quality(self,old):
        self.calls.append('old_quality');return dict(G=True,Q='FAIL' if self.mode=='A' else 'PASS',status='PASS',audit_scope='REFERENCE_SOURCE_GQ_ONLY_NOT_COMPLETE_EXECUTION_AUDIT',evidence_kind=LABEL)
    def candidate(self,old,new,sigma):
        self.calls.append('candidate:'+str(sigma))
        q='UNKNOWN' if self.mode=='B' and sigma==.08 else 'PASS'
        if self.mode in ('C','SUCCESS') and sigma==.08:q='FAIL'
        return dict(old_G=True,new_G=True,old_Q='PASS',new_Q=q,sigma=sigma,probe_id=new['branch_id'],evidence_kind=LABEL)
    def candidate_values(self,row):self.calls.append('values:'+str(row['sigma']));return row
    def admit(self,rows):self.calls.append('admit');return dict(selected_sigma=rows[-1]['sigma'],evidence_kind=LABEL)
    def dynamic(self,name,sigma,admission):
        self.calls.append('dynamic:'+name)
        result=dict(branch_id=name,raw_output='SYNTHETIC_RAW_RETAINED',sigma=sigma,raw_task_completed=True,evidence_kind=LABEL)
        self.dynamic_results[name]=result;return result
    def dynamic_realized(self,b0,b1,sigma):self.calls.append('dynamic_realized');return self.mode!='C'
    def b3(self):self.calls.append('b3');return dict(evidence_kind=LABEL)
    def f1(self,b1):self.calls.append('f1')
    def special(self,name,source):self.calls.append('special:'+name)
    def final_science(self,*args):self.calls.append('final_science');return self.final_result

class PatchTests(TestCase):
    def test_resource_receipt_accepts_valid_and_exact_limit(self):
        for label,measured_cpu,measured_wall in [('normal',1.25,2.5),('zero',0,0),('cpu_equal',480,2.5),('wall_equal',1.25,600),('both_equal',480,600)]:
            r=receipt_fixture();r.update(tree_cpu_seconds=measured_cpu,wall_seconds=measured_wall)
            result=resource_case(self,label,r,'PASS')
            self.assertTrue(result['resource_validation']['numeric_valid']);self.assertTrue(result['resource_validation']['single_attempt_valid'])
        tree=ast.parse((ROOT/'scripts/stfbs_d1b_qm_run_g1_watchdog.py').read_text())
        main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        calls=[n for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='final_resource_audit']
        self.assertEqual(len(calls),1)
        self.assertEqual([ast.unparse(a) for a in calls[0].args],['receipt',"permit.bindings['cpu_limit']","permit.bindings['wall_limit']",'ledger','unchanged'])
        valid=next(n for n in ast.walk(main) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='valid' for t in n.targets))
        self.assertEqual(ast.unparse(valid.value),"audit['status'] == 'PASS'")
        self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='dump' and isinstance(n.args[0],ast.Name) and n.args[0].id=='audit' for n in ast.walk(main)))

    def test_resource_receipt_rejects_cpu_and_wall_excess(self):
        for field,value,reason in [('tree_cpu_seconds',math.nextafter(480.,math.inf),'TREE_CPU_LIMIT_EXCEEDED'),('wall_seconds',math.nextafter(600.,math.inf),'WALL_LIMIT_EXCEEDED'),('tree_cpu_seconds',481,'TREE_CPU_LIMIT_EXCEEDED'),('wall_seconds',601,'WALL_LIMIT_EXCEEDED'),('tree_cpu_seconds',10**400,'TREE_CPU_LIMIT_EXCEEDED')]:
            r=receipt_fixture();r[field]=value
            result=resource_case(self,field+'_excess_'+repr(value),r,'BLOCKED',reason=reason)
            self.assertEqual(result['resource_validation']['status'],'BLOCKED')

    def test_resource_receipt_rejects_nonfinite_negative_missing_and_bool(self):
        invalid=[float('nan'),float('inf'),float('-inf'),-1,None,True,False,'120']
        for field in ('tree_cpu_seconds','wall_seconds','cpu_limit','wall_limit'):
            for value in invalid:
                r=receipt_fixture();r[field]=value
                result=resource_case(self,field+':'+repr(value),r,'BLOCKED',reason='INVALID_RESOURCE_MEASUREMENT')
                self.assertFalse(result['resource_validation']['numeric_valid'])
            r=receipt_fixture();r.pop(field)
            resource_case(self,'missing:'+field,r,'BLOCKED',reason='INVALID_RESOURCE_MEASUREMENT')
        for field in ('cpu','wall'):
            for value in invalid+[0]:
                kwargs={field:value};resource_case(self,'invalid_approved_'+field+':'+repr(value),receipt_fixture(),'BLOCKED',reason='INVALID_APPROVED_LIMIT',**kwargs)
        for value in (0,2,True,False,None,'1',1.0):
            r=receipt_fixture();r['attempts']=value
            result=resource_case(self,'attempts:'+repr(value),r,'BLOCKED',reason='INVALID_ATTEMPT_COUNT')
            self.assertFalse(result['resource_validation']['single_attempt_valid'])
        r=receipt_fixture();r.pop('attempts');resource_case(self,'missing_attempts',r,'BLOCKED',reason='INVALID_ATTEMPT_COUNT')
        for field,value in [('status','TIMED_OUT'),('status',None),('exit_code',1),('exit_code',False),('cpu_complete',False),('cpu_complete',1),('active_processes',1),('active_processes',False)]:
            r=receipt_fixture();r[field]=value;resource_case(self,'exit_or_cleanup:'+field+':'+repr(value),r,'BLOCKED')
        for field in ('status','exit_code','cpu_complete','active_processes'):
            r=receipt_fixture();r.pop(field);resource_case(self,'missing_exit:'+field,r,'BLOCKED')

    def test_resource_receipt_rejects_approved_limit_mismatch(self):
        for field,value in [('cpu_limit',960),('wall_limit',1200),('cpu_limit',479),('wall_limit',599)]:
            r=receipt_fixture();r[field]=value
            resource_case(self,'mismatch:'+field+':'+str(value),r,'BLOCKED',reason='APPROVED_LIMIT_MISMATCH')
        resource_case(self,'unverified_journal',receipt_fixture(),'BLOCKED',reason='RESOURCE_LEDGER_INCOMPLETE',ledger=dict(status='RESOURCE_LEDGER_INCOMPLETE'))
        resource_case(self,'source_changed',receipt_fixture(),'BLOCKED',reason='SOURCE_PINS_CHANGED_OR_UNVERIFIED',sources=False)
        resource_case(self,'source_integer_not_bool',receipt_fixture(),'BLOCKED',sources=1)
        save(REPORT/'RESOURCE_RECEIPT_ACCEPTANCE.json',dict(status='PASS',case_count=len(RESOURCE_CASES),cases=RESOURCE_CASES,
            final_decision_connection='Tests call same final_resource_audit as actual main; AST checks direct valid/output dependency',
            actual_g1_main_invoked=False,evidence_kind=LABEL))

    def test_scenario_admission_early_stop_has_complete_science(self):
        ops=SyntheticOps('A');result=coordinate_batch(ops);EARLY_RESULTS['A']=result
        self.assertEqual(result['status'],'SCENARIO_ADMISSION_FAILED');self.assertEqual(set(result['science']),SCIENCE_KEYS)
        self.assertTrue(all(v is None for v in result['science'].values()));self.assertEqual(set(result['science_disposition']),SCIENCE_KEYS)
        self.assertEqual(ops.calls,['probe:QM_PROBE_OLD','old_quality']);scope=result['science_evidence_scope']
        self.assertEqual(scope['tested_probe_sigmas'],[]);self.assertEqual(scope['probe_stages']['QM_PROBE_OLD'],'EXECUTED')
        self.assertTrue(all(scope['probe_stages']['QM_PROBE_DEGRADED_'+str(i)]=='NOT_EXECUTED_GATE_NOT_MET' for i in range(1,5)))
        self.assertTrue(all(v=='NOT_EXECUTED_GATE_NOT_MET' for v in result['stages'].values()))
        self.assertIsNone(result['probe_q_only_failure_observed'])

    def test_no_q_only_fail_early_stop_has_complete_science(self):
        ops=SyntheticOps('B');result=coordinate_batch(ops);EARLY_RESULTS['B']=result
        self.assertEqual(result['status'],'NO_Q_ONLY_FAIL_FOUND');self.assertEqual(set(result['science']),SCIENCE_KEYS)
        self.assertIs(result['science']['Q_ONLY_FAILURE_OBSERVED'],False)
        self.assertTrue(all(v is None for k,v in result['science'].items() if k!='Q_ONLY_FAILURE_OBSERVED'))
        self.assertEqual(result['science_disposition']['Q_ONLY_FAILURE_OBSERVED'],'NOT_OBSERVED_IN_TESTED_PROBES')
        self.assertEqual(result['science_evidence_scope']['Q_ONLY_FAILURE_OBSERVED'],'FIXED_FOUR_SIGMA_PROBES')
        self.assertEqual(result['science_evidence_scope']['tested_probe_sigmas'],[.04,.08,.16,.32])
        self.assertEqual(len([x for x in ops.calls if x.startswith('probe:')]),5)
        self.assertFalse(any(x=='admit' or x.startswith('dynamic:') for x in ops.calls))
        self.assertTrue(all(v=='NOT_EXECUTED_GATE_NOT_MET' for v in result['stages'].values()))

    def test_dynamic_not_realized_preserves_executed_b0_b1(self):
        ops=SyntheticOps('C');result=coordinate_batch(ops);EARLY_RESULTS['C']=result
        self.assertEqual(result['status'],'DYNAMIC_Q_ONLY_NOT_REALIZED');self.assertEqual(set(result['science']),SCIENCE_KEYS)
        self.assertTrue(all(v is None for v in result['science'].values()))
        self.assertIs(result['probe_q_only_failure_observed'],True);self.assertEqual(result['formal_dynamic_q_only_gate'],'NOT_CONFIRMED')
        for name in ('B0','B1'):
            self.assertEqual(result['stages'][name],'EXECUTED');self.assertEqual(result['science_evidence_scope']['dynamic_branch_disposition'][name],'EXECUTED_AWAITING_FINAL_AUDIT')
        self.assertEqual(result['science_evidence_scope']['dynamic_result_references']['B0'],ops.dynamic_results['QM_B0_KEEP'])
        self.assertEqual(result['science_evidence_scope']['dynamic_result_references']['B1'],ops.dynamic_results['QM_B1_MEMBER_CHANGE'])
        self.assertTrue(all(result['stages'][name]=='NOT_EXECUTED_GATE_NOT_MET' for name in ('B3','F1','F2','F3A','F3B')))
        self.assertEqual(result['science_evidence_scope']['tested_probe_sigmas'],[.04,.08])
        self.assertEqual(result['science_disposition']['Q_ONLY_FAILURE_OBSERVED'],'NOT_CONFIRMED_IN_FORMAL_DYNAMIC_BRANCH')
        self.assertFalse(any(x in ('b3','f1','final_science') or x.startswith('special:') for x in ops.calls))

    def test_early_stop_science_semantics_and_no_scientific_execution(self):
        self.assertEqual(set(EARLY_RESULTS),{'A','B','C'})
        for result in EARLY_RESULTS.values():
            self.assertIsNone(result['science']['EXECUTION_VALID'])
            self.assertEqual(result['science_disposition']['EXECUTION_VALID'],'EXECUTED_AWAITING_FINAL_AUDIT')
            self.assertTrue(all(result['science'][k] is None for k in ('GQ_RESTORED','SERVICE_RESUMED','TASK_COMPLETED')))
        ops=SyntheticOps('SUCCESS');result=coordinate_batch(ops)
        self.assertEqual(result['status'],'EXECUTED_AWAITING_FINAL_AUDIT');self.assertIs(result['science'],ops.final_result)
        self.assertEqual(ops.calls,['probe:QM_PROBE_OLD','old_quality','probe:QM_PROBE_DEGRADED_1','candidate:0.04','values:0.04','probe:QM_PROBE_DEGRADED_2','candidate:0.08','values:0.08','admit','dynamic:QM_B0_KEEP','dynamic:QM_B1_MEMBER_CHANGE','dynamic_realized','b3','f1','special:QM_F2_VALID_HISTORY','special:QM_F3_STREAM_A','special:QM_F3_STREAM_B','final_science'])
        snapshots=json.loads((REPORT/'BASE_SOURCE_SNAPSHOTS.json').read_bytes())
        path='research/non_oracle/stfbs_d1b_qm_run_evidence.py';old=ast.parse(snapshots[path]);new=ast.parse((ROOT/path).read_text())
        old_coord=next(n for n in old.body if isinstance(n,ast.FunctionDef) and n.name=='coordinate_batch')
        new_coord=next(n for n in new.body if isinstance(n,ast.FunctionDef) and n.name=='coordinate_batch')
        def calls(node):
            return [ast.unparse(n) for n in sorted((n for n in ast.walk(node) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='ops'),key=lambda n:(n.lineno,n.col_offset))]
        self.assertEqual(calls(old_coord),calls(new_coord));self.assertEqual(ast.dump(old_coord.body[-1]),ast.dump(new_coord.body[-1]))
        before=[ast.dump(n) for n in old.body if not isinstance(n,ast.FunctionDef) or n.name!='coordinate_batch']
        after=[ast.dump(n) for n in new.body if not isinstance(n,ast.FunctionDef) or n.name not in ('coordinate_batch','_early_scientific_result')]
        self.assertEqual(before,after)
        self.assertEqual(active_registry().calls,[])
        save(REPORT/'EARLY_STOP_SCIENCE_ACCEPTANCE.json',dict(status='PASS',early_results=EARLY_RESULTS,success_result=result,success_call_trace=ops.calls,
            normal_path_ops_calls_and_final_return_ast_unchanged=True,all_other_original_module_nodes_unchanged=True,
            science_execution_valid_not_inferred_from_return_or_quality_pass=True,evidence_kind=LABEL))
