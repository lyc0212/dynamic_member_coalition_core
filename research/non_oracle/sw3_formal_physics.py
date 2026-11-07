"""Production physics binding. Entry remains closed in this implementation release."""
from copy import deepcopy

from .environment import StaggeredEnvironment
from .sw3_physical_admissibility_v1 import sample, construct
from .sw3_c1_manifest import announcements_for
from .sw3_c1_sealing import compare_family,public_handoff
from .sw3_c1_actual_labels import extract_label
from scripts.run_a1 import Sensing
from scripts.run_a2_prediction_sw3_dev import commit
from hashlib import sha256
import json
import math


def require_formal_release():
    from research.non_oracle.sw3_release_scope import check_scope
    check_scope()


class ProductionPhysics:
    def __init__(self, world, announcements):
        self.world, self.announcements = world, announcements
        self.admission_records = []

    def global_precheck(self):
        construct(self.world)

    def public_prechecks(self):
        from .sw3_formal_core import TEST
        self.global_precheck()
        return {n:self.public_precheck(n) for n in TEST}

    def public_precheck(self,n):
        from .sw3_c1_manifest import CENTERS
        announcement=announcements_for(self.announcements,n)
        target=announcement["announcements"][1]
        checks=dict(task_id=target["id"]==1,
                      birth_cut=target["announcement_tick"]==60,
                      prior=target["velocity_prior"]==[0.,0.],
                      motion=target["motion_model"]=="constant_velocity",
                      error_bound=target["design_error_bound"]==.5,
                      speed_bound=target["speed_limit"]==.8,
                      center_binding=target["coarse_position"]==list(CENTERS[n]))
        if not all(checks.values()):
            raise ValueError("Frozen family announcement contract failed")
        center=target["coarse_position"]
        if len(center)!=2 or any(type(x) not in (int,float) or not math.isfinite(x) for x in center):
            raise ValueError("Malformed frozen public center")
        in_domain=all(0<=x<=self.world["config"]["side"] for x in center)
        checks["public_position_domain"]=in_domain
        return dict(status="PASS" if in_domain else "FAMILY_PRECHECK_FAILED",
            kind="MOTION_DOMAIN",family_id=n,before_private_sampling=not self.admission_records,
            announcement=announcement,checks=checks,
            basis="frozen announcements_for contract and common Environment constructor",
            sha256=sha256(json.dumps(announcement,sort_keys=True).encode()).hexdigest())

    def prepare(self, identities, *, formal_authorized=False):
        require_formal_release()
        paused, public = [], {}
        for identity in identities:
            n, previous = identity["actual_family_id"], []
            announcements = announcements_for(self.announcements,n)
            views = []
            for w in range(4):
                draw = sample(self.world, "test", n, w, previous,
                              replaces=identity["replaces_family_id"])
                self.admission_records.append(dict(identity=deepcopy(identity),world=w,draw=draw))
                if draw["status"] != "ACCEPTED":
                    raise ValueError("EXHAUSTED")
                previous.append(draw["world"])
                env = StaggeredEnvironment(draw["world"],Sensing(),f"SW3_FORMAL_{n}_{w}",
                                           announcements["announcements"])
                prefix = []
                for tick in (0,20,40):
                    view = env.prepare_decision()
                    if [t["id"] for t in view["targets"]] != [0] or 1 in view["beliefs"]:
                        raise ValueError("Premature T1 visibility")
                    prefix.append(commit(env,tick,0))
                if sum(cost["wls"] for _,cost in prefix)>61:
                    raise ValueError("T0 prefix ACTUAL WLS budget exceeded")
                view = env.prepare_decision()
                prior=deepcopy(view["beliefs"][1])
                public_cut=public_handoff(view)["public_sha256"]
                views.append(view)
                paused.append(dict(identity=deepcopy(identity),world_number=w,draw=draw,
                    env=env,view=deepcopy(view),prior_belief=prior,public_sha256=public_cut,
                    environment_object_id=id(env),checkpoint=env.observe_public()["checkpoint_id"],prefix=prefix))
            public[identity["evaluation_slot"]] = compare_family(views)
        return public, paused

    def verify_pauses(self, paused):
        for item in paused:
            env=item["env"]
            if (env.tick!=60 or env.decision_tick!=60 or
                    env.observe_public()["checkpoint_id"]!=item["checkpoint"]
                    or id(env)!=item["environment_object_id"]
                    or public_handoff(item["view"])["public_sha256"]!=item["public_sha256"]
                    or item["view"]["beliefs"][1]!=item["prior_belief"]):
                raise ValueError("D60 identity lost")

    def finish(self, paused, *, formal_authorized=False):
        require_formal_release()
        self.verify_pauses(paused)
        records=[]
        for item in paused:
            env=item["env"]
            first,c60=commit(env,60,1)
            d80=env.prepare_decision()
            updated=deepcopy(d80["beliefs"][1])
            consumed=deepcopy([r for r in env.beliefs.consumed if r["target_id"]==1])
            ticks=[r["measurement_tick"] for r in consumed]
            if ticks!=list(range(60,81)) or any(
                    r["consumed_tick"]!=80 or r["available_tick"]!=r["measurement_tick"] for r in consumed):
                raise ValueError("Unexpected actual consumption")
            second,c80=commit(env,80,1)
            changes=[r for r in second["action_commit"]["transitions"] if r["target_id"]==1]
            if len(changes)!=1 or changes[0]["kind"]!="KEEP":
                raise ValueError("Expected KEEP")
            if (second["frames"][0]["progress"]["1"]!=first["frames"][-1]["progress"]["1"] or
                    second["frames"][0]["actual_endpoints"]["1"]!=first["frames"][-1]["actual_endpoints"]["1"]):
                raise ValueError("KEEP left endpoint changed")
            if any(r["start_tick"]!=81 for r in second["fusion_records"]):
                raise ValueError("KEEP fusion restart mismatch")
            if c60["wls"]+c80["wls"]>41:
                raise ValueError("Actual WLS budget exceeded")
            label=extract_label(second,env.private_snapshot()["state"])
            records.append(dict(identity=item["identity"],world_number=item["world_number"],
                                first=first,second=second,consumed=consumed,label=label,
                                prior_belief=deepcopy(item["prior_belief"]),updated_belief=updated,
                                D60=deepcopy(item["view"]),D60_checkpoint=item["checkpoint"],
                                environment_object_id=id(env),D60_public_sha256=item["public_sha256"],
                                costs=[c60,c80],D80=deepcopy(d80)))
        return records
