from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
import inspect
import os
import subprocess
import sys

from research.non_oracle.sw3_formal_adapter import ProductionAdapter
from research.non_oracle.sw3_formal_core import Coordinator,slots,TEST
from research.non_oracle.sw3_formal_physics import ProductionPhysics
from scripts.run_a2_prediction_sw3_dev import read


class ReleasePreparationTests(TestCase):
    def setUp(self):
        self.world=read("configs/a2_value2_two_target_v1.json")
        self.ann=read("configs/a2_value2_public_announcements_v1.json")

    def test_all_public_families_and_reserve(self):
        p=ProductionPhysics(self.world,self.ann)
        with patch("research.non_oracle.sw3_formal_physics.sample",side_effect=AssertionError("private draw")):
            normal=p.public_prechecks()
            self.assertEqual(tuple(normal),TEST)
            self.assertTrue(all(r["status"]=="PASS" and r["before_private_sampling"] for r in normal.values()))
            a=ProductionAdapter(self.world,self.ann,"unused",None,{})
            reserve=a.reserve_precheck()
            self.assertEqual(reserve["family_id"],7)
            self.assertTrue(all(reserve["checks"].values()))
            self.assertEqual(reserve["announcement"]["announcements"][1]["coarse_position"],[9.1,10.3])
            self.assertEqual(slots(normal,lambda:reserve)[0]["actual_family_id"],3)

    def test_shared_failure_is_not_replacement(self):
        world=read("configs/a2_value2_two_target_v1.json")
        world["positions_initial"]=[]
        with self.assertRaises(ValueError):
            ProductionPhysics(world,self.ann).public_prechecks()
        with patch.object(ProductionPhysics,"public_precheck",return_value=dict(status="BLOCKED")) as check:
            a=ProductionAdapter(self.world,self.ann,"unused",None,{})
            self.assertEqual(a.reserve_precheck()["status"],"BLOCKED")
            check.assert_called_once_with(7)

    def test_production_public_failure_classification(self):
        p=ProductionPhysics(self.world,self.ann)
        # Inject a recorded frozen-domain rejection without private sampling.
        with patch.object(p,"global_precheck"),patch.object(p,"public_precheck",
                side_effect=lambda n:dict(status="FAMILY_PRECHECK_FAILED",kind="MOTION_DOMAIN",basis="artificial" ) if n==3 else dict(status="PASS")):
            result=slots(p.public_prechecks(),lambda:dict(status="PASS"))
            self.assertEqual(result[0]["actual_family_id"],7)

    def test_cli_and_all_locks(self):
        r=subprocess.run([sys.executable,"-B","scripts/run_a2_prediction_sw3_formal.py",
                          "--mode","FORMAL_RUN"],capture_output=True)
        self.assertNotEqual(r.returncode,0)
        self.assertIn(b"not authorized",r.stderr+r.stdout)
        class Real:kind="PRODUCTION"
        with self.assertRaises(PermissionError):Coordinator("unused","FORMAL_RUN",Real())
        with self.assertRaises(PermissionError):Coordinator("unused","IMPLEMENTATION_TEST",Real())
        p=ProductionPhysics(self.world,self.ann)
        with patch.dict(os.environ,FORMAL_RUN="1",FORMAL_AUTHORIZED="true"):
            with patch("research.non_oracle.sw3_formal_physics.sample",side_effect=AssertionError):
                with self.assertRaises(PermissionError):p.prepare([],formal_authorized=True)
                with self.assertRaises(PermissionError):p.finish([],formal_authorized=True)

    def test_frozen_budget_binding(self):
        source=inspect.getsource(ProductionPhysics.prepare)
        self.assertIn('sum(cost["wls"] for _,cost in prefix)>61',source)
        self.assertIn('sample(self.world, "test"',source)
        self.assertNotIn("private_world(",source)
        self.assertEqual(8*(41+123+123),2296)
        self.assertEqual(32*61+32*41,3264)
