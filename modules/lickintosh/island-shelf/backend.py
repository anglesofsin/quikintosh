"""Private reference tray. File drops never move or delete the originals."""
import itertools
import json,math,mimetypes,os,subprocess,sys,tempfile,time,zipfile
from pathlib import Path
from urllib.parse import unquote,urlparse

from file_ops import FileOperations
from app_ops import AppOperations
from vault_ops import VaultOperations
from media_queue import MediaQueue

class Shelf(FileOperations,AppOperations,VaultOperations,MediaQueue):
    def __init__(self,root=None):
        self.root=Path(root or Path.home()/'.local/state/quickintosh/island-shelf')
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.file=self.root/'tray.json'
        self.activities={}
        try:self.items=json.loads(self.file.read_text())
        except (OSError,ValueError):self.items=[]
        self.items=[x for x in self.items if isinstance(x,dict) and isinstance(x.get('path'),str)][:256]
    def save(self):
        fd,tmp=tempfile.mkstemp(dir=self.root,prefix='.tray-')
        try:
            with os.fdopen(fd,'w') as f:json.dump(self.items,f,ensure_ascii=False)
            Path(tmp).replace(self.file)
        finally:Path(tmp).unlink(missing_ok=True)
    def path(self,value):
        if value.startswith('file:'):
            url=urlparse(value)
            if url.netloc not in ('','localhost'):raise ValueError('Only local files are supported')
            value=unquote(url.path)
        p=Path(value).expanduser()
        if not p.is_absolute():raise ValueError('Choose an absolute local file path')
        return p
    def add(self,values):
        known={x['path'] for x in self.items}
        for value in values[:256]:
            p=self.path(str(value))
            if not p.exists() or str(p) in known:continue
            self.items.append(dict(path=str(p),pinned=False,added=time.time()));known.add(str(p))
        self.items=self.items[-256:];self.save()
    def entries(self):
        rows=[]
        for item in self.items:
            p=Path(item['path'])
            try:s=p.stat()
            except OSError:continue
            mime=mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
            rows.append(dict(item,name=p.name,directory=p.is_dir(),size=s.st_size,uri=p.as_uri(),preview=self.thumbnail(p,mime),mime=mime,dimensions=self.dimensions(p,mime),textPreview=self.text_preview(p,mime),count=sum(1 for _ in itertools.islice(p.iterdir(),10000)) if p.is_dir() else 0))
        return sorted(rows,key=lambda x:(not x.get('pinned',False),-x.get('added',0)))
    def managed(self,values):
        allowed={x['path'] for x in self.items}
        paths=[self.path(str(x)) for x in values]
        if not paths or any(str(p) not in allowed or not p.exists() for p in paths):raise ValueError('Select files currently in the tray')
        return paths
    def archive(self,values):
        paths=self.managed(values)
        # Bounded archive work. Do not follow directory symlinks or read devices.
        files=[];total=0
        for base in paths:
            if base.is_symlink():raise ValueError('Archive symlinks from Finder instead')
            candidates=[base] if base.is_file() else base.rglob('*')
            for p in candidates:
                if p.is_symlink() or not p.is_file():continue
                total+=p.stat().st_size
                if len(files)>=10000 or total>2*1024**3:raise ValueError('Selection is too large; archive it in Finder')
                files.append((p,str(Path(base.name)/p.relative_to(base)) if base.is_dir() else base.name))
        folder=Path.home()/'Downloads';folder.mkdir(exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix='Quickintosh-',suffix='.zip',dir=folder)
        try:
            with os.fdopen(fd,'wb') as f:
                with zipfile.ZipFile(f,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
                    used=set()
                    for p,name in files:
                        if name in used:raise ValueError('Duplicate archive names; archive folders separately')
                        z.write(p,name);used.add(name)
            self.add([tmp]);return tmp
        except Exception:Path(tmp).unlink(missing_ok=True);raise
    def clipboard(self):
        folder=Path.home()/'.cache/quickshell/spotlight_clip';rows=[]
        if not folder.exists():return rows
        for p in sorted(folder.iterdir(),key=lambda p:p.stat().st_mtime,reverse=True):
            if p.suffix not in ('.txt','.png') or p.is_symlink() or not p.is_file():continue
            text=p.read_text(errors='replace')[:4096] if p.suffix=='.txt' else ''
            rows.append(dict(path=str(p),name=text[:120].replace('\n',' ') if text else p.name,text=text,image=p.as_uri() if p.suffix=='.png' else '',kind='image' if p.suffix=='.png' else 'text'))
            if len(rows)>=80:break
        try:meta=json.loads((self.root/'clipboard-meta.json').read_text())
        except (OSError,ValueError):meta={}
        for item in rows:
            item.update(meta.get(item['path'],{}));item['added']=Path(item['path']).stat().st_mtime
            text=item.get('text','').strip()
            if text.startswith(('http://','https://')):item['kind']='link'
            elif len(text)==7 and text.startswith('#') and all(c in '0123456789abcdefABCDEF' for c in text[1:]):item['kind']='color'
        return sorted(rows,key=lambda x:(not x.get('pinned',False),-x.get('added',0)))
    def handle(self,event):
        action=event.get('action','list');values=event.get('paths',[])
        if action=='jobHistory':
            file=self.root/'job-history.jsonl';rows=[]
            if file.exists() and file.stat().st_size<1024*1024:
                for line in file.read_text().splitlines()[-200:]:
                    try:
                        item=json.loads(line)
                        if isinstance(item,dict) and isinstance(item.get('title'),str) and isinstance(item.get('seconds'),(int,float)) and isinstance(item.get('code'),int):rows.append(item)
                    except ValueError:continue
            return dict(type='jobHistory',items=list(reversed(rows)),seconds=sum(max(0,item['seconds']) for item in rows),completed=sum(item['code']==0 for item in rows),failed=sum(item['code']!=0 for item in rows))
        elif action=='queueWatch':return self.queue_watch(event)
        elif action=='queueAction':return self.queue_action(event)
        elif action in ('vaultSelect','vaultList','vaultRead','vaultSave'):return self.vault(event)
        elif action=='utilityPreferences':
            path=self.root/'utilities.json'
            try:state=json.loads(path.read_text())
            except (ValueError,OSError):state={}
            values=event.get('values',{})
            if 'teleprompterText' in values:state['teleprompterText']=str(values['teleprompterText'])[:100000]
            if values.get('voiceLanguage') in ('auto','pt','en','es','fr','de','it','ja','ko','zh','ru'):state['voiceLanguage']=values['voiceLanguage']
            if 'selectionActionsEnabled' in values:state['selectionActionsEnabled']=values['selectionActionsEnabled'] is True
            if 'widgetRecent' in values:state['widgetRecent']=list(dict.fromkeys(key[:64] for key in values['widgetRecent'][:40] if isinstance(key,str)))
            if 'ringCount' in values:state['ringCount']=max(1,min(3,int(values['ringCount'])))
            if 'ringActions' in values:state['ringActions']=[key[:32] for key in values['ringActions'][:18] if isinstance(key,str)]
            if 'commandColumns' in values:state['commandColumns']=max(4,min(7,int(values['commandColumns'])))
            if 'commandFavorites' in values:state['commandFavorites']=[str(key)[:64] for key in values['commandFavorites'][:64] if isinstance(key,str)]
            if 'breaksEnabled' in values:state['breaksEnabled']=values['breaksEnabled'] is True
            for key in ('eyesMinutes','stretchMinutes','waterMinutes'):
                if key in values:state[key]=max(5,min(240,int(values[key])))
            if values:
                fd,tmp=tempfile.mkstemp(dir=self.root,prefix='.utilities-')
                try:
                    with os.fdopen(fd,'w') as stream:json.dump(state,stream,ensure_ascii=False)
                    Path(tmp).replace(path)
                finally:Path(tmp).unlink(missing_ok=True)
            return dict(type='utilityPreferences',values=state)
        elif action=='developerTool':
            from developer_tools import transform
            try:return dict(type='developerResult',text=transform(event.get('text',''),event.get('operation','')),error='')
            except (ValueError,TypeError,UnicodeError,RecursionError) as error:return dict(type='developerResult',text='',error=str(error))
        elif action=='copyText':
            text=str(event.get('text',''))
            if len(text)>1024*1024:raise ValueError('Text is too large')
            subprocess.run(['wl-copy','--type','text/plain;charset=utf-8'],input=text.encode(),check=True,timeout=4)
        elif action=='add':self.add(values)
        elif action=='remove':self.items=[x for x in self.items if x['path'] not in values];self.save()
        elif action=='clear':self.items=[x for x in self.items if x.get('pinned')];self.save()
        elif action=='pin':
            for x in self.items:
                if x['path'] in values:x['pinned']=not x.get('pinned',False)
            self.save()
        elif action=='renameMany':
            after=self.rename_many(event);return dict(type='renamed',items=self.entries(),before=values,after=after)
        elif action=='rename':self.rename(values,str(event.get('name','')))
        elif action=='unzip':self.unpack(values)
        elif action=='folder':self.folder_copy(values,event)
        elif action=='transform':self.transform(event)
        elif action in ('presets','savePreset','removePreset'):return self.presets(event)
        elif action in ('pinClip','removeClip'):return self.clip_action(event)
        elif action=='applications':return self.applications(event)
        elif action=='applicationData':return self.application_data(event)
        elif action=='uninstall':return self.uninstall(event)
        elif action=='share':return self.sharing(event)
        elif action=='storage':return self.storage()
        elif action=='cleanPreviews':
            folder=self.root/'previews'
            for p in folder.glob('*.png'):
                if p.is_file() and not p.is_symlink():p.unlink()
            return self.storage()
        elif action=='track':
            self.managed(values)
            for x in self.items:
                if x['path'] in values and Path(x['path']).is_dir():x['tracked']=not x.get('tracked',False);x['pinned']=True;x['seen']=[str(p) for p in Path(x['path']).iterdir()][:2048]
            self.save()
        elif action=='scanTracked':
            arrivals=[]
            for x in list(self.items):
                if not x.get('tracked'):continue
                try:current=[str(p) for p in Path(x['path']).iterdir() if not p.name.startswith('.')][:2048]
                except OSError:continue
                arrivals.extend(p for p in current if p not in x.get('seen',[]));x['seen']=current
            if arrivals:self.add(arrivals)
        elif action=='archive':self.archive(values)
        elif action=='copy':
            paths=self.managed(values)
            subprocess.run(['wl-copy','--type','text/uri-list'],input=('\r\n'.join(p.as_uri() for p in paths)+'\r\n').encode(),check=True,timeout=4)
        elif action=='copyClip':
            p=self.path(event.get('path',''));folder=Path.home()/'.cache/quickshell/spotlight_clip'
            if p.parent!=folder or p.suffix not in ('.txt','.png') or p.is_symlink():raise ValueError('Unknown clipboard entry')
            with p.open('rb') as f:subprocess.run(['wl-copy','--type','image/png' if p.suffix=='.png' else 'text/plain;charset=utf-8'],stdin=f,check=True,timeout=4)
        elif action=='activity':
            item=event.get('activity',{});key=str(item.get('id',''))[:120]
            if not key:raise ValueError('Activity id is required')
            if item.get('remove'):self.activities.pop(key,None)
            else:
                title=str(item.get('title',''))[:160]
                if not title:raise ValueError('Activity title is required')
                ttl=float(item.get('ttl',60))
                if not math.isfinite(ttl):raise ValueError('Activity duration must be finite')
                ttl=max(1,min(3600,ttl))
                progress=item.get('progress')
                if progress is not None:
                    progress=float(progress)
                    if not math.isfinite(progress):raise ValueError('Activity progress must be finite')
                    progress=max(0,min(1,progress))
                self.activities[key]=dict(id=key,title=title,subtitle=str(item.get('subtitle',''))[:240],progress=progress,expires=time.time()+ttl)
                if len(self.activities)>32:self.activities.pop(next(iter(self.activities)))
            self.activities={k:v for k,v in self.activities.items() if v['expires']>time.time()}
            return dict(type='activities',items=list(self.activities.values()))
        elif action=='convert':
            paths=self.managed(values);fmt=event.get('format','png')
            if fmt not in ('png','jpeg','webp'):raise ValueError('Unsupported image format')
            from PIL import Image
            folder=Path.home()/'Downloads';folder.mkdir(exist_ok=True)
            for original in paths[:32]:
                with Image.open(original) as image:
                    if getattr(image,'is_animated',False):raise ValueError('Use Finder to convert animated media')
                    fd,tmp=tempfile.mkstemp(prefix=original.stem+'-',suffix='.'+fmt,dir=folder);os.close(fd)
                    try:
                        converted=image.convert('RGB') if fmt=='jpeg' else image
                        converted.save(tmp,format=fmt.upper(),quality=92)
                        self.add([tmp])
                    except Exception:Path(tmp).unlink(missing_ok=True);raise
        elif action=='clipboard':return dict(type='clipboard',items=self.clipboard())
        return dict(type='tray',items=self.entries())

def transform_job():
    import signal
    def cancel(*_):raise RuntimeError('Transformation cancelled')
    signal.signal(signal.SIGTERM,cancel)
    os.nice(5)
    shelf=Shelf();outputs=[]
    shelf.add=lambda values:outputs.extend(str(x) for x in values)
    try:
        event=json.loads(sys.stdin.readline());shelf.transform(event)
        print(json.dumps(dict(type='transformDone',paths=outputs)),flush=True)
    except Exception as error:
        print(json.dumps(dict(type='error',message=str(error))),flush=True)
        return 1
    return 0

def application_job():
    os.nice(5)
    try:
        shelf=Shelf();event=json.loads(sys.stdin.readline(65537))
        if event.get('action')=='applicationData':result=shelf.application_data(event)
        elif event.get('action')=='uninstall':result=shelf.uninstall(event)
        else:raise ValueError('Unknown application operation')
        print(json.dumps(result),flush=True)
    except Exception as error:
        print(json.dumps(dict(type='error',message=str(error))),flush=True);return 1
    return 0

def main():
    if '--application-job' in sys.argv:raise SystemExit(application_job())
    if '--transform-job' in sys.argv:raise SystemExit(transform_job())
    import threading
    from concurrent.futures import ThreadPoolExecutor
    lock=threading.Lock()
    def emit(event):
        line=json.dumps(event,ensure_ascii=False)+'\n'
        with lock:sys.stdout.write(line);sys.stdout.flush()
    shelf=Shelf();shelf.defer_previews=True;shelf.preview_pending=set();shelf.preview_executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='file-preview');shelf.emit_preview=emit;shelf.emit_event=emit
    emit(dict(type='ready',items=shelf.entries(),capabilities=shelf.capabilities()))
    for line in sys.stdin:
        busy=False
        try:
            event=json.loads(line)
            busy=event.get('action') in ('transform','archive','unzip','folder','rename')
            if busy:emit(dict(type='busy',value=True))
            response=shelf.handle(event)
        except Exception as e:response=dict(type='error',message=str(e))
        emit(response)
        if busy:emit(dict(type='busy',value=False))
if __name__=='__main__':main()
