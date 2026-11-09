"""D1B profile/public interfaces and preset actions, no automatic execution."""
from copy import deepcopy
import json,math
from .stfbs_d1a_model import Branch,Budget,point
from .stfbs_d1a_replay import digest
from .stfbs_d1b_qm_scenario import validate_fixture
from research.information_service_online.public import seal_slot

class PublicQueryRejected(ValueError):pass
class CandidateAdmissionRejected(ValueError):pass

class PublicProfiles:
    """Detached immutable publication snapshot, with no authority/closure reference."""
    __slots__=('_published_json','_watermark')
    def __init__(self,watermark,published):
        object.__setattr__(self,'_watermark',watermark)
        object.__setattr__(self,'_published_json',json.dumps(published,sort_keys=True))
    def __setattr__(self,name,value):raise AttributeError('Immutable public publication snapshot')
    def __deepcopy__(self,memo):return self
    @property
    def watermark(self):return self._watermark
    def public_profile_at(self,tick):
        if type(tick) is not int or tick>self._watermark:raise PublicQueryRejected('PUBLIC_QUERY_REJECTED_AS_FUTURE')
        rows=json.loads(self._published_json);eligible=[r for r in rows if r['effective_tick']<=tick]
        if not eligible:raise PublicQueryRejected('PUBLIC_QUERY_OUTSIDE_PUBLISHED_HISTORY')
        return [dict(p,observed_tick=tick) for p in eligible[-1]['profiles']]
    def to_public_dict(self):return dict(watermark=self._watermark,published=json.loads(self._published_json))

class SensorAuthority:
    """Trusted executor only. This object is never a policy-visible object."""
    def __init__(self,degraded_sigma=.08):
        if type(degraded_sigma) not in (int,float) or not math.isfinite(degraded_sigma) or degraded_sigma<=0:raise ValueError('Invalid sigma')
        normal=[dict(sensor_id='U'+str(i),sigma=.02,health='available') for i in range(3)]
        changed=deepcopy(normal);changed[1]['sigma']=degraded_sigma
        self._schedule=[dict(effective_tick=60,public_tick=60,profiles=normal),dict(effective_tick=80,public_tick=80,profiles=changed)]
        self._watermark=60;self._published=[deepcopy(self._schedule[0])]
    def physical_profile_at(self,tick):
        if type(tick) is not int or not 60<=tick<=120:raise ValueError('Invalid MODEL physical profile tick')
        row=next(r for r in reversed(self._schedule) if r['effective_tick']<=tick)
        return [dict(p,observed_tick=tick) for p in deepcopy(row['profiles'])]
    def publish_from_executor(self,executor_tick):
        if type(executor_tick) is not int or not self._watermark<=executor_tick<=120:raise ValueError('Invalid trusted publication cut')
        self._published=[deepcopy(r) for r in self._schedule if r['public_tick']<=executor_tick]
        self._watermark=executor_tick
    def public_snapshot(self):return PublicProfiles(self._watermark,self._published)

def initial_team():return [dict(target=0,role='dual_neg45'),dict(target=0,role='dual_pos45'),dict(target=None,role='none')]
def changed_team():return [dict(target=0,role='dual_neg45'),dict(target=None,role='none'),dict(target=0,role='dual_pos45')]

def validate_assignment(view,actions):
    if not isinstance(actions,list) or len(actions)!=view['config']['robots']:raise ValueError('Complete Assignment required')
    targets={t['id']:t for t in view['targets']};teams={j:[] for j in targets}
    for i,a in enumerate(actions):
        if not isinstance(a,dict) or set(a)!={'target','role'}:raise ValueError('Malformed Assignment')
        if a['target'] is None:
            if a['role']!='none':raise ValueError('Idle role mismatch')
        else:
            if type(a['target']) is not int or a['target'] not in targets:raise ValueError('Inactive/foreign target')
            teams[a['target']].append((i,a['role']))
    for j,team in teams.items():
        if team and (len(team)!=targets[j]['required_robots'] or len(team)!=2 or {role for _,role in team}!={'dual_neg45','dual_pos45'}):raise ValueError('Invalid complete q2 team')
    return deepcopy(actions)

def admit_substitute(robot_ids,team,retained=0,outgoing=1):
    if len(set(robot_ids))!=len(robot_ids) or len(set(team))!=2 or retained not in team or outgoing not in team or retained==outgoing:raise CandidateAdmissionRejected('INVALID_PUBLIC_CANDIDATE_STATE')
    available=[r for r in robot_ids if r not in team]
    if not available:raise CandidateAdmissionRejected('PUBLIC_CANDIDATE_ADMISSION_REJECTED_AS_EXPECTED')
    return tuple(available)

