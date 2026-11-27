"""Bounded local operations. Generated outputs never overwrite input files."""
from pathlib import Path
import os,shutil,stat,tempfile,zipfile,json,hashlib,time,subprocess,itertools

from media_ops import MediaOperations

class FileOperations(MediaOperations):
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
            import ctypes
            libc=ctypes.CDLL(None,use_errno=True)
            if libc.renameat2(-100,os.fsencode(src),-100,os.fsencode(dst),1)!=0:
                error=ctypes.get_errno();raise OSError(error,os.strerror(error))
            for item in self.items:
                child=Path(item['path'])
                if child!=src and child.is_relative_to(src):item['path']=str(dst/child.relative_to(src))

        else:raise ValueError('Unsupported file type')
        for item in self.items:
            if item['path']==str(src):item['path']=str(dst)
        self.save()
    def rename_many(self,event):
        paths=self.managed(event.get('paths',[]));pattern=str(event.get('pattern','{name}-{index}{ext}'));plans=[]
        if len(paths)>256:raise ValueError('Rename at most 256 files')
        for index,path in enumerate(paths,1):
            name=pattern.replace('{name}',path.stem if path.is_file() else path.name).replace('{index}',str(index)).replace('{ext}',path.suffix if path.is_file() else '')
            if not name or name in ('.','..') or '/' in name or '\\' in name or len(name)>240:raise ValueError('Choose a simple file name pattern')
            target=path.with_name(name)
            if target!=path and target.exists():raise ValueError('A destination name already exists: '+name)
            plans.append((path,target))
        if len({str(dst) for _,dst in plans})!=len(plans):raise ValueError('Use {index} to make each name unique')
        done=[]
        try:
            for src,dst in plans:
                if src==dst:continue
                self.rename([str(src)],dst.name);done.append((src,dst))
        except BaseException:
            for src,dst in reversed(done):self.rename([str(dst)],src.name)
            raise
        return [str(dst) for _,dst in plans]
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
    def dimensions(self,p,mime):
        if not mime.startswith('image/') or p.stat().st_size>100*1024**2:return ''
        try:
            from PIL import Image
            with Image.open(p) as image:return f'{image.width}×{image.height}'
        except Exception:return ''
    def text_preview(self,p,mime):
        if not mime.startswith('text/') or not p.is_file():return ''
        try:
            with p.open(errors='replace') as f:return f.read(600)
        except OSError:return ''
    def thumbnail(self,p,mime):
        if not getattr(self,'defer_previews',False):return self.make_thumbnail(p,mime)
        if not p.is_file() or not (mime.startswith(('image/','video/')) or mime=='application/pdf'):return ''
        key=hashlib.sha256((str(p)+str(p.stat().st_mtime_ns)).encode()).hexdigest();out=self.root/'previews'/(key+'.png')
        if out.exists():return out.as_uri()
        if key not in self.preview_pending:
            self.preview_pending.add(key)
            def prepare():
                preview=self.make_thumbnail(p,mime)
                if preview:self.emit_preview(dict(type='preview',path=str(p),preview=preview))
            self.preview_executor.submit(prepare)
        return ''
    def make_thumbnail(self,p,mime):
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
            elif mime.startswith('video/'):
                subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-threads','1','-i',str(p),'-frames:v','1','-vf','scale=256:220:force_original_aspect_ratio=decrease','-threads','1',str(out)],capture_output=True,timeout=10,check=True)
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
        if op not in ['compress','convert','resize','rotate','metadata','pdf','background','split']:raise ValueError('Unsupported transformation')
        if not paths:raise ValueError('Select files to transform')
        if any((__import__('mimetypes').guess_type(str(p))[0] or '').startswith('video/') for p in paths):return self.video_transform(paths,event)
        if all(p.suffix.lower()=='.pdf' for p in paths) or (op=='pdf' and any(p.suffix.lower()=='.pdf' for p in paths)):return self.pdf_transform(paths,event)
        if op=='background':return self.remove_background(paths,event)
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
                    target=int(event.get('targetBytes',0))
                    if target<0 or target>2*1024**3:raise ValueError('Choose a valid target file size')
                    im.save(dst,format=targetfmt.upper(),**kwargs)
                    if target and targetfmt!='png':
                        for attempt in range(8):
                            if dst.stat().st_size<=target:break
                            kwargs['quality']=max(12,int(kwargs['quality']*.78))
                            if attempt>=4:im.thumbnail((max(1,int(im.width*.8)),max(1,int(im.height*.8))),Image.Resampling.LANCZOS)
                            im.save(dst,format=targetfmt.upper(),**kwargs)
                        if dst.stat().st_size>target:raise ValueError('Cannot reach this size without excessive quality loss')
                    elif target and dst.stat().st_size>target:raise ValueError('Choose JPEG or WebP for size-based compression')
                    outputs.append(str(dst))
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
