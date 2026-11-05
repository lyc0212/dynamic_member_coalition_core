"""Versioned minimal identity mapping policy for A0-Ib. No fields are ignored.

Only decimal array indices match '*'. Artifact kind and namespace are mandatory.
Mapping never establishes internal validity: call the Ia-2 validators first.
"""
from types import MappingProxyType
import re
from .a0_evidence import require

VERSION='a0_windows_identity_mapping_v1'
_rules={
 'operation':{'/operation/work_instance_id':'work','/operation/physical_environment_id':'environment'},
 'checkpoint':{'/checkpoint_id':'checkpoint','/previous_checkpoint_id':'checkpoint'},
 'request':{'/evaluation_request_id':'request'},
 'manifest':{'/request_identity':'request','/world_identity':'world','/candidates/*/candidate_id':'candidate','/candidates/*/evaluation_request_id':'request','/candidates/*/world_id':'world'},
 'candidate':{'/request_identity':'request','/world_identity':'world','/candidate_identity':'candidate','/candidate/candidate_identity':'candidate','/candidate/request_identity':'request','/candidate/world_identity':'world'},
 'selection':{'/checkpoint_id':'checkpoint','/request_identity':'request','/world_identity':'world','/selected_candidate_ids/*':'candidate','/table/*/candidate_id':'candidate'},
 'step':{'/action_commit_id':'commit','/action_commit/action_commit_id':'commit','/action_commit/checkpoint_id':'checkpoint'},
}
_fusion={
 '/frame/stream_id':'stream','/frame/frame_id':'frame','/frame/records/*/packet_id':'packet',
 '/result/stream_id':'stream','/result/frame_id':'frame','/result/frame_sha256':'frame_digest',
 '/result/normalized_frame/stream_id':'stream','/result/normalized_frame/frame_id':'frame',
 '/result/normalized_frame/records/*/packet_id':'packet','/result/quality/frame_id':'frame',
}
for prefix in ('/result/flow_context','/result/flow_registration/context','/context'):
 for leaf,kind in [('work_instance_id','work'),('physical_environment_id','environment'),('checkpoint_id','checkpoint'),('request_identity','request'),('world_identity','world'),('action_identity','action')]:
  _fusion[prefix+'/'+leaf]=kind
_fusion['/result/flow_registration/stream_id']='stream'
_rules['fusion']=_fusion
# Authorized minimal supplement: public.plan_action_metadata repeats each
# registered actual stream under transitions and flows; worker uses RUN_mode.
for branch in ('transitions','flows'):
 prefix='/action_metadata/'+branch+'/*'
 for leaf,kind in [('/stream_id','stream'),('/flow_registration/operation/physical_environment_id','environment'),('/flow_registration/operation/work_instance_id','work'),('/flow_registration/operation/stream_id','stream'),('/context/physical_environment_id','environment'),('/context/work_instance_id','work'),('/registration/stream_id','stream'),('/registration/context/physical_environment_id','environment'),('/registration/context/work_instance_id','work')]:
  _rules['selection'][prefix+leaf]=kind
for leaf,kind in _fusion.items():
 # Only the observed actual runtime differences, not scientific identities.
 if kind in ('stream','frame','packet','frame_digest','work','environment'):
  _rules['step']['/fusion_records/*'+leaf]=kind
RULES=MappingProxyType({k:MappingProxyType(dict(v)) for k,v in _rules.items()})
del _rules,_fusion

def namespace(artifact,path):
 normalized='/'.join('*' if re.fullmatch(r'0|[1-9][0-9]*',s) else s for s in path.split('/'))
 require(artifact in RULES and normalized in RULES[artifact],path,'unregistered identity path')
 return RULES[artifact][normalized]

def scope_key(scope):
 require(type(scope) is tuple and len(scope)==3 and all(type(v) is str and v for v in scope),'/scope','expected (run_pair, decision, scientific_object)')
 return scope
