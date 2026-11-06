"""Run only the registered SW3-A/B smoke and frozen SW2 references."""
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from test_a2_prediction_sw3_ab import compare_reference, public_view, read
from research.non_oracle.shadow_feedback_prediction import WorldHypothesis
from research.non_oracle.sw3_f1_prediction import predict_method

OUT = Path(__file__).parent


def save(name, data):
    (OUT/(name+".json")).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")


def main():
    pins = read(OUT/"SOURCE_PINS.json")["pins"]
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in pins.items())
    view = public_view()
    scenarios = [WorldHypothesis("N/N",(9.,10.3),(0.,0.))]
    for i,root in enumerate(("a2_switch_episode_001","a2_value2_open_001"),1):
        target = read(Path("runs")/root/"WORLD_INPUT.json")["targets"][1]
        scenarios.append(WorldHypothesis(f"VALUE{i}_ORACLE_DIAGNOSTIC",
                         tuple(target["position_at_birth"]),tuple(target["velocity"]),True))
    eq,results,costs = {},{},{}
    for h,wanted in zip(scenarios,(97,None,95),strict=True):
        try:
            result,check=compare_reference(view,h)
            assert result["Y_H"]["completion_tick"]==wanted
            assert result["progress"]==(0. if wanted is None else 1.05)
        except Exception as exc:
            save("FIRST_DIVERGENCE",dict(hypothesis=h.label,error=repr(exc)))
            raise
        eq[h.label] = check | dict(Y_H=result["Y_H"],released=result["released"],progress=result["progress"])
        costs[h.label]=result["cost"] | dict(sw2_calls=check["sw2_calls"])
        results[h.label]=result
    save("F1_SW2_EQUIVALENCE",eq)
    save("F1_ENDPOINTS",results)
    selections,smoke = {},{}
    for method in ("M0","M1","M2"):
        r=predict_method(view,method)
        pred,sel=r["prediction"],r["selection"]
        assert pred["cost"]["wls"]<=41*len(sel["selected"])
        selections[method]={k:[asdict(h) for h in v] if k in ("all_candidates","legal_candidates","selected") else v
                            for k,v in sel.items()}
        smoke[method]=dict(outputs={k:v for k,v in pred.items() if k not in ("results","cost")},
                           high_fidelity_runs=len(pred["results"]),cost=pred["cost"],
                           validation=sel["validation_timing"],screening=sel["screening_timing"],
                           end_to_end=r["end_to_end"],geometry_endpoints=sel["geometry_endpoints"])
    save("HYPOTHESIS_SELECTION_TESTS",selections)
    save("WLS_AND_TIMING",dict(references=costs,smoke=smoke))
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in pins.items())


if __name__=="__main__":
    main()
