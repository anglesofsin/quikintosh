"""Bounded local operations. Generated outputs never overwrite input files."""
from pathlib import Path
import os,shutil,stat,tempfile,zipfile,json,hashlib,time,subprocess,itertools

class FileOperations:
    def output(self,source,suffix,where='downloads'):
        folder=source.parent if where=='beside' else Path.home()/'Downloads'
        folder.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(prefix=source.stem+'-',suffix=suffix,dir=folder);os.close(fd)
        return Path(name)
    def rename(self,values,name):
        paths=self.managed(values)
        if len(paths)!=1:raise ValueError('Select one file to rename')
        if not name or name in ('.','..') or '/' in name or '\\' in name or len(name)>240:raise ValueError('Choose a simple file name')
        src=paths[0];dst=src.with_name(name)
        if dst.exists():raise ValueError('That name already exists')
        # A same-filesystem link+unlink prevents replacing a concurrently created file.
        if src.is_file() and not src.is_symlink():
            os.link(src,dst);src.unlink()
        elif src.is_dir():
            raise ValueError('Rename folders in Finder')
        else:raise ValueError('Unsupported file type')
        for item in self.items:
            if item['path']==str(src):item['path']=str(dst)
        self.save()
    def unpack(self,values):
        outputs=[]
        for src in self.managed(values):
            if not zipfile.is_zipfile(src):raise ValueError('Choose a ZIP archive')
            with zipfile.ZipFile(src) as archive:
                entries=archive.infolist()
                if len(entries)>10000 or sum(x.file_size for x in entries)>2*1024**3:raise ValueError('Archive is too large')
                for item in entries:
                    p=Path(item.filename)
                    if p.is_absolute() or '..' in p.parts or '\\' in item.filename or stat.S_ISLNK(item.external_attr>>16):raise ValueError('Archive contains an unsafe path')
                folder=Path(tempfile.mkdtemp(prefix=src.stem+'-',dir=src.parent))
                try:archive.extractall(folder)
                except Exception:shutil.rmtree(folder);raise
                outputs.append(str(folder))
        self.add(outputs)
    def folder_copy(self,values,event):
        sources=self.managed(values)
        target=self.path(event.get('target','')) if event.get('target') else None
        allowed={x['path'] for x in self.items}
        if target:
            if str(target) not in allowed or not target.is_dir() or target.is_symlink():raise ValueError('Choose a folder in the tray')
        else:
            folder=Path.home()/'Downloads';folder.mkdir(parents=True,exist_ok=True)
            target=Path(tempfile.mkdtemp(prefix='Quickintosh-folder-',dir=folder))
        total=0
        for src in sources:
            if src.is_symlink():raise ValueError('Copy symbolic links in Finder')
            if target==src or target.is_relative_to(src):raise ValueError('Cannot copy a folder into itself')
            files=[src] if src.is_file() else list(itertools.islice(src.rglob('*'),10001))
            if len(files)>10000:raise ValueError('Selection is too large')
            for p in files:
                if p.is_symlink():raise ValueError('Copy folders containing links in Finder')
                if p.is_file():total+=p.stat().st_size
            if total>2*1024**3:raise ValueError('Selection is too large')
        for src in sources:
            dest=target/src.name
            if dest.exists():raise ValueError('A destination file already exists: '+src.name)
        for src in sources:
            dest=target/src.name
            if src.is_dir():shutil.copytree(src,dest,symlinks=False)
            else:
                with src.open('rb') as a,dest.open('xb') as b:shutil.copyfileobj(a,b)
                shutil.copystat(src,dest)
        self.add([str(target)])
    def thumbnail(self,p,mime):
        cache=self.root/'previews';cache.mkdir(exist_ok=True)
        if not p.is_file() or p.stat().st_size>100*1024**2:return ''
        key=hashlib.sha256((str(p)+str(p.stat().st_mtime_ns)).encode()).hexdigest()
        out=cache/(key+'.png')
        if out.exists():return out.as_uri()
        try:
            if mime.startswith('image/'):
                from PIL import Image,ImageOps
                with Image.open(p) as im:
                    im=ImageOps.exif_transpose(im);im.thumbnail((256,220));im.convert('RGBA').save(out)
            elif mime=='application/pdf' and shutil.which('pdftoppm'):
                subprocess.run(['pdftoppm','-f','1','-singlefile','-scale-to','256','-png',str(p),str(out.with_suffix(''))],capture_output=True,timeout=8,check=True)
            elif mime.startswith('text/') and p.stat().st_size<1000000:
                # Preserve document meaning: actual text is shown by the QML card.
                return ''
            else:return ''
            return out.as_uri()
        except Exception:return ''
    def transform(self,event):
        paths=self.managed(event.get('paths',[]));op=event.get('operation','compress');fmt=event.get('format','automatic');quality=int(event.get('quality',72));side=int(event.get('side',0))
        if not 1<=quality<=100 or side<0 or side>16000:raise ValueError('Invalid image quality or size')
        if op=='zip':return self.archive(event['paths'])
        if op=='unzip':return self.unpack(event['paths'])
        if op not in ['compress','convert','resize','rotate','metadata','pdf']:raise ValueError('Unsupported transformation')
        from PIL import Image,ImageOps
        if len(paths)>32:raise ValueError('Choose at most 32 images')
        if fmt not in ['automatic','png','jpeg','webp']:raise ValueError('Unsupported image format')
        outputs=[];pages=[]
        try:
            for src in paths:
                with Image.open(src) as original:
                    if getattr(original,'is_animated',False):raise ValueError('Animated images must be converted separately')
                    im=ImageOps.exif_transpose(original).copy()
                if side:im.thumbnail((side,side),Image.Resampling.LANCZOS)
                if op=='rotate':im=im.rotate(-90,expand=True)
                if op=='pdf':pages.append(im.convert('RGB'));continue
                targetfmt=fmt if fmt!='automatic' else ('png' if im.mode in ('RGBA','LA') else 'jpeg')
                dst=self.output(src,'.'+targetfmt,event.get('destination','downloads'))
                try:
                    if targetfmt=='jpeg':im=im.convert('RGB')
                    if op=='metadata' or event.get('stripMetadata',True):im.info.clear()
                    kwargs={'quality':quality,'optimize':True} if targetfmt!='png' else {'optimize':True}
                    if targetfmt=='jpeg':kwargs['progressive']=True
                    if op!='metadata' and not event.get('stripMetadata',True):
                        for key in ('exif','icc_profile'):
                            if im.info.get(key):kwargs[key]=im.info[key]
                    im.save(dst,format=targetfmt.upper(),**kwargs);outputs.append(str(dst))
                except Exception:dst.unlink(missing_ok=True);raise
            if pages:
                dst=self.output(paths[0],'.pdf',event.get('destination','downloads'))
                try:pages[0].save(dst,format='PDF',save_all=True,append_images=pages[1:]);outputs.append(str(dst))
                except Exception:dst.unlink(missing_ok=True);raise
            self.add(outputs)
            return outputs
        finally:
            for im in pages:im.close()
    def clip_action(self,event):
        path=self.path(event.get('path',''));folder=Path.home()/'.cache/quickshell/spotlight_clip'
        if path.parent!=folder or path.is_symlink() or path.suffix not in ('.png','.txt'):raise ValueError('Unknown clipboard entry')
        meta=self.root/'clipboard-meta.json'
        try:data=json.loads(meta.read_text())
        except (OSError,ValueError):data={}
        if event['action']=='pinClip':
            d=data.get(str(path),{});d['pinned']=not d.get('pinned',False);data[str(path)]=d
        elif event['action']=='removeClip':path.unlink(missing_ok=True);data.pop(str(path),None)
        meta.write_text(json.dumps(data))
        return dict(type='clipboard',items=self.clipboard())
    def storage(self):
        s=shutil.disk_usage(Path.home());cache=self.root/'previews';size=sum(p.stat().st_size for p in cache.glob('*.png') if p.is_file() and not p.is_symlink()) if cache.exists() else 0
        return dict(type='storage',total=s.total,used=s.used,free=s.free,cache=size)
