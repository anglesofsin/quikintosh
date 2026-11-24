from pathlib import Path
import json,subprocess
home=Path.home();(home/'Pictures/Screenshots').mkdir(parents=True,exist_ok=True);config=home/'.config/eqsh';config.mkdir(parents=True,exist_ok=True);(config/'plugins').mkdir(exist_ok=True)
if not (config/'config.json').exists():
 wallpaper=''
 try:
  cache=json.loads((home/'.cache/noctalia-legacy/wallpapers.json').read_text())
  wallpaper=next(v['dark'] for v in cache.get('wallpapers',{}).values() if Path(v.get('dark','')).is_file())
 except (OSError,ValueError,StopIteration,KeyError):pass
 monitors=[]
 try:monitors=[m['name'] for m in json.loads(subprocess.check_output(['hyprctl','monitors','-j'],text=True))]
 except (OSError,ValueError,subprocess.SubprocessError):pass
 value={'general':{'language':'en_US'},'account':{'firstTimeRunning':False},
        'wallpaper':{'path':wallpaper,'folder':str(home/'Pictures/Wallpapers')},
        'dock':{'apps':['eq:launchpad','org.kde.dolphin','kitty','eq:settings']},
        'lockScreen':{'interactiveScreens':monitors,'mainScreen':monitors[0] if monitors else '', 'usageInfo':'Enter password'}}
 (config/'config.json').write_text(json.dumps(value,indent=2)+'\n');(config/'config.json').chmod(0o600)
for name,value in [('notifications.json',[]),('widgets.json',{'widgets':[]})]:
 path=config/name
 if not path.exists():path.write_text(json.dumps(value)+'\n')
