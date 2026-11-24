#!/run/current-system/sw/bin/bash
# Toggle a simulated zoomed-out overview for the active canvas workspace.
exec python3 /home/pg/scripts/infinite_desktop_overview.py "${1:-toggle}"
