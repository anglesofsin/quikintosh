"""Load only the matching read-only geometry plugin; never force an ABI change."""
import json,os,subprocess,sys
if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):raise SystemExit(0)
try:
 result=subprocess.run(['hyprctl','plugins','list','-j'],capture_output=True,text=True,timeout=2)
 plugins=json.loads(result.stdout)
 if isinstance(plugins,list) and any(p.get('name')=='quickintosh-geometry' for p in plugins):raise SystemExit(0)
 loaded=subprocess.run(['hyprctl','plugin','load',sys.argv[1]],capture_output=True,text=True,timeout=3)
 if loaded.returncode:print('Quickintosh: precise compositor geometry unavailable; keeping native fallback.',file=sys.stderr)
except (OSError,ValueError,subprocess.SubprocessError):pass
