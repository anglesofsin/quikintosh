"""Update corner rules in one transaction with the complete native glass registry."""
from pathlib import Path
import fcntl
import sys

def command(api, glass, radius, enabled, values, previous):
    if isinstance(radius, bool) or not isinstance(radius, int) or not 0 <= radius <= 24:
        raise ValueError('Invalid menu corner radius')
    if not isinstance(enabled, bool):
        raise ValueError('Invalid corner policy')
    # Even an empty profile set needs the baseline namespace/preset declarations:
    # Hyprland's successful eval commits hyprglass's pending registry wholesale.
    material = glass.commands(api, values, previous or ['baseline'])
    rule = "hl.window_rule({name='quickintosh-menubar-corners',enabled=" + ('true' if enabled else 'false') + ",match={tag='quickintosh-maximized'},rounding=" + str(radius) + "})"
    tag = "for _,w in ipairs(hl.get_windows()) do local m=w.monitor; if m and w.fullscreen==0 then local a=m.reserved; if math.abs(w.at.x-(m.x+a.left))<1 and math.abs(w.at.y-(m.y+a.top))<1 and math.abs(w.size.x-(m.mode.width-a.left-a.right))<1 and math.abs(w.size.y-(m.mode.height-a.top-a.bottom))<1 then local tagged=false;for _,t in ipairs(w.tags or {}) do if t=='quickintosh-maximized' then tagged=true end end;if not tagged then hl.dispatch(hl.dsp.window.tag({tag='+quickintosh-maximized',window='address:'..w.address})) end end end end"
    return material + ';' + rule + ';' + tag

def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'settingsapp'))
    import backend as api
    import native_glass as glass
    radius = int(sys.argv[1])
    if sys.argv[2] not in ('true', 'false'):
        raise ValueError('Invalid corner policy')
    api.STATE.mkdir(parents=True, exist_ok=True)
    with (api.STATE / 'runtime.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prefs = api.read_json(api.PREFERENCES).get('inputOverrides', {})
        values = {k:v for k,v in prefs.items() if k.startswith(glass.PREFIX)}
        previous = api.read_json(api.STATE / 'native-glass-runtime.json').get('targets', [])
        response = api.run(['hyprctl','eval',command(api,glass,radius,sys.argv[2]=='true',values,previous)])
        if 'error' in response.lower():
            raise RuntimeError(response)
if __name__ == '__main__':
    main()
