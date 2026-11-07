"""Public packet assembly only; no sampler, estimator or actual cache mutation.

The executor supplies acquired slots; the predictor supplies its frozen public
cut. The same record assembler retains observed data and only models UNQUERIED.
"""
from copy import deepcopy
import math
import numpy as np
from pursuit_v2.config import Config
from pursuit_v2 import observation_geometry as geometry
from .common import ContractError, DT, digest
from . import public

MEASUREMENT_ID = public.IDS['measurement_payload']


def _packet_payload(packets):
    return {'sensor_ids':[p['sensor_id'] for p in packets],
            'positions':[deepcopy(p['position']) for p in packets],
            'bearings':[p['bearing'] for p in packets],'sigmas':[p['sigma'] for p in packets],
            'domain':[[0.,0.],[20.,20.]]}


def _frame(source_slots, team, target_id, tick, stream_id):
    if type(stream_id) is not str or not stream_id: raise ContractError('Nonempty fusion stream required')
    records=[]
    for row in source_slots:
        if row['outcome']=='VALID':
            p=deepcopy(row['packet'])
            # Transport scope may change; physical/public packet values do not.
            p['packet_id']=f'{stream_id}:tick{tick}:U{row["slot_key"]["robot_id"]}'
            records.append(p)
    frame={'contract_id':MEASUREMENT_ID,'stream_id':stream_id,'frame_id':f'{stream_id}:tick{tick}',
           'tick':tick,'target_id':target_id,'measurement_time':tick*DT,'available_time':tick*DT,'records':records}
    payload=_packet_payload([r['packet'] for r in source_slots if r['outcome']=='VALID'])
    return {'frame':frame,'allowed_sensor_ids':['U'+str(m['robot_id']) for m in team],
            'source_slots':deepcopy(source_slots),'payload':payload,'payload_digest':digest(payload),
            'stream_id':stream_id,'target_id':target_id,'tick':tick}


def _slot_rows(current_slots,target_id,tick,robot_count):
    rows={}
    for raw in current_slots:
        s=public.validate_schema(raw,'MeasurementSlot');key=s['slot_key']
        if key['target_id']!=target_id: continue
        if key['tick']!=tick or key['robot_id'] in rows: raise ContractError('Wrong/duplicate current slot identity')
        if s['state']!='UNQUERIED': public._require_digest(s,'slot_digest')
        rows[key['robot_id']]=s
    if sorted(rows)!=list(range(robot_count)): raise ContractError('Complete logical current-slot row for target required')
    return rows


