#!/usr/bin/env bash
# Super+Ctrl+left/right por modo:
#   scrolling -> janela focada vira coluna propria ao lado; se a coluna tiver
#                so ela, troca de lugar com a vizinha
#   tiled     -> troca de lugar com a janela vizinha na direção (dwindle)
#   canvas    -> no-op
DIR="$1"
case "$DIR" in left|right) ;; *) exit 0 ;; esac

WS_ID=$("$(dirname -- "$0")/get-active-ws.sh")
[ -n "$WS_ID" ] || exit 0
STATE=$(cat "$HOME/.local/state/infinite-desktop/state-${WS_ID}" 2>/dev/null)

if [ "$STATE" = "scrolling" ]; then
    COUNT=$(python3 - <<PY
import json, subprocess
try:
    aw = json.loads(subprocess.run(['hyprctl', 'activewindow', '-j'], capture_output=True, text=True, timeout=0.5).stdout or '{}')
    ax = aw.get('at', [None, None])[0]
    if ax is None:
        print(0); raise SystemExit
    ws = int('${WS_ID}')
    n = 0
    for c in json.loads(subprocess.run(['hyprctl', 'clients', '-j'], capture_output=True, text=True, timeout=0.5).stdout):
        if c.get('workspace', {}).get('id') == ws and not c.get('floating') and abs(c['at'][0] - ax) <= 2:
            n += 1
    print(n)
except Exception:
    print(0)
PY
)

    if [ "${COUNT:-0}" -gt 1 ]; then
        case "$DIR" in
            left)  MSG="consume_or_expel prev" ;;
            right) MSG="consume_or_expel next" ;;
        esac
    else
        case "$DIR" in
            left)  MSG="swapcol l" ;;
            right) MSG="swapcol r" ;;
        esac
    fi

    exec hyprctl eval "hl.dispatch(hl.dsp.layout(\"${MSG}\"))" >/dev/null 2>&1
fi

exit 0
