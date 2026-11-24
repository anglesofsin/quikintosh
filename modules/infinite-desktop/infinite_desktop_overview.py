#!/usr/bin/env python3
import json
import math
import os
import subprocess
import sys

STATE_DIR = os.path.expanduser("~/.local/state/infinite-desktop")
CANVAS_TAG = "infinite-desktop-canvas"
HYPRCTL = "/run/current-system/sw/bin/hyprctl"


def run(args, timeout=0.5):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def hypr_json(*args, fallback=None):
    try:
        result = run([HYPRCTL, *args])
        return json.loads(result.stdout)
    except Exception:
        return fallback


def active_workspace():
    monitors = hypr_json("monitors", "-j", fallback=[]) or []
    monitor = next((m for m in monitors if m.get("focused")), monitors[0] if monitors else None)
    if monitor:
        sw = monitor.get("specialWorkspace") or {}
        if sw.get("id"):
            return {"id": sw["id"], "key": sw.get("name") or str(sw["id"])}
    ws = hypr_json("activeworkspace", "-j", fallback={}) or {}
    return {"id": ws.get("id"), "key": str(ws.get("id", "unknown"))}


def active_monitor():
    monitors = hypr_json("monitors", "-j", fallback=[]) or []
    return next((m for m in monitors if m.get("focused")), monitors[0] if monitors else {"x": 0, "y": 0, "width": 1920, "height": 1080})


def managed_windows(ws_id):
    clients = hypr_json("clients", "-j", fallback=[]) or []
    windows = []
    for window in clients:
        if window.get("workspace", {}).get("id") != ws_id:
            continue
        if window.get("fullscreen", 0) != 0:
            continue
        if CANVAS_TAG not in window.get("tags", []):
            continue
        windows.append(window)
    return windows


def state_path(key):
    safe = key.replace("/", "_")
    return os.path.join(STATE_DIR, f"canvas-overview-{safe}.json")


def mode_for_key(key):
    try:
        with open(os.path.join(STATE_DIR, f"state-{key}")) as f:
            return f.read().strip()
    except Exception:
        return "tiled"


def exit_focus_mode(key):
    for name in (f"infinite-desktop-focus-{key}",):
        path = os.path.join("/tmp", name)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass


def lua_escape(value):
    return str(value).replace("\\", "\\\\").replace('"', '\\"')


def dispatch_geometry(entries):
    if not entries:
        return
    lines = []
    for item in entries:
        addr = lua_escape(item["address"])
        x, y = item["at"]
        w, h = item["size"]
        lines.append(f'hl.dispatch(hl.dsp.window.resize({{x = {int(w)}, y = {int(h)}, window = "address:{addr}"}}))')
        lines.append(f'hl.dispatch(hl.dsp.window.move({{x = {int(x)}, y = {int(y)}, window = "address:{addr}"}}))')
    run([HYPRCTL, "eval", "\n".join(lines)], timeout=2.0)


def restore(path):
    try:
        with open(path) as f:
            saved = json.load(f)
    except Exception:
        return 1
    dispatch_geometry(saved.get("windows", []))
    try:
        os.remove(path)
    except OSError:
        pass
    return 0


def overview_layout(windows, monitor):
    count = len(windows)
    if count == 0:
        return []
    margin = 46
    gap = 22
    columns = max(1, math.ceil(math.sqrt(count * monitor["width"] / max(1, monitor["height"]))))
    rows = max(1, math.ceil(count / columns))
    cell_w = max(240, (monitor["width"] - margin * 2 - gap * (columns - 1)) / columns)
    cell_h = max(160, (monitor["height"] - margin * 2 - gap * (rows - 1)) / rows)
    entries = []
    for index, window in enumerate(windows):
        ww, wh = window.get("size", [960, 600])
        scale = min(cell_w / max(1, ww), cell_h / max(1, wh), 0.72)
        new_w = max(280, int(ww * scale))
        new_h = max(180, int(wh * scale))
        col = index % columns
        row = index // columns
        x = int(monitor["x"] + margin + col * (cell_w + gap) + (cell_w - new_w) / 2)
        y = int(monitor["y"] + margin + row * (cell_h + gap) + (cell_h - new_h) / 2)
        entries.append({"address": window["address"], "at": [x, y], "size": [new_w, new_h]})
    return entries


def enter(path, key, ws_id):
    windows = managed_windows(ws_id)
    if not windows:
        return 0
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump({
            "key": key,
            "windows": [
                {"address": w["address"], "at": w.get("at", [0, 0]), "size": w.get("size", [960, 600])}
                for w in windows
            ],
        }, f)
    exit_focus_mode(key)
    dispatch_geometry(overview_layout(windows, active_monitor()))
    return 0


def main():
    ws = active_workspace()
    key = ws["key"]
    ws_id = ws["id"]
    if not ws_id or mode_for_key(key) != "canvas":
        return 0
    path = state_path(key)
    action = sys.argv[1] if len(sys.argv) > 1 else "toggle"
    if action == "enter":
        return enter(path, key, ws_id)
    if action == "exit":
        return restore(path) if os.path.exists(path) else 0
    if action == "toggle":
        return restore(path) if os.path.exists(path) else enter(path, key, ws_id)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
