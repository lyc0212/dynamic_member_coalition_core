"""Deterministic SW3-A public-only hypothesis selection."""
from copy import deepcopy
from dataclasses import asdict
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
import math
from time import perf_counter, process_time

import numpy as np

from pursuit_v2.config import Config
from pursuit_v2.observation_geometry import offset, radius
from research.information_service_online import public
from .policy import command
from .shadow_feedback_prediction import TEAM, WorldHypothesis

VERSION = "SW3-PUBLIC-V1"
FIELDS = {"kind","tick","end_tick","config","positions","assignment","sensor_profiles",
          "targets","beliefs","histories","current_slots","first_policy_visible_ticks"}
ANN = {"id","announcement_tick","birth","weight","deadline","service_duration","required_robots",
       "coarse_position","velocity_prior","design_error_bound","motion_model","speed_limit"}
BELIEF = {"target_id","estimate_tick","available_tick","position_estimate","velocity_estimate",
          "velocity_source","last_observation_tick","source","status","diagnostics"}


def digest(value):
    def normalize(x):
        if type(x) is float:
            if not math.isfinite(x):
                raise ValueError("Nonfinite public number")
            return (x if x else 0.).hex()
        if type(x) is dict:
            return {str(k):normalize(v) for k,v in x.items()}
        if isinstance(x,(list,tuple)):
            return [normalize(v) for v in x]
        if x is None or type(x) in (int,str,bool):
            return x
        raise TypeError("Unsupported public value")
    return hashlib.sha256(json.dumps(normalize(value),sort_keys=True,ensure_ascii=False,
        separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest()


def public_input(view):
    if set(view)!=FIELDS or view["kind"]!="A2_POLICY_INPUT" or view["tick"]!=60 or view["end_tick"]!=120:
        raise ValueError("Expected closed D60 A2 public view")
    v = deepcopy(view)
    cfg = Config(**v["config"])
    if (set(v["config"])!=set(cfg.to_dict()) or
            (cfg.robots,cfg.task_count,cfg.step_dt,cfg.geometry_mode,cfg.observation_radius,cfg.observation_tolerance)
            !=(3,2,.05,"angular_standoff_v1",.6,.15)):
        raise ValueError("Unsupported scientific configuration")
    if (len(v["positions"])!=3 or len(v["assignment"])!=3 or len(v["sensor_profiles"])!=3):
        raise ValueError("Expected three public robots")
    for i,(p,a,s) in enumerate(zip(v["positions"],v["assignment"],v["sensor_profiles"])):
        public.validate_schema(p,"Vector2")
        public.validate_schema(a,"Assignment")
        public.validate_schema(s,"SensorProfile")
        if s["sensor_id"]!=f"U{i}" or s["observed_tick"]!=60:
            raise ValueError("Invalid sensor cut")
    if v["assignment"][2]["target"] is not None or any(a["target"]==1 for a in v["assignment"]):
        raise ValueError("Expected idle U2 and unassigned T1")
    if [t["id"] for t in v["targets"]]!=[0,1] or any(set(t)!=ANN for t in v["targets"]):
        raise ValueError("Unexpected public announcements")
    for t in v["targets"]:
        for k in ("coarse_position","velocity_prior"):
            public.validate_schema(t[k],"Vector2")
        if any(type(t[k]) not in (int,float) or not math.isfinite(t[k]) or t[k]<=0
               for k in ("weight","service_duration","design_error_bound","speed_limit")):
            raise ValueError("Invalid announcement magnitude")
        if (t["required_robots"]!=2 or type(t["announcement_tick"]) is not int
                or not all(type(t[k]) in (int,float) and math.isfinite(t[k]) for k in ("birth","deadline"))
                or t["birth"]!=t["announcement_tick"]*.05 or t["deadline"]<t["birth"]):
            raise ValueError("Invalid announcement task")
    t = v["targets"][1]
    if (t["announcement_tick"],t["motion_model"],list(t["velocity_prior"]),t["service_duration"])!=(60,"constant_velocity",[0,0],1.05):
        raise ValueError("T1 must be the registered fresh q2 task with zero velocity prior")
    for field in ("beliefs","first_policy_visible_ticks"):
        raw = v[field]
        if set(raw) not in ({0,1},{"0","1"}):
            raise ValueError("Expected public maps keyed by T0/T1")
        v[field] = {int(k):x for k,x in raw.items()}
    if v["first_policy_visible_ticks"]!={0:0,1:60}:
        raise ValueError("Unexpected first visibility")
    for j,b in v["beliefs"].items():
        if set(b)!=BELIEF or b["target_id"]!=j:
            raise ValueError("Invalid belief fields")
        public.validate_schema(b["position_estimate"],"Vector2")
        public.validate_schema(b["velocity_estimate"],"Vector2")
    b = v["beliefs"][1]
    if (b["status"],b["source"],b["velocity_source"],b["estimate_tick"],b["available_tick"],
        b["last_observation_tick"],b["diagnostics"],b["position_estimate"],b["velocity_estimate"])!=(
        "PRIOR_ONLY","PUBLIC_PRIOR","PUBLIC_PRIOR",60,60,None,None,t["coarse_position"],t["velocity_prior"]):
        raise ValueError("T1 belief must match its public birth announcement")
    if [h["target_id"] for h in v["histories"]]!=[0,1]:
        raise ValueError("Invalid task histories")
    _,assigned = public._validate_actions(v,v["assignment"])
    for h,target in zip(v["histories"],v["targets"]):
        public.validate_schema(h,"TaskHistory")
        public._history(h,target,v,assigned[target["id"]])
    h = v["histories"][1]
    if h["birth_tick"]!=60 or h["cutoff_tick"]!=60 or h["segments"] or h["active_segment_id"] is not None:
        raise ValueError("Expected a fresh T1 history")
    for s in v["current_slots"]:
        public.validate_schema(s,"MeasurementSlot")
        if s["state"]!="UNQUERIED":
            public._require_digest(s,"slot_digest")
        if s["slot_key"]["target_id"]==1 and s["state"]!="UNQUERIED":
            raise ValueError("Unexpected T1 measurement before FIRST_ASSIGNMENT")
    if [s["slot_key"] for s in v["current_slots"]]!=[
        dict(target_id=j,robot_id=i,tick=60) for j in (0,1) for i in range(3)]:
        raise ValueError("Invalid public slot order/coverage")
    return v,cfg,t


def public_fingerprint(view):
    def project(x):
        if isinstance(x,dict):
            ignored = {"diagnostics","slot_digest","history_digest","segment_history_digest","endpoint_digest"}
            return {k:project(v) for k,v in x.items() if k not in ignored}
        if isinstance(x,list):
            return [project(v) for v in x]
        return x
    return digest(dict(version=VERSION,team=TEAM,view=project(view)))


def legal(h,cfg,t):
    return (len(h.position)==len(h.velocity)==2 and all(math.isfinite(x) for x in (*h.position,*h.velocity))
            and h.velocity[0]>=0 and math.hypot(*h.velocity)<=t["speed_limit"]
            and all(0<=x<cfg.side and 0<=y<=cfg.side for x,y in (
                h.position,tuple(p+2*v for p,v in zip(h.position,h.velocity)))))


def library(t,cfg):
    x,y = t["coarse_position"]
    r,s = t["design_error_bound"]/2,t["speed_limit"]/2
    d = s/math.sqrt(2)
    ps = (("N",(x,y)),("X+",(x+r,y)),("X−",(x-r,y)),("Y+",(x,y+r)),("Y−",(x,y-r)))
    vs = (("N",(0.,0.)),("E",(s,0.)),("NE",(d,d)),("SE",(d,-d)),("北",(0.,s)),("南",(0.,-s)))
    all_rows = [WorldHypothesis(f"{p}/{v}",xy,uv) for p,xy in ps for v,uv in vs]
    accepted,seen = [],set()
    for h in all_rows:
        key = (h.position,h.velocity)
        if legal(h,cfg,t) and key not in seen:
            accepted.append(h)
            seen.add(key)
    if len(accepted)<3 or accepted[0]!=all_rows[0]:
        raise ValueError("BLOCKED: invalid nominal or fewer than three distinct legal hypotheses")
    return all_rows,accepted


def margin(positions, point, cfg):
    roles = np.array([offset(role,cfg) for _,role in TEAM])
    return float(radius(cfg)-np.max(np.linalg.norm(np.asarray(positions)-np.asarray(point)-roles,axis=1)))


def score(margins):
    longest = streak = 0
    for a,b in zip(margins,margins[1:]):
        streak = streak+1 if a>=0 and b>=0 else 0
        longest = max(longest,streak)
    best = max(min(margins[i:i+22]) for i in range(20))
    with localcontext() as ctx:
        ctx.prec = 80
        bucket = int((Decimal.from_float(best)*10**12).to_integral_value(rounding=ROUND_HALF_EVEN))
    return longest,bucket,best


def pick_m1(accepted):
    chosen = [accepted[0]]
    for label in ("X+/E","Y−/NE"):
        remaining = [h for h in accepted if h not in chosen]
        chosen.append(next((h for h in remaining if h.label==label),remaining[0]))
    return chosen


def pick_m2(accepted, scores):
    others = accepted[1:]
    high = max(others,key=lambda h:scores[h.label][:2])
    low = min((h for h in others if h!=high),key=lambda h:scores[h.label][:2])
    return [accepted[0],high,low]


def select_hypotheses(view, method):
    if method not in ("M0","M1","M2"):
        raise ValueError("Unknown SW3 method")
    wall,cpu = perf_counter(),process_time()
    v,cfg,t = public_input(view)
    public_sha = public_fingerprint(v)
    all_rows,accepted = library(t,cfg)
    validation = dict(wall=perf_counter()-wall,cpu=process_time()-cpu)
    wall,cpu = perf_counter(),process_time()
    scores = {}
    if method=="M2":
        positions = np.array(v["positions"][:2])
        path = [positions]
        for tick in range(60,100):
            positions = positions + .05*command(v["beliefs"][1],tick,positions,[r for _,r in TEAM],cfg)
            path.append(positions)
        for h in accepted:
            scores[h.label] = score([margin(p,[x+u*(tick*.05-3.) for x,u in zip(h.position,h.velocity)],cfg)
                                     for tick,p in enumerate(path,60)])
        chosen = pick_m2(accepted,scores)
    elif method=="M1":
        chosen = pick_m1(accepted)
    else:
        chosen = accepted[:1]
    screening = dict(wall=perf_counter()-wall,cpu=process_time()-cpu)
    return dict(version=VERSION,version_sha256=digest(VERSION),public_sha256=public_sha,
                library_sha256=digest([asdict(h) for h in accepted]),selection_sha256=digest([asdict(h) for h in chosen]),
                all_candidates=all_rows,legal_candidates=accepted,selected=chosen,scores=scores,
                candidate_scores=len(scores),geometry_endpoints=41*len(scores),screening_wls=0,
                validation_timing=validation,screening_timing=screening)
