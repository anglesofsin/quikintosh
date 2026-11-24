#!/usr/bin/env python3
import sys, struct, threading, time, subprocess, json, os

EVENT_SIZE = struct.calcsize('llHHi')
EV_KEY=1; EV_REL=2; REL_X=0; REL_Y=1
BTN_LEFT=272

PERSISTENT_STATE_DIR = "/home/pg/.local/state/infinite-desktop"
OFFSET_FILE    = PERSISTENT_STATE_DIR + "/canvas-offset"
TMP_OFFSET_FILE = "/tmp/infinite-desktop-canvas-offset"
STATE_DIR      = "/tmp"
PAN_SIGNAL     = STATE_DIR + "/infinite-desktop-pan-mode"
CENTER_SIGNAL  = STATE_DIR + "/infinite-desktop-center-clicked"

HYPRCTL = "/run/current-system/sw/bin/hyprctl"
CANVAS_TAG = "infinite-desktop-canvas"

def get_ws_id():
    try:
        r = subprocess.run([HYPRCTL, 'monitors', '-j'], capture_output=True, text=True, timeout=0.2)
        ms = json.loads(r.stdout)
        m = next((x for x in ms if x.get('focused')), ms[0])
        sw = (m.get('specialWorkspace') or {}).get('id')
        if sw:
            return sw
    except Exception:
        pass
    r = subprocess.run([HYPRCTL, 'activeworkspace', '-j'], capture_output=True, text=True, timeout=0.2)
    return json.loads(r.stdout)['id']

def get_ws_state_key():
    try:
        r = subprocess.run([HYPRCTL, 'monitors', '-j'], capture_output=True, text=True, timeout=0.2)
        ms = json.loads(r.stdout)
        m = next((x for x in ms if x.get('focused')), ms[0])
        sw = m.get('specialWorkspace') or {}
        if sw.get('id'):
            return sw.get('name')
    except Exception:
        pass
    return str(get_ws_id())

lock=threading.Lock()
btn_left=False
acc_x=0.0; acc_y=0.0
is_panning=False
canvas_ox=0; canvas_oy=0
canvas_mode=False

drag_addr=""
mw=1920; mh=1080

def is_canvas_mode():
    try:
        ws_key = get_ws_state_key()
        with open(f"/home/pg/.local/state/infinite-desktop/state-{ws_key}") as f:
            return f.read().strip() == 'canvas'
    except:
        return False

def any_canvas_active():
    for fname in os.listdir("/home/pg/.local/state/infinite-desktop"):
        # Negative IDs are legacy special-workspace files. Their IDs are not
        # stable across sessions, so only named special files are authoritative.
        if fname.startswith("state-") and not fname.startswith("state--"):
            try:
                with open(os.path.join("/home/pg/.local/state/infinite-desktop", fname)) as f:
                    if f.read().strip() == 'canvas':
                        return True
            except:
                pass
    return False

def get_focus_addr():
    for fname in os.listdir(STATE_DIR):
        if fname.startswith("infinite-desktop-focus-"):
            try:
                with open(os.path.join(STATE_DIR, fname)) as f:
                    return json.load(f).get('address', '')
            except:
                pass
    return ''

