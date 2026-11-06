import copy
from pathlib import Path
import unittest

from scripts.run_a2_value2_locked import compare_before_action, compare_prefork_step, load_open, read


class DynamicForkTests(unittest.TestCase):
    def rows(self, tick, fork=False):
        opened = dict(policy_input=dict(tick=tick, belief=[1.,2.]),
                      choice=dict(actions=[0], rows=[.25,.5], exact_value="1/4"), evidence={})
        locked = copy.deepcopy(opened)
        locked["locked"] = dict(protection={"target":1} if fork else None,
                                selected=dict(actions=[1] if fork else [0],exact_value="1/8"))
        return opened, locked

    def test_early_late_and_no_fork(self):
        for fork in (60,100,None):
            result = None
            for tick in range(0,120,20):
                result = compare_before_action(*self.rows(tick,tick==fork),[],[],"R",tick)
                if result is not None:
                    break
            self.assertEqual(result["FIRST_FORK_TICK"] if result else None,fork)
            if result:
                self.assertEqual(result["OPEN_ACTION"],[0])
                self.assertEqual(result["LOCKED_ACTION"],[1])

    def test_fork_cannot_mask_scientific_differences(self):
        for change in ("belief","candidate","order","consumed"):
            a,b = self.rows(80,True)
            observed = []
            if change=="belief":
                b["policy_input"]["belief"][0] += .01
            elif change=="candidate":
                b["choice"]["rows"][0] += .01
            elif change=="order":
                b["choice"]["rows"].reverse()
            else:
                observed = [dict(consumed_tick=80)]
            with self.assertRaises(Exception):
                compare_before_action(a,b,[],observed,"R",80)

    def test_fixed_identity_paths(self):
        a = dict(fusion_records=[dict(context=dict(work_instance_id="A2_R"))])
        b = dict(fusion_records=[dict(context=dict(work_instance_id="A2_VALUE2_LOCKED_R"))])
        self.assertEqual(compare_prefork_step(a,b,"R",20),1)
        b["fusion_records"][0]["context"]["work_instance_id"]="A2_VALUE1_LOCKED_R"
        with self.assertRaisesRegex(ValueError,"work_instance_id"):
            compare_prefork_step(a,b,"R",20)

    def test_old_open_is_rejected_for_new_world(self):
        root = Path("runs/a2_switch_episode_001")
        if not root.is_dir():
            self.skipTest("Local historical evidence is unavailable")
        with self.assertRaisesRegex(Exception,"/world"):
            load_open(root,read(Path("configs/a2_value2_two_target_v1.json")),
                      read(Path("configs/a2_value2_public_announcements_v1.json")))
