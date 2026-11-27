"""Load/upgrade only Quickintosh's matching telemetry plugin; never force ABI."""
import json,os,re,subprocess,sys
from pathlib import Path
signature=os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
if not signature:raise SystemExit(0)
def query(*args):
 return subprocess.run(['hyprctl',*args],capture_output=True,text=True,timeout=3)
try:
 plugins=json.loads(query('plugins','list','-j').stdout)
 ours=next((p for p in plugins if p.get('name')=='quickintosh-geometry'),None)
 if ours and ours.get('version')=='1.2.0':raise SystemExit(0)
 if ours:
  # Hyprland unload expects a path. Capabilities can make /proc/maps unreadable.
  # Restrict fallback candidates to Quickintosh's installed system launchers.
  candidates=[]
  record=Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid())))/'quickintosh-geometry.path'
  try:candidates.append(record.read_text().strip())
  except OSError:pass
  launchers=[Path('/run/current-system/sw/bin/quickintosh')]
  profiles=Path('/nix/var/nix/profiles')
  if profiles.exists():launchers += [p/'sw/bin/quickintosh' for p in sorted(profiles.glob('system-*-link'),key=lambda p:int(p.name.split('-')[1]),reverse=True)]
  for launcher in launchers:
   try:candidates += re.findall(r'/nix/store/[^ \"\n]+/lib/quickintosh-geometry\.so',launcher.read_text())
   except OSError:pass
  removed=False
  for path in dict.fromkeys(candidates):
   if not path.startswith('/nix/store/') or not path.endswith('/lib/quickintosh-geometry.so'):continue
   result=query('plugin','unload',path)
   if result.returncode==0 and result.stdout.strip()=='ok':removed=True;break
  if not removed:raise RuntimeError('Cannot unload previous telemetry library')
 loaded=query('plugin','load',sys.argv[1])
 if loaded.returncode or loaded.stdout.strip()!='ok':raise RuntimeError('Matching compositor geometry unavailable')
 record=Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/'+str(os.getuid())))/'quickintosh-geometry.path'
 record.write_text(sys.argv[1])
except (OSError,ValueError,KeyError,StopIteration,RuntimeError,subprocess.SubprocessError):
 print('Quickintosh: compositor frame stream unavailable; keeping geometry fallback.',file=sys.stderr)
