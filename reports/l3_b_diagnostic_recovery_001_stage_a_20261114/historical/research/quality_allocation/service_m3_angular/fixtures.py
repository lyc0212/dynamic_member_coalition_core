"""Hand-specified before evaluation. No seeds, tuning or favorable-input search."""
from dataclasses import replace
import math
import numpy as np
from pursuit_v2.config import Config
from pursuit_v2.types import Target, Observation, Assignment, IDLE
from pursuit_v2.service import initial_state
from .model import Case


def make(name,robots,rows,positions,start=0.,until=3.,rates=(0.,),states=(),old=None,expectation='audit',speed_max=.8):
    cfg=Config(robots=robots,task_count=len(rows),side=20.,max_stages=2,
               capture_mode='stepwise_service',geometry_mode='angular_standoff_v1',target_speed_max=speed_max)
    worlds=tuple(tuple(Target(j,0.,xy,velocity,q,weight,4.,
                             arc_rates=((start if start else 1.,rate),(6.,0.)),service_duration=h)
                       for j,(xy,velocity,q,weight,h) in enumerate(rows)) for rate in rates)
    public=tuple(t.observed(start) for t in worlds[0])
    state_rows=tuple(states) if states else tuple((t.id,initial_state(cfg)) for t in public)
    obs=Observation(cfg,int(start//3),np.array(positions,float),public,
                    tuple(old) if old else (IDLE,)*robots,(),(),start,state_rows)
    return Case(name,obs,until,worlds,expectation)


def frozen_cases():
    s=initial_state(Config(capture_mode='stepwise_service',geometry_mode='angular_standoff_v1'))
    tri=((0,'tri_0'),(1,'tri_120'),(2,'tri_240'))
    d=.3*math.sqrt(3)
    return (
        make('skip_v1',4,[((5.,5.),(.4,0.),3,4.,2.),((10.,10.),(.4,0.),2,1.,10.),
                          ((15.,15.),(.4,0.),1,1.,10.)],
             [[6.8,5.],[5.9,5.+d],[5.9,5.-d],[9.,8.]],start=3.,until=6.,
             states=((0,replace(s,base=1.85,team=tri)),(1,s),(2,s)),
             old=(Assignment(0,'tri_0'),Assignment(0,'tri_120'),Assignment(0,'tri_240'),IDLE),expectation='skip'),
        make('full_v1',3,[((5.,5.),(.4,0.),3,2.,.15)],[[6.,5.],[7.,5.],[8.,5.]],expectation='full'),
        make('mixed_history_v1',5,[((5.,5.),(.4,0.),3,3.,2.),((8.,8.),(.4,0.),2,2.,.3)],
             [[6.8,5.],[5.9,5.+d],[5.9,5.-d],[9.2+.6/2**.5,8.-.6/2**.5],[12.,10.]],
             start=3.,until=6.,rates=(0.,.03),
             states=((0,replace(s,base=1.5,team=tri)),
                     (1,replace(s,base=.1,team=((3,'dual_neg45'),(4,'dual_pos45'))))),
             old=(Assignment(0,'tri_0'),Assignment(0,'tri_120'),Assignment(0,'tri_240'),
                  Assignment(1,'dual_neg45'),Assignment(1,'dual_pos45'))),
        make('escape_edges_v1',3,[((19.927,5.),(1.,0.),3,1.,.15),
                                 ((19.85,5.),(1.,0.),2,1.,.15),((19.7,5.),(1.,0.),1,1.,.12)],
             [[20.527,5.],[19.627,5.+d],[19.627,5.-d]],rates=(0.,.01),speed_max=1.),
        make('prefix_v1',4,[((5.,5.),(.4,0.),3,3.,.4),((8.,8.),(.4,0.),1,2.,.2)],
             [[6.8,5.],[5.9,5.+d],[5.9,4.1],[9.8,8.]],start=3.,until=6.,rates=(0.,.03),
             states=((0,replace(s,base=.1,team=tri)),(1,s)),
             old=(Assignment(0,'tri_0'),Assignment(0,'tri_120'),Assignment(0,'tri_240'),Assignment(1,'solo_0'))),
    )


def boundary_cases():
    base=frozen_cases()[1]
    result=[]
    for h in (5e-11,.10000000005,.1000000002,.12):
        worlds=tuple(tuple(replace(t,service_duration=h) for t in world) for world in base.worlds)
        result.append(replace(base,name=f'boundary_H_{h}',worlds=worlds,
                              obs=replace(base.obs,targets=tuple(t.observed(base.obs.time) for t in worlds[0])),expectation='boundary'))
    return tuple(result)
