"""Seed a new Quickintosh installation; never replace existing settings."""
from pathlib import Path
import json, sys
source=Path(sys.argv[1]); home=Path.home()
for file,target in [('shell-config.json',home/'.config/lickintosh/shell-config.json'),('island.json',home/'.config/lickintosh/rosa/island.json')]:
    if target.exists(): continue
    data=json.loads((source/file).read_text())
    if file=='shell-config.json':
        data['wallpaper']={'path':sys.argv[2]}
        data['capture']['directory']='~/Desktop'
        data['dock']={'pinnedApps':[
            {'name':name,'cmd':cmd,'icon':icon,'iconPath':'','autostart':False}
            for name,cmd,icon in [('Launchpad','__launchpad__',''),('Finder','lickintosh-finder','system-file-manager'),('Terminal','kitty','kitty'),('Settings','','preferences-system')]]}
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('x') as out:json.dump(data,out,indent=2)
    target.chmod(0o600)
