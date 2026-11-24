#!/run/current-system/sw/bin/bash
# Moves the focused window based on the active workspace mode:
#   canvas    -> move the floating window by a step
#   scrolling -> move the window between tape columns
#   tiled     -> move the window in the dwindle layout
DIR="$1"
STEP=100
WS_ID=$(/home/pg/scripts/get-active-ws.sh)
STATE="tiled"
if [ -f "/home/pg/.local/state/infinite-desktop/state-$WS_ID" ]; then
    STATE=$(cat "/home/pg/.local/state/infinite-desktop/state-$WS_ID")
fi

if [ "$STATE" = "canvas" ]; then
    case "$DIR" in
        left)  hyprctl eval "hl.dispatch(hl.dsp.window.move({x = -$STEP, y = 0, relative = true}))" >/dev/null 2>&1 ;;
        right) hyprctl eval "hl.dispatch(hl.dsp.window.move({x = $STEP, y = 0, relative = true}))" >/dev/null 2>&1 ;;
        up)    hyprctl eval "hl.dispatch(hl.dsp.window.move({x = 0, y = -$STEP, relative = true}))" >/dev/null 2>&1 ;;
        down)  hyprctl eval "hl.dispatch(hl.dsp.window.move({x = 0, y = $STEP, relative = true}))" >/dev/null 2>&1 ;;
    esac
elif [ "$STATE" = "scrolling" ]; then
    case "$DIR" in
        left)  hyprctl eval 'hl.dispatch(hl.dsp.layout("consume_or_expel prev"))' >/dev/null 2>&1 ;;
        right) hyprctl eval 'hl.dispatch(hl.dsp.layout("consume_or_expel next"))' >/dev/null 2>&1 ;;
        up)    hyprctl eval 'hl.dispatch(hl.dsp.layout("promote"))' >/dev/null 2>&1 ;;
        down)  hyprctl eval 'hl.dispatch(hl.dsp.layout("promote"))' >/dev/null 2>&1 ;;
    esac
else
    hyprctl eval "hl.dispatch(hl.dsp.window.move({direction = \"$DIR\"}))" >/dev/null 2>&1
fi
