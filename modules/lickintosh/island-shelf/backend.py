"""Private reference tray. File drops never move or delete the originals."""
import json,math,mimetypes,os,subprocess,sys,tempfile,time,zipfile
from pathlib import Path
from urllib.parse import unquote,urlparse

class Shelf:
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
            rows.append(dict(item,name=p.name,directory=p.is_dir(),size=s.st_size,uri=p.as_uri(),preview=p.as_uri() if mime.startswith('image/') else '',mime=mime))
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
        return rows
    def handle(self,event):
        action=event.get('action','list');values=event.get('paths',[])
        if action=='add':self.add(values)
        elif action=='remove':self.items=[x for x in self.items if x['path'] not in values];self.save()
        elif action=='clear':self.items=[x for x in self.items if x.get('pinned')];self.save()
        elif action=='pin':
            for x in self.items:
                if x['path'] in values:x['pinned']=not x.get('pinned',False)
            self.save()
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

def main():
    shelf=Shelf()
    print(json.dumps(dict(type='ready',items=shelf.entries())),flush=True)
    for line in sys.stdin:
        try:
            event=json.loads(line);response=shelf.handle(event)
        except Exception as e:response=dict(type='error',message=str(e))
        print(json.dumps(response,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
