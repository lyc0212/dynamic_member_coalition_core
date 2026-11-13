"""Assemble this conversation-authorized one-shot record; no MODEL advancement."""
import sys,json,hashlib,subprocess,time
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import numpy,scipy,psutil
from research.non_oracle.stfbs_d1a_preflight import check_source_lock,REQUIRED_SOURCES
from scripts.stfbs_d1a_run import frozen_registration,LIMITS

root=Path.cwd();out=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_bytes())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(name,value):
    with (out/name).open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
assert head=='fa42557fd4ee453a27b38ab3644000830246ac42'
branch=subprocess.check_output(['git','branch','--show-current'],text=True).strip()
snapshot=read('reports/stfbs_lite_d1a_h1_preflight_lock_001/SCIENCE_DEPENDENCY_PINS.json')
expected=snapshot['sha256'];assert set(expected)==set(REQUIRED_SOURCES) and len(expected)==45
check_source_lock(root,expected)
actual={p:sha(p) for p in expected};assert actual==expected
runtime=read('reports/stfbs_lite_d1a_h1_preflight_lock_001/RUNTIME_IDENTITY.json')['runtime']
for name,module in [('numpy',numpy),('scipy',scipy),('psutil',psutil)]:
    assert module.__version__==runtime[name]['version']
    assert str(Path(module.__file__))==runtime[name]['module_file']
    assert sha(module.__file__)==runtime[name]['module_sha256']
assert sys.version==runtime['python']['version'] and sys.executable==runtime['python']['executable']
assert sha(sys.executable)==runtime['python']['exe_sha256']
for p,s in dict(runtime['python']['DLLs'],**runtime['psutil_native']).items():assert sha(p)==s
view,seed,contexts,manifest,world,plans,frozen_plan=frozen_registration()
assert manifest['public_digest']=='a37cde42a2c4c147f4abc9289e5de693790218d17bcafcbe7fe3cfb49a9d6602'
assert world['world_digest']=='e51e132471e668802881e53ece684e04e1e3ba828ebaeb061ffb9db24e1db45d'
output=root/'reports/stfbs_lite_d1a_h1_revalidation_001'
watchdog=root/'reports/stfbs_lite_d1a_h1_revalidation_001_watchdog'
assert not output.exists() and not watchdog.exists() and not (out/'APPROVAL.json').exists()
baseline=read('reports/stfbs_lite_d1a_h1_preflight_lock_001/BASELINE.json')
protected={p:s for p,s in baseline['pins'].items() if p.startswith('reports/')}
assert all(sha(p)==s for p,s in protected.items())
# Pin complete protected current report trees, including the latest preflight report.
for directory in ('reports/stfbs_lite_d1a_001','reports/stfbs_lite_d1a_g3_history_repair_001','reports/stfbs_lite_d1a_g3_supplement_001','reports/stfbs_lite_d1a_g3_audit_hardening_001','reports/stfbs_lite_d1a_h1_revalidation_prep_001','reports/stfbs_lite_d1a_h1_preflight_lock_001'):
    for p in Path(directory).rglob('*'):
        if p.is_file():protected[p.as_posix()]=sha(p)
save('PRECHECK.json',dict(status='PASS',head=head,branch=branch,worktree_science='PASS',source_snapshot_sha256=sha('reports/stfbs_lite_d1a_h1_preflight_lock_001/SCIENCE_DEPENDENCY_PINS.json'),expected_sources=expected,actual_sources=actual,runtime_snapshot_match=True,runtime=runtime,output_and_watchdog_absent=True,public_digest=manifest['public_digest'],world_digest=world['world_digest'],plan=frozen_plan,source_registration=manifest,protected_before=protected,created_utc=time.time()))
attachment=Path(r'C:\Users\14738\.codex\attachments\62f9b056-e90e-4be1-b61b-76f10f0fdb4a\已粘贴的文本.txt')
(out/'USER_AUTHORIZATION_REFERENCE.txt').write_bytes(attachment.read_bytes())
approval=dict(status='APPROVED_FOR_ONE_H1_REVALIDATION',experiment='D1_A_FROZEN_H1',task='D1-A-H1-MODEL-REVALIDATION-0',authorized_by='用户在本次对话中直接授权；不声明个人身份、签名或额外审批编号',authorization_attachment_sha256=sha(attachment),head=head,source_pins=expected,output_dir=str(output),watchdog_evidence_dir=str(watchdog),limits=LIMITS,scope='一次原冻结 KEEP/SWITCH 联合MODEL成对复验；失败不修复重试；无ACTUAL STEP',public_digest=manifest['public_digest'],world_digest=world['world_digest'],D60_sources=manifest['source_files'],frozen_plan=frozen_plan,continuation='policy.decide(view, method="R") at D80/D100',protocol='D1-A V1.3 + H1 revalidation prep V0.2 + preflight lock V1.0 + this MODEL revalidation V1.0',prepared_expected_snapshot='reports/stfbs_lite_d1a_h1_preflight_lock_001/SCIENCE_DEPENDENCY_PINS.json')
save('APPROVAL.json',approval)
print('One-shot approval created; version/runtime/frozen source/world/plan verified. No Branch.run or WLS called.')
