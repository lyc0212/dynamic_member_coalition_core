"""Single authorized H4 turn, fixed HF holds, four fixed-belief proxy cells."""
import sys,os,time,json,hashlib,copy,math,ast,traceback,subprocess,ctypes,types,html,itertools
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1];S=REPO/'reports/stfbs_lite_h2_h3_extension_005';P=REPO/'reports/stfbs_lite_l3_b_p1_reproduction_001';B=REPO/'reports/stfbs_lite_l3_b_p2_p4_mechanism_diagnostics_001';H=REPO/'reports/l3_b_diagnostic_recovery_001_stage_a_20261114';STAGE=REPO/'reports/l3_b_stage_a_minimal_remediation_execution_001_20261114121457'
sys.path.insert(0,str(STAGE))
from recovery import Writer,Clock,require,plain,typed,digest,HistoricalImports,build_kernel,boundary_check,controller,prediction,TraceRecorder,ledger_check
HEAD='953cc41a5ead22f7f3058ae18126c3b57d7434c7';ACTIONS=('KEEP','SWITCH','MEMBER_CHANGE')
class BudgetStop(RuntimeError):pass
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint(x):return digest(plain(x))
def motion_spec(world):
    s=world['turn_spec'];require(s['physics_digest']==digest({k:v for k,v in s.items() if k!='physics_digest'}),'PHYSICS_SPEC_DIGEST');return s

def point(world,j,tick):
    import numpy as np
    m=world['motion'][j];p=np.asarray(m['position']);v=np.asarray(m['velocity']);s=world['turn_spec']
    if j!=s['target_id'] or tick<=s['turn_tick']:return p+v*((tick-60)*.05)
    return p+v*((s['turn_tick']-60)*.05)+np.asarray(s['velocity_after'])*((tick-s['turn_tick'])*.05)
def velocity_at(world,j,tick):
    s=world['turn_spec'];return list(s['velocity_after']) if j==s['target_id'] and tick>=s['turn_tick'] else list(world['motion'][j]['velocity'])
def escape_time(world,j,start_seconds,side):
    tick=start_seconds/.05;p=point(world,j,tick);v=velocity_at(world,j,tick);s=world['turn_spec'];turn=s['turn_tick']*.05
    if p[0]>=side:return start_seconds
    if j==s['target_id'] and start_seconds<turn:
        first=math.inf if v[0]<=0 else start_seconds+(side-p[0])/v[0]
        if first<=turn:return first
        p=point(world,j,s['turn_tick']);v=s['velocity_after'];return math.inf if v[0]<=0 else turn+(side-p[0])/v[0]
    return math.inf if v[0]<=0 else start_seconds+(side-p[0])/v[0]
def world_digest(world):
    require(world.get('h4_kind') in ('MODEL','PROXY'),'H4_SCHEMA');motion_spec(world)
    expected={'MODEL':'H4_PIECEWISE_CV_SINGLE_TURN_MODEL_V1','PROXY':'H4_PIECEWISE_CV_SINGLE_TURN_PROXY_V1'}[world['h4_kind']]
    require(world['motion_rule' if world['h4_kind']=='MODEL' else 'generation_rule']==expected,'H4_RULE')
    return digest({k:v for k,v in world.items() if k!='world_digest'})
def isolated(text,name,extra=None,package='research.non_oracle'):
    ns=dict(__name__=name,__package__=package,__file__=str(HERE/(name+'.py')));ns.update(extra or {});exec(compile(text,str(HERE/(name+'.py')),'exec'),ns);return ns

def adapt_model(source):
    tree=ast.parse(source);p=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='point');p.body=ast.parse('return _h4_point(world,j,tick)').body
    branch=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Branch');advance=next(n for n in branch.body if isinstance(n,ast.FunctionDef) and n.name=='advance')
    found={'v':0,'escape':0}
    for n in ast.walk(advance):
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            k=n.targets[0].id
            if k=='v':require(ast.unparse(n.value)=="self.world['motion'][j]['velocity']",'HF_VELOCITY_SITE');n.value=ast.parse('_velocity_at(self.world,j,self.tick-1)',mode='eval').body;found[k]+=1
            if k=='escape':n.value=ast.parse('_escape_time(self.world,j,lo,self.cfg.side)',mode='eval').body;found[k]+=1
    require(found=={'v':1,'escape':1},'HF_MOTION_SITES');ast.fix_missing_locations(tree);return ast.unparse(tree)+'\n'
def adapt_proxy(source):
    tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='run_proxy');vx=[n for n in ast.walk(fn) if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='vx'];esc=[n for n in ast.walk(fn) if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='escape']
    # ast.walk visits top-level certificate statements before nested loop statements: identify by the old expression.
    require(len(vx)==len(esc)==2,'PROXY_MOTION_SITES')
    for n in vx:
        require(ast.unparse(n.value)=="world['motion'][j]['velocity'][0]",'PROXY_VELOCITY_SITE')
        n.value=ast.parse('_velocity_at(world,j,_motion_tick)[0]',mode='eval').body
    # Replace the velocity expressions in their actual containing statement lists.
    loop=next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='k')
    for n in ast.walk(loop):
        if isinstance(n,ast.Assign) and n in vx:n.value=ast.parse('_velocity_at(world,j,k-1)[0]',mode='eval').body
        if isinstance(n,ast.Assign) and n in esc:n.value=ast.parse('_escape_time(world,j,lo,cfg.side)',mode='eval').body
    for n in vx:
        if '_motion_tick' in ast.unparse(n.value):n.value=ast.parse('_velocity_at(world,j,start)[0]',mode='eval').body
    for n in esc:
        if '_escape_time' not in ast.unparse(n.value):n.value=ast.parse('_escape_time(world,j,start*DT,cfg.side)',mode='eval').body
    ast.fix_missing_locations(tree);return ast.unparse(tree)+'\n'
def adapt_verify(source):
    tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='verify');count=0
    for n in ast.walk(fn):
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            if n.targets[0].id=='x':n.value=ast.parse('_h4_point(result["world"],j,n-1)[0]',mode='eval').body
            if n.targets[0].id=='escape':n.value=ast.parse('_escape_time(result["world"],j,lo,cfg.side)',mode='eval').body;count+=1
    require(count==1,'VERIFY_ESCAPE_SITE');ast.fix_missing_locations(tree);return ast.unparse(tree)+'\n'
def adapt_audit(source):
    tree=ast.parse(source);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='service_audit');count=0
    for n in ast.walk(fn):
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='p':n.value=ast.parse('_h4_point(result["world"],j,n)',mode='eval').body;count+=1
    require(count==1,'AUDIT_GEOMETRY_SITE');ast.fix_missing_locations(tree);return ast.unparse(tree)+'\n'

def thin(b):return {k:copy.deepcopy(v) for k,v in b.items() if k!='diagnostics'}
def rejection(row,hist):
    e=row['estimate']
    if e is None:return ['ESTIMATE_MISSING']
    out=[]
    if not e.get('has_accepted_estimate'):out.append('NO_ACCEPTED_ESTIMATE')
    if not e.get('optimizer_converged'):out.append('OPTIMIZER_NOT_CONVERGED')
    out += [k.upper() for k in ('numerical_ill_conditioned','ambiguity_detected','boundary_active','numeric_contract_violation') if e.get(k,True)]
    if out:return out
    p=e['estimate'];t=row['measurement_tick']
    if len(p)!=2:return ['INVALID_ESTIMATE_DIMENSION']
    if not all(math.isfinite(x) for x in p):return ['NONFINITE_ESTIMATE']
    if hist and t<=hist[-1][0]:return ['NONINCREASING_MEASUREMENT_TICK']
    return []
def recorded_freeze_source(source):
    tree=ast.parse(source);cl=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Beliefs');fn=copy.deepcopy(next(n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name=='freeze'));fn.name='recorded_freeze';loops=[n for n in fn.body if isinstance(n,ast.For) and ast.unparse(n.iter)=='self.pending'];require(len(loops)==1,'FREEZE_QUEUE_SITE');loop=loops[0]
    before=ast.parse('_capture=self._record_before(row,tick)').body[0];final=ast.parse('self._record_after(row,tick,_capture)').body
    loop.body=[before,ast.Try(body=loop.body,handlers=[],orelse=[],finalbody=final)];module=ast.Module(body=[fn],type_ignores=[]);ast.fix_missing_locations(module);return ast.unparse(module)+'\n'