def move_all_floating(dx, dy, exclude_addr=""):
    focus_addr = get_focus_addr()
    lua = (
        'local ws = hl.get_active_special_workspace() or hl.get_active_workspace()\n'
        'local skip = "{}"\n'
        'local focus = "{}"\n'
        'for _, v in ipairs(hl.get_workspace_windows(ws)) do\n'
        '  local managed = false\n'
        '  for _, tag in ipairs(v.tags) do\n'
        '    if tag == "{}" then managed = true end\n'
        '  end\n'
        '  if managed and v.floating and v.fullscreen == 0 and v.address ~= skip and v.address ~= focus then\n'
        '    hl.dispatch(hl.dsp.window.move({{x = {}, y = {}, relative = true, window = "address:" .. v.address}}))\n'
        '  end\n'
        'end\n'
    ).format(exclude_addr, focus_addr, CANVAS_TAG, dx, dy)
    subprocess.Popen([HYPRCTL, 'eval', lua],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def load_canvas_offset():
    for path in (OFFSET_FILE, TMP_OFFSET_FILE):
        try:
            with open(path) as f:
                parts = f.read().strip().split(',')
                return int(parts[0]), int(parts[1])
        except:
            pass
    return 0, 0

def save_canvas_offset(x, y):
    os.makedirs(PERSISTENT_STATE_DIR, exist_ok=True)
    for path in (OFFSET_FILE, TMP_OFFSET_FILE):
        try:
            with open(path, 'w') as f:
                f.write(f"{x},{y}")
        except:
            pass

def set_follow(val):
    subprocess.run([HYPRCTL, 'eval', 'hl.config({input={follow_mouse=' + str(val) + '}})'],
                   capture_output=True, timeout=0.2)

def start_pan():
    set_follow(0)
    global is_panning
    is_panning = True

def end_pan():
    global is_panning
    if is_panning:
        is_panning = False
        set_follow(1)

def move_view(dx, dy, exclude_addr=""):
    move_all_floating(dx, dy, exclude_addr)
    global canvas_ox, canvas_oy
    canvas_ox += dx
    canvas_oy += dy
    save_canvas_offset(canvas_ox, canvas_oy)

def signal_cleanup(prefix):
    for f in os.listdir(STATE_DIR):
        if f.startswith(prefix):
            try:
                os.remove(os.path.join(STATE_DIR, f))
            except:
                pass

def center_on_clicked_window():
    try:
        r = subprocess.run([HYPRCTL, 'cursorpos', '-j'], capture_output=True, text=True, timeout=0.2)
        cursor = json.loads(r.stdout)
        cxq, cyq = cursor['x'], cursor['y']
        r = subprocess.run([HYPRCTL, 'clients', '-j'], capture_output=True, text=True, timeout=0.2)
        clients = json.loads(r.stdout)
        ws_id = get_ws_id()
        target = None
        for w in clients:
            if w.get('workspace', {}).get('id') != ws_id: continue
            wx, wy = w.get('at', [0, 0])
            ww, wh = w.get('size', [0, 0])
            if wx <= cxq < wx + ww and wy <= cyq < wy + wh:
                target = w
                break
        if not target: return
        r = subprocess.run([HYPRCTL, 'monitors', '-j'], capture_output=True, text=True, timeout=0.2)
        monitors = json.loads(r.stdout)
        for m in monitors:
            if m.get('focused'):
                mw, mh = m['width'], m['height']
                wx, wy = target['at']
                ww, wh = target['size']
                dx = mw//2 - (wx + ww//2)
                dy = mh//2 - (wy + wh//2)
                move_view(dx, dy)
                return
    except:
        pass

def center_on_active_window():
    try:
        r = subprocess.run([HYPRCTL, 'activewindow', '-j'], capture_output=True, text=True, timeout=0.2)
        window = json.loads(r.stdout)
        r = subprocess.run([HYPRCTL, 'monitors', '-j'], capture_output=True, text=True, timeout=0.2)
        monitors = json.loads(r.stdout)
        for m in monitors:
            if m.get('focused'):
                mw, mh = m['width'], m['height']
                wx, wy = window['at']
                ww, wh = window['size']
                dx = mw//2 - (wx + ww//2)
                dy = mh//2 - (wy + wh//2)
                move_view(dx, dy)
                return
    except:
        pass

def mouse_reader():
    global acc_x, acc_y, btn_left, is_panning, drag_addr
    fd = open(mouse_dev, 'rb')
    while True:
        data = fd.read(EVENT_SIZE)
        if not data or len(data) < EVENT_SIZE:
            break
        _, _, etype, code, value = struct.unpack('llHHi', data)
        with lock:
            if etype == EV_KEY and code == BTN_LEFT:
                was = btn_left
                btn_left = (value == 1)
                if btn_left and not was:
                    try:
                        r = subprocess.run([HYPRCTL, 'activewindow', '-j'], capture_output=True, text=True, timeout=0.1)
                        drag_addr = json.loads(r.stdout).get('address', '')
                    except:
                        drag_addr = ''
                    if os.path.exists(CENTER_SIGNAL):
                        os.remove(CENTER_SIGNAL)
                        center_on_clicked_window()
                elif not btn_left and was and is_panning:
                    end_pan()
                elif not btn_left and was:
                    drag_addr = ''
            elif etype == EV_REL:
                if is_panning:
                    if code == REL_X:
                        acc_x += value * speed
                    elif code == REL_Y:
                        acc_y += value * speed

NEW_SIGNAL_DIR = STATE_DIR + "/infinite-desktop-new"

def center_new_windows():
    try:
        os.makedirs(NEW_SIGNAL_DIR, exist_ok=True)
        names = os.listdir(NEW_SIGNAL_DIR)
    except OSError:
        return
    for name in names:
        addr = name
        path = os.path.join(NEW_SIGNAL_DIR, name)
        try:
            os.remove(path)
        except OSError:
            continue
        lua = (
            'local mon = hl.get_active_monitor()\n'
            'local mw, mh = 1920, 1080\n'
            'if mon then\n'
            '  mw, mh = mon.width, mon.height\n'
            'end\n'
            'local ww = math.floor(mw * 0.7)\n'
            'local wh = math.floor(mh * 0.7)\n'
            'local cx = math.floor((mw - ww) / 2)\n'
            'local cy = math.floor((mh - wh) / 2)\n'
            'local f2 = io.open("/home/pg/.local/state/infinite-desktop/canvas-offset", "r") or io.open("/tmp/infinite-desktop-canvas-offset", "r")\n'
            'if f2 then\n'
            '  local content = f2:read("*all")\n'
            '  f2:close()\n'
            '  local ox, oy = content:match("([%d%-]+),([%d%-]+)")\n'
            '  if ox and oy then\n'
            '    cx = cx - tonumber(ox)\n'
            '    cy = cy - tonumber(oy)\n'
            '  end\n'
            'end\n'
            'local a = "{}"\n'
            'hl.dispatch(hl.dsp.window.float({{action = "enable", window = "address:" .. a}}))\n'
            'hl.dispatch(hl.dsp.window.resize({{x = ww, y = wh, window = "address:" .. a}}))\n'
            'hl.dispatch(hl.dsp.window.move({{x = cx, y = cy, window = "address:" .. a}}))\n'
        ).format(addr)
        subprocess.run([HYPRCTL, 'eval', lua], capture_output=True, timeout=1.0)

def auto_float_thread():
    global canvas_mode
    while True:
        canvas_mode = is_canvas_mode()
        if canvas_mode:
            try:
                lua = (
                    'local ws = hl.get_active_special_workspace() or hl.get_active_workspace()\n'
                    'for _, v in ipairs(hl.get_workspace_windows(ws)) do\n'
                    '  if not v.floating and v.fullscreen == 0 then\n'
                    '    hl.dispatch(hl.dsp.window.tag({tag = "+infinite-desktop-canvas", window = "address:" .. v.address}))\n'
                    '    hl.dispatch(hl.dsp.window.float({action = "enable", window = "address:" .. v.address}))\n'
                    '  end\n'
                    'end\n'
                )
                subprocess.run([HYPRCTL, 'eval', lua], capture_output=True, timeout=1.0)
                center_new_windows()
            except:
                pass
        time.sleep(0.5)

if len(sys.argv) < 3:
    print("Usage: infinite_desktop_core.py <mouse_dev> <speed>", file=sys.stderr)
    sys.exit(1)

mouse_dev = sys.argv[1]
speed     = float(sys.argv[2])

canvas_ox, canvas_oy = load_canvas_offset()

try:
    r = subprocess.run([HYPRCTL, 'monitors', '-j'], capture_output=True, text=True, timeout=0.2)
    for m in json.loads(r.stdout):
        if m.get('focused'):
            mw, mh = m['width'], m['height']
except:
    pass

canvas_mode = is_canvas_mode()

import signal, atexit
def log_exit(signum=None, frame=None):
    sig = signum if signum else "clean"
    with open("/tmp/infinite-desktop-exit.log", "a") as f:
        f.write(f"EXIT signal={sig} at {time.time()}\n")
    os._exit(0)
atexit.register(log_exit)
signal.signal(signal.SIGTERM, log_exit)
signal.signal(signal.SIGHUP, log_exit)
signal.signal(signal.SIGINT, log_exit)

def heartbeat_thread():
    while True:
        time.sleep(1)
        try:
            open("/tmp/infinite-desktop-heartbeat", "w").close()
        except:
            pass

threading.Thread(target=mouse_reader, daemon=True).start()
threading.Thread(target=auto_float_thread, daemon=True).start()
threading.Thread(target=heartbeat_thread, daemon=True).start()

idle_frames = 0
while True:
    time.sleep(0.016)
    try:
        with lock:
            active_drag = is_panning
            dx = acc_x
            dy = acc_y
            acc_x = 0.0
            acc_y = 0.0
        if active_drag:
            idx = int(round(dx))
            idy = int(round(dy))
            if idx != 0 or idy != 0:
                move_view(idx, idy, "")
        if os.path.exists(PAN_SIGNAL):
            try:
                os.remove(PAN_SIGNAL)
            except:
                pass
            if not is_panning:
                start_pan()
        if any_canvas_active() and os.path.exists(STATE_DIR + "/infinite-desktop-center-active"):
            try:
                os.remove(STATE_DIR + "/infinite-desktop-center-active")
            except:
                pass
            center_on_active_window()
    except Exception as e:
        import traceback
        with open("/tmp/infinite-desktop-crash.log", "a") as f:
            f.write(f"CRASH at {time.time()}: {e}\n{traceback.format_exc()}\n")
