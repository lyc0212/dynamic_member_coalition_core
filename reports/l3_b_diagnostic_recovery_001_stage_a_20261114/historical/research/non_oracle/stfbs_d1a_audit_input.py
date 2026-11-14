"""Single read-only boundary for the world.motion target-ID mapping only."""
from copy import deepcopy


def audit_input(result, view):
    expected = {t['id'] for t in view['targets']}
    if any(type(j) is not int or j < 0 for j in expected):
        raise ValueError('Invalid public target ID')
    motion = result['world']['motion']
    converted = {}
    for key, value in motion.items():
        if type(key) is int and key >= 0:
            j = key
        elif type(key) is str and key.isascii() and key.isdecimal() and str(int(key)) == key:
            j = int(key)
        else:
            raise ValueError('Noncanonical motion target ID')
        if j in converted:
            raise ValueError('Ambiguous motion target ID')
        converted[j] = deepcopy(value)
    if set(converted) != expected:
        raise ValueError('Motion target set mismatch')
    copy = deepcopy(result)
    copy['world']['motion'] = converted
    return copy
