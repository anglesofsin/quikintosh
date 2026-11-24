#!/run/current-system/sw/bin/bash
# Enters scrolling layout mode on the active workspace:
# windows become columns on an infinitely growing tape.
WS_ID=$(/home/pg/scripts/get-active-ws.sh)
if [ -z "$WS_ID" ]; then
    exit 1
fi

mkdir -p "${HOME}/.local/state/infinite-desktop"
echo "scrolling" > "${HOME}/.local/state/infinite-desktop/state-${WS_ID}"

# Drop any stale focus-mode state
rm -f /tmp/infinite-desktop-focus-${WS_ID}

# Panning daemon is canvas-only, make sure it is stopped
systemctl --user stop infinite-desktop 2>/dev/null || true

# Save current opacity setting and force uniform opacity (same as canvas mode)
SAVE_FILE="/tmp/infinite-desktop-scrolling-saved-opts"
python3 - "$SAVE_FILE" <<'PYEOF'
import json, subprocess, sys
try:
    r = subprocess.run(['hyprctl', 'getoption', 'decoration:inactive_opacity', '-j'],
                       capture_output=True, text=True, timeout=0.3)
    v = json.loads(r.stdout).get('float', 0.9)
    with open(sys.argv[1], 'w') as f:
        json.dump({'inactive_opacity': v}, f)
except Exception:
    pass
PYEOF
hyprctl eval 'hl.config({decoration={inactive_opacity=1.0}})' >/dev/null 2>&1

# Assign the scrolling layout to this workspace (special workspaces are
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
hyprctl eval "hl.workspace_rule({ workspace = \"${RULE_WS}\", layout = \"scrolling\", layout_opts = { direction = \"right\" } })" >/dev/null 2>&1
# Touch a scrolling config value to force a layout refresh, so the rule is
# applied to the already-running workspace
hyprctl eval 'hl.config({ scrolling = { direction = "right" } })' >/dev/null 2>&1
sleep 0.2

# Put only canvas-managed windows back on the tape. Native floating windows
# (dialogs, menus, notifications and overlays) must keep their geometry.
hyprctl eval '
local ws = hl.get_active_special_workspace() or hl.get_active_workspace()
for _, v in ipairs(hl.get_workspace_windows(ws)) do
  local addr = v.address
  local managed = false
  for _, tag in ipairs(v.tags) do
    if tag == "infinite-desktop-canvas" then managed = true end
  end
  if managed then
    hl.dispatch(hl.dsp.window.float({action = "disable", window = "address:" .. addr}))
    hl.dispatch(hl.dsp.window.tag({tag = "-infinite-desktop-canvas", window = "address:" .. addr}))
  end
  if managed or not v.floating then
    hl.dispatch(hl.dsp.window.set_prop({prop = "border_size", value = 0, window = "address:" .. addr}))
  end
end
' >/dev/null 2>&1

# Bring the focused window into view
hyprctl eval 'hl.dispatch(hl.dsp.layout("fit active"))' >/dev/null 2>&1
