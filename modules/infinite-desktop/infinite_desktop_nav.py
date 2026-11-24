import subprocess, json, sys, os

direction = sys.argv[1] if len(sys.argv) > 1 else 'right'
HYPRCTL = '/run/current-system/sw/bin/hyprctl'
STATE_DIR = '/home/pg/.local/state/infinite-desktop'
OFFSET_FILE = os.path.join(STATE_DIR, 'canvas-offset')
TMP_OFFSET_FILE = '/tmp/infinite-desktop-canvas-offset'
CANVAS_TAG = 'infinite-desktop-canvas'

def exit_focus_mode(ws_key):
    fname = f"/tmp/infinite-desktop-focus-{ws_key}"
    if not os.path.exists(fname):
        return
    try:
        with open(fname) as f:
            d = json.load(f)
    except Exception:
        os.remove(fname)
        return
    addr = d.get('address')
    at, size = d.get('at'), d.get('size')
    if addr and at and size:
        lua = (
            f'hl.dispatch(hl.dsp.window.resize({{x = {size[0]}, y = {size[1]}, window = "address:{addr}"}}))\n'
            f'hl.dispatch(hl.dsp.window.move({{x = {at[0]}, y = {at[1]}, window = "address:{addr}"}}))'
        )
        subprocess.run(['hyprctl', 'eval', lua], capture_output=True, timeout=0.5)
    os.remove(fname)

def get_center():
    r = subprocess.run([HYPRCTL, 'monitors', '-j'], capture_output=True, text=True, timeout=0.2)
    for m in json.loads(r.stdout):
        if m.get('focused', False):
            return m['x'] + m['width'] // 2, m['y'] + m['height'] // 2
    m = json.loads(r.stdout)[0]
    return m['x'] + m['width'] // 2, m['y'] + m['height'] // 2

def get_ws():
    try:
        r = subprocess.run([HYPRCTL, 'monitors', '-j'], capture_output=True, text=True, timeout=0.2)
        ms = json.loads(r.stdout)
        m = next((x for x in ms if x.get('focused')), ms[0])
        sw = m.get('specialWorkspace') or {}
        if sw.get('id'):
            return sw.get('id'), sw.get('name') or str(sw.get('id'))
    except Exception:
        pass
    r = subprocess.run([HYPRCTL, 'activeworkspace', '-j'], capture_output=True, text=True, timeout=0.2)
    ws_id = json.loads(r.stdout)['id']
    return ws_id, str(ws_id)

def has_canvas_tag(w):
    return CANVAS_TAG in w.get('tags', [])

def load_offset():
    for path in (OFFSET_FILE, TMP_OFFSET_FILE):
        try:
            with open(path) as f:
                x, y = f.read().strip().split(',', 1)
                return int(x), int(y)
        except Exception:
            pass
    return 0, 0

def save_offset(x, y):
    os.makedirs(STATE_DIR, exist_ok=True)
    for path in (OFFSET_FILE, TMP_OFFSET_FILE):
        try:
            with open(path, 'w') as f:
                f.write(f'{x},{y}')
        except Exception:
            pass

ws_id, ws_key = get_ws()
exit_focus_mode(ws_key)
r2 = subprocess.run([HYPRCTL, 'clients', '-j'], capture_output=True, text=True, timeout=0.2)
clients = json.loads(r2.stdout)
floating = [
    w for w in clients
    if w.get('floating')
    and w.get('workspace', {}).get('id') == ws_id
    and has_canvas_tag(w)
    and w.get('fullscreen', 0) == 0
]
if len(floating) <= 1:
    sys.exit(0)

r3 = subprocess.run([HYPRCTL, 'activewindow', '-j'], capture_output=True, text=True, timeout=0.2)
focused = json.loads(r3.stdout) if r3.stdout else None
cur_addr = focused.get('address') if focused else None

