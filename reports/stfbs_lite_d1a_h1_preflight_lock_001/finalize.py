"""Evidence assembly only; never imports a scientific MODEL module."""
import json,hashlib,subprocess,sys
from pathlib import Path
import numpy,scipy,psutil
root=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(name,v):(root/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
baseline=read(root/'BASELINE.json')
changes=[p for p,s in baseline['pins'].items() if sha(p)!=s]
assert changes==['scripts/stfbs_d1a_run.py'] or set(changes)=={'scripts/stfbs_d1a_run.py'},changes
full=read(root/'TEST_EVIDENCE_004.json');last=read(root/'TEST_EVIDENCE_006.json')
assert full['success'] and last['success']
for p in root.glob('ZERO_WLS_STEP_PROOF_*.json'):assert not any(read(p)['calls'].values())
inventory=read(root/'STATIC_IMPORT_REVIEW.json')
save('SCIENCE_DEPENDENCY_PINS.json',dict(status='PREPARED_SNAPSHOT_NOT_APPROVED',required_files=inventory['required'],sha256={p:sha(p) for p in inventory['required']},basis='Fixed literal REQUIRED_SOURCES, finite static transitive import review including delayed imports/package initializers; no dynamic Python imports or runtime rescanning to replace approved expected hashes'))
save('SOURCE_LOCK_CONTRACT.json',dict(required_count=len(inventory['required']),expected='Future externally approved exact file->SHA256 map, never replaced from current filesystem',checks=['explicit approval and HEAD','fixed required-set inclusion','unstaged and staged scientific changes','untracked and ignored executable sources in research/pursuit_v2/scripts and root','each expected file existence + independent byte SHA','original D60/H1/plan identity'],data_rules='Reports and runs are data, not import roots in the H1 call chain; .py/.pyc and other executable extensions under code/root are rejected. Parent watchdog uses isolated (-I) child and -B. No broad deletion or workspace cleanup is performed.',current_worktree='Authorized engineering changes deliberately make current production preflight reject until future reviewed execution version is fixed',limitation='Minimal launch binding, not a sandbox against hostile trusted Python code or a cryptographic approval system'))
save('SOURCE_NEGATIVE_TESTS.json',[c for c in full['cases'] if c['case'].startswith('SOURCE') or c['case']=='REAL_GIT_WORKTREE'])
save('EXTERNAL_WATCHDOG_TESTS.json',[c for c in last['cases'] if c['case'].startswith('WATCHDOG')])
old=[p for p in baseline['pins'] if p.startswith('reports/')]
save('WORKTREE_RESTORATION.json',dict(original_HEAD=baseline['head'],final_HEAD=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),changed_tracked=changes,frozen_scientific_files_changed=[],old_report_files_unchanged=len(old),tests='Negative mutations only in isolated archive/copies; actual HEAD Git object store read-only, private copied index; original index SHA checked unchanged; no reset/checkout/add/commit',index_proof=[c for c in full['cases'] if c['case']=='SOURCE-7_REAL_GIT'],final_status=subprocess.check_output(['git','status','--short'],text=True)))
save('ZERO_WLS_STEP_PROOF.json',dict(attempts={p.name:read(p) for p in root.glob('ZERO_WLS_STEP_PROOF_*.json')},H1_pair_runs=0,real_WLS=0,MODEL_advance=0,MODEL_run=0,ACTUAL_STEP=0,new_scientific_worlds=0,new_pair_values=0,ordinary_subprocesses='Short normal/abnormal/sleep/tree-sleep tests only; not MODEL'))
runtime={}
for name,module in [('numpy',numpy),('scipy',scipy),('psutil',psutil)]:
    runtime[name]=dict(version=module.__version__,module_file=module.__file__,module_sha256=sha(module.__file__))
