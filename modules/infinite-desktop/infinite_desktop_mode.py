import subprocess, json, os, sys, time

from workspace_identity import workspace_identity

STATE_DIR = os.path.expanduser("~/.local/state/infinite-desktop")
POS_DIR = os.path.join(STATE_DIR, "canvas-positions")
OFFSET_FILE = os.path.join(STATE_DIR, "canvas-offset")
TMP_OFFSET_FILE = "/tmp/infinite-desktop-canvas-offset"
STATE_FILE = "/tmp/infinite-desktop-state"
SAVE_FILE = "/tmp/infinite-desktop-canvas-saved-opts"
CANVAS_TAG = "infinite-desktop-canvas"

def canvas_managed(client):
    return CANVAS_TAG in client.get('tags', [])

def get_active_workspace():
    try:
        r = subprocess.run(['hyprctl', 'monitors', '-j'], capture_output=True, text=True, timeout=0.2)
        ms = json.loads(r.stdout)
        m = next((x for x in ms if x.get('focused')), ms[0])
        sw = m.get('specialWorkspace') or {}
        if sw.get('name'):
            # Keep the stable name for persistence and the runtime identity for selection.
            return {'id': workspace_identity(sw), 'name': sw['name'], 'special': True}
    except Exception:
        pass
    r = subprocess.run(['hyprctl', 'activeworkspace', '-j'], capture_output=True, text=True, timeout=0.2)
    ws = json.loads(r.stdout)
    ws['special'] = False
    return ws

def get_clients():
    r = subprocess.run(['hyprctl', 'clients', '-j'], capture_output=True, text=True, timeout=0.2)
    return json.loads(r.stdout)

def get_monitor():
    r = subprocess.run(['hyprctl', 'monitors', '-j'], capture_output=True, text=True, timeout=0.2)
    for m in json.loads(r.stdout):
        if m.get('focused', False):
            return m
    return json.loads(r.stdout)[0]

def get_option_str(key):
    r = subprocess.run(['hyprctl', 'getoption', key, '-j'], capture_output=True, text=True, timeout=0.3)
    return json.loads(r.stdout)

def run_lua(lines):
    if lines:
        subprocess.run(['hyprctl', 'eval', '\n'.join(lines)], capture_output=True, timeout=2.0)

def set_lua_cfg(cfg_str):
    subprocess.run(['hyprctl', 'eval', f'hl.config({{{cfg_str}}})'],
                   capture_output=True, timeout=0.5)

def pos_file_for_ws(ws_key):
    safe_key = ws_key.replace('/', '_').replace(':', '_')
    return os.path.join(POS_DIR, f"canvas-positions-{safe_key}.json")

def load_saved_positions(ws_key):
    path = pos_file_for_ws(ws_key)
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}

def save_saved_positions(ws_key, positions):
    os.makedirs(POS_DIR, exist_ok=True)
    path = pos_file_for_ws(ws_key)
    try:
        with open(path, 'w') as f:
            json.dump(positions, f)
    except:
        pass

def save_canvas_offset(x, y):
    os.makedirs(STATE_DIR, exist_ok=True)
    for path in (OFFSET_FILE, TMP_OFFSET_FILE):
        try:
            with open(path, 'w') as f:
                f.write(f"{x},{y}")
        except:
            pass

