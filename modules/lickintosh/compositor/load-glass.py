"""Optional exact-ABI glass plugin. A failure must not prevent shell startup."""
import json,os,subprocess,sys
if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):raise SystemExit(0)
try:
 plugins=json.loads(subprocess.check_output(['hyprctl','plugins','list','-j'],text=True,timeout=3))
 if not any(p.get('name')=='hyprglass' for p in plugins):
  result=subprocess.run(['hyprctl','plugin','load',sys.argv[1]],capture_output=True,text=True,timeout=8)
  if result.returncode or result.stdout.strip()!='ok':print('Quickintosh: window glass unavailable; standard blur remains active.',file=sys.stderr)
except (OSError,ValueError,subprocess.SubprocessError):pass
