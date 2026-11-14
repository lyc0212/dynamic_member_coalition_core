from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from scripts import run_a2_prediction_sw3_dev as dev


class DevGateTests(TestCase):
    def setUp(self):
        self.view=dev.read("runs/a2_value2_open_001/R_D60.json")["policy_input"]

    def test_unapproved_families_and_private_input(self):
        for n in (3,7,10,5,1,8,2,0,9,True):
            with self.assertRaises(ValueError):
                dev.require_family(n)
        for forbidden in ({"position_now":[9,10]}, {"checkpoint_id":"private"}):
            with self.assertRaises(ValueError):
                dev.public_handoff(self.view|forbidden)

    def test_preparation_only_freezes_once_at_d60(self):
        prepared=[]
        view=self.view
        class FakeEnvironment:
            def __init__(self,*args):
                self.tick=0
                self.freezes=[]
                prepared.append(self)
            def prepare_decision(self):
                self.freezes.append(self.tick)
                if self.tick==60:
                    return deepcopy(view)
                return dict(targets=[{"id":0}],beliefs={0:{}})
            @property
            def decision_tick(self):
                return self.freezes[-1]
            def observe_public(self):
                return {"checkpoint_id":str(self.tick)}
        def commit(env,tick,target):
            self.assertLess(tick,60)
            self.assertEqual(target,0)
            env.tick+=20
            return {"fusion_records":[]},{"wls":0}
        with (TemporaryDirectory(dir=dev.ROOT.parent.resolve()) as tmp,
              patch.object(dev,"StaggeredEnvironment",FakeEnvironment),
              patch.object(dev,"private_world",return_value={"status":"ACCEPTED","world":{}}),
              patch.object(dev,"announcements_for",return_value={"announcements":[]}),
              patch.object(dev,"commit",side_effect=commit)):
            dev.prepare_family(11,Path(tmp),{}, {})
        self.assertEqual(len(prepared),4)
        for env in prepared:
            self.assertEqual(env.freezes,[0,20,40,60])
            self.assertEqual(env.tick,60)

    def test_mismatch_stops_before_prediction_and_labels(self):
        wrong=deepcopy(self.view)
        wrong["positions"][0][0]+=.1
        p=[dict(env=SimpleNamespace(tick=60),view=x) for x in (self.view,self.view,self.view,wrong)]
        with (TemporaryDirectory(dir=dev.ROOT.parent.resolve()) as tmp,patch.object(dev,"prepare_family",return_value=p),
              patch.object(dev,"predict_and_seal") as predict,patch.object(dev,"finish") as finish):
            with self.assertRaisesRegex(ValueError,"/positions/0/0"):
                dev.run_family(11,Path(tmp),{}, {})
            predict.assert_not_called()
            finish.assert_not_called()

    def test_full_seal_and_tampering(self):
        summary=dict(predicted_completion_status_set=[True],predicted_completion_ticks=[95],
                     completion_time_envelope=[95,95],noncompletion_possible=False)
        calls=[]
        def predict(view,method):
            calls.append(method)
            k=1 if method=="M0" else 3
            return dict(method=method,selection=dict(public_sha256=dev.public_handoff(view)["public_sha256"],
                selected=list(range(k)),geometry_endpoints=0,screening_wls=0),
                prediction=summary|dict(results=[{}]*k,cost=dict(wls=0)))
        with TemporaryDirectory(dir=dev.ROOT.parent.resolve()) as tmp:
            folder=Path(tmp)
            dev.save(folder/"D60.json",dev.public_handoff(self.view))
            with patch.object(dev,"commit") as commit:
                with self.assertRaises(FileNotFoundError):
                    dev.finish({},folder,self.view)
                commit.assert_not_called()
            seals=dev.predict_and_seal(folder,self.view,{},predict=predict)
            self.assertEqual(calls,list(dev.METHODS))
            self.assertEqual(list(seals),calls)
            with (folder/"M2_prediction.json").open("ab") as stream:
                stream.write(b" ")
            with patch.object(dev,"commit") as commit:
                with self.assertRaisesRegex(ValueError,"content changed"):
                    dev.finish({},folder,self.view)
                commit.assert_not_called()


