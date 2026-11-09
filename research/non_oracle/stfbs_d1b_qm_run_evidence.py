"""Read-only real-source capture, independent G/Q and service/economic verification."""
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,math,os
import numpy as np
from .stfbs_d1b_qm_model import QMBranch
from .stfbs_d1a_replay import digest
from .stfbs_d1b_qm_run_audit import endpoint_join

LABEL='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'
_SOURCE_SEAL=object();_CANDIDATE_SEAL=object()

class BudgetAwareQMBranch(QMBranch):
    def __init__(self,*args,**kwargs):
        from .stfbs_d1b_qm_run_release import require_run_g1
        permit=require_run_g1();super().__init__(*args,**kwargs)
        folder=Path(permit.bindings['output_dir'])/'branch_journals';folder.mkdir(exist_ok=True)
        self._trace_path=str(folder/(self.name+'.jsonl'));Path(self._trace_path).open('x').close()
        self._trace_cursor=0;self._trace_sequence=0;self.raw_trace=[]
    def raw(self,j,i,tick):
        from .stfbs_d1b_qm_run_release import require_run_g1
        require_run_g1()
        before=dict(self.cache.counts);slot=super().raw(j,i,tick)
        self.raw_trace.append(dict(branch=self.name,target=j,robot=i,tick=tick,new=self.cache.counts['new']-before['new'],reuses=self.cache.counts['reuses']-before['reuses']))
        return slot
    def checkpoint(self,phase):
        self._trace_sequence+=1
        row=dict(sequence=self._trace_sequence,phase=phase,branch=self.name,tick=self.tick,positions=self.positions.tolist(),actions=self.actions,
                 histories=self.histories,feedback=self.feedback[self._trace_cursor:],frame=self.frames[-1] if self.frames else None,
                 pending=self.consumer.pending,frozen=self.frozen,events=self.events,components=self.components,change_cost=self.change_cost,status=self.status)
        with Path(self._trace_path).open('a',encoding='utf-8') as f:f.write(json.dumps(row,sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
        self._trace_cursor=len(self.feedback)
    def assign(self,*args,**kwargs):
        from .stfbs_d1b_qm_run_release import require_run_g1
        require_run_g1()
        super().assign(*args,**kwargs);self.checkpoint('ASSIGN_COMMITTED')
    def advance(self):
        from .stfbs_d1b_qm_run_release import require_run_g1
        require_run_g1()
        super().advance();self.checkpoint('ADVANCE_COMMITTED')
    def fuse(self,j,segment,tick):
        from .stfbs_d1b_qm_run_release import require_run_g1
        require_run_g1()
        frame_id=f'{self.name}:T{j}:first{segment["first_fusion_tick"]}:tick{tick}'
        with self.budget.for_frame(frame_id):return super().fuse(j,segment,tick)

def result_from_branch(b):
    return dict(branch=b.name,world=deepcopy(b.world),provenance='SIMULATED',observation_origin='MODEL',components=deepcopy(b.components),
                change_cost=b.change_cost,net=sum(b.components.values())-b.change_cost,frames=deepcopy(b.frames),events=deepcopy(b.events),
                boundaries=deepcopy(b.boundaries),decisions=deepcopy(b.decisions),feedback=deepcopy(b.feedback),status=deepcopy(b.status),
                histories=deepcopy(b.histories),actions=deepcopy(b.actions),tick=b.tick,view=deepcopy(b.view),
                pending=deepcopy(b.consumer.pending),frozen_beliefs=deepcopy(b.frozen),raw_counts=deepcopy(b.cache.counts),endpoint_fusions=b.fusions,raw_trace=deepcopy(getattr(b,'raw_trace',[])))

def records_from_branch(b):
    positions={60:deepcopy(b.view['positions'])}
    positions.update({f['tick']:deepcopy(f['positions']) for f in b.frames})
    ticks={row['frame']['tick'] for row in b.feedback}
    return dict(feedback=deepcopy(b.feedback),histories=deepcopy(b.histories),cache=deepcopy(b.cache.rows),positions=positions,
                physical_profiles={k:b._sensor_authority.physical_profile_at(k) for k in ticks})

def serial_records(records):
    out=deepcopy(records);out['cache']=[dict(key=list(k),value=v) for k,v in out['cache'].items()];return out

def restore_records(records):
    out=deepcopy(records);out['cache']={tuple(x['key']):x['value'] for x in out['cache']}
    for key in ('histories','positions','physical_profiles'):out[key]={int(k):v for k,v in out[key].items()}
    return out

def normalize_int_maps(result):
    for key in ('histories','status'):result[key]={int(k):v for k,v in result[key].items()}
    result['world']['motion']={int(k):v for k,v in result['world']['motion'].items()}
    for frame in result['frames']:frame['clocks']={int(k):v for k,v in frame['clocks'].items()}
    return result

def independent_gq(endpoint,records,world,config,registration,*,segment_id=None,side=None):
    from pursuit_v2.config import Config
    from pursuit_v2.observation_geometry import offset,radius
    from research.information_service.public_quality import assess_quality,prepare_frame
    link=endpoint_join(endpoint,records,registration,segment_id=segment_id,side=side)
    tick=endpoint['tick'];motion=world['motion'][endpoint['target_id']];cfg=Config(**config)
    target=np.asarray(motion['position'])+np.asarray(motion['velocity'])*((tick-60)*.05)
    actual=all(np.linalg.norm(np.asarray(records['positions'][tick][m['robot_id']])-target-offset(m['role'],cfg))<=radius(cfg) for m in endpoint['team'])
    if bool(actual)!=endpoint['G']:raise ValueError('INDEPENDENT_G_MISMATCH')
    row=records['feedback'][link['feedback_index']]
    for packet in row['frame']['records']:
        pos=packet['position'];expected=(math.atan2(float(target[1]-pos[1]),float(target[0]-pos[0]))+math.pi)%(2*math.pi)-math.pi
        if packet['bearing']!=expected:raise ValueError('INDEPENDENT_ZERO_NOISE_BEARING_MISMATCH')
    prepared=prepare_frame(row['frame'],['U'+str(m['robot_id']) for m in endpoint['team']])
    quality=assess_quality(prepared['payload'],row['result']['estimate_result']);quality['frame_id']=row['frame']['frame_id']
    if quality!=endpoint['quality'] or quality!=row['result']['quality']:raise ValueError('INDEPENDENT_Q_MISMATCH')
    return dict(status='PASS',G=bool(actual),Q=quality['status'],radius_proxy=quality['radius_proxy'],link=link)

@dataclass(frozen=True)
class FrozenBranchSource:
    batch_id: str
    branch_id: str
    path: str
    file_sha256: str
    registration: object
    evidence_kind: str
    seal: object

def save_branch_source(branch,verified_registration,path,batch_id):
    from .stfbs_d1b_qm_run_release import require_run_g1
    from .stfbs_d1b_qm_independent_audit import audit_registered
    permit=require_run_g1()
    if permit.bindings['batch_id']!=batch_id:raise ValueError('Batch identity mismatch')
    audit=audit_registered(branch,verified_registration.registration)
    records=records_from_branch(branch)
    for row in records['feedback']:independent_gq(row['endpoint'],records,branch.world,branch.view['config'],verified_registration.registration)
    payload=dict(batch_id=batch_id,branch_id=branch.name,result=result_from_branch(branch),records=serial_records(records),external_history_audit=audit,evidence_kind='MODEL')
    path=Path(path)
    with path.open('x',encoding='utf-8') as f:json.dump(payload,f,sort_keys=True,ensure_ascii=False,indent=2)
    return FrozenBranchSource(batch_id,branch.name,str(path),hashlib.sha256(path.read_bytes()).hexdigest(),verified_registration.registration,'MODEL',_SOURCE_SEAL)

def read_verified_source(source,*,test=False):
    if type(source) is not FrozenBranchSource or source.seal is not _SOURCE_SEAL:raise ValueError('SOURCE_NOT_VERIFIED')
    if source.evidence_kind==LABEL:
        if not test:raise PermissionError('Test source cannot enter real special')
    else:
        from .stfbs_d1b_qm_run_release import require_run_g1
        if require_run_g1().bindings['batch_id']!=source.batch_id:raise ValueError('SOURCE_BATCH_MISMATCH')
    raw=Path(source.path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=source.file_sha256:raise ValueError('SOURCE_FILE_HASH_MISMATCH')
    payload=json.loads(raw)
    if payload['batch_id']!=source.batch_id or payload['branch_id']!=source.branch_id or payload['evidence_kind']!=source.evidence_kind:raise ValueError('SOURCE_RUN_IDENTITY_MISMATCH')
    records=restore_records(payload['records']);result=normalize_int_maps(payload['result'])
    if result['branch']!=source.branch_id or records['histories']!=result['histories'] or records['feedback']!=result['feedback']:raise ValueError('SOURCE_CROSS_RECORD_MISMATCH')
    from .stfbs_d1a_history_audit import AuditContext,audit_branch_independent
    from pursuit_v2.config import Config
    branch=SimpleNamespace(name=source.branch_id,histories=result['histories'],actions=result['actions'],status=result['status'],tick=result['tick'],events=result['events'],boundaries=result['boundaries'],cfg=Config(**result['view']['config']),change_cost=result['change_cost'])
    audit_branch_independent(branch,context=AuditContext(source.registration.branch_id,source.registration.prefix_json))
    if payload['external_history_audit']['status']!='PASS':raise ValueError('SOURCE_EXTERNAL_AUDIT_FAILED')
    return payload,result,records

def create_test_source(payload,registration,path):
    """Only complete synthetic fixtures; cannot mint a MODEL source capability."""
    if payload.get('evidence_kind')!=LABEL:raise PermissionError('Only labelled test source')
    path=Path(path)
    with path.open('x',encoding='utf-8') as f:json.dump(payload,f,sort_keys=True,indent=2)
    return FrozenBranchSource(payload['batch_id'],payload['branch_id'],str(path),hashlib.sha256(path.read_bytes()).hexdigest(),registration,LABEL,_SOURCE_SEAL)

@dataclass(frozen=True)
class TrustedCandidate:
    row_json: str
    evidence_kind: str
    seal: object

def candidate_from_sources(old_source,new_source,sigma,*,test=False):
    _,old,orecords=read_verified_source(old_source,test=test);_,new,nrecords=read_verified_source(new_source,test=test)
    expected=('QM_PROBE_DEGRADED_'+str((.04,.08,.16,.32).index(sigma)+1))
    if old_source.branch_id!='QM_PROBE_OLD' or new_source.branch_id!=expected or old_source.batch_id!=new_source.batch_id:raise ValueError('CANDIDATE_SOURCE_IDENTITY')
    def right80(records):
        rows=[x for x in records['feedback'] if x['endpoint']['tick']==80]
        if len(rows)!=1:raise ValueError('Probe right80 ambiguity')
        return rows[0]['endpoint']
    oe=right80(orecords);ne=right80(nrecords)
    if old['world']!=new['world'] or orecords['positions'][80]!=nrecords['positions'][80] or oe['team']!=ne['team']:raise ValueError('PROBE_GEOMETRY_NOT_IDENTICAL')
    for records in (orecords,nrecords):
        if records['physical_profiles'][79][1]['sigma']!=.02:raise ValueError('Probe prefix not normal')
    if orecords['physical_profiles'][80][1]['sigma']!=.02 or nrecords['physical_profiles'][80][1]['sigma']!=sigma:raise ValueError('Probe sigma mismatch')
    og=independent_gq(oe,orecords,old['world'],old['view']['config'],old_source.registration,side='RIGHT')
    ng=independent_gq(ne,nrecords,new['world'],new['view']['config'],new_source.registration,side='RIGHT')
    row=dict(probe_id=expected,sigma=sigma,old_G=og['G'],new_G=ng['G'],old_Q=og['Q'],new_Q=ng['Q'],old_source_sha=old_source.file_sha256,new_source_sha=new_source.file_sha256)
    return TrustedCandidate(json.dumps(row,sort_keys=True),LABEL if test else 'MODEL',_CANDIDATE_SEAL)

def service_and_control_audit(result,view):
    """Independent walk: same-tick competing endpoints are resolved by full team."""
    from .belief import trajectory
    from pursuit_v2.config import Config
    from pursuit_v2.observation_geometry import offset
    cfg=Config(**view['config']);boundaries={b['tick']:b for b in result['boundaries']}
    actions=deepcopy(view['assignment']);frozen=view['beliefs'];clock=0;left=None;team=[];checked=0;resets=[]
    decisions={d['view']['tick']:d['view'] for d in result['decisions']}
    terminal=next(e for e in result['events'] if e['target']==0 and e['kind'] in ('completed','escaped','unfinished'))
    def endpoint(tick,members):
        rows=[f['endpoint'] for f in result['feedback'] if f['endpoint']['tick']==tick and f['endpoint']['team']==members]
        if len(rows)!=1:raise ValueError('Service endpoint identity ambiguity')
        return rows[0]
    for frame in result['frames']:
        n=frame['tick'];lo=(n-1)*.05
        if n-1 in decisions:frozen=decisions[n-1]['beliefs']
        if n-1 in boundaries:
            actions=boundaries[n-1]['after'];new=[dict(robot_id=i,role=a['role']) for i,a in enumerate(actions) if a['target']==0]
            if new!=team:team=new;clock=0;left=endpoint(n-1,team) if team else None
        for i,a in enumerate(actions):
            u=np.zeros(2);elapsed=0.
            if a['target'] is not None and (terminal['time']>lo or terminal['time']==lo and terminal['tick']>=n):
                belief=frozen.get(0,frozen.get('0'));p,v=trajectory(belief,n-1)
                force=np.asarray(v)+cfg.travel_gain*(np.asarray(p)+offset(a['role'],cfg)-np.asarray(frame['before'][i]))
                u=force*min(1.,cfg.max_speed/max(float(np.linalg.norm(force)),1e-15))
                m=result['world']['motion'][0];x=m['position'][0]+m['velocity'][0]*(lo-3.)
                escape=lo if x>=cfg.side else lo+(cfg.side-x)/m['velocity'][0] if m['velocity'][0]>0 else math.inf
                elapsed=max(0.,min(n*.05,escape)-lo)
            bound=16*math.ulp(max(1.,float(np.max(np.abs(u)))))
            if np.max(np.abs(u-np.asarray(frame['control'][i])))>bound or elapsed!=frame['elapsed'][i]:raise ValueError('Independent control/elapsed mismatch')
        if team and terminal['time']>=lo and not (terminal['kind']=='escaped' and terminal['time']<=n*.05+1e-10) and not (terminal['tick']<n):
            right=endpoint(n,team);valid=left['G'] and right['G'] and left['quality']['status']==right['quality']['status']=='PASS'
            if not valid and clock>0:resets.append(dict(target=0,kind='reset',tick=n,time=n*.05,reason='observation_invalid',progress_before=clock*.05))
            clock=clock+1 if valid else 0;done=clock*.05>=view['targets'][0]['service_duration']-1e-10
            if done and not (terminal['kind']=='completed' and terminal['tick']==n):raise ValueError('Independent service completion mismatch')
            raw=frame['clocks'][0]
            if not done and raw is not None and (raw['base']!=0. or raw['intervals']!=clock):raise ValueError('Independent service clock mismatch')
            left=right;checked+=1
    from .stfbs_d1a_audit import audit
    if resets!=[e for e in result['events'] if e['kind']=='reset']:raise ValueError('Independent reset event mismatch')
    accounting=audit(result,view)
    return dict(status='PASS',service_intervals=checked,control=True,accounting=accounting)

def coordinate_batch(ops):
    """Single fixed order, also exercised by a fully synthetic operation port."""
    status={k:'NOT_EXECUTED_GATE_NOT_MET' for k in ('B0','B1','B3','F1','F2','F3A','F3B')}
    old=ops.probe('QM_PROBE_OLD');old_quality=ops.old_quality(old)
    if not old_quality['G'] or old_quality['Q']!='PASS':return dict(status='SCENARIO_ADMISSION_FAILED',stages=status)
    candidates=[];selected=None
    for index,sigma in enumerate((.04,.08,.16,.32),1):
        new=ops.probe('QM_PROBE_DEGRADED_'+str(index));row=ops.candidate(old,new,sigma);candidates.append(row)
        values=ops.candidate_values(row)
        if values['old_G'] and values['new_G'] and values['old_Q']=='PASS' and values['new_Q']=='FAIL':selected=sigma;break
    if selected is None:return dict(status='NO_Q_ONLY_FAIL_FOUND',stages=status)
    admitted=ops.admit(candidates)
    b0=ops.dynamic('QM_B0_KEEP',selected,admitted);status['B0']='EXECUTED'
    b1=ops.dynamic('QM_B1_MEMBER_CHANGE',selected,admitted);status['B1']='EXECUTED'
    if not ops.dynamic_realized(b0,b1,selected):return dict(status='DYNAMIC_Q_ONLY_NOT_REALIZED',stages=status)
    b3=ops.b3();status['B3']='EXECUTED'
    ops.f1(b1);status['F1']='PASS'
    ops.special('QM_F2_VALID_HISTORY',b1);status['F2']='PASS'
    ops.special('QM_F3_STREAM_A',b0);status['F3A']='PASS'
    ops.special('QM_F3_STREAM_B',b1);status['F3B']='PASS'
    return dict(status='EXECUTED_AWAITING_FINAL_AUDIT',selected_sigma=selected,stages=status,science=ops.final_science(b0,b1,b3))

class RealBatchOps:
    def __init__(self,permit,budget,fixture):
        from .stfbs_d1b_qm_run_release import require_run_g1
        require_run_g1(permit);self.permit=permit;self.budget=budget;self.fixture=fixture;self.output=Path(permit.bindings['output_dir']);self.active={};self.audits={}
    def _registration(self,name):
        from .stfbs_d1b_qm_run_audit import SourceAnchor,register_verified_fixture
        pins=self.permit.bindings['source_pins'];return register_verified_fixture(Path(__file__).resolve().parents[2],self.fixture,name,pins,SourceAnchor('APPROVED_RUN_G1',json.dumps(pins,sort_keys=True)))
    def _save(self,b,reg,full=False):
        source=save_branch_source(b,reg,self.output/(b.name+'.json'),self.permit.bindings['batch_id'])
        if full:self.audits[b.name]=service_and_control_audit(result_from_branch(b),b.view)
        return source
    def probe(self,name):
        from .stfbs_d1b_qm_run_release import prepare_probe_branch
        from .stfbs_d1b_qm_execution import ProbeSchedule
        reg=self._registration(name);b=prepare_probe_branch(self.fixture,name,self.budget,reg);self.active[name]=b
        ProbeSchedule(b,name).run_to_80();return self._save(b,reg)
    def old_quality(self,source):
        _,r,records=read_verified_source(source);rows=[x['endpoint'] for x in records['feedback'] if x['endpoint']['tick']==80]
        if len(rows)!=1:raise ValueError('OLD right80 ambiguity')
        return independent_gq(rows[0],records,r['world'],r['view']['config'],source.registration,side='RIGHT')
    def candidate(self,old,new,sigma):return candidate_from_sources(old,new,sigma)
    def candidate_values(self,row):return json.loads(row.row_json)
    def admit(self,candidates):
        from .stfbs_d1b_qm_run_release import freeze_admission
        result=freeze_admission(candidates,self.permit.bindings['batch_id'])
        self._write('ADMISSION.json',result.__dict__);return result
    def dynamic(self,name,sigma,admission):
        from .stfbs_d1b_qm_run_release import prepare_dynamic_branch
        from .stfbs_d1b_qm_execution import DynamicSchedule
        reg=self._registration(name);b=prepare_dynamic_branch(self.fixture,name,self.budget,reg,selected_sigma=sigma,admission=admission);self.active[name]=b
        DynamicSchedule(b,name).run_to_end();return self._save(b,reg,True)
    def dynamic_realized(self,b0,b1,sigma):
        all_positions=[]
        for source in (b0,b1):
            _,r,records=read_verified_source(source);all_positions.append(records['positions'][80])
            rows=[x['endpoint'] for x in records['feedback'] if x['endpoint']['tick']==80 and [m['robot_id'] for m in x['endpoint']['team']]==[0,1]]
            if len(rows)!=1:return False
            q=independent_gq(rows[0],records,r['world'],r['view']['config'],source.registration,side='RIGHT')
            if not q['G'] or q['Q']!='FAIL' or records['physical_profiles'][80][1]['sigma']!=sigma:return False
        return all_positions[0]==all_positions[1]
    def b3(self):
        from .stfbs_d1b_qm_run_release import prepare_b3_branch
        from .stfbs_d1b_qm_execution import DynamicSchedule
        reg=self._registration('QM_B3_UNKNOWN');b=prepare_b3_branch(self.fixture,self.budget,reg);self.active[b.name]=b
        DynamicSchedule(b,b.name).run_to_end();return self._save(b,reg,True)
    def f1(self,b1):
        _,r,records=read_verified_source(b1)
        rows=[f for f in records['feedback'] if f['endpoint']['tick']==80]
        if len(rows)!=2:raise ValueError('F1 two endpoints required')
        u0=[next(s for s in f['slots'] if s['slot_key']['robot_id']==0) for f in rows]
        if u0[0]!=u0[1] or rows[0]['frame']['stream_id']==rows[1]['frame']['stream_id']:raise ValueError('F1 retained raw/stream mismatch')
        trace=[x for x in r['raw_trace'] if x['tick']==80 and x['robot']==0]
        if sum(x['new'] for x in trace)!=1 or sum(x['reuses'] for x in trace)!=1:raise ValueError('F1 producer/cache count mismatch')
        self._write('F1_READONLY_AUDIT.json',dict(status='PASS',extra_wls=0,source_sha=b1.file_sha256,raw_trace=trace))
    def special(self,name,source):
        from .stfbs_d1b_qm_run_specials import run_special
        result=run_special(name,source,self.budget);self._write(name+'.json',result);return result
    def _write(self,name,value):
        with (self.output/name).open('x',encoding='utf-8') as f:json.dump(value,f,sort_keys=True,indent=2)
    def final_science(self,b0,b1,b3):
        _,r,records=read_verified_source(b1);segments=[s for s in records['histories'][0]['segments'] if s['start_tick']==80]
        sid=segments[0]['segment_id'] if len(segments)==1 else None
        endpoints=[f['endpoint'] for f in records['feedback'] if f['endpoint']['team']==segments[0]['team'] and f['endpoint']['tick']>=80] if sid else []
        restored=[e['tick'] for e in endpoints if e['G'] and e['quality']['status']=='PASS'];resumed=[e['tick'] for a,e in zip(endpoints,endpoints[1:]) if e['tick']==a['tick']+1 and a['G'] and e['G'] and a['quality']['status']==e['quality']['status']=='PASS']
        return dict(EXECUTION_VALID=True,Q_ONLY_FAILURE_OBSERVED=True,GQ_RESTORED=bool(restored),SERVICE_RESUMED=bool(resumed),TASK_COMPLETED=r['status'][0]=='completed',first_GQ_tick=min(restored) if restored else None,first_resume_tick=min(resumed) if resumed else None,net_values={k:self.audits[k]['accounting']['net'] for k in self.audits},scope='MODEL simulation, not ACTUAL flight')
    def preserve_partial(self,error):
        self._write('PARTIAL_BRANCHES.json',dict(error=repr(error),branches={k:result_from_branch(b) for k,b in self.active.items()},status='BLOCKED_PARTIAL_NOT_FULL_EXPERIMENT'))
