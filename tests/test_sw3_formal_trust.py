from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import json

from research.non_oracle.sw3_formal_core import seal,sha,write
from research.non_oracle.sw3_formal_trust import Trust
from research.non_oracle.sw3_formal_physics import ProductionPhysics


class TrustTests(TestCase):
    def test_coordinated_tamper_rejected(self):
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            root=Path(tmp)
            write(root/"raw.json",{"artificial":True})
            m=seal({"x":root/"raw.json"},["x"],root/"sealed")
            trust=Trust(root/"trusted","artificial","trusted-test","mock-sid")
            trust.fix(1,1,root/"sealed/MANIFEST.json",m)
            trust.verify(1)
            file=Path(m["x"]["path"])
            file.write_text("{}")
            m["x"]["sha256"]=sha(file)
            (root/"sealed/MANIFEST.json").write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,"Anchored manifest"):
                trust.verify(1)

    def test_missing_wrong_or_modified_anchor(self):
        with TemporaryDirectory(dir=Path("reports").resolve()) as tmp:
            root=Path(tmp);write(root/"raw.json",{})
            m=seal({"x":root/"raw.json"},["x"],root/"sealed")
            trust=Trust(root/"trusted","artificial","trusted-test","mock-sid")
            with self.assertRaises(ValueError):trust.fix(2,2,root/"sealed/MANIFEST.json",m)
            anchor=trust.fix(1,1,root/"sealed/MANIFEST.json",m)
            Path(anchor["receipt_path"]).write_text("{}")
            with self.assertRaisesRegex(ValueError,"Trusted receipt"):trust.verify(1)

    def test_bool_cannot_open_physics(self):
        physical=ProductionPhysics({}, {})
        with patch("research.non_oracle.sw3_formal_physics.sample",side_effect=AssertionError):
            with self.assertRaises(PermissionError):physical.prepare([],formal_authorized=True)
            with self.assertRaises(PermissionError):physical.finish([],formal_authorized=True)
