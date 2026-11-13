import sys,os,json,hashlib,subprocess,time,copy,math
from pathlib import Path
from copy import deepcopy
ROOT=Path(sys.argv[0]).resolve().parent
TASKROOT=ROOT.parent
REPO=Path(r'D:\1st\dynamic_member_coalition_core')
sys.path.insert(0,str(REPO));sys.path.insert(0,str(TASKROOT))
LIMIT=268435456
def require(b,m):
 if not b:raise RuntimeError(m)
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def save(n,x):
 encoded=(json.dumps(x,sort_keys=True,allow_nan=False,indent=2)+'\n').encode()
 require(sum(p.stat().st_size for p in ROOT.rglob('*') if p.is_file())+len(encoded)<=LIMIT,'BRANCH_STORAGE_LIMIT')
 with (ROOT/n).open('xb') as f:f.write(encoded);f.flush();os.fsync(f.fileno())
def git(*a):return subprocess.check_output(['git','-c','safe.directory='+REPO.as_posix(),*a],cwd=REPO,text=True).strip()
a=read(ROOT/'authorization.json');ATTEMPT=a['attempt_id'];RUN=a['run_id']
def load_state():
 c=read(a['candidate_path'])['candidate'];v=c['a2_policy_view'];s=c['consumer_seed'];v['beliefs']={int(k):b for k,b in v['beliefs'].items()}
 for k in ('internal_states_at_D60','accepted_position_history','accepted_receipts'):s[k]={int(j):b for j,b in s[k].items()}
 return v,s
