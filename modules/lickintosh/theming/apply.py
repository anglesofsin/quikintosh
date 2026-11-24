"""Reuse the user's enabled Noctalia Legacy templates without starting its shell."""
from pathlib import Path
import json,tomllib,subprocess,sys,fcntl,hashlib,time,os

HOME=Path.home();STATE=HOME/'.local/state/lickintosh/theming';STATE.mkdir(parents=True,exist_ok=True)
SOURCE=Path(sys.argv[1]);image=Path(sys.argv[2]).expanduser();mode=sys.argv[3]
subprocess.run(['lickintosh-desktop-profile','mode',mode],check=True)
if not image.is_file():raise SystemExit('Wallpaper is not a readable image')
with (STATE/'apply.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 defaults=Path(__file__).resolve().parent.parent/'quickintosh-defaults'
 try:settings=json.loads((HOME/'.config/noctalia-legacy/settings.json').read_text())
 except FileNotFoundError:settings=json.loads((defaults/'theming-settings.json').read_text())
 enabled={t['id'] for t in settings.get('templates',{}).get('activeTemplates',[]) if t.get('enabled')}
 templates={};skipped=[]
 def read(path):
  try:return tomllib.loads(path.read_text()).get('templates',{})
  except FileNotFoundError:return {}
 for name,t in read(HOME/'.cache/noctalia-legacy/theming.dynamic.toml').items():
  if name!='noctalia' and (name.split('_')[0] in enabled):templates[name]=dict(t)
 if not templates:
  bundled=json.loads((defaults/'theming.json').read_text())
  zen=next(iter((HOME/'.config/zen').glob('*/chrome')),HOME/'.cache/quickintosh/zen/chrome')
  for name,t in bundled.items():
   templates[name]={k:v.replace('@HOME@',str(HOME)).replace('@LEGACY@',str(SOURCE)).replace('@DEFAULTS@',str(defaults)).replace('@ZEN_CHROME@',str(zen)) for k,v in t.items()}
 if settings.get('templates',{}).get('enableUserTheming'):templates.update(read(HOME/'.config/noctalia-legacy/user-templates.toml'))
 if 'discord' in enabled:
  for client in ['Vencord','Equicord','equibop','vesktop','BetterDiscord','vencord','VencordCanary','VencordPTB']:
   folder=HOME/'.config'/client/'themes'
   if folder.is_dir():
    for variant,file in [('midnight','noctalia.theme.css'),('material','noctalia-material.theme.css')]:
     templates['discord_'+client+'_'+variant]={'input_path':str(SOURCE/'Assets/Templates'/('discord-'+variant+'.css')),'output_path':str(folder/file)}
 if 'code' in enabled:
  for base in ['.vscode','.vscode-oss','.cursor','.antigravity-ide']:
   for output in (HOME/base/'extensions').glob('noctalia.noctaliatheme-*/themes/NoctaliaTheme-color-theme.json'):
    templates['code_'+hashlib.sha256(str(output).encode()).hexdigest()[:8]]={'input_path':str(SOURCE/'Assets/Templates/code.json'),'output_path':str(output)}
 valid={}
 for name,t in templates.items():
  if str(Path(t['output_path']).expanduser()) in [str(HOME/'.config/gtk-3.0/gtk.css'),str(HOME/'.config/gtk-4.0/gtk.css')]:continue
  old=Path(t['input_path']).expanduser()
  if '/Assets/Templates/' in str(old):t['input_path']=str(SOURCE/'Assets/Templates'/str(old).split('/Assets/Templates/',1)[1])
  if not Path(t['input_path']).expanduser().is_file():skipped.append(name+': missing input');continue
  target=Path(t['output_path']).expanduser()
  if target.is_symlink() and str(target.resolve()).startswith('/nix/store/'):
   skipped.append(name+': immutable output');continue
  target.parent.mkdir(parents=True,exist_ok=True)
  if name.startswith('gtk'):t.pop('post_hook',None)
  if 'post_hook' in t:
   hook=t['post_hook'];start=hook.find('/nix/store/');end=hook.find('/share/noctalia-shell/',start)
   if start>=0 and end>=0:hook=hook[:start]+str(SOURCE)+hook[end+len('/share/noctalia-shell'):]
   if name=='hyprland-borders':hook='true' # Lua color template above reloads the current compositor API.
   t['post_hook']=hook
  valid[name]=t
 method=settings.get('colorSchemes',{}).get('generationMethod','content')
 if method not in ['content','tonal-spot','fruit-salad','rainbow','monochrome','vibrant','faithful','dysfunctional','muted']:method='content'
 signature=hashlib.sha256((str(image.resolve())+str(image.stat().st_mtime_ns)+mode+method+json.dumps(valid,sort_keys=True)).encode()).hexdigest()
 statusfile=STATE/'status.json'
 try:previous=json.loads(statusfile.read_text())
 except (FileNotFoundError,ValueError):previous={}
 if previous.get('signature')==signature and previous.get('success') and all(Path(t['output_path']).expanduser().is_file() for t in valid.values()):raise SystemExit(0)
 lines=['[config]']
 for name,t in valid.items():
  lines+=['','[templates.'+json.dumps(name)+']']+[key+' = '+json.dumps(value) for key,value in t.items() if key in ['input_path','output_path','post_hook','pre_hook']]
 config=STATE/'templates.toml';config.write_text('\n'.join(lines)+'\n')
 paths=list(valid.values());backup=STATE/('backup-'+time.strftime('%Y%m%d-%H%M%S'));backup.mkdir(exist_ok=True)
 for i,t in enumerate(paths):
  p=Path(t['output_path']).expanduser()
  if p.is_file():(backup/str(i)).write_bytes(p.read_bytes())
 (backup/'manifest.json').write_text(json.dumps([t['output_path'] for t in paths],indent=2))
 command=[sys.executable,str(SOURCE/'Scripts/python/src/theming/template-processor.py'),str(image),'--scheme-type',method,'--config',str(config),'--default-mode',mode,'-o',str(STATE/'palette.json')]
 with (STATE/'apply.log').open('w') as log:
  result=subprocess.run(command,stdout=log,stderr=log,timeout=180)
 status={'success':result.returncode==0,'signature':signature,'wallpaper':str(image),'mode':mode,'method':method,'templates':list(valid),'skipped':skipped,'updated':time.time()}
 statusfile.write_text(json.dumps(status,indent=2));print(json.dumps(status))
 raise SystemExit(result.returncode)
