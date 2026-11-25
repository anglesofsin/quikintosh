from pathlib import Path
import json,sys
r=Path(sys.argv[1]);here=Path(__file__).parent
def write(name,text):
 p=r/name
 if p.exists():p.chmod(p.stat().st_mode|0o200)
 p.write_text(text)
write('settingsapp/hyprimate-settings.json',(here/'hyprimate-settings.json').read_text())
write('settingsapp/compositor_policy.py',(here/'options.py').read_text())
p='settingsapp/backend.py';s=(r/p).read_text();s=s.replace('INPUTS = {','import compositor_policy\nINPUTS = {',1);at=s.index('\n\n\ndef run(');s=s[:at]+'\nINPUTS.update(compositor_policy.OPTIONS | compositor_policy.HYPRIMATE_OPTIONS)\n'+s[at:]
s=s.replace('def query(page, args=None):','def query(page, args=None):\n    if page == "compositor": return compositor_policy.query(sys.modules[__name__])',1)
s=s.replace("    if name == 'runtime':\n        runtime(args.get('values', {}))", "    if name == 'compositor-rules':\n        return compositor_policy.save_rules(sys.modules[__name__],args.get('rules',[]))\n    if name == 'runtime':\n        runtime(args.get('values', {}))\n        compositor_policy.apply_rules(sys.modules[__name__])",1)
s=s.replace("    STATE.mkdir(parents=True, exist_ok=True)\n    with (STATE/'runtime.lock')", "    native = {key.removeprefix(compositor_policy.NATIVE_PREFIX): value for key, value in (values or {}).items() if key.startswith(compositor_policy.NATIVE_PREFIX)}\n    native_windows = {key: value for key, value in (values or {}).items() if key.startswith(compositor_policy.WINDOW_PREFIX)}\n    values = {key: value for key, value in (values or {}).items() if not key.startswith((compositor_policy.NATIVE_PREFIX,compositor_policy.WINDOW_PREFIX))}\n    STATE.mkdir(parents=True, exist_ok=True)\n    with (STATE/'runtime.lock')",1)
s=s.replace("        path = STATE/'runtime.json'", "        compositor_policy.apply_native_workspace(sys.modules[__name__],native,restore)\n        compositor_policy.apply_native_windows(sys.modules[__name__],native_windows,restore)\n        path = STATE/'runtime.json'",1)
s=s.replace('        if restore:\n            apply_options', '        if restore:\n            compositor_policy.apply_rules(sys.modules[__name__],restore=True)\n            apply_options',1)
s=s.replace("['bool', 'int', 'float', 'str']", "['bool', 'int', 'float', 'str', 'css']")
s=s.replace("    spec = INPUTS[key]", "    spec = INPUTS[key]\n    if key in {'general:gaps_in','general:gaps_out'} and isinstance(value,str) and re.fullmatch(r'[0-9 ]{1,40}',value) and 1 <= len(value.split()) <= 4 and all(0 <= int(n) <= spec[2] for n in value.split()):\n        return value",1)
s=s.replace("branch[parts[-1]] = value", "branch[parts[-1]] = compositor_policy.option_value(key,value)",1)
s=s.replace("    if spec[0] == 'bool':", """    if spec[0] == 'plugin-color':
        if not ((isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 0xffffffff)
                or (isinstance(value, str) and re.fullmatch(r'(?:#|0x)?[0-9a-fA-F]{8}', value))):
            raise ValueError('Enter eight hexadecimal ARGB digits.')
    elif spec[0] == 'plugin-set':
        if not isinstance(value, str) or not set(value.replace(',', ' ').split()) <= set(spec[1]) | {'all'}:
            raise ValueError('Unsupported animation sides.')
    elif spec[0] == 'plugin-text':
        if not isinstance(value, str) or len(value) > 4096 or any(ord(c) < 32 for c in value):
            raise ValueError('Invalid animation setting.')
    elif spec[0] == 'bool':""",1)
s=s.replace("            apply_options(dict(removed, **values))", "            desired = dict(removed, **values)\n            changes = {key: value for key, value in desired.items() if not compositor_policy.equivalent(key, current.get(key), value)}\n            apply_options(changes)",1)
s=s.replace("        for key in values:\n", "        values = {key: value for key, value in values.items() if not key.startswith('plugin:') or current.get(key) is not None}\n        for key in values:\n",1)
s=s.replace("if k not in values}", "if k not in values and current.get(k) is not None}",1)
s=s.replace("            apply_options(record['original'])", "            live_plugins = input_values(key for key in record['original'] if key.startswith('plugin:'))\n            apply_options({key: value for key, value in record['original'].items() if not key.startswith('plugin:') or live_plugins.get(key) is not None})",1)
write(p,s)
write('settingsapp/CompositorPage.qml'  ,(here/'CompositorPage.qml').read_text())
p='settingsapp/qmldir';write(p,(r/p).read_text()+'\nCompositorPage CompositorPage.qml\n')
p='settingsapp/catalog.json';data=json.loads((r/p).read_text());data.append({'id':'compositor','title':'Windows & Effects','icon':'display.svg','group':3,'keywords':'hyprland blur transparency opacity shadow rounding gaps layout compositor liquid kitty'})
write(p,json.dumps(data,indent=2))
p='settings.qml';s=(r/p).read_text();needle="source:!window.page ? '':";assert needle in s,'Settings loader route changed'
s=s.replace(needle,"source:window.route==='compositor' ? Quickshell.shellDir+'/settingsapp/CompositorPage.qml':!window.page ? '':",1);write(p,s)
