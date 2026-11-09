"""Independent, unfused MODEL fixture. No sampling, WLS or dynamics on creation."""
from copy import deepcopy
from dataclasses import dataclass
import math
from pursuit_v2.config import Config
from pursuit_v2.types import Target
from pursuit_v2.observation_geometry import offset
from .belief import Beliefs
from .stfbs_d1a_replay import digest
from .stfbs_d1a_history_audit import register_context,audit_histories
from research.information_service_online.public import seal_slot

FIXTURE_STATUS='STRUCTURALLY_VALIDATED_UNFUSED_MODEL_FIXTURE'
TEST_DOUBLE='TEST_DOUBLE_NOT_PHYSICAL_EVIDENCE'

@dataclass(frozen=True)
class ModelFixture:
    view: dict
    seed: dict
    world: dict
    identity: dict

def build_fixture(*,change_cost=.01):
    cfg=Config(robots=3,task_count=1,side=20.,max_stages=2,prediction_stages=1,
               capture_mode='stepwise_service',geometry_mode='angular_standoff_v1',change_cost=change_cost)
    target=Target(id=0,birth=3.,position_at_birth=(9.,10.),velocity=(.4,0.),
                  required_robots=2,weight=1.,deadline=5.,service_duration=1.05)
    ann=dict(id=0,birth=target.birth,announcement_tick=60,coarse_position=[9.,10.],
             velocity_prior=[.4,0.],speed_limit=.8,required_robots=2,weight=1.,deadline=5.,service_duration=1.05)
    beliefs=Beliefs([ann],deferred=True);beliefs.activate_visible(60,{0});frozen=beliefs.freeze(60)
    positions=[(offset(role,cfg)+[9.,10.]).tolist() for role in ('dual_neg45','dual_pos45')]
    positions.append([positions[1][0]+.70,positions[1][1]])
    event=dict(event_index=0,target_id=0,kind='BIRTH',segment_id=None,
               at=dict(time_seconds=3.,event_tick=60),progress_before=0.,progress_after=0.,
               reasons=['MODEL_BIRTH'],provenance='SIMULATED',observation_origin='MODEL',model_branch_id='D1B_MODEL_FIXTURE')
    history=dict(target_id=0,birth_tick=60,cutoff_tick=60,active_segment_id=None,segments=[],
                 unassigned_intervals=[dict(start_tick=60,end_at=None,opened_by='BIRTH',opening_event_index=0,closing_event_index=None)],
                 events=[event],contract_id='D1B_UNFUSED_MODEL_HISTORY_V1')
    history['history_digest']=digest(history)
    profiles=[dict(sensor_id='U'+str(i),sigma=.02,health='available',observed_tick=60) for i in range(3)]
    slots=[seal_slot(dict(slot_key=dict(target_id=0,robot_id=i,tick=60),state='UNQUERIED',packet=None,slot_digest=None)) for i in range(3)]
    view=dict(kind='A2_POLICY_INPUT',tick=60,end_tick=120,config=cfg.to_dict(),positions=positions,
              assignment=[dict(target=None,role='none') for _ in range(3)],sensor_profiles=profiles,
              targets=[deepcopy(ann)],beliefs=deepcopy(frozen),histories=[history],current_slots=slots,first_policy_visible_ticks={0:60})
    seed=dict(announcements=[deepcopy(ann)],internal_states_at_D60=deepcopy(beliefs.states),
              frozen_policy_beliefs_at_D60=deepcopy(frozen),accepted_position_history=deepcopy(beliefs.history),
              pending_observations=[],consumed_records=[],accepted_receipts={},provenance='SIMULATED',
              observation_origin='MODEL',recovery_contract='D1B_INDEPENDENT_PUBLIC_PRIOR_SEED_V1',public_D60_digest=digest(view))
    world=dict(public_digest=digest(view),motion={0:dict(position=[9.,10.],velocity=[.4,0.])},
               start_tick=60,end_tick=120,motion_rule='constant_velocity_from_public_D60_v1',perturbation='zero_v1',
               provenance='SIMULATED',observation_origin='MODEL',contract_id='D1B_QM_CONDITIONAL_WORLD_V1')
    world['world_digest']=digest(world)
    identity=dict(status=FIXTURE_STATUS,public_digest=digest(view),world_digest=world['world_digest'],
                  seed_digest=digest(seed),source='Independent MODEL birth/public-prior fixture, no ACTUAL checkpoint',
                  fused=False,physical_validation=False,initial_endpoint=None,Q=None)
    fixture=ModelFixture(view,seed,world,identity);validate_fixture(fixture)
    return fixture