def make_consumer(Base,freeze_fn):
    class RecordedConsumer(Base):
        def __init__(self,seed):super().__init__(seed);self.recorded_events=[];self._ordinal=0;self._bindings={}
        def freeze(self,tick):self._ordinal=0;return freeze_fn(self,tick)
        def _record_before(self,row,tick):
            j=row['target_id'];hist=self.history[j];ordinal=self._ordinal;self._ordinal+=1
            return dict(state=thin(self.states[j]),history_len=len(hist),consumed_len=len(self.consumed),reference=next(((s,copy.deepcopy(p)) for s,p in reversed(hist) if row['measurement_tick']-s>=5),None),ordinal=ordinal,reasons=rejection(row,hist))
        def _record_after(self,row,tick,before):
            j=row['target_id'];consumed=len(self.consumed)==before['consumed_len']+1;accepted=len(self.history[j])==before['history_len']+1;matches=self._bindings.get(digest(row),[])
            require(len(matches)==1,'HF_FEEDBACK_FRAME_IDENTITY');binding=matches[0];s=None if before['reference'] is None else before['reference'][0];k=row['measurement_tick']
            interval='NOT_APPLICABLE' if s is None or j!=0 else 'PRE_TURN' if k<=75 else 'CROSSES_TURN' if s<75 else 'POST_TURN'
            if accepted and s is None:require(self.states[j]['velocity_estimate']==before['state']['velocity_estimate'] and self.states[j]['velocity_source']==before['state']['velocity_source'],'VELOCITY_RETENTION_CHANGED')
            raw=None if s is None or not accepted else [(x-y)/((k-s)*.05) for x,y in zip(row['estimate']['estimate'],before['reference'][1])]
            event=dict(frame_id=binding['frame_id'],generation_ordinal=binding['ordinal'],freeze_id=tick,freeze_ordinal=before['ordinal'],target=j,measurement_tick=k,available_tick=row['available_tick'],consumed_tick=tick if consumed else None,status='PENDING' if not consumed else 'ACCEPTED' if accepted else 'REJECTED',accepted=accepted,reasons=[] if accepted or not consumed else before['reasons'],before=before['state'],after=thin(self.states[j]),reference_tick=s,reference_interval_ticks=None if s is None else k-s,reference_class=interval,unclipped_difference_velocity=raw,actual_velocity=list(self.states[j]['velocity_estimate']),velocity_source=self.states[j]['velocity_source'],source=row.get('source'),provenance=row.get('provenance'),observation_origin=row.get('observation_origin'))
            require(not consumed or row['available_tick']<=tick,'PREMATURE_CONSUMPTION');self.recorded_events.append(event)
    return RecordedConsumer

class TaskBudget:
    def __init__(self,ctx,name,estimator_source):
        self.ctx=ctx;self.name=name;self.counts=dict(observation_wls=0,solver=0);self.sequence=0;ns=isolated(estimator_source,'h4_estimator_'+name,package='research.cooperative_sensing');self.original_solver=ns['least_squares'];ns['least_squares']=self.solver;self.estimate=ns['estimate']
    def check(self):self.ctx['clock'].check()
    def invoke(self,kind,fn,*args,**kwargs):
        self.check();limits={'observation_wls':(63,189),'solver':(600,1800)};local,total=limits[kind]
        if self.counts[kind]>=local or self.ctx['counts'][kind]>=total:raise BudgetStop('RESOURCE_CALL_LIMIT/'+kind)
        self.sequence+=1;cid=self.name+':'+str(self.sequence);record=dict(call_id=cid,branch=self.name,resource=kind,actual_source='MODEL',accounting_category='MODEL_OBSERVATION_WLS' if kind=='observation_wls' else 'MODEL_SOLVER_START',status='STARTED')
        self.ctx['w'].write('RESOURCE_EVENTS.jsonl',json.dumps(record,separators=(',',':'))+'\n',append=True);self.counts[kind]+=1;self.ctx['counts'][kind]+=1
        try:out=fn(*args,**kwargs)
        except BaseException as exc:
            record.update(status='FAILED',exception_type=type(exc).__name__,message=str(exc));self.ctx['w'].write('RESOURCE_EVENTS.jsonl',json.dumps(record,separators=(',',':'))+'\n',append=True);raise
        record['status']='RETURNED';self.ctx['w'].write('RESOURCE_EVENTS.jsonl',json.dumps(record,separators=(',',':'))+'\n',append=True);self.check();return out
    def estimator(self,kind):
        require(kind=='MODEL_OBSERVATION_WLS','POLICY_WLS_PROHIBITED');return lambda payload:self.invoke('observation_wls',self.estimate,payload)
    def solver(self,*args,**kwargs):return self.invoke('solver',self.original_solver,*args,**kwargs)
    def choose(self,*args,**kwargs):raise RuntimeError('R_AND_ASSIGNMENT_OPTIMIZATION_PROHIBITED')

def branch_physical(b):
    return dict(positions=b.positions.copy(),actions=copy.deepcopy(b.actions),status=copy.deepcopy(b.status),components=copy.deepcopy(b.components),change_cost=b.change_cost,events=copy.deepcopy(b.events),clocks={j:None if b.segment(j) is None else copy.deepcopy(b.segment(j)['latest_clock']) for j in b.targets},endpoints={j:None if b.segment(j) is None else copy.deepcopy(b.segment(j)['latest_endpoint']) for j in b.targets})
def stripped_history(b):
    h=copy.deepcopy(b.histories)
    for row in h.values():
        for s in row['segments']:s.pop('first_fusion_tick',None)
    return h

def make_fixed_branch(Base):
    class FixedBranch(Base):
        def run(self,*args,**kwargs):raise RuntimeError('ORIGINAL_R_RUN_PROHIBITED')
        def policy_view(self):
            bindings={}
            for i,f in enumerate(self.feedback):
                row=dict(source='MODEL',provenance='SIMULATED',observation_origin='MODEL',target_id=f['frame']['target_id'],measurement_tick=f['frame']['tick'],available_tick=round(f['frame']['available_time']/.05),estimate=copy.deepcopy(f['result']['estimate_result']))
                bindings.setdefault(digest(row),[]).append(dict(frame_id=f['frame']['frame_id'],ordinal=i))
            self.consumer._bindings=bindings;before=branch_physical(self);v=super().policy_view();require(typed(branch_physical(self))==typed(before),'FREEZE_PHYSICAL_SERVICE_CHANGED');return v
        def fixed_run(self,initial):
            self.assign(copy.deepcopy(initial));self.hold_checks=[]
            while self.tick<120:
                self.advance()
                if self.tick in (80,100):
                    v=self.policy_view();self.decisions.append(dict(mode='FIXED_ACTION_HOLD',optimization_called=False,view=copy.deepcopy(v)));before=branch_physical(self);hbefore=stripped_history(self);old_first={j:None if self.segment(j) is None else self.segment(j)['first_fusion_tick'] for j in self.targets};current=copy.deepcopy(self.actions);self.assign(current)
                    require(typed(branch_physical(self))==typed(before) and typed(stripped_history(self))==typed(hbefore),'FIXED_HOLD_CHANGED_PHYSICAL_OR_HISTORY');require(self.boundaries[-1]['changes']==0 and self.boundaries[-1]['cost']==0,'HOLD_RECHARGE')
                    self.hold_checks.append(dict(tick=self.tick,mode='FIXED_ACTION_HOLD',physical_service_continuity='VERIFIED',freeze_view_saved=True,first_fusion_before=old_first,first_fusion_after={j:None if self.segment(j) is None else self.segment(j)['first_fusion_tick'] for j in self.targets},no_R=True,no_assignment_optimizer=True))
            net=sum(self.components.values())-self.change_cost
            return dict(branch=self.name,world=copy.deepcopy(self.world),provenance='SIMULATED',observation_origin='MODEL',components=copy.deepcopy(self.components),change_cost=self.change_cost,net=net,frames=copy.deepcopy(self.frames),events=copy.deepcopy(self.events),boundaries=copy.deepcopy(self.boundaries),decisions=copy.deepcopy(self.decisions),feedback=copy.deepcopy(self.feedback),status=copy.deepcopy(self.status),raw_counts=self.cache.counts,endpoint_fusions=self.fusions)
    return FixedBranch


