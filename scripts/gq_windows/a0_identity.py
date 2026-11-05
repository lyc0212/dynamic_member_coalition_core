"""A0-Ia offline content identity checks; never grants execution provenance.

Public schema validation is reused as a format definition. Hash recipes below
are implemented separately, without calling seal/build_manifest/select.
"""
import hashlib
import json
from itertools import combinations, permutations
from .a0_evidence import EvidenceError, Reader, require

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,
        separators=(',',':'),allow_nan=False).encode('utf-8')).hexdigest()

def same(a,b,path):
    require(type(a) is type(b) and digest(a)==digest(b),path,'identity/reference mismatch')

def exact_tree(actual,expected,path):
    """Closed typed JSON equality with the first differing leaf pointer."""
    require(type(actual) is type(expected),path,'field type mismatch')
    if type(expected) is dict:
        for key in sorted(set(actual)-set(expected)):
            raise EvidenceError('INVALID_EVIDENCE',path+'/'+pointer(key),'unknown field')
        for key in expected:
            p=path+'/'+pointer(key)
            require(key in actual,p,'missing field')
            exact_tree(actual[key],expected[key],p)
    elif type(expected) is list:
        require(len(actual)==len(expected),path,'array length mismatch')
        for i,(a,b) in enumerate(zip(actual,expected)):exact_tree(a,b,path+'/'+str(i))
    else:
        # float.hex retains signed zero; integers and booleans never coerce.
        equal=actual.hex()==expected.hex() if type(expected) is float else actual==expected
        require(equal,path,'value mismatch')

def pointer(key):return str(key).replace('~','~0').replace('/','~1')

def prediction_receipt(req,row,spec,saved,path):
    from research.information_service_online.quality_audit import audit_fusion
    from research.information_service_online.acceptance import audit_prediction
    checks=[]
    for i,s in enumerate(row['sensing_results']):
        try:checks.append(audit_fusion(s))
        except AssertionError as e:
            label=e.args[0][0] if e.args and isinstance(e.args[0],tuple) else ''
            leaf='/result/quality/radius_proxy' if label=='independent radius' else ''
            raise EvidenceError('INVALID_EVIDENCE',path+f'/evidence/sensing_results/{i}'+leaf,'saved fusion audit rejected: '+str(e)) from e
    expected=guarded(lambda:dict(status='PASS',fusion_checks=checks,prediction=audit_prediction(req,row,spec)),path+'/recomputed')
    # Worker save() serializes Counter mappings to ordinary JSON objects.
    expected=json.loads(json.dumps(expected,ensure_ascii=False,allow_nan=False))
    exact_tree(saved,expected,path)
    return expected

def fields(value,names,path):
    require(type(value) is dict and set(value)==set(names.split()),path,'unknown or missing fields')

def sealed(value,field,path):
    require(type(value.get(field)) is str,path+'/'+field,'digest must be string')
    same(value[field],digest({k:v for k,v in value.items() if k!=field}),path+'/'+field)

def schema(value,definition,path):
    from research.information_service_online.public import validate_schema
    try:
        clean=validate_schema(value,definition)
        same(clean,value,path)
    except (ValueError,TypeError,KeyError) as error:
        raise EvidenceError('INVALID_EVIDENCE',path,str(error)) from error

def checkpoint(cp,path='/checkpoint'):
    schema(cp,'Checkpoint',path);sealed(cp,'checkpoint_id',path)
    for i,h in enumerate(cp['task_histories']):
        hp=f'{path}/task_histories/{i}';sealed(h,'history_digest',hp)
        for n,s in enumerate(h['segments']):
            sp=f'{hp}/segments/{n}';sealed(s,'segment_history_digest',sp)
            keys=('contract_id','target_id','segment_index','previous_segment_id','start_tick','team','opened_by')
            same(s['segment_id'],digest({k:s[k] for k in keys}),sp+'/segment_id')
            ep=s['latest_endpoint'];sealed(ep,'endpoint_digest',sp+'/latest_endpoint')
            for k,slot in enumerate(ep['slots']):
                matches=[v for v in cp['current_slots'] if v['slot_key']==slot['slot_key']]
                if matches:
                    same(slot,{name:matches[0][name] for name in ('slot_key','slot_digest','state')},f'{sp}/latest_endpoint/slots/{k}')
    for i,slot in enumerate(cp['current_slots']):
        if slot['state']!='UNQUERIED':sealed(slot,'slot_digest',f'{path}/current_slots/{i}')
    return cp

