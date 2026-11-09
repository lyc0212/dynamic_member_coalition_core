"""One-off static local-import inventory; no scientific imports/execution."""
import ast,json,hashlib,subprocess
from pathlib import Path
root=Path.cwd();report=root/'reports/stfbs_lite_d1a_h1_preflight_lock_001'
seeds=['scripts/stfbs_d1a_run.py','scripts/stfbs_d1a_watchdog.py','research/non_oracle/stfbs_d1a_preflight.py','research/non_oracle/stfbs_d1a_watchdog_support.py']
seeds += [p.as_posix() for p in Path('research/non_oracle').glob('stfbs_d1a_*.py')]
seen=set();queue=list(seeds);edges={}
def module_files(module):
    bits=module.split('.') if module else []
    found=[]
    for i in range(1,len(bits)+1):
        p=Path(*bits[:i])/'__init__.py'
        if p.is_file():found.append(p.as_posix())
    for p in (Path(*bits).with_suffix('.py') if bits else Path('absent'),Path(*bits)/'__init__.py'):
        if p.is_file():found.append(p.as_posix())
    return found
while queue:
    name=queue.pop()
    if name in seen or not Path(name).is_file():continue
    seen.add(name);tree=ast.parse(Path(name).read_text(encoding='utf-8-sig'));imports=[]
    package=name[:-3].split('/')[:-1]
    for node in ast.walk(tree):
        modules=[]
        if isinstance(node,ast.Import):modules=[a.name for a in node.names]
        elif isinstance(node,ast.ImportFrom):
            base='.'.join(package[:len(package)-node.level+1]+([node.module] if node.module else [])) if node.level else (node.module or '')
            modules=[base]+[base+'.'+a.name for a in node.names]
        for module in modules:imports.extend(module_files(module))
    edges[name]=sorted(set(imports));queue.extend(imports)
# The inventory itself is intentionally not runtime code; dependency set is fixed in a literal.
files=sorted(seen)
p=Path('research/non_oracle/stfbs_d1a_preflight.py')
text=p.read_text();text=text.replace('REQUIRED_SOURCES = ()','REQUIRED_SOURCES = '+repr(tuple(files)))
p.write_bytes(text.encode('utf-8'))
baseline={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in subprocess.check_output(['git','ls-files','research','pursuit_v2','scripts','configs','docs','reports/stfbs_lite_d1a_001','reports/stfbs_lite_d1a_g3_history_repair_001','reports/stfbs_lite_d1a_g3_supplement_001','reports/stfbs_lite_d1a_g3_audit_hardening_001','reports/stfbs_lite_d1a_h1_revalidation_prep_001'],text=True).splitlines() if Path(p).is_file()}
# Main driver was already minimally edited; preserve committed original SHA explicitly.
baseline['scripts/stfbs_d1a_run.py']=hashlib.sha256(subprocess.check_output(['git','show','HEAD:scripts/stfbs_d1a_run.py'])).hexdigest()
(report/'BASELINE.json').write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),initial_status='clean',pins=baseline,note='Read-only initial status saved before edits; main original bytes recovered from HEAD'),indent=2),encoding='utf-8')
(report/'STATIC_IMPORT_REVIEW.json').write_text(json.dumps(dict(required=files,edges=edges,scope='All AST imports including function-local/relative imports and package initializers; fixed literal required set at runtime, not a discovery mechanism at approval time'),indent=2),encoding='utf-8')
print('Required local files:',len(files))
