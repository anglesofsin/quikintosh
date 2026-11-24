#!/run/current-system/sw/bin/bash
# Pans the canvas viewport by moving all canvas-managed windows.
DIR="${1:-right}"
STEP="${2:-260}"
WS_ID=$(/home/pg/scripts/get-active-ws.sh)
STATE="tiled"
if [ -f "/home/pg/.local/state/infinite-desktop/state-$WS_ID" ]; then
    STATE=$(cat "/home/pg/.local/state/infinite-desktop/state-$WS_ID")
fi

if [ "$STATE" != "canvas" ]; then
    exec /home/pg/scripts/infinite-desktop-nav.sh "$DIR"
fi

case "$DIR" in
    left)  DX="$STEP"; DY=0 ;;
    right) DX="-$STEP"; DY=0 ;;
    up)    DX=0; DY="$STEP" ;;
    down)  DX=0; DY="-$STEP" ;;
    *) exit 2 ;;
esac

exec python3 /home/pg/scripts/infinite_desktop_pan.py "$DX" "$DY"
