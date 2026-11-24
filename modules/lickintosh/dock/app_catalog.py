"""Resolve window identities only against installed, visible desktop applications."""
import configparser
import os
from pathlib import Path
import shlex
import shutil
import time


def identity(value):
    value=str(value or '').strip().casefold()
    return value[:-8] if value.endswith('.desktop') else value


class AppCatalog:
    def __init__(self, roots=None):
        home=Path.home()
        defaults=[Path(os.environ.get('XDG_DATA_HOME',home/'.local/share'))]
        defaults += [Path(p) for p in os.environ.get('XDG_DATA_DIRS','/usr/local/share:/usr/share').split(':') if p]
        defaults += [home/'.nix-profile/share', Path('/run/current-system/sw/share'),
                     home/'.local/share/flatpak/exports/share', Path('/var/lib/flatpak/exports/share')]
        self.roots=list(dict.fromkeys(Path(p)/'applications' for p in (roots if roots is not None else defaults)))
        self.aliases={};self.signature=None;self.updated=-100

    def refresh(self):
        signature=[]
        for root in self.roots:
            try:signature.append((str(root),root.stat().st_mtime_ns))
            except OSError:signature.append((str(root),None))
        if signature==self.signature and time.monotonic()-self.updated<60:return
        self.signature=signature;self.updated=time.monotonic();aliases={};seen=set()
        for root in self.roots:
            if not root.is_dir():continue
            for path in sorted(root.rglob('*.desktop')):
                desktop_id=str(path.relative_to(root)).replace(os.sep,'-')
                if desktop_id in seen:continue
                seen.add(desktop_id)
                try:
                    parser=configparser.ConfigParser(interpolation=None,strict=False)
                    parser.read(path,encoding='utf-8');entry=parser['Desktop Entry']
                    if entry.get('Type')!='Application' or entry.getboolean('Hidden',False) or entry.getboolean('NoDisplay',False):continue
                    command=shlex.split(entry.get('Exec',''))
                    if not command:continue
                    executable=command[0]
                    if Path(executable).name=='env':
                        rest=[part for part in command[1:] if not part.startswith('-') and '=' not in part]
                        if not rest:continue
                        executable=rest[0]
                    check=entry.get('TryExec',executable)
                    if not shutil.which(check):continue
                    key=desktop_id[:-8]
                    app={'key':key,'desktopId':desktop_id,'name':entry.get('Name',key),'icon':entry.get('Icon','')}
                    if identity(key)=='org.gnome.nautilus':app['name']='Finder'
                    names=[key,entry.get('StartupWMClass',''),Path(executable).name]
                    for name in names:
                        if name:aliases.setdefault(identity(name),app)
                except (OSError,ValueError,configparser.Error):continue
        self.aliases=aliases

    def sanitize(self, rows):
        self.refresh();result=[];seen=set()
        if not isinstance(rows,list):return result
        for row in rows:
            if not isinstance(row,dict):continue
            app=self.aliases.get(identity(row.get('desktopId') or row.get('key')))
            if not app or app['desktopId'] in seen:continue
            seen.add(app['desktopId'])
            key=str(row.get('key') or app['key'])
            if self.aliases.get(identity(key),{}).get('desktopId')!=app['desktopId']:key=app['key']
            result.append(dict(app,key=key,icon=app['icon'] or row.get('icon','')))
        return result
