"""Frozen real-MODEL aggregation, never fixture selector."""
import pathlib,json,hashlib,math
from fractions import Fraction
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def need(v,m):
 if not v:raise RuntimeError(m)
def aggregate(root,index):
 root=pathlib.Path(root);c5=next(root.parent.glob('stfbs_member_change_001*'));historic=c5/'THREE_ACTION_COMPARISON.json'
 need(sha(historic)=='59d5402db2a429c78e05bbc1e6a9039520c21589be4de2ee147cde373b5e4a42','H1_IDENTITY')
 matrix={'H1':{r['action']:r['net'] for r in read(historic)['rows']},'H2':{},'H3':{}};cells=[]
 for row in index:
  d=pathlib.Path(row['directory']);report=read(d/'FINAL_BRANCH_REPORT.json');need(report['valid_cell_candidate'] is True,'UNACCEPTED_CELL');raw=read(d/'BRANCH_RAW.json')
  need(raw['provenance']=='SIMULATED' and raw['observation_origin']=='MODEL' and raw['branch']==row['branch_id'],'REAL_MODEL_IDENTITY')
  need(raw['world']==row['world'] and raw['boundaries'][0]['after']==row['initial_actions'],'WORLD_ACTION')
  need(raw['frames'][-1]['tick']==120 and len(raw['frames'])==60,'HORIZON');need(math.isfinite(raw['net']),'NONFINITE')
  for e in read(d/'evidence_manifest.json')['files']:need(sha(d/e['path'])==e['sha256'],'CELL_EVIDENCE_CHANGED')
  h,a=row['name'][:2],row['name'][3:];need(a not in matrix[h],'DUPLICATE_CELL');matrix[h][a]=raw['net'];cells.append(dict(world=h,action=a,raw_sha256=sha(d/'BRANCH_RAW.json'),world_digest=raw['world']['world_digest'],initial_actions=row['initial_actions'],horizon=[60,120],resource_counts=read(d/'RESOURCE_COUNTS.json')))
 actions=['KEEP','SWITCH','MEMBER_CHANGE'];worlds=['H1','H2','H3'];need(all(set(matrix[h])==set(actions) for h in worlds),'NINE_CELLS_REQUIRED')
 vals={(a,h):Fraction.from_float(matrix[h][a]) for a in actions for h in worlds};best={h:max(vals[a,h] for a in actions) for h in worlds};regret={(a,h):best[h]-vals[a,h] for a in actions for h in worlds};worst={a:max(regret[a,h] for h in worlds) for a in actions}
 key=lambda a:tuple(((-1 if x['target'] is None else x['target']),{'none':0,'dual_neg45':1,'dual_pos45':2}[x['role']]) for x in next(r['initial_actions'] for r in index if r['name'][3:]==a))
 selected=min(actions,key=lambda a:(worst[a],a!='KEEP',key(a)));frac=lambda v:dict(numerator=v.numerator,denominator=v.denominator,display=float(v))
 return dict(matrix=matrix,regret={h:{a:frac(regret[a,h]) for a in actions} for h in worlds},worst_regret={a:frac(worst[a]) for a in actions},selected_action=selected,per_world_best={h:[a for a in actions if vals[a,h]==best[h]] for h in worlds},worst_worlds={a:[h for h in worlds if regret[a,h]==worst[a]] for a in actions},cell_evidence=cells,h1_evidence=dict(path=str(historic),sha256=sha(historic)),scope='OFFLINE_D60_MODEL_CONDITIONAL',synthetic_fixture=False)