runtime['python']=dict(version=sys.version,executable=sys.executable,exe_sha256=sha(sys.executable),DLLs={str(p):sha(p) for p in Path(sys.base_prefix).glob('python*.dll')})
runtime['psutil_native']={str(p):sha(p) for p in Path(psutil.__file__).parent.glob('*.pyd')}
save('RUNTIME_IDENTITY.json',dict(scope='Interpreter/DLL and runtime version/module identities recorded; local project source lock has 45 files. This is not a claim that every third-party library source file is in the project Git worktree.',runtime=runtime))
save('ENGINEERING_REPAIR_LOG.json',dict(first_failure='TEST_ATTEMPT_001.log: subprocess.CREATE_SUSPENDED is not exported; no child started in that failed probe',repair='Use documented Windows CREATE_SUSPENDED value 0x00000004; assign Job before resume',subsequent=['11/11 after fix','12/12 after isolated real-Git evidence','13/13 after live-binding/receipt tests','3/3 affected CPU evidence cases','4/4 final watchdog/CLI cases'],preserved=True,science_rules_changed=False))
save('ACCEPTANCE.json',dict(status='D1_A_H1_PREFLIGHT_LOCK_READY_FOR_REVIEW',D1_A_status='D1_A_BLOCKED',source_lock='PASS',worktree_and_independent_SHA='PASS',watchdog_short_OS_tests='PASS',launch_binding_and_resource_rejection='PASS',finite_regression='13/13 plus final4/4 affected',actual_H1='NOT_RUN',actual_WLS=0,MODEL_advance=0,ACTUAL_STEP=0,external900s_real_H1='NOT_RUN',independent_review_pending=True))
(root/'RESOURCE_TIMING_CONTRACT.md').write_text('''# 资源计量与保护契约

正式唯一入口为 scripts/stfbs_d1a_watchdog.py；其CLI只允许固定900秒墙钟与600秒CPU配置，不提供阈值覆盖参数。主脚本缺少合法watchdog票据会在authorize/输出/Branch前拒绝。票据绑定真实父子PID、父进程命令、批准文件SHA、900秒及挂入Job后才恢复执行；子解释器使用-I/-B。这里是最小可信编排检查，不声称能防御恶意可信Python代码。

watchdog先执行原authorize（审批、HEAD、源码、工作树、新目录），再创建与正式输出并列的新 <output>_watchdog 证据目录。子进程以CREATE_SUSPENDED启动，在执行任何用户代码前加入Windows Job，写入LAUNCH后恢复。Job启用KILL_ON_JOB_CLOSE，不允许子进程breakaway；正常、异常和超时均保留退出码、stdout/stderr原字节及真实墙钟。900秒或整树600秒触发即终止整个Job，等待退出，无自动重试。子进程内部原Budget仍保持600/900及1000/4000/5000原值。

主进程CPU来自保留的进程句柄GetProcessTimes；整树CPU来自Job Basic Accounting的累计用户/内核时间；后代CPU为两者之差。CPU与墙钟均覆盖H1子进程完整生命周期，而非只覆盖Branch.run。确认Job ActiveProcesses=0后才标cpu_complete。查询失败或仍有活动进程时保留null/原始已得值、缺失原因和范围，不能填零。OS实际返回零CPU是测量分辨率下的真实值，不能用预设零替代。watchdog自身开销不包含在子进程CPU字段内，scope明确登记。

短时测试只验证机制：正常、退出码7异常、0.3秒单进程超时、1秒带后代超时；未进行真实900秒或H1负载试验。初次因Python未导出常量失败的原始回执仍保留。全部实际测量值见EXTERNAL_WATCHDOG_TESTS与各WATCHDOG_RECEIPT。

未来G5必须由外层收齐正式LAUNCH/最终回执、原始日志、批准/执行源码指纹、PID与输出身份、整组WLS/CPU账本后独立验收。verify_watchdog_receipt默认拒绝短时测试回执、非正式生产标记、缺失或无效CPU、超时、非零退出及未清零的进程树；资源函数PASS只表示资源证据必要条件成立，不自动判定G5或D1-A通过。内部Budget通过、watchdog启动成功、或历史人工回执均不能替代这次正式证据。
''',encoding='utf-8')
(root/'H1_READINESS_DEPENDENCIES.md').write_text('''# 后续授权边界

本轮有限补强完成，不另起准备性研究阶段。本工作树尚未提交，因此真实source/worktree预检现在应拒绝，这是正确保护，不是新的科学阻断。

独立审查后，如负责人正式批准一次原H1复验，应固定包含本轮修改的实际执行版本，确认必需科学源码已受版本管理且无未批准修改/未跟踪可执行代码。源目录中现存未跟踪/忽略的.pyc/.pyd等也会拒绝，不会自动清理。外部批准文件保留原experiment/status/authorized_by/head/output_dir/limits，并登记完整45项及必要额外源码的source_pins、与输出同级的新watchdog_evidence_dir=<output>_watchdog。当前SCIENCE_DEPENDENCY_PINS仅是待审查快照，不是批准记录。

未来只经watchdog CLI显式执行：--execute-frozen-h1 --approval-manifest <外部批准> --output-dir <独立新目录> --evidence-dir <同级新目录_watchdog>。本轮没有创建有效批准记录，也没有调用这条正式命令。脚本主入口直接执行无法提供合法父进程绑定，因此不能绕过外部墙钟。

D60/世界/计划、D80/D100 R、外部上下文、原Branch独立G3与verify/service/audit、共享Budget和失败阻断保持原实现。实际D60—D120完整联合物理、belief、服务、生命周期与经济正确性仍须一次获授权的MODEL复验；原三组正差额不升级为有效结果。未来G0—G5沿用已归档协议，G5追加使用本次外部计量证据的必要性，不改变科学阈值。此次准备不代表ACTUAL收益或算法有效性。
''',encoding='utf-8')
(root/'REPORT.md').write_text(f'''# D1-A-H1-PREFLIGHT-LOCK-0 收尾

状态：D1_A_H1_PREFLIGHT_LOCK_READY_FOR_REVIEW。D1-A总体仍为D1_A_BLOCKED。

本地基准 {baseline['head']}，main，初始工作树干净；没有fetch或远端当前状态声明。沿真实静态导入（含函数内延迟导入、相对导入与包初始化）固定45个项目内必需源码文件；清单明确覆盖policy、belief、solver、WLS、公开质量/观测、G/Q、service、候选与经济、MODEL/审计、预检和watchdog。无发现字符串动态导入需要额外运行时猜测的本地科学依赖。指纹是准备快照，预期值必须由未来外部批准固定，运行时不再即时生成或替换。

源码检查独立覆盖Git未暂存/暂存修改、必需删除、代码路径中未跟踪/忽略的可执行源码，以及每份实际文件SHA。真实Git隔离副本测试在固定HEAD下修改policy并成功拒绝；跳过工作树检查后同一修改仍被独立SHA层拒绝；未跟踪导入代码也拒绝。测试只读取主Git对象并使用独立索引，不创建提交、不改主索引或原科学文件。普通报告数据不会被当作科学源码。当前新增工程源码未提交，真实生产预检如实拒绝，不会放行这份开发工作树。

watchdog正常退出、异常退出、短时超时与后代整树终止均有真实Windows Job回执。主脚本加入最小父子进程绑定和隔离解释器检查，正式入口由外部900秒watchdog承接；原共享Budget与科学规则未变。CPU明确保存主进程、整树、后代与完整性；缺失证据、短时测试回执不能通过正式资源核验。首次常量导出错误、修复和每轮测试均保留。

13组完整有限回归通过，最新4组受影响测试通过（包含新增CLI接线）；七个WLS/融合/STEP/Branch禁用哨兵所有轮次计数均为0。实际H1运行0、MODEL推进0、ACTUAL STEP/WLS0。旧报告/归档{len(old)}份字节SHA未变；跟踪代码仅改主入口身份检查，新增预检/Job辅助/外部脚本与测试。未修改冻结模型、策略、控制、服务、G/Q、WLS、历史审计或经济公式。

没有发现新的直接科学正确性阻断。已完成本轮有限工程任务并停止，不再增设准备阶段；等待独立审查及一次H1正式授权。实际模型物理和经济链路仍是未复验，不能签发D1_A_MODEL_PAIR_VALIDATED。未提交、未推送。
''',encoding='utf-8')
(root/'REPAIR.diff').write_bytes(subprocess.check_output(['git','diff','--','scripts/stfbs_d1a_run.py']))
save('FINAL_SOURCE_PINS.json',{p:sha(p) for p in inventory['required']+['tests/test_stfbs_d1a_preflight_lock.py']})
files=[p for p in root.rglob('*') if p.is_file() and p.name!='SHA256.json']
save('SHA256.json',{p.relative_to(root).as_posix():sha(p) for p in sorted(files)})
print('READY; old report files preserved:',len(old));print('Changed tracked sources:',changes)
