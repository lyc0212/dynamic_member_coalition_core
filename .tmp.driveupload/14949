"""Compare SW1 to saved records, then time only the 20-step window."""
import hashlib
import json
from pathlib import Path
import platform
from statistics import median
from time import perf_counter, process_time

import numpy as np
import scipy

from research.non_oracle.policy import evaluate
from research.non_oracle.shadow_service_prediction import Hypothesis, predict_windows
from test_a2_prediction_shadow import ShadowTests, compare_frames

OUT = Path(__file__).parent


def save(name, data):
    (OUT/(name+".json")).write_text(json.dumps(data,indent=2),encoding="utf-8")


def timed(fn):
    rows = []
    for _ in range(3):
        cpu,wall = process_time(),perf_counter()
        fn()
        rows.append(dict(cpu=process_time()-cpu,wall=perf_counter()-wall))
    return dict(samples=rows,median={k:median(row[k] for row in rows) for k in rows[0]})


def main():
    ShadowTests.setUpClass()
    test = ShadowTests()
    for method in (test.test_a_nominal,test.test_b_value1,test.test_c_value2,
                   test.test_d_shared_control_is_exact_and_view_unchanged):
        method()
    view, key = test.view,test.key
    diagnostics = predict_windows(view,key,test.hypotheses)
    save("ENDPOINTS",dict(zip(("nominal","VALUE1_ORACLE_DIAGNOSTIC","VALUE2_ORACLE_DIAGNOSTIC"),diagnostics)))
    task = next(t for t in view["targets"] if t["id"]==key["target"])
    p = tuple(task["coarse_position"])
    v = tuple(task["velocity_prior"])
    radius = task["design_error_bound"]/2
    speed = task["speed_limit"]/2
    # Axis probes chosen from the public design magnitudes alone.
    probes = [Hypothesis(p,v)]
    for axis in range(2):
        for sign in (-1,1):
            probes.append(Hypothesis(tuple(x+(sign*radius if i==axis else 0) for i,x in enumerate(p)),v))
    probes.append(Hypothesis(p,(v[0]+speed,v[1])))
    results = predict_windows(view,key,probes)
    save("SENSITIVITY",dict(classification="DESIGN_SENSITIVITY",rule="nominal, +/- half design radius along each axis, eastward half speed limit",
        hypotheses=[dict(position=h.position,velocity=h.velocity,result=r) for h,r in zip(probes,results)]))
    assert len({r["longest_intervals"] for r in results})>1
    baseline_view = dict(view,end_tick=80)
    native = evaluate(baseline_view,key)
    compare_frames(diagnostics[0]["frames"][1:],native["frames"],actual=False)
    modes = dict(
        native_20_step=lambda:evaluate(baseline_view,key),
        shadow_nominal=lambda:predict_windows(view,key,probes[:1]),
        shadow_single_offset=lambda:predict_windows(view,key,probes[-1:]),
        shadow_six_shared=lambda:predict_windows(view,key,probes),
        shadow_six_unshared=lambda:predict_windows(view,key,probes,share_control=False))
    save("TIMING",dict(repetitions=3,unit="seconds",platform=platform.platform(),
                      processor=platform.processor(),python=platform.python_version(),numpy=np.__version__,
                      scipy=scipy.__version__,measurements={name:timed(fn) for name,fn in modes.items()}))
    root = Path("reports/a2_factorial_preflight_001")
    historical = json.loads((root/"HISTORICAL_PINS.json").read_bytes())
    def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert all(sha(p)==h for p,h in historical.items())
    paths = ["research/non_oracle/shadow_service_prediction.py","tests/test_a2_prediction_shadow.py",str(Path(__file__))]
    save("ACCEPTANCE",dict(status="SHADOW_SW1_VALID",NOMINAL_REPRODUCED="PASS",
        VALUE1_PHYSICS_REPRODUCED="PASS",VALUE2_PHYSICS_REPRODUCED="PASS",
        INFORMATION_ISOLATION="PASS",CONTROL_TRAJECTORY_REUSE="PASS",RUNTIME_OVERHEAD_RECORDED="PASS",
        historical_pins_checked=len(historical),sha256={p:sha(p) for p in paths}))


if __name__=="__main__":
    main()
