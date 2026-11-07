"""Frozen SW3 metrics. This module never creates worlds or predictions."""
from statistics import mean

METHODS = ("M0", "M1", "M2")


def ratio(values):
    return dict(numerator=sum(values), denominator=len(values),
                value=mean(values) if values else None)


def validate_prediction(p):
    classes = p["predicted_completion_status_set"]
    if not classes or any(type(x) is not bool for x in classes) or classes not in (
            [False], [True], [False, True]):
        raise ValueError("Invalid completion classes")
    ticks = p["predicted_completion_ticks"]
    if ticks != sorted(set(ticks)) or any(type(t) is not int or not 60 <= t <= 100 for t in ticks):
        raise ValueError("Invalid completion ticks")
    envelope = [ticks[0], ticks[-1]] if ticks else None
    if p["completion_time_envelope"] != envelope or bool(ticks) != (True in classes):
        raise ValueError("Inconsistent completion envelope")
    if p["noncompletion_possible"] is not (False in classes):
        raise ValueError("Inconsistent noncompletion flag")


def evaluate(predictions, labels):
    if set(predictions) != set(range(8)) or set(labels) != set(range(8)):
        raise ValueError("Eight evaluation slots required")
    worlds, families = [], []
    for slot in range(8):
        if set(predictions[slot]) != set(METHODS) or len(labels[slot]) != 4:
            raise ValueError("Incomplete evaluation slot")
        for p in predictions[slot].values():
            validate_prediction(p)
        rows = []
        for w, label in enumerate(labels[slot]):
            y, tick = label["completed_by_H"], label["completion_tick"]
            if type(y) is not bool or (y and (type(tick) is not int or not 60 <= tick <= 100)) or (not y and tick is not None):
                raise ValueError("Invalid label")
            methods = {}
            for m, p in predictions[slot].items():
                s, ts = p["predicted_completion_status_set"], p["predicted_completion_ticks"]
                methods[m] = dict(covered=y in s, classes=s,
                    losses={str(l): int(y not in s) + l * int(len(s) == 2) for l in (0., .1, .25, .5)},
                    discrete_hit=(tick in ts) if y else None,
                    envelope_hit=bool(ts and ts[0] <= tick <= ts[-1]) if y else None,
                    empty_time=y and not ts,
                    width=ts[-1]-ts[0] if ts else None,
                    median_error=abs(ts[(len(ts)-1)//2]-tick) if y and ts else None,
                    nearest_error=min(abs(t-tick) for t in ts) if y and ts else None)
            rows.append(dict(slot=slot, world=w, actual=label, methods=methods))
        worlds.extend(rows)
        losses = {m:{str(l):mean(r["methods"][m]["losses"][str(l)] for r in rows)
                     for l in (0., .1, .25, .5)} for m in METHODS}
        families.append(dict(slot=slot, losses=losses,
            D={k:losses["M1"][k]-losses["M2"][k] for k in losses["M1"]}))
    summary = {}
    for m in METHODS:
        complete = [r for r in worlds if r["actual"]["completed_by_H"]]
        optimistic = [r for r in worlds if r["methods"]["M0"]["classes"] == [True] and not r["actual"]["completed_by_H"]]
        pessimistic = [r for r in worlds if r["methods"]["M0"]["classes"] == [False] and r["actual"]["completed_by_H"]]
        correct = [r for r in complete if r["methods"]["M0"]["classes"] == [True]]
        methods = [r["methods"][m] for r in worlds]
        summary[m] = dict(loss={k:mean(f["losses"][m][k] for f in families) for k in families[0]["losses"][m]},
            coverage=ratio([r["covered"] for r in methods]),
            class_coverage={str(y):ratio([r["methods"][m]["covered"] for r in worlds if r["actual"]["completed_by_H"] == y]) for y in (False, True)},
            sets={str(s):ratio([r["classes"] == s for r in methods]) for s in ([False],[True],[False,True])},
            optimistic_recovery=ratio([False in r["methods"][m]["classes"] for r in optimistic]),
            pessimistic_recovery=ratio([True in r["methods"][m]["classes"] for r in pessimistic]),
            false_alarm=ratio([False in r["methods"][m]["classes"] for r in correct]),
            empty_time=ratio([r["methods"][m]["empty_time"] for r in complete]),
            discrete_hit=ratio([r["methods"][m]["discrete_hit"] for r in complete]),
            envelope_hit=ratio([r["methods"][m]["envelope_hit"] for r in complete]),
            errors={k:dict(n=len(v),mean=mean(v) if v else None)
                    for k in ("median_error","nearest_error","width")
                    for v in [[r[k] for r in methods if r[k] is not None]]})
    common = [r for r in worlds if all(r["methods"][m]["median_error"] is not None for m in ("M1","M2"))]
    gain = mean(f["D"]["0.25"] for f in families)
    wins = sum(f["D"]["0.25"] > 0 for f in families)
    better = gain >= .05 and wins >= 5 and summary["M2"]["coverage"]["value"] >= summary["M1"]["coverage"]["value"]
    return dict(worlds=worlds, families=families, methods=summary, mean_D=gain, improved_families=wins,
        costs={s:{m:dict(simulation=predictions[s][m].get("cost"),
                       implementation=predictions[s][m].get("implementation_cost"))
                  for m in METHODS} for s in range(8)},
        service_diagnostics=[r["actual"].get("service_diagnostics") for r in worlds],
        time_common=dict(n=len(common),excluded=len([r for r in worlds if r["actual"]["completed_by_H"]])-len(common),
            means={m:{k:mean(r["methods"][m][k] for r in common) if common else None
                      for k in ("median_error","nearest_error")} for m in ("M1","M2")}),
        METHOD_VALID=True, result="PREDICTIVE_GAIN_OBSERVED" if better else "NO_DEMONSTRATED_GAIN")
