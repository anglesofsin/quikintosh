"""Add the default ring shortcut only when free; never overwrite user bindings."""
import json,os,subprocess

def ensure(runner=subprocess.run):
    if not os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):return False
    result=runner(['hyprctl','-j','binds'],capture_output=True,text=True,timeout=3)
    binds=json.loads(result.stdout)
    if any(b.get('description')=='Action Ring' for b in binds):return False
    if any(b.get('modmask')==72 and str(b.get('key','')).lower()=='r' for b in binds):return False
    script='hl.bind("SUPER + ALT + R",hl.dsp.exec_cmd("quickintosh ipc call actionRing show"),{description="Action Ring"}); hl.bind("SUPER + ALT + R",hl.dsp.exec_cmd("quickintosh ipc call actionRing release"),{description="Action Ring release",release=true})'
    result=runner(['hyprctl','eval',script],capture_output=True,text=True,timeout=3)
    return result.returncode==0
if __name__=='__main__':
    try:ensure()
    except (OSError,ValueError,subprocess.SubprocessError):pass
