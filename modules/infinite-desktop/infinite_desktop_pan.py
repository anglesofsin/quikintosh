#!/usr/bin/env python3
import json
import os
import subprocess
import sys

STATE_DIR = os.path.expanduser("~/.local/state/infinite-desktop")
OFFSET_FILE = os.path.join(STATE_DIR, "canvas-offset")
TMP_OFFSET_FILE = "/tmp/infinite-desktop-canvas-offset"
CANVAS_TAG = "infinite-desktop-canvas"


def load_offset():
    for path in (OFFSET_FILE, TMP_OFFSET_FILE):
        try:
            with open(path) as f:
                x, y = f.read().strip().split(",", 1)
                return int(x), int(y)
        except Exception:
            pass
    return 0, 0


def save_offset(x, y):
    os.makedirs(STATE_DIR, exist_ok=True)
    for path in (OFFSET_FILE, TMP_OFFSET_FILE):
        try:
            with open(path, "w") as f:
                f.write(f"{x},{y}")
        except Exception:
            pass


def focus_addr():
    try:
        for name in os.listdir("/tmp"):
            if name.startswith("infinite-desktop-focus-"):
                with open(os.path.join("/tmp", name)) as f:
                    return json.load(f).get("address", "")
    except Exception:
        pass
    return ""


def main():
    dx = int(float(sys.argv[1])) if len(sys.argv) > 1 else 0
    dy = int(float(sys.argv[2])) if len(sys.argv) > 2 else 0
    skip_focus = focus_addr()
    lua = f'''
local ws = hl.get_active_special_workspace() or hl.get_active_workspace()
local focus = "{skip_focus}"
for _, v in ipairs(hl.get_workspace_windows(ws)) do
  local managed = false
  for _, tag in ipairs(v.tags) do
    if tag == "{CANVAS_TAG}" then managed = true end
  end
  if managed and v.floating and v.fullscreen == 0 and v.address ~= focus then
    hl.dispatch(hl.dsp.window.move({{x = {dx}, y = {dy}, relative = true, window = "address:" .. v.address}}))
  end
end
'''
    subprocess.run(["hyprctl", "eval", lua], capture_output=True, timeout=1.0)
    ox, oy = load_offset()
    save_offset(ox + dx, oy + dy)


if __name__ == "__main__":
    main()
