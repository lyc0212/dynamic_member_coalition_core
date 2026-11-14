"""Private candidate draws. No execution or labels."""
from copy import deepcopy
import hashlib
import math

from pursuit_v2.types import Target
from .sw3_c1_manifest import CENTERS, ORDER, family_digest


def hash_unit(text):
    raw = hashlib.sha256(text.encode("utf-8")).digest()
    z = int.from_bytes(raw[:8],"big")>>12
    return raw.hex(),z,(z+.5)/2**52


def draw_component(split,n,w,a,j,*,replaces=None):
    family_digest(n)
    if split not in ("dev","test") or any(type(x) is not int or not 0<=x<limit
                                          for x,limit in ((w,4),(a,32),(j,4))):
        raise ValueError("Invalid private draw coordinate")
    group = ORDER[:3] if split=="dev" else ORDER[3:11]
    if (n==7 and (type(replaces) is not int or replaces not in group)) or (n!=7 and (n not in group or replaces is not None)):
        raise ValueError("Unregistered family/split or missing reserve replacement")
    return hash_unit(f"SW3-V1|world|{split}|{n}|{w}|{a}|{j}")


def reject_motion(p,v,side,seen):
    if not all(math.isfinite(x) for x in (*p,*v)):
        return "NONFINITE"
    if v[0]<0 or math.hypot(*v)>.8:
        return "VELOCITY_DOMAIN"
    if not all(0<=x<side and 0<=y<=side for x,y in (p,(p[0]+2*v[0],p[1]+2*v[1]))):
        return "POSITION_DOMAIN_OR_ESCAPE"
    if (p,v) in seen:
        return "DUPLICATE"
    return None


def private_world(template,split,n,w,previous,*,replaces=None):
    if type(w) is not int or not 0<=w<4 or len(previous)!=w:
        raise ValueError("Supply the previous accepted worlds in order")
    seen = {(tuple(r["targets"][1]["position_at_birth"]),tuple(r["targets"][1]["velocity"])) for r in previous}
    attempts = []
    for a in range(32):
        draws = [draw_component(split,n,w,a,j,replaces=replaces) for j in range(4)]
        u0,u1,u2,u3 = (d[2] for d in draws)
        x,y = CENTERS[n]
        r,theta = .5*math.sqrt(u0),2*math.pi*u1
        speed,angle = .8*math.sqrt(u2),math.pi*(u3-.5)
        p = (x+r*math.cos(theta),y+r*math.sin(theta))
        v = (speed*math.cos(angle),speed*math.sin(angle))
        reason = reject_motion(p,v,template["config"]["side"],seen)
        target = dict(template["targets"][1],position_at_birth=list(p),velocity=list(v))
        if reason is None:
            try:
                Target(**target)
            except (TypeError,ValueError):
                reason = "INVALID_TARGET"
        attempts.append(dict(a=a,draws=draws,position=p,velocity=v,rejection=reason))
        if reason is None:
            world=deepcopy(template)
            world["targets"][1]=target
            return dict(status="ACCEPTED",world=world,attempts=attempts)
    return dict(status="EXHAUSTED",world=None,attempts=attempts)
