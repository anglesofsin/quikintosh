"""Install the metadata addon in existing mods, preserving their complete contents.
No client is restarted. Equibop uses its supported state.equicordDir setting.
"""
from pathlib import Path
import json,os,shutil,struct,time,subprocess,tempfile
BASE=Path(__file__).parent
ADDON='\n'+(BASE/'discord-bridge.js').read_text()
MARKER='__lickintoshVoiceBridge'
BACKUP=Path.home()/'.local/state/nixos-rice/voice-backup'/time.strftime('%Y%m%d-%H%M%S')

def backup(path):
    target=BACKUP/path.relative_to(Path.home()) if path.is_relative_to(Path.home()) else BACKUP/'system'/path.relative_to('/')
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)

def append(path):
    text=path.read_text()
    if MARKER in text:
        start=text.find('\n/* Lickintosh voice metadata only.')
        if start < 0: raise RuntimeError('Existing voice addon has an unfamiliar layout')
        updated=text[:start]+ADDON
        if updated==text: return False
    else: updated=text+ADDON
    backup(path);path.write_text(updated);return True

def unpack(archive,dest):
    with archive.open('rb') as f:
        head=f.read(16); _,size,_,length=struct.unpack('<4I',head)
        header=json.loads(f.read(length)); start=8+size
        def walk(files,parent):
            for name,entry in files.items():
                if name in ('.','..') or '/' in name or '\\' in name: raise ValueError('Unsafe archive entry')
                target=parent/name
                if 'files' in entry: target.mkdir(parents=True,exist_ok=True);walk(entry['files'],target)
                elif 'link' in entry: raise ValueError('Linked archive entries are unsupported')
                else:
                    target.parent.mkdir(parents=True,exist_ok=True)
                    if entry.get('unpacked'): shutil.copy2(Path(str(archive)+'.unpacked')/target.relative_to(dest),target)
                    else:
                        f.seek(start+int(entry['offset'])); target.write_bytes(f.read(entry['size']))
        walk(header['files'],dest)

def managed_clients():
    # Discover only currently running managed Discord installs, without reading args/environment.
    resources=set()
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit(): continue
        try: exe=(proc/'exe').resolve(strict=True)
        except (OSError,RuntimeError): continue
        if '/clients/' not in str(exe) or 'Discord' not in exe.name: continue
        directory=exe.parent/'resources'
        if (directory/'bootstrap/manifest.json').exists(): resources.add(directory)
    if not resources: return
    addon=Path.home()/'.local/share/lickintosh/discord-voice'
    addon.mkdir(parents=True,exist_ok=True)
    for name in ('main-hook.cjs','discord-bridge.js'): shutil.copy2(BASE/name,addon/name)
    modules=Path.home()/'Shade/ShadeSelfbot/node_modules/.pnpm'
    asar=next(modules.glob('@electron+asar*/node_modules/@electron/asar/lib/asar.js'),None)
    if asar is None: raise RuntimeError('Electron ASAR packager is unavailable for the Shade companion')
    for directory in resources:
        archive=directory/'app.asar'
        with tempfile.TemporaryDirectory(prefix='lickintosh-discord-') as temp:
            temp=Path(temp); unpack(archive,temp/'app')
            index=temp/'app/index.js';code=index.read_text()
            if 'lickintosh-voice-companion' in code: continue
            if not code.startswith('// Selfbot managed integration v1'):
                raise RuntimeError('Unrecognized managed client entry point; not modified')
            index.write_text(code+'\n// lickintosh-voice-companion\nrequire('+json.dumps(str(addon/'main-hook.cjs'))+');\n')
            output=temp/'app.asar'
            js="import(process.argv[1]).then(asar=>asar.createPackage(process.argv[2],process.argv[3]))"
            subprocess.run(['node','--input-type=module','-e',js,str(asar),str(temp/'app'),str(output)],check=True)
            backup(archive)
            replacement=archive.with_suffix('.voice.tmp');shutil.copy2(output,replacement);replacement.replace(archive)
        print('Shade managed client: companion installed, original bootstrap retained (restart required)')

def main():
    managed_clients()
    desktop=Path('/etc/equicord/desktop/renderer.js')
    if desktop.exists() and os.access(desktop,os.W_OK):
        append(desktop);print('Discord mod: addon installed (client reload required)')
    else: print('Discord mod: managed by Nix; addon applied at the next system activation')
    config=Path.home()/'.config/equibop'; state=config/'state.json'
    if not state.exists(): return
    data=json.loads(state.read_text()); current=Path(data.get('equicordDir',''))/'equibop'
    dest=Path.home()/'.local/share/lickintosh/discord-mod/equibop'
    if current.is_dir() and (current/'renderer.js').exists():
        # Keep the currently chosen build including all existing user plugins.
        dest=current
    elif not (dest/'renderer.js').exists():
        unpack(config/'sessionData/equicord.asar',dest)
    append(dest/'renderer.js')
    if data.get('equicordDir')!=str(dest.parent):
        backup(state);data['equicordDir']=str(dest.parent)
        temp=state.with_suffix('.voice.tmp');temp.write_text(json.dumps(data,indent=2));temp.replace(state)
    print('Equibop mod: addon installed (client restart required)')
if __name__=='__main__': main()
