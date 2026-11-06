"""Private physical world, explicit sanitized A1 policy view."""
from copy import deepcopy
import numpy as np
from research.information_service_online.execution import OnlineEnvironment
from .belief import Beliefs,trajectory

class NonOracleEnvironment(OnlineEnvironment):
    def __init__(self,case,sense_callback,physical_environment_id,announcements,**kwargs):
        source=case.get('private_execution_input',case)
        self._validate_announcements(source,announcements)
        self.beliefs=Beliefs(announcements,deferred=self.policy_kind=='A2_POLICY_INPUT');self.frozen=None;self.decision_tick=None
        super().__init__(case,sense_callback,physical_environment_id,**kwargs)

    policy_kind='A1_POLICY_INPUT'

    def _validate_announcements(self,source,announcements):
        if [a['id'] for a in announcements]!=[t['id'] for t in source['targets']]:raise ValueError('Announcement IDs must match current A1 world')
        for a,t in zip(announcements,source['targets']):
            if self.policy_kind=='A1_POLICY_INPUT' and (a['announcement_tick']!=0 or t['birth']!=0.):raise ValueError('A1 simultaneous-birth input only')
            if any(a[k]!=t[k] for k in ('birth','weight','deadline','service_duration','required_robots')):raise ValueError('Public task metadata mismatch')
    def _fuse(self,state,target,team,tick):
        endpoint,slots=super()._fuse(state,target,team,tick)
        self.beliefs.enqueue(dict(source='ACTUAL',target_id=target,measurement_tick=tick,available_tick=tick,estimate=deepcopy(self.fusions[-1]['result']['estimate_result'])))
        return endpoint,slots
    def prepare_decision(self):
        if self.decision_tick==self.tick:raise ValueError('Decision already frozen')
        cp=self.observe_public() # private execution cut, not passed to policy
        if self.policy_kind=='A2_POLICY_INPUT':self.beliefs.activate_visible(self.tick,{t['id'] for t in cp['targets']})
        self.frozen=self.beliefs.freeze(self.tick);self.decision_tick=self.tick
        announcements={a['id']:a for a in self.beliefs.announcements}
        targets=[deepcopy(announcements[t['id']]) for t in cp['targets']]
        return dict(kind=self.policy_kind,tick=self.tick,end_tick=self.end_tick,config=deepcopy(cp['config']),positions=deepcopy(cp['positions']),assignment=deepcopy(cp['assignment']),sensor_profiles=deepcopy(cp['sensor_profiles']),targets=targets,beliefs=deepcopy(self.frozen),histories=deepcopy(cp['task_histories']),current_slots=deepcopy(cp['current_slots']))
    def _control_command(self,target_id,at,positions,offsets):
        if self.frozen is None or self.decision_tick!=self.tick-self.tick%20:raise ValueError('Missing current frozen belief')
        p,v=trajectory(self.frozen[target_id],round(at/.05))
        return np.asarray(v)+self.cfg.travel_gain*(np.asarray(p)+offsets-positions)

class StaggeredEnvironment(NonOracleEnvironment):
    policy_kind='A2_POLICY_INPUT'

    def prepare_decision(self):
        if self.tick%20 or self.done:
            raise ValueError('A2 requires a live decision tick')
        view=super().prepare_decision()
        if not hasattr(self,'first_visible_ticks'):
            self.first_visible_ticks={}
        for target in view['targets']:
            self.first_visible_ticks.setdefault(target['id'],self.tick)
        view['first_policy_visible_ticks']=deepcopy(self.first_visible_ticks)
        return view

    def _validate_announcements(self,source,announcements):
        super()._validate_announcements(source,announcements)
        for a,t in zip(announcements,source['targets']):
            tick=a['announcement_tick']
            if type(tick) is not int or tick<0 or tick%20 or abs(tick*.05-t['birth'])>1e-10:
                raise ValueError('A2 announcement must coincide with birth on a decision tick')
