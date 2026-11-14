import json,sys,tempfile,subprocess,hashlib,os,io,tarfile,shutil
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from types import SimpleNamespace
from research.non_oracle import stfbs_d1a_preflight as lock
from research.non_oracle.stfbs_d1a_watchdog_support import require_watchdog,verify_watchdog_receipt
from scripts.stfbs_d1a_watchdog import supervise

EVIDENCE=[]
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'reports/stfbs_lite_d1a_h1_preflight_lock_001'

class LockTests(TestCase):
    def test_real_git_isolated_copy(self):
        head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        index=ROOT/'.git/index';index_sha=hashlib.sha256(index.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(dir=REPORT) as tmp:
            r=Path(tmp).resolve();self.assertTrue(r.is_relative_to(REPORT.resolve()))
            archive=subprocess.check_output(['git','archive','HEAD','research','pursuit_v2','scripts'])
            with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
                self.assertTrue(all((m.isfile() or m.isdir()) and (r/m.name).resolve().is_relative_to(r) for m in tar.getmembers()))
                tar.extractall(r,filter='data')
            private_index=r/'fixture-index';shutil.copyfile(index,private_index)
            env=dict(os.environ,GIT_INDEX_FILE=str(private_index))
            def git(root,*args):
                return subprocess.check_output(['git','--no-optional-locks','--git-dir='+str(ROOT/'.git'),'--work-tree='+str(r),*args],env=env)
            name='research/non_oracle/policy.py';p=r/name;pins={name:hashlib.sha256(p.read_bytes()).hexdigest()}
            with patch.object(lock,'REQUIRED_SOURCES',(name,)),patch.object(lock,'git',git):
                self.assertEqual(lock.check_source_lock(r,pins)['status'],'PASS')
                original=p.read_bytes();p.write_bytes(original+b'\n# isolated source negative\n')
                with self.assertRaisesRegex(ValueError,'Uncommitted'):lock.check_source_lock(r,pins)
                with self.assertRaisesRegex(ValueError,'SHA256'):lock.check_source_lock(r,pins,worktree_check=lambda root:None)
                p.write_bytes(original)
                (r/'research/non_oracle/untracked_import.py').write_text('raise RuntimeError("do not import")')
                with self.assertRaisesRegex(ValueError,'Untracked importable'):lock.check_source_lock(r,pins)
                EVIDENCE.append(dict(case='SOURCE_REAL_GIT',cases=['SOURCE-1','SOURCE-2','SOURCE-3','SOURCE-6'],status='PASS',HEAD=head,git_status_provider='actual git diff/ls-files on isolated archived HEAD with private index',main_worktree_modified=False))
        self.assertEqual(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),head)
        self.assertEqual(hashlib.sha256(index.read_bytes()).hexdigest(),index_sha)
        EVIDENCE.append(dict(case='SOURCE-7_REAL_GIT',status='PASS',original_index_sha256=index_sha,HEAD_unchanged=True))

    def test_source_cases(self):
        original=ROOT/'research/non_oracle/policy.py';before=hashlib.sha256(original.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(dir=REPORT) as tmp:
            r=Path(tmp);name='research/non_oracle/policy.py';p=r/name;p.parent.mkdir(parents=True);p.write_bytes(original.read_bytes())
            pins={name:hashlib.sha256(p.read_bytes()).hexdigest()}
            state={'unstaged':b'','staged':b'','untracked':b''}
            def git(root,*args):
                if args[0]=='diff':return state['staged' if '--cached' in args else 'unstaged']
                return state['untracked'] if '--others' in args else name.encode()+b'\0'
            with patch.object(lock,'REQUIRED_SOURCES',(name,)),patch.object(lock,'git',git):
                self.assertEqual(lock.check_source_lock(r,pins)['status'],'PASS')
                EVIDENCE.append(dict(case='SOURCE-1',status='PASS',scope='isolated real copied science bytes; deterministic Git status provider'))
                p.write_bytes(p.read_bytes()+b'\n# test-only mutation\n');state['unstaged']=(name+'\0').encode()
                with self.assertRaisesRegex(ValueError,'Uncommitted'):lock.check_source_lock(r,pins)
                EVIDENCE.append(dict(case='SOURCE-2',status='PASS',HEAD='fixed synthetic identity',reason='worktree',original_file_modified=False))
                with self.assertRaisesRegex(ValueError,'SHA256'):lock.check_source_lock(r,pins,worktree_check=lambda root:None)
                EVIDENCE.append(dict(case='SOURCE-3',status='PASS',reason='independent SHA comparison with worktree seam passing'))
                state['unstaged']=b'';p.unlink()
                with self.assertRaisesRegex(ValueError,'source missing'):lock.check_source_lock(r,pins)
                EVIDENCE.append(dict(case='SOURCE-4',status='PASS'))
                p.write_bytes(original.read_bytes())
                with self.assertRaisesRegex(ValueError,'dependency pins'):lock.check_source_lock(r,{})
                EVIDENCE.append(dict(case='SOURCE-5',status='PASS'))
                untracked=r/'research/non_oracle/unapproved.py';untracked.write_text('raise RuntimeError("must never import")')
                state['untracked']=b'research/non_oracle/unapproved.py\0'
                with self.assertRaisesRegex(ValueError,'Untracked importable'):lock.check_source_lock(r,pins)
                # Executable cache and staged mutations are not quietly treated as data.
                state['untracked']=b'research/non_oracle/__pycache__/unapproved.pyc\0'
                with self.assertRaisesRegex(ValueError,'Untracked importable'):lock.check_source_lock(r,pins)
                state['untracked']=b'';state['staged']=(name+'\0').encode()
                with self.assertRaisesRegex(ValueError,'Uncommitted'):lock.check_source_lock(r,pins)
                EVIDENCE.append(dict(case='SOURCE-6',status='PASS',also=['ignored executable bytecode','staged source']))
                state['staged']=b'';state['untracked']=b'reports/normal.json\0'
                self.assertEqual(lock.check_source_lock(r,pins)['status'],'PASS')
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),before)
        EVIDENCE.append(dict(case='SOURCE-7',status='PASS',original_SHA256=before,original_never_modified=True))

    def test_live_dirty_tree(self):
        # Real Git query must refuse the current known engineering worktree; never run MODEL.
        with self.assertRaisesRegex(ValueError,'Uncommitted|Untracked'):lock.check_worktree(ROOT)
        EVIDENCE.append(dict(case='REAL_GIT_WORKTREE',status='PASS',expected='deny uncommitted authorized development files before future version fixation'))

    def test_source_list(self):
        for p in ('research/non_oracle/policy.py','pursuit_v2/service.py','research/cooperative_sensing/estimator.py','scripts/stfbs_d1a_watchdog.py','research/non_oracle/stfbs_d1a_preflight.py'):
            self.assertIn(p,lock.REQUIRED_SOURCES)
        self.assertEqual(len(lock.REQUIRED_SOURCES),len(set(lock.REQUIRED_SOURCES)))
        self.assertTrue(all((ROOT/p).is_file() for p in lock.REQUIRED_SOURCES))

    def test_entry_and_receipt_negatives(self):
        from scripts import stfbs_d1a_run as driver
        with patch.object(driver,'authorize',side_effect=AssertionError('must reject watchdog first')):
            with self.assertRaisesRegex(ValueError,'watchdog'):driver.main([])
        for argv in ([],['--execute-frozen-h1']):
            result=subprocess.run([sys.executable,'-B','scripts/stfbs_d1a_run.py',*argv],capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('watchdog launch required',result.stderr)
        for record in ({},{'status':'EXITED','exit_code':0,'wall_seconds':1,'cpu_complete':False}):
            with self.assertRaises(ValueError):verify_watchdog_receipt(record)
        with self.assertRaisesRegex(ValueError,'watchdog'):require_watchdog(None,None)
        EVIDENCE.append(dict(case='SOURCE-8/DIRECT_ENTRY',status='PASS',no_output_created=True))

    def test_watchdog_binding_contract(self):
        from research.non_oracle import stfbs_d1a_watchdog_support as support
        with tempfile.TemporaryDirectory(dir=REPORT) as tmp:
            r=Path(tmp);approval=r/'stub_only.txt';approval.write_text('TEST_STUB_ONLY: NOT AUTHORIZED')
            ticket=r/'ticket.json'
            record=dict(watchdog_pid=4242,child_pid=4343,wall_limit=900,assigned_before_resume=True,approval_sha256=hashlib.sha256(approval.read_bytes()).hexdigest())
            parent=SimpleNamespace(pid=4242,cmdline=lambda:[sys.executable,str(ROOT/'scripts/stfbs_d1a_watchdog.py')])
            with patch.object(support.psutil,'Process',return_value=parent),patch.object(support.os,'getpid',return_value=4343),patch.object(support.os,'getppid',return_value=4242),patch.object(support.sys,'flags',SimpleNamespace(isolated=1)):
                ticket.write_text(json.dumps(record));self.assertEqual(support.require_watchdog(ticket,approval),record)
                for field,value in [('watchdog_pid',1),('child_pid',1),('wall_limit',901),('assigned_before_resume',False),('approval_sha256','bad')]:
                    bad=dict(record);bad[field]=value;ticket.write_text(json.dumps(bad))
                    with self.assertRaises(ValueError):support.require_watchdog(ticket,approval)
        valid=dict(status='EXITED',exit_code=0,wall_seconds=1,wall_limit=900,production_launch=True,cpu_complete=True,tree_cpu_seconds=.02,process_cpu_seconds=.01,active_processes=0,assigned_before_resume=True,child_pid=4343)
        support.verify_watchdog_receipt(valid)
        for field,value in [('cpu_complete',False),('process_cpu_seconds',None),('tree_cpu_seconds',None),('tree_cpu_seconds',601),('active_processes',1),('exit_code',7),('wall_seconds',901),('production_launch',False)]:
            bad=dict(valid);bad[field]=value
            with self.assertRaises(ValueError):support.verify_watchdog_receipt(bad)
        EVIDENCE.append(dict(case='WATCHDOG_BINDING_AND_G5_RESOURCE_REJECTION',status='PASS',scope='synthetic TEST_STUB_ONLY binding/unit inputs, no formal receipt or authorization generated'))

    def test_watchdog_cli_wiring(self):
        from scripts import stfbs_d1a_run as driver,stfbs_d1a_watchdog as watchdog
        with tempfile.TemporaryDirectory(dir=REPORT) as tmp:
            r=Path(tmp).resolve();output=r/'stub_pair';evidence=r/'stub_pair_watchdog';approval=r/'stub.json'
            approval.write_text(json.dumps(dict(status='TEST_STUB_ONLY',watchdog_evidence_dir=str(evidence))))
            args=['--execute-frozen-h1','--approval-manifest',str(approval),'--output-dir',str(output),'--evidence-dir',str(evidence)]
            with patch.object(driver,'authorize',return_value=(output,{})),patch.object(watchdog,'supervise',return_value={'status':'EXITED','cpu_complete':True}) as launch:
                self.assertEqual(watchdog.main(args),0)
                command=launch.call_args.args[0];self.assertIn('-I',command);self.assertIn('--watchdog-ticket',command)
                self.assertEqual(launch.call_args.kwargs['wall_limit'],900)
                self.assertEqual(launch.call_args.kwargs['cpu_limit'],600)
                launch.reset_mock();bad=r/'unrelated';approval.write_text(json.dumps(dict(status='TEST_STUB_ONLY',watchdog_evidence_dir=str(bad))))
                with self.assertRaisesRegex(ValueError,'path mismatch'):watchdog.main(args[:-1]+[str(bad)])
                launch.assert_not_called()
        EVIDENCE.append(dict(case='WATCHDOG_CLI_WIRING',status='PASS',scope='stub supervision; fixed900/600, isolated child and protected new sibling path, no real H1 launch'))

    def test_watchdog_processes(self):
        for label,code,limit,status in (
            ('normal','print("normal-marker",flush=True)',5,'EXITED'),
            ('abnormal','import sys;print("error-marker",file=sys.stderr,flush=True);sys.exit(7)',5,'ABNORMAL_EXIT'),
            ('timeout','import time; print("started",flush=True); time.sleep(10)',.3,'TIMED_OUT'),
            ('tree_timeout','import subprocess,sys,time; subprocess.Popen([sys.executable,"-c","import time;time.sleep(10)"]);time.sleep(10)',1,'TIMED_OUT')):
            out=REPORT/('watchdog_'+label)
            if out.exists():
                n=2
                while out.with_name(out.name+'_'+str(n)).exists():n+=1
                out=out.with_name(out.name+'_'+str(n))
            receipt=supervise([sys.executable,'-B','-c',code],out,wall_limit=limit)
            EVIDENCE.append(dict(case='WATCHDOG_'+label,receipt=receipt,evidence=str(out.relative_to(ROOT))))
            self.assertEqual(receipt['status'],status,receipt)
            self.assertTrue(receipt['cpu_complete'],receipt);self.assertEqual(receipt['active_processes'],0)
            self.assertEqual(receipt['attempts'],1);self.assertIsNotNone(receipt['process_cpu_seconds'])
            if label=='normal':
                with self.assertRaisesRegex(ValueError,'Not a formal'):verify_watchdog_receipt(receipt)
            else:self.assertNotEqual(receipt['exit_code'],0)
            if label=='tree_timeout':self.assertGreaterEqual(receipt['total_processes'],2)
