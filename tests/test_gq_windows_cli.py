import importlib.util,unittest,tempfile,json,uuid
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gq_cli',ROOT/'scripts/run_gq_windows.py');cli=importlib.util.module_from_spec(spec);spec.loader.exec_module(cli)
@contextmanager
def local_temp():
 p=ROOT/'reports/windows_gq_cli_packaging_20261105/test_artifacts'/uuid.uuid4().hex
 p.mkdir(parents=True);yield str(p)
class Tests(unittest.TestCase):
 def test_parameters(self):
  for mode in ['R','S_NEW','both']:
   a=cli.parser().parse_args(['--scene','a.json','--output','new','--evaluator',mode]);self.assertEqual(a.evaluator,mode);self.assertIsNone(a.max_decisions);self.assertEqual(a.audit,'required')
 def test_invalid_limit(self):
  with self.assertRaises(SystemExit):cli.parser().parse_args(['--scene','a','--output','b','--timeout','0'])
 def test_existing_output_no_execution(self):
  with local_temp() as t,patch.object(cli.subprocess,'run') as run:
   with self.assertRaises(FileExistsError):cli.main(['--scene','missing','--output',t])
   run.assert_not_called()
 def test_invalid_input_no_execution(self):
  with local_temp() as t,patch.object(cli.subprocess,'run') as run:
   source=Path(t)/'bad.json';source.write_text('{}')
   with self.assertRaises(ValueError):cli.main(['--scene',str(source),'--output',str(Path(t)/'out')])
   self.assertFalse((Path(t)/'out').exists());run.assert_not_called()
 def test_fixture_matches_validated_input(self):
  import hashlib
  source=ROOT/'configs/gq_windows_single_target.json';meta=json.loads((ROOT/'configs/gq_windows_single_target.provenance.json').read_text())
  self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),meta['sha256'])
if __name__=='__main__':unittest.main()
