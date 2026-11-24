#!/usr/bin/env bash
# Shared dispatcher for the special workspace toggles. The four
# toggle-special-*.sh scripts are thin wrappers around it.
#
# Why this file exists: Hyprland's specialWorkspaceIn / specialWorkspaceOut
# leaves are GLOBAL -- one leaf each, not one per workspace. Each toggle used to
# write its own two leaves and then toggle, so opening workspace B while
# workspace A was still open closed A with B's out style. When both were the
# same axis (S then W, both slidevert) A had no readable exit at all: it left
# with the wrong animation, hidden behind B sliding in over it.
#
# Here the outgoing workspace's out leaf is written BEFORE the new workspace is
# toggled, so every special workspace leaves with its own animation. The leaves
# stay global -- Hyprland gives no per-workspace hook for this -- but the value
# is correct at the moment the close happens.
#
# Switching also takes two dispatches instead of one. A single toggle on a
# different workspace closes the open one and opens the target in the same event,
# so the two animations start together and the incoming one covers the outgoing
# one. Closing first, waiting OUT_DELAY, then opening is what keeps them from
# overlapping on screen.
set -u

WORKSPACE="${1:-}"
case "$WORKSPACE" in
    special|public|left|right) ;;
    *)
        echo "uso: $0 <special|public|left|right>" >&2
        exit 1
        ;;
esac

# Measured on this build, from the user's own tests. The same string means the
# opposite thing in the two leaves: "slide right" enters from the right edge but
# leaves toward the left edge. Do not carry a value from one line to the other.
#   name | in style       | out style
#   ----+-----------------+------------
#   special | slidevert      | slidevert
#   public  | slidevert top  | slidevert bottom
#   left    | slide left     | slide right
#   right   | slide right    | slide left
ANIMATIONS="special:slidevert|slidevert
public:slidevert top|slidevert bottom
left:slide left|slide right
right:slide right|slide left"

# Measured, not assumed: on this build a LARGER speed value means a SLOWER
# animation -- lowering 2.8 -> 1.35 made it faster, not slower. Treat these as
# durations. Curves are unchanged.
IN_SPEED=3.0
IN_BEZIER=emphasizedDecel
OUT_SPEED=1.7
OUT_BEZIER=emphasizedAccel

# How long to wait after closing one special workspace before opening the next,
# so the exit animation is not covered by the incoming one sliding over it.
# Derived from OUT_SPEED to keep the two in step when you retune the speed.
OUT_DELAY=$(awk -v s="$OUT_SPEED" 'BEGIN { printf "%.2f", s / 10 }')

# Echoes "<in>|<out>" for a workspace name, empty if unknown.
styles_for() {
    printf '%s\n' "$ANIMATIONS" | awk -F'[:|]' -v key="$1" '$1 == key { print $2 "|" $3; exit }'
}

apply_leaf() {
    hyprctl eval "hl.animation({leaf=\"$1\", enabled=true, speed=$3, bezier=\"$4\", style=\"$2\"})" >/dev/null 2>&1
}

toggle() {
    hyprctl dispatch "hl.dsp.workspace.toggle_special(\"$1\")"
}

# Name of the special workspace currently open on the focused monitor, empty if none.
# Keys off the name, not the id: Hyprland gives special workspaces negative ids, and
# an id of 0 would read as falsy. "specialWorkspace" is "" when none is open.
current_special() {
    hyprctl monitors -j 2>/dev/null | python3 -c '
import json, sys
try:
    monitors = json.load(sys.stdin)
    monitor = next((m for m in monitors if m.get("focused")), monitors[0])
    special = monitor.get("specialWorkspace") or {}
    name = special.get("name") or "" if isinstance(special, dict) else ""
    if name:
        print(name)
except Exception:
    pass
'
}

# The workspace leaving, if any, gets its own out leaf. Also covers the plain
# close case (current == WORKSPACE): the script would otherwise rely on whatever
# leaf the last press happened to leave behind.
OUTGOING=$(current_special)
IN_STYLES=$(styles_for "$WORKSPACE")
if [ -z "$IN_STYLES" ]; then
    echo "special-toggle.sh: sem estilos para '$WORKSPACE'" >&2
    exit 1
fi

if [ -n "$OUTGOING" ]; then
    OUTGOING_STYLES=$(styles_for "${OUTGOING#special:}")
    if [ -n "$OUTGOING_STYLES" ]; then
        apply_leaf specialWorkspaceOut "${OUTGOING_STYLES#*|}" "$OUT_SPEED" "$OUT_BEZIER"
    fi
fi

# One dispatch per workspace, not one per keypress. A single toggle on a different
# workspace closes the open one and opens the target in the same event, so both
# animations start together and the incoming one hides the outgoing one. Closing
# first and waiting OUT_DELAY lets the exit finish before the entry begins.
if [ -n "$OUTGOING" ] && [ "$OUTGOING" != "special:$WORKSPACE" ]; then
    toggle "${OUTGOING#special:}"
    sleep "$OUT_DELAY"
fi

apply_leaf specialWorkspaceIn "${IN_STYLES%|*}" "$IN_SPEED" "$IN_BEZIER"
toggle "$WORKSPACE"
