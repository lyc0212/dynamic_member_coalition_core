"""H5 saved-data finalization. Standard library only; no scientific imports."""
import collections,datetime,hashlib,itertools,json,math,re,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[2]
START='2026-11-15T14:51:05.8712714+08:00';ORIGIN=time.monotonic()-(time.time()-datetime.datetime.fromisoformat(START).timestamp())
PRIOR=12115003;LIMIT=134217728;WRITTEN=PRIOR+Path(__file__).stat().st_size;OPS=[dict(file='offline_finalize.py',bytes=Path(__file__).stat().st_size)]
ACTIONS=('KEEP','SWITCH','MEMBER_CHANGE');METHODS=('HF','ON','OFF');CELLS=[('HF',a) for a in ACTIONS]+[('OFF','KEEP')]+[('ON',a) for a in ACTIONS]
def check():
    assert 0<=time.monotonic()-ORIGIN<900,'OFFLINE_WALL_LIMIT'
    assert time.process_time()<30,'OFFLINE_CPU_LIMIT'
    assert WRITTEN<LIMIT,'CUMULATIVE_WRITE_LIMIT'
def read(p):check();return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def put(name,text):
    global WRITTEN
    check();b=text.encode();assert WRITTEN+len(b)<=LIMIT
    with (ROOT/name).open('xb') as f:assert f.write(b)==len(b)
    WRITTEN+=len(b);OPS.append(dict(file=name,bytes=len(b)))
def diff(a,b,path=''):
    if type(a)!=type(b):return [dict(path=path,left=a,right=b)]
    if isinstance(a,dict):
        out=[]
        for k in sorted(a.keys()|b.keys(),key=lambda x:(type(x).__name__,repr(x))):
            p=path+'/'+str(k)
            if k not in a or k not in b:out.append(dict(path=p,left=a.get(k),right=b.get(k),missing_key=True))
            else:out.extend(diff(a[k],b[k],p))
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return [dict(path=path,left_length=len(a),right_length=len(b))]
        return [r for i,(x,y) in enumerate(zip(a,b)) for r in diff(x,y,path+'/'+str(i))]
    return [] if a==b else [dict(path=path,left=a,right=b)]
PATTERNS=(r'/branch',r'/frame/(stream_id|frame_id)',r'/frame/records/\d+/packet_id',r'/result/(frame_sha256|frame_id|stream_id)',r'/result/normalized_frame/(stream_id|frame_id)',r'/result/normalized_frame/records/\d+/packet_id',r'/result/quality/frame_id',r'/endpoint/branch',r'/endpoint/quality/frame_id')
def identity(path):return any(re.fullmatch(p,path) for p in PATTERNS)
def frame_binding(f,name):
    a=f['frame'];r=f['result'];q=r['quality'];e=f['endpoint'];n=r['normalized_frame']
    assert f['branch']==e['branch']==name
    assert a['frame_id']==r['frame_id']==n['frame_id']==q['frame_id']==e['quality']['frame_id']
    assert a['stream_id']==r['stream_id']==n['stream_id'] and a['stream_id'].startswith(name+':')
    assert a['frame_id']==a['stream_id']+':tick'+str(a['tick'])
    assert r['frame_sha256']==digest(n) and r['payload_sha256']==digest(r['payload'])==q['payload_sha256']==e['quality']['payload_sha256']
    assert e['quality']==q and a['target_id']==r['target_id']==n['target_id']==e['target_id']
    for row in a['records']:assert row['packet_id']==a['frame_id']+':'+row['sensor_id']
def vector_minus(a,b):return [x-y for x,y in zip(a,b)]
def heading(v):return math.atan2(v[1],v[0])
def angle_delta(a,b):return (heading(a)-heading(b)+math.pi)%(2*math.pi)-math.pi
def index(rows):
    result={}
    for row in rows:
        k=(row['target'],row['tick'])
        if k in result:assert row['prediction_position']==result[k]['prediction_position'] and row['prediction_velocity']==result[k]['prediction_velocity']
        else:result[k]=row
    return result

