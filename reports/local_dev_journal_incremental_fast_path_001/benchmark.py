"""Identical fresh-process baseline/optimized measurement; deterministic stubs only."""
import time
START_CPU, START_WALL = time.process_time(), time.perf_counter()
import sys, pathlib, json, runpy, statistics, hashlib
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent.parent))
# Reuse the archived import barrier and deterministic science stubs verbatim.
original = ROOT.parent/'stfbs_lite_h2_h3_extension_004_continuation_001/precheck.py'
setup = original.read_text(encoding='utf-8').split('results={}')[0]
ns = {'__file__': str(ROOT/'stub_setup.py')}
exec(compile(setup, str(original), 'exec'), ns)
Q, J, est = ns['Q'], ns['J'], ns['est']
phase = sys.argv[1]
out = ROOT/phase
out.mkdir()
result = {'phase': phase, 'historical': {}, 'scales': []}

def measured(fn):
    c, w = time.process_time(), time.perf_counter()
    value = fn()
    return value, {'cpu_seconds': time.process_time()-c, 'wall_seconds': time.perf_counter()-w}

history = ROOT.parent/'stfbs_lite_h2_h3_extension_004_continuation_001/H2_KEEP/worker.jsonl'
raw = history.read_bytes()
lines = raw.splitlines()
# Read-only state adapter: bypass constructor; never acquire a writer for history.
j = object.__new__(J.LocalJournal)
import os, threading
st = history.stat()
j.path, j.task_id, j.attempt_id = history, 'STFBS_LITE_LOCAL_DEV_H2_H3_EXTENSION_004', 'EXT004_H2_KEEP_001'
j.pid, j.thread, j.invalid = os.getpid(), threading.get_ident(), False
j.identity, j.size, j.sequence, j.hash = (st.st_dev, st.st_ino), len(raw), len(lines), hashlib.sha256(raw)
for name, fn in [('records', j.records), ('raw_sha256', lambda: hashlib.sha256(history.read_bytes()).hexdigest())]:
    samples = [measured(fn)[1] for _ in range(3)]
    result['historical'][name] = {'samples': samples, 'median_cpu': statistics.median(s['cpu_seconds'] for s in samples), 'median_wall': statistics.median(s['wall_seconds'] for s in samples)}

for scale in (10, 20):
    d = out/str(scale); d.mkdir()
    scans, hashes = [], []
    records = J.LocalJournal._records
    rawcheck = getattr(J.LocalJournal, 'verify_raw_bytes', None)
    def observed(self):
        scans.append(self.sequence)
        return records(self)
    def observed_hash(self):
        hashes.append(self.sequence)
        return rawcheck(self)
    J.LocalJournal._records = observed
    if rawcheck: J.LocalJournal.verify_raw_bytes = observed_hash
    def estimate(*a, **k):
        return [est.least_squares(None) for _ in range(9)]
    Q_budget_context = Q.initialized_budget(d/'journal.jsonl', 'FAST_PATH_SYNTHETIC', 'BENCH_%d'%scale, lambda b,t: {})
    b = Q_budget_context.__enter__()
    b.est = estimate
    def work():
        with b.solver_guard():
            return [b.estimator('MODEL_OBSERVATION_WLS')(None) for _ in range(scale)]
    values, hot = measured(work)
    hot_scans, hot_hashes = len(scans), len(hashes)
    _, final = measured(lambda: Q_budget_context.__exit__(None, None, None))
    final_scans, final_hashes = len(scans)-hot_scans, len(hashes)-hot_hashes
    J.LocalJournal._records = records
    if rawcheck: J.LocalJournal.verify_raw_bytes = rawcheck
    rows = b.local.records()
    counts = b.counts
    assert b.state == 'FINALIZED_PASS' and len(rows)==scale*20
    assert counts['MODEL_OBSERVATION_WLS']==scale and counts['MODEL_SOLVER_START']==scale*9
    item = dict(scale=scale, hot=hot, final=final, hot_records_calls=hot_scans, final_records_calls=final_scans, hot_raw_hash_calls=hot_hashes, final_raw_hash_calls=final_hashes, events=len(rows), counts=counts, finalization=b.finalization_report, stub_results=values, lifecycle=[{k:r['event'][k] for k in ('call_id','parent_call_id','call_type','status')} for r in rows])
    result['scales'].append(item)
result['process_cpu_seconds']=time.process_time()-START_CPU
result['process_wall_seconds']=time.perf_counter()-START_WALL
(ROOT/(phase.upper()+'_TIMINGS.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='scales'}))
