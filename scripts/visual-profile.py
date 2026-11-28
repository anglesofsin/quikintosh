#!/usr/bin/env python3
"""Export only selected appearance preferences; preview or restore with backups."""
import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import re
import tempfile

SHELL_GROUPS = ['appearance','battery','dockAppearance','edges','general','glass','menuBar','notifications','performance','sound','topbar']
DROP = {'blurApplied','blurStatus','logoSource','logoText','recentAppBlacklist','stackPreferences'}
PREFS = {'accessibility':None, 'profile':['autoAppearance'],
         'notifications':['banners','previews','duration','sounds','sound','soundVolume'],
         'session':['autoLock','lockAfter']}
ROOT = '.config/lickintosh/'
ALLOWED = {ROOT+p for p in ['shell-config.json','rosa/island.json','rosa/config.json','core/settings-preferences.json','core/widgets.json','core/privacy-indicators.json']}
ALLOWED |= {'.local/state/quickintosh/island-shelf/utilities.json','.config/kitty/kitty.conf','.config/kitty/current-theme.conf'}
KITTY = {'background_opacity','dynamic_background_opacity','window_margin_width','single_window_margin_width','resize_draw_strategy','resize_debounce_time','confirm_os_window_close','font_size'}


def read(home,relative):
    try:
        value=json.loads((home/relative).read_text())
        return value if isinstance(value,dict) else {}
    except (OSError,ValueError):return {}


def select(data,keys):return {k:copy.deepcopy(data[k]) for k in keys if k in data}


def portable(value):
    """Never export source-local file paths, addresses, credentials or commands."""
    if isinstance(value,dict):return {k:portable(v) for k,v in value.items() if k not in DROP and not re.search(r'(?i)(?:password|secret|token|credential|authorization|api[_-]?key|private[_-]?key)',k)}
    if isinstance(value,list):return [portable(v) for v in value]
    if isinstance(value,str) and (re.search(r'(?:/home/|/tmp/|/nix/store/|://|~/)',value) or '\n' in value):
        return ''
    return value


def export(home):
    source=read(home,ROOT+'shell-config.json')
    shell=portable(select(source,SHELL_GROUPS))
    shell['wallpaper']=select(source.get('wallpaper',{}),['fit','dim','backgroundColor','videoEnabled','videoFps','videoHeight','videoPauseBattery','pauseFullscreen','pauseMaximized','transitionMs'])
    files={ROOT+'shell-config.json':{'json':shell}}
    island=read(home,ROOT+'rosa/island.json')
    files[ROOT+'rosa/island.json']={'json':portable({'style':island.get('style',{})})}
    cfg=read(home,ROOT+'rosa/config.json')
    files[ROOT+'rosa/config.json']={'json':select(cfg,['barPosition','cornerRadius','design','dockEnabled','fontDisplay','greetingEnabled','idleDimLeadSec','idleEnabled','idleLockSec','idleScreenOffSec','language','notifySound','osdStyle','polkitEnabled','sfxEnabled','sfxVolume','uiScale','weatherEnabled','widgetsEnabled'])}
    prefs=read(home,ROOT+'core/settings-preferences.json')
    safe={k:portable(prefs.get(k,{})) if keys is None else select(prefs.get(k,{}),keys) for k,keys in PREFS.items()}
    overrides=prefs.get('inputOverrides',{})
    safe['inputOverrides']={k:v for k,v in overrides.items() if k.startswith(('native-glass:','plugin:','qi-cursor:','workspace-animation:','input:','cursor:')) and portable(v)==v and not isinstance(v,(dict,list))}
    files[ROOT+'core/settings-preferences.json']={'json':safe}
    widgets=read(home,ROOT+'core/widgets.json')
    # Widget contents, file names and desktop icon positions are personal data.
    files[ROOT+'core/widgets.json']={'json':select(widgets,['allowCtrlFreePlacement','avoidDesktopIcons','desktopMenuMaterial','desktopSort','dimWidgets','iconSize','iconSpacing','showDesktopWidgets','showHidden','widgetMaterial','widgetStyle','widgetTint'])}
    privacy=read(home,ROOT+'core/privacy-indicators.json')
    files[ROOT+'core/privacy-indicators.json']={'json':select(privacy,['categories','controlCenter','enabled','hideFullscreen','island','showExpanded'])}
    utility=read(home,'.local/state/quickintosh/island-shelf/utilities.json')
    keys=['commandColumns','voiceLanguage','navigationShown','navigationWidgets','navigationTrayOnlyWithFiles','navigationGestures','navigationFavorites','ringCount','ringActions','selectionActionsEnabled','breaksEnabled','eyesMinutes','stretchMinutes','waterMinutes']
    files['.local/state/quickintosh/island-shelf/utilities.json']={'json':portable(select(utility,keys))}
    try:lines=(home/'.config/kitty/kitty.conf').read_text().splitlines()
    except OSError:lines=[]
    kitty=[line.strip() for line in lines if line.strip() and line.strip().split()[0] in KITTY]
    if kitty:
        files['.config/kitty/kitty.conf']={'text':'# Optional Quickintosh visual profile\n'+'\n'.join(kitty)+'\ninclude current-theme.conf\ninclude quickintosh-fonts.conf\n'}
        palette=[]
        try:
            for line in (home/'.config/kitty/current-theme.conf').read_text().splitlines():
                parts=line.split()
                if len(parts)==2 and re.fullmatch(r'[a-z_]+\d*',parts[0]) and re.fullmatch(r'#[0-9a-fA-F]{6}',parts[1]):palette.append(' '.join(parts))
        except OSError:pass
        files['.config/kitty/current-theme.conf']={'text':'\n'.join(palette)+'\n'}
    for entry in files.values():
        if 'json' in entry:entry['json']=portable(entry['json'])
    return {'schema':1,'description':'Optional sanitized visual preferences; excludes private content, wallpaper files and machine credentials.','files':files}


