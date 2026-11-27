"""Installed app inventory and explicit, scoped uninstall operations."""
from pathlib import Path
import configparser,json,subprocess,shutil,os,re,time

class AppOperations:
    def capabilities(self):
        local=bool(shutil.which('localsend'))
        if not local and shutil.which('flatpak'):
            local=subprocess.run(['flatpak','info','--show-ref','org.localsend.localsend_app'],capture_output=True,timeout=10).returncode==0
        return {'share':local,'video':bool(shutil.which('ffmpeg')),'pdf':True,'background':True}
    def applications(self,event=None):
        rows=[]
        if shutil.which('flatpak'):
            result=subprocess.run(['flatpak','list','--app','--columns=application,name,size,installation'],capture_output=True,text=True,timeout=20)
            for line in result.stdout.splitlines():
                fields=line.split('\t')
                if len(fields)<4:continue
                app,name,size,installation=fields[:4]
                rows.append(dict(id=app,name=name,size=size,kind='flatpak',scope=installation,removable=installation=='user',icon=app))
        folder=Path.home()/'.local/share/applications'
        for p in sorted(folder.glob('*.desktop')):
            if p.is_symlink():continue
            try:
                config=configparser.ConfigParser(interpolation=None);config.read(p);entry=config['Desktop Entry']
                if entry.get('NoDisplay','false')=='true':continue
                command=entry.get('Exec','');kind='shortcut';target=''
                # AppImages have a single, explicit absolute executable; do not parse a shell.
                import shlex
                argv=shlex.split(command)
                if argv and Path(argv[0]).is_absolute() and argv[0].lower().endswith('.appimage'):
                    image=Path(argv[0]);allowed=[Path.home()/'Applications',Path.home()/'.local/bin']
                    if image.is_file() and not image.is_symlink() and any(image.is_relative_to(a) for a in allowed):kind='appimage';target=str(image)
                rows.append(dict(id=str(p),name=entry.get('Name',p.stem),size='',kind=kind,target=target,scope='user',removable=True,icon=entry.get('Icon','application-x-executable')))
            except (OSError,ValueError,KeyError,configparser.Error):continue
        seen={r['id'] for r in rows}
        for folder in [Path('/run/current-system/sw/share/applications'),Path.home()/'.nix-profile/share/applications']:
            for p in sorted(folder.glob('*.desktop')):
                if p.stem in seen:continue
                try:
                    config=configparser.ConfigParser(interpolation=None);config.read(p);entry=config['Desktop Entry']
                    if entry.get('NoDisplay','false')=='true' or entry.get('Hidden','false')=='true':continue
                    rows.append(dict(id=p.stem,name=entry.get('Name',p.stem),size='',kind='NixOS',scope='system',removable=False,icon=entry.get('Icon','application-x-executable')));seen.add(p.stem)
                except (OSError,ValueError,KeyError,configparser.Error):continue
        rows.sort(key=lambda r:r['name'].casefold())
        result=dict(type='applications',items=rows)
        if event and event.get('path'):
            path=self.path(str(event['path']))
            match=next((r for r in rows if r['id']==str(path) or r.get('target')==str(path) or path.suffix=='.desktop' and r['id']==path.stem),None)
            if match:result['suggested']=match['id']
        return result
    def app_data_candidates(self,row):
        if row.get('kind')!='flatpak' or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{2,160}',row.get('id','')):return []
        path=Path.home()/'.var/app'/row['id']
        if path.is_symlink() or not path.is_dir() or path.resolve().parent!=(Path.home()/'.var/app').resolve():return []
        return [path]
    def application_data(self,event):
        row=next((r for r in self.applications()['items'] if r['id']==event.get('id')),None)
        if not row or not row['removable']:raise ValueError('Choose a user-managed application')
        candidates=[]
        for path in self.app_data_candidates(row):
            total=0;count=0;bounded=False;deadline=time.monotonic()+2
            for parent,dirs,files in os.walk(path,followlinks=False):
                dirs[:]=[d for d in dirs if not (Path(parent)/d).is_symlink()]
                for name in files:
                    file=Path(parent)/name
                    if not file.is_symlink():
                        try:total+=file.stat().st_size
                        except OSError:pass
                    count+=1
                    if count>=20000 or time.monotonic()>deadline:bounded=True;break
                if bounded:break
            candidates.append(dict(path=str(path),size=total,bounded=bounded))
        return dict(type='applicationData',id=row['id'],items=candidates)
    def uninstall(self,event):
        key=event.get('id');row=next((r for r in self.applications()['items'] if r['id']==key),None)
        if not row or not row['removable']:raise ValueError('Manage this application in system settings')
        if event.get('confirmed') is not True:raise ValueError('Confirm the selected application before uninstalling')
        data=self.app_data_candidates(row) if event.get('removeData') is True else []
        if row['kind']=='flatpak':
            subprocess.run(['flatpak','uninstall','--user','--noninteractive','--assumeyes',row['id']],capture_output=True,text=True,check=True,timeout=300)
        else:
            # Trash rather than permanently delete AppImages and local launchers.
            files=[row['id']]+([row['target']] if row['kind']=='appimage' else [])
            subprocess.run(['gio','trash','--',*files],capture_output=True,text=True,check=True,timeout=20)
        if data:subprocess.run(['gio','trash','--',*[str(path) for path in data]],capture_output=True,text=True,check=True,timeout=30)
        return self.applications()
    def sharing(self,event):
        paths=self.managed(event.get('paths',[]))
        if shutil.which('localsend'):
            subprocess.Popen(['localsend',*[str(p) for p in paths]],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        elif shutil.which('flatpak') and subprocess.run(['flatpak','info','--show-ref','org.localsend.localsend_app'],capture_output=True,timeout=10).returncode==0:
            subprocess.Popen(['flatpak','run','org.localsend.localsend_app',*[str(p) for p in paths]],start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        else:raise ValueError('Install LocalSend to share with nearby devices')
        return dict(type='shared',count=len(paths))