def preset_action(view,branch):
    if branch not in ('B0','B1') or view['tick'] not in (60,80,100):raise ValueError('Unknown preset branch/cut')
    if view['tick']==80 and any(t['id']==0 for t in view['targets']) and view['assignment']!=initial_team():raise ValueError('Unexpected pre-intervention team')
    if not any(t['id']==0 for t in view['targets']):actions=deepcopy(view['assignment'])
    elif view['tick']==60:actions=initial_team()
    elif view['tick']==80 and branch=='B1':
        candidates=admit_substitute(tuple(range(view['config']['robots'])),(0,1))
        if 2 not in candidates or view['assignment'][2]['target'] is not None:raise CandidateAdmissionRejected('R2_NOT_AVAILABLE')
        actions=changed_team()
    else:actions=deepcopy(view['assignment'])
    return dict(contract_id='D1B_PRESET_ACTION_V1',source='EXPERIMENT_PRESET_NOT_AUTONOMOUS',branch=branch,
                tick=view['tick'],public_digest=digest(view),actions=validate_assignment(view,actions))

class QMBranch(Branch):
    def __init__(self,fixture,name='B0',degraded_sigma=.08):
        validate_fixture(fixture)
        super().__init__(fixture.view,fixture.seed,fixture.world,name,Budget())
        self._sensor_authority=SensorAuthority(degraded_sigma);self._last_public_cut=60
    def public_inputs(self):
        public=self._sensor_authority.public_snapshot()
        v=self.policy_view()
        return dict(policy_view=v,config=deepcopy(v['config']),public_profiles=public)
    def policy_view(self):
        public=self._sensor_authority.public_snapshot()
        profiles=public.public_profile_at(self.tick)  # Reject before state mutation.
        if self.tick not in (60,80,100):raise ValueError('Illegal public decision cut')
        if self.tick!=self._last_public_cut:
            self.frozen=self.consumer.freeze(self.tick);self._last_public_cut=self.tick
        active=[j for j in self.targets if self.status[j]=='active']
        v=deepcopy(self.view);v.update(tick=self.tick,positions=self.positions.tolist(),assignment=deepcopy(self.actions),
            targets=[deepcopy(self.targets[j]) for j in active],histories=[deepcopy(self.histories[j]) for j in active],
            beliefs=deepcopy(self.frozen),sensor_profiles=profiles,
            current_slots=[deepcopy(self.cache.rows[(self.name,j,i,self.tick)]['slot']) if (self.name,j,i,self.tick) in self.cache.rows else seal_slot(dict(slot_key=dict(target_id=j,robot_id=i,tick=self.tick),state='UNQUERIED',packet=None,slot_digest=None)) for j in active for i in range(3)])
        for h in v['histories']:
            h['cutoff_tick']=self.tick;h['contract_id']='D1B_MODEL_TASK_HISTORY_V1'
            h['inherited_model_history_digest']=next(x['history_digest'] for x in self.view['histories'] if x['target_id']==h['target_id'])
            for segment in h['segments']:
                segment.pop('segment_history_digest',None);segment['segment_history_digest']=digest(segment)
            h.pop('history_digest',None);h['history_digest']=digest(h)
        return v
    def run(self,*args,**kwargs):
        raise RuntimeError('QM1A_INTERFACE_ONLY: physical execution requires separately authorized 1B')
    def raw(self,j,i,tick):
        if tick!=self.tick:raise ValueError('Raw query must match actual MODEL cut')
        p=self._sensor_authority.physical_profile_at(tick)[i];pos=self.positions[i].tolist()
        context=dict(position=pos,sigma=p['sigma'],health=p['health'])
        def producer():
            packet=None;state='MISSING'
            if p['health']=='available':
                target=point(self.world,j,tick);angle=math.atan2(float(target[1]-pos[1]),float(target[0]-pos[0]))
                packet=dict(sensor_id='U'+str(i),position=pos,bearing=(angle+math.pi)%(2*math.pi)-math.pi,sigma=p['sigma'],measurement_tick=tick,available_tick=tick,status='ok');state='VALID'
            return seal_slot(dict(slot_key=dict(target_id=j,robot_id=i,tick=tick),state=state,packet=packet,slot_digest=None))
        return self.cache.query(self.name,j,i,tick,context,producer)