def bootstrap(w,clock):
    require(Path(sys.executable).resolve()==Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\python.exe').resolve(),'INTERPRETER_IDENTITY')
    site=Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\Lib\site-packages');sys.path.insert(0,str(site));pins=read(H/'HISTORICAL_IDENTITY.json');guard=HistoricalImports(H/'historical',pins);guard.install()
    import importlib,numpy,scipy
    original_proxy=importlib.import_module('research.non_oracle.stfbs_lite_proxy');from research.non_oracle.stfbs_d1a_state import ModelBeliefConsumer
    require(numpy.__version__=='2.1.3' and scipy.__version__=='1.15.3','NUMERICAL_ENVIRONMENT')
    for module in (numpy,scipy):require(Path(module.__file__).resolve().is_relative_to(site.resolve()),'NUMERICAL_ORIGIN')
    protections={};sources={}
    names={'model':'research/non_oracle/stfbs_d1a_model.py','proxy':'research/non_oracle/stfbs_lite_proxy.py','verify':'research/non_oracle/stfbs_d1a_verify.py','audit':'research/non_oracle/stfbs_d1a_audit.py','belief':'research/non_oracle/belief.py','estimator':'research/cooperative_sensing/estimator.py'}
    for key,rel in names.items():
        p=H/'historical'/rel;require(sha(p)==pins[rel]['sha256'],'HISTORICAL_SOURCE_SHA/'+rel);sources[key]=p.read_text(encoding='utf-8');protections[str(p)]=sha(p)
    mapping=read(S/'MODEL_WORLD_MAPPING.json');base_model=copy.deepcopy(mapping['H3']);base_proxy=copy.deepcopy(mapping['STFBS']['H3']);base_model['motion']={int(k):v for k,v in base_model['motion'].items()};base_proxy['motion']={int(k):v for k,v in base_proxy['motion'].items()}
    require(base_model['perturbation']['stfbs_world_digest']==base_proxy['world_digest'],'H3_WORLD_MAPPING');bindings=read(P/'INPUT_BINDINGS.json');require(all(x['original_world_digest']==base_proxy['world_digest'] for x in bindings if x['cell'].startswith('H3_')),'ACCEPTED_H3_BINDING')
    raw_public=read(S/'PUBLIC_INPUT_FREEZE.json');auth=read(S/'H3_KEEP/authorization.json');candidate_path=Path(auth['candidate_path']);candidate=read(candidate_path)['candidate'];view=copy.deepcopy(candidate['a2_policy_view']);seed=copy.deepcopy(candidate['consumer_seed'])
    require(digest(seed)==read(S/'S4_STATIC.json')['seed_digest'],'D60_SEED_IDENTITY')
    view['beliefs']={int(k):v for k,v in view['beliefs'].items()}
    for k in ('internal_states_at_D60','accepted_position_history','accepted_receipts'):seed[k]={int(j):v for j,v in seed[k].items()}
    require(digest(view)==base_model['public_digest'],'HF_PUBLIC_D60_IDENTITY');require(not seed['pending_observations'],'INITIAL_PENDING_UNSUPPORTED')
    from pursuit_v2.service import ServiceState
    def make_proxy_view():
        v=copy.deepcopy(raw_public)
        for k in ('beliefs','service_states','current_endpoints','current_q','public_profiles'):v[k]={int(j):x for j,x in v[k].items()}
        for ep in v['current_endpoints'].values():
            if ep is not None:ep['team']=tuple(tuple(p) for p in ep['team'])
        v['service_states']={j:ServiceState(base=x['base'],intervals=x['intervals'],team=tuple(tuple(y) for y in x['team'])) for j,x in v['service_states'].items()};return v
    require(original_proxy.public_input_digest(make_proxy_view())==base_proxy['public_input_digest'],'PROXY_PUBLIC_D60_IDENTITY')
    v0=list(base_model['motion'][0]['velocity']);p0=list(base_model['motion'][0]['position']);theta=.5;v1=[math.cos(theta)*v0[0]-math.sin(theta)*v0[1],math.sin(theta)*v0[0]+math.cos(theta)*v0[1]]
    spec=dict(name='H4_TURN_T0',base_world='H3',base_model_world_digest=base_model['world_digest'],base_proxy_world_digest=base_proxy['world_digest'],target_id=0,position_D60=p0,velocity_before=v0,turn_tick=75,turn_angle_radians=theta,velocity_after=v1,dt=.05,start_tick=60,end_tick=120,position_convention='continuous; D75 endpoint from pre-turn segment',velocity_convention='right-continuous: v1 at D75',HF_public_digest=base_model['public_digest'],proxy_public_digest=base_proxy['public_input_digest'],public_motion_model='constant_velocity (unchanged; mismatch diagnostic)');spec['physics_digest']=digest(spec)
    model=copy.deepcopy(base_model);model.update(motion_rule='H4_PIECEWISE_CV_SINGLE_TURN_MODEL_V1',h4_kind='MODEL',turn_spec=copy.deepcopy(spec),perturbation=dict(base_world='H3',base_digest=base_model['world_digest'],physics_digest=spec['physics_digest'],diagnostic='PUBLIC_MOTION_MODEL_MISMATCH_DIAGNOSTIC'));model.pop('world_digest');model['world_digest']=world_digest(model)
    proxy=copy.deepcopy(base_proxy);proxy.update(generation_rule='H4_PIECEWISE_CV_SINGLE_TURN_PROXY_V1',h4_kind='PROXY',turn_spec=copy.deepcopy(spec),is_h1=False,world_ordinal=0);proxy.pop('world_digest');proxy['world_digest']=world_digest(proxy)
    require(model['world_digest']!=base_model['world_digest'] and proxy['world_digest']!=base_proxy['world_digest'],'H4_IDENTITY_NOT_NEW')
    adapted={'model_h4.py':adapt_model(sources['model']),'proxy_h4.py':adapt_proxy(sources['proxy']),'verify_h4.py':adapt_verify(sources['verify']),'audit_h4.py':adapt_audit(sources['audit']),'consumer_freeze_observer.py':recorded_freeze_source(sources['belief'])}
    for n,text in adapted.items():ast.parse(text);w.write(n,text)
    freeze_ns=isolated(adapted['consumer_freeze_observer.py'],'consumer_freeze_observer',dict(deepcopy=copy.deepcopy,math=math));consumer=make_consumer(ModelBeliefConsumer,freeze_ns['recorded_freeze'])
    model_ns=isolated(adapted['model_h4.py'],'model_h4',dict(_h4_point=point,_velocity_at=velocity_at,_escape_time=escape_time));model_ns['ModelBeliefConsumer']=consumer;Branch=make_fixed_branch(model_ns['Branch'])
    kernel,proxy_ns=build_kernel(adapted['proxy_h4.py']);proxy_ns.update(point=point,_velocity_at=velocity_at,_escape_time=escape_time,world_digest=world_digest,WORLD_RULE_VERSION='H4_PIECEWISE_CV_SINGLE_TURN_PROXY_V1',certificate=lambda *a,**k:dict(status='NOT_CERTIFIED',certificate_role='DIAGNOSTIC_ONLY',reason='piecewise motion certificate not assessed'))
    verify_ns=isolated(adapted['verify_h4.py'],'verify_h4',dict(_h4_point=point,_escape_time=escape_time));audit_ns=isolated(adapted['audit_h4.py'],'audit_h4',dict(_h4_point=point))
    checks={};representative=(60,74,75,76,80,100,120);zero=copy.deepcopy(model);zero['turn_spec']['velocity_after']=v0;zero['turn_spec']['turn_angle_radians']=0.
    zero_errors=[]
    for k in representative:
        expected=numpy.asarray(p0)+numpy.asarray(v0)*((k-60)*.05);zero_errors.append(float(numpy.max(numpy.abs(point(zero,0,k)-expected))));require(zero_errors[-1]<=1e-10,'ZERO_TURN_REDUCTION');require(numpy.array_equal(point(model,0,k),point(proxy,0,k)),'MODEL_PROXY_PHYSICS_MAPPING');require(numpy.array_equal(point(model,1,k),numpy.asarray(base_model['motion'][1]['position'])+numpy.asarray(base_model['motion'][1]['velocity'])*((k-60)*.05)),'T1_CHANGED')
    require(numpy.array_equal(point(model,0,75),numpy.asarray(p0)+numpy.asarray(v0)*.75),'D75_CONTINUITY');require(velocity_at(model,0,75)==v1 and velocity_at(model,0,74)==v0,'RIGHT_CONTINUOUS_VELOCITY');require(abs(math.hypot(*v1)-math.hypot(*v0))<=1e-10,'SPEED_CHANGED');require(abs(math.atan2(v1[1],v1[0])-math.atan2(v0[1],v0[0])-.5)<=1e-10,'TURN_DIRECTION')
    for side in (9.3,9.6,20.):
        escape=escape_time(model,0,3.,side);require(abs(point(model,0,escape/.05)[0]-side)<=1e-10,'PIECEWISE_ESCAPE_TIME')
    def function_dump(text,name,cls=None):
        tree=ast.parse(text);nodes=tree.body if cls is None else next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==cls).body;return ast.dump(next(n for n in nodes if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
    protected_methods=['__init__','raw','fuse','finish','policy_view','assign']
    require(all(function_dump(sources['model'],n,'Branch')==function_dump(adapted['model_h4.py'],n,'Branch') for n in protected_methods),'PROTECTED_HF_METHOD_CHANGED');require(function_dump(sources['proxy'],'ledger')==function_dump(adapted['proxy_h4.py'],'ledger'),'ECONOMIC_FUNCTION_CHANGED');require(function_dump(sources['audit'],'audit')==function_dump(adapted['audit_h4.py'],'audit'),'PHYSICAL_ECONOMIC_AUDIT_CHANGED')
    checks=dict(status='PASS',V1=dict(zero_turn_max_position_error=max(zero_errors),representative_ticks=representative,D75_position_continuous=True,right_continuous_velocity=True,speed_and_angle=True,T1_unchanged=True,piecewise_escape_checked=True),V2=dict(D60_HF_public_digest=base_model['public_digest'],D60_proxy_public_digest=base_proxy['public_input_digest'],physics_digest=spec['physics_digest'],new_world_digests=True,controls_receive_beliefs_not_world=True),V3=dict(original_WLS_source_sha256=pins[names['estimator']]['sha256'],HF_protected_methods_identical=protected_methods,proxy_ledger_identical=True,HF_physical_economic_audit_identical=True,consumer_math='original freeze body with observational try/finally only',same_action_hold='checked on actual HF runtime',R_and_assignment_optimization='not called; budget.choose prohibited'))
    for p in (candidate_path,S/'PUBLIC_INPUT_FREEZE.json',S/'MODEL_WORLD_MAPPING.json',S/'CANDIDATE_FREEZE.json',P/'P1_RESULTS.json',B/'P2_RESULTS.json',B/'SCIENTIFIC_ANALYSIS.json',B/'L3_B_FINAL_INDEPENDENT_SCIENTIFIC_ACCEPTANCE.md',REPO/'pursuit_v2/policies.py'):protections[str(p)]=sha(p)
    ctx=dict(w=w,clock=clock,pins=pins,guard=guard,sources=sources,adapted=adapted,model=model,proxy=proxy,spec=spec,view=view,seed=seed,make_proxy_view=make_proxy_view,Branch=Branch,kernel=kernel,proxy_ns=proxy_ns,verify=verify_ns['verify'],audit=audit_ns['audit'],service_audit=audit_ns['service_audit'],counts=dict(observation_wls=0,solver=0),HF={},CAP={},NOCAP={},traces={},HF_started=0,proxy_started=0,failures=[],protected=protections,validation=checks,candidates=read(S/'CANDIDATE_FREEZE.json'),H3_HF={r['action']:r['HF'] for r in read(P/'P1_METRICS.json')['cells'] if r['world']=='H3'},H3_CAP={n[3:]:v for n,v in read(P/'P1_RESULTS.json').items() if n.startswith('H3_')},H3_NOCAP=read(B/'P2_RESULTS.json')['H3_KEEP'])
    w.json('WORLD_H4.json',dict(physical_definition=spec,MODEL_world=plain(model),PROXY_world=plain(proxy),D60_PUBLIC_MOTION_MODEL='constant_velocity',interpretation='PUBLIC_MOTION_MODEL_MISMATCH_DIAGNOSTIC'));w.json('MINIMAL_VALIDATION.json',checks)
    w.json('EXPERIMENT_CONFIG.json',dict(task='STFBS_LITE_TARGET_TURN_EXPLORATION_001',specification='V1.0_WITH_REVIEW_ADDENDUM',git_head=HEAD,historical_commit='98ed1160d9aba266d36cc263d95cfbeecef865e9',entry_sha256=sha(__file__),adapted_source_sha256={n:sha(HERE/n) for n in adapted},source_references={key:dict(path=str(H/'historical'/rel),**pins[rel]) for key,rel in names.items()},D60_candidate_path=str(candidate_path),D60_candidate_sha256=sha(candidate_path),limits=dict(cpu=300,wall=1800,logical_writes=536870912,HF=3,proxy=4,observation_wls_per_HF=63,observation_wls_total=189,solver_per_HF=600,solver_total=1800,policy_WLS=0,R=0,assignment_solver=0,ACTUAL_STEP=0,ACTUAL_WLS=0),environment=dict(python=sys.executable,version=sys.version,numpy=dict(version=numpy.__version__,path=numpy.__file__),scipy=dict(version=scipy.__version__,path=scipy.__file__)),world_generation='one deterministic rotation; no random seed',HF_boundary='policy_view freeze then FIXED_ACTION_HOLD assign; full view retained in decisions without fake choice',certificate='NOT_CERTIFIED; no CV certificate asserted',counterfactuals='3 HF, 3 CAP, 1 NoCap KEEP only'))
    return ctx

def feedback_metrics(branch,result):
    events=branch.consumer.recorded_events;frames=result['feedback'];out={}
    for j in branch.targets:
        generated=[f for f in frames if f['frame']['target_id']==j];after=[f for f in generated if f['frame']['tick']>=75];post=[f for f in generated if f['frame']['tick']>75 and not rejection(dict(estimate=f['result']['estimate_result'],measurement_tick=f['frame']['tick']),[])]
        def descriptor(f):
            if f is None:return None
            linked=[e for e in events if e['frame_id']==f['frame']['frame_id']];return dict(frame_id=f['frame']['frame_id'],measurement_tick=f['frame']['tick'],available_tick=round(f['frame']['available_time']/.05),quality=f['result']['quality']['status'],consumer_records=linked,truth_position=point(result['world'],j,f['frame']['tick']).tolist(),truth_velocity=velocity_at(result['world'],j,f['frame']['tick']))
        out[j]=dict(first_measurement_at_or_after_D75=descriptor(after[0] if after else None),first_quality_valid_position_strictly_after_D75=descriptor(post[0] if post else None),definition='quality-valid means original consumer estimate flags; actual service Q and acceptance recorded separately',reference_intervals=[e for e in events if e['target']==j],turn_boundary='D75 position contains pre-turn displacement; instantaneous velocity right-continuous')
    return out

def actual_control_records(ctx,result,kind,no_cap=False):
    records=[]
    if kind=='HF':
        frozen=ctx['view']['beliefs'];views={d['view']['tick']:d['view'] for d in result['decisions']};bounds={b['tick']:b['after'] for b in result['boundaries']};actions=copy.deepcopy(ctx['view']['assignment'])
        from research.non_oracle.belief import trajectory
        for frame in result['frames']:
            t=frame['tick']-1
            if t in views:frozen=views[t]['beliefs']
            if t in bounds:actions=bounds[t]
            for i,a in enumerate(actions):
                if a['target'] is None or frame['elapsed'][i]<=0:continue
                j=a['target'];b=frozen[j];p,v=trajectory(b,t);records.append(control_row(ctx['model'],b,t,i,p,v,frame['control'][i],no_cap=False))
    else:
        for r in result:records.append(control_row(ctx['proxy'],dict(target_id=r['target'],estimate_tick=r['estimate_tick'],available_tick=r['available_tick'],last_observation_tick=r['last_observation_tick'],position_estimate=r['estimate_position'],velocity_estimate=r['estimate_velocity'],source=r['source'],velocity_source=r['velocity_source']),r['tick'],r['robot_ids'][0],r['position_prediction'],r['velocity_prediction'],r['control'][0],no_cap=no_cap))
    return records

def control_row(world,b,t,robot,p,v,u,no_cap):
    j=b['target_id'];truth=point(world,j,t);instant=velocity_at(world,j,t);et=b['estimate_tick'];estate=point(world,j,et) if et>=60 else None;ev=velocity_at(world,j,et) if et>=60 else None
    return dict(target=j,tick=t,robot_id=robot,estimate_tick=et,last_observation_tick=b['last_observation_tick'],propagation_age=(t-et)*.05,observation_age=None if b['last_observation_tick'] is None else (t-b['last_observation_tick'])*.05,belief_position=list(b['position_estimate']),belief_velocity=list(b['velocity_estimate']),source=b['source'],velocity_source=b['velocity_source'],prediction_position=list(p),prediction_velocity=list(v),truth_position=truth.tolist(),truth_velocity=instant,position_error=math.dist(p,truth),velocity_error=math.dist(v,instant),estimation_position_error=None if estate is None else math.dist(b['position_estimate'],estate),estimation_velocity_error=None if ev is None else math.dist(b['velocity_estimate'],ev),estimation_reference='NOT_IDENTIFIABLE_BEFORE_D60' if estate is None else 'H4_WORLD_RIGHT_CONTINUOUS',cap_applied=not no_cap and b['last_observation_tick'] is not None and (t-et)*.05>1.,control=list(u))

def run_hf(ctx,action):
    w,clock=ctx['w'],ctx['clock'];clock.check();require(ctx['HF_started']<3,'HF_BRANCH_START_LIMIT');ctx['HF_started']+=1;name='H4_HF_'+action;w.json('CALLS/'+name+'_STARTED.json',dict(cell=name,mode='MODEL',input_sha256=fingerprint([ctx['view'],ctx['seed'],ctx['model']]),state='STARTED'));budget=TaskBudget(ctx,name,ctx['sources']['estimator']);branch=None
    try:
        branch=ctx['Branch'](copy.deepcopy(ctx['view']),copy.deepcopy(ctx['seed']),copy.deepcopy(ctx['model']),name,budget);actions=copy.deepcopy(next(c['actions'] for c in ctx['candidates'] if c['kind']==action));result=branch.fixed_run(actions);w.json('RAW/'+name+'.json',plain(result))
        from research.non_oracle.stfbs_d1a_history_audit import audit_branch_independent
        audits=dict(history=audit_branch_independent(branch,context=branch._audit_context),control_and_freeze_views=ctx['verify'](result,ctx['view'],ctx['seed'],audit_context=branch._audit_context),service=ctx['service_audit'](result,ctx['view']),physical_economic=ctx['audit'](result,ctx['view']))
        require(all(x['status']=='PASS' for x in audits.values()),'HF_SCIENTIFIC_AUDIT');require(len(result['frames'])==60 and result['frames'][-1]['tick']==120 and len(result['decisions'])==2,'HF_HORIZON');require(budget.counts['observation_wls']==len(result['feedback'])==branch.fusions,'OBSERVATION_COUNT_DISAGREEMENT')
        control=actual_control_records(ctx,result,'HF');terminal=dict(states=branch.consumer.states,history=branch.consumer.history,accepted_receipts=branch.consumer.accepted_receipts,pending=branch.consumer.pending,consumed=branch.consumer.consumed,events=branch.consumer.recorded_events)
        w.json('TRACE/'+name+'.json',plain(dict(control_records=control,feedback_response=feedback_metrics(branch,result),freeze_views=result['decisions'],hold_checks=branch.hold_checks,consumer_terminal=terminal,physical_history=branch.histories,resource_counts=budget.counts,audits=audits,interpretation='HF physical observations and WLS are MODEL; fixed holds are state transactions, not optimization calls')))
        ctx['HF'][action]=result;ctx['traces'][name]=dict(control_records=control,raw=result);return result
    except BaseException as exc:
        w.json('RAW/'+name+'_FAILURE.json',dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),resource_counts=budget.counts,tick=None if branch is None else branch.tick))
        if branch is not None:w.json('RAW/'+name+'_PARTIAL.json',plain(dict(frames=branch.frames,feedback=branch.feedback,events=branch.events,boundaries=branch.boundaries,decisions=branch.decisions,status=branch.status,consumer_events=branch.consumer.recorded_events)))
        raise

