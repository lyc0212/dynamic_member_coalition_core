"""Guarded, zero-physics test runner; evidence is preparation-only."""
import sys,json,time,unittest,io,traceback
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from research.non_oracle import stfbs_d1a_model as model,policy
from research.cooperative_sensing import estimator
from research.information_service_bridge.public_stream import BridgeFrameProcessor
from research.information_service_online.execution import OnlineEnvironment
from tests import test_stfbs_d1a_h1_revalidation_prep as cases

root=Path(__file__).resolve().parent
counts={}
def deny(name):
    counts[name]=0
    def call(*a,**k):
        counts[name]+=1
        raise AssertionError('Forbidden actual call: '+name)
    return call

cpu=time.process_time();wall=time.monotonic()
with ExitStack() as stack:
    for owner,name in ((model,'estimate'),(policy,'estimate'),(estimator,'estimate'),(BridgeFrameProcessor,'process'),(OnlineEnvironment,'step'),(model.Branch,'run'),(model.Branch,'advance')):
        stack.enter_context(patch.object(owner,name,deny(owner.__name__+'.'+name)))
    suite=unittest.TestSuite()
    names=('tests.test_stfbs_d1a_h1_revalidation_prep',) if '--targeted' in sys.argv else ('tests.test_stfbs_d1a_h1_revalidation_prep','tests.test_stfbs_d1a_history_repair','tests.test_stfbs_d1a_history_supplement','tests.test_stfbs_d1a_audit_hardening')
    for name in names:
        suite.addTests(unittest.defaultTestLoader.loadTestsFromName(name))
    stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
sequence=1
while (root/f'TEST_ATTEMPT_{sequence:03}.log').exists():sequence+=1
(root/f'TEST_ATTEMPT_{sequence:03}.log').write_text(stream.getvalue(),encoding='utf-8')
(root/f'TEST_EVIDENCE_{sequence:03}.json').write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),success=result.wasSuccessful(),cases=cases.EVIDENCE),indent=2,default=str),encoding='utf-8')
(root/f'ZERO_WLS_STEP_PROOF_{sequence:03}.json').write_text(json.dumps(dict(calls=counts,cpu_seconds=time.process_time()-cpu,wall_seconds=time.monotonic()-wall,scope='in-process guarded suite; subprocess CLI checks separately return before registration; stub run is not real Branch.run'),indent=2),encoding='utf-8')
print(stream.getvalue())
raise SystemExit(0 if result.wasSuccessful() and not any(counts.values()) else 1)