if not cur_addr:
    target = floating[0]
    target_addr = target['address']
    subprocess.run([HYPRCTL, 'eval', f'hl.dispatch(hl.dsp.focus({{ window = "address:{target_addr}" }}))'],
                   capture_output=True, timeout=0.5)
    sys.exit(0)

cur = None
for w in floating:
    if w['address'] == cur_addr:
        cur = w
        break
if not cur:
    cur = floating[0]

cx = cur['at'][0] + cur['size'][0] // 2
cy = cur['at'][1] + cur['size'][1] // 2

best = None
best_score = float('inf')

for w in floating:
    if w['address'] == cur['address']:
        continue
    wx = w['at'][0] + w['size'][0] // 2
    wy = w['at'][1] + w['size'][1] // 2

    dx = wx - cx
    dy = wy - cy

    if direction == 'right':
        if dx <= 0: continue
    elif direction == 'left':
        if dx >= 0: continue
    elif direction == 'up':
        if dy >= 0: continue
    elif direction == 'down':
        if dy <= 0: continue
    else:
        sys.exit(0)

    if direction in ('right', 'left'):
        cur_top, cur_bot = cur['at'][1], cur['at'][1] + cur['size'][1]
        w_top, w_bot = w['at'][1], w['at'][1] + w['size'][1]
        overlap = max(0, min(cur_bot, w_bot) - max(cur_top, w_top))
        if overlap > 0:
            dist = abs(dx)
        else:
            gap = max(w_top - cur_bot, cur_top - w_bot, 0)
            dist = abs(dx) + gap * 10
    else:
        cur_l, cur_r = cur['at'][0], cur['at'][0] + cur['size'][0]
        w_l, w_r = w['at'][0], w['at'][0] + w['size'][0]
        overlap = max(0, min(cur_r, w_r) - max(cur_l, w_l))
        if overlap > 0:
            dist = abs(dy)
        else:
            gap = max(w_l - cur_r, cur_l - w_r, 0)
            dist = abs(dy) + gap * 10

    if dist < best_score:
        best_score = dist
        best = w

if not best:
    idx = -1
    for i, w in enumerate(floating):
        if w['address'] == cur['address']:
            idx = i
            break
    if idx == -1:
        idx = 0
    if direction in ('right', 'down'):
        new_idx = (idx + 1) % len(floating)
    else:
        new_idx = (idx - 1) % len(floating)
    target = floating[new_idx]
    best = target

target = best
cx_mon, cy_mon = get_center()
tx = target['at'][0] + target['size'][0] // 2
ty = target['at'][1] + target['size'][1] // 2
dx = int(cx_mon - tx)
dy = int(cy_mon - ty)

mon_w, mon_h = 1920, 1080
for m in json.loads(subprocess.run([HYPRCTL, 'monitors', '-j'], capture_output=True, text=True, timeout=0.2).stdout):
    if m.get('focused', False):
        mon_w, mon_h = m['width'], m['height']
        break
dx = max(-mon_w * 2, min(mon_w * 2, dx))
dy = max(-mon_h * 2, min(mon_h * 2, dy))

target_addr = target['address']
lua = (
    f'local ws = hl.get_active_special_workspace() or hl.get_active_workspace()\n'
    f'for _, v in ipairs(hl.get_workspace_windows(ws)) do\n'
    f'  local managed = false\n'
    f'  for _, tag in ipairs(v.tags) do\n'
    f'    if tag == "{CANVAS_TAG}" then managed = true end\n'
    f'  end\n'
    f'  if managed and v.floating and v.fullscreen == 0 then\n'
    f'    hl.dispatch(hl.dsp.window.move({{x = {dx}, y = {dy}, relative = true, window = "address:" .. v.address}}))\n'
    f'  end\n'
    f'end\n'
    f'hl.dispatch(hl.dsp.focus({{ window = "address:{target_addr}" }}))\n'
)
subprocess.run([HYPRCTL, 'eval', lua], capture_output=True, timeout=0.5)
ox, oy = load_offset()
save_offset(ox + dx, oy + dy)