def run_proxy(ctx,action,no_cap=False):
    w,clock=ctx['w'],ctx['clock'];clock.check();require(ctx['proxy_started']<4,'PROXY_CELL_START_LIMIT');ctx['proxy_started']+=1;kind='NOCAP' if no_cap else 'CAP';name='H4_'+kind+'_'+action;view=ctx['make_proxy_view']();world=copy.deepcopy(ctx['proxy']);actions=copy.deepcopy(next(c['actions'] for c in ctx['candidates'] if c['kind']==action));initial=typed(view['beliefs']);trace=TraceRecorder();controls=[];boundaries=[];cmd=controller(ctx['proxy_ns'],no_cap,controls,actions=actions)
    def command(*a):clock.check();return cmd(*a)
    def boundary(t,v,physical):
        clock.check();before=plain(physical);invoked=[]
        def noop():invoked.append(t)
        check=boundary_check(t,v,physical,operation=noop);require(invoked==[t],'PROXY_BOUNDARY_NOT_EXECUTED');check.update(before=before,after=plain(physical));boundaries.append(check)
    def record(s):clock.check();trace(s)
    w.json('CALLS/'+name+'_STARTED.json',dict(cell=name,input_sha256=fingerprint([view,actions,world]),no_cap=no_cap,state='STARTED'))
    try:
        result=ctx['kernel'](view,actions,world,command,boundary,record);w.json('RAW/'+name+'.json',plain(result));ledger_check(result['ledger'],result['value']);require(typed(view['beliefs'])==initial,'PROXY_BELIEF_CHANGED');require(len(trace.rows)==60 and trace.rows[-1]['tick']==120 and [x['tick'] for x in boundaries]==[80,100],'PROXY_HORIZON_BOUNDARY');records=actual_control_records(ctx,controls,kind,no_cap=no_cap);ctx[kind][action]=result;ctx['traces'][name]=dict(control_records=records,frames=plain(trace.rows),raw=result)
        return result
    finally:w.json('TRACE/'+name+'.json',plain(dict(frames=trace.rows,controls=controls,boundaries=boundaries,control_records=actual_control_records(ctx,controls,kind,no_cap=no_cap),Q_semantics='optimistic unknown proxy Q; not observed PASS')))


