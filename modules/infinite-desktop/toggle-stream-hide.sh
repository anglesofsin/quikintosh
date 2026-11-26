#!/usr/bin/env bash
# Hide/show only the active special workspace in screen capture.
set -euo pipefail
case "${1:-}" in hide|show) ;; *) echo 'Usage: toggle-stream-hide.sh hide|show' >&2; exit 1;; esac
exec python3 - "$1" <<'PY'
import fcntl,json,os,subprocess,sys
from pathlib import Path
monitors=json.loads(subprocess.check_output(['hyprctl','monitors','-j'],text=True))
monitor=next((m for m in monitors if m.get('focused')),monitors[0] if monitors else {})
target=(monitor.get('specialWorkspace') or {}).get('name','')
if not target.startswith('special:'):sys.exit(0)
state=Path.home()/'.local/state/infinite-desktop/stream-hidden'
state.parent.mkdir(parents=True,exist_ok=True)
with (state.parent/'stream-hidden.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 names=set(state.read_text().splitlines()) if state.exists() else set()
 names={x for x in names if x.startswith('special:')}
 hidden=sys.argv[1]=='hide'
 value='1' if hidden else '0'
 # Lua set_prop takes text; JSON quoting is valid for these Unicode-free
 # workspace control strings and names are encoded as UTF-8 Lua byte escapes.
 quote=lambda s:'"'+''.join('\\%03d'%b for b in s.encode())+'"'
 lua='for _,ws in ipairs(hl.get_workspaces()) do if ws.special and ws.name=='+quote(target)+' then for _,w in ipairs(hl.get_workspace_windows(ws)) do hl.dispatch(hl.dsp.window.set_prop({prop="no_screen_share",value="'+value+'",window="address:"..w.address})) end end end'
 result=subprocess.run(['hyprctl','eval',lua],text=True,capture_output=True)
 if result.returncode or 'error' in result.stdout.lower():
  print(result.stdout+result.stderr,file=sys.stderr);sys.exit(1)
 if hidden:names.add(target)
 else:names.discard(target)
 temporary=state.with_suffix('.tmp');temporary.write_text(''.join(n+'\n' for n in sorted(names)));temporary.replace(state)
PY
