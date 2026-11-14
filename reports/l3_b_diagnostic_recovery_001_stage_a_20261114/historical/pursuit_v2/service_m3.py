"""Explicit single-decision angular service M3 API. Episode runner stays guarded."""
from .policies import Decision
from research.quality_allocation.service_m3_angular.worlds import public_request
from research.quality_allocation.service_m3_angular.model import candidates
from research.quality_allocation.service_m3_angular.lazy import lazy
from research.quality_allocation.service_m3_angular.additive import assignment

POLICY_NAME='M3_service_angular_v1'


class M3ServiceAngularPolicy:
    """Stateless API: each call builds a fresh request and fresh motion cache."""
    name=POLICY_NAME

    def __init__(self, *, epsilon=0., budget=None, until=None):
        self.epsilon=epsilon
        self.budget=budget
        self.until=until

    def decide(self, obs):
        case=public_request(obs,self.until)
        specs=candidates(case)
        result=lazy(case,specs,self.epsilon,self.budget)
        selected=tuple(specs[i].key for i in result['selected'])
        actions=assignment(case,selected)
        log=dict(policy=self.name,solver='exact_dyadic',request_identity=case.identity,
                 observation_identity=case.observation_identity,world_contract='public_cv_v1',
                 prediction_worlds=1,window=[case.obs.time,case.until],candidate_count=len(specs),
                 selected=[dict(target=specs[i].target,robots=specs[i].robots,roles=specs[i].roles,
                                resource_mask=specs[i].mask) for i in result['selected']],
                 certificate=dict(L=str(result['L']),U=str(result['U']),gap=str(result['U']-result['L']),
                                  epsilon=self.epsilon,accuracy_met=result['accuracy_met'],
                                  scope='frozen_binary64_candidate_table_and_costs_v1'),
                 lazy=dict(exact=result['exact'],skipped=result['total']-result['exact'],
                           partial_incumbents=result['partial_incumbents'],full_target_batches=result['full_target_batches'],
                           components=result['components'],component_cache_hits=result['component_cache_hits'],
                           robot_control_substeps=result['robot_control_substeps'],dp_calls=result['dp_calls'],
                           requests=result['requests'],history=result['history']),
                 stop_reason=result['stop_reason'],budget=result['budget'],online_episode_validated=False)
        return Decision(actions,log)


def make_service_m3_policy(name, **options):
    if name!=POLICY_NAME: raise ValueError('Unknown explicit service M3 strategy')
    return M3ServiceAngularPolicy(**options)
