#!/usr/bin/env bash
# Cycles the active workspace through modes: tiled -> canvas -> scrolling -> tiled
WS_ID=$(/home/pg/scripts/get-active-ws.sh)
if [ -z "$WS_ID" ]; then
    exit 1
fi
STATE_DIR="${HOME}/.local/state/infinite-desktop"
mkdir -p "$STATE_DIR"
STATE_FILE="${STATE_DIR}/state-${WS_ID}"
current=$(cat "$STATE_FILE" 2>/dev/null || echo "tiled")

case "$current" in
    canvas)
        echo "scrolling" > "$STATE_FILE"
        /home/pg/scripts/infinite-desktop-exit-canvas.sh
        exec /home/pg/scripts/infinite-desktop-enter-scrolling.sh
        ;;
    scrolling)
        echo "tiled" > "$STATE_FILE"
        exec /home/pg/scripts/infinite-desktop-exit-scrolling.sh
        ;;
    *)
        echo "canvas" > "$STATE_FILE"
        exec /home/pg/scripts/infinite-desktop-enter-canvas.sh
        ;;
esac
