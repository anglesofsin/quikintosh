#!/run/current-system/sw/bin/bash
# Exits scrolling layout mode on the active workspace and returns to dwindle.
WS_ID=$(/home/pg/scripts/get-active-ws.sh)
if [ -z "$WS_ID" ]; then
    exit 1
fi

# Restore saved opacity setting
python3 - <<'PYEOF'
import json, subprocess
v = 0.9
try:
    with open('/tmp/infinite-desktop-scrolling-saved-opts') as f:
        saved = json.load(f)
    v = saved.get('inactive_opacity', 0.9)
except Exception:
    pass
subprocess.run(['hyprctl', 'eval', 'hl.config({decoration={inactive_opacity=%s}})' % v],
               capture_output=True, timeout=0.5)
PYEOF

# Restore per-window properties
BS=$(hyprctl getoption general:border_size -j 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('int', 0))" 2>/dev/null)
hyprctl eval '
local ws = hl.get_active_special_workspace() or hl.get_active_workspace()
for _, v in ipairs(hl.get_workspace_windows(ws)) do
  if not v.floating then
    local addr = v.address
    hl.dispatch(hl.dsp.window.set_prop({prop = "decorate", value = 1, window = "address:" .. addr}))
    hl.dispatch(hl.dsp.window.set_prop({prop = "border_size", value = '"$BS"', window = "address:" .. addr}))
  end
end
' >/dev/null 2>&1

# Switch the workspace back to the dwindle layout (special workspaces are
# matched by name; '-' prefixed numeric selectors are parsed as relative)
SPECIAL_NAME=$(hyprctl monitors -j 2>/dev/null | python3 -c '
import sys, json
try:
    ms = json.load(sys.stdin)
except Exception:
    sys.exit(0)
m = next((x for x in ms if x.get("focused")), ms[0] if ms else None)
if m is None:
    sys.exit(0)
print((m.get("specialWorkspace") or {}).get("name", ""))
' 2>/dev/null)
RULE_WS="${WS_ID}"
if [ -n "$SPECIAL_NAME" ]; then RULE_WS="$SPECIAL_NAME"; fi
hyprctl eval "hl.workspace_rule({ workspace = \"${RULE_WS}\", layout = \"dwindle\" })" >/dev/null 2>&1
# Force a layout refresh so the running workspace switches algorithm
hyprctl eval 'hl.config({ scrolling = { direction = "right" } })' >/dev/null 2>&1
sleep 0.2
