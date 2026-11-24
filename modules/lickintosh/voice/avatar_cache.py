"""Bounded persistent Discord image cache; downloads never block call events."""
import asyncio,hashlib,os,re,time,urllib.request
from pathlib import Path
VALID=re.compile(r'https://cdn\.discordapp\.com/(?:avatars|icons|channel-icons)/\d{1,24}/[a-zA-Z0-9_]+\.png\?size=80\Z')
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None
class AvatarCache:
    def __init__(self,publish,directory=None,fetch=None):
        self.root=Path(directory or Path(os.environ.get('XDG_CACHE_HOME',str(Path.home()/'.cache')))/'lickintosh/voice-images')
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.publish=publish; self.fetch=fetch or self.download
        self.tasks={}; self.needed=set(); self.semaphore=asyncio.Semaphore(3)
    def paths(self,url):
        digest=hashlib.sha256(url.encode()).hexdigest()
        subject=hashlib.sha256('/'.join(url.split('/')[:-1]).encode()).hexdigest()
        return self.root/(digest+'.png'),self.root/(subject+'.last.png')
    def image(self,url):
        if not VALID.fullmatch(url):return ''
        self.needed.add(url)
        path,last=self.paths(url)
        if path.exists():return path.as_uri()
        if url not in self.tasks:
            self.tasks[url]=asyncio.create_task(self.load(url))
        return last.as_uri() if last.exists() else ''
    @staticmethod
    def download(url):
        request=urllib.request.Request(url,headers={'User-Agent':'Lickintosh-Dynamic-Island/1.0'})
        with urllib.request.build_opener(NoRedirect).open(request,timeout=5) as response:
            data=response.read(1024*1024+1)
        if len(data)>1024*1024 or not data.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Invalid avatar image')
        return data
    def write(self,path,data):
        temp=path.with_suffix('.tmp');temp.write_bytes(data);temp.chmod(0o600);temp.replace(path)
    def prune(self):
        files=sorted(self.root.glob('*.png'),key=lambda p:p.stat().st_mtime,reverse=True)
        total=0
        for index,path in enumerate(files):
            total+=path.stat().st_size
            if index>=256 or total>24*1024*1024:path.unlink(missing_ok=True)
    async def load(self,url):
        try:
            for delay in (0,2,5,15,30,60):
                if delay:await asyncio.sleep(delay)
                if url not in self.needed:return
                try:
                    async with self.semaphore:data=await asyncio.to_thread(self.fetch,url)
                    if len(data)>1024*1024 or not data.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Invalid image')
                    path,last=self.paths(url);self.write(path,data);self.write(last,data);self.prune()
                    self.publish();return
                except (OSError,ValueError):continue
        finally:self.tasks.pop(url,None)
