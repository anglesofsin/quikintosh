#!/usr/bin/env python3
"""Runtime adapter; graphical Nix programs get a GPU wrapper, not host executables."""
import json, os, shutil, subprocess, sys
from pathlib import Path

HOME=Path.home()
ROOT=HOME/'.local/share/quickintosh'
STATE=HOME/'.local/state/quickintosh-arch'

def environment(bundle):
    env=dict(os.environ)
    env['PATH']=str(ROOT/'bin')+':'+str(bundle/'runtime/bin')+':'+env.get('PATH','/usr/bin:/bin')
    env['RICE_SHELL_MANIFEST']=str(ROOT/'shells.json')
    env['RICE_CATALOG']=str(ROOT/'rices.json')
    env['RICE_SHELL_STATE_DIR']=str(STATE/'rice')
    env['QUICKINTOSH_BIN']=str(ROOT/'bin')
    env['LICKINTOSH_CLI']=str(ROOT/'bin/lickintosh')
    env['QUICKINTOSH_PLATFORM']='arch'
    env['QUICKINTOSH_ORIGINAL_LD_LIBRARY_PATH']=os.environ.get('QUICKINTOSH_ORIGINAL_LD_LIBRARY_PATH',os.environ.get('LD_LIBRARY_PATH',''))
    # GUI wrappers add their own Qt paths. Never mix Arch Qt plug-ins with Nix Qt.
    for key in ['QT_PLUGIN_PATH','QML_IMPORT_PATH','QML2_IMPORT_PATH','QT_QPA_PLATFORMTHEME']:
        env.pop(key,None)
    env['XDG_DATA_DIRS']=str(bundle/'runtime/share')+':'+env.get('XDG_DATA_DIRS','/usr/local/share:/usr/share')
    env['XDG_CURRENT_DESKTOP']='Quickintosh:Hyprland'
    env['XDG_SESSION_DESKTOP']='quickintosh'
    env['XDG_SESSION_TYPE']='wayland'
    env['QT_QPA_PLATFORM']='wayland'
    env['NIXOS_OZONE_WL']='1'
    env['MOZ_ENABLE_WAYLAND']='1'
    env['XCURSOR_PATH']=str(bundle/'runtime/share/icons')+':'+str(HOME/'.icons')+':/usr/share/icons'
    return env

def graphics_command(command, data):
    if not data.get('graphics'):return command
    directory=Path(data['graphics'])/'bin'
    choices=[directory/name for name in ['nixGLIntel','nixGLNvidia','nixGL'] if (directory/name).is_file()]
    if not choices:choices=list(directory.glob('nixGLNvidia-*'))
    if not choices:raise RuntimeError('GPU wrapper missing; reinstall with --graphics mesa/nvidia, or diagnose before choosing none')
    return [str(choices[0]),*command]

def main(argv):
    if not argv:raise RuntimeError('Command required')
    data=json.loads((STATE/'installation.json').read_text())
    bundle=Path(data['bundle']).resolve(strict=True)
    env=environment(bundle)
    name,*args=argv
    aliases={'quickintosh':'lickintosh','quickintosh-finder':'lickintosh-finder','quickintosh-quicklook':'lickintosh-quicklook'}
    name=aliases.get(name,name)
    if name=='quickintosh-doctor':
        checks={k:shutil.which(k,path=env['PATH']) for k in ['Hyprland','hyprctl','lickintosh','rice-shell','playerctl','matugen','grim','wl-copy']}
        status={'commands':checks,'bundle':str(bundle),'graphics':data.get('graphics'),
                'pam_lock':Path('/etc/pam.d/lickintosh-lock').is_file(),'session':os.environ.get('XDG_CURRENT_DESKTOP','')}
        print(json.dumps(status,indent=2));return 0 if all(checks.values()) else 1
    if name=='quickintosh-session':
        if args:raise RuntimeError('Session accepts no arguments')
        if os.environ.get('WAYLAND_DISPLAY') or os.environ.get('DISPLAY'):
            raise RuntimeError('Start from a TTY/display manager after leaving the current graphical session; it will not be replaced automatically')
        if not os.environ.get('DBUS_SESSION_BUS_ADDRESS'):
            os.execv('/usr/bin/dbus-run-session',['dbus-run-session','--',sys.executable,str(ROOT/'launcher.py'),'quickintosh-session'])
        command=graphics_command([str(bundle/'runtime/bin/Hyprland'),'--config',data['config']],data)
        try:return subprocess.call(command,env=env)
        finally:
            subprocess.run([str(ROOT/'bin/rice-shell'),'stop'],env=env,check=False)
            subprocess.run(['/usr/bin/systemctl','--user','stop','quickintosh-portal-hyprland.service'],check=False)
    if name=='quickintosh-session-ready':
        subprocess.run(['/usr/bin/systemctl','--user','daemon-reload'],env=env,check=False)
        agent=bundle/'runtime/libexec/polkit-gnome-authentication-agent-1'
        if agent.is_file():subprocess.Popen([str(agent)],env=env,start_new_session=True)
        subprocess.run(['/usr/bin/dbus-update-activation-environment','--systemd','WAYLAND_DISPLAY','XDG_CURRENT_DESKTOP','XDG_SESSION_DESKTOP','XDG_SESSION_TYPE','PATH'],env=env,check=False)
        subprocess.run(['/usr/bin/systemctl','--user','stop','xdg-desktop-portal-hyprland.service'],env=env,check=False)
        subprocess.run(['/usr/bin/systemctl','--user','start','quickintosh-portal-hyprland.service'],env=env,check=False)
        subprocess.run(['/usr/bin/systemctl','--user','restart','xdg-desktop-portal.service'],env=env,check=False)
        return 0
    target=bundle/'runtime/bin'/name
    if not target.is_file():raise RuntimeError('Command not included in this bundle: '+name)
    command=[str(target),*args]
    graphical=name in ['lickintosh','lickintosh-finder','rice-file-manager','kitty','noctalia','noctalia-legacy','caelestia','eqsh']
    if graphical and not (args and args[0] in ['ipc','list','log','--help','--version','brightness','settings-restore']):
        command=graphics_command(command,data)
    os.execvpe(command[0],command,env)
if __name__=='__main__':
    try:sys.exit(main(sys.argv[1:]))
    except (OSError,ValueError,RuntimeError) as error:print('Quickintosh: '+str(error),file=sys.stderr);sys.exit(1)
