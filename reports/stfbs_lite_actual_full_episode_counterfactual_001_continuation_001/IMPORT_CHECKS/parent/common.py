import sys,os,json,hashlib,subprocess,time,math
from pathlib import Path
from copy import deepcopy
ROOT=Path(sys.argv[0]).resolve().parent
TASKROOT=ROOT.parent
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(TASKROOT))
from bootstrap import bind,REPO
ROLE='worker' if '--worker' in sys.argv else 'parent' if '--parent' in sys.argv else 'outer'
ENVIRONMENT=bind(ROOT,ROLE)
TASK='STFBS_LITE_ACTUAL_FULL_EPISODE_COUNTERFACTUAL_001'
LIMIT=268435456
def require(v,m):
 if not v:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def size():return sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())
def save(n,x):
 data=json.dumps(x,indent=2,sort_keys=True,allow_nan=False).encode()
 require(size()+len(data)<=LIMIT,'BRANCH_STORAGE_LIMIT')
 with (ROOT/n).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
def git(*args):return subprocess.check_output(['git','-c','safe.directory='+REPO.as_posix(),*args],cwd=REPO,text=True).strip()
a=read(ROOT/'authorization.json');ATTEMPT=a['attempt_id'];RUN=a['run_id']
def verify_frozen():
 freeze=read(TASKROOT/'EXECUTION_FREEZE.json')
 require(git('rev-parse','HEAD')==a['git_head'],'HEAD_DRIFT')
 for p,h in freeze['files'].items():require(sha(TASKROOT/p)==h,'PROGRAM_INPUT_DRIFT/'+p)
 for p,h in freeze['source_sha256'].items():require(sha(REPO/p)==h,'SOURCE_DRIFT/'+p)
 for p,h in freeze['runtime_sha256'].items():require(sha(p)==h,'RUNTIME_DRIFT/'+p)
 return a
