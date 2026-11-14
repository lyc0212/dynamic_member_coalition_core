"""Production restoration of a declared candidate batch, not a full-table solver."""
from copy import deepcopy
import math

from . import contracts
from .common import SCIENTIFIC_CONTRACT, ContractError, typed_digest


def restore_candidate_subset(request,rows,declared_indices,history_authority=None,unit_fixture=None):
    """Validate against the complete admitted catalogue and return canonical rows.

    A valid sparse subset carries no claim of full-table coverage or DP optimality.
    """
    flat,manifest=contracts.admit_request(request,history_authority=history_authority,unit_fixture=unit_fixture)
    if (type(declared_indices) is not list or any(type(i) is not int for i in declared_indices)
            or len(set(declared_indices))!=len(declared_indices)):
        raise ContractError('Batch requires unique typed canonical indices')
    catalogue={s['index']:s for s in manifest['candidates']}
    if any(i not in catalogue for i in declared_indices):raise ContractError('Declared subset contains an unknown candidate')
    if type(rows) is not list or len(rows)!=len(declared_indices):raise ContractError('Incomplete or extra batch results')
    observed={}
    for row in rows:
        if type(row) is not dict or type(row.get('candidate')) is not dict:raise ContractError('Candidate result shape missing')
        spec=row['candidate'];index=spec.get('index')
        if type(index) is not int or index not in declared_indices or index in observed:raise ContractError('Duplicate or foreign batch index')
        descriptor=contracts.select_descriptor(manifest,spec)
        if typed_digest(descriptor)!=typed_digest(catalogue[index]):raise ContractError('Candidate metadata mismatch')
        required=dict(kind='candidate_evaluation',execution_contract_id=SCIENTIFIC_CONTRACT,mode='GQ',
            request_identity=manifest['request_identity'],world_identity=manifest['world_identity'],
            candidate_identity=descriptor['candidate_id'],start_tick=flat['start_tick'],end_tick=flat['prediction_end_tick'])
        if any(k not in row or typed_digest(row[k])!=typed_digest(v) for k,v in required.items()):
            raise ContractError('Batch result identity/mode/time differs from admitted request')
        j=descriptor['key']['target'];targets=row.get('per_target')
        if type(targets) is not dict or set(targets)!={str(j)}:raise ContractError('Batch result has another target set')
        target=targets[str(j)];team=[list(pair) for pair in zip(descriptor['key']['robots'],descriptor['key']['roles'])]
        if (type(target) is not dict or type(target.get('target')) is not int or target['target']!=j
                or typed_digest(target.get('selected_team'))!=typed_digest(team)):
            raise ContractError('Result team/target differs from descriptor')
        for name in ('absolute_O','baseline','v'):
            if type(target.get(name)) is not float or not math.isfinite(target[name]):raise ContractError('Finite binary64 candidate value required')
        if typed_digest(target['v'])!=typed_digest(float(target['absolute_O']-target['baseline'])):
            raise ContractError('Candidate v does not match the unchanged subtraction')
        observed[index]=deepcopy(row)
    if set(observed)!=set(declared_indices):raise ContractError('Declared subset coverage mismatch')
    return [observed[i] for i in sorted(declared_indices)]
