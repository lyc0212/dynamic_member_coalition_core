"""Public-only numeric views after online history admission; never legacy bypass."""
from copy import deepcopy
from .common import ContractError,digest
from . import public

def flatten_request(request, *,authority=None,unit_only=False):
    manifest=public.build_manifest(request,authority=authority,unit_only=unit_only)
    req=manifest['payload'];cp=req['checkpoint'];histories=[]
    for h in cp['task_histories']:
        active=h['active_segment_id']
        if active is None:
            clock=dict(base=0.,intervals=0,team=[]);left=None
        else:
            seg=next(s for s in h['segments'] if s['segment_id']==active)
            c=seg['latest_clock'];clock=dict(base=c['base'],intervals=c['intervals'],
                team=[[r['robot_id'],r['role']] for r in c['team']])
            endpoint=seg['latest_endpoint']
            left=dict(tick=endpoint['tick'],G=endpoint['G'],Q=endpoint['quality']['status'],
                      public_payload_sha256=endpoint['quality']['payload_digest'])
        histories.append(dict(target_id=h['target_id'],clock_state=clock,last_endpoint=left,
                              mode='admitted_online_history',public_history_sha256=h['history_digest']))
    return dict(config=deepcopy(cp['config']),start_tick=cp['tick'],prediction_end_tick=req['prediction_end_tick'],
        positions=deepcopy(cp['positions']),assignment=deepcopy(cp['assignment']),targets=deepcopy(cp['targets']),
        sensor_profiles=deepcopy(cp['sensor_profiles']),gq_histories=histories),manifest

def legacy_spec(descriptor):
    return dict(descriptor['key'],index=descriptor['index'],mask=descriptor['resource_mask'],
        structural_key=deepcopy(descriptor['key']),candidate_identity=descriptor['candidate_id'],
        request_identity=descriptor['evaluation_request_id'],world_identity=descriptor['world_id'])

def legacy_manifest(request,*,history_authority=None,unit_only=False):
    manifest=public.build_manifest(request,authority=history_authority,unit_only=unit_only)
    return dict(request_identity=manifest['request_identity'],world_identity=manifest['world_identity'],
                candidates=[legacy_spec(c) for c in manifest['candidates']])

def validate_flat_request(request,*,history_authority=None,unit_only=False):
    return flatten_request(request,authority=history_authority,unit_only=unit_only)[0]

def joint_identity(request,actions,*,history_authority=None,unit_only=False):
    manifest=public.build_manifest(request,authority=history_authority,unit_only=unit_only)
    public.validate_assignment(manifest['payload']['checkpoint'],actions)
    return digest(dict(evaluation_request_id=manifest['request_identity'],assignment=actions))
