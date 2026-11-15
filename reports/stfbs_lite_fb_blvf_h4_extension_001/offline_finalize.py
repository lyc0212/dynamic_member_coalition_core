"""Read saved JSON only. No project/scientific imports or scientific execution."""
import collections,datetime,hashlib,itertools,json,math,re,sys,time,traceback
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1]
START='2026-11-15T13:48:08.3822075+08:00'
ORIGIN=time.monotonic()-(time.time()-datetime.datetime.fromisoformat(START).timestamp())
PRIOR_WRITE=8334160;LIMIT=134217728;WRITTEN=PRIOR_WRITE+Path(__file__).stat().st_size
OPS=[dict(file=Path(__file__).name,bytes=Path(__file__).stat().st_size)]
ACTIONS=('KEEP','SWITCH','MEMBER_CHANGE')
CELLS=('BLVF_OFF_KEEP','BLVF_ON_KEEP','BLVF_ON_SWITCH','BLVF_ON_MEMBER_CHANGE')
def check():
    assert 0<=time.monotonic()-ORIGIN<900,'OFFLINE_WALL_LIMIT'
    assert time.process_time()<30,'OFFLINE_CPU_LIMIT'
    assert WRITTEN<LIMIT,'CUMULATIVE_WRITE_LIMIT'
def read(p):check();return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def put(name,data):
    global WRITTEN
    check();b=data.encode();assert WRITTEN+len(b)<=LIMIT
    with (ROOT/name).open('xb') as f:
        n=f.write(b);f.flush();assert n==len(b)
    WRITTEN+=n;OPS.append(dict(file=name,bytes=n));return n
def diffs(a,b,p=''):
    if type(a)!=type(b):return [dict(path=p,OFF=a,ON=b)]
    if isinstance(a,dict):
        out=[]
        for k in sorted(a.keys()|b.keys()):
            if k not in a or k not in b:out.append(dict(path=p+'/'+k,OFF=a.get(k),ON=b.get(k),missing_key=True))
            else:out.extend(diffs(a[k],b[k],p+'/'+k))
        return out
    if isinstance(a,list):
        if len(a)!=len(b):return [dict(path=p,OFF_length=len(a),ON_length=len(b))]
        return [r for i,(x,y) in enumerate(zip(a,b)) for r in diffs(x,y,p+'/'+str(i))]
    return [] if a==b else [dict(path=p,OFF=a,ON=b)]
IDENTITY_PATTERNS=(r'/branch',r'/frame/(stream_id|frame_id)',r'/frame/records/\d+/packet_id',r'/result/(frame_sha256|frame_id|stream_id)',r'/result/normalized_frame/(stream_id|frame_id)',r'/result/normalized_frame/records/\d+/packet_id',r'/result/quality/frame_id',r'/endpoint/branch',r'/endpoint/quality/frame_id')
def identity_path(p):return any(re.fullmatch(pattern,p) for pattern in IDENTITY_PATTERNS)
def frame_binding(f,branch):
    frame=f['frame'];r=f['result'];q=r['quality'];endpoint=f['endpoint'];nf=r['normalized_frame']
    assert f['branch']==endpoint['branch']==branch
    assert frame['frame_id']==r['frame_id']==nf['frame_id']==q['frame_id']==endpoint['quality']['frame_id']
    assert frame['stream_id']==r['stream_id']==nf['stream_id'] and frame['stream_id'].startswith(branch+':')
    assert frame['frame_id']==frame['stream_id']+':tick'+str(frame['tick'])
    assert r['frame_sha256']==digest(nf)
    assert r['payload_sha256']==digest(r['payload'])==q['payload_sha256']==endpoint['quality']['payload_sha256']
    assert endpoint['quality']==q and endpoint['target_id']==frame['target_id']==r['target_id']==nf['target_id']
    for record in frame['records']:assert record['packet_id']==frame['frame_id']+':'+record['sensor_id']

