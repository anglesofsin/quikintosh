#!/run/current-system/sw/bin/bash
# In canvas mode: toggles "focus mode" on the active window — it is maximized
# to the full screen area (with a gap around it) and raised above all others,
# staying focused until toggled again or Win+arrows. Outside canvas: plain
# float toggle.
WS_ID=$(/home/pg/scripts/get-active-ws.sh)
if [ -z "$WS_ID" ]; then
    exit 1
fi
STATE_FILE="/home/pg/.local/state/infinite-desktop/state-${WS_ID}"
STATE=$(cat "$STATE_FILE" 2>/dev/null || echo "tiled")

if [ "$STATE" != "canvas" ]; then
    exec hyprctl eval 'hl.dispatch(hl.dsp.window.float({action = "toggle"}))'
fi

FOCUS_FILE="/tmp/infinite-desktop-focus-${WS_ID}"
if [ -f "$FOCUS_FILE" ]; then
    # OFF: restore the window to its saved geometry
    python3 - "$FOCUS_FILE" <<'PYEOF'
import json, subprocess, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
addr = d.get('address')
if addr:
    at, size = d.get('at'), d.get('size')
    lua = ''
    if at and size:
        lua += (
            f'hl.dispatch(hl.dsp.window.resize({{x = {size[0]}, y = {size[1]}, window = "address:{addr}"}}))\n'
            f'hl.dispatch(hl.dsp.window.move({{x = {at[0]}, y = {at[1]}, window = "address:{addr}"}}))'
        )
    if lua:
        subprocess.run(['hyprctl', 'eval', lua], capture_output=True, timeout=0.5)
PYEOF
    rm -f "$FOCUS_FILE"
else
    # ON: save geometry, then maximize + raise above everything
    python3 - "$FOCUS_FILE" <<'PYEOF'
import json, subprocess, sys
MARGIN = 20
r = subprocess.run(['hyprctl', 'activewindow', '-j'], capture_output=True, text=True, timeout=0.3)
w = json.loads(r.stdout) if r.stdout else None
if not w or not w.get('address'):
    sys.exit(1)
with open(sys.argv[1], 'w') as f:
    json.dump({'address': w['address'], 'at': w.get('at'), 'size': w.get('size')}, f)
addr = w['address']
mw, mh = 1920, 1080
try:
    r2 = subprocess.run(['hyprctl', 'monitors', '-j'], capture_output=True, text=True, timeout=0.3)
    for m in json.loads(r2.stdout):
        if m.get('focused', False):
            mw, mh = m['width'], m['height']
            break
except Exception:
    pass
ww = mw - 2 * MARGIN
wh = mh - 2 * MARGIN
lua = (
    f'hl.dispatch(hl.dsp.focus({{window = "address:{addr}"}}))\n'
    f'hl.dispatch(hl.dsp.window.resize({{x = {ww}, y = {wh}, window = "address:{addr}"}}))\n'
    f'hl.dispatch(hl.dsp.window.move({{x = {MARGIN}, y = {MARGIN}, window = "address:{addr}"}}))\n'
    f'hl.dispatch(hl.dsp.window.bring_to_top())'
)
subprocess.run(['hyprctl', 'eval', lua], capture_output=True, timeout=0.5)
PYEOF
fi
