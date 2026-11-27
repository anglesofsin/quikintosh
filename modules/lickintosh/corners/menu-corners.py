"""Update corner rules without enqueueing or reloading native material profiles."""
from pathlib import Path
import fcntl
import sys

def command(radius, enabled):
    if isinstance(radius, bool) or not isinstance(radius, int) or not 0 <= radius <= 24:
        raise ValueError('Invalid menu corner radius')
    if not isinstance(enabled, bool):
        raise ValueError('Invalid corner policy')
    rule = "hl.window_rule({name='quickintosh-menubar-corners',enabled=" + ('true' if enabled else 'false') + ",match={tag='quickintosh-maximized'},rounding=" + str(radius) + "})"
    tag = "for _,w in ipairs(hl.get_windows()) do local m=w.monitor; if m and w.fullscreen<=1 then local a=m.reserved; if math.abs(w.at.x-(m.x+a.left))<1 and math.abs(w.at.y-(m.y+a.top))<1 and math.abs(w.size.x-(m.mode.width-a.left-a.right))<1 and math.abs(w.size.y-(m.mode.height-a.top-a.bottom))<1 then local tagged=false;for _,t in ipairs(w.tags or {}) do if t=='quickintosh-maximized' then tagged=true end end;if not tagged then hl.dispatch(hl.dsp.window.tag({tag='+quickintosh-maximized',window='address:'..w.address})) end end end end"
    return rule + ';' + tag

def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'settingsapp'))
    import backend as api
    radius = int(sys.argv[1])
    if sys.argv[2] not in ('true', 'false'):
        raise ValueError('Invalid corner policy')
    api.STATE.mkdir(parents=True, exist_ok=True)
    with (api.STATE / 'runtime.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        response = api.run(['hyprctl','eval',command(radius,sys.argv[2]=='true')])
        if 'error' in response.lower():
            raise RuntimeError(response)
if __name__ == '__main__':
    main()
