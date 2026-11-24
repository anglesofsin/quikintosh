#!/run/current-system/sw/bin/bash
# Screen magnifier helper for Hyprland's cursor zoom.
# Usage: zoom.sh in|out|reset|rigid|loose|toggle-rigid [step]
set -euo pipefail

ACTION="${1:-in}"
STEP="${2:-0.2}"
MIN_ZOOM=1.0
MAX_ZOOM=5.0

get_zoom() {
    hyprctl getoption cursor:zoom_factor -j 2>/dev/null \
        | python3 -c 'import json,sys; print(json.load(sys.stdin).get("float", 1.0))' 2>/dev/null \
        || printf '1.0\n'
}

get_rigid() {
    hyprctl getoption cursor:zoom_rigid -j 2>/dev/null \
        | python3 -c 'import json,sys; print("true" if json.load(sys.stdin).get("bool", False) else "false")' 2>/dev/null \
        || printf 'false\n'
}

set_zoom() {
    local value="$1"
    hyprctl eval "hl.config({ cursor = { zoom_factor = ${value} } })" >/dev/null 2>&1
}

set_rigid() {
    local value="$1"
    hyprctl eval "hl.config({ cursor = { zoom_rigid = ${value} } })" >/dev/null 2>&1
}

case "$ACTION" in
    in|out)
        CURRENT="$(get_zoom)"
        NEW="$(python3 - "$CURRENT" "$ACTION" "$STEP" "$MIN_ZOOM" "$MAX_ZOOM" <<'PYEOF'
import sys
cur = float(sys.argv[1])
action = sys.argv[2]
step = float(sys.argv[3])
mn = float(sys.argv[4])
mx = float(sys.argv[5])
next_value = cur + step if action == "in" else cur - step
next_value = max(mn, min(mx, next_value))
print(f"{next_value:.2f}")
PYEOF
)"
        set_zoom "$NEW"
        ;;
    reset)
        set_zoom "$MIN_ZOOM"
        ;;
    rigid)
        set_rigid true
        ;;
    loose)
        set_rigid false
        ;;
    toggle-rigid)
        if [ "$(get_rigid)" = "true" ]; then
            set_rigid false
        else
            set_rigid true
        fi
        ;;
    *)
        echo "Usage: zoom.sh in|out|reset|rigid|loose|toggle-rigid [step]" >&2
        exit 2
        ;;
esac
