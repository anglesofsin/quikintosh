#!/usr/bin/env bash
# Reset canvas offset to 0,0 by moving canvas-managed windows back.
exec python3 -c "
import subprocess, os

offset_paths = [
    '/home/pg/.local/state/infinite-desktop/canvas-offset',
    '/tmp/infinite-desktop-canvas-offset',
]
ox = oy = 0
for path in offset_paths:
    try:
        with open(path) as f:
            ox, oy = f.read().strip().split(',')
            ox, oy = int(ox), int(oy)
            break
    except Exception:
        pass

if ox == 0 and oy == 0:
    exit(0)

lua = (
    'local ws = hl.get_active_special_workspace() or hl.get_active_workspace()\\n'
    'for _, v in ipairs(hl.get_workspace_windows(ws)) do\\n'
    '  local managed = false\\n'
    '  for _, tag in ipairs(v.tags) do\\n'
    '    if tag == \"infinite-desktop-canvas\" then managed = true end\\n'
    '  end\\n'
    '  if managed and v.floating and v.fullscreen == 0 then\\n'
    '    hl.dispatch(hl.dsp.window.move({{x = {}, y = {}, relative = true, window = \"address:\" .. v.address}}))\\n'
    '  end\\n'
    'end\\n'
).format(-ox, -oy)

subprocess.run(['hyprctl', 'eval', lua], capture_output=True, timeout=0.5)

os.makedirs('/home/pg/.local/state/infinite-desktop', exist_ok=True)
for path in offset_paths:
    try:
        with open(path, 'w') as f:
            f.write('0,0')
    except Exception:
        pass
"
