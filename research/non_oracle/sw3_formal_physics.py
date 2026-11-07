"""Production physics binding. Entry remains closed in this implementation release."""
from copy import deepcopy

from .environment import StaggeredEnvironment
from .sw3_physical_admissibility_v1 import sample, construct
from .sw3_c1_manifest import announcements_for
from .sw3_c1_sealing import compare_family
from .sw3_c1_actual_labels import extract_label
from scripts.run_a1 import Sensing
from scripts.run_a2_prediction_sw3_dev import commit


class ProductionPhysics:
    def __init__(self, world, announcements):
        self.world, self.announcements = world, announcements

    def global_precheck(self):
        construct(self.world)

    def public_prechecks(self):
        # No new family-specific physical thresholds are registered.
        from .sw3_formal_core import TEST
        return {n:dict(status="PASS", announcement=announcements_for(self.announcements,n))
                for n in TEST}

    def prepare(self, identities, *, formal_authorized=False):
        if not formal_authorized:
            raise PermissionError("Formal private generation is disabled")
        paused, public = [], {}
        for identity in identities:
            n, previous = identity["actual_family_id"], []
            announcements = announcements_for(self.announcements,n)
            views = []
            for w in range(4):
                draw = sample(self.world, "test", n, w, previous,
                              replaces=identity["replaces_family_id"])
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
                view = env.prepare_decision()
                views.append(view)
                paused.append(dict(identity=deepcopy(identity),world_number=w,draw=draw,
                    env=env,view=view,checkpoint=env.observe_public()["checkpoint_id"],prefix=prefix))
            public[identity["evaluation_slot"]] = compare_family(views)
        return public, paused

    def verify_pauses(self, paused):
        for item in paused:
            env=item["env"]
            if (env.tick!=60 or env.decision_tick!=60 or
                    env.observe_public()["checkpoint_id"]!=item["checkpoint"]):
                raise ValueError("D60 identity lost")

    def finish(self, paused, *, formal_authorized=False):
        if not formal_authorized:
            raise PermissionError("Formal physical continuation is disabled")
        self.verify_pauses(paused)
        records=[]
        for item in paused:
            env=item["env"]
            first,c60=commit(env,60,1)
            d80=env.prepare_decision()
            consumed=deepcopy([r for r in env.beliefs.consumed if r["target_id"]==1])
            ticks=[r["measurement_tick"] for r in consumed]
            if ticks!=list(range(60,81)) or any(r["consumed_tick"]!=80 for r in consumed):
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
                                costs=[c60,c80],D80=d80))
        return records
