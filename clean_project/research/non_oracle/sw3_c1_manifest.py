"""Public SW3-C family numbering and frozen split."""
from copy import deepcopy
import hashlib

CENTERS = tuple((x,y) for x in (8.70,8.90,9.10,9.30) for y in (10.05,10.30,10.55))
ORDER = (11,6,4,3,10,5,1,8,2,0,9,7)


def family_digest(n):
    if type(n) is not int or not 0<=n<12:
        raise ValueError("Invalid family number")
    return hashlib.sha256(f"SW3-V1|family|{n}".encode("utf-8")).hexdigest()


def manifest():
    order = sorted(range(12),key=lambda n:(family_digest(n),n))
    if tuple(order)!=ORDER:
        raise ValueError("Frozen split mismatch")
    return [dict(n=n,center=list(CENTERS[n]),sha256=family_digest(n),
                 split="dev" if i<3 else "test" if i<11 else "reserve")
            for i,n in enumerate(order)]


def announcements_for(template,n):
    family_digest(n)
    result = deepcopy(template)
    a = result["announcements"]
    if [t["id"] for t in a]!=[0,1]:
        raise ValueError("Expected frozen two-target announcement template")
    t = a[1]
    if (t["coarse_position"],t["velocity_prior"],t["design_error_bound"],t["speed_limit"],
        t["announcement_tick"],t["motion_model"])!=([9.,10.3],[0.,0.],.5,.8,60,"constant_velocity"):
        raise ValueError("Invalid frozen T1 announcement")
    t["coarse_position"] = list(CENTERS[n])
    return result
