import sys,pathlib,json,importlib
REPO=pathlib.Path(r'D:\1st\dynamic_member_coalition_core')
ENV=pathlib.Path(r'D:\miniconda3\envs\dynamic_member_coalition_core')
def bind(root,role):
 root=pathlib.Path(root)
 if pathlib.Path(sys.executable).resolve()!=ENV/'python.exe' or pathlib.Path(sys.prefix).resolve()!=ENV:raise RuntimeError('FIXED_ENVIRONMENT_IDENTITY')
 if sys.version_info[:3]!=(3,13,5):raise RuntimeError('PYTHON_VERSION')
 site=ENV/'Lib/site-packages'
 if not site.is_dir():raise RuntimeError('SITE_PACKAGES_MISSING')
 sys.path[:0]=[str(REPO),str(root),str(root.parent),str(site)]
 modules={}
 for n,v in {'numpy':'2.1.3','scipy':'1.15.3','psutil':'7.2.2'}.items():
  m=importlib.import_module(n);p=pathlib.Path(m.__file__).resolve()
  if m.__version__!=v or not p.is_relative_to(site.resolve()):raise RuntimeError('PACKAGE_BINDING/'+n)
  modules[n]=dict(version=m.__version__,file=str(p))
 record=dict(status='PASS',role=role,executable=sys.executable,prefix=sys.prefix,modules=modules,isolated=True)
 with (root/('ENTRY_IMPORT_'+role+'.json')).open('x') as f:json.dump(record,f,indent=2)
 return record