def binding(b,path='/binding'):
    schema(b,'PublicHistoryBinding',path);cp=checkpoint(b['public_checkpoint'],path+'/public_checkpoint')
    for name in ('checkpoint_id','previous_checkpoint_id'):same(b[name],cp[name],path+'/'+name)
    same(b['target_history_digests'],[dict(target_id=h['target_id'],history_digest=h['history_digest']) for h in cp['task_histories']],path+'/target_history_digests')
    return cp

def request(req,cp=None,path='/request'):
    schema(req,'EvaluationRequest',path);sealed(req,'evaluation_request_id',path)
    checkpoint(req['checkpoint'],path+'/checkpoint')
    if cp is not None:same(req['checkpoint'],cp,path+'/checkpoint')
    same(req['prediction_end_tick'],min(req['checkpoint']['episode_end_tick'],req['checkpoint']['tick']+60),path+'/prediction_end_tick')
    return digest({k:req[k] for k in ('forecast_contract_id','current_endpoint_contract_id','evaluation_request_id')})

def manifest(m,req,path='/manifest'):
    fields(m,'payload request_identity world_identity candidate_count candidates',path)
    world=request(req,path=path+'/payload');same(m['payload'],req,path+'/payload')
    same(m['request_identity'],req['evaluation_request_id'],path+'/request_identity');same(m['world_identity'],world,path+'/world_identity')
    expected=[]
    for t in req['checkpoint']['targets']:
        roles={2:('dual_neg45','dual_pos45'),3:('tri_0','tri_120','tri_240')}[t['required_robots']]
        for robots in combinations(range(req['checkpoint']['config']['robots']),t['required_robots']):
            for rr in permutations(roles):expected.append(dict(target=t['id'],robots=list(robots),roles=list(rr)))
    same(m['candidate_count'],len(expected),path+'/candidate_count')
    require(len(m['candidates'])==len(expected),path+'/candidates','incomplete catalogue')
    for i,(c,key) in enumerate(zip(m['candidates'],expected)):
        p=f'{path}/candidates/{i}';schema(c,'CandidateDescriptor',p)
        for name,value in [('index',i),('key',key),('resource_mask',sum(1<<r for r in key['robots'])),('evaluation_request_id',m['request_identity']),('world_id',world)]:same(c[name],value,p+'/'+name)
        same(c['candidate_id'],digest(dict(evaluation_request_id=m['request_identity'],world_id=world,key=key)),p+'/candidate_id')
    return m

def candidate(row,c,req,path='/candidate'):
    fields(row,'kind execution_contract_id mode request_identity world_identity candidate_identity candidate start_tick end_tick frames events per_target sensing_results metrics final_positions final_assignment input_unchanged',path)
    world=request(req,path=path+'/request')
    for name,value in [('request_identity',req['evaluation_request_id']),('world_identity',world),('candidate_identity',c['candidate_id']),('start_tick',req['checkpoint']['tick']),('end_tick',req['prediction_end_tick'])]:same(row[name],value,path+'/'+name)
    legacy=dict(c['key'],index=c['index'],mask=c['resource_mask'],structural_key=c['key'],candidate_identity=c['candidate_id'],request_identity=c['evaluation_request_id'],world_identity=c['world_id'])
    same(row['candidate'],legacy,path+'/candidate')
    for i,s in enumerate(row['sensing_results']):
        fusion(s,path+f'/sensing_results/{i}',req['checkpoint']['checkpoint_id'],c['candidate_id'],world)

