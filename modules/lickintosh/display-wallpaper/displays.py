"""Per-rice Hyprland display transactions with an independent rollback watchdog."""
import contextlib,fcntl,json,math,os,re,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'quickintosh/displays'
def atomic(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data));tmp.replace(path)
@contextlib.contextmanager
def locked():
 ROOT.mkdir(parents=True,exist_ok=True)
 with (ROOT/'lock').open('a') as f:
  fcntl.flock(f,fcntl.LOCK_EX);yield

def read(path,default=None):
 try:return json.loads(path.read_text())
 except (OSError,ValueError):return default

def ctl(*args):
 p=subprocess.run(['hyprctl',*args],capture_output=True,text=True,timeout=15)
 if p.returncode or p.stdout.strip().lower().startswith('error'):raise ValueError(p.stderr.strip() or p.stdout.strip() or 'Hyprland rejected the configuration')
 return p.stdout

def monitors():return json.loads(ctl('monitors','all','-j'))
def spec(m):
 return dict(output=m['name'],mode=f"{m['width']}x{m['height']}@{m.get('refreshRate',60):.3f}" if m.get('width') else 'preferred',position=f"{m.get('x',0)}x{m.get('y',0)}",scale=m.get('scale',1),transform=m.get('transform',0),disabled=m.get('disabled',False),mirror=m.get('mirrorOf','') if m.get('mirrorOf') not in ('none',None) else '',vrr=int(bool(m.get('vrr',False))),bitdepth=10 if '2101010' in m.get('currentFormat','') else 8,cm=m.get('colorManagementPreset','auto'))

def validate(specs,connected):
 names={m['name'] for m in connected}
 if len(specs)!=len(names) or {s.get('output') for s in specs}!=names:raise ValueError('Displays changed. Refresh and try again.')
 by={s['output']:s for s in specs}
 if not any(not s.get('disabled') and not s.get('mirror') for s in specs):raise ValueError('Keep at least one independent display enabled.')
 for s in specs:
  if not re.fullmatch(r'(preferred|highres|highrr|\d+x\d+(@\d+(\.\d+)?)?)',str(s.get('mode',''))):raise ValueError('Invalid display mode')
  if not re.fullmatch(r'(auto|-?\d+x-?\d+)',str(s.get('position',''))):raise ValueError('Invalid display position')
  scale=s.get('scale',1)
  if not isinstance(scale,(int,float)) or not math.isfinite(scale) or not .5<=scale<=4:raise ValueError('Scale must be between 0.5 and 4')
  if s.get('transform',0) not in range(8):raise ValueError('Invalid orientation')
  target=s.get('mirror','')
  if target and (target not in by or target==s['output'] or by[target].get('disabled') or by[target].get('mirror')):raise ValueError('Choose an enabled extended display to mirror')
  if s.get('bitdepth',8) not in (8,10):raise ValueError('Invalid color depth')
  if s.get('cm','auto') not in ('auto','srgb','dcip3','dp3','adobe','wide','edid','hdr','hdredid'):raise ValueError('Invalid color profile')
 return specs

def lua(s):
 q=lambda x:json.dumps(str(x),ensure_ascii=True)
 if s.get('disabled'):return 'hl.monitor({output='+q(s['output'])+',disabled=true})'
 fields=['output='+q(s['output']),'mode='+q(s['mode']),'position='+q(s['position']),'scale='+str(float(s['scale'])),'transform='+str(int(s.get('transform',0))),'vrr='+str(int(bool(s.get('vrr',0)))),'bitdepth='+str(s.get('bitdepth',8)),'cm='+q(s.get('cm','auto')),'mirror='+q(s.get('mirror',''))]
 return 'hl.monitor({'+','.join(fields)+'})'
def apply(specs):
 # Enable independent screens before mirrors; disable outputs last.
 for s in sorted(specs,key=lambda s:(bool(s.get('disabled')),bool(s.get('mirror')))):
  ctl('eval',lua(s))
def revert_pending(token=None):
 with locked():
  pending=read(ROOT/'pending.json')
  if not pending or (token and pending['token']!=token):return
  current={m['name'] for m in monitors()}
  safe=[s for s in pending['before'] if s['output'] in current]
  if safe:apply(safe)
  (ROOT/'pending.json').unlink(missing_ok=True)
def watchdog(token):
 time.sleep(30)
 try:revert_pending(token)
 except Exception as e:(ROOT/'rollback-error.log').write_text(str(e))
def command(request):
 action=request.get('action','refresh')
 if action=='refresh':return {'monitors':monitors(),'pending':read(ROOT/'pending.json'),'saved':read(ROOT/'saved.json',{}),'profiles':read(ROOT/'profiles.json',{})}
 if action=='preview':
  with locked():
   if read(ROOT/'pending.json'):raise ValueError('Confirm or revert the pending display change first')
   current=monitors();after=validate(request['specs'],current);token=uuid.uuid4().hex
   pending={'token':token,'before':[spec(m) for m in current],'after':after,'deadline':time.time()+30}
   atomic(ROOT/'pending.json',pending)
   subprocess.Popen([sys.executable,__file__,'--watchdog',token],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True)
   try:apply(after)
   except Exception:
    apply(pending['before']);(ROOT/'pending.json').unlink(missing_ok=True);raise
   return {'pending':pending,'monitors':monitors()}
 if action=='confirm':
  with locked():
   p=read(ROOT/'pending.json')
   if not p or p['token']!=request.get('token'):raise ValueError('The display preview has expired')
   atomic(ROOT/'saved.json',{'specs':p['after']});(ROOT/'pending.json').unlink(missing_ok=True)
  return command({'action':'refresh'})
 if action=='revert':revert_pending(request.get('token'));return command({'action':'refresh'})
 if action=='restore':
  pending=read(ROOT/'pending.json')
  if pending:
   if pending['deadline']<=time.time():revert_pending(pending['token'])
   return command({'action':'refresh'})
  saved=read(ROOT/'saved.json',{}).get('specs',[]);current=monitors()
  if saved and {s['output'] for s in saved}=={m['name'] for m in current}:apply(validate(saved,current))
  return command({'action':'refresh'})
 if action in ('save-profile','delete-profile'):
  name=str(request.get('name','')).strip()[:64]
  if not name:raise ValueError('Enter a profile name')
  with locked():
   profiles=read(ROOT/'profiles.json',{})
   if action=='save-profile':profiles[name]=validate(request['specs'],monitors())
   else:profiles.pop(name,None)
   atomic(ROOT/'profiles.json',profiles)
  return {'profiles':profiles}
 raise ValueError('Unknown display action')
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='--watchdog':watchdog(sys.argv[2])
 else:
  print(json.dumps({"ready":True}),flush=True)
  for line in sys.stdin:
   try:print(json.dumps({'ok':True,**command(json.loads(line))}),flush=True)
   except Exception as e:print(json.dumps({'ok':False,'error':str(e)}),flush=True)
