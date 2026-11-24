#!/usr/bin/env python3
import json
import os
import subprocess
import sys

HYPRCTL = "/run/current-system/sw/bin/hyprctl"
STATE_DIR = os.path.expanduser("~/.local/state/infinite-desktop")
CANVAS_TAG = "infinite-desktop-canvas"
MIN_ZOOM = 0.35
MAX_ZOOM = 2.5


def run(args, timeout=0.5):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def hypr_json(*args, fallback=None):
    try:
        return json.loads(run([HYPRCTL, *args]).stdout)
    except Exception:
        return fallback


def active_workspace():
    monitors = hypr_json("monitors", "-j", fallback=[]) or []
    monitor = next((m for m in monitors if m.get("focused")), monitors[0] if monitors else None)
    if monitor:
        sw = monitor.get("specialWorkspace") or {}
        if sw.get("id"):
            return sw["id"], sw.get("name") or str(sw["id"])
    ws = hypr_json("activeworkspace", "-j", fallback={}) or {}
    return ws.get("id"), str(ws.get("id", "unknown"))


def active_monitor():
    monitors = hypr_json("monitors", "-j", fallback=[]) or []
    return next((m for m in monitors if m.get("focused")), monitors[0] if monitors else {"x": 0, "y": 0, "width": 1920, "height": 1080})


def cursor_anchor():
    cursor = hypr_json("cursorpos", "-j", fallback=None)
    if cursor and "x" in cursor and "y" in cursor:
        return float(cursor["x"]), float(cursor["y"])
    mon = active_monitor()
    return mon["x"] + mon["width"] / 2, mon["y"] + mon["height"] / 2


def mode_for_key(key):
    try:
        with open(os.path.join(STATE_DIR, f"state-{key}")) as f:
            return f.read().strip()
    except Exception:
        return "tiled"


def state_path(key):
    return os.path.join(STATE_DIR, f"canvas-zoom-{key.replace('/', '_')}.json")


def managed_windows(ws_id):
    clients = hypr_json("clients", "-j", fallback=[]) or []
    return [
        w for w in clients
        if w.get("workspace", {}).get("id") == ws_id
        and w.get("floating")
        and w.get("fullscreen", 0) == 0
        and CANVAS_TAG in w.get("tags", [])
    ]


def save_state(path, zoom, windows):
    os.makedirs(STATE_DIR, exist_ok=True)
    if os.path.exists(path):
        try:
            with open(path) as f:
                saved = json.load(f)
        except Exception:
            saved = {}
    else:
        saved = {
            "base": [
                {"address": w["address"], "at": w.get("at", [0, 0]), "size": w.get("size", [960, 600])}
                for w in windows
            ]
        }
    saved["zoom"] = zoom
    with open(path, "w") as f:
        json.dump(saved, f)


def current_zoom(path):
    try:
        with open(path) as f:
            return float(json.load(f).get("zoom", 1.0))
    except Exception:
        return 1.0


def restore(path):
    try:
        with open(path) as f:
            saved = json.load(f)
    except Exception:
        return 0
    dispatch_geometry(saved.get("base", []))
    try:
        os.remove(path)
    except OSError:
        pass
    return 0


def dispatch_geometry(entries):
    if not entries:
        return
    lines = []
    for item in entries:
        addr = str(item["address"]).replace("\\", "\\\\").replace('"', '\\"')
        x, y = item["at"]
        w, h = item["size"]
        lines.append(f'hl.dispatch(hl.dsp.window.resize({{x = {int(w)}, y = {int(h)}, window = "address:{addr}"}}))')
        lines.append(f'hl.dispatch(hl.dsp.window.move({{x = {int(x)}, y = {int(y)}, window = "address:{addr}"}}))')
    run([HYPRCTL, "eval", "\n".join(lines)], timeout=2.0)


def zoom_windows(windows, factor):
    ax, ay = cursor_anchor()
    entries = []
    for w in windows:
        x, y = w.get("at", [0, 0])
        ww, wh = w.get("size", [960, 600])
        new_w = max(180, int(round(ww * factor)))
        new_h = max(120, int(round(wh * factor)))
        new_x = int(round(ax + (x - ax) * factor))
        new_y = int(round(ay + (y - ay) * factor))
        entries.append({"address": w["address"], "at": [new_x, new_y], "size": [new_w, new_h]})
    dispatch_geometry(entries)


def main():
    action = sys.argv[1] if len(sys.argv) > 1 else "in"
    ws_id, key = active_workspace()
    if not ws_id or mode_for_key(key) != "canvas":
        return 0
    path = state_path(key)
    if action == "reset":
        return restore(path)

    step = 1.12 if action == "in" else 1 / 1.12
    old_zoom = current_zoom(path)
    new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, old_zoom * step))
    if abs(new_zoom - old_zoom) < 0.001:
        return 0
    factor = new_zoom / old_zoom
    windows = managed_windows(ws_id)
    if not windows:
        return 0
    save_state(path, new_zoom, windows)
    zoom_windows(windows, factor)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