def assemble_left_state(*,tick,target_id,target_position,positions,sensor_profiles,current_slots,
                        team,stream_id,actual=False,traversal_robot_ids=None):
    """The actual production assembler also used by the fixed nonzero probes.

    No history is asserted by these explicit inputs. actual=True requires every
    needed slot already queried by the execution-owned sampler.
    """
    if type(actual) is not bool: raise ContractError('Explicit actual/prediction selector required')
    public.validate_schema(tick,'Tick');public.validate_schema(target_id,'TargetId')
    point=public.validate_schema(target_position,'Vector2')
    pos=[public.validate_schema(p,'Vector2') for p in positions]
    if not 2<=len(pos)<=16: raise ContractError('Independent robot position count invalid')
    team=public.validate_schema(team,'Team');public._team(team,len(team),len(pos))
    profiles=[public.validate_schema(p,'SensorProfile') for p in sensor_profiles]
    if ([p['sensor_id'] for p in profiles]!=['U'+str(i) for i in range(len(pos))]
            or any(p['observed_tick']!=tick for p in profiles)):
        raise ContractError('Current profile clock/order mismatch')
    slots=_slot_rows(current_slots,target_id,tick,len(pos));sources=[]
    before=digest(current_slots)
    visit=[m['robot_id'] for m in team] if traversal_robot_ids is None else list(traversal_robot_ids)
    if any(type(i) is not int for i in visit) or sorted(visit)!=[m['robot_id'] for m in team]:
        raise ContractError('Internal traversal must be a permutation of the same team')
    for i in visit:
        slot=slots[i];profile=profiles[i];key=deepcopy(slot['slot_key'])
        if slot['state']=='UNQUERIED':
            if actual: raise ContractError('Actual fusion cannot invent an unqueried result')
            source='MODEL';observed=None
            if profile['health']=='missing': packet=None;outcome='MISSING'
            else:
                angle=math.atan2(point[1]-pos[i][1],point[0]-pos[i][0]);angle=(angle+math.pi)%(2*math.pi)-math.pi
                packet={'sensor_id':'U'+str(i),'position':deepcopy(pos[i]),'bearing':angle,
                        'sigma':profile['sigma'],'measurement_tick':tick,'available_tick':tick,'status':'ok'}
                outcome='VALID'
        else:
            source='OBSERVED';observed=slot['slot_digest'];outcome=slot['state'];packet=deepcopy(slot['packet'])
            if packet is not None and (packet['sensor_id']!='U'+str(i) or packet['position']!=pos[i]
                or packet['sigma']!=profile['sigma'] or packet['measurement_tick']!=tick
                or packet['available_tick']!=tick or profile['health']!='available'):
                raise ContractError('Known current packet conflicts with key/position/profile')
        row={'slot_key':key,'source':source,'outcome':outcome,'packet':packet,'observed_slot_digest':observed}
        public.validate_schema(row,'PredictedSourceSlot');sources.append(row)
    sources.sort(key=lambda s:s['slot_key']['robot_id'])
    if digest(current_slots)!=before: raise ContractError('Assembler modified actual slots')
    # The same frozen geometry expression; no control step or WLS is performed.
    angles={'dual_neg45':-45.,'dual_pos45':45.,'tri_0':0.,'tri_120':120.,'tri_240':240.}
    offsets=np.array([[.6*math.cos(math.radians(angles[m['role']])),.6*math.sin(math.radians(angles[m['role']]))] for m in team])
    selected=np.array([pos[m['robot_id']] for m in team])
    G=bool(np.all(np.linalg.norm(selected-np.array(point)-offsets,axis=1)<=.15+1e-10))
    return _frame(sources,team,target_id,tick,stream_id)|{'G':G,'actual':actual,'reused_actual_endpoint':False,
        'actual_endpoint':None,'team':team,'real_sampling_calls':0,'estimator_calls':0}


def frame_from_slots(slots,team,target_id,tick,stream_id):
    """Copy already acquired packets without a target point or G computation."""
    team=public.validate_schema(team,'Team');sources=[]
    matching={}
    for raw in slots:
        s=public.validate_schema(raw,'MeasurementSlot');key=s['slot_key']
        if key['target_id']==target_id and key['tick']==tick:
            if key['robot_id'] in matching: raise ContractError('Duplicate actual slot')
            matching[key['robot_id']]=s
    for m in team:
        s=matching.get(m['robot_id'])
        if s is None or s['state']=='UNQUERIED': raise ContractError('Actual team slot is not acquired')
        public._require_digest(s,'slot_digest')
        sources.append({'slot_key':deepcopy(s['slot_key']),'source':'OBSERVED','outcome':s['state'],
                        'packet':deepcopy(s['packet']),'observed_slot_digest':s['slot_digest']})
    return _frame(sources,team,target_id,tick,stream_id)|{'actual':True}


