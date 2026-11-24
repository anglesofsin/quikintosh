#!/bin/sh
if pgrep -f 'quickshell.*noctalia' >/dev/null 2>&1; then
  pkill -f 'quickshell.*noctalia' 2>/dev/null
else
  nohup noctalia-shell >/dev/null 2>&1 &
fi
