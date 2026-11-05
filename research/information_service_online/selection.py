"""Complete-table exact selection and independent Cartesian objective audit."""
from copy import deepcopy
from fractions import Fraction
from itertools import product
import math
from types import SimpleNamespace
from pursuit_v2.types import Assignment
from research.quality_allocation.certified_solver import solve,SCALE
from . import public
from .adapter import legacy_spec
from .common import CONTRACT_ID,ContractError,digest


def restore_canonical_table(manifest,candidate_results):
    """Restore a complete declared table, validating identities independently of v.

    Production callers obtain ``manifest`` from public.build_manifest first;
    this function does not grant history authority or re-enumerate physics.
    A unit fixture may declare a synthetic finite subtable at this boundary.
    Required result fields are those emitted by the primary candidate evaluator;
    trajectories and numerical correctness remain the independent audit's scope.
    """
    def exact(value,expected,label):
        try:matches=digest(value)==digest(expected)
        except (TypeError,ValueError) as error:
            raise ContractError(label+' is not finite canonical JSON') from error
        if not matches:raise ContractError(label+' differs from the canonical candidate manifest')

    def finite_float(value,label):
        if type(value) is not float or not math.isfinite(value):
            raise ContractError(label+' must be a finite binary64 float')
        return value

    if not isinstance(manifest,dict):raise ContractError('A prevalidated candidate manifest is required')
    required={'payload','request_identity','world_identity','candidate_count','candidates'}
    if not required.issubset(manifest):raise ContractError('Candidate manifest is incomplete')
    request_id=public.validate_schema(manifest['request_identity'],'Sha256')
    world_id=public.validate_schema(manifest['world_identity'],'Sha256')
    descriptors=manifest['candidates']
    if (not isinstance(descriptors,list) or type(manifest['candidate_count']) is not int or
            manifest['candidate_count']!=len(descriptors)):
        raise ContractError('Declared candidate count differs from canonical manifest')
    try:
        start=manifest['payload']['checkpoint']['tick']
        end=manifest['payload']['prediction_end_tick']
    except (KeyError,TypeError) as error:
        raise ContractError('Manifest must bind the evaluated time window') from error
    if type(start) is not int or type(end) is not int or not 0<=start<end:
        raise ContractError('Manifest time window must be increasing integer ticks')
    specs=[];expected_by_id={}
    for index,raw in enumerate(descriptors):
        descriptor=public.validate_schema(raw,'CandidateDescriptor')
        key=descriptor['key'];robots=key['robots'];roles=key['roles']
        if (descriptor['index']!=index or robots!=sorted(robots) or len(set(robots))!=len(robots) or
                len(roles)!=len(robots) or len(robots) not in public.ROLES or
                set(roles)!=set(public.ROLES[len(robots)])):
            raise ContractError('Canonical candidate index/member/role order is malformed')
        exact(descriptor['evaluation_request_id'],request_id,'Manifest candidate request identity')
        exact(descriptor['world_id'],world_id,'Manifest candidate world identity')
        exact(descriptor['resource_mask'],sum(1<<i for i in robots),'Manifest candidate resource mask')
        expected_id=digest(dict(evaluation_request_id=request_id,world_id=world_id,key=key))
        exact(descriptor['candidate_id'],expected_id,'Manifest candidate identity')
        if expected_id in expected_by_id:raise ContractError('Repeated canonical candidate identity')
        spec=legacy_spec(descriptor);specs.append(spec);expected_by_id[expected_id]=spec
    if not isinstance(candidate_results,(list,tuple)) or len(candidate_results)!=len(specs):
        raise ContractError('Selection requires exactly the complete active candidate table')
    by_id={}
    for result in candidate_results:
        if not isinstance(result,dict):raise ContractError('Each candidate result must be a mapping')
        needed={'kind','execution_contract_id','mode','request_identity','world_identity','candidate_identity',
                'candidate','start_tick','end_tick','per_target'}
        if not needed.issubset(result):raise ContractError('Candidate result identity/descriptor is incomplete')
        candidate_id=result['candidate_identity']
        if not isinstance(candidate_id,str) or candidate_id not in expected_by_id:
            raise ContractError('Unknown candidate result identity')
        if candidate_id in by_id:raise ContractError('Duplicate candidate result identity')
        spec=expected_by_id[candidate_id]
        exact(result['kind'],'candidate_evaluation','Candidate result kind')
        exact(result['execution_contract_id'],CONTRACT_ID,'Candidate execution contract')
        exact(result['mode'],'GQ','Candidate evaluation mode')
        exact(result['request_identity'],request_id,'Candidate request identity')
        exact(result['world_identity'],world_id,'Candidate world identity')
        # Includes index, target, robots, roles, mask, structural_key and all
        # three identities. Equal numerical values cannot conceal swapped rows.
        exact(result['candidate'],spec,'Candidate result descriptor')
        exact(result['start_tick'],start,'Candidate start tick')
        exact(result['end_tick'],end,'Candidate end tick')
        per_target=result['per_target'];target_key=str(spec['target'])
        if not isinstance(per_target,dict) or set(per_target)!={target_key}:
            raise ContractError('Primary result must contain exactly its declared target row')
        row=per_target[target_key]
        if not isinstance(row,dict) or not {'target','selected_team','absolute_O','baseline','v'}.issubset(row):
            raise ContractError('Candidate value row lacks target/team/value fields')
        exact(row['target'],spec['target'],'Candidate value-row target')
        exact(row['selected_team'],[[i,r] for i,r in zip(spec['robots'],spec['roles'])],
              'Candidate value-row selected team')
        for field in ('absolute_O','baseline','v'):finite_float(row[field],'Candidate '+field)
        by_id[candidate_id]=result
    if set(by_id)!=set(expected_by_id):raise ContractError('Canonical candidate table coverage differs')
    values=[];base_by_target={};table=[]
    for spec in specs:
        row=by_id[spec['candidate_identity']]['per_target'][str(spec['target'])]
        # Preserve the original binary64 value and physical-baseline operations.
        if row['v']!=float(row['absolute_O']-row['baseline']):raise ContractError('Incremental value arithmetic differs')
        previous=base_by_target.setdefault(spec['target'],row['baseline'])
        if previous.hex()!=row['baseline'].hex():raise ContractError('Inconsistent physical baseline')
        values.append(row['v']);table.append(dict(index=spec['index'],key=deepcopy(spec['structural_key']),
            candidate_id=spec['candidate_identity'],absolute_O=row['absolute_O'],baseline=row['baseline'],v=row['v']))
    base=0.
    for target in sorted(base_by_target):base+=base_by_target[target]
    return dict(specs=specs,values=values,table=table,B64=base)


