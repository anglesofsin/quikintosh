"""Add the default ring shortcut only when free; never overwrite user bindings."""
import json,os,re,subprocess
from pathlib import Path

def binding():
    key='SUPER + ALT + R'
    file=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))/'lickintosh/core/shortcuts.tsv'
    try:
        for line in file.read_text().splitlines():
            if line.startswith('Action Ring\t'):key=line.split('\t',1)[1]
    except OSError:pass
    parts=[part.strip().upper() for part in key.split('+')]
    mods={'SUPER':64,'CTRL':4,'CONTROL':4,'ALT':8,'SHIFT':1}
    if len(parts)<2 or any(part not in mods for part in parts[:-1]) or not re.fullmatch(r'[A-Z0-9_:-]{1,32}',parts[-1]):return 'SUPER + ALT + R',72,'R'
    mask=0
    for part in parts[:-1]:mask |= mods[part]
    return ' + '.join(parts),mask,parts[-1]

def ensure(runner=subprocess.run):
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):return False
    result=runner(['hyprctl','-j','binds'],capture_output=True,text=True,timeout=3)
    binds=json.loads(result.stdout)
    if any(b.get('description')=='Action Ring' for b in binds):return False
    chord,mask,key=binding()
    if any(b.get('modmask')==mask and str(b.get('key','')).upper()==key for b in binds):return False
    script='hl.bind('+json.dumps(chord)+',hl.dsp.exec_cmd("quickintosh ipc call actionRing show"),{description="Action Ring"}); hl.bind('+json.dumps(chord)+',hl.dsp.exec_cmd("quickintosh ipc call actionRing release"),{description="Action Ring release",release=true})'
    result=runner(['hyprctl','eval',script],capture_output=True,text=True,timeout=3)
    return result.returncode==0
if __name__=='__main__':
    try:ensure()
    except (OSError,ValueError,subprocess.SubprocessError):pass
