#!/run/current-system/sw/bin/bash
# Canvas-only zoom. Does nothing outside canvas mode.
exec python3 /home/pg/scripts/infinite_desktop_canvas_zoom.py "${1:-in}"
