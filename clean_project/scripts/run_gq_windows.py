"""Public Windows GQ CLI. Importing it does not import scientific modules."""
from pathlib import Path
import argparse,json,subprocess,sys,os,platform,hashlib,uuid,importlib.metadata as md
ROOT=Path(__file__).resolve().parents[1]
def positive(value):
 n=int(value)
 if n<=0:raise argparse.ArgumentTypeError('must be positive')
 return n
def parser():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--scene',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 p.add_argument('--evaluator',choices=['R','S_NEW','both'],default='both')
 p.add_argument('--max-candidates',type=positive,default=12)
 p.add_argument('--max-decisions',type=positive,default=None)
 p.add_argument('--timeout',type=positive,default=180)
 p.add_argument('--audit',choices=['required'],default='required',help='Candidate/decision/episode audit always required; no extra reference simulation')
 return p
def main(argv=None):
 args=parser().parse_args(argv);out=args.output.resolve();scene=args.scene.resolve()
 if out.exists():raise FileExistsError('Choose a new output directory: '+str(out))
 if os.name!='nt':raise RuntimeError('This entry is validated for Windows only')
 raw=scene.read_bytes();source=json.loads(raw)
 required={'config','positions_initial','targets','initial_assignment','sensor_declaration_schedule','measurement_model'}
 if not required.issubset(source):raise ValueError('Expected existing GQ private execution input format')
 # Preserve declared input bytes independently of the source path.
 out.mkdir(parents=True,exist_ok=False);(out/'INPUT.json').write_bytes(raw)
 options=dict(scene=str(out/'INPUT.json'),evaluator=args.evaluator,max_candidates=args.max_candidates,max_decisions=args.max_decisions,timeout=args.timeout,audit='required',reference_required=False,run_id='WINDOWS_GQ_'+uuid.uuid4().hex)
 (out/'RUN_OPTIONS.json').write_text(json.dumps(options,indent=2),encoding='utf-8')
 (out/'ENVIRONMENT.json').write_text(json.dumps(dict(python=sys.version,executable=sys.executable,platform=platform.platform(),numpy=md.version('numpy'),scipy=md.version('scipy'),input_sha256=hashlib.sha256(raw).hexdigest()),indent=2),encoding='utf-8')
 files=[]
 for tree in ['pursuit_v2','research/information_service_online','research/information_service_shared','research/information_service_memory_accounting','research/information_service','research/cooperative_sensing','research/quality_allocation','scripts']:
  for f in sorted((ROOT/tree).rglob('*.py')):files.append(dict(path=str(f),sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
 (out/'SOURCE_PINS.json').write_text(json.dumps(files,indent=2),encoding='utf-8')
 command=[sys.executable,'-B',str(ROOT/'scripts/gq_windows/worker.py'),str(out),str(out/'RUN_OPTIONS.json')]
 (out/'COMMAND.json').write_text(json.dumps(command,indent=2),encoding='utf-8')
 try:
  result=subprocess.run(command,cwd=ROOT,capture_output=True,timeout=args.timeout)
  (out/'stdout.log').write_bytes(result.stdout);(out/'stderr.log').write_bytes(result.stderr)
  status='PASS' if result.returncode==0 else 'FAIL';exitcode=result.returncode
 except subprocess.TimeoutExpired as e:
  (out/'stdout.log').write_bytes(e.stdout or b'');(out/'stderr.log').write_bytes(e.stderr or b'');status='TIMEOUT';exitcode=124
 summary=dict(status=status,exit_code=exitcode,reference_required=False,historical_research_coverage='NOT_APPLICABLE',audit_scope='primary candidate sensing/trajectory, independent combinations and episode physics/accounting; no independent candidate simulation',timeout_seconds=args.timeout)
 if status=='PASS':
  summary['runs']=json.loads((out/'RESULT.json').read_text(encoding='utf-8'))['runs']
  summary['methods']={}
  for r in summary['runs']:
   m=r['method'];summary['methods'][m]=dict(metrics=json.loads((out/m/'FINAL_METRICS.json').read_text(encoding='utf-8')),actual_sensing=json.loads((out/m/'ACTUAL_SENSE_SUMMARY.json').read_text(encoding='utf-8'))['wls'],episode_audit=str(out/m/'EPISODE_AUDIT/episode_audit.json'))
 (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 (out/'README.md').write_text('GQ run: '+status+'\nSee SUMMARY.json, RESULT.json, per-method EPISODE_INDEX and EPISODE_AUDIT. No performance claim.\n',encoding='utf-8')
 print(json.dumps(dict(status=status,output=str(out)),ensure_ascii=False));return exitcode
if __name__=='__main__':sys.exit(main())
