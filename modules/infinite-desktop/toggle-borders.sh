#!/usr/bin/env bash
WS_ID=$(/home/pg/scripts/get-active-ws.sh)
if [ -f "/home/pg/.local/state/infinite-desktop/state-$WS_ID" ] && grep -q "canvas" "/home/pg/.local/state/infinite-desktop/state-$WS_ID" 2>/dev/null; then
    exit 0
fi
FLAG="/tmp/borders-off-global"
if [ -f "$FLAG" ]; then
    rm -f "$FLAG"
    hyprctl eval 'hl.config({general={border_size=2}})'
else
    touch "$FLAG"
    hyprctl eval 'hl.config({general={border_size=0}})'
fi