def unique_prediction_rows(rows):
    indexed={};counts={}
    for r in rows:
        key=(r['target'],r['tick']);counts[key]=counts.get(key,0)+1
        if key in indexed:require(all(indexed[key][k]==r[k] for k in ('prediction_position','prediction_velocity','position_error','velocity_error')),'ROBOT_WEIGHTING_AMBIGUITY')
        else:indexed[key]=r
    return indexed,counts

def summarize_prediction(rows):
    idx,robot_counts=unique_prediction_rows(rows);out={}
    for target in sorted({j for j,t in idx}):
        group=[r for (j,t),r in sorted(idx.items()) if j==target];out[target]=dict(denominator_target_ticks=len(group),robot_control_record_count=sum(n for (j,t),n in robot_counts.items() if j==target),valid_control_ticks=[r['tick'] for r in group],valid_interval=None if not group else [group[0]['tick'],group[-1]['tick']],mean_position_error=None if not group else sum(r['position_error'] for r in group)/len(group),mean_velocity_error=None if not group else sum(r['velocity_error'] for r in group)/len(group),segments={label:dict(denominator=sum(lo<=r['tick']<hi for r in group),mean_position_error=None if not any(lo<=r['tick']<hi for r in group) else sum(r['position_error'] for r in group if lo<=r['tick']<hi)/sum(lo<=r['tick']<hi for r in group),mean_velocity_error=None if not any(lo<=r['tick']<hi for r in group) else sum(r['velocity_error'] for r in group if lo<=r['tick']<hi)/sum(lo<=r['tick']<hi for r in group)) for label,lo,hi in [('D60_before_D75',60,75),('D75_before_D80',75,80),('D80_before_D100',80,100),('D100_before_D120',100,120)]})
    return dict(targets=out,weighting='one record per target and control tick; multiple robots verified identical prediction then deduplicated; no post-control interpolation')
def pair_prediction(a,b,target=0):
    ia,_=unique_prediction_rows(a);ib,_=unique_prediction_rows(b);keys=sorted(k for k in ia.keys()&ib.keys() if k[0]==target)
    return dict(status='NOT_IDENTIFIABLE' if not keys else 'VALID_COMMON_CONTROL_TICKS',target=target,common_ticks=[t for j,t in keys],denominator=len(keys),a_mean_position_error=None if not keys else sum(ia[k]['position_error'] for k in keys)/len(keys),b_mean_position_error=None if not keys else sum(ib[k]['position_error'] for k in keys)/len(keys),a_mean_velocity_error=None if not keys else sum(ia[k]['velocity_error'] for k in keys)/len(keys),b_mean_velocity_error=None if not keys else sum(ib[k]['velocity_error'] for k in keys)/len(keys),paired_rows=[dict(tick=k[1],a_position_error=ia[k]['position_error'],b_position_error=ib[k]['position_error'],a_velocity_error=ia[k]['velocity_error'],b_velocity_error=ib[k]['velocity_error']) for k in keys],interpretation='prediction error comparison only; completion/value retain each full rollout horizon')
def historical_row(world,b,t,i,p,v,u):
    import numpy as np
    j=b['target_id'];m=world['motion'][j];truth=np.asarray(m['position'])+np.asarray(m['velocity'])*((t-60)*.05)
    return dict(target=j,tick=t,robot_id=i,prediction_position=list(p),prediction_velocity=list(v),position_error=math.dist(p,truth),velocity_error=math.dist(v,m['velocity']),control=list(u),reference='archived H3 actual freeze view/control time; no re-simulation')
def historical_controls(ctx,kind,action):
    from research.non_oracle.belief import trajectory
    if kind=='HF':
        raw=read(S/('H3_'+action)/'BRANCH_RAW.json');world=copy.deepcopy(raw['world']);world['motion']={int(k):v for k,v in world['motion'].items()};views={d['view']['tick']:d['view'] for d in raw['decisions']};bounds={b['tick']:b['after'] for b in raw['boundaries']};frozen=ctx['view']['beliefs'];actions=copy.deepcopy(ctx['view']['assignment']);out=[]
        for f in raw['frames']:
            t=f['tick']-1
            if t in views:frozen={int(k):v for k,v in views[t]['beliefs'].items()}
            if t in bounds:actions=bounds[t]
            for i,a in enumerate(actions):
                if a['target'] is None or f['elapsed'][i]<=0:continue
                b=frozen[a['target']];p,v=trajectory(b,t);out.append(historical_row(world,b,t,i,p,v,f['control'][i]))
        return out
    path=P/'TRACE'/('H3_'+action+'.json') if kind=='CAP' else B/'TRACE'/('P2_H3_'+action+'.json');trace=read(path);world=copy.deepcopy(read(S/'MODEL_WORLD_MAPPING.json')['H3']);world['motion']={int(k):v for k,v in world['motion'].items()};out=[]
    for r in trace['controls']:
        b=dict(target_id=r['target']);out.append(historical_row(world,b,r['tick'],r['robot_ids'][0],r['position_prediction'],r['velocity_prediction'],r['control'][0]))
    return out

def proxy_outcome(out,action):
    j='1' if action=='SWITCH' else '0';tasks=plain(out['tasks']);t=tasks[j]
    return dict(P0=t['P0'],Pmax=t['Pmax'],NG=t['NG'],completion_tick=t['completion_tick'],stop_time=t['stop_time'],value=out['value'],economics=out['ledger'],release='NOT_APPLICABLE: proxy control stop is not Assignment release')
def hf_outcome(ctx,action):
    raw=ctx['HF'][action];j=1 if action=='SWITCH' else 0;duration=next(t['service_duration'] for t in ctx['view']['targets'] if t['id']==j);clocks=[f['clocks'][j] for f in raw['frames'] if f['clocks'][j] is not None];peaks=[math.fsum((s['base'],s['intervals']*.05)) for s in clocks];terminal=next(e for e in raw['events'] if e['target']==j and e['kind'] in ('completed','escaped','unfinished'))
    if terminal['kind']=='completed':peaks.append(duration)
    init=next(h for h in ctx['view']['histories'] if h['target_id']==j);seg=next((s for s in init['segments'] if s['segment_id']==init['active_segment_id']),None);inherited=tuple((m['robot_id'],m['role']) for m in seg['team']) if seg else ();requested=tuple((i,a['role']) for i,a in enumerate(next(c['actions'] for c in ctx['candidates'] if c['kind']==action)) if a['target']==j);p0=0. if inherited!=requested or seg is None else math.fsum((seg['latest_clock']['base'],seg['latest_clock']['intervals']*.05))
    selected=[f for f in raw['feedback'] if f['frame']['target_id']==j];previous=copy.deepcopy(seg['latest_endpoint']) if seg is not None and inherited==requested else None;ng=0;qualified=0
    for f in selected:
        right=f['endpoint']
        if f['frame']['tick']==60:previous=right;continue
        if previous is not None:
            ng+=int(previous['G'] and right['G']);qualified+=int(previous['G'] and right['G'] and previous['quality']['status']==right['quality']['status']=='PASS')
        previous=right
    return dict(P0=p0,Pmax=max([p0]+peaks),NG=ng,effective_service_intervals=qualified,completion_tick=terminal['tick'] if terminal['kind']=='completed' else None,terminal=terminal,net=raw['net'],raw_signed_components=raw['components'],change_cost=raw['change_cost'],positive_cost_ledger=dict(completion=raw['components']['completion'],flow=-raw['components']['flow'],late=-raw['components']['late'],effort=-raw['components']['effort'],terminal=-raw['components']['terminal'],change=raw['change_cost']),resets=[e for e in raw['events'] if e['target']==j and e['kind']=='reset'],assignment_transactions=raw['boundaries'],freeze_mode='FIXED_ACTION_HOLD')
