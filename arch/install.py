#!/usr/bin/env python3
"""Arch activation: an isolated, backed-up user installation of the pinned Nix bundle."""
import argparse, datetime, hashlib, json, os, platform, re, shlex, shutil, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NIX = ['nix', '--extra-experimental-features', 'nix-command flakes']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def read_os(path=Path('/etc/os-release')):
    return dict(line.split('=', 1) for line in path.read_text().splitlines() if '=' in line and not line.startswith('#'))

def doctor(home, require_arch=True):
    osinfo = read_os()
    arch = 'arch' in (osinfo.get('ID', '')+' '+osinfo.get('ID_LIKE', '')).replace('"', '').split()
    checks = {'arch_linux': arch, 'x86_64': platform.machine() == 'x86_64',
              'nix': bool(shutil.which('nix')), 'python3': bool(shutil.which('python3')),
              'dbus_session': bool(os.environ.get('DBUS_SESSION_BUS_ADDRESS')),
              'pam_lock': Path('/etc/pam.d/lickintosh-lock').is_file(),
              'system_portal': bool(shutil.which('xdg-desktop-portal') or Path('/usr/lib/xdg-desktop-portal').exists()),
              'pipewire_session': bool(os.environ.get('XDG_RUNTIME_DIR') and Path(os.environ['XDG_RUNTIME_DIR'],'pipewire-0').exists())}
    checks['services']={name:subprocess.run(['systemctl','is-active','--quiet',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0 for name in ['NetworkManager','bluetooth','upower']} if shutil.which('systemctl') else {}
    fatal = ['x86_64','nix','python3'] + (['arch_linux'] if require_arch else [])
    print(json.dumps({'checks': checks, 'home': str(home), 'fatal_missing': [k for k in fatal if not checks[k]],
                      'note': 'D-Bus, PipeWire, PAM and GPU need checking in the real login session.'}, indent=2))
    return not any(not checks[k] for k in fatal)

class Activation:
    def __init__(self, home):
        self.home = home.resolve()
        self.root = self.home/'.local/share/quickintosh'
        self.state = self.home/'.local/state/quickintosh-arch'
        self.record = self.state/'installation.json'
        self.data = json.loads(self.record.read_text()) if self.record.exists() else {'files': {}}
        self.stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
        self.backup = self.state/'backups'/self.stamp

    def save(self):
        self.state.mkdir(parents=True, exist_ok=True)
        temporary = self.record.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.data,indent=2)+'\n'); temporary.chmod(0o600); temporary.replace(self.record)

    def put(self, path, content, executable=False):
        """Remember the original once; updates never overwrite that first backup."""
        if not path.is_relative_to(self.home): raise ValueError('User activation cannot write outside home')
        key = str(path)
        if key not in self.data['files']:
            original = None
            if path.is_symlink(): original = {'link': os.readlink(path)}
            elif path.exists():
                if not path.is_file(): raise ValueError('Refusing non-file target: '+key)
                self.backup.mkdir(parents=True,exist_ok=True)
                dest = self.backup/str(len(self.data['files']))
                shutil.copy2(path,dest); original = {'backup':str(dest)}
            self.data['files'][key] = {'original':original}
        elif path.exists() and digest(path) != self.data['files'][key].get('sha256'):
            raise ValueError('Managed file was edited; preserve/reconcile it before updating: '+key)
        if getattr(self,'undo',None) is not None and key not in self.undo:
            self.undo[key] = {'link':os.readlink(path)} if path.is_symlink() else {'data':path.read_bytes(),'mode':path.stat().st_mode & 0o777} if path.exists() else None
        path.parent.mkdir(parents=True,exist_ok=True)
        tmp = path.with_name(path.name+'.quickintosh-tmp')
        tmp.write_text(content); tmp.chmod(0o755 if executable else 0o644); tmp.replace(path)
        self.data['files'][key]['sha256'] = digest(path)
        self.save()

    def activate(self, bundle, graphics=None):
        previous=json.loads(json.dumps(self.data)); self.undo={}
        try:self._activate(bundle,graphics)
        except Exception:
            for name,value in reversed(list(self.undo.items())):
                path=Path(name);path.unlink(missing_ok=True)
                if value:
                    if 'link' in value:path.symlink_to(value['link'])
                    else:path.write_bytes(value['data']);path.chmod(value['mode'])
            self.data=previous;self.save()
            raise
        finally:self.undo=None

    def _activate(self, bundle, graphics=None):
        if any(c.isspace() or c in '\'"`$;\\' for c in str(self.home)):raise ValueError('Home path contains unsupported shell characters')
        bundle=bundle.resolve(strict=True)
        for required in ['runtime/bin/lickintosh','runtime/bin/Hyprland','hypr/hyprland.lua','scripts','config/shells.json']:
            if not (bundle/required).exists(): raise ValueError('Incomplete bundle: '+required)
        # Freeze a generation: updates don't mutate the previous generation.
        generation=self.root/'generations'/self.stamp
        generation.mkdir(parents=True)
        (generation/'bundle').symlink_to(bundle)
        if graphics: (generation/'graphics').symlink_to(graphics.resolve(strict=True))
        localbin=self.home/'.local/bin'
        privatebin=self.root/'bin'
        configdir=self.home/'.config/quickintosh/hypr'
        scriptdir=self.root/'scripts'
        for file in (bundle/'scripts').iterdir():
            if file.is_file():
                text=file.read_text().replace('/home/demo',str(self.home)).replace('/home/pg',str(self.home))
                text=text.replace(str(self.home)+'/scripts/',str(scriptdir)+'/').replace(str(self.home)+'/.config/hypr/',str(configdir)+'/')
                text=text.replace('/run/current-system/sw/bin/',str(bundle/'runtime/bin')+'/')
                self.put(scriptdir/file.name,text,True)
        for file in (bundle/'hypr').rglob('*.lua'):
            text=file.read_text().replace('/home/demo',str(self.home)).replace('/home/pg',str(self.home))
            text=text.replace(str(self.home)+'/scripts/',str(scriptdir)+'/')
            text=text.replace(str(self.home)+'/.config/hypr/',str(configdir)+'/')
            text=text.replace('/.local/state/nixos-rice/active-shell','/.local/state/quickintosh-arch/rice/active-shell')
            text=re.sub(r'os.getenv\("HOME"\) \.\. "(/\.config/hypr/[^" ]*)"',lambda m:json.dumps(str(configdir)+'/'+m[1].split('/.config/hypr/',1)[1]),text)
            text=text.replace('/run/current-system/sw/bin/',str(privatebin)+'/')
            text=text.replace('    hl.exec_cmd("systemctl --user start nixos-fake-graphical-session.target")','    hl.exec_cmd('+json.dumps(str(privatebin/'quickintosh-session-ready'))+')')
            if file.name=='hyprland.lua':
                text='hl.env("LD_LIBRARY_PATH", os.getenv("QUICKINTOSH_ORIGINAL_LD_LIBRARY_PATH") or "")\n'+text
            self.put(configdir/file.relative_to(bundle/'hypr'),text)
        # Session state lives separately from any existing rice-shell installation.
        self.put(self.root/'shells.json',(bundle/'config/shells.json').read_text().replace('"default":"noctalia"','"default":"lickintosh"'))
        self.put(self.root/'rices.json',(bundle/'config/rices.json').read_text())
        self.put(self.root/'launcher.py',(REPO/'arch/launcher.py').read_text(),True)
        commands=['quickintosh','lickintosh','quickintosh-finder','lickintosh-finder','quickintosh-quicklook','lickintosh-quicklook',
                  'rice-shell','rice-file-manager','lickintosh-desktop-profile','quickintosh-session','quickintosh-doctor',
                  'quickintosh-session-ready','quickintosh-discord-install','kitty','playerctl','hyprctl','noctalia-legacy','noctalia','caelestia','eqsh']
        script='#!/bin/sh\nexec /usr/bin/python3 '+shlex.quote(str(self.root/'launcher.py'))+' '
        for command in commands:
            self.put(privatebin/command,script+shlex.quote(command)+' "$@"\n',True)
        for command in commands:
            if command in ['kitty','playerctl','hyprctl','noctalia-legacy','noctalia','caelestia','eqsh']: continue
            self.put(localbin/command,script+shlex.quote(command)+' "$@"\n',True)
        for file in (bundle/'runtime/share/applications').glob('lickintosh-*.desktop'):
            text=file.read_text()
            for original,command in [('lickintosh-finder','quickintosh-finder'),('lickintosh-quicklook','quickintosh-quicklook')]:
                if original in text:
                    text='\n'.join('Exec='+shlex.quote(str(localbin/command))+' %U' if line.startswith('Exec=') else line for line in text.splitlines())+'\n'
            self.put(self.home/'.local/share/applications'/file.name,text)
        portal=bundle/'runtime/libexec/xdg-desktop-portal-hyprland'
        if not portal.exists():portal=bundle/'runtime/lib/xdg-desktop-portal-hyprland'
        self.put(self.home/'.config/systemd/user/quickintosh-portal-hyprland.service',
                 '[Unit]\nDescription=Quickintosh matched portal backend\n[Service]\nType=dbus\nBusName=org.freedesktop.impl.portal.desktop.hyprland\nExecStart='+str(portal)+'\n')
        active=self.state/'rice/active-shell'
        if not active.exists():self.put(active,'lickintosh\n')
        self.put(self.home/'.config/xdg-desktop-portal/quickintosh-portals.conf','[preferred]\ndefault=hyprland;gtk;\norg.freedesktop.impl.portal.FileChooser=gtk;\n')
        self.put(self.home/'.local/share/wayland-sessions/quickintosh.desktop',
                 '[Desktop Entry]\nName=Quickintosh\nComment=Isolated Quickintosh desktop\nType=Application\nDesktopNames=Quickintosh;Hyprland\nExec='+shlex.quote(str(localbin/'quickintosh-session'))+'\n')
        self.data.update(bundle=str(generation/'bundle'),graphics=str(generation/'graphics') if graphics else '',
                         home=str(self.home),repo=str(REPO),config=str(configdir/'hyprland.lua'),version=1)
        self.save()
        print('Installed. No session was stopped or started. Launch ~/.local/bin/quickintosh-session from a TTY, or register the login entry. Backups: '+str(self.state/'backups'))

    def uninstall(self):
        preserved=[]
        for name,entry in reversed(list(self.data['files'].items())):
            path=Path(name)
            if not path.is_relative_to(self.home):raise ValueError('Invalid saved target')
            if path.exists() and digest(path)!=entry.get('sha256'):
                preserved.append(name);continue
            original=entry['original']
            path.unlink(missing_ok=True)
            if original:
                if 'link' in original:path.symlink_to(original['link'])
                else:shutil.copy2(original['backup'],path)
        self.data['files']={k:v for k,v in self.data['files'].items() if k in preserved};self.save()
        print(json.dumps({'restored':not preserved,'edited_files_preserved':preserved,
                          'note':'User preferences, backups, Nix generations and system packages are retained.'},indent=2))

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=['doctor','install','uninstall','register-session'])
    parser.add_argument('--graphics',choices=['mesa','nvidia','none'],default='mesa')
    parser.add_argument('--bundle',type=Path,help='Use an already built #arch bundle')
    args=parser.parse_args(argv)
    if os.geteuid()==0:parser.error('Run as the regular desktop user, not root. Only system-setup.sh uses sudo.')
    home=Path.home();activation=Activation(home)
    if args.command=='doctor':return 0 if doctor(home) else 1
    if args.command=='uninstall':
        if os.environ.get('XDG_CURRENT_DESKTOP','').startswith('Quickintosh'):parser.error('Leave the Quickintosh session before uninstalling')
        activation.uninstall();return 0
    if args.command=='register-session':
        source=home/'.local/share/wayland-sessions/quickintosh.desktop'
        if not source.is_file():parser.error('Install first')
        target='/usr/share/wayland-sessions/quickintosh-'+str(os.getuid())+'.desktop'
        subprocess.run(['sudo','install','-b','-Dm644',str(source),target],check=True)
        print('Login entry installed: '+target+'; remove with sudo rm '+target);return 0
    if not doctor(home):return 1
    if not Path('/etc/pam.d/lickintosh-lock').is_file():raise ValueError('Install host PAM prerequisites first: sudo bash arch/system-setup.sh')
    generation=activation.root/'builds'/activation.stamp;generation.mkdir(parents=True)
    bundle=args.bundle
    if not bundle:
        bundle=generation/'bundle'
        subprocess.run(NIX+['build',str(REPO)+'#arch','--out-link',str(bundle)],check=True)
    graphics=None
    if args.graphics!='none':
        graphics=generation/'graphics'
        command=NIX+['build',str(REPO)+'#arch-'+args.graphics,'--out-link',str(graphics)]
        if args.graphics=='nvidia':command=NIX+['build','--impure','--expr', '(builtins.getFlake '+json.dumps(str(REPO))+').inputs.nixgl.packages.x86_64-linux.default','--out-link',str(graphics)]
        subprocess.run(command,check=True)
    activation.activate(bundle,graphics)
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (OSError,ValueError,subprocess.CalledProcessError) as e:print('Quickintosh install: '+str(e),file=sys.stderr);sys.exit(1)