def enter_canvas():
    os.makedirs(STATE_DIR, exist_ok=True)
    os.makedirs(POS_DIR, exist_ok=True)
    save_canvas_offset(0, 0)

    # Drop any stale focus-mode state
    for fname in os.listdir('/tmp'):
        if fname.startswith('infinite-desktop-focus-'):
            try:
                os.remove(os.path.join('/tmp', fname))
            except:
                pass

    # Save and override settings for canvas mode
    try:
        opts = {
            'inactive_opacity': get_option_str('decoration:inactive_opacity').get('float', 0.9),
        }
        with open(SAVE_FILE, 'w') as f:
            json.dump(opts, f)
    except:
        pass
    set_lua_cfg('decoration={inactive_opacity=1.0}')

    # Save global border-off state before canvas disables everything
    with open('/tmp/infinite-desktop-border-off.json', 'w') as f:
        import json as _json
        _json.dump(os.path.exists('/tmp/borders-off-global'), f)

    ws = get_active_workspace()
    ws_id = ws['id']
    # Use stable name for special workspaces, numeric ID for regular
    ws_key = ws['name'] if ws.get('special') else str(ws_id)
    clients = get_clients()
    mon = get_monitor()

    # Load saved canvas positions for THIS workspace
    saved = load_saved_positions(ws_key)

    # Count windows on workspace
    ws_windows = [
        c for c in clients
        if workspace_identity(c.get('workspace', {})) == ws_id
        and c.get('fullscreen', 0) == 0
        and (not c.get('floating') or canvas_managed(c))
    ]
    n = len(ws_windows)
    if n == 0:
        return

    # Default window size
    if n <= 4:
        default_h = int(mon['height'] * 0.7)
    elif n <= 8:
        default_h = int(mon['height'] * 0.55)
    else:
        default_h = int(mon['height'] * 0.45)
    default_w = int(mon['width'] * 0.7)

    # Grid with no overlap
    cols = max(2, int(n ** 0.5))
    pw = min(mon['width'] // cols - 40, default_w)
    ph = default_h
    step_x = pw + 20
    step_y = ph + 60

    pos_entries = []
    for i, c in enumerate(ws_windows):
        addr = c['address']
        sp = saved.get(addr)
        if sp:
            px, py = sp['at']
            pw2, ph2 = sp['size']
            pos_entries.append(f'  ["{addr}"] = {{x={px}, y={py}, w={pw2}, h={ph2}}}')
        else:
            col = i % cols
            row = i // cols
            px = mon['x'] + col * step_x + 20
            py = mon['y'] + row * step_y + 20
            pos_entries.append(f'  ["{addr}"] = {{x={px}, y={py}, w={pw}, h={ph}}}')

    pos_table = "{ " + ",\n".join(pos_entries) + " }"

    # Single pass: float + position together (no sleep = no flicker)
    lua = (
        f'local ws = hl.get_active_special_workspace() or hl.get_active_workspace()\n'
        f'local targets = {pos_table}\n'
        f'for _, v in ipairs(hl.get_workspace_windows(ws)) do\n'
        f'  local addr = v.address\n'
        f'  local t = targets[addr]\n'
        f'  if t then\n'
        f'    if not v.floating and v.fullscreen == 0 then\n'
        f'      hl.dispatch(hl.dsp.window.tag({{tag = "+{CANVAS_TAG}", window = "address:" .. addr}}))\n'
        f'      hl.dispatch(hl.dsp.window.float({{action = "enable", window = "address:" .. addr}}))\n'
        f'    end\n'
        f'    hl.dispatch(hl.dsp.window.move({{x = t.x, y = t.y, window = "address:" .. addr}}))\n'
        f'    hl.dispatch(hl.dsp.window.resize({{x = t.w, y = t.h, window = "address:" .. addr}}))\n'
        f'    hl.dispatch(hl.dsp.window.set_prop({{prop = "border_size", value = 0, window = "address:" .. addr}}))\n'
        f'  end\n'
        f'end\n'
    )
    run_lua([lua])

    # Save current positions for this workspace
    clients_after = get_clients()
    positions = {}
    for c in clients_after:
        if canvas_managed(c) and workspace_identity(c.get('workspace', {})) == ws_id:
            positions[c['address']] = {'at': c['at'], 'size': c['size']}
    save_saved_positions(ws_key, positions)

def exit_canvas():
    # Restore saved settings
    try:
        with open(SAVE_FILE) as f:
            saved = json.load(f)
        if 'inactive_opacity' in saved:
            set_lua_cfg(f'decoration={{inactive_opacity={saved["inactive_opacity"]}}}')
    except:
        set_lua_cfg('decoration={inactive_opacity=0.9}')

    # Restore per-window canvas mode properties
    gbs = get_option_str('general:border_size').get('int', 0)
    run_lua([f'''
local ws = hl.get_active_special_workspace() or hl.get_active_workspace()
for _, v in ipairs(hl.get_workspace_windows(ws)) do
  local managed = false
  for _, tag in ipairs(v.tags) do
    if tag == "{CANVAS_TAG}" then managed = true end
  end
  if managed then
    hl.dispatch(hl.dsp.window.set_prop({{prop = "decorate", value = 1, window = "address:" .. v.address}}))
    hl.dispatch(hl.dsp.window.set_prop({{prop = "border_size", value = {gbs}, window = "address:" .. v.address}}))
  end
end
'''])

    # Re-disable borders globally if they were off before canvas mode
    try:
        with open('/tmp/infinite-desktop-border-off.json') as f:
            import json as _json2
            borders_were_off = _json2.load(f)
    except:
        borders_were_off = False
    if borders_were_off:
        subprocess.run(['hyprctl', 'eval', 'hl.config({general={border_size=0}})'], capture_output=True, timeout=0.2)

    ws = get_active_workspace()
    ws_id = ws['id']
    # Use stable name for special workspaces
    ws_key = ws['name'] if ws.get('special') else str(ws_id)
    clients = get_clients()

    # Save current floating positions for THIS workspace
    floating = [
        c for c in clients
        if canvas_managed(c) and workspace_identity(c.get('workspace', {})) == ws_id
    ]
    positions = {c['address']: {'at': c['at'], 'size': c['size']} for c in floating}
    save_saved_positions(ws_key, positions)

    # Return only the windows owned by canvas to tiled mode
    lua = (
        f'local ws = hl.get_active_special_workspace() or hl.get_active_workspace()\n'
        f'for _, v in ipairs(hl.get_workspace_windows(ws)) do\n'
        f'  local managed = false\n'
        f'  for _, tag in ipairs(v.tags) do\n'
        f'    if tag == "{CANVAS_TAG}" then managed = true end\n'
        f'  end\n'
        f'  if managed then\n'
        f'    hl.dispatch(hl.dsp.window.float({{action = "disable", window = "address:" .. v.address}}))\n'
        f'    hl.dispatch(hl.dsp.window.tag({{tag = "-{CANVAS_TAG}", window = "address:" .. v.address}}))\n'
        f'  end\n'
        f'end\n'
    )
    run_lua([lua])

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'enter'
    if action == 'enter':
        enter_canvas()
    else:
        exit_canvas()
