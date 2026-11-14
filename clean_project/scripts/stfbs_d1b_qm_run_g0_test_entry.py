"""One protected RUN_G0 suite. No direct or unbound execution."""
import argparse,hashlib,json,sys,io,traceback
from pathlib import Path

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--suite',required=True);parser.add_argument('--launch-ticket',required=True)
    parser.add_argument('--run-policy',required=True);parser.add_argument('--policy-sha256',required=True)
    args=parser.parse_args();root=Path(__file__).resolve().parents[1]
    raw=Path(args.run_policy).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=args.policy_sha256:raise ValueError('Untrusted policy digest')
    initial=json.loads(raw)
    if Path(initial['root']).resolve()!=root or Path(initial['entry_script']).resolve()!=Path(__file__).resolve():raise ValueError('Untrusted repository/script')
    sys.path.insert(0,str(root))
    from research.non_oracle.stfbs_d1b_qm_run_audit import verify_launch,install_guards,save,IDS,NAMES
    policy,binding=verify_launch(root,args)
    report=Path(args.run_policy).resolve().parent;save(report/'LAUNCH_BINDING.json',binding)
    registry=install_guards()  # All guards before test-module loading.
    stream=io.StringIO();result=None;fatal=None
    try:
        import unittest,importlib
        module=importlib.import_module('tests.test_stfbs_d1b_qm_run_g0')
        if Path(module.__file__).resolve()!=root/'tests/test_stfbs_d1b_qm_run_g0.py':raise ValueError('Wrong test module')
        actual_names=sorted(n for n in vars(module.RunG0Tests) if n.startswith('test_'))
        if actual_names!=sorted(NAMES):raise ValueError('Runtime whitelist mismatch')
        loaded=[]
        for name,m in list(sys.modules.items()):
            if name.split('.')[0] in ('research','pursuit_v2','scripts','tests'):
                file=getattr(m,'__file__',None)
                if file and not Path(file).resolve().is_relative_to(root):raise ValueError('Non-repository project import: '+name)
                if file:loaded.append(dict(module=name,path=str(Path(file).resolve())))
        save(report/'LOADED_MODULE_ORIGINS.json',loaded)
        registry.integrity('after whitelist module import')
        class Result(unittest.TextTestResult):
            def __init__(self,*a,**kw):
                super().__init__(*a,**kw);self.executed=[];self.case_records=[]
            def startTest(self,test):
                identifier=test.id()
                if identifier not in IDS or identifier in self.executed:raise ValueError('Extra/duplicate formal test')
                registry.current_test=identifier;registry.integrity('before '+identifier)
                self.executed.append(identifier);super().startTest(test)
            def stopTest(self,test):
                try:registry.integrity('after '+test.id())
                except Exception:self.addError(test,sys.exc_info())
                failed=any(x.id()==test.id() for x,_ in self.errors+self.failures)
                self.case_records.append(dict(id=test.id(),status='FAIL' if failed else 'PASS',double_evidence=[s for s in registry.scopes if s['test']==test.id()]))
                super().stopTest(test)
        suite=unittest.TestSuite([module.RunG0Tests(name) for name in NAMES])
        result=unittest.TextTestRunner(stream=stream,verbosity=2,resultclass=Result).run(suite)
        registry.integrity('all ten finished')
    except Exception as error:
        fatal=dict(error=repr(error),traceback=traceback.format_exc())
    finally:
        try:registry.integrity('final exit')
        except Exception as e:
            if fatal is None:fatal=dict(error=repr(e),traceback=traceback.format_exc())
        ledger=registry.ledger();save(report/'FORBIDDEN_CALL_LEDGER.json',ledger)
        with (report/'TEST_OUTPUT.log').open('x',encoding='utf-8') as f:f.write(stream.getvalue())
    summary=dict(task=policy['task'],suite=policy['suite'],policy_sha256=args.policy_sha256,
        executed_ids=[] if result is None else result.executed,cases=[] if result is None else result.case_records,
        all_passed=bool(result is not None and result.wasSuccessful() and result.executed==list(IDS) and not fatal),
        errors=[] if result is None else [dict(id=t.id(),trace=s) for t,s in result.errors],failures=[] if result is None else [dict(id=t.id(),trace=s) for t,s in result.failures],
        skips=[] if result is None else [str(x) for x in result.skipped],unexpected_successes=[] if result is None else [x.id() for x in result.unexpectedSuccesses],fatal=fatal)
    save(report/'DETERMINISTIC_TEST_RESULTS.json',summary)
    good=summary['all_passed'] and not registry.calls and not registry.overwritten
    save(report/'INTERFACE_ACCEPTANCE.json',dict(status='DETERMINISTIC_TESTS_PASS_PENDING_SUPERVISION' if good else 'INTERFACE_NOT_VERIFIED',fixture='STRUCTURALLY_VALIDATED_UNFUSED_MODEL_FIXTURE',physical_validation=False,tests_passed=summary['all_passed'],forbidden_attempts=len(registry.calls),guards_intact=not registry.overwritten,next_stage_authorized=False))
    print(stream.getvalue())
    if fatal:print(json.dumps(fatal),file=sys.stderr)
    return 0 if good else 1

if __name__=='__main__':raise SystemExit(main())