def ranking(values):
    if not all(a in values for a in ACTIONS):return dict(status='NOT_IDENTIFIABLE',available=values)
    best=max(values.values());return dict(status='VALID',values=values,strict_order=sorted(ACTIONS,key=lambda a:-values[a]),exact_best=[a for a in ACTIONS if values[a]==best],epsilon_best=[a for a in ACTIONS if best-values[a]<=1e-8],pairwise={a+'-'+b:values[a]-values[b] for a,b in itertools.combinations(ACTIONS,2)})

def analyze(ctx):
    w=ctx['w'];matrix={a:dict(H3_HF=ctx['H3_HF'][a],H3_CAP=ctx['H3_CAP'][a]['value'],H4_HF=None if a not in ctx['HF'] else ctx['HF'][a]['net'],H4_CAP=None if a not in ctx['CAP'] else ctx['CAP'][a]['value']) for a in ACTIONS};w.json('VALUE_MATRIX.json',matrix)
    hf4={a:r['net'] for a,r in ctx['HF'].items()};cap4={a:r['value'] for a,r in ctx['CAP'].items()};hf_rank=ranking(hf4);cap_rank=ranking(cap4);h3_rank=ranking(ctx['H3_HF']);pairs=sorted(set(hf4)&set(cap4));errors={a:dict(signed_error=cap4[a]-hf4[a],AE=abs(cap4[a]-hf4[a])) for a in pairs};mae=None if len(pairs)!=3 else sum(r['AE'] for r in errors.values())/3
    regret=None
    if hf_rank['status']==cap_rank['status']=='VALID':regret={a:max(hf4.values())-hf4[a] for a in cap_rank['epsilon_best']}
    conflict=None if hf_rank['status']!='VALID' or h3_rank['status']!='VALID' else set(hf_rank['epsilon_best']).isdisjoint(h3_rank['epsilon_best'])
    predicted={};paired={};outcomes={}
    for kind,container in [('HF',ctx['HF']),('CAP',ctx['CAP']),('NOCAP',ctx['NOCAP'])]:
        for action in container:
            ctx['clock'].check();key='H4_'+kind+'_'+action;rows=ctx['traces'][key]['control_records'];predicted[key]=summarize_prediction(rows);old=historical_controls(ctx,kind,action);predicted['H3_'+kind+'_'+action]=summarize_prediction(old);target=1 if action=='SWITCH' else 0;paired['H4_H3_'+kind+'_'+action]=pair_prediction(rows,old,target);outcomes[key]=hf_outcome(ctx,action) if kind=='HF' else proxy_outcome(container[action],action)
    if 'KEEP' in ctx['CAP'] and 'KEEP' in ctx['NOCAP']:paired['H4_NOCAP_CAP_KEEP']=pair_prediction(ctx['traces']['H4_NOCAP_KEEP']['control_records'],ctx['traces']['H4_CAP_KEEP']['control_records'],0)
    h3_cap=ctx['H3_CAP']['KEEP']['value'];h3_nocap=ctx['H3_NOCAP']['value'];keep=dict(H3_CAP=h3_cap,H3_NOCAP=h3_nocap,H3_HF=ctx['H3_HF']['KEEP'],NoCapEffect_H3=h3_nocap-h3_cap,NoCapEffect_H4=None,EffectDifference=None,HF_value_error_status='NOT_IDENTIFIABLE')
    if 'KEEP' in ctx['CAP'] and 'KEEP' in ctx['NOCAP']:
        c=ctx['CAP']['KEEP']['value'];n=ctx['NOCAP']['KEEP']['value'];keep.update(H4_CAP=c,H4_NOCAP=n,NoCapEffect_H4=n-c,EffectDifference=(n-c)-(h3_nocap-h3_cap))
        if 'KEEP' in hf4:keep.update(H4_HF=hf4['KEEP'],H4_CAP_AE=abs(c-hf4['KEEP']),H4_NOCAP_AE=abs(n-hf4['KEEP']),H4_Delta_AE=abs(n-hf4['KEEP'])-abs(c-hf4['KEEP']),H3_CAP_AE=abs(h3_cap-ctx['H3_HF']['KEEP']),H3_NOCAP_AE=abs(h3_nocap-ctx['H3_HF']['KEEP']),HF_value_error_status='VALID_KEEP_PAIR')
    cap_rows=ctx['traces'].get('H4_CAP_KEEP',{}).get('control_records',[]);ix,_=unique_prediction_rows(cap_rows);pre=[r for (j,t),r in ix.items() if j==0 and t<75];post=[r for (j,t),r in ix.items() if j==0 and t>=75]
    pre_mean=None if not pre else sum(r['position_error'] for r in pre)/len(pre);post_mean=None if not post else sum(r['position_error'] for r in post)/len(post)
    motion_finding=dict(status='NOT_IDENTIFIABLE' if not pre or not post else 'SUPPORTED_IN_TESTED_CASE' if post_mean>pre_mean+1e-10 else 'NOT_SUPPORTED_BY_POSITION_ERROR_GROWTH',pre_turn_position_error_mean=pre_mean,post_turn_position_error_mean=post_mean,pre_denominator=len(pre),post_denominator=len(post),diagnostic_numerical_threshold=1e-10,not_statistical_significance=True)
    responses={}
    for action,raw in ctx['HF'].items():
        rows=[]
        for d in raw['decisions']:
            t=d['view']['tick']
            for j,b in d['view']['beliefs'].items():
                p,v=prediction(b,t,False);rows.append(dict(freeze_tick=t,target=j,assigned=any(a['target']==j for a in d['view']['assignment']),estimate_tick=b['estimate_tick'],last_observation_tick=b['last_observation_tick'],belief_velocity=b['velocity_estimate'],true_velocity=velocity_at(ctx['model'],j,t),velocity_error=math.dist(b['velocity_estimate'],velocity_at(ctx['model'],j,t)),control_time_position_prediction_error=math.dist(p,point(ctx['model'],j,t)),propagation_age=(t-b['estimate_tick'])*.05))
        responses[action]=rows
    analysis=dict(motion_model_mismatch=motion_finding,HF_freeze_response=responses,matrix=matrix,H4_HF_ranking=hf_rank,H4_CAP_ranking=cap_rank,H3_HF_ranking=h3_rank,H3_H4_HF_optimum_conflict=conflict,H4_CAP_HF_errors=errors,H4_complete_three_cell_MAE=mae,paired_error_subset=dict(actions=pairs,denominator=len(pairs),mean_AE=None if not pairs else sum(errors[a]['AE'] for a in pairs)/len(pairs),status='COMPLETE' if len(pairs)==3 else 'PARTIAL_NOT_FULL_MAE'),H4_CAP_selected_HF_regret=regret,KEEP_comparison=keep,outcomes=outcomes,prediction_summaries=predicted,paired_prediction_comparisons=paired,limitations=['one deterministic right-continuous turn; no finite-acceleration claim','public constant-velocity model intentionally mismatched','fixed HF hold evaluates candidates, not dynamic R optimal policy','no feedback-off HF comparison; observed feedback response is descriptive','NoCap only KEEP: no full NoCap ranking, MAE or decision regret','prediction comparison uses common valid target/tick records; whole-horizon value/completion unchanged'])
    w.json('SCIENTIFIC_ANALYSIS.json',analysis);return analysis

def svgplot(parts,title,series,x,y,width,height):
    points=[(a,b) for label,data in series for a,b in data if b is not None];parts.append('<text x="%s" y="%s" font-size="14">%s</text>'%(x,y-12,html.escape(title)))
    if not points:return
    xmin=min(a for a,b in points);xmax=max(a for a,b in points);ymin=min(b for a,b in points);ymax=max(b for a,b in points);span=max(ymax-ymin,1e-9);ymin-=.08*span;ymax+=.08*span;colors={'TRUTH':'#111827','HF':'#16a34a','CAP':'#2563eb','NOCAP':'#ea580c'}
    parts.append('<path d="M %s %s V %s H %s" fill="none" stroke="#888"/>'%(x,y,y+height,x+width))
    for label,data in series:
        coords=' '.join('%.3f,%.3f'%(x+(a-xmin)/max(1e-9,xmax-xmin)*width,y+height-(b-ymin)/(ymax-ymin)*height) for a,b in data if b is not None);parts.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2"/>'%(coords,colors.get(label,'#9333ea')))
    parts.append('<text x="%s" y="%s" font-size="10">%.4g</text><text x="%s" y="%s" font-size="10">%.4g</text>'%(x-38,y+10,ymax,x-38,y+height,ymin))
