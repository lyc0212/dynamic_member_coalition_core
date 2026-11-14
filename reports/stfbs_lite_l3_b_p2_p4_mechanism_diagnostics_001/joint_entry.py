"""Authorized P2-P4 joint diagnosis; frozen P1 read-only; at most 18 new cells."""
import sys,os,time,json,hashlib,copy,traceback,subprocess,ctypes,math,itertools,html
from pathlib import Path
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[1]
STAGE=REPO/'reports/l3_b_stage_a_minimal_remediation_execution_001_20261114121457';HISTORY=REPO/'reports/l3_b_diagnostic_recovery_001_stage_a_20261114';S=REPO/'reports/stfbs_lite_h2_h3_extension_005';P=REPO/'reports/stfbs_lite_l3_b_p1_reproduction_001'
sys.path.insert(0,str(STAGE))
from recovery import Writer,Clock,require,plain,typed,digest,HistoricalImports,build_kernel,boundary_check,controller,prediction,Replay,event_catalog,source_order_evidence,verify_replay_snapshot,TraceRecorder,trajectory_metrics,value_metrics,ledger_check,economic_reconciliation,feedback_chain,final_status,REQUIRED_GATES
HEAD='0f9e99a2a2590d2e13b617635894a4fac0e74474';VERSIONS=('P1','P2','P3','P4');ACTIONS=('KEEP','SWITCH','MEMBER_CHANGE')
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def fingerprint(x):return digest(plain(x))
def error(exc,phase):return dict(phase=phase,type=type(exc).__name__,message=str(exc),traceback=traceback.format_exc())
def pending_core(rows):return [{k:plain(r[k]) for k in ('target_id','measurement_tick','available_tick','estimate')} for r in rows]
def bootstrap(w,clock):
    require(Path(sys.executable).resolve()==Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\python.exe').resolve(),'PYTHON_IDENTITY')
    require(sha(STAGE/'recovery.py')==read(STAGE/'MANIFEST.json')['files']['recovery.py']['sha256'],'ACCEPTED_KERNEL_SHA')
    require('P1_SCIENTIFIC_REPRODUCTION = PASS' in (P/'P1_FINAL_INDEPENDENT_ACCEPTANCE.md').read_text(encoding='utf-8'),'P1_NOT_CLOSED')
    config=read(P/'EXECUTION_CONFIG.json');require(config['kernel_sha256']==sha(STAGE/'recovery.py'),'P1_KERNEL_IDENTITY')
    site=Path(r'D:\miniconda3\envs\dynamic_member_coalition_core\Lib\site-packages');sys.path.insert(0,str(site));pins=read(HISTORY/'HISTORICAL_IDENTITY.json');guard=HistoricalImports(HISTORY/'historical',pins);guard.install()
    import importlib,numpy,scipy
    proxy=importlib.import_module('research.non_oracle.stfbs_lite_proxy');from pursuit_v2.service import ServiceState
    require(numpy.__version__=='2.1.3' and scipy.__version__=='1.15.3','SCIENTIFIC_ENVIRONMENT')
    for m in (numpy,scipy):require(Path(m.__file__).resolve().is_relative_to(site.resolve()),'SCIENTIFIC_PACKAGE_ORIGIN')
    bindings=read(P/'INPUT_BINDINGS.json');p1=read(P/'P1_RESULTS.json');p1metrics=read(P/'P1_METRICS.json');raw_view=read(S/'PUBLIC_INPUT_FREEZE.json');worlds=read(S/'WORLD_LIBRARY.json')['worlds'];mapping=read(S/'MODEL_WORLD_MAPPING.json');candidate=read(S/'CANDIDATE_FREEZE.json')
    require(len(bindings)==len(p1)==6,'P1_BASELINE_COUNT');original_manifest=read(S/'archive_evidence_manifest.json')
    protected={}
    for n in ('PUBLIC_INPUT_FREEZE.json','WORLD_LIBRARY.json','MODEL_WORLD_MAPPING.json','CANDIDATE_FREEZE.json'):
        expected=next(x['sha256'] for x in original_manifest['files'] if x['path']==n);require(sha(S/n)==expected,'FROZEN_INPUT_SHA/'+n);protected[str(S/n)]=expected
    for p in (P/'P1_RESULTS.json',P/'P1_METRICS.json',P/'INPUT_BINDINGS.json',P/'P1_FINAL_INDEPENDENT_ACCEPTANCE.md',STAGE/'recovery.py',HISTORY/'HISTORICAL_IDENTITY.json',REPO/'pursuit_v2/policies.py'):protected[str(p)]=sha(p)
    def make_view():
        v=copy.deepcopy(raw_view)
        for k in ('beliefs','service_states','current_endpoints','current_q','public_profiles'):v[k]={int(j):x for j,x in v[k].items()}
        for ep in v['current_endpoints'].values():
            if ep is not None:ep['team']=tuple(tuple(x) for x in ep['team'])
        v['service_states']={j:ServiceState(base=x['base'],intervals=x['intervals'],team=tuple(tuple(y) for y in x['team'])) for j,x in v['service_states'].items()};return v
    cells={};traces={};hf={};baseline={}
    for b in bindings:
        clock.check();name=b['cell'];world_name=name[:2];action=name[3:];mw=mapping[world_name];wd=mw['perturbation']['stfbs_world_digest'];require(wd==b['original_world_digest'] and mw['world_digest']==b['model_world_digest'],'P1_WORLD_BINDING')
        world=copy.deepcopy(next(x for x in worlds if x['world_digest']==wd));world['motion']={int(k):x for k,x in world['motion'].items()};c=next(x for x in candidate if x['kind']==action);require(c['actions']==b['actions'],'P1_ACTION_BINDING');require(proxy.world_digest(world)==wd and proxy.public_input_digest(make_view())==world['public_input_digest'],'PUBLIC_WORLD_IDENTITY')
        cells[name]=dict(binding=b,world=world,actions=copy.deepcopy(c['actions']));traces['P1/'+name]=read(P/'TRACE'/(''+name+'.json'));baseline[name]=next(x for x in p1metrics['cells'] if x['world']==world_name and x['action']==action);require(baseline[name]['P1']==p1[name]['value'] and baseline[name]['HF_status']=='VERIFIED_ARCHIVED_IDENTITY','P1_HF_LABEL');hf[name]=baseline[name]['HF']
    source=HISTORY/'historical/research/non_oracle/stfbs_lite_proxy.py';kernel,ns=build_kernel(source.read_text(encoding='utf-8'))
    ctx=dict(w=w,clock=clock,pins=pins,guard=guard,proxy=proxy,make_view=make_view,cells=cells,results={'P1':p1,'P2':{},'P3':{},'P4':{}},traces=traces,hf=hf,baseline=baseline,kernel=kernel,ns=ns,protected=protected,feedback={},feedback_status={},calls={'P2':0,'P3':0,'P4':0},failures=[],shared_fault=None,scientific_checks={},environment=dict(python=sys.executable,version=sys.version,numpy=dict(version=numpy.__version__,path=numpy.__file__),scipy=dict(version=scipy.__version__,path=scipy.__file__)))
    w.json('EXPERIMENT_CONFIG.json',dict(task='STFBS_LITE_L3_B_P2_P4_MECHANISM_DIAGNOSTICS_001',git_head=HEAD,p1_accepted_commit='0ba1daf8cd9e1f34064d0b654bf33619738e9ea8',entry_sha256=sha(__file__),kernel_sha256=sha(STAGE/'recovery.py'),limits=dict(cpu=120,wall=1800,cumulative_logical_write_bytes=134217728),environment=ctx['environment'],bindings=bindings,interventions=dict(P2='NoCap fixed D60',P3='Cap fixed historical feedback',P4='NoCap same fixed historical feedback'),comparison_pairs=['P2/P1','P3/P1','P4/P3','P4/P2'],control_atol=0.,epsilon_best=1e-8,feedback_interpretation='fixed historical information, not endogenous sensor observability',controller_prediction_changed='NoCap compared with Cap at SAME belief/time; not feedback effect',seed='deterministic archived world identity; no new random seed'))
    return ctx

def prepare_feedback(ctx,name):
    w=ctx['w'];clock=ctx['clock'];d=S/name;em=read(d/'evidence_manifest.json');files={x['path']:x['sha256'] for x in em['files']};source_files={}
    def verified(n):
        clock.check();p=d/n;require(n in files and sha(p)==files[n],'FEEDBACK_EVIDENCE_SHA/'+n);source_files[str(p)]=files[n];return read(p)
    raw=verified('BRANCH_RAW.json');tx={t:verified('D%d_TRANSACTION.json'%t) for t in (60,80,100)};snaps={t:verified('BELIEF_PROVENANCE_D%d.json'%t) for t in (60,80,100)};terminal=verified('TERMINAL_BRANCH_HISTORY.json');pending120=verified('D120_PENDING_OBSERVATIONS.json');details=verified('ENDPOINT_CONNECTION_DETAILS.json');auth=verified('authorization.json')
    require(raw['world']['world_digest']==ctx['cells'][name]['binding']['model_world_digest'],'FEEDBACK_WORLD');require(raw['boundaries'][0]['after']==ctx['cells'][name]['actions'],'FEEDBACK_ACTION');require(raw['net']==ctx['hf'][name],'HF_LABEL_IDENTITY')
    cp=Path(auth['candidate_path']);candidate_record=read(cp);seed=copy.deepcopy(candidate_record['candidate']['consumer_seed']);seed_original_digest=digest(seed);require(seed_original_digest==read(S/'S4_STATIC.json')['seed_digest'],'D60_SEED_FREEZE');source_files[str(cp)]=sha(cp)
    for k in ('internal_states_at_D60','accepted_position_history','accepted_receipts'):seed[k]={int(j):x for j,x in seed[k].items()}
    require(plain(seed['internal_states_at_D60'])==snaps[60]['states'] and plain(seed['accepted_position_history'])==snaps[60]['accepted_history'] and plain(seed['accepted_receipts'])==snaps[60]['accepted_receipts'],'D60_COMPLETE_SEED_SNAPSHOT')
    require(pending_core(seed['pending_observations'])==pending_core(snaps[60]['pending']),'D60_INITIAL_PENDING')
    require(pending_core(terminal['pending'])==pending_core(pending120),'TERMINAL_PENDING_SOURCES')
    # ENDPOINT_CONNECTION_DETAILS decorates existing connection records. Strip ONLY these four display/audit keys.
    decoration={'G','Q','endpoint_id','event_order'};connections=[{k:v for k,v in e.items() if k not in decoration} for e in details['endpoints'] if 'feedback_event_ordinal' in e]
    require(len(connections)==len(raw['feedback']) and [e['feedback_event_ordinal'] for e in connections]==list(range(len(raw['feedback']))),'COMMITTED_EVENT_DIRECTORY')
    for t,transaction in tx.items():
        for c in transaction['connections']:require(c in connections,'TRANSACTION_CONNECTION_PROJECTION')
    proof=source_order_evidence(HISTORY/'historical',ctx['pins']);catalog=event_catalog(raw,tx,{t:snaps[t] for t in (80,100)},connections,order_evidence=proof,initial_pending=seed['pending_observations'],terminal_pending=pending120)
    require(raw['endpoint_fusions']==details['connections']['endpoint_count']-sum(e['endpoint_side']=='INHERITED_ACTUAL_LEFT' for e in details['endpoints']),'ENDPOINT_GENERATION_COUNT')
    for e in catalog['events']:
        require(e['observation_origin']=='MODEL' and e['provenance']=='SIMULATED','FEEDBACK_ORIGIN')
    f=dict(seed=seed,events=catalog['events'],snaps=snaps,terminal=terminal,pending120=pending120,raw=raw,identity=digest(dict(seed=plain(seed),events=catalog['events'])),sources=source_files,order_proof=proof)
    w.json('FEEDBACK/'+name+'_IDENTITY.json',dict(status='VERIFIED_DIRECTORY_AND_SEED',seed_digest=seed_original_digest,feedback_digest=f['identity'],events=catalog['events'],sources=source_files,order_proof=proof,initial_pending=len(seed['pending_observations']),historical_consumed=len(seed['consumed_records']),pre_d60='SOURCE_UNRESOLVED',projection='remove G,Q,endpoint_id,event_order; verify equality against original transaction connections',terminal_pending_count=len(pending120),mathematical_replay='verified during each actual P3/P4 cell; not precomputed'))
    return f

def eligible(e,t):return e['frame_tick']<t or (e['frame_tick']==t and e['phase']=='MODEL_INTERVAL_RIGHT')
def enqueue_until(consumer,events,t,terminal=False):
    for e in events:
        if e['identity'] not in consumer.enqueued and (terminal or eligible(e,t)):consumer.enqueue(e)

def run_cell(ctx,version,name):
    w,clock=ctx['w'],ctx['clock'];clock.check();cell=ctx['cells'][name];view=ctx['make_view']();actions=copy.deepcopy(cell['actions']);world=copy.deepcopy(cell['world']);no_cap=version in ('P2','P4');feedback=version in ('P3','P4');f=ctx['feedback'].get(name);consumer=Replay(copy.deepcopy(f['seed'])) if feedback else None
    trace=TraceRecorder();controls=[];boundaries=[];batches=[];initial_belief=typed(view['beliefs']);initial_actions=typed(actions);cmd=controller(ctx['ns'],no_cap,controls,actions=actions)
    def command(*args):clock.check();return cmd(*args)
    def boundary(t,v,physical):
        clock.check();p_before=copy.deepcopy(physical);before_beliefs=copy.deepcopy(v['beliefs']);invoked=[];audit_start=0 if consumer is None else len(consumer.audit_rows)
        def pause_resume():invoked.append(t)
        def update():
            enqueue_until(consumer,f['events'],t);frozen=consumer.freeze(t);verify_replay_snapshot(consumer,f['snaps'][t]);return frozen
        check=boundary_check(t,v,physical,consumer=consumer,operation=pause_resume,feedback_operation=update if feedback else None);require(invoked==[t],'BOUNDARY_OPERATION_NOT_EXECUTED');require(typed(p_before)==typed(physical),'FEEDBACK_PHYSICAL_CHANGE');require(typed(actions)==initial_actions,'FEEDBACK_ACTION_OR_COST_CHANGE')
        check.update(before_physical=plain(p_before),after_physical=plain(physical),before_beliefs=plain(before_beliefs),after_beliefs=plain(v['beliefs']),consumer_verification='NOT_APPLICABLE' if consumer is None else 'VERIFIED_ARCHIVED_STATES_HISTORY_RECEIPTS_PENDING_AND_EVENT_ORDER');boundaries.append(check)
        if feedback:
            rows=copy.deepcopy(consumer.audit_rows[audit_start:]);before_prediction={j:prediction(b,t,no_cap) for j,b in before_beliefs.items()};after_prediction={j:prediction(b,t,no_cap) for j,b in v['beliefs'].items()};accepted=any(r['accepted'] for r in rows)
            chain=feedback_chain(accepted,before_beliefs,v['beliefs'],before_prediction,after_prediction)
            if not rows:chain['feedback_status']='NOT_APPLICABLE'
            batches.append(dict(freeze_id=t,event_count=len(rows),accepted_count=sum(r['accepted'] for r in rows),rejected_count=sum(not r['accepted'] for r in rows),events=rows,before_prediction=plain(before_prediction),after_prediction=plain(after_prediction),same_time=t,same_propagation_rule='NoCap' if no_cap else 'Cap',chain=chain,attribution_unit='freeze batch; no event-level counterfactual allocation'))
    def record(s):clock.check();trace(s)
    require(sum(ctx['calls'].values())<18,'CELL_COUNT_LIMIT');ctx['calls'][version]+=1;w.json('CALLS/'+version+'_'+name+'_STARTED.json',dict(version=version,cell=name,state='STARTED',call_ordinal=sum(ctx['calls'].values()),input_digest=fingerprint([view,actions,world]),feedback_digest=None if f is None else f['identity']))
    output=None
    try:
        output=ctx['kernel'](view,actions,world,command,boundary,record);w.json('RAW/'+version+'_'+name+'.json',plain(output));ledger_check(output['ledger'],output['value']);require(len(trace.rows)==60 and trace.rows[-1]['tick']==120 and [b['tick'] for b in boundaries]==[80,100],'HORIZON_BOUNDARY')
        if not feedback:require(typed(view['beliefs'])==initial_belief,'P2_BELIEF_CHANGED')
        if feedback:
            enqueue_until(consumer,f['events'],120,terminal=True);terminal=consumer.terminal(120)
            require(plain(consumer.states)==f['terminal']['consumer_states'],'TERMINAL_CONSUMER_STATE');require(plain(consumer.history)==f['terminal']['accepted_position_history'],'TERMINAL_ACCEPTED_HISTORY');require(plain(consumer.accepted_receipts)==f['terminal']['accepted_receipts'],'TERMINAL_ACCEPTED_RECEIPTS');require(plain(consumer.consumed)==f['terminal']['consumed'],'TERMINAL_CONSUMED_ORDER');require(pending_core(consumer.pending)==pending_core(f['pending120']),'TERMINAL_PENDING_ORDER');require(len(consumer.enqueued)==len(f['events'])+len(f['seed']['pending_observations']),'EVENT_DIRECTORY_ENQUEUE_COMPLETENESS')
            w.json('FEEDBACK/'+version+'_'+name+'_REPLAY.json',plain(dict(status='VERIFIED',feedback_digest=f['identity'],audit_rows=consumer.audit_rows,terminal=terminal,pending_identity_order=[r['identity'] for r in consumer.pending],batches=batches,source_scope='MODEL/SIMULATED, internal ACTUAL_WLS labels retained',D120_freeze=False)))
        if version=='P2' and name.endswith('_SWITCH'):
            baseline=ctx['traces']['P1/'+name];relevant=[r for r in controls if r['source']=='PUBLIC_PRIOR' and r['target']==1];require(relevant,'PUBLIC_PRIOR_NEGATIVE_CONTROL_MISSING');require(all(not r['prediction_changed'] and not r['cap_applicable'] for r in relevant),'PUBLIC_PRIOR_PROPAGATION_CHANGED')
            ctx['scientific_checks'][name+'_PUBLIC_PRIOR']=dict(status='VERIFIED',records=len(relevant),core_outputs_equal=plain(output)==ctx['results']['P1'][name],whole_control_sequence_equal=plain([r['control'] for r in controls])==[r['control'] for r in baseline['controls']],interpretation='formula invariant required; whole-cell equality separately observed')
        require(typed(actions)==initial_actions,'D60_ACTION_CHANGED');pending_trace=plain(dict(frames=trace.rows,controls=controls,boundaries=boundaries,batches=batches,Q_semantics='G-only optimistic UNKNOWN Q; reset observation_invalid is not WLS failure'))
        if feedback:
            if version=='P4':
                previous=read(HERE/'FEEDBACK'/('P3_'+name+'_REPLAY.json'));require(previous['feedback_digest']==f['identity'],'P3_P4_INFORMATION_STREAM_CHANGED');require(plain(previous['audit_rows'])==plain(consumer.audit_rows),'P3_P4_CONSUMER_UPDATE_DIFFERENCE')
        if feedback:ctx['feedback_status'].setdefault(name,{})[version]='VERIFIED'
        ctx['results'][version][name]=plain(output);ctx['traces'][version+'/'+name]=pending_trace
        return output
    finally:w.json('TRACE/'+version+'_'+name+'.json',plain(dict(frames=trace.rows,controls=controls,boundaries=boundaries,batches=batches,Q_semantics='G-only optimistic Q; no synthetic observation generation',controller_prediction_changed='NoCap effect only')))


def analyze(ctx):
    w=ctx['w'];clock=ctx['clock'];results=ctx['results'];hf=ctx['hf'];rows=[];pair_metrics={};trajectory={};batch_chains={};economics={}
    for v in VERSIONS:
        for name,out in results[v].items():
            base=results['P1'][name];e=out['value']-hf[name];rows.append(dict(version=v,world=name[:2],action=name[3:],cell=name,value=out['value'],hf=hf[name],signed_error=e,AE=abs(e),Delta_AE=abs(e)-abs(base['value']-hf[name]),ledger=out['ledger'],tasks=out['tasks']))
    versions={}
    for v in VERSIONS:
        r=[x for x in rows if x['version']==v];versions[v]=dict(valid_cells=[x['cell'] for x in r],denominator=len(r),MAE=None if not r else sum(x['AE'] for x in r)/len(r),signed_bias=None if not r else sum(x['signed_error'] for x in r)/len(r),action_signed_bias={a:dict(denominator=sum(x['action']==a for x in r),value=None if not any(x['action']==a for x in r) else sum(x['signed_error'] for x in r if x['action']==a)/sum(x['action']==a for x in r)) for a in ACTIONS})
    for p,b in [('P2','P1'),('P3','P1'),('P4','P3'),('P4','P2')]:
        common=sorted(set(results[p])&set(results[b]));pa=[abs(results[p][n]['value']-hf[n]) for n in common];ba=[abs(results[b][n]['value']-hf[n]) for n in common]
        pair_metrics[p+'/'+b]=dict(status='NOT_IDENTIFIABLE' if not common else 'VALID_PAIRED_COMPARISON',common_cells=common,denominator=len(common),baseline_MAE=None if not common else sum(ba)/len(common),treatment_MAE=None if not common else sum(pa)/len(common),paired_Delta_MAE=None if not common else sum(a-z for a,z in zip(pa,ba))/len(common))
        for name in common:
            clock.check();cur=ctx['traces'][p+'/'+name];old=ctx['traces'][b+'/'+name];world=ctx['cells'][name]['world']
            def truth(j,t):return None if t<60 else (ctx['proxy'].point(world,j,t),world['motion'][j]['velocity'])
            tm=trajectory_metrics(cur['frames'],cur['controls'],truth,old['controls'],comparison_pair=p+'/'+b,control_atol=0.)
            tm['first_robot_position_change']=next((x['tick'] for x,y in zip(cur['frames'],old['frames']) if x['positions']!=y['positions']),None)
            tm['rule_applicable_control_records']=sum(r['cap_applicable'] for r in cur['controls']);tm['NoCap_prediction_changed_control_records']=sum(r['prediction_changed'] for r in cur['controls']);tm['controller_prediction_changed_scope']='mechanism A only, same belief/time'
            tm['mechanism_chain']=dict(rule_triggered=bool(tm['rule_applicable_control_records']),prediction_difference_from_comparator=any(x['position_prediction']!=y['position_prediction'] or x['velocity_prediction']!=y['velocity_prediction'] for x,y in zip(cur['controls'],old['controls'])),control_changed=tm['first_control_divergence'] is not None,robot_trajectory_changed=tm['first_robot_position_change'] is not None,service_changed=cur['frames'][-1]['tasks']!=old['frames'][-1]['tasks'],value_changed=results[p][name]['value']!=results[b][name]['value'],interpretation='separate descriptive levels; positive value or accuracy effect not assumed')
            trajectory[p+'/'+b+'/'+name]=tm;w.json('ANALYSIS/'+p+'_'+b+'_'+name+'_TRAJECTORY.json',tm)
            if (p,b) in [('P3','P1'),('P4','P2')]:
                groups=[]
                for batch in cur.get('batches',[]):
                    t=batch['freeze_id'];end=100 if t==80 else 120;current_frames=[f for f in cur['frames'] if t<f['tick']<=end];old_frames=[f for f in old['frames'] if t<f['tick']<=end]
                    control_changed=[f['controls'] for f in current_frames]!=[f['controls'] for f in old_frames];service_changed=[dict(states=f['states'],tasks=f['tasks'],statuses=f['statuses']) for f in current_frames]!=[dict(states=f['states'],tasks=f['tasks'],statuses=f['statuses']) for f in old_frames]
                    chain=copy.deepcopy(batch['chain']);chain['control_changed']='CHANGED' if control_changed else 'UNCHANGED';chain['service_outcome_changed']='CHANGED' if service_changed else 'UNCHANGED';groups.append(dict(freeze_id=t,event_count=batch['event_count'],accepted_count=batch['accepted_count'],rejected_count=batch['rejected_count'],chain=chain,control_and_service_comparator=p+'/'+b,interval=[t,end],prediction_comparator='same tick, target, propagation rule before/after current freeze',attribution='batch-level descriptive; control/service include prior feedback and trajectory consequences, not event-level causal proof'))
                batch_chains[p+'/'+b+'/'+name]=groups
    ranks={};effects=[]
    for v in VERSIONS:
        ranks[v]={}
        for world in ('H2','H3'):
            names=[world+'_'+a for a in ACTIONS]
            if not all(n in results[v] for n in names):ranks[v][world]=dict(status='NOT_IDENTIFIABLE',missing=[n for n in names if n not in results[v]]);continue
            values={n[3:]:results[v][n]['value'] for n in names};best=max(values.values());opt=[a for a in ACTIONS if best-values[a]<=1e-8];truthbest=max(hf[n] for n in names)
            ranks[v][world]=dict(status='VALID',values=values,keep_minus_switch=values['KEEP']-values['SWITCH'],strict_order=sorted(ACTIONS,key=lambda a:-values[a]),exact_best=[a for a in ACTIONS if values[a]==best],epsilon_best=opt,HF_regret={a:truthbest-hf[world+'_'+a] for a in opt})
    for name in ctx['cells']:
        values={v:results[v].get(name,{}).get('value') for v in VERSIONS};delta=lambda a,b:None if values[a] is None or values[b] is None else values[a]-values[b]
        a0,a1,b0,b1=delta('P2','P1'),delta('P4','P3'),delta('P3','P1'),delta('P4','P2');full=all(x is not None for x in values.values());effects.append(dict(world=name[:2],action=name[3:],A0=a0,A1=a1,B0=b0,B1=b1,ME_A=(a0+a1)/2 if full else None,ME_B=(b0+b1)/2 if full else None,Interaction=values['P4']-values['P3']-values['P2']+values['P1'] if full else None,status='VALID' if full else 'NOT_IDENTIFIABLE'))
        for v in VERSIONS:
            if name not in results[v]:continue
            out=results[v][name];baseline=ctx['baseline'][name];raw=ctx['feedback'].get(name,{}).get('raw');raw=raw if raw is not None else dict(components=baseline['HF_components'],change_cost=baseline['HF_change_cost'],net=baseline['HF'])
            try:economics[v+'/'+name]=economic_reconciliation(out['ledger'],out['value'],raw)
            except Exception as exc:economics[v+'/'+name]=dict(status='NOT_VERIFIED',reason=str(exc),proxy=out['ledger'],hf_raw_reference=str(S/name/'BRANCH_RAW.json'))
    full_metrics=None
    if len(rows)==24:full_metrics=value_metrics([dict(version=x['version'],world=x['world'],action=x['action'],value=x['value'],hf=x['hf']) for x in rows])
    analysis=dict(matrix_status='COMPLETE_24_CELLS' if len(rows)==24 else 'PARTIAL',cells=rows,versions=versions,paired_MAE=pair_metrics,rankings=ranks,effects=effects,frozen_value_metrics=full_metrics,feedback_batch_attribution=batch_chains,economics=economics,negative_controls=ctx['scientific_checks'])
    w.json('SCIENTIFIC_ANALYSIS.json',analysis)
    w.json('VALUE_MATRIX.json',{name:dict(HF=hf[name],**{v:results[v].get(name,{}).get('value') for v in VERSIONS}) for name in ctx['cells']});w.json('FEEDBACK_BATCH_ATTRIBUTION.json',batch_chains)
    return analysis,trajectory

def svg_line_panel(parts,title,series,x,y,width,height):
    allpts=[p for name,points in series for p in points if p[1] is not None and math.isfinite(p[1])]
    parts.append('<text x="%s" y="%s" font-size="14">%s</text>'%(x,y-9,html.escape(title)))
    if not allpts:return
    xmin=min(p[0] for p in allpts);xmax=max(p[0] for p in allpts);ymin=min(0,min(p[1] for p in allpts));ymax=max(p[1] for p in allpts);span=max(ymax-ymin,1e-9);ymax+=.08*span;span=ymax-ymin
    parts.append('<path d="M %s %s V %s H %s" fill="none" stroke="#777"/>'%(x,y,y+height,x+width))
    colors={'P1':'#2563eb','P2':'#ea580c','P3':'#16a34a','P4':'#9333ea','HF':'#111827'}
    for name,points in series:
        coords=' '.join('%.3f,%.3f'%(x+(t-xmin)/max(1,xmax-xmin)*width,y+height-(v-ymin)/span*height) for t,v in points if v is not None and math.isfinite(v))
        parts.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.8"/>'%(coords,colors[name]))
    parts.append('<text x="%s" y="%s" font-size="10">%.4g</text><text x="%s" y="%s" font-size="10">%.4g</text><text x="%s" y="%s" font-size="10">tick %s - %s</text>'%(x-35,y+10,ymax,x-35,y+height,ymin,x,y+height+15,xmin,xmax))
def make_figures(ctx,analysis):
    w=ctx['w'];colors={'P1':'#2563eb','P2':'#ea580c','P3':'#16a34a','P4':'#9333ea','HF':'#111827'}
    def begin(width,height,title):return ['<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" viewBox="0 0 %s %s"><rect width="100%%" height="100%%" fill="white"/><g font-family="Arial,Microsoft YaHei,sans-serif">'%(width,height,width,height),'<text x="25" y="27" font-size="20">'+html.escape(title)+'</text>','<text x="25" y="49" font-size="12">HF black | P1 blue | P2 orange | P3 green | P4 purple; fixed archived worlds</text>']
    parts=begin(1100,650,'Action values: archived HF and P1-P4')
    for idx,name in enumerate(ctx['cells']):
        col=idx%3;row=idx//3;x=65+col*350;y=90+row*275;vals=[('HF',ctx['hf'][name])]+[(v,ctx['results'][v].get(name,{}).get('value')) for v in VERSIONS];points=[(i,v) for i,(label,v) in enumerate(vals) if v is not None];parts.append('<text x="%s" y="%s" font-size="14">%s</text>'%(x,y-12,html.escape(name)));parts.append('<path d="M %s %s V %s H %s" fill="none" stroke="#777"/>'%(x-5,y,x-5 if False else y+190,x+270))
        lo=min(0,min(v for i,v in points));hi=max(0,max(v for i,v in points));span=max(hi-lo,1e-9)*1.08
        for i,(label,v) in enumerate(vals):
            parts.append('<text x="%s" y="%s" font-size="11">%s</text>'%(x+i*54,y+212,label))
            if v is None:continue
            yy=y+190-(v-lo)/span*190;zero=y+190-(0-lo)/span*190;parts.append('<rect x="%s" y="%.3f" width="27" height="%.3f" fill="%s"/><text x="%s" y="%s" font-size="9">%.5f</text>'%(x+i*54,min(yy,zero),max(1,abs(zero-yy)),colors[label],x+i*54,y+231,v))
    w.write('FIGURES/action_values.svg',''.join(parts)+ '</g></svg>')
    parts=begin(1100,1050,'Prediction errors and proxy service progress')
    for idx,(world,action) in enumerate(itertools.product(('H2','H3'),('KEEP','SWITCH'))):
        name=world+'_'+action;target=0 if action=='KEEP' else 1;error_series=[];progress_series=[]
        for v in VERSIONS:
            tr=ctx['traces'].get(v+'/'+name)
            if tr is None:continue
            points={}
            for r in tr['controls']:
                if r['target']==target:points[r['tick']]=math.dist(r['position_prediction'],ctx['proxy'].point(ctx['cells'][name]['world'],target,r['tick']))
            error_series.append((v,sorted(points.items())));progress=[]
            for f in tr['frames']:
                s=f['states'][str(target)];progress.append((f['tick'],math.fsum((s['base'],s['intervals']*.05))))
            progress_series.append((v,progress))
        svg_line_panel(parts,name+' position prediction error',error_series,75,90+idx*235,410,170);svg_line_panel(parts,name+' service progress (seconds)',progress_series,625,90+idx*235,410,170)
    w.write('FIGURES/state_service_curves.svg',''.join(parts)+'</g></svg>')
    parts=begin(1100,570,'MAE and decision regret: prediction and decision are distinct')
    for i,v in enumerate(VERSIONS):
        val=analysis['versions'][v]['MAE'];parts.append('<text x="35" y="%s" font-size="14">%s MAE %s (n=%s)</text>'%(90+i*33,v,'N/A' if val is None else format(val,'.8f'),analysis['versions'][v]['denominator']))
        for j,world in enumerate(('H2','H3')):
            r=analysis['rankings'][v][world];s='N/A' if r['status']!='VALID' else 'best='+','.join(r['epsilon_best'])+' regret='+','.join(a+':'+format(g,'.8f') for a,g in r['HF_regret'].items());parts.append('<text x="%s" y="%s" font-size="12">%s %s %s</text>'%(380+j*345,90+i*33,v,world,html.escape(s)))
    for i,(pair,row) in enumerate(analysis['paired_MAE'].items()):parts.append('<text x="35" y="%s" font-size="14">%s paired Delta MAE=%s; n=%s</text>'%(290+i*40,pair,row['paired_Delta_MAE'],row['denominator']))
    w.write('FIGURES/error_decision_summary.svg',''.join(parts)+'</g></svg>')


def worker():
    prep=read(HERE/'PREPARATION_ACCOUNTING.json');origin=float(sys.argv[-1]);clock=Clock(origin,cpu_limit=120,wall_limit=1800);w=Writer(HERE,limit=134217728,initial_written=prep['cumulative_logical_write_bytes'],clock=clock);ctx=None;top_failure=None;analysis=None;trajectory=None;plot_status='NOT_EXECUTED'
    try:
        ctx=bootstrap(w,clock)
        # Scientific order: all P2 first; then feedback identity checks, then P3, then P4.
        for name in ctx['cells']:
            try:run_cell(ctx,'P2',name)
            except BaseException as exc:
                fault=error(exc,'P2/'+name);ctx['failures'].append(fault);ctx['shared_fault']=fault;w.json('FAILURES/P2_'+name+'.json',fault);break
        w.json('P2_RESULTS.json',ctx['results']['P2']);w.json('P2_NEGATIVE_CONTROLS.json',ctx['scientific_checks'])
        if ctx['shared_fault'] is None:
            for name in ctx['cells']:
                try:ctx['feedback'][name]=prepare_feedback(ctx,name);ctx['feedback_status'][name]=dict(identity='VERIFIED_CATALOG_AND_SEED')
                except Exception as exc:
                    fault=error(exc,'FEEDBACK_IDENTITY/'+name);ctx['feedback_status'][name]=dict(identity='NOT_IDENTIFIABLE_OR_NOT_VERIFIED',reason=fault);w.json('FAILURES/FEEDBACK_'+name+'.json',fault)
            for version in ('P3','P4'):
                if ctx['shared_fault'] is not None:break
                for name in ctx['cells']:
                    if name not in ctx['feedback']:continue
                    if version=='P4' and name not in ctx['results']['P3']:continue
                    try:run_cell(ctx,version,name)
                    except BaseException as exc:
                        fault=error(exc,version+'/'+name);ctx['failures'].append(fault);ctx['shared_fault']=fault;w.json('FAILURES/'+version+'_'+name+'.json',fault);break
                w.json(version+'_RESULTS.json',ctx['results'][version])
        for version in ('P3','P4'):
            if not (HERE/(version+'_RESULTS.json')).exists():w.json(version+'_RESULTS.json',ctx['results'][version])
        w.json('FEEDBACK_VALIDATION.json',ctx['feedback_status']);w.json('ALL_RESULTS.json',ctx['results']);clock.check()
        analysis,trajectory=analyze(ctx)
        try:make_figures(ctx,analysis);plot_status='GENERATED_FROM_EXISTING_RESULTS'
        except Exception as exc:plot_status=dict(status='NOT_COMPLETED',failure=error(exc,'FIGURES'));w.json('FIGURES_LIMITATION.json',plot_status)
    except BaseException as exc:
        top_failure=error(exc,'TASK');w.json('TASK_FAILURE.json',top_failure)
    clock.check();valid={v:0 if ctx is None else len(ctx['results'][v]) for v in VERSIONS};calls={'P2':0,'P3':0,'P4':0} if ctx is None else ctx['calls'];entry_sha=sha(__file__)
    protection={} if ctx is None else {p:sha(p)==h for p,h in ctx['protected'].items()};w.json('PROTECTION_CHECK.json',dict(files=protection,unchanged=bool(protection) and all(protection.values()),scope='frozen inputs, accepted P1 and kernel, owner policies.py; no production writes'))
    actual={} if ctx is None else ctx['guard'].audit();w.json('RUNTIME_IMPORTS.json',dict(actual_modules=actual,namespace_paths={} if ctx is None else ctx['guard'].namespace_paths,untriggered_lazy_imports='NOT_VERIFIED',historical_identity_reference=str(HISTORY/'HISTORICAL_IDENTITY.json')))
    all24=valid=={'P1':6,'P2':6,'P3':6,'P4':6};scientific_validity='VALID_COMPLETE_24_CELL_DIAGNOSTIC_MATRIX' if all24 and top_failure is None and ctx['shared_fault'] is None and analysis is not None else 'PARTIAL_VALID_RESULTS' if valid['P2']+valid['P3']+valid['P4'] else 'NO_NEW_VALID_CELLS'
    input_sha=digest([] if ctx is None else [c['binding'] for c in ctx['cells'].values()]);statuses=dict(historical_identity='VERIFIED' if actual else 'NOT_VERIFIED',import_closure='NOT_VERIFIED',p1_reproduction='VERIFIED' if ctx is not None else 'NOT_VERIFIED',boundary_continuity='VERIFIED' if all24 else 'NOT_VERIFIED',feedback_integrity='VERIFIED' if valid['P3']==valid['P4']==6 else 'NOT_IDENTIFIABLE',treatment_definition='VERIFIED' if all24 else 'NOT_VERIFIED',metrics_complete='VERIFIED' if all24 and analysis is not None else 'NOT_VERIFIED',history_protected='VERIFIED' if protection and all(protection.values()) else 'NOT_VERIFIED',resource_accounting='INCOMPLETE',evidence_sealed='NOT_VERIFIED')
    w.json('V05_GATE_EVIDENCE.json',dict(code_sha256=entry_sha,checks={k:dict(status=statuses[k],check_id=k,input_sha256=input_sha,evidence_scope='actual current results and accepted P1; resource and full dependency closure not promoted to VERIFIED') for k in REQUIRED_GATES}))
    records={k:dict(path='V05_GATE_EVIDENCE.json',sha256=sha(HERE/'V05_GATE_EVIDENCE.json')) for k in REQUIRED_GATES};formal=final_status(records,HERE,entry_sha,feedback_identifiable=valid['P3']==valid['P4']==6);w.json('V05_FINAL_STATUS.json',formal)
    report=dict(task='STFBS_LITE_L3_B_P2_P4_MECHANISM_DIAGNOSTICS_001',git_head=HEAD,entry_sha256=entry_sha,kernel_sha256=sha(STAGE/'recovery.py'),scientific_diagnostic_validity=scientific_validity,valid_cells=valid,started_calls=calls,total_new_calls=sum(calls.values()),P1_reexecutions=0,REF_reexecutions=0,new_WLS=0,new_Assignment=0,new_R=0,new_HF=0,new_worlds=0,new_random_seeds=0,scientific_attempts=0,feedback_validation={} if ctx is None else ctx['feedback_status'],shared_fault=None if ctx is None else ctx['shared_fault'],top_failure=top_failure,V05_formal_acceptance=formal,resource_accounting='INCOMPLETE',resource_compliance='NOT_ESTABLISHED',exploratory_incomplete_accounting='OWNER_ACCEPTED',plots=plot_status,MAE=None if analysis is None else {v:r['MAE'] for v,r in analysis['versions'].items()},paired_MAE=None if analysis is None else analysis['paired_MAE'],rankings=None if analysis is None else analysis['rankings'],independent_acceptance='PENDING',PRODUCTION_ADMISSION='BLOCKED',L3_C='NOT_STARTED',limitations=['fixed historical MODEL information stream, not sensor observability on each proxy trajectory','pre-D60 source unresolved, conditional on complete D60 seed','deterministic worlds are not independent random samples','HF labels from accepted archives; no new HF or full HF event re-audit','untriggered lazy imports NOT_VERIFIED','resource accounting incomplete; no blanket V0.5 PASS claimed'])
    w.json('FINAL_REPORT.json',report)
    lines=['# P2—P4 联合机制诊断结果','',scientific_validity,'','| 世界 | 动作 | HF | P1 | P2 | P3 | P4 |','|---|---|---|---|---|---|---|']
    if ctx is not None:
        for name in ctx['cells']:lines.append('| '+' | '.join([name[:2],name[3:],repr(ctx['hf'][name])]+[str(ctx['results'][v].get(name,{}).get('value','NOT_IDENTIFIABLE')) for v in VERSIONS])+' |')
    if analysis is not None:
        lines+=['','| 版本 | MAE（有效分母） | H2最优动作 | H3最优动作 | H2 HF regret | H3 HF regret |','|---|---|---|---|---|---|']
        for v in VERSIONS:
            r=analysis['rankings'][v];lines.append('| '+' | '.join([v,str(analysis['versions'][v]['MAE'])+' (n='+str(analysis['versions'][v]['denominator'])+')',str(r['H2'].get('epsilon_best','NOT_IDENTIFIABLE')),str(r['H3'].get('epsilon_best','NOT_IDENTIFIABLE')),str(r['H2'].get('HF_regret','NOT_IDENTIFIABLE')),str(r['H3'].get('HF_regret','NOT_IDENTIFIABLE'))])+' |')
        lines+=['','| 世界 | 动作 | 传播效应A0 | 反馈效应B0 | 交互效应 |','|---|---|---|---|---|']
        for e in analysis['effects']:lines.append('| '+' | '.join(str(e[k]) for k in ['world','action','A0','B0','Interaction'])+' |')
        lines+=['','## 配对误差与决策质量','']
        for pair,r in analysis['paired_MAE'].items():lines.append('- '+pair+'：共同有效单元 '+str(r['common_cells'])+'；n='+str(r['denominator'])+'；基准MAE='+str(r['baseline_MAE'])+'；处理MAE='+str(r['treatment_MAE'])+'；配对Delta_MAE='+str(r['paired_Delta_MAE'])+'。')
        lines+=['','## 机制证据及解释边界','']
        for world in ('H2','H3'):
            for action in ('KEEP','SWITCH','MEMBER_CHANGE'):
                name=world+'_'+action;parts=[]
                for v in VERSIONS:
                    out=ctx['results'][v].get(name)
                    if out is None:continue
                    j='1' if action=='SWITCH' else '0';task=out['tasks'][j];parts.append(v+': completion_tick='+str(task['completion_tick'])+', Pmax='+str(task['Pmax'])+', NG='+str(task['NG'])+', stop_time='+str(task['stop_time']))
                lines.append('- '+name+'：'+'；'.join(parts)+'。')
        lines+=['','所有NoCap prediction_changed仅用于机制A。反馈预测变化由同一freeze时刻、同一目标、相同传播规则下的前后belief计算；控制及服务归因来自实际配对轨迹，以批次描述，不向单个事件分摊因果效果。无合格五tick历史参考时保留更新前速度及来源，不强制回退D60先验。','', 'P2负对照直接检查PUBLIC_PRIOR传播不变，整体单元是否完全相同另行如实记录；不能仅以整体差异判实现失败。','', '代理价值升高、相对HF误差减小、动作选择正确是三个不同结果。应联合阅读MAE、KEEP−SWITCH、完整排序与HF regret；不只选择有利指标。','', 'P3/P4固定历史观测流不随代理运动重新生成或筛选，结果不证明其在自身轨迹上能够获得同样的信息，不可直接部署为生产自主感知预测算法。','', 'RAW保存原始输出；TRACE保存控制、G、代理Q、服务时钟和reset、D80/D100前后快照以及D120状态；FEEDBACK保存种子/事件身份、消费回执、pending与反馈批次；ANALYSIS保存规定比较对的逐拍误差和分层机制。代理stop_time不等于HF真实释放事务，未创造新的Assignment或收费。']
    lines+=['','## 正式门槛与资源','', 'V0.5最终状态：'+formal['status']+'。实际科学诊断有效性单列为'+scientific_validity+'。资源会计仍为INCOMPLETE，资源合规NOT_ESTABLISHED；完整依赖闭包与退出后的最终封存不伪装VERIFIED。正式门槛文件见V05_FINAL_STATUS.json。','', '历史Stage A墙钟334.8579769秒超时和历史CPU/累计写入未知保持原状。当前窗口为新批准的120 CPU秒、1800连续墙钟秒、134217728逻辑写入字节；最终资源数据见RESOURCE_RECEIPT.json。','', '只使用现有18个以内新增诊断单元，没有重跑P1/REF、WLS、Assignment、R或HF，没有修改生产源码。完成后停止，不启动L3-C。']
    w.write('REPORT.md','\n'.join(lines));clock.check()
    inventory={p.relative_to(HERE).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in HERE.rglob('*') if p.is_file()};w.json('FILE_SHA256.json',dict(files=inventory,excluded=['FILE_SHA256.json self','WORKER_ACCOUNTING.json','RESOURCE_RECEIPT.json']))
    w.accounting_receipt('WORKER_ACCOUNTING.json',dict(worker_pid=os.getpid(),cpu_snapshot=time.process_time(),wall_snapshot=time.monotonic()-origin,logical_writes_scope='controlled task writes incl preparation, deletions do not refund',operations=w.operations,resource_accounting='INCOMPLETE',scientific_validity=scientific_validity))
    print(json.dumps(dict(scientific_validity=scientific_validity,valid_cells=valid,calls=calls,formal_status=formal['status'],MAE=report['MAE'],shared_failure=None if ctx is None or ctx['shared_fault'] is None else ctx['shared_fault']['message'],top_failure=None if top_failure is None else top_failure['message']),ensure_ascii=False),flush=True);return 0 if all24 and top_failure is None else 1

def process_times(handle):
    from ctypes import wintypes
    class FT(ctypes.Structure):_fields_=[('low',wintypes.DWORD),('high',wintypes.DWORD)]
    a,b,c,d=FT(),FT(),FT(),FT();f=ctypes.windll.kernel32.GetProcessTimes;f.argtypes=[wintypes.HANDLE]+[ctypes.POINTER(FT)]*4;f.restype=wintypes.BOOL;require(f(int(handle),ctypes.byref(a),ctypes.byref(b),ctypes.byref(c),ctypes.byref(d)),'GET_PROCESS_TIMES');v=lambda x:(x.high<<32)|x.low
    return dict(creation_filetime=v(a),exit_filetime=v(b),kernel_seconds=v(c)/1e7,user_seconds=v(d)/1e7)
def meter():
    prep=read(HERE/'PREPARATION_ACCOUNTING.json');origin=time.monotonic()-(prep['elapsed_at_launch']+max(0.,time.time()-prep['bridge_utc_epoch']));deadline=origin+1800;p=subprocess.Popen([sys.executable,'-I','-S','-B',str(Path(__file__).resolve()),'--worker',str(origin)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);limit=None
    while p.poll() is None:
        t=process_times(p._handle)
        if time.monotonic()>=deadline or t['kernel_seconds']+t['user_seconds']+time.process_time()>=120:limit='RESOURCE_LIMIT';p.kill();break
        time.sleep(.05)
    out,err=p.communicate();end=time.monotonic();final=process_times(p._handle);entry_cpu=time.process_time();wf=HERE/'WORKER_ACCOUNTING.json';prior=read(wf)['cumulative_logical_write_bytes'] if wf.exists() else prep['cumulative_logical_write_bytes'];writer=Writer(HERE,limit=134217728,initial_written=prior)
    receipt=writer.accounting_receipt('RESOURCE_RECEIPT.json',dict(worker_pid=p.pid,worker_exit_status=p.returncode,worker_final_cpu=final,entry_pid=os.getpid(),entry_cpu_at_worker_exit=entry_cpu,known_cpu_subtotal=entry_cpu+final['kernel_seconds']+final['user_seconds'],limits=dict(cpu=120,wall=1800,cumulative_logical_write_bytes=134217728),wall_start_utc=prep['wall_start_utc'],wall_seconds_at_worker_exit=end-origin,deadline_trigger=limit,path_b='APPROVED: worker exit cutoff; final receipt and handle closure only',resource_accounting='INCOMPLETE',resource_compliance='NOT_ESTABLISHED',unknown_cpu='host preparation and readonly tools; final entry tail INCOMPLETE',wall_limitation='initial readonly command before clock anchor not precisely captured; UTC bridge at startup then common monotonic deadline',write_limitation='controlled writes counted; host writes INCOMPLETE',entry_tail='INCOMPLETE; not zero',stdout=out.decode(errors='replace'),stderr=err.decode(errors='replace')));p._handle.Close();print(json.dumps(receipt,ensure_ascii=False),flush=True);return p.returncode
if __name__=='__main__':sys.exit(worker() if '--worker' in sys.argv else meter())