def enumerate_plans(checkpoint,specs,values,base):
    choices=[]
    for target in checkpoint['targets']:
        choices.append([None]+[s for s in specs if s['target']==target['id']])
    for selected in product(*choices):
        chosen=[s for s in selected if s is not None]
        members=[i for s in chosen for i in s['robots']]
        if len(set(members))!=len(members):continue
        actions=[dict(target=None,role='none') for _ in checkpoint['positions']]
        for s in chosen:
            for i,r in zip(s['robots'],s['roles']):actions[i]=dict(target=s['target'],role=r)
        changes=sum(a!=b for a,b in zip(actions,checkpoint['assignment']))
        score=Fraction.from_float(base)+sum((Fraction.from_float(values[s['index']]) for s in chosen),Fraction())-Fraction.from_float(checkpoint['config']['change_cost'])*changes
        yield dict(selected=[s['index'] for s in chosen],actions=actions,changes=changes,exact_value=score)


def select(request,candidate_results,*,authority,work_identity,physical_environment_id):
    manifest=public.build_manifest(request,authority=authority)
    request=manifest['payload'];cp=request['checkpoint']
    restored=restore_canonical_table(manifest,candidate_results)
    specs,values,table,base=(restored[k] for k in ('specs','values','table','B64'))
    obs=SimpleNamespace(config=SimpleNamespace(robots=cp['config']['robots'],change_cost=cp['config']['change_cost']),
                        assignment=tuple(Assignment(**a) for a in cp['assignment']))
    native=[SimpleNamespace(**s) for s in specs]
    selected,units=solve(obs,native,values)
    plans=list(enumerate_plans(cp,specs,values,base))
    optimum=max(p['exact_value'] for p in plans)
    table_value=Fraction.from_float(base)+Fraction(units,SCALE)
    if table_value!=optimum:raise ContractError('Exact DP differs from independent Cartesian optimum')
    chosen=next(p for p in plans if p['selected']==list(selected))
    if chosen['exact_value']!=optimum:raise ContractError('Returned actions are not table optimal')
    # The sealed solver owns the canonical tie rule; a restored canonical table
    # must produce the same actions independent of result arrival order.
    reverse_restored=restore_canonical_table(manifest,list(reversed(candidate_results)))
    if digest(reverse_restored)!=digest(restored):raise ContractError('Canonical candidate identity/value restoration differs by arrival order')
    selected_again,units_again=solve(obs,native,reverse_restored['values'])
    if selected_again!=selected or units_again!=units:raise ContractError('Canonical tie/order stability failed')
    plan=public.plan_action_metadata(cp,chosen['actions'],work_identity,physical_environment_id=physical_environment_id)
    return dict(passed=True,optimality_checked=True,tie_rule_checked=True,tie_rule_scope='canonical manifest and unchanged exact solver; restored arrival order checked',checkpoint_id=cp['checkpoint_id'],request_identity=manifest['request_identity'],
        world_identity=manifest['world_identity'],candidate_count=len(specs),table=table,B64=base,
        selected_indices=list(selected),selected_candidate_ids=[specs[i]['candidate_identity'] for i in selected],
        actions=chosen['actions'],assignment_change_count=chosen['changes'],exact_table_value=str(table_value),
        table_value_float=float(table_value),legal_plan_count=len(plans),tied_optima=sum(p['exact_value']==optimum for p in plans),
        independent_plans=[dict(p,exact_value=str(p['exact_value'])) for p in plans],
        action_metadata=plan,scope='one admitted public snapshot and its complete binary64 table, not episode optimality')