def figures(ctx,analysis):
    def start(title,h):return ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="%s"><rect width="100%%" height="100%%" fill="white"/><g font-family="Arial,Microsoft YaHei,sans-serif"><text x="25" y="28" font-size="20">%s</text><text x="25" y="49" font-size="12">Truth black; HF green; CAP blue; NoCap orange. Actual valid control records only.</text>'%(h,html.escape(title))]
    p=start('H4 turn and actual control predictions',550);series=[('TRUTH',[(float(point(ctx['model'],0,t)[0]),float(point(ctx['model'],0,t)[1])) for t in range(60,121)])]
    for kind in ('HF','CAP','NOCAP'):
        tr=ctx['traces'].get('H4_'+kind+'_KEEP')
        if tr:
            ix,_=unique_prediction_rows(tr['control_records']);series.append((kind,[(r['prediction_position'][0],r['prediction_position'][1]) for (j,t),r in sorted(ix.items()) if j==0]))
    svgplot(p,'T0 x-y trajectory and control-time position predictions',series,85,90,800,350);ctx['w'].write('FIGURES/turn_prediction_response.svg',''.join(p)+'</g></svg>')
    p=start('KEEP service progress and control-time prediction error',650);s1=[];s2=[]
    for kind in ('HF','CAP','NOCAP'):
        tr=ctx['traces'].get('H4_'+kind+'_KEEP')
        if tr is None:continue
        ix,_=unique_prediction_rows(tr['control_records']);s2.append((kind,[(t,r['position_error']) for (j,t),r in sorted(ix.items()) if j==0]));data=[]
        if kind=='HF':
            raw=tr['raw'];dur=next(x['service_duration'] for x in ctx['view']['targets'] if x['id']==0)
            for f in raw['frames']:
                s=f['clocks'][0];val=dur if f['status'][0]=='completed' else None if s is None else math.fsum((s['base'],s['intervals']*.05));data.append((f['tick'],val))
        else:
            for f in tr['frames']:
                s=f['states']['0'];data.append((f['tick'],math.fsum((s['base'],s['intervals']*.05))))
        s1.append((kind,data))
    svgplot(p,'Service progress (seconds); completed HF uses recorded terminal event',s1,80,90,830,210);svgplot(p,'Position prediction error on each actual control interval',s2,80,375,830,210);ctx['w'].write('FIGURES/keep_service_error.svg',''.join(p)+'</g></svg>')
    p=start('H3/H4 values, prediction error and decision regret',570)
    for i,a in enumerate(ACTIONS):
        r=analysis['matrix'][a];p.append('<text x="30" y="%s" font-size="15">%s: H3 HF=%s CAP=%s | H4 HF=%s CAP=%s</text>'%(95+i*55,a,r['H3_HF'],r['H3_CAP'],r['H4_HF'],r['H4_CAP']))
    p.append('<text x="30" y="300" font-size="15">H4 CAP three-cell MAE: %s</text>'%analysis['H4_complete_three_cell_MAE']);p.append('<text x="30" y="345" font-size="15">H4 CAP selected HF regret: %s</text>'%html.escape(str(analysis['H4_CAP_selected_HF_regret'])));p.append('<text x="30" y="390" font-size="15">H3/H4 HF optimal-set conflict: %s</text>'%analysis['H3_H4_HF_optimum_conflict']);p.append('<text x="30" y="440" font-size="14">NoCap KEEP effect H3=%s H4=%s</text>'%(analysis['KEEP_comparison']['NoCapEffect_H3'],analysis['KEEP_comparison']['NoCapEffect_H4']));ctx['w'].write('FIGURES/value_error_decision.svg',''.join(p)+'</g></svg>')


def reconcile_resources(ctx):
    p=HERE/'RESOURCE_EVENTS.jsonl';rows=[] if not p.exists() else [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()];started={};closed={};counts=dict(observation_wls=0,solver=0)
    for r in rows:
        require(r['actual_source']=='MODEL','RESOURCE_SOURCE')
        if r['status']=='STARTED':require(r['call_id'] not in started,'RESOURCE_ID_REUSE');started[r['call_id']]=r;counts[r['resource']]+=1
        else:require(r['call_id'] in started and r['call_id'] not in closed and r['status'] in ('RETURNED','FAILED'),'RESOURCE_CLOSURE');closed[r['call_id']]=r
    require(counts==ctx['counts'],'RESOURCE_DISK_RUNTIME_DISAGREEMENT');require(set(started)==set(closed),'UNCLOSED_RESOURCE_CALL')
    result=dict(status='VERIFIED_CONTROLLED_CALL_ACCOUNTING',disk_starts=counts,runtime_starts=ctx['counts'],started=len(started),closed=len(closed),failed_calls=sum(r['status']=='FAILED' for r in closed.values()),source='MODEL',legacy_ACTUAL_SOLVER_START_used=False,policy_wls_calls=0,R_calls=0,assignment_optimization_calls=0,ACTUAL_STEP_calls=0,ACTUAL_WLS_calls=0)
    ctx['w'].json('RESOURCE_CALL_RECONCILIATION.json',result);return result