def validate_fixture(fixture):
    v=fixture.view;s=fixture.seed;w=deepcopy(fixture.world)
    cfg=Config(**v['config'])
    if (cfg.robots,cfg.task_count,v['tick'],v['end_tick'])!=(3,1,60,120):raise ValueError('Invalid independent fixture dimensions')
    t=v['targets'][0]
    if len(v['targets'])!=1 or (t['id'],t['birth'],t['service_duration'],t['deadline'])!=(0,3.,1.05,5.):raise ValueError('Invalid fixture task')
    if t['coarse_position']!=[9.,10.] or t['velocity_prior']!=[.4,0.] or t['weight']!=1. or t['announcement_tick']!=60:raise ValueError('Invalid fixture public prior')
    if len(v['positions'])!=3 or any(len(p)!=2 or any(not math.isfinite(x) or not 0<=x<=20 for x in p) for p in v['positions']):raise ValueError('Invalid fixture positions')
    if v['assignment']!=[dict(target=None,role='none')]*3 or any(x['state']!='UNQUERIED' for x in v['current_slots']):raise ValueError('Fixture must be unfused/unassigned')
    if s['provenance']!='SIMULATED' or s['observation_origin']!='MODEL':raise ValueError('Fixture provenance must be MODEL')
    if s['pending_observations'] or s['consumed_records'] or s['accepted_receipts']:raise ValueError('Unfused fixture cannot have observations')
    if s['internal_states_at_D60']!=v['beliefs'] or s['frozen_policy_beliefs_at_D60']!=v['beliefs']:raise ValueError('Prior/seed mismatch')
    if s['announcements']!=v['targets'] or v['beliefs'][0]['position_estimate']!=t['coarse_position'] or v['beliefs'][0]['velocity_estimate']!=t['velocity_prior']:raise ValueError('Announcement/state mismatch')
    if v['beliefs'][0]['source']!='PUBLIC_PRIOR' or v['beliefs'][0]['last_observation_tick'] is not None:raise ValueError('Fixture must start from public prior')
    for h in v['histories']:
        if h['segments'] or h['active_segment_id'] is not None or h['events'][0]['observation_origin']!='MODEL':raise ValueError('Fixture history not an unfused MODEL birth')
    ctx=register_context('FIXTURE_CHECK',{h['target_id']:h for h in v['histories']})
    audit_histories({h['target_id']:h for h in v['histories']},v['assignment'],{0:'active'},60,context=ctx)
    saved=w.pop('world_digest')
    if saved!=digest(w) or w['public_digest']!=digest(v) or s['public_D60_digest']!=digest(v):raise ValueError('Fixture identity mismatch')
    if w['motion']!={0:dict(position=[9.,10.],velocity=[.4,0.])} or w['provenance']!='SIMULATED' or w['observation_origin']!='MODEL':raise ValueError('Conditional MODEL world mismatch')
    if fixture.identity['status']!=FIXTURE_STATUS or fixture.identity['fused'] or fixture.identity['physical_validation'] or fixture.identity['Q'] is not None:raise ValueError('Invalid unfused identity')
    return dict(status=FIXTURE_STATUS,fused=False,physical_validation=False)
