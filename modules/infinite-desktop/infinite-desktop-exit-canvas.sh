#!/usr/bin/env bash
systemctl --user stop infinite-desktop 2>/dev/null || true
exec python3 /home/pg/scripts/infinite_desktop_mode.py exit