def main():
    check();original={p.relative_to(ROOT).as_posix():sha(p) for p in ROOT.rglob('*') if p.is_file() and p.name!='offline_finalize.py'}
    manifest=read(ROOT/'FILE_SHA256.json');manifest_checks={name:sha(ROOT/name)==v['sha256'] and (ROOT/name).stat().st_size==v['bytes'] for name,v in manifest.items()};assert all(manifest_checks.values()),'ORIGINAL_MANIFEST_MISMATCH'
    config=read(ROOT/'EXPERIMENT_CONFIG.json');failure=read(ROOT/'FINAL_REPORT.json');assert failure['status']=='PARTIAL_RESULTS' and failure['started']==failure['valid']==4
    source_checks={p:sha(p)==h for p,h in config['code_sources'].items()};assert all(source_checks.values()),'SOURCE_BINDING_MISMATCH'
    refs=read(REPO/'reports/stfbs_lite_target_turn_exploration_001/ATTEMPT_003/VALUE_MATRIX.json')
    for info in config['historical_comparability'].values():assert sha(info['source'])==info['sha256']
    candidate_path=Path(read(REPO/'reports/stfbs_lite_h2_h3_extension_005/H3_KEEP/authorization.json')['candidate_path']);c=read(candidate_path)['candidate'];view=c['a2_policy_view'];seed=c['consumer_seed']
    assert digest(view)==config['D60_view_digest'] and digest(seed)==config['seed_digest'] and not seed['pending_observations']
    candidates=read(REPO/'reports/stfbs_lite_h2_h3_extension_005/CANDIDATE_FREEZE.json')
    raw={name:read(ROOT/('RAW/'+name+'.json')) for name in CELLS};trace={name:read(ROOT/('TRACE/'+name+'.json')) for name in CELLS}
    off=raw[CELLS[0]];on=raw[CELLS[1]];fo=[f for f in off['feedback'] if 61<=f['frame']['tick']<=80];fn=[f for f in on['feedback'] if 61<=f['frame']['tick']<=80]
    assert len(fo)==len(fn)==20 and [f['frame']['tick'] for f in fo]==[f['frame']['tick'] for f in fn]==list(range(61,81))
    identity_differences=[]
    for x,y in zip(fo,fn):
        frame_binding(x,CELLS[0]);frame_binding(y,CELLS[1]);rows=diffs(x,y)
        assert all(identity_path(row['path']) and not row.get('missing_key') for row in rows),'NON_IDENTITY_FEEDBACK_DIFFERENCE'
        identity_differences.extend(dict(tick=x['frame']['tick'],**row) for row in rows)
    before_off=[f for f in off['frames'] if f['tick']<=80];before_on=[f for f in on['frames'] if f['tick']<=80]
    assert len(before_off)==20 and not diffs(before_off,before_on),'PRE_D80_PHYSICAL_DIFFERENCE'
    assert trace[CELLS[0]]['initial_service']==trace[CELLS[1]]['initial_service'],'INITIAL_SERVICE_DIFFERENCE'
    cells={};consumer_bindings={}
    for name in CELLS:
        check();r=raw[name];t=trace[name];action=next(a for a in ACTIONS if name.endswith(a));actions=next(row['actions'] for row in candidates if row['kind']==action)
        assert r['branch']==name and r['world']==config['world'] and len(r['frames'])==60 and [f['tick'] for f in r['frames']]==list(range(61,121))
        assert r['boundaries'][0]['tick']==60 and r['boundaries'][0]['after']==actions
        assert [d['view']['tick'] for d in r['decisions']]==[80,100] and [f['tick'] for f in t['freeze_records']]==[80,100]
        assert all(b['before']==b['after'] and b['cost']==0 and b['changes']==0 for b in r['boundaries'] if b['tick'] in (80,100))
        assert set(t['audits'])=={'history','service','physical_economic','actual_control'} and all(v['status']=='PASS' for v in t['audits'].values())
        assert all(row['status']=='PASS' for row in t['hold_checks']) and len(t['hold_checks'])==2
        assert sum(r['components'].values())-r['change_cost']==r['net']==t['audits']['physical_economic']['net']
        assert 'pending_D120' in t and all(row['available_tick']>100 and row['available_tick']<=120 for row in t['pending_D120'])
        if name==CELLS[0]:assert all(f['actual_control_beliefs']==view['beliefs'] for f in t['freeze_records'])
        else:assert all(f['actual_control_beliefs']==f['shadow_beliefs'] for f in t['freeze_records'])
        own={(f['frame']['frame_id'],f['frame']['target_id'],f['frame']['tick']):f for f in r['feedback']};used=set();bindings=[]
        for row in t['actual_consumer_records']:
            key=(row['frame_id'],row['target'],row['measurement_tick']);assert key in own and key not in used;used.add(key);f=own[key]
            assert row['available_tick']<=row['consumed_tick']==row['freeze_tick'] and row['freeze_tick'] in (80,100)
            assert row['provenance']=='SIMULATED' and row['observation_origin']=='MODEL' and row['Q']==f['result']['quality']['status']
            assert row['accepted']==(not row['rejection_reasons'])
            if row['accepted']:
                assert [row['measurement_tick'],row['accepted_position']] in t['accepted_history'][str(row['target'])]
                assert row['accepted_position']==f['result']['estimate_result']['estimate']
            bindings.append(dict(frame_id=row['frame_id'],accepted=row['accepted'],measurement_tick=row['measurement_tick'],consumed_tick=row['consumed_tick'],reasons=row['rejection_reasons']))
        consumer_bindings[name]=dict(status='VERIFIED_FROM_SAVED_RECORDS_NOT_REPLAY',records=len(bindings),accepted=sum(b['accepted'] for b in bindings),rejected=sum(not b['accepted'] for b in bindings))
        cells[name]=dict(status='ACCEPTED_FOR_OFFLINE_SUMMARY_PENDING_INDEPENDENT_REVIEW',steps=60,end_tick=120,world_digest=r['world']['world_digest'],initial_action=actions,original_audits=t['audits'],original_audits_scope='original saved PASS records cited; no scientific audit functions rerun',OFF_D60_control_check='PASS' if name==CELLS[0] else 'NOT_APPLICABLE',ON_control_matches_consumer_shadow='NOT_APPLICABLE' if name==CELLS[0] else 'PASS',pending_D120_count=len(t['pending_D120']),service=t['service_summary'],components=r['components'],change=r['change_cost'],net=r['net'])
    logs=[json.loads(line) for line in (ROOT/'ANALYTIC_CALLS.jsonl').read_text().splitlines()];starts={};ends={};per=collections.Counter()
    for row in logs:
        key=row['call_id']
        if row['status']=='STARTED':assert key not in starts;starts[key]=row;per[row['cell']]+=1
        else:assert key in starts and key not in ends and row['status']=='RETURNED';ends[key]=row
    assert starts.keys()==ends.keys() and len(starts)<=252 and all(row['scope']=='SCIENCE' for row in starts.values())
    for name in CELLS:
        assert per[name]<=63 and per[name]==trace[name]['analytic_calls']==sum(f['result']['estimator_called'] for f in raw[name]['feedback'])
    assert len(starts)==failure['analytic_counts']['total']==205
    for r in raw.values():
        for f in r['feedback']:
            e=f['result']['estimate_result']
            if e is not None:assert e['estimator_method']=='ANALYTIC_BEARING_INTERSECTION' and e['nonlinear_solver_starts']==0 and e['starts']==[]
    hf={a:refs[a]['H4_HF'] for a in ACTIONS};cap={a:refs[a]['H4_CAP'] for a in ACTIONS};onvalues={a:raw['BLVF_ON_'+a]['net'] for a in ACTIONS}
    values={a:dict(CAP=cap[a],FB_OFF=off['net'] if a=='KEEP' else 'NOT_RUN',FB_ON=onvalues[a],HF=hf[a]) for a in ACTIONS}
    methods={}
    for label,v in [('CAP',cap),('FB_ON',onvalues)]:
        best=[a for a in ACTIONS if max(v.values())-v[a]<=1e-8];errors={a:dict(signed_error=v[a]-hf[a],AE=abs(v[a]-hf[a])) for a in ACTIONS}
        methods[label]=dict(errors=errors,MAE=sum(e['AE'] for e in errors.values())/3,denominator=3,strict_order=sorted(ACTIONS,key=lambda a:-v[a]),epsilon_best=best,HF_regret={a:max(hf.values())-hf[a] for a in best},actual_selection='NOT_SPECIFIED',relative_errors={a+'-'+b:(v[a]-v[b])-(hf[a]-hf[b]) for a,b in itertools.combinations(ACTIONS,2)})
    effect=dict(structure_value_effect=off['net']-cap['KEEP'],feedback_value_effect=on['net']-off['net'],feedback_accuracy_improvement=abs(off['net']-hf['KEEP'])-abs(on['net']-hf['KEEP']))
    def pred_index(rows):
        out={}
        for row in rows:
            key=(row['target'],row['tick'])
            if key in out:assert row['prediction_position']==out[key]['prediction_position'] and row['prediction_velocity']==out[key]['prediction_velocity']
            else:out[key]=row
        return out
    io=pred_index(trace[CELLS[0]]['control_records']);ino=pred_index(trace[CELLS[1]]['control_records']);common=sorted(io.keys()&ino.keys());paired=dict(denominator=len(common),common_target_ticks=[list(k) for k in common])
    for mode,index in [('OFF',io),('ON',ino)]:
        for field in ('position_error','velocity_error'):paired[mode+'_'+field]=sum(index[k][field] for k in common)/len(common) if common else None
    existing=read(ROOT/'SCIENTIFIC_ANALYSIS.json')['mechanisms']['KEEP']['paired_prediction']
    assert paired['denominator']==existing['denominator'] and paired['common_target_ticks']==[[r['target'],r['tick']] for r in existing['common_keys']]
    for k in ('OFF_position_error','ON_position_error','OFF_velocity_error','ON_velocity_error'):assert paired[k]==existing[k]
    layers={};st0=trace[CELLS[0]]['service_summary'];st1=trace[CELLS[1]]['service_summary']
    layers['belief']='CHANGED' if [f['actual_control_beliefs'] for f in trace[CELLS[0]]['freeze_records']]!=[f['actual_control_beliefs'] for f in trace[CELLS[1]]['freeze_records']] else 'UNCHANGED'
    for label,field in [('actual_control','control'),('robot_trajectory','positions')]:layers[label]='CHANGED' if [f[field] for f in off['frames']]!=[f[field] for f in on['frames']] else 'UNCHANGED'
    layers['observations_and_Q']='CHANGED' if [(f['result']['payload'],f['result']['quality']['status']) for f in off['feedback']]!=[(f['result']['payload'],f['result']['quality']['status']) for f in on['feedback']] else 'UNCHANGED'
    for label,key in [('G_intervals','G_intervals'),('GQ_intervals','GQ_intervals'),('continuous_progress','Pmax'),('completion','completion_tick')]:layers[label]='CHANGED' if st0[key]!=st1[key] else 'UNCHANGED'
    layers['economic_value']='CHANGED' if off['net']!=on['net'] else 'UNCHANGED'
    freeze=next(f for f in trace[CELLS[1]]['freeze_records'] if f['tick']==80);b=freeze['actual_control_beliefs']['0'];event=next(e for e in trace[CELLS[1]]['actual_consumer_records'] if e['freeze_tick']==80 and e['target']==0 and e['measurement_tick']==b['estimate_tick'] and e['accepted']);s=event['reference_tick'];k=event['measurement_tick'];p=event['accepted_position'];q=event['reference_position'];delta=[(x-y)/((k-s)*.05) for x,y in zip(p,q)]
    assert event['reference_interval']==k-s>=5 and event['unclipped_difference_velocity']==delta
    hist=trace[CELLS[1]]['accepted_history']['0'];assert [s,q] in hist and [k,p] in hist
    spec=config['physical_definition'];turn=spec['turn_tick'];before=spec['velocity_before'];after=spec['velocity_after'];basepos=spec['position_D60']
    def true_position(t):return [x+v*(min(t,turn)-60)*.05+w*max(0,t-turn)*.05 for x,v,w in zip(basepos,before,after)]
    # Offline truth arithmetic only; never fed back to consumer or estimator.
    adaptation=dict(freeze_tick=80,accepted_event=event,actual_control_belief=b,velocity_difference=delta,reference_position_error=math.dist(q,true_position(s)),accepted_position_error=math.dist(p,true_position(k)),true_velocity_at_control_tick=after if 80>=turn else before,true_velocity_at_estimate_tick=after if k>=turn else before,velocity_error_at_control_tick=math.dist(b['velocity_estimate'],after if 80>=turn else before),velocity_error_at_estimate_tick=math.dist(b['velocity_estimate'],after if k>=turn else before),reference_class='PRE_TURN' if k<=turn else 'CROSSES_TURN' if s<turn else 'POST_TURN')
    assert all(sha(ROOT/name)==h for name,h in original.items()),'ORIGINAL_FILE_CHANGED'
    limitations=['Original worker complete runtime module-import receipt was never saved: NOT_VERIFIED; no replacement runtime receipt fabricated.','HF KEEP is ATTEMPT_002 RAW accepted offline with missing original terminal memory and some historical objects.','Single deterministic H4 world, fixed-action conditional value evaluation, only KEEP paired; no claim of general unknown-future prediction.','Resource accounting INCOMPLETE, resource compliance NOT_ESTABLISHED, end-to-end speedup NOT_ESTABLISHED.','Original PARTIAL_RESULTS, failure and all original data retained unchanged.']
    result=dict(task='STFBS_LITE_FB_BLVF_H4_EXTENSION_001_OFFLINE_FINALIZATION',source_commit='4a831fc734e88aad0e88d508ae902a61a13a2b28',SOURCE_EXECUTION_STATUS='PARTIAL_RESULTS',OFFLINE_FINALIZATION_STATUS='PASS',SCIENTIFIC_REEXECUTION='NO',VALID_SCIENTIFIC_CELLS=4,NEW_SCIENTIFIC_STARTS=0,NEW_ANALYTIC_CALLS=0,NEW_SCIENTIFIC_WORKERS=0,SCIENTIFIC_RESULT_STATUS='READY_FOR_INDEPENDENT_ACCEPTANCE',INDEPENDENT_SCIENTIFIC_ACCEPTANCE='PENDING',original_manifest_checks=manifest_checks,source_bindings=source_checks,original_files_sha256=original,pre_D80_pairing=dict(status='PASS',feedback_pairs=20,physical_frames=20,scientific_differences=0,identity_differences=identity_differences,allowed_paths=IDENTITY_PATTERNS,internal_frame_payload_quality_bindings='VERIFIED'),cells=cells,consumer_saved_record_bindings=consumer_bindings,matrix=values,methods=methods,OFF_scope=dict(valid_actions=['KEEP'],signed_error=off['net']-hf['KEEP'],AE=abs(off['net']-hf['KEEP']),full_ranking='NOT_IDENTIFIABLE',three_cell_MAE='NOT_APPLICABLE',regret='NOT_APPLICABLE'),KEEP_effect=effect,KEEP_mechanism_layers=layers,KEEP_paired_prediction=paired,D80_adaptation=adaptation,analytic_call_audit=dict(status='PASS',starts=len(starts),closed=len(ends),per_cell=dict(per),direct=0,actual_rerun=False),forbidden_calls=dict(original_recorded=failure['forbidden_entry_counts'],offline='0 scientific calls; standard-library JSON arithmetic only; no original runtime monitor rerun'),limits=limitations,RESOURCE_ACCOUNTING='INCOMPLETE',RESOURCE_COMPLIANCE='NOT_ESTABLISHED',END_TO_END_SPEEDUP='NOT_ESTABLISHED',H5_ARC_EXECUTION_AUTHORIZATION='NOT_GRANTED',PRODUCTION_ADMISSION='BLOCKED')
    lines=['# H4 BLVF四格结果最小离线汇总核验','', 'OFFLINE_FINALIZATION_STATUS = PASS','SCIENTIFIC_RESULT_STATUS = READY_FOR_INDEPENDENT_ACCEPTANCE','INDEPENDENT_SCIENTIFIC_ACCEPTANCE = PENDING','', '原科学提交：4a831fc734e88aad0e88d508ae902a61a13a2b28。原PARTIAL_RESULTS及失败记录保持不变。本次仅核验保存JSON，不导入项目模块，不执行consumer、解析估计或仿真。','', '## 科学内容及身份','',f'D61—D80共20对反馈、20个物理帧科学内容一致。递归差异{len(identity_differences)}处均位于明确身份白名单；分支内frame、packet、quality、payload和frame摘要关联分别核验。未删除传感器ID、目标ID、tick或payload摘要。','', '| 动作 | CAP | FB-OFF | FB-ON | HF |','|---|---|---|---|---|']
    for a,row in values.items():lines.append('| '+' | '.join([a]+[str(row[k]) for k in ('CAP','FB_OFF','FB_ON','HF')])+' |')
    lines+=['','## 完整ON分析及KEEP反馈效应','',json.dumps(dict(methods=methods,KEEP_effect=effect,mechanism_layers=layers,paired_prediction=paired),ensure_ascii=False,indent=2),'','## D80合法转向适应','',json.dumps(adaptation,ensure_ascii=False,indent=2),'','## 四格服务与经济','',json.dumps({name:dict(service=row['service'],components=row['components'],change=row['change'],net=row['net']) for name,row in cells.items()},ensure_ascii=False,indent=2),'','## 调用闭合及证据范围','',json.dumps(result['analytic_call_audit'],ensure_ascii=False,indent=2),'','原单元内四类审计PASS为历史保存回执引用，未重新执行其科学函数。205次解析记录根据日志重新核对闭合；禁止调用依据原回执、源码路由和保存方法字段，未伪造动态监测回执。','', '## 解释限制','']+limitations+['','离线CPU、墙钟及计入原8334160 bytes后的受控累计写入见OFFLINE_FINALIZATION.json。未知宿主开销及进程退出尾部不记零；不宣称完整资源合规。完成后停止，不启动后续实验。']
    put('OFFLINE_FINALIZATION_REPORT.md','\n'.join(lines)+'\n')
    check();result['offline_resources']=dict(cpu_snapshot=time.process_time(),wall_snapshot=time.monotonic()-ORIGIN,wall_start_utc=START,prior_cpu_measured_subtotal=37.859375,prior_wall_recorded=375.8997876001231,prior_writes=PRIOR_WRITE,operations=OPS,unknown='host preparation/read-only tools and process exit tail INCOMPLETE',cpu_limit=30,wall_limit=900,cumulative_write_limit=LIMIT)
    encoded=''
    for _ in range(20):
        result['offline_resources']['task_cumulative_write_bytes']=WRITTEN+len(encoded.encode());result['offline_resources']['offline_controlled_write_bytes']=WRITTEN+len(encoded.encode())-PRIOR_WRITE
        new=json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n'
        if len(new.encode())==len(encoded.encode()):encoded=new;break
        encoded=new
    assert result['offline_resources']['task_cumulative_write_bytes']==WRITTEN+len(encoded.encode())
    put('OFFLINE_FINALIZATION.json',encoded)
    print(json.dumps(dict(status='PASS',valid=4,scientific_reexecution='NO',matrix=values,methods=methods,KEEP_effect=effect,D80_velocity_error=adaptation['velocity_error_at_control_tick'],paired_prediction=paired,identity_differences=len(identity_differences),closed=len(ends),resources=result['offline_resources']),ensure_ascii=False))

if __name__=='__main__':
    try:main()
    except BaseException as exc:
        failure=dict(status='STOPPED',type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc(),cpu=time.process_time(),wall=time.monotonic()-ORIGIN,scientific_starts=0,analytic_calls=0)
        try:put('OFFLINE_FINALIZATION_FAILURE.json',json.dumps(failure,ensure_ascii=False,indent=2,allow_nan=False))
        except BaseException:pass
        print(json.dumps(failure,ensure_ascii=False));sys.exit(1)