def fusion(row,path,checkpoint_id,action_id,world):
    needed(row,{'frame':dict,'result':dict},path)
    needed(row['frame'],{'records':list,'target_id':int,'tick':int,'stream_id':str,'frame_id':str},path+'/frame')
    needed(row['result'],{'flow_context':dict,'flow_registration':dict,'payload':dict,'quality':dict,'normalized_frame':dict,'payload_sha256':str,'frame_sha256':str},path+'/result')
    for i,record in enumerate(row['frame']['records']):
        needed(record,{'sensor_id':str,'packet_id':str,'position':list,'bearing':float,'sigma':float,'measurement_tick':int,'available_tick':int,'status':str},path+f'/frame/records/{i}')
        require(len(record['position'])==2,path+f'/frame/records/{i}/position','expected xy')
        for n,v in enumerate(record['position']):require(type(v) is float,path+f'/frame/records/{i}/position/{n}','invalid coordinate type')
    needed(row['result']['flow_context'],{'checkpoint_id':str,'action_identity':str,'work_instance_id':str},path+'/result/flow_context')
    needed(row['result']['flow_registration'],{'context':dict,'start_tick':int,'stream_id':str,'target_id':int,'allowed_sensor_ids':list},path+'/result/flow_registration')
    needed(row['result']['quality'],{'payload_sha256':str},path+'/result/quality')
    frame=row['frame'];result=row['result'];ctx=result['flow_context'];reg=result['flow_registration']
    same(ctx['checkpoint_id'],checkpoint_id,path+'/result/flow_context/checkpoint_id')
    same(ctx['action_identity'],action_id,path+'/result/flow_context/action_identity')
    same(ctx['world_identity'],world,path+'/result/flow_context/world_identity')
    same(reg['context'],ctx,path+'/result/flow_registration/context')
    stream=f"{ctx['work_instance_id']}:T{frame['target_id']}:first{reg['start_tick']}"
    same(frame['stream_id'],stream,path+'/frame/stream_id')
    same(frame['frame_id'],f"{stream}:tick{frame['tick']}",path+'/frame/frame_id')
    for i,p in enumerate(frame['records']):
        same(p['packet_id'],f"{stream}:tick{frame['tick']}:{p['sensor_id']}",path+f'/frame/records/{i}/packet_id')
    for name in ('stream_id','frame_id','tick','target_id'):same(result[name],frame[name],path+'/result/'+name)
    same(result['payload_sha256'],digest(result['payload']),path+'/result/payload_sha256')
    same(result['quality']['payload_sha256'],result['payload_sha256'],path+'/result/quality/payload_sha256')
    same(result['frame_sha256'],digest(result['normalized_frame']),path+'/result/frame_sha256')
    records=sorted(frame['records'],key=lambda r:int(r['sensor_id'][1:]))
    same(result['normalized_frame'],dict(frame,records=records),path+'/result/normalized_frame')
    require(len({r['sensor_id'] for r in records})==len(records),path+'/frame/records','duplicate sensor')
    current=[r for r in records if r['measurement_tick']==frame['tick']]
    payload=dict(sensor_ids=[r['sensor_id'] for r in current],positions=[r['position'] for r in current],bearings=[r['bearing'] for r in current],sigmas=[r['sigma'] for r in current],domain=[[0.,0.],[20.,20.]])
    same(result['payload'],payload,path+'/result/payload')
    for name,value in [('stream_id',stream),('target_id',frame['target_id']),('context',ctx),('allowed_sensor_ids',row['allowed_sensor_ids'])]:same(reg[name],value,path+'/result/flow_registration/'+name)
    same(row['start_tick'],reg['start_tick'],path+'/start_tick')

def needed(value,requirements,path):
    require(type(value) is dict,path,'expected object')
    for key,kind in requirements.items():
        require(key in value,path+'/'+key,'missing field')
        require(type(value[key]) is kind,path+'/'+key,'invalid field type')

def guarded(call,path):
    """Batch boundary: malformed input is a rejection, never a batch crash."""
    try:return call()
    except EvidenceError:raise
    except KeyError as e:raise EvidenceError('INVALID_EVIDENCE',path+'/'+str(e.args[0]),'missing nested field') from e
    except (TypeError,ValueError,IndexError,AttributeError,OverflowError,AssertionError) as e:
        raise EvidenceError('INVALID_EVIDENCE',path,'malformed structure: '+str(e)) from e

