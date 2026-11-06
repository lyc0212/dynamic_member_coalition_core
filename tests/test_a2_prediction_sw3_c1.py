from copy import deepcopy
import json
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from research.non_oracle.sw3_c1_actual_labels import extract_label
from research.non_oracle.sw3_c1_manifest import CENTERS, announcements_for, family_digest, manifest
from research.non_oracle.sw3_c1_private_worlds import draw_component, hash_unit, private_world, reject_motion
from research.non_oracle.sw3_c1_sealing import (
    archive_private, association_receipt, compare_family, public_handoff, seal_prediction, verify_prediction_seal,
)


def read(path):
    return json.loads(Path(path).read_bytes())


class EncodingTests(TestCase):
    def test_golden_vectors_and_groups(self):
        self.assertEqual(CENTERS,((8.7,10.05),(8.7,10.3),(8.7,10.55),
            (8.9,10.05),(8.9,10.3),(8.9,10.55),(9.1,10.05),(9.1,10.3),(9.1,10.55),
            (9.3,10.05),(9.3,10.3),(9.3,10.55)))
        self.assertEqual(family_digest(0),"a56bf20f600f6a890acce6e35180ee1fa465989b2ec8e5c5c3b96303d0690d36")
        self.assertEqual(family_digest(11),"08298c60b615ddea5b9964e2a308ba16beb5b3e1db78cbf0488b34c0d7737efb")
        self.assertEqual(draw_component("dev",11,0,0,0),
            ("4efc0f8c936d0a372f14745cff5d57aa6d687d0a602ba825230a314a88325268",1389511993538256,.3085336416437948))
        self.assertEqual(hash_unit("SW3-V1|world|test|99|7|5|3"),
            ("cd66ab9ddec2921b45f6a51f02863b64455f99d92cd4735e55302a2a9e6eef37",3613453593734185,.8023478756356418))
        rows=manifest()
        self.assertEqual([r["n"] for r in rows],[11,6,4,3,10,5,1,8,2,0,9,7])
        self.assertEqual([r["split"] for r in rows],["dev"]*3+["test"]*8+["reserve"])
        with patch("research.non_oracle.sw3_c1_private_worlds.hash_unit",return_value=(None,0,0.)) as h:
            draw_component("test",7,0,0,0,replaces=3)
            h.assert_called_once_with("SW3-V1|world|test|7|0|0|0")

    def test_illegal_indices_and_split(self):
        for args in (("test",99,7,5,3),("DEV",11,0,0,0),("dev",3,0,0,0),
                     ("dev",7,0,0,0),("dev",11,4,0,0),("dev",11,0,32,0),("dev",11,0,0,4)):
            with self.subTest(args=args),self.assertRaises(ValueError):
                draw_component(*args)
        self.assertEqual(draw_component("dev",11,0,0,0),draw_component("dev",11,0,0,0))

    def test_motion_rules_and_mock_exhaustion(self):
        self.assertEqual(reject_motion((9.,10.),(-.1,0.),20.,set()),"VELOCITY_DOMAIN")
        self.assertEqual(reject_motion((19.9,10.),(.1,0.),20.,set()),"POSITION_DOMAIN_OR_ESCAPE")
        self.assertEqual(reject_motion((9.,10.),(0.,0.),20.,{((9.,10.),(0.,0.))}),"DUPLICATE")
        template=read("configs/a2_value2_two_target_v1.json")
        with (patch("research.non_oracle.sw3_c1_private_worlds.draw_component",return_value=("fixture",0,.5)), patch("research.non_oracle.sw3_c1_private_worlds.reject_motion",return_value="DUPLICATE")):
            result=private_world(template,"dev",11,0,[])
        self.assertEqual(result["status"],"EXHAUSTED")
        self.assertEqual(len(result["attempts"]),32)
        ann=read("configs/a2_value2_public_announcements_v1.json")
        self.assertEqual(announcements_for(ann,0)["announcements"][1]["coarse_position"],[8.7,10.05])
        ann["announcements"][1]["velocity_prior"]=[.1,0.]
        with self.assertRaises(ValueError):
            announcements_for(ann,0)


class IsolationAndLabelTests(TestCase):
    def test_mock_four_public_views_and_seals(self):
        v=read("runs/a2_value2_open_001/R_D60.json")["policy_input"]
        views=[deepcopy(v) for _ in range(4)]
        handoff=compare_family(views)
        views[-1]["positions"][0][0]+=.1
        with self.assertRaisesRegex(ValueError,"/positions/0/0"):
            compare_family(views)
        forged=deepcopy(v)
        forged["beliefs"]["0"]["diagnostics"]={"world_id":"private"}
        with self.assertRaisesRegex(ValueError,"/beliefs/0/diagnostics/world_id"):
            public_handoff(forged)
        summary=dict(predicted_completion_status_set=[True],predicted_completion_ticks=[97],
                     completion_time_envelope=[97,97],noncompletion_possible=False)
        sealed=seal_prediction(v,"M0",summary,sequence=0)
        self.assertEqual(verify_prediction_seal(v,sealed),handoff["public_sha256"])
        private=archive_private({"fixture":True},{"source":"ACTUAL"})
        self.assertEqual(association_receipt(v,sealed,private,sequence=1)["sequence"],1)
        with self.assertRaises(ValueError):
            association_receipt(v,sealed,private,sequence=0)
        sealed["body"]["summary"]["predicted_completion_ticks"]=[98]
        with self.assertRaises(ValueError):
            verify_prediction_seal(v,sealed)

    def test_constructed_horizon_boundary_and_invalid_label(self):
        at=dict(event_tick=100,time_seconds=5.)
        event=dict(target_id=1,kind="COMPLETED",at=at,event_index=3)
        step=dict(status="COMMITTED",end_tick=100,events=[event])
        state=dict(tick=100,statuses=["active","completed"],events=[event],assignment=[{"target":None}]*3,
                   archives={"1":dict(terminal_status="completed",terminal_at=at,closing_event_index=3,released_robots=[0,1])})
        self.assertEqual(extract_label(step,state)["completion_tick"],100)
        active=dict(state,statuses=["active","active"],archives={},events=[])
        self.assertFalse(extract_label(dict(step,events=[]),active)["completed_by_H"])
        with self.assertRaises(ValueError):
            extract_label(step,dict(active,statuses=["active","escaped"]))
        with self.assertRaises(ValueError):
            extract_label(dict(step,status="FAILED"),active)
