"""Evidence checks before service diagnostics enter the label seal."""
from copy import deepcopy
import json

from .sw3_c1_sealing import public_handoff


def sealed_diagnostics(record):
    from scripts.run_a2_prediction_sw3_dev import diagnose,encode_special
    prior,updated=record["prior_belief"],record["updated_belief"]
    d60,d80=record["D60"],record["D80"]
    def belief(view):
        return view["beliefs"][1] if 1 in view["beliefs"] else view["beliefs"]["1"]
    if (d60["tick"]!=60 or d80["tick"]!=80 or not prior or not updated
            or prior!=belief(d60) or updated!=belief(d80)
            or prior["target_id"]!=1 or updated["target_id"]!=1
            or public_handoff(d60)["public_sha256"]!=record["D60_public_sha256"]):
        raise ValueError("Belief provenance mismatch")
    consumed=record["consumed"]
    if ([r["measurement_tick"] for r in consumed]!=list(range(60,81))
            or any(r["target_id"]!=1 or r["consumed_tick"]!=80
                   or r["available_tick"]!=r["measurement_tick"] for r in consumed)):
        raise ValueError("Actual observation provenance mismatch")
    diagnostics=diagnose(record["first"],record["second"],consumed,prior,updated)
    return json.loads(json.dumps(diagnostics,default=encode_special,allow_nan=False))