class IdentityMap:
    """Explicit namespace, scope, path, and scientific-object-bound bijection."""
    def __init__(self):self.forward={};self.reverse={};self.records=[]
    def register(self,namespace,scope,path,left,right,left_object,right_object,*,artifact='operation'):
        from .a0_mapping import namespace as policy_namespace, scope_key
        require(namespace==policy_namespace(artifact,path),path,'identity namespace mismatch')
        scope=scope_key(scope)
        same(left_object,right_object,path+'/scientific_object')
        require(type(left) is str and type(right) is str,path,'identity must be string')
        a=(namespace,scope,left);b=(namespace,scope,right)
        require(a not in self.forward or self.forward[a]==right,path,'identity mapping conflict')
        require(b not in self.reverse or self.reverse[b]==left,path,'identity mapping conflict')
        self.forward[a]=right;self.reverse[b]=left
        self.records.append(dict(namespace=namespace,scope=scope,path=path,left=left,right=right))

def decision(root,mode,index):
    r=Reader(root);folder=f'{mode}/D{index}'
    cp=binding(r.read(folder+'/BINDING.json'),'/'+folder+'/BINDING')
    req=r.read(folder+'/REQUEST.json');request(req,cp,'/'+folder+'/REQUEST')
    m=r.read(folder+'/MANIFEST.json');manifest(m,req,'/'+folder+'/MANIFEST')
    for i,c in enumerate(m['candidates']):
        label=folder+'/PREDICT/'+(f'C{i}' if mode=='R' else f'B{i//4}/C{i}')
        candidate(r.read(label+'.json'),c,req,'/'+label)
    return dict(status='IDENTITY_SUBSET_VALIDATED',scope='checkpoint/binding/request/manifest/candidate outer identities',files=r.files)

