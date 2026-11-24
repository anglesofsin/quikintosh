"""Repair companion entry points after managed-client/mod updates, without restart."""
from pathlib import Path
import os,sys,time,json,subprocess,hashlib
BASE=Path(__file__).parent
# Guard owns no Discord credentials, messages, audio or network connections.
def signature():
 paths=list((Path.home()/'.config').glob('*/sessionData/equicord.asar'))
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   exe=(proc/'exe').resolve(strict=True)
   if '/clients/' in str(exe) and 'Discord' in exe.name:paths.append(exe.parent/'resources/app.asar')
  except (OSError,RuntimeError):pass
 paths += [Path('/etc/equicord/desktop/renderer.js')]
 rows=[]
 for p in sorted(set(paths)):
  try:s=p.stat();rows.append((str(p),s.st_mtime_ns,s.st_size))
  except OSError:pass
 return rows
if __name__=='__main__':
 previous=None
 while True:
  current=signature()
  if current!=previous:
   try:
    r=subprocess.run([sys.executable,str(BASE/'install-clients.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=45)
    if r.returncode:print('Voice integration repair: '+r.stderr[-400:],file=sys.stderr,flush=True)
   except (OSError,subprocess.TimeoutExpired) as e:print(str(e),file=sys.stderr,flush=True)
   previous=signature()
  time.sleep(30)
