from dataclasses import replace
from pursuit_v2 import observation_geometry as geometry
"""B: independent robot motion cache; joint timers and stopping remain candidate-specific."""
import numpy as np
from pursuit_v2.observation_geometry import offset as role_offset
from pursuit_v2.service import DT,TOL,ServiceState,ServiceRollout,canonical_team,advance_clock,tick
from .reference import benefit


class SharedEvaluator:
    def __init__(self,case):
        from .domain import require_angular
        require_angular(case)
        self.case=case
        self.components={}
        self.control_substeps=0
        self.requests=[]
        self.cache_hits=0
        self.scope=(case.identity,geometry.identity(case.obs.config))
        from .model import candidates
        self.specs={s.index:s for s in candidates(case)}

    def component(self,w,j,i,role):
        key=self.scope+(w,j,i,role)
        if key in self.components:
            self.cache_hits+=1
            return self.components[key]
        case=self.case; cfg=case.obs.config; path=case.path(w,j)
        first,last=tick(case.obs.time),tick(case.until)
        offset=role_offset(role,cfg)
        pos=case.obs.positions[i].copy()[None,:]
        positions=[pos[0].copy()]; valid=[]; commands=[]; squares=[]; speeds=[]; lengths=[]
        escape=path.escape_time(cfg.side)
        for n in range(first,last+1):
            at=n*DT
            valid.append(bool(np.linalg.norm(pos-path.position(at)-offset,axis=1)[0]<=geometry.radius(cfg)))
            if n==last:
                break
            lo,hi=n*DT,(n+1)*DT
            elapsed=max(0.,min(hi,escape)-lo)
            command=path.velocity_at(lo)+cfg.travel_gain*(path.position(lo)+offset-pos)
            speed=np.linalg.norm(command,axis=1)
            command*=np.minimum(1.,cfg.max_speed/np.maximum(speed,1e-15))[:,None]
            if escape<=lo+TOL:
                command[:]=0.; elapsed=0.
            else:
                self.control_substeps+=1
            positions.append((pos+command*elapsed)[0].copy())
            commands.append(command[0].copy()); squares.append((command**2)[0].copy())
            speeds.append(float(np.linalg.norm(command,axis=1)[0])); lengths.append(elapsed)
            pos+=command*elapsed
        result=dict(positions=np.array(positions),valid=np.array(valid),commands=np.array(commands),
                    squares=np.array(squares),speeds=np.array(speeds),lengths=np.array(lengths),
                    times=np.arange(first,last+1)*DT,escape=escape)
        self.components[key]=result
        return result

    def evaluate(self,specs):
        self.requests.append([s.index for s in specs])
        return {s.index:self.one(s) for s in specs}

    def one(self,spec):
        if self.specs.get(spec.index)!=spec: raise ValueError('Candidate identity mismatch')
        case=self.case; cfg=case.obs.config; rows=[]
        for w in range(len(case.worlds)):
            path=case.path(w,spec.target)
            parts=[self.component(w,spec.target,i,r) for i,r in zip(spec.robots,spec.roles)]
            positions=np.stack([p['positions'] for p in parts],axis=1)
            valid=np.all(np.stack([p['valid'] for p in parts],axis=1),axis=1)
            squares=np.ascontiguousarray(np.stack([p['squares'] for p in parts],axis=1))
            speeds=np.stack([p['speeds'] for p in parts],axis=1)
            team=canonical_team(zip(spec.robots,spec.roles))
            state=dict(case.obs.service_states)[spec.target]
            events=[]; frames=[]; effort=peak=0.; completion=escaped=None
            if state.team!=team:
                if state.progress>0:
                    events.append(dict(time=case.obs.time,reason='team_changed',progress_before=state.progress))
                state=replace(state,base=0.,intervals=0,team=team)
            escape=parts[0]['escape']
            reason='episode_end' if case.until>=cfg.end_time-TOL else 'horizon_truncated'
            if escape<=case.obs.time+TOL:
                escaped,reason=escape,'escaped'
            elif not valid[0] and state.progress>0:
                events.append(dict(time=case.obs.time,reason='observation_invalid',progress_before=state.progress))
                state=replace(state,base=0.,intervals=0,team=team)
            pos=positions[0].copy()

            def frame(at,ready,legal=True):
                frames.append(dict(time=at,positions=pos.tolist(),valid=bool(ready),
                                   progress=min(path.service_duration,state.progress),effort=effort,legal_check=legal))

            frame(case.obs.time,valid[0] and escaped is None)
            first,last=tick(case.obs.time),tick(case.until)
            for k in range(last-first):
                hi=(first+k+1)*DT
                if completion is not None or escaped is not None:
                    frame(hi,False); continue
                pos=positions[k+1].copy()
                effort+=float(np.sum(squares[k]))*float(parts[0]['lengths'][k])
                peak=max(peak,float(speeds[k].max()))
                if escape<=hi+TOL:
                    escaped,reason=escape,'escaped'
                    if escape<hi-TOL:
                        frame(escape,False,False)
                    frame(hi,False); continue
                state,done,more=advance_clock(state,path.service_duration,team,bool(valid[k] and valid[k+1]),hi)
                events.extend(more)
                if done:
                    completion,reason=hi,'completed'
                frame(hi,valid[k+1])
            result=ServiceRollout(pos,state,completion,escaped,effort,peak,frames,events,reason)
            rows.append((result,benefit(case,path,completion,effort)))
        return rows