def make_actual_endpoint(*,target_id,tick,team,G,assembly,quality_result):
    """Project a real fusion result; never accept a PREDICTION_ONLY endpoint."""
    if assembly.get('actual') is not True: raise ContractError('Prediction assembly cannot become an actual endpoint')
    if quality_result.get('flow_context',{}).get('purpose','ACTUAL_EXECUTION')!='ACTUAL_EXECUTION': raise ContractError('Prediction fusion result cannot become actual')
    if any(s['source']!='OBSERVED' for s in assembly['source_slots']): raise ContractError('Actual endpoint contains MODEL input')
    quality=quality_result.get('quality',quality_result)
    if quality.get('contract_id')!=public.IDS['quality'] or quality.get('payload_sha256')!=assembly['payload_digest']:
        raise ContractError('Actual quality contract/payload mismatch')
    slots=[{'slot_key':deepcopy(s['slot_key']),'slot_digest':s['observed_slot_digest'],'state':s['outcome']} for s in assembly['source_slots']]
    return public.seal_endpoint({'target_id':target_id,'tick':tick,'source_kind':'ACTUAL','team':deepcopy(team),'G':G,
      'quality':{'contract_id':public.IDS['quality'],'status':quality['status'],'payload_digest':assembly['payload_digest'],
                 'radius_proxy':quality.get('radius_proxy')},'slots':slots})


def assemble_current(request,candidate_descriptor,work_identity,authority=None,unit_only=False,*,
                     physical_environment_id='prediction-context',purpose='CANDIDATE_PREDICTION'):
    r=public.validate_request(request,authority,unit_only)
    meta=public.prediction_metadata(r,candidate_descriptor,work_identity,authority,unit_only,
                                   physical_environment_id=physical_environment_id,purpose=purpose)
    cp=r['checkpoint'];j=meta['target_id'];tick=cp['tick']
    if meta['reused_actual_endpoint']:
        rows=_slot_rows(cp['current_slots'],j,tick,len(cp['positions']))
        sources=[]
        for m in meta['team']:
            s=rows[m['robot_id']]
            if s['state']=='UNQUERIED': raise ContractError('KEEP endpoint has an unqueried actual slot')
            sources.append({'slot_key':deepcopy(s['slot_key']),'source':'OBSERVED','outcome':s['state'],
                            'packet':deepcopy(s['packet']),'observed_slot_digest':s['slot_digest']})
        return meta|{'frame':None,'source_slots':sources,'G':meta['actual_endpoint']['G'],
                     'payload_digest':meta['actual_endpoint']['quality']['payload_digest'],
                     'actual':False,'real_sampling_calls':0,'estimator_calls':0}
    target=next(t for t in cp['targets'] if t['id']==j)
    result=assemble_left_state(tick=tick,target_id=j,target_position=target['position_now'],positions=cp['positions'],
          sensor_profiles=cp['sensor_profiles'],current_slots=cp['current_slots'],team=meta['team'],
          stream_id=meta['stream_id'],actual=False)
    return result|meta


def assemble_future(request,candidate_descriptor,tick,positions,work_identity,authority=None,unit_only=False,*,
                    physical_environment_id='prediction-context',purpose='CANDIDATE_PREDICTION'):
    r=public.validate_request(request,authority,unit_only)
    meta=public.prediction_metadata(r,candidate_descriptor,work_identity,authority,unit_only,
                                   physical_environment_id=physical_environment_id,purpose=purpose)
    cp=r['checkpoint'];j=meta['target_id'];public.validate_schema(tick,'Tick')
    if not cp['tick']<tick<=r['prediction_end_tick']: raise ContractError('Future prediction tick outside window')
    if len(positions)!=cp['config']['robots']: raise ContractError('Future positions must retain all stable Uk')
    target=next(t for t in cp['targets'] if t['id']==j)
    elapsed=tick*DT-cp['tick']*DT
    point=[target['position_now'][i]+target['velocity_now'][i]*elapsed for i in (0,1)]
    profiles=[deepcopy(p)|{'observed_tick':tick} for p in cp['sensor_profiles']]
    slots=[public.seal_slot({'slot_key':{'target_id':j,'robot_id':i,'tick':tick},'state':'UNQUERIED','packet':None})
           for i in range(cp['config']['robots'])]
    result=assemble_left_state(tick=tick,target_id=j,target_position=point,positions=positions,sensor_profiles=profiles,
          current_slots=slots,team=meta['team'],stream_id=meta['stream_id'],actual=False)
    # Reuse is a start-of-flow property only. Future endpoint itself is MODEL.
    return result|{k:v for k,v in meta.items() if k not in ('actual_endpoint','reused_actual_endpoint')}
