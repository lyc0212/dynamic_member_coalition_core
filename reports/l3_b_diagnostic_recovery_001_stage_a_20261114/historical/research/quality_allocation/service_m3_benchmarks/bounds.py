"""Immediate-completion relaxation; identical binary64 benefit operation order."""
from research.quality_allocation.service_m3_angular.reference import benefit
from research.quality_allocation.service_m3_angular.bounds import all_bounds as clock_bounds


def all_bounds(case,specs,kind='L1'):
    if kind=='L1': return clock_bounds(case,specs)
    if kind!='L0': raise ValueError('Unknown bound')
    details={s.index:[dict(value=max(0.,benefit(case,case.path(w,s.target),case.obs.time,0.)))
                           for w in range(len(case.worlds))] for s in specs}
    return [sum(r['value'] for r in details[s.index])/len(case.worlds) for s in specs],details
