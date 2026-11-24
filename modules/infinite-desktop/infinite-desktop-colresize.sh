#!/run/current-system/sw/bin/bash
# Resizes the current column in scrolling mode (no-op in other modes).
# Usage: infinite-desktop-colresize.sh +conf|-conf|+0.1|-0.1|0.5
STEP="$1"
WS_ID=$(/home/pg/scripts/get-active-ws.sh)
if [ -f "/home/pg/.local/state/infinite-desktop/state-$WS_ID" ] && [ "$(cat "/home/pg/.local/state/infinite-desktop/state-$WS_ID")" = "scrolling" ]; then
    hyprctl eval "hl.dispatch(hl.dsp.layout(\"colresize ${STEP}\"))" >/dev/null 2>&1
fi
