#!/run/current-system/sw/bin/bash
# Navigates based on the active workspace mode:
#   canvas    -> pan the canvas
#   scrolling -> scroll the tape / move column focus
#   tiled     -> move focus between windows
DIR="${1:-right}"
WS_ID=$(/home/pg/scripts/get-active-ws.sh)
STATE="tiled"
if [ -f "/home/pg/.local/state/infinite-desktop/state-$WS_ID" ]; then
    STATE=$(cat "/home/pg/.local/state/infinite-desktop/state-$WS_ID")
fi

if [ "$STATE" = "canvas" ]; then
    exec python3 /home/pg/scripts/infinite_desktop_nav.py "$DIR"
elif [ "$STATE" = "scrolling" ]; then
    case "$DIR" in
        left)  hyprctl eval 'hl.dispatch(hl.dsp.layout("focus l"))' >/dev/null 2>&1 ;;
        right) hyprctl eval 'hl.dispatch(hl.dsp.layout("focus r"))' >/dev/null 2>&1 ;;
        up)    hyprctl eval 'hl.dispatch(hl.dsp.layout("fit active"))' >/dev/null 2>&1 ;;
        down)  hyprctl eval 'hl.dispatch(hl.dsp.layout("fit toend"))' >/dev/null 2>&1 ;;
    esac
else
    exec hyprctl eval 'hl.dispatch(hl.dsp.focus({direction = "'"$DIR"'"}))'
fi
