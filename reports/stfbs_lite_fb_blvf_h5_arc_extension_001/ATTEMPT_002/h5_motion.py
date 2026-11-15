"""Frozen H5 analytic single arc; simulation and offline truth only."""
import math
DT=.05

def speed(world):return math.hypot(*world['motion'][0]['velocity'])

def point(world,j,tick):
    import numpy as np
    m=world['motion'][j];t=float(tick)*DT
    if j!=0:return np.asarray(m['position'])+np.asarray(m['velocity'])*((float(tick)-60)*DT)
    v=speed(world);p=m['position'];ts=75*DT;te=85*DT
    ps=(p[0]+v*(ts-3.),p[1])
    if t<=ts:return np.asarray((p[0]+v*(t-3.),p[1]))
    tau=min(t,te)-ts
    pe=(ps[0]+v*math.sin(tau),ps[1]+v*(1-math.cos(tau)))
    if t<te:return np.asarray(pe)
    return np.asarray((pe[0]+v*(t-te)*math.cos(.5),pe[1]+v*(t-te)*math.sin(.5)))

def velocity_at(world,j,tick):
    if j!=0:return list(world['motion'][j]['velocity'])
    angle=min(.5,max(0.,float(tick)*DT-75*DT));v=speed(world)
    return [v*math.cos(angle),v*math.sin(angle)]

def escape_time(world,j,start_seconds,side):
    p=point(world,j,start_seconds/DT)
    if p[0]>=side:return start_seconds
    if j!=0:
        vx=world['motion'][j]['velocity'][0]
        return math.inf if vx<=0 else start_seconds+(side-p[0])/vx
    v=speed(world);xs=point(world,0,75)[0];xe=point(world,0,85)[0]
    if side<=xs:t=75*DT+(side-xs)/v
    elif side<=xe:
        arg=(side-xs)/v
        if not -1<=arg<=1:raise ValueError('ARC_ESCAPE_ASIN_DOMAIN')
        t=75*DT+math.asin(arg)
    else:t=85*DT+(side-xe)/(v*math.cos(.5))
    tolerance=8*math.ulp(max(1.,abs(t),abs(start_seconds)))
    if t<start_seconds-tolerance:raise ValueError('ESCAPE_BEFORE_QUERY')
    return max(start_seconds,t)

def make_world(base,digest):
    import copy
    world=copy.deepcopy(base);v=speed(world)
    if world['motion'][0]['velocity'][0]<=0 or world['motion'][0]['velocity'][1]!=0:raise ValueError('H5_INITIAL_HEADING')
    physical=dict(name='H5_ARC_T0',base_world_digest=base['world_digest'],target_id=0,position_D60=list(world['motion'][0]['position']),original_velocity=list(world['motion'][0]['velocity']),speed=v,turn_start_tick=75,turn_end_tick=85,turn_duration_seconds=.5,turn_angle_radians=.5,turn_rate_radians_per_second=1.,dt=DT,start_tick=60,end_tick=120,position_rule='analytic circular arc, then tangent continuation',public_motion_model='constant_velocity',D60_public_digest=base['public_digest'])
    physical['physics_digest']=digest(physical)
    world.pop('world_digest');world.update(motion_rule='H5_ANALYTIC_ARC_T0_V1',h5_kind='MODEL',arc_spec=physical,perturbation=dict(base_world='H3',base_digest=base['world_digest'],physics_digest=physical['physics_digest']),provenance='SIMULATED',observation_origin='MODEL')
    world['world_digest']=digest(world)
    return world,physical
