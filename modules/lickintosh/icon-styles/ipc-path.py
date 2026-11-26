"""Resolve a running shell, validating one cached PID before a process scan."""
from pathlib import Path
import json,os,sys,tempfile

def config_for(proc):
 try:
  args=(proc/'cmdline').read_bytes().decode().split('\0')
  if '-p' not in args or any(x in args for x in ['ipc','list','log']):return None
  path=Path(args[args.index('-p')+1])
  if '-lickintosh-source-' not in str(path) or path.name=='settings.qml':return None
  if path.name=='shell.qml' or (path.is_dir() and (path/'shell.qml').exists()):return str(path)
 except (OSError,UnicodeError,ValueError,IndexError):pass
 return None

def resolve(fallback,processes=Path('/proc'),cache=None):
 if cache:
  try:
   saved=json.loads(cache.read_text());pid=str(saved['pid'])
   if pid.isdecimal():
    current=config_for(processes/pid)
    if current and current==saved['path']:return current
  except (OSError,ValueError,KeyError,TypeError):pass
 for proc in processes.iterdir():
  if not proc.name.isdecimal():continue
  path=config_for(proc)
  if not path:continue
  if cache:
   try:
    fd,tmp=tempfile.mkstemp(prefix='.qi-ipc-',dir=cache.parent)
    try:
     with os.fdopen(fd,'w') as f:json.dump({'pid':proc.name,'path':path},f)
     Path(tmp).replace(cache)
    finally:Path(tmp).unlink(missing_ok=True)
   except OSError:pass
  return path
 return fallback

if __name__=='__main__':
 runtime=os.environ.get('XDG_RUNTIME_DIR');cache=Path(runtime)/'quickintosh-ipc-path.json' if runtime else None
 print(resolve(sys.argv[1],cache=cache))
