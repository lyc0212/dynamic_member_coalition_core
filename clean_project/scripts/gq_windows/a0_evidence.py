"""Read-only Windows worker evidence inventory. Inventory is not scientific PASS."""
import hashlib
import json
from pathlib import Path


class EvidenceError(ValueError):
    def __init__(self, status, path, reason):
        self.status, self.path, self.reason = status, str(path), reason
        super().__init__(f'{status}: {path}: {reason}')


class Reader:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.files = {}

    def path(self, name, expected=None):
        p = Path(name)
        p = (p if p.is_absolute() else self.root/p).resolve()
        if not p.is_relative_to(self.root):
            raise EvidenceError('INVALID_EVIDENCE', name, 'outside run directory')
        if expected is not None and p != (self.root/expected).resolve():
            raise EvidenceError('INVALID_EVIDENCE', name, 'wrong artifact reference')
        if not p.is_file():
            raise EvidenceError('INCOMPLETE', name, 'missing artifact')
        return p

    def read(self, name, expected=None):
        p = self.path(name, expected)
        def pairs(items):
            result = {}
            for k,v in items:
                if k in result:
                    raise ValueError('duplicate JSON member '+k)
                result[k] = v
            return result
        raw = p.read_bytes()
        try:
            value = json.loads(raw, object_pairs_hook=pairs,
                               parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
        except (ValueError, UnicodeError) as error:
            raise EvidenceError('INVALID_EVIDENCE', name, str(error)) from error
        self.files[str(p.relative_to(self.root))] = hashlib.sha256(raw).hexdigest()
        return value


def require(condition, path, reason, status='INVALID_EVIDENCE'):
    if not condition:
        raise EvidenceError(status, path, reason)


def inventory(root):
    """Rebuild mandatory file paths from worker loops, never saved counts alone."""
    r = Reader(root)
    summary = r.read('SUMMARY.json'); result = r.read('RESULT.json')
    options = r.read('RUN_OPTIONS.json'); source = r.read('INPUT.json')
    environment = r.read('ENVIRONMENT.json'); r.read('SOURCE_PINS.json')
    require(options['evaluator']=='both', '/RUN_OPTIONS/evaluator', 'both methods required', 'INCOMPLETE')
    require(summary['status']=='PASS' and result['status']=='PASS_FULL_EPISODE_AND_INDEPENDENT_AUDIT', '/SUMMARY/status', 'run not complete', 'INCOMPLETE')
    require(environment['input_sha256']==hashlib.sha256(r.path('INPUT.json').read_bytes()).hexdigest(), '/ENVIRONMENT/input_sha256', 'input digest mismatch')
    require(r.read(options['scene'], 'INPUT.json')==source, '/RUN_OPTIONS/scene', 'wrong input')
    require(r.read('SOURCE_INPUT.json')==source, '/SOURCE_INPUT', 'input mismatch')
    r.read('DESIGN.json'); r.read('COUNTS.json')
    end = round(source['config']['stage_dt']*source['config']['max_stages']/.05)
    require(end>0 and end%20==0, '/INPUT/config', 'unsupported episode grid')
    runs = result['runs']
    require([x['method'] for x in runs]==['R','S_NEW'], '/RESULT/runs', 'missing or duplicate mode', 'INCOMPLETE')
    for run in runs:
        mode = run['method']; index = r.read(mode+'/EPISODE_INDEX.json')
        require(run['terminal'] is True and run['final_tick']==end, '/RESULT/'+mode, 'truncated episode', 'INCOMPLETE')
        expected_ticks = list(range(0,end,20))
        require([d['tick'] for d in index['decisions']]==expected_ticks, '/'+mode+'/decisions', 'missing decision', 'INCOMPLETE')
        require([d['start_tick'] for d in run['cycles']]==expected_ticks, '/RESULT/'+mode+'/cycles', 'missing cycle', 'INCOMPLETE')
        r.read(index['design_file'],'DESIGN.json');r.read(index['private_input_file'],'SOURCE_INPUT.json')
        r.read(index['initial_artifacts']['public_checkpoint'],mode+'/INITIAL_CHECKPOINT.json')
        r.read(index['final_artifacts']['private_snapshot'],mode+'/PRIVATE_SNAPSHOT.json')
        r.read(mode+'/INITIAL_BINDING.json')
        for i,d in enumerate(index['decisions']):
            folder=f'{mode}/D{i}'
            for field,suffix in [('selection_file','SELECTION.json'),('selection_audit_file','SELECTION_AUDIT/decision_audit.json'),('step_result_file','STEP.json')]:
                r.read(d[field],folder+'/'+suffix)
            for name in ['BINDING','BINDING_PIN','REQUEST','MANIFEST','TABLE','ACTUAL_REGISTRATION','ACTUAL_FRAMES','ACTUAL_FUSIONS','AFTER','ACTUAL_SENSE']:
                r.read(folder+'/'+name+'.json')
            pin=r.read(folder+'/BINDING_PIN.json');raw=r.path(folder+'/BINDING.json').read_bytes()
            require(pin['sha256']==hashlib.sha256(raw).hexdigest() and pin['size']==len(raw),folder+'/BINDING_PIN','binding pin mismatch')
            manifest=r.read(folder+'/MANIFEST.json')
            require(manifest['candidate_count']==len(manifest['candidates']),folder+'/MANIFEST','count mismatch')
            for c,spec in enumerate(manifest['candidates']):
                label=folder+'/PREDICT/'+(f'C{c}' if mode=='R' else f'B{c//4}/C{c}')
                row=r.read(label+'.json')
                require(row['candidate_identity']==spec['candidate_id'],label,'candidate reference mismatch')
                r.read(label+'/PREDICTION_REGISTRATION.json')
                audit=r.read(label+'/PREDICTION_AUDIT.json')
                require(audit['status']=='PASS',label+'/PREDICTION_AUDIT','prediction audit rejected','FAIL')
            if mode=='S_NEW':
                for b in range((len(manifest['candidates'])+3)//4):
                    for name in ['RESTORED','SIDECAR','MEMORY','CACHE']:
                        r.read(folder+f'/PREDICT/B{b}/{name}.json')
            step=r.read(folder+'/STEP.json');after=r.read(folder+'/AFTER.json')
            audit=r.read(folder+'/SELECTION_AUDIT/decision_audit.json')
            require(audit['passed'] is True and audit['tick']==i*20 and audit['candidate_count']==len(manifest['candidates']),folder+'/SELECTION_AUDIT','decision audit rejected or unrelated','FAIL')
            require(step['status']=='COMMITTED' and step['start_tick']==i*20 and step['end_tick']==(i+1)*20,folder+'/STEP','time continuity mismatch')
            require(after==step['checkpoint_after'] and after['tick']==(i+1)*20,folder+'/AFTER','checkpoint mismatch')
        final=r.read(mode+'/FINAL_CHECKPOINT.json')
        require(final['tick']==end and final['phase']=='TERMINAL','/'+mode+'/FINAL_CHECKPOINT','not terminal','INCOMPLETE')
        for name in ['FINAL_METRICS','ACTUAL_SENSE_SUMMARY','EVENTS','EPISODE_AUDIT/episode_audit']:
            r.read(mode+'/'+name+'.json')
        audit=r.read(mode+'/EPISODE_AUDIT/episode_audit.json')
        require(audit['passed'] is True and audit['numerical_contract_passed'] is True and audit['decisions']==len(expected_ticks),mode+'/EPISODE_AUDIT','episode audit rejected or truncated','FAIL')
    return dict(status='INVENTORY_COMPLETE', scientific_acceptance='NOT_EVALUATED',files=r.files)
