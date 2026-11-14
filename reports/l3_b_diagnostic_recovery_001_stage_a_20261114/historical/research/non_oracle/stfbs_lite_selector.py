"""Complete synthetic binary64 value table -> exact-rational minimax regret."""
from fractions import Fraction
import math

from .stfbs_lite_candidates import FIXTURE, assignment_key, digest


def table_context(candidates, worlds, *, economy_digest):
    return digest(dict(actions=[assignment_key(a['actions']) for a in candidates],
                       worlds=[(w['world_ordinal'], w['world_digest']) for w in worlds],
                       horizon=120, economy_digest=economy_digest))


def fallback(*, keep_legal, a2_available, budget_available):
    return ('KEEP_FALLBACK' if keep_legal else 'A2_FALLBACK_REQUIRED'
            if a2_available and budget_available else 'BLOCKED_NO_LEGAL_ACTION')


def select(candidates, worlds, rows, *, economy_digest, context_digest,
           keep_legal=True, a2_available=False, budget_available=True):
    """Rows are a sequence so duplicate cells cannot be silently overwritten."""
    def failed(reason):
        return dict(status=fallback(keep_legal=keep_legal, a2_available=a2_available,
                                    budget_available=budget_available), reason=reason)
    try:
        if not budget_available:
            return failed('BUDGET_EXHAUSTED')
        keys = [assignment_key(a['actions']) for a in candidates]
        ws = [w['world_digest'] for w in worlds]
        if (not keys or len(keys) != len(set(keys)) or len(worlds) != 3 or len(set(ws)) != 3
                or len({w['world_ordinal'] for w in worlds}) != 3
                or context_digest != table_context(candidates, worlds, economy_digest=economy_digest)):
            return failed('FROZEN_IDENTITY_CONFLICT')
        keeps = [k for k, a in zip(keys, candidates) if a['kind'] == 'KEEP']
        if len(keeps) != 1 or not keep_legal:
            return failed('KEEP_IDENTITY_OR_LEGALITY_FAILURE')
        values = {}
        for row in rows:
            cell = (row['assignment_key'], row['world_digest'])
            value = row['value']
            if (cell in values or cell[0] not in keys or cell[1] not in ws
                    or row['source'] != FIXTURE or row['context_digest'] != context_digest
                    or type(value) is not float or not math.isfinite(value)):
                return failed('INVALID_VALUE_CELL')
            values[cell] = Fraction.from_float(value)
        if len(values) != len(keys)*len(ws):
            return failed('INCOMPLETE_VALUE_TABLE')
        regret = {k: max(max(values[b, w] for b in keys)-values[k, w] for w in ws) for k in keys}
        keep = keeps[0]
        best = min(keys, key=lambda k: (regret[k], 0 if k == keep else 1, k))
        return dict(status='SELECTED_ACTION', assignment_key=best,
                    kind=candidates[keys.index(best)]['kind'], regrets=regret,
                    evidence=FIXTURE)
    except (KeyError, TypeError, ValueError, OverflowError):
        return failed('INVALID_TABLE_INPUT')
