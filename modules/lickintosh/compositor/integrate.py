from pathlib import Path
import json,sys
r=Path(sys.argv[1]);here=Path(__file__).parent
def write(name,text):
 p=r/name
 if p.exists():p.chmod(p.stat().st_mode|0o200)
 p.write_text(text)
write('settingsapp/compositor_policy.py',(here/'options.py').read_text())
p='settingsapp/backend.py';s=(r/p).read_text();s=s.replace('INPUTS = {','import compositor_policy\nINPUTS = {',1);at=s.index('\n\n\ndef run(');s=s[:at]+'\nINPUTS.update(compositor_policy.OPTIONS)\n'+s[at:]
s=s.replace('def query(page, args=None):','def query(page, args=None):\n    if page == "compositor": return compositor_policy.query(sys.modules[__name__])',1)
s=s.replace("    if name == 'runtime':\n        runtime(args.get('values', {}))", "    if name == 'compositor-rules':\n        return compositor_policy.save_rules(sys.modules[__name__],args.get('rules',[]))\n    if name == 'runtime':\n        runtime(args.get('values', {}))\n        compositor_policy.apply_rules(sys.modules[__name__])",1)
s=s.replace('        if restore:\n            apply_options', '        if restore:\n            compositor_policy.apply_rules(sys.modules[__name__],restore=True)\n            apply_options',1)
s=s.replace("['bool', 'int', 'float', 'str']", "['bool', 'int', 'float', 'str', 'css']")
s=s.replace("    spec = INPUTS[key]", "    spec = INPUTS[key]\n    if key in {'general:gaps_in','general:gaps_out'} and isinstance(value,str) and re.fullmatch(r'[0-9 ]{1,40}',value) and 1 <= len(value.split()) <= 4 and all(0 <= int(n) <= spec[2] for n in value.split()):\n        return value",1)
s=s.replace("branch[parts[-1]] = value", "branch[parts[-1]] = compositor_policy.option_value(key,value)",1)
write(p,s)
write('settingsapp/CompositorPage.qml'  ,(here/'CompositorPage.qml').read_text())
p='settingsapp/qmldir';write(p,(r/p).read_text()+'\nCompositorPage CompositorPage.qml\n')
p='settingsapp/catalog.json';data=json.loads((r/p).read_text());data.append({'id':'compositor','title':'Windows & Effects','icon':'display.svg','group':3,'keywords':'hyprland blur transparency opacity shadow rounding gaps layout compositor liquid kitty'})
write(p,json.dumps(data,indent=2))
p='settings.qml';s=(r/p).read_text();needle="source:!window.page ? '':";assert needle in s,'Settings loader route changed'
s=s.replace(needle,"source:window.route==='compositor' ? Quickshell.shellDir+'/settingsapp/CompositorPage.qml':!window.page ? '':",1);write(p,s)
