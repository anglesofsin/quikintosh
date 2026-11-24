#!/run/current-system/sw/bin/bash
# Ctrl+Super+H/S changes capture visibility for the active special workspace.
# Normal workspaces are intentionally always visible in screen capture.
set -u

ACTION="${1:-}"
case "$ACTION" in
    hide|show) ;;
    *) echo "uso: $0 hide|show" >&2; exit 1 ;;
esac

STATE="$HOME/.local/state/infinite-desktop/stream-hidden"
mkdir -p "$(dirname "$STATE")"
touch "$STATE"

TARGET=$(hyprctl monitors -j 2>/dev/null | python3 -c '
import json, sys
try:
    monitors = json.load(sys.stdin)
    monitor = next((item for item in monitors if item.get("focused")), monitors[0])
    special = monitor.get("specialWorkspace") or {}
    if special.get("id"):
        print(special.get("name", ""))
except Exception:
    pass
' 2>/dev/null)

if [ -z "$TARGET" ]; then
    exit 0
fi

# Drop legacy entries for normal workspaces and duplicate special entries.
SANITIZED=$(mktemp)
awk 'index($0, "special:") == 1 && !seen[$0]++' "$STATE" > "$SANITIZED"
mv "$SANITIZED" "$STATE"

if [ "$ACTION" = "hide" ]; then
    grep -qxF "$TARGET" "$STATE" || echo "$TARGET" >> "$STATE"
    VALUE=1
else
    FILTERED=$(mktemp)
    grep -vxF "$TARGET" "$STATE" > "$FILTERED" || true
    mv "$FILTERED" "$STATE"
    VALUE=0
fi

LUA="for _, ws in ipairs(hl.get_workspaces()) do
    if ws.special and ws.name == '${TARGET}' then
        for _, w in ipairs(hl.get_workspace_windows(ws)) do
            hl.dispatch(hl.dsp.window.set_prop({prop = \"no_screen_share\", value = ${VALUE}, window = \"address:\" .. w.address}))
        end
    end
end"
hyprctl eval "$LUA" >/dev/null 2>&1
