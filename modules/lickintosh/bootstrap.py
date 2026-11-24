"""Seed only a missing Lickintosh config; preserve all subsequent user edits."""
import json
from pathlib import Path
import sys

home = Path.home()
config = home / '.config/lickintosh/shell-config.json'
if not config.exists():
    wallpaper = Path(sys.argv[1])
    try:
        cached = json.loads((home / '.cache/noctalia-legacy/wallpapers.json').read_text())
        for screen in cached.get('wallpapers', {}).values():
            candidate = Path(screen.get('dark', ''))
            if candidate.is_file():
                wallpaper = candidate
                break
    except (OSError, ValueError, TypeError):
        pass
    pinned = [
        ('Launchpad', '__launchpad__', ''), ('Finder', 'lickintosh-finder', 'system-file-manager'),
        ('Terminal', 'kitty', 'kitty'), ('Zen', 'zen', 'zen-browser'),
        ('Settings', '', 'preferences-system'),
    ]
    config.parent.mkdir(parents=True, exist_ok=True)
    with config.open('x') as stream:
        json.dump({'wallpaper': {'path': str(wallpaper)},
                   'dock': {'pinnedApps': [dict(name=name, cmd=cmd, icon=icon, iconPath='', autostart=False)
                                            for name, cmd, icon in pinned]}}, stream)
    config.chmod(0o600)

# Migrate upstream's default spelling while preserving custom directories.
wallpapers = home / 'Pictures/Wallpapers'
if wallpapers.is_dir():
    data = json.loads(config.read_text())
    indexing = data.setdefault('spotlight', {}).setdefault('indexing', {})
    if indexing.get('wallpaperDir', '~/Pictures/wallpapers') in (
        '~/Pictures/wallpapers', '~/Pictures/wallpaper',
        str(home / 'Pictures/wallpapers'), str(home / 'Pictures/wallpaper'),
    ):
        indexing['wallpaperDir'] = '~/Pictures/Wallpapers'
        temporary = config.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=4) + '\n')
        temporary.chmod(0o600)
        temporary.replace(config)

# Screenshot defaults moved to the desktop; custom save locations stay intact.
data = json.loads(config.read_text())
capture = data.setdefault('capture', {})
if capture.get('directory', '~/Pictures/Screenshots') in ('~/Pictures/Screenshots', str(home / 'Pictures/Screenshots')):
    capture['directory'] = '~/Desktop'
    temporary = config.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=4) + '\n')
    temporary.chmod(0o600)
    temporary.replace(config)

# Replace only the former default file manager within this shell's private Dock.
for path in [config,home/'.config/lickintosh/dock/dock-state.json']:
    if not path.exists(): continue
    data=json.loads(path.read_text()); changed=False
    apps=data.get('dock',{}).get('pinnedApps',[]) if path==config else data.get('pinnedApps',[])
    for app in apps:
        if app.get('cmd')=='dolphin' and app.get('name') in ['Finder','Dolphin']:
            app.update(name='Finder',cmd='lickintosh-finder');changed=True
    if changed:
        temporary=path.with_suffix('.tmp');temporary.write_text(json.dumps(data,ensure_ascii=False,indent=2));temporary.chmod(0o600);temporary.replace(path)