def execution_links(cp,req,m,table,selection,step,after,path):
    """Identity/transaction linkage only; no optimality or physics claim."""
    for name,value in [('checkpoint_id',cp['checkpoint_id']),('request_identity',req['evaluation_request_id']),('world_identity',m['world_identity']),('candidate_count',len(m['candidates']))]:
        same(selection[name],value,path+'/SELECTION/'+name)
    same(selection['table'],table['table'],path+'/SELECTION/table')
    same(selection['B64'],table['B64'],path+'/SELECTION/B64')
    ids=selection['selected_indices'];require(len(ids)==len(set(ids)),path+'/SELECTION/selected_indices','duplicate candidate')
    require(all(type(i) is int and 0<=i<len(m['candidates']) for i in ids),path+'/SELECTION/selected_indices','invalid index')
    same(selection['selected_candidate_ids'],[m['candidates'][i]['candidate_id'] for i in ids],path+'/SELECTION/selected_candidate_ids')
    actions=[dict(target=None,role='none') for _ in cp['positions']];occupied=set();targets=set()
    for i in ids:
        key=m['candidates'][i]['key'];require(key['target'] not in targets,path+'/SELECTION/selected_indices','duplicate target');targets.add(key['target'])
        for robot,role in zip(key['robots'],key['roles']):
            require(robot not in occupied,path+'/SELECTION/actions','overlapping resources');occupied.add(robot);actions[robot]=dict(target=key['target'],role=role)
    same(selection['actions'],actions,path+'/SELECTION/actions')
    meta=selection['action_metadata'];same(meta['actions'],actions,path+'/SELECTION/action_metadata/actions')
    changes=sum(a!=b for a,b in zip(cp['assignment'],actions))
    same(selection['assignment_change_count'],changes,path+'/SELECTION/assignment_change_count')
    for name in ('assignment_change_count','change_count'):same(meta[name],changes,path+'/SELECTION/action_metadata/'+name)
    same(meta['change_cost'],float(cp['config']['change_cost']*changes),path+'/SELECTION/action_metadata/change_cost')
    commit=step['action_commit'];schema(commit,'CommittedAction',path+'/STEP/action_commit')
    sealed(commit,'action_commit_id',path+'/STEP/action_commit')
    same(step['action_commit_id'],commit['action_commit_id'],path+'/STEP/action_commit_id')
    same(commit['checkpoint_id'],cp['checkpoint_id'],path+'/STEP/action_commit/checkpoint_id')
    same(commit['assignment'],actions,path+'/STEP/action_commit/assignment')
    same(commit['assignment_change_count'],changes,path+'/STEP/action_commit/assignment_change_count')
    same(commit['change_cost'],meta['change_cost'],path+'/STEP/action_commit/change_cost')
    same(commit['start_tick'],cp['tick'],path+'/STEP/action_commit/start_tick')
    same([t['target_id'] for t in commit['transitions']],[t['target_id'] for t in meta['transitions']],path+'/STEP/action_commit/transitions')
    for i,(a,b) in enumerate(zip(commit['transitions'],meta['transitions'])):
        for name in ('kind','old_segment_id','new_segment_id'):
            same(a[name],b[name],path+f'/STEP/action_commit/transitions/{i}/'+name)
    for i,row in enumerate(meta['flows']):
        p=path+f'/SELECTION/action_metadata/flows/{i}';f=row['flow_registration'];schema(f,'FlowRegistration',p+'/flow_registration')
        same(f['checkpoint_id'],cp['checkpoint_id'],p+'/flow_registration/checkpoint_id')
        for name in ('target_id','team','segment_id','service_start_tick','first_new_fusion_tick','allowed_sensor_ids'):
            same(f[name],row[name],p+'/flow_registration/'+name)
        ctx=row['context'];op=f['operation']
        for name in ('work_instance_id','physical_environment_id'):same(ctx[name],op[name],p+'/context/'+name)
        same(row['registration']['context'],ctx,p+'/registration/context')
        same(row['registration']['stream_id'],op['stream_id'],p+'/registration/stream_id')
        same(row['stream_id'],op['stream_id'],p+'/stream_id')
    same(step['start_tick'],cp['tick'],path+'/STEP/start_tick')
    same(step['end_tick'],min(cp['tick']+20,cp['episode_end_tick']),path+'/STEP/end_tick')
    same(step['status'],'COMMITTED',path+'/STEP/status');same(step['replayed'],False,path+'/STEP/replayed')
    same(step['checkpoint_after'],after,path+'/STEP/checkpoint_after');checkpoint(after,path+'/AFTER')
    same(after['previous_checkpoint_id'],cp['checkpoint_id'],path+'/AFTER/previous_checkpoint_id')
    same(after['tick'],step['end_tick'],path+'/AFTER/tick')
    same(binding(step['public_binding'],path+'/STEP/public_binding'),after,path+'/STEP/public_binding/public_checkpoint')
    same(step['frames'][0]['assignment'],actions,path+'/STEP/frames/0/assignment')
    for i,row in enumerate(step['fusion_records']):
        fusion(row,path+f'/STEP/fusion_records/{i}',cp['checkpoint_id'],row['context']['segment_id'],None)
        same(row['context'],row['result']['flow_context'],path+f'/STEP/fusion_records/{i}/context')

def mode_chain(root,mode):
    """Validate one mode; no cross-mode mapping or science equivalence."""
    return guarded(lambda:_mode_chain(root,mode),'/'+mode)

