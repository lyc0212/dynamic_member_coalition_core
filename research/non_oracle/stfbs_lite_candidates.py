"""IMP-1 finite-table candidates. No real A2 scoring is performed."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import math

from scripts.gq_windows.a0_plans import catalogue, plans

FIXTURE = 'SYNTHETIC_PURE_FIXTURE_NOT_SCIENTIFIC_EVIDENCE'
ROLE_CODE = {'none': 0, 'dual_neg45': 1, 'dual_pos45': 2}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def assignment_key(actions):
    if len(actions) != 3:
        raise ValueError('Expected exactly three robots')
    result = []
    for action in actions:
        target, role = action['target'], action['role']
        if target is None:
            if role != 'none':
                raise ValueError('Idle assignment has non-idle role')
            target = -1
        elif type(target) is not int or target < 0 or role not in ('dual_neg45', 'dual_pos45'):
            raise ValueError('Invalid assigned identity')
        result.append((target, ROLE_CODE[role]))
    return tuple(result)


def team(actions):
    assignment_key(actions)
    assigned = [(i, a['target'], a['role']) for i, a in enumerate(actions) if a['target'] is not None]
    if not assigned:
        return None, ()
    if len(assigned) != 2 or len({a[1] for a in assigned}) != 1 or {a[2] for a in assigned} != {'dual_neg45', 'dual_pos45'}:
        raise ValueError('Expected complete q2 team or all idle')
    return assigned[0][1], tuple((i, r) for i, _, r in assigned)


def applicability(view):
    """Validate a public-only IMP-1 envelope; receipts are not reconstructed here."""
    try:
        ids = [t['id'] for t in view['targets']]
        if (view['config']['robots'] != 3 or len(view['positions']) != 3 or len(ids) != 2
                or any(type(j) is not int or j < 0 for j in ids) or len(set(ids)) != 2
                or any(t['required_robots'] != 2 for t in view['targets'])
                or type(view['tick']) is not int or view['tick'] not in (60, 80, 100)
                or view['tick'] in view['attempted_ticks']):
            return 'NOT_APPLICABLE'
        j, members = team(view['assignment'])
        if j not in ids or len(members) != 2:
            return 'NOT_APPLICABLE'
        if (set(view['beliefs']) != set(ids) or set(view['service_states']) != set(ids)
                or set(view['public_profiles']) != set(range(3))
                or set(view['active_ids']) != set(ids) or set(view['visible_ids']) != set(ids)
                or view['public_provenance'] != 'LEGAL_PUBLIC_SNAPSHOT'):
            return 'INVALID_PUBLIC_INPUT'
        if any(len(p) != 2 or not all(math.isfinite(x) for x in p) for p in view['positions']):
            return 'INVALID_PUBLIC_INPUT'
        return 'APPLICABLE'
    except (KeyError, TypeError, ValueError):
        return 'INVALID_PUBLIC_INPUT'


def classify(current, actions):
    old_j, old_team = team(current)
    j, members = team(actions)
    if assignment_key(current) == assignment_key(actions):
        return 'KEEP'
    if j is None:
        return 'EXCLUDED'
    if j != old_j:
        return 'SWITCH'
    if {i for i, _ in members} != {i for i, _ in old_team}:
        return 'MEMBER_CHANGE'
    return 'EXCLUDED'


def select_candidates(view, keys, rows, *, source):
    status = applicability(view)
    if status != 'APPLICABLE':
        return dict(status=status, candidates=[])
    if source != FIXTURE:
        raise ValueError('IMP-1 requires synthetic injected scores')
    table = plans(view, keys, rows)  # canonical coverage, arithmetic and baseline checks
    if len(table) != 13:
        raise ValueError('Expected thirteen complete assignments')
    records = []
    for plan in table:
        kind = classify(view['assignment'], plan['actions'])
        records.append(dict(**deepcopy(plan), kind=kind,
                            assignment_key=assignment_key(plan['actions']), source=source))
    selected = []
    for kind in ('KEEP', 'SWITCH', 'MEMBER_CHANGE'):
        choices = [p for p in records if p['kind'] == kind]
        if choices:
            selected.append(min(choices, key=lambda p: (-Fraction(p['exact_value']), p['assignment_key'])))
    chosen = {p['assignment_key'] for p in selected}
    for p in records:
        p['reason'] = ('SELECTED_CLASS_BEST' if p['assignment_key'] in chosen else
                       'OUTSIDE_THREE_ACTION_CLASSES' if p['kind'] == 'EXCLUDED' else 'LOWER_SCORE_OR_KEY')
    result = dict(status='CANDIDATES_FROZEN', candidates=deepcopy(selected), audit=records, source=source)
    result['candidate_digest'] = digest(result)
    return result
