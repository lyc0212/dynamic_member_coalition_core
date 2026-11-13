"""Import-only verification of actual fixed entry bytes in isolated scratch."""
import sys,pathlib,runpy,json
HERE=pathlib.Path(__file__).resolve().parent
role=sys.argv[1]
target=HERE/('outer_controller.py' if role=='outer' else 'model_driver.py')
sys.argv=[str(target)]+([] if role=='outer' else ['--'+role])
runpy.run_path(str(target),run_name='ENTRY_IMPORT_ONLY')
# Cover each real worker/parent delayed dependency by import only.
from scripts.run_a1 import Sensing
from research.non_oracle.environment import StaggeredEnvironment
from research.non_oracle import policy
from research.non_oracle.a2_analysis import decision_evidence
from research.information_service_bridge import public_stream
from research.cooperative_sensing import estimator
from research.non_oracle.stfbs_lite_real_d60_source import DurableResourceLedger,guard_wls_bindings,inspect_production_aliases
from research.non_oracle.local_dev.journal import LocalJournal
import actual_resources,physical_audit,comparison,analysis
for name in ['attempt.consumed','parent_start_attempt.lock','worker.jsonl','controller_start.lock']:
 if (HERE/name).exists():raise RuntimeError('IMPORT_PROBE_CREATED_FORMAL_STATE/'+name)
with (HERE/'RESULT.json').open('x') as f:
 json.dump(dict(status='PASS',role=role,mode='IMPORT_ONLY',entry=str(target),isolated_flags=['-I','-S','-B'],science_calls=0,formal_locks_created=False,environment_created=False,delayed_scientific_dependencies_imported=True),f,indent=2)