def _mode_chain(root,mode):
    require(mode in ('R','S_NEW'),'/mode','unknown mode');r=Reader(root)
    ix=r.read(mode+'/EPISODE_INDEX.json');source=r.read(ix['private_input_file'],'SOURCE_INPUT.json')
    design=r.read(ix['design_file'],'DESIGN.json')
    declarations=[e for e in design['episodes'] if e['episode_id']==ix['episode_id']]
    require(len(declarations)==1,'/'+mode+'/EPISODE_INDEX/episode_id','missing or duplicate design episode')
    same(declarations[0]['private_execution_input'],source,'/'+mode+'/EPISODE_INDEX/private_input_file')
    previous=checkpoint(r.read(ix['initial_artifacts']['public_checkpoint'],mode+'/INITIAL_CHECKPOINT.json'),'/'+mode+'/INITIAL_CHECKPOINT')
    same(binding(r.read(mode+'/INITIAL_BINDING.json')),previous,'/'+mode+'/INITIAL_BINDING')
    end=previous['episode_end_tick'];ticks=list(range(0,end,20))
    same([d['tick'] for d in ix['decisions']],ticks,'/'+mode+'/EPISODE_INDEX/decisions')
    for i,d in enumerate(ix['decisions']):
        folder=f'{mode}/D{i}';path='/'+folder
        b=r.read(folder+'/BINDING.json');cp=binding(b,path+'/BINDING')
        same(cp,previous,path+'/BINDING/public_checkpoint')
        req=r.read(folder+'/REQUEST.json');request(req,cp,path+'/REQUEST')
        m=r.read(folder+'/MANIFEST.json');manifest(m,req,path+'/MANIFEST')
        table=r.read(folder+'/TABLE.json');rows=[]
        for n,c in enumerate(m['candidates']):
            label=folder+'/PREDICT/'+(f'C{n}' if mode=='R' else f'B{n//4}/C{n}')
            row=r.read(label+'.json');candidate(row,c,req,'/'+label);rows.append(row)
            audit=r.read(label+'/PREDICTION_AUDIT.json')
            prediction_receipt(req,row,c,audit,'/'+label+'/PREDICTION_AUDIT')
        same([s['candidate_identity'] for s in table['specs']],[c['candidate_id'] for c in m['candidates']],path+'/TABLE/specs')
        for n,(c,row) in enumerate(zip(m['candidates'],rows)):
            value=row['per_target'][str(c['key']['target'])];tr=table['table'][n]
            for key,v in [('candidate_id',c['candidate_id']),('key',c['key']),('index',n),('absolute_O',value['absolute_O']),('baseline',value['baseline']),('v',value['v'])]:same(tr[key],v,path+f'/TABLE/table/{n}/'+key)
            same(table['values'][n],value['v'],path+f'/TABLE/values/{n}')
        selection=r.read(d['selection_file'],folder+'/SELECTION.json');step=r.read(d['step_result_file'],folder+'/STEP.json');after=r.read(folder+'/AFTER.json')
        execution_links(cp,req,m,table,selection,step,after,path)
        audit=r.read(d['selection_audit_file'],folder+'/SELECTION_AUDIT/decision_audit.json')
        for key,v in [('passed',True),('tick',cp['tick']),('candidate_count',len(m['candidates'])),('selected_indices',selection['selected_indices']),('exact_optimum',selection['exact_table_value']),('legal_plan_count',selection['legal_plan_count'])]:same(audit[key],v,path+'/SELECTION_AUDIT/'+key)
        same(r.read(folder+'/ACTUAL_FRAMES.json'),step['frames'],path+'/ACTUAL_FRAMES');same(r.read(folder+'/ACTUAL_FUSIONS.json'),step['fusion_records'],path+'/ACTUAL_FUSIONS')
        previous=after
    final=r.read(mode+'/FINAL_CHECKPOINT.json');same(final,previous,'/'+mode+'/FINAL_CHECKPOINT');same(final['phase'],'TERMINAL','/'+mode+'/FINAL_CHECKPOINT/phase')
    snapshot=r.read(ix['final_artifacts']['private_snapshot'],mode+'/PRIVATE_SNAPSHOT.json');sealed(snapshot,'snapshot_digest','/'+mode+'/PRIVATE_SNAPSHOT')
    same(snapshot['checkpoint'],final,'/'+mode+'/PRIVATE_SNAPSHOT/checkpoint');same(snapshot['case'],source,'/'+mode+'/PRIVATE_SNAPSHOT/case');same(snapshot['source_identity'],digest(source),'/'+mode+'/PRIVATE_SNAPSHOT/source_identity')
    same(snapshot['action_commits'],[r.read(d['step_result_file'])['action_commit'] for d in ix['decisions']],'/'+mode+'/PRIVATE_SNAPSHOT/action_commits')
    audit=r.read(mode+'/EPISODE_AUDIT/episode_audit.json')
    for key,v in [('episode_id',ix['episode_id']),('passed',True),('decisions',len(ticks))]:same(audit[key],v,'/'+mode+'/EPISODE_AUDIT/'+key)
    same(r.read(mode+'/FINAL_METRICS.json'),snapshot['frames'][-1]['metrics'],'/'+mode+'/FINAL_METRICS')
    return dict(status='SINGLE_MODE_LINKS_VALIDATED',mode=mode,science_acceptance='NOT_EVALUATED',closed_nested_schema='DEFERRED_TO_IA3',files=r.files)