def main():
    check();original={str(p):sha(p) for p in ROOT.parent.rglob('*') if p.is_file() and p!=Path(__file__) and p.name not in ('OFFLINE_FINALIZATION.json','OFFLINE_FINALIZATION_REPORT.md')}
    manifest=read(ROOT/'FILE_SHA256.json');manifest_check={name:sha(ROOT/name)==v['sha256'] and (ROOT/name).stat().st_size==v['bytes'] for name,v in manifest.items()};assert all(manifest_check.values()),'SOURCE_MANIFEST_MISMATCH'
    config=read(ROOT/'EXPERIMENT_CONFIG.json');source=read(ROOT/'FINAL_REPORT.json');receipt=read(ROOT/'RESOURCE_RECEIPT.json');worldfile=read(ROOT/'WORLD_H5_ARC.json');world=worldfile['MODEL_world'];physical=worldfile['physical_definition']
    assert source['status']=='PARTIAL_RESULTS' and source['started']==source['valid']==7
    assert digest({k:v for k,v in world.items() if k!='world_digest'})==world['world_digest']=='6d23db4be70d86ad95c95de8cb4022de9a3617c38e7f7a4f2c085b56b488bf5f'
    assert digest({k:v for k,v in physical.items() if k!='physics_digest'})==physical['physics_digest']=='e3730bdbc45a6ccc6ede9ced9dc5089963dd8a080817455967971a79af0796d6'
    assert config['world']==world and sha(ROOT/'h5_entry.py')==config['entry_sha256']=='2adf086deaf2562e743b5e568522d836efdc95bd3c08e663b1a984bf0e63fa37'
    assert sha(ROOT/'h5_motion.py')==config['motion_sha256']=='ef05b290837b60761ccd209c03d6b2af07a2c7648e1af017044aa2ac63fb82bd'
    assert sha(ROOT/'blvf.py')==config['blvf_sha256']=='204fc231bf78004c33daf151983d751685666da75ed9e9b911abb83854c7365e'
    protected={p:sha(p)==h for p,h in config['protected_source_hashes'].items()};assert all(protected.values()),'PROTECTED_SOURCE_MISMATCH'
    before_binding=read(ROOT/'RUNTIME_BINDINGS_BEFORE_SCIENCE.json');assert not (ROOT/'RUNTIME_BINDINGS_FINAL.json').exists(),'UNEXPECTED_FINAL_BINDING_FILE'
    candidate=read(config['candidate_source'])['candidate'];view=candidate['a2_policy_view'];seed=candidate['consumer_seed'];assert digest(view)==config['D60_digest'] and digest(seed)==config['seed_digest'] and not seed['pending_observations']
    candidates=read(REPO/'reports/stfbs_lite_h2_h3_extension_005/CANDIDATE_FREEZE.json')
    raw={};trace={};timing={};integrity={};consumer={}
    for method,action in CELLS:
        check();name='H5_'+method+'_'+action;r=read(ROOT/('RAW/'+name+'.json'));t=read(ROOT/('TRACE/'+name+'.json'));tm=read(ROOT/('TIMING/'+name+'.json'));raw[name]=r;trace[name]=t;timing[name]=tm
        assert r['branch']==name and r['method_route']==method and r['world']==world and r['provenance']=='SIMULATED' and r['observation_origin']=='MODEL'
        assert r['method']==('HF_NINE_START_WLS' if method=='HF' else 'STFBS_LITE_FB_BLVF_V0.1') and r['feedback_enabled']==(method!='OFF')==t['feedback_enabled']
        assert len(r['frames'])==60 and [f['tick'] for f in r['frames']]==list(range(61,121))
        actions=next(c['actions'] for c in candidates if c['kind']==action);assert r['boundaries'][0]['tick']==60 and r['boundaries'][0]['after']==actions
        assert [d['view']['tick'] for d in r['decisions']]==[80,100] and [f['tick'] for f in t['freeze_records']]==[80,100]
        assert all(b['changes']==0 and b['cost']==0 and b['before']==b['after'] for b in r['boundaries'] if b['tick'] in (80,100))
        assert len(t['hold_checks'])==2 and all(x['status']=='PASS' for x in t['hold_checks'])
        assert set(t['audits'])=={'history','service','physical_economic','actual_control'} and all(x['status']=='PASS' for x in t['audits'].values())
        assert sum(r['components'].values())-r['change_cost']==r['net']==t['audits']['physical_economic']['net']
        assert 'pending_D120' in t and all(100<x['available_tick']<=120 for x in t['pending_D120'])
        if method=='OFF':assert all(x['actual_control_beliefs']==view['beliefs'] for x in t['freeze_records'])
        else:assert all(x['actual_control_beliefs']==x['shadow_beliefs'] for x in t['freeze_records'])
        assert tm['method']==method and tm['action']==action
        own={(f['frame']['frame_id'],f['frame']['target_id'],f['frame']['tick']):f for f in r['feedback']};used=set();accepted=0;rejected=0;estimates=0;starts=0
        for f in r['feedback']:
            assert f['branch']==name and f['endpoint']['provenance']=='SIMULATED' and f['endpoint']['observation_origin']=='MODEL'
            result=f['result'];est=result['estimate_result'];payload=result['payload']
            if payload is not None:assert set(payload)=={'sensor_ids','positions','bearings','sigmas','domain'} and digest(payload)==result['payload_sha256']
            if result['estimator_called']:
                estimates+=1;assert est is not None
                if method=='HF':
                    assert len(est['starts'])==9 and 'analytic_solution_success' not in est and 'nonlinear_solver_starts' not in est;starts+=len(est['starts'])
                else:assert est['estimator_method']=='ANALYTIC_BEARING_INTERSECTION' and est['nonlinear_solver_starts']==0 and est['starts']==[]
        for event in t['actual_consumer_records']:
            key=(event['frame_id'],event['target'],event['measurement_tick']);assert key in own and key not in used;used.add(key)
            assert event['available_tick']<=event['consumed_tick']==event['freeze_tick'] and event['freeze_tick'] in (80,100)
            assert event['observation_origin']=='MODEL' and event['provenance']=='SIMULATED'
            assert event['accepted']==(not event['rejection_reasons'])
            if event['accepted']:
                accepted+=1;assert [event['measurement_tick'],event['accepted_position']] in t['accepted_history'][str(event['target'])] and event['accepted_position']==own[key]['result']['estimate_result']['estimate']
            else:rejected+=1
        resource='WLS' if method=='HF' else 'ANALYTIC';assert t['counts'][resource]==estimates
        if method=='HF':assert t['counts']['SOLVER']==starts
        integrity[name]=dict(status='PASS_SAVED_EVIDENCE',method=method,feedback_enabled=method!='OFF',physical_steps=60,terminal_tick=120,original_audits=t['audits'],audits_scope='cited original PASS receipts, original scientific audit functions not rerun',net=r['net'],components=r['components'],change=r['change_cost'],service=t['service_summary'],pending_D120_count=len(t['pending_D120']),counts=t['counts'])
        consumer[name]=dict(status='VERIFIED_SAVED_BINDINGS_NOT_CONSUMER_REPLAY',consumed=len(used),accepted=accepted,rejected=rejected)
    off=raw['H5_OFF_KEEP'];on=raw['H5_ON_KEEP'];early_off=[f for f in off['feedback'] if f['frame']['tick']<=80];early_on=[f for f in on['feedback'] if f['frame']['tick']<=80];assert len(early_off)==len(early_on)
    identity_diff=[]
    for x,y in zip(early_off,early_on):
        frame_binding(x,'H5_OFF_KEEP');frame_binding(y,'H5_ON_KEEP');rows=diff(x,y);assert all(identity(r['path']) and not r.get('missing_key') for r in rows),'KEEP_SCIENTIFIC_DIFFERENCE';identity_diff.extend(dict(tick=x['frame']['tick'],**r) for r in rows)
    frames_off=[f for f in off['frames'] if f['tick']<=80];frames_on=[f for f in on['frames'] if f['tick']<=80];assert not diff(frames_off,frames_on),'KEEP_PHYSICAL_DIFFERENCE'
    assert trace['H5_OFF_KEEP']['initial_service']==trace['H5_ON_KEEP']['initial_service'],'KEEP_INITIAL_SERVICE_DIFFERENCE'
    # Frozen analytic truth evaluated only for offline mathematics; no h5_motion import.
    v=physical['speed'];dt=physical['dt'];ts=physical['turn_start_tick']*dt;te=physical['turn_end_tick']*dt;omega=physical['turn_rate_radians_per_second'];turnangle=physical['turn_angle_radians'];p0=physical['position_D60']
    def truth(j,k):
        m=world['motion'][str(j)];t=k*dt
        if j!=0:return [x+y*(k-60)*dt for x,y in zip(m['position'],m['velocity'])]
        if t<=ts:return [p0[0]+v*(t-3.),p0[1]]
        tau=min(t,te)-ts;end=[p0[0]+v*(ts-3.)+v/omega*math.sin(omega*tau),p0[1]+v/omega*(1-math.cos(omega*tau))]
        if t<te:return end
        return [end[0]+v*(t-te)*math.cos(turnangle),end[1]+v*(t-te)*math.sin(turnangle)]
    def velocity(j,k):
        if j!=0:return list(world['motion'][str(j)]['velocity'])
        a=min(turnangle,max(0.,k*dt-ts)*omega);return [v*math.cos(a),v*math.sin(a)]
    motion_analysis={};decomposition={};indexes={}
    for name,t in trace.items():
        idx=index(t['control_records']);indexes[name]=idx;rows=[]
        for (j,tick),r in idx.items():
            k=r['actual_control_belief']['estimate_tick'];b=r['actual_control_belief'];assert math.dist(r['true_position'],truth(j,tick))<1e-12 and math.dist(r['true_velocity'],velocity(j,tick))<1e-12
            if k<60:rows.append(dict(target=j,tick=tick,status='NOT_IDENTIFIABLE'));continue
            pk=truth(j,k);vk=velocity(j,k);p=truth(j,tick);age=(tick-k)*dt;cap=b['last_observation_tick'] is not None and age>1.;assert cap==r['cap_applied']
            actual=vector_minus(r['prediction_position'],p)
            if cap:rows.append(dict(target=j,tick=tick,status='ORIGINAL_CAP_ACTIVE',estimate_tick=k,age=age,actual_position_error=actual,actual_velocity_error=vector_minus(r['prediction_velocity'],velocity(j,tick)),note='no uncapped decomposition applied'));continue
            pos=vector_minus(b['position_estimate'],pk);vel=[x*age for x in vector_minus(b['velocity_estimate'],vk)];mis=[x+y*age-z for x,y,z in zip(pk,vk,p)];residual=[x+y+z-a for x,y,z,a in zip(pos,vel,mis,actual)]
            assert max(abs(x) for x in residual)<1e-12,'UNCLIPPED_DECOMPOSITION_IDENTITY'
            rows.append(dict(target=j,tick=tick,status='UNCAPPED_IDENTITY',estimate_tick=k,age=age,position_estimation_error=pos,historical_velocity_estimation_times_age=vel,instantaneous_CV_future_mismatch=mis,actual_position_error=actual,roundoff_residual=residual))
        decomposition[name]=rows
    for method in ('HF','ON'):
        name='H5_'+method+'_KEEP';t=trace[name];f=next(f for f in t['freeze_records'] if f['tick']==80);b=f['actual_control_beliefs']['0'];k=b['estimate_tick'];event=next((e for e in t['actual_consumer_records'] if e['freeze_tick']==80 and e['target']==0 and e['measurement_tick']==k and e['accepted']),None)
        if event is None:motion_analysis[method]=dict(status='NOT_IDENTIFIABLE',actual_control_belief=b);continue
        s=event['reference_tick'];q=event['reference_position'];p=event['accepted_position'];mean=None if s is None else [(x-y)/((k-s)*dt) for x,y in zip(truth(0,k),truth(0,s))];unclipped=None if s is None else [(x-y)/((k-s)*dt) for x,y in zip(p,q)]
        if s is not None:assert event['reference_interval']==k-s>=5 and event['unclipped_difference_velocity']==unclipped and [s,q] in t['accepted_history']['0']
        estimated=b['velocity_estimate'];vk=velocity(0,k);vc=velocity(0,80);done=t['service_summary']['completion_tick']
        motion_analysis[method]=dict(status='IDENTIFIABLE',actual_event=event,actual_control_belief=b,reference_true_position=None if s is None else truth(0,s),accepted_true_position=truth(0,k),position_estimation_error=vector_minus(p,truth(0,k)),true_interval_mean_velocity=mean,actual_difference_velocity=unclipped,final_belief_velocity=estimated,true_velocity_at_estimate_tick=vk,true_velocity_at_control_tick=vc,velocity_vector_error_at_estimate_tick=math.dist(estimated,vk),velocity_vector_error_at_control_tick=math.dist(estimated,vc),speed_error=math.hypot(*estimated)-math.hypot(*vk),direction_error_rad=angle_delta(estimated,vk),estimate_minus_true_mean=None if mean is None else vector_minus(estimated,mean),true_mean_minus_anchor_velocity=None if mean is None else vector_minus(mean,vk),clipping_or_retention_effect=None if unclipped is None else vector_minus(estimated,unclipped),actual_difference_direction=heading(estimated),actual_instantaneous_direction=heading(vk),D100_control_status='TERMINAL_BELIEF_NOT_ACTIVE_CONTROL' if done is not None and done<=100 else 'SEE_VALID_CONTROL_RECORDS',interpretation='actual reference interval; no theoretical value used as acceptance gate')
    pairs={}
    for left,right in [('HF','ON'),('OFF','ON')]:
        for action in ACTIONS:
            ln='H5_'+left+'_'+action;rn='H5_'+right+'_'+action
            if ln not in indexes or rn not in indexes:continue
            il=indexes[ln];ir=indexes[rn];keys=sorted(il.keys()&ir.keys());row=dict(common_target_ticks=[list(k) for k in keys],denominator=len(keys),left_valid_count=len(il),right_valid_count=len(ir))
            for side,idx in [('left',il),('right',ir)]:
                for field in ('position_error','velocity_error'):row[side+'_'+field]=None if not keys else sum(idx[k][field] for k in keys)/len(keys)
            pairs[left+'/'+right+'/'+action]=row
    values={m:{a:raw['H5_'+m+'_'+a]['net'] for a in ACTIONS if 'H5_'+m+'_'+a in raw} for m in METHODS};matrix={a:{m:dict(status='VALID_SAVED_RESULT',value=values[m][a]) if a in values[m] else dict(status='NOT_RUN',value=None) for m in METHODS} for a in ACTIONS}
    errors={a:dict(signed_error=values['ON'][a]-values['HF'][a],AE=abs(values['ON'][a]-values['HF'][a])) for a in ACTIONS};ranks={}
    for method in ('HF','ON'):
        vv=values[method];top=max(vv.values());best=[a for a in ACTIONS if top-vv[a]<=1e-8];ranks[method]=dict(strict_order=sorted(ACTIONS,key=lambda a:-vv[a]),exact_ties=[[a for a in ACTIONS if vv[a]==value] for value in sorted(set(vv.values()),reverse=True)],epsilon=1e-8,epsilon_best=best,actual_selection='NOT_SPECIFIED',HF_regret={a:max(values['HF'].values())-values['HF'][a] for a in best})
    st_off=trace['H5_OFF_KEEP']['service_summary'];st_on=trace['H5_ON_KEEP']['service_summary'];ov=values['OFF']['KEEP'];nv=values['ON']['KEEP'];hv=values['HF']['KEEP'];layers={}
    for label,key in [('G','G_intervals'),('GQ','GQ_intervals'),('continuous_service','Pmax'),('completion','completion_tick')]:layers[label]='CHANGED' if st_off[key]!=st_on[key] else 'UNCHANGED'
    for label,key in [('actual_control','control'),('robot_trajectory','positions')]:layers[label]='CHANGED' if [f[key] for f in off['frames']]!=[f[key] for f in on['frames']] else 'UNCHANGED'
    layers['belief']='CHANGED' if [f['actual_control_beliefs'] for f in trace['H5_OFF_KEEP']['freeze_records']]!=[f['actual_control_beliefs'] for f in trace['H5_ON_KEEP']['freeze_records']] else 'UNCHANGED'
    layers['observations']='CHANGED' if [f['result']['payload'] for f in off['feedback']]!=[f['result']['payload'] for f in on['feedback']] else 'UNCHANGED';layers['Q']='CHANGED' if [f['result']['quality']['status'] for f in off['feedback']]!=[f['result']['quality']['status'] for f in on['feedback']] else 'UNCHANGED';layers['economic_value']='CHANGED' if ov!=nv else 'UNCHANGED'
    feedback=dict(FEEDBACK_EFFECT_IDENTIFIED='YES',FEEDBACK_BENEFIT_SUPPORTED='POSITIVE_NET_VALUE_EFFECT' if nv>ov else 'ZERO_NET_VALUE_EFFECT' if nv==ov else 'NEGATIVE_NET_VALUE_EFFECT',Delta_V_FB=nv-ov,I_FB=abs(ov-hv)-abs(nv-hv),mechanism_layers=layers,scope='conditional closed-loop total increment; not a single velocity-update causal effect')
    records=[json.loads(line) for line in (ROOT/'RESOURCE_EVENTS.jsonl').read_text().splitlines()];starts={};ends={};per=collections.defaultdict(collections.Counter)
    for row in records:
        cid=row['call_id']
        if row['status']=='STARTED':assert cid not in starts;starts[cid]=row;per[row['cell']][row['resource']]+=1
        else:assert cid in starts and cid not in ends and row['status'] in ('RETURNED','FAILED');ends[cid]=row
    assert starts.keys()==ends.keys(),'RESOURCE_CALL_CLOSURE';total=collections.Counter(row['resource'] for row in starts.values());assert dict(total)==source['counts']==receipt['current_scientific_counts']
    for method,action in CELLS:
        name='H5_'+method+'_'+action;p=per[name];saved=trace[name]['counts'];assert all(p[k]==saved[k] for k in ('WLS','SOLVER','ANALYTIC'))
        assert p['WLS']<=63 and p['SOLVER']<=600 and p['ANALYTIC']<=63
        assert all(starts[cid]['method']==method for cid in starts if starts[cid]['cell']==name)
        assert (p['ANALYTIC']==0 if method=='HF' else p['WLS']==p['SOLVER']==0)
    assert total['WLS']<=189 and total['SOLVER']<=1800 and total['ANALYTIC']<=252
    alogs=[json.loads(line) for line in (ROOT/'ANALYTIC_CALLS.jsonl').read_text().splitlines()];astarts={r['call_id']:r for r in alogs if r['status']=='STARTED'};aends={r['call_id']:r for r in alogs if r['status']!='STARTED'}
    assert len(astarts)==len(aends)==total['ANALYTIC'] and len(alogs)==len(astarts)*2 and astarts.keys()==aends.keys()
    for cid in astarts:assert astarts[cid]==starts[cid] and aends[cid]==ends[cid]
    resource=dict(status='PASS',started=len(starts),closed=len(ends),failed_internal_calls=sum(r['status']=='FAILED' for r in ends.values()),totals=dict(total),per_cell={n:dict(p) for n,p in per.items()},analytic_log_counted_as_subset=True,direct_scientific_estimate_calls=0,forbidden_original_evidence=dict(records_before_science=str(ROOT/'RUNTIME_BINDINGS_BEFORE_SCIENCE.json'),original_estimator_routes='preserved RAW diagnostics and per-cell counters matched',limitation='original per-call payload hashes absent; no nonexistent digest binding or new runtime monitor claimed'))
    comparisons={}
    for action in ACTIONS:
        hf=timing['H5_HF_'+action];on_t=timing['H5_ON_'+action];assert hf['core_scope']==on_t['core_scope'] and hf['complete_scope']==on_t['complete_scope']
        comparisons[action]=dict(HF=hf,ON=on_t,core_wall_ratio_HF_over_ON=hf['core']['wall']/on_t['core']['wall'],core_CPU_ratio_HF_over_ON=hf['core']['cpu']/on_t['core']['cpu'] if on_t['core']['cpu'] else None,complete_wall_ratio_HF_over_ON=hf['complete_cell']['wall']/on_t['complete_cell']['wall'])
    hf_wall=sum(timing['H5_HF_'+a]['core']['wall'] for a in ACTIONS);on_wall=sum(timing['H5_ON_'+a]['core']['wall'] for a in ACTIONS)
    timing_summary=dict(per_action=comparisons,HF_three_core_wall=hf_wall,ON_three_core_wall=on_wall,ratio_HF_over_ON=hf_wall/on_wall,scope='single paired run, same core boundary; method preparation separately recorded; full cell includes RAW, TRACE and audits; no repeated performance trials; not generic end-to-end advantage')
    protection_end={p:sha(p)==h for p,h in original.items()};assert all(protection_end.values()),'ORIGINAL_FILE_MODIFIED'
    limits=['FINAL_RUNTIME_BINDING_RECEIPT = NOT_VERIFIED; original final runtime receipt never generated; no replacement imports performed.','Pre-science binding receipt preserved and checked by source manifest; source hashes are offline protection evidence, not restored dynamic execution evidence.','Per-call payload digest was not saved in original resource log; preserved RAW/TRACE and method/per-cell counts provide cross-evidence, no fabricated per-call hash binding.','One deterministic H5 conditional world, only KEEP has ON/OFF pairing; no unknown-future, statistical robustness or Minimax Regret claims.','Resource accounting INCOMPLETE, overall compliance and generic end-to-end speedup NOT_ESTABLISHED; original two execution windows and failure records retained.']
    mae=sum(e['AE'] for e in errors.values())/3;relative={a+'-'+b:(values['ON'][a]-values['ON'][b])-(values['HF'][a]-values['HF'][b]) for a,b in itertools.combinations(ACTIONS,2)}
    result=dict(task='STFBS_LITE_FB_BLVF_H5_ARC_EXTENSION_001',subtask='ATTEMPT_002_OFFLINE_FINALIZATION',source_commit='7558e2aaa2286e3c4e65d81c21948820fd4de4c4',SOURCE_EXECUTION_STATUS='PARTIAL_RESULTS',OFFLINE_FINALIZATION_STATUS='PASS',SCIENTIFIC_REEXECUTION='NO',VALID_SCIENTIFIC_CELLS=7,NEW_SCIENTIFIC_STARTS=0,NEW_WLS_CALLS=0,NEW_SOLVER_CALLS=0,NEW_ANALYTIC_CALLS=0,NEW_CONSUMER_EXECUTIONS=0,NEW_TESTS=0,SCIENTIFIC_RESULT_STATUS='READY_FOR_INDEPENDENT_ACCEPTANCE',INDEPENDENT_SCIENTIFIC_ACCEPTANCE='PENDING',world_digest=world['world_digest'],physics_digest=physical['physics_digest'],seven_cell_integrity=integrity,consumer_saved_binding=consumer,KEEP_pairing=dict(status='PASS',feedback_pairs=len(early_off),physical_frame_pairs=len(frames_off),scientific_difference_count=0,identity_differences=identity_diff,explicit_identity_paths=PATTERNS,internal_identity_hash_binding='PASS'),H5_A_MOTION_ESTIMATION_FINDINGS=motion_analysis,propagation_analysis=decomposition,state_prediction_pairs=pairs,H5_B_FEEDBACK_SERVICE_FINDINGS=feedback,H5_C_CONDITIONAL_VALUE_FINDINGS=dict(matrix=matrix,errors=errors,MAE=mae,denominator=3,relative_errors=relative,rankings=ranks,OFF_scope=dict(actions=['KEEP'],complete_ranking='NOT_APPLICABLE',three_cell_MAE='NOT_APPLICABLE',regret='NOT_APPLICABLE')),H5_COMPUTATIONAL_SIMPLIFICATION_FINDINGS=resource,single_run_timing=timing_summary,original_manifest_checks=manifest_check,source_protection=protected,original_files_sha256=original,original_files_unchanged=all(protection_end.values()),FINAL_RUNTIME_BINDING_RECEIPT='NOT_VERIFIED',limits=limits,RESOURCE_ACCOUNTING='INCOMPLETE',RESOURCE_COMPLIANCE='NOT_ESTABLISHED',END_TO_END_SPEEDUP='NOT_ESTABLISHED')
    lines=['# H5-ARC ATTEMPT_002最小离线汇总恢复','', 'OFFLINE_FINALIZATION_STATUS = PASS','SCIENTIFIC_RESULT_STATUS = READY_FOR_INDEPENDENT_ACCEPTANCE','INDEPENDENT_SCIENTIFIC_ACCEPTANCE = PENDING','', '原科学提交：7558e2aaa2286e3c4e65d81c21948820fd4de4c4。原PARTIAL_RESULTS及失败堆栈保持不变。本次只用Python标准库核验保存数据，不导入项目模块，不执行consumer、估计器、运动推进或测试。','',f'七格完整结果及原单元内审计PASS得到保存证据核对。KEEP早期{len(early_off)}对观测及{len(frames_off)}对物理帧科学内容一致；{len(identity_diff)}处差异仅为明确身份字段及派生摘要。','', '| 动作 | HF | FB-ON | FB-OFF |','|---|---|---|---|']
    for action in ACTIONS:lines.append('| '+' | '.join([action]+[str(values[m][action]) if action in values[m] else 'NOT_RUN' for m in METHODS])+' |')
    lines+=['','## H5-A：区间平均速度、瞬时速度及传播失配','',json.dumps(motion_analysis,ensure_ascii=False,indent=2),'','D80速度滞后是实际差分区间对应的历史平均速度与瞬时速度之差。该分解不等于所有价值变化的单因素因果证明。逐目标—控制tick分解见JSON；超过一秒截断使用真实输出，不套用未截断公式。','', '## H5-B：反馈与服务','',json.dumps(feedback,ensure_ascii=False,indent=2),'',json.dumps({n:x['service'] for n,x in integrity.items()},ensure_ascii=False,indent=2),'','## H5-C：价值、排序及条件regret','',json.dumps(result['H5_C_CONDITIONAL_VALUE_FINDINGS'],ensure_ascii=False,indent=2),'','## 配对预测误差','',json.dumps(pairs,ensure_ascii=False,indent=2),'','## 科学调用闭合','',json.dumps(resource,ensure_ascii=False,indent=2),'','## 单次同口径计时','',json.dumps(timing_summary,ensure_ascii=False,indent=2),'','## 证据及科学解释限制','']+limits+['','历史审计PASS为原回执引用，没有在本次重新执行科学审计函数。H5与H4的差异仅可解释为不同条件世界整体差异，不能把全部差异归因于单一速度滞后。状态误差与价值预测误差分别判断，完成一致不等于全部状态一致。','', '## 资源','', '三个窗口分别保留：首次失败CPU小计1.046875秒、墙钟397.43556092950166秒；第二次科学执行CPU小计63.234375秒、墙钟124.95685481486726秒。本离线窗口资源见JSON，原累计写入12115003 bytes继续计入。不将独立窗口墙钟之和描述为单一连续授权窗口。未知宿主和退出尾部不记零。完成后停止，不登记H5正式关闭，不启动后续研究。']
    put('OFFLINE_FINALIZATION_REPORT.md','\n'.join(lines)+'\n');check()
    result['offline_resources']=dict(cpu_snapshot=time.process_time(),wall_snapshot=time.monotonic()-ORIGIN,wall_start_utc=START,prior_task_controlled_writes=PRIOR,operations=OPS,limits=dict(cpu=30,wall=900,task_cumulative_writes=LIMIT),previous_windows=dict(ATTEMPT_001=dict(cpu_known_subtotal=1.046875,wall_recorded=397.43556092950166,writes=122024),ATTEMPT_002=dict(cpu_known_subtotal=63.234375,wall_recorded=124.95685481486726,scientific_starts=7,WLS=total['WLS'],SOLVER=total['SOLVER'],ANALYTIC=total['ANALYTIC'])),task_cumulative_scientific_counts=dict(starts=8,valid=7,WLS=1+total['WLS'],SOLVER=total['SOLVER'],ANALYTIC=total['ANALYTIC']),unknown='host preparation, readonly tools and process-exit tail INCOMPLETE; snapshots are not complete final process CPU')
    encoded=''
    for _ in range(20):
        result['offline_resources']['task_cumulative_controlled_write_bytes']=WRITTEN+len(encoded.encode());result['offline_resources']['offline_controlled_write_bytes']=WRITTEN+len(encoded.encode())-PRIOR;new=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
        if len(new.encode())==len(encoded.encode()):encoded=new;break
        encoded=new
    assert result['offline_resources']['task_cumulative_controlled_write_bytes']==WRITTEN+len(encoded.encode())
    put('OFFLINE_FINALIZATION.json',encoded)
    print(json.dumps(dict(status='PASS',valid=7,MAE=mae,rankings=ranks,KEEP_feedback=feedback,D80_motion={m:dict(reference_tick=x['actual_event']['reference_tick'],estimate_tick=x['actual_control_belief']['estimate_tick'],velocity_error=x['velocity_vector_error_at_estimate_tick'],direction_error=x['direction_error_rad']) for m,x in motion_analysis.items()},pairing=dict(feedback_pairs=len(early_off),physical_pairs=len(frames_off),identity_differences=len(identity_diff)),resource_counts=dict(total),closed=len(ends),HF_core_wall=hf_wall,ON_core_wall=on_wall,core_wall_ratio=hf_wall/on_wall,offline_resources=result['offline_resources']),ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        # Only the two authorized output names are used, including on failure.
        record=dict(OFFLINE_FINALIZATION_STATUS='STOPPED',type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),new_scientific_starts=0,new_estimator_calls=0,cpu_snapshot=time.process_time(),wall_snapshot=time.monotonic()-ORIGIN)
        try:
            if not (ROOT/'OFFLINE_FINALIZATION.json').exists():put('OFFLINE_FINALIZATION.json',json.dumps(record,ensure_ascii=False,indent=2,allow_nan=False))
        except BaseException:pass
        print(json.dumps(record,ensure_ascii=False));sys.exit(1)
