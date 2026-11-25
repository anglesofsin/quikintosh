#!/run/current-system/sw/bin/bash
# Resolves the stable state key for the workspace the user is currently on.
# Normal workspaces use their numeric ID. Special-workspace numeric IDs change
# between sessions, so they use their stable name (for example special:public).
SPECIAL_NAME=$(hyprctl monitors -j 2>/dev/null | python3 -c '
import sys, json
try:
    ms = json.load(sys.stdin)
except Exception:
    sys.exit(0)
m = next((x for x in ms if x.get("focused")), ms[0] if ms else None)
if m is None:
    sys.exit(0)
sw = m.get("specialWorkspace") or {}
if sw.get("name"):
    print(sw.get("name", ""))
' 2>/dev/null)
if [ -n "$SPECIAL_NAME" ]; then
    echo "$SPECIAL_NAME"
    exit 0
fi
hyprctl activeworkspace -j 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null