def merge(old,new):
    result=copy.deepcopy(old)
    for key,value in new.items():
        result[key]=merge(result.get(key,{}),value) if isinstance(value,dict) and isinstance(result.get(key,{}),dict) else value
    return result


def restore(profile,home,apply=False):
    if profile.get('schema')!=1 or not isinstance(profile.get('files'),dict):raise ValueError('Unsupported profile')
    plan=[]
    for relative,entry in profile['files'].items():
        if relative not in ALLOWED:raise ValueError('Unsupported destination: '+relative)
        path=home/relative
        # Refuse a parent symlink leading outside the chosen home.
        if not path.parent.resolve().is_relative_to(home.resolve()):raise ValueError('Destination parent escapes home')
        if set(entry)=={'json'} and isinstance(entry['json'],dict):
            content=json.dumps(merge(read(home,relative),entry['json']),ensure_ascii=False,indent=2)+'\n'
        elif set(entry)=={'text'} and isinstance(entry['text'],str):content=entry['text']
        else:raise ValueError('Invalid profile entry')
        plan.append((relative,path,content))
    if not apply:return [x[0] for x in plan],None
    backup=home/'.local/state/quickintosh/profile-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup.mkdir(parents=True,mode=0o700)
    for relative,path,content in plan:
        if path.exists():
            saved=backup/relative;saved.parent.mkdir(parents=True,exist_ok=True,mode=0o700);saved.write_bytes(path.read_bytes());saved.chmod(0o600)
        path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        fd,tmp=tempfile.mkstemp(dir=path.parent,prefix='.profile-')
        try:
            with os.fdopen(fd,'w') as stream:stream.write(content)
            Path(tmp).replace(path)
        finally:Path(tmp).unlink(missing_ok=True)
    return [x[0] for x in plan],str(backup)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['export','restore']);parser.add_argument('profile',type=Path)
    parser.add_argument('--home',type=Path,default=Path.home());parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if args.action=='export':
        args.profile.parent.mkdir(parents=True,exist_ok=True);args.profile.write_text(json.dumps(export(args.home),ensure_ascii=False,indent=2)+'\n');print('Exported sanitized visual profile:',args.profile)
    else:
        paths,backup=restore(json.loads(args.profile.read_text()),args.home,args.apply)
        print(('Applied' if args.apply else 'Preview only — use --apply to restore')+':\n'+'\n'.join(paths))
        if backup:print('Backup:',backup)

if __name__=='__main__':main()