def worker():
    prep=read(HERE/'PREPARATION_ACCOUNTING.json');origin=float(sys.argv[-1]);clock=Clock(origin,cpu_limit=300,wall_limit=1800);w=Writer(HERE,limit=536870912,initial_written=prep['cumulative_logical_write_bytes'],clock=clock);ctx=None;fatal=None;analysis=None;reconciliation=None;plot_status='NOT_EXECUTED'
    try:
        clock.check();ctx=bootstrap(w,clock)
        for action in ACTIONS:run_hf(ctx,action)
        for action in ACTIONS:run_proxy(ctx,action,False)
        run_proxy(ctx,'KEEP',True)
    except BaseException as exc:
        fatal=dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc());w.json('FAILURE.json',fatal)
    if ctx is not None:
        clock.check()
        try:analysis=analyze(ctx)
        except Exception as exc:w.json('ANALYSIS_FAILURE.json',dict(type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc()));fatal=fatal or dict(type=type(exc).__name__,message='ANALYSIS/'+str(exc))
        try:reconciliation=reconcile_resources(ctx)
        except Exception as exc:w.json('RESOURCE_RECONCILIATION_FAILURE.json',dict(type=type(exc).__name__,message=str(exc)));fatal=fatal or dict(type=type(exc).__name__,message='RESOURCE_RECONCILIATION/'+str(exc))
        if analysis is not None:
            try:figures(ctx,analysis);plot_status='GENERATED_FROM_EXISTING_DATA'
            except Exception as exc:plot_status='NOT_COMPLETED: '+str(exc);w.json('FIGURE_LIMITATION.json',dict(message=str(exc)))
        protected={p:sha(p)==h for p,h in ctx['protected'].items()};w.json('PROTECTION_CHECK.json',dict(files=protected,unchanged=all(protected.values())));require(all(protected.values()),'HISTORICAL_ASSET_CHANGED');actual=ctx['guard'].audit();w.json('RUNTIME_IDENTITIES.json',dict(project_modules=actual,namespace_paths=ctx['guard'].namespace_paths,untriggered_lazy_imports='NOT_VERIFIED',local_adapted_sources={n:sha(HERE/n) for n in ctx['adapted']}))
    clock.check();hfstarted=0 if ctx is None else ctx['HF_started'];proxystarted=0 if ctx is None else ctx['proxy_started'];hfvalid=0 if ctx is None else len(ctx['HF']);proxyvalid=0 if ctx is None else len(ctx['CAP'])+len(ctx['NOCAP']);validity='VALID_SEVEN_CELL_EXPLORATORY_RESULT' if hfvalid==3 and proxyvalid==4 and fatal is None else 'PARTIAL_VALID_SCIENTIFIC_RESULTS' if hfvalid+proxyvalid else 'BLOCKED_NO_VALID_CELLS';counts=dict(observation_wls=None,solver=None) if ctx is None else ctx['counts']
    report=dict(task='STFBS_LITE_TARGET_TURN_EXPLORATION_001',git_head=HEAD,entry_sha256=sha(__file__),TURN_WORLD_IDENTITY='NOT_VERIFIED' if ctx is None else ctx['spec']['physics_digest'],MINIMAL_VALIDATION_STATUS='NOT_COMPLETED' if ctx is None else 'V1_V3_PASS_AND_V4_PASS' if hfvalid==3 and proxyvalid==4 and fatal is None else 'V1_V3_PASS_V4_PARTIAL_OR_FAILED',HF_STARTED_CELLS=hfstarted,HF_VALID_CELLS=hfvalid,PROXY_STARTED_CELLS=proxystarted,PROXY_VALID_CELLS=proxyvalid,TOTAL_STARTED_CELLS=hfstarted+proxystarted,TOTAL_VALID_CELLS=hfvalid+proxyvalid,resource_counts=counts,OBSERVATION_WLS_CALLS=counts['observation_wls'],SOLVER_STARTS=counts['solver'],POLICY_WLS_CALLS=0,R_CALLS=0,ASSIGNMENT_SOLVER_CALLS=0,ACTUAL_STEP_CALLS=0,ACTUAL_WLS_CALLS=0,RESOURCE_ACCOUNTING='INCOMPLETE',RESOURCE_COMPLIANCE='NOT_ESTABLISHED',SCIENTIFIC_DIAGNOSTIC_VALIDITY=validity,INDEPENDENT_ACCEPTANCE='PENDING',fatal=fatal,reconciliation=reconciliation,figures=plot_status,L3_B_EXPLORATORY_STAGE='CLOSED',L3_C_EXECUTION_AUTHORIZATION='NOT_GRANTED',PRODUCTION_ADMISSION='BLOCKED',HF_state_transactions=None if ctx is None else {a:dict(initial_and_hold_transactions=len(r['boundaries']),hold_count=sum(d['mode']=='FIXED_ACTION_HOLD' for d in r['decisions']),terminal_state_transitions=sum(e['kind'] in ('completed','escaped','unfinished') for e in r['events']),optimization_calls=0) for a,r in ctx['HF'].items()},limitations=['one deterministic instantaneous direction change, not bounded acceleration','public constant-velocity model intentionally mismatched','HF uses endogenous MODEL observations; proxy control receives fixed D60 beliefs','fixed candidate holds, not dynamic R policy assessment','existing audit-only consumer consistency checks are not additional rollout cells','control prediction errors conditional on actual valid control intervals','NoCap is KEEP only; no full NoCap ranking or regret','host preparation, subprocess and meter tail accounting INCOMPLETE; unknown not zero'])
    if analysis is not None:
        keep=analysis['KEEP_comparison'];report.update(MOTION_MODEL_MISMATCH_FINDINGS=analysis['motion_model_mismatch'],NOCAP_EFFECT_FINDINGS=keep,HF_FEEDBACK_RESPONSE_FINDINGS=analysis['HF_freeze_response'],ACTION_RANKING_FINDINGS=dict(H4_HF=analysis['H4_HF_ranking'],H4_CAP=analysis['H4_CAP_ranking'],H3_H4_optimum_conflict=analysis['H3_H4_HF_optimum_conflict'],HF_regret=analysis['H4_CAP_selected_HF_regret']))
    w.json('FINAL_REPORT.json',report)
    lines=['# H4独立目标转向探索实验','',validity,'','参数：H3基础世界，T0于D75逆时针转向0.5 rad；使用原始双精度速度，D75位置连续、速度右连续；T1与D60公共信息不变。','']
    if analysis is not None:
        lines+=['| 动作 | H3 HF | H3 CAP | H4 HF | H4 CAP |','|---|---|---|---|---|']
        for a,row in analysis['matrix'].items():lines.append('| '+' | '.join([a]+[str(row[k]) for k in ('H3_HF','H3_CAP','H4_HF','H4_CAP')])+' |')
        lines+=['','H4 CAP完整三格MAE：'+str(analysis['H4_complete_three_cell_MAE'])+'。有效HF/CAP配对子集：'+str(analysis['paired_error_subset'])+'。','H4 HF排序：'+str(analysis['H4_HF_ranking'])+'。','H4 CAP排序与HF regret：'+str(analysis['H4_CAP_ranking'])+'；'+str(analysis['H4_CAP_selected_HF_regret'])+'。','H3/H4 HF近似最优集合是否冲突：'+str(analysis['H3_H4_HF_optimum_conflict'])+'。','','## KEEP专项及共同控制区间','',json.dumps(analysis['KEEP_comparison'],ensure_ascii=False,indent=2),'']
        lines+=['HF实际冻结响应：'+json.dumps(analysis['HF_freeze_response'],ensure_ascii=False),'运动失配实际证据：'+json.dumps(analysis['motion_model_mismatch'],ensure_ascii=False)]
        for key,row in analysis['outcomes'].items():lines.append('- '+key+'：'+json.dumps(row,ensure_ascii=False))
        for key,row in analysis['paired_prediction_comparisons'].items():lines.append('- '+key+'：共同目标tick分母='+str(row['denominator'])+'；区间='+str(None if not row['common_ticks'] else [row['common_ticks'][0],row['common_ticks'][-1]])+'；A/B位置误差='+str((row['a_mean_position_error'],row['b_mean_position_error']))+'；A/B速度误差='+str((row['a_mean_velocity_error'],row['b_mean_velocity_error']))+'。')
        lines+=['','## 对科研问题的回答','', '1. 运动模型失配：D60正确初始状态不包含未来转向。D75真实瞬时速度已转向，D75位置尚仅包含转向前位移，D76开始包含转向后位移。实际预测误差见TRACE及SCIENTIFIC_ANALYSIS；不能把D75位置观测准确当作转向后速度已识别。','2. NoCap在H4 KEEP中的作用：净价值效应='+str(keep.get('NoCapEffect_H4'))+'，相对HF绝对误差变化='+str(keep.get('H4_Delta_AE','NOT_IDENTIFIABLE'))+'；H3/H4效应差='+str(keep.get('EffectDifference'))+'。结合完成时刻与Pmax评价，不把净价值升高单独解释为改善。','3. HF反馈响应：逐条记录实际生成、可用、消费、接受/拒绝、前后belief及差分参考。PRE_TURN/CROSSES_TURN/POST_TURN分类用于解释速度差分，跨越D75时是两段运动的时间加权平均；无合格参考则保留更新前速度。每个HF TRACE提供第一条measurement>=75及第一条measurement>75的质量有效观测，另有实际冻结误差和后续控制/服务。未新增关闭反馈对照，因此不声称反馈净因果效应已独立识别。','4. 服务及价值变化：逐动作完成、Pmax、重置及终止事件见上表和RAW；HF保留原始带符号账本并提供收益/正成本表达，代理保留原六项账本。各自净价值由原始审计公式核对。','5. H4代理排序误差与HF regret：'+str(analysis['H4_CAP_selected_HF_regret'])+'；完整排序与误差分别满足R4必要数据时才报告，不插补。','6. H3/H4真实HF最优动作冲突：'+str(analysis['H3_H4_HF_optimum_conflict'])+'。未重跑H3，历史比较不代表本次验证了H4上的动态R策略。','7. 后续研究启示：本次只为运动模型不确定性、反馈估计响应及服务连续性风险提供案例证据；不据单一转向世界宣称新算法、鲁棒策略或普遍计算优势已经得到验证，也不启动后续算法实验。']
    lines+=['','## 范围、实际执行与资源限制','',json.dumps(report,ensure_ascii=False,indent=2),'','所有有效单元原始数据均保留。失败或缺失按指标分别限制解释，不用历史H3冒充H4，不增加单元或自动重试。控制停止后不生成预测记录；配对误差按目标和同tick的共同有效范围去重，完整价值与终端状态不截断至该范围。','', '本任务仅新增专属目录内容，保留全部历史资产、已关闭L3-B及生产准入限制。资源最终退出回执见RESOURCE_RECEIPT.json；累计逻辑写入包括受控追加、覆盖及最终回执，未测资源不记零。']
    w.write('REPORT.md','\n'.join(lines));clock.check();inventory={p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in HERE.rglob('*') if p.is_file()};w.json('FILE_SHA256.json',dict(files=inventory,excludes=['FILE_SHA256.json self','WORKER_ACCOUNTING.json','RESOURCE_RECEIPT.json']))
    w.accounting_receipt('WORKER_ACCOUNTING.json',dict(worker_pid=os.getpid(),cpu_snapshot=time.process_time(),wall_snapshot=time.monotonic()-origin,operations=w.operations,resource_counts=counts,resource_accounting='INCOMPLETE'))
    print(json.dumps(dict(validity=validity,HF_started=hfstarted,HF_valid=hfvalid,proxy_started=proxystarted,proxy_valid=proxyvalid,counts=counts,failure=None if fatal is None else dict(type=fatal['type'],message=fatal['message']),values=None if analysis is None else analysis['matrix'],KEEP=None if analysis is None else analysis['KEEP_comparison']),ensure_ascii=False),flush=True);return 0 if hfvalid==3 and proxyvalid==4 and fatal is None else 1

def process_times(handle):
    from ctypes import wintypes
    class FT(ctypes.Structure):_fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
    a,b,c,d=FT(),FT(),FT(),FT();f=ctypes.windll.kernel32.GetProcessTimes;f.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(FT)]*4;f.restype=wintypes.BOOL;require(f(int(handle),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)),'GET_PROCESS_TIMES');v=lambda x:(x.high<<32)|x.low
    return dict(creation_filetime=v(a),exit_filetime=v(b),kernel_seconds=v(c)/1e7,user_seconds=v(d)/1e7)
def meter():
    prep=read(HERE/'PREPARATION_ACCOUNTING.json');origin=time.monotonic()-(prep['elapsed_at_launch']+max(0.,time.time()-prep['bridge_utc_epoch']));deadline=origin+1800;p=subprocess.Popen([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),'--worker',str(origin)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);limit=None
    while p.poll() is None:
        t=process_times(p._handle)
        if time.monotonic()>=deadline or t['kernel_seconds']+t['user_seconds']+time.process_time()>=300:limit='RESOURCE_LIMIT';p.kill();break
        time.sleep(.05)
    out,err=p.communicate();end=time.monotonic();final=process_times(p._handle);entry_cpu=time.process_time();wf=HERE/'WORKER_ACCOUNTING.json';prior=read(wf)['cumulative_logical_write_bytes'] if wf.exists() else prep['cumulative_logical_write_bytes'];writer=Writer(HERE,limit=536870912,initial_written=prior)
    receipt=writer.accounting_receipt('RESOURCE_RECEIPT.json',dict(worker_pid=p.pid,worker_exit_status=p.returncode,internal_call_counts=read(HERE/'FINAL_REPORT.json').get('resource_counts') if (HERE/'FINAL_REPORT.json').exists() else 'INCOMPLETE',worker_final_cpu=final,entry_pid=os.getpid(),entry_cpu_at_worker_exit=entry_cpu,known_cpu_subtotal=entry_cpu+final['kernel_seconds']+final['user_seconds'],limits=dict(cpu=300,wall=1800,cumulative_logical_write_bytes=536870912),wall_start_utc=prep['wall_start_utc'],wall_seconds_at_worker_exit=end-origin,deadline_trigger=limit,path_b='APPROVED: worker exit cutoff; final receipt and handle closure only',resource_accounting='INCOMPLETE',resource_compliance='NOT_ESTABLISHED',unknown_cpu='host preparation and readonly tools; final entry tail INCOMPLETE',wall_limitation='initial readonly command before clock anchor not precisely captured; UTC bridge at startup then common monotonic deadline',write_limitation='controlled writes counted; host writes INCOMPLETE',entry_tail='INCOMPLETE; not zero',stdout=out.decode(errors='replace'),stderr=err.decode(errors='replace')));p._handle.Close();print(json.dumps(receipt,ensure_ascii=False),flush=True);return p.returncode
if __name__=='__main__':sys.exit(worker() if '--worker' in sys.argv else meter())
