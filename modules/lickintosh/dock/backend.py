"""Local Dock file services: recent documents, folder stacks and reversible trash."""
import os,sys,json,time,signal,ctypes,subprocess,urllib.parse,xml.etree.ElementTree as ET
import threading,hashlib,struct,shutil,concurrent.futures,configparser
from datetime import datetime
from PIL import Image,ImageOps
from pathlib import Path
from app_catalog import AppCatalog
from app_identity import ProcessIdentities
HOME=Path.home();STATE=HOME/'.local/state/lickintosh/dock';STATE.mkdir(parents=True,exist_ok=True)

_output_lock=threading.Lock()
_recent_lock=threading.RLock()
_pool=concurrent.futures.ThreadPoolExecutor(max_workers=2)
_pending=set()
_recent_file=STATE/'recent-files.json'

def emit(kind,**data):
 with _output_lock:print(json.dumps(dict(type=kind,**data)),flush=True)
def journal():
 try:return json.loads(_recent_file.read_text())
 except (OSError,ValueError):return {}
def recent_policy():
 try:return json.loads((STATE/'recent-removed.json').read_text())
 except (OSError,ValueError):return {'clearBefore':0,'paths':{}}
def remove_recent(paths,clear=False):
 with _recent_lock:
  policy=recent_policy();now=time.time()
  if clear:policy={'clearBefore':now,'paths':{}}
  else:
   for path in paths:policy.setdefault('paths',{})[str(Path(path).expanduser())]=now
  target=STATE/'recent-removed.json';temp=target.with_suffix('.tmp');temp.write_text(json.dumps(policy));temp.replace(target)
def rename_recent(changes):
 with _recent_lock:
  data=journal();policy=recent_policy()
  for change in changes:
   old,new=change['old'],change['new']
   data[new]=data.pop(old,time.time())
   if old in policy.get('paths',{}):policy['paths'][new]=policy['paths'].pop(old)
  target=_recent_file;temp=target.with_suffix('.tmp');temp.write_text(json.dumps(data));temp.replace(target)
  target=STATE/'recent-removed.json';temp=target.with_suffix('.tmp');temp.write_text(json.dumps(policy));temp.replace(target)
def record_recent(path):
 path=Path(path).expanduser()
 if not path.exists() or path.name.startswith('.'):return
 with _recent_lock:
  data=journal();data[str(path)]=time.time();data=dict(sorted(data.items(),key=lambda x:x[1],reverse=True)[:400])
  tmp=_recent_file.with_suffix('.tmp');tmp.write_text(json.dumps(data));tmp.replace(_recent_file)
def thumbnail_path(path):
 stat=path.stat();key=hashlib.sha256((str(path)+str(stat.st_mtime_ns)+str(stat.st_size)).encode()).hexdigest()
 out=HOME/'.cache/lickintosh/dock-thumbnails';out.mkdir(parents=True,exist_ok=True)
 return out/(key+'.png')
def make_thumbnail(path):
 try:
  target=thumbnail_path(path)
  if target.exists():return
  if path.stat().st_size>80_000_000:return
  ext=path.suffix.lower()
  if ext in ['.png','.jpg','.jpeg','.webp','.avif','.gif','.bmp','.tiff']:
   with Image.open(path) as image:
    image.draft('RGB',(256,256));image=ImageOps.exif_transpose(image);image.thumbnail((256,256));image.convert('RGBA').save(target)
  elif ext in ['.mp4','.webm','.mkv','.mov','.avi'] and shutil.which('ffmpeg'):
   subprocess.run(['ffmpeg','-nostdin','-loglevel','error','-y','-ss','0','-i',str(path),'-frames:v','1','-vf',r'scale=256:256:force_original_aspect_ratio=decrease',str(target)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=10)
  elif ext=='.pdf' and shutil.which('pdftoppm'):
   prefix=str(target.with_suffix(''));subprocess.run(['pdftoppm','-f','1','-singlefile','-scale-to','256','-png',str(path),prefix],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True,timeout=10)
  if target.is_file():emit('thumbnail',path=str(path),thumbnail=target.as_uri())
 except (OSError,ValueError,subprocess.SubprocessError,Image.DecompressionBombError):pass
 finally:_pending.discard(str(path))
def fileitem(path):
 stat=path.stat();target=thumbnail_path(path) if not path.is_dir() else None
 if target is not None and not target.exists() and str(path) not in _pending and path.suffix.lower() in ['.png','.jpg','.jpeg','.webp','.avif','.gif','.bmp','.tiff','.pdf','.mp4','.webm','.mkv','.mov','.avi']:
  _pending.add(str(path));_pool.submit(make_thumbnail,path)
 return dict(path=str(path),name=path.name,directory=path.is_dir(),modified=stat.st_mtime,added=stat.st_ctime,created=getattr(stat,'st_birthtime',stat.st_ctime),size=stat.st_size,thumbnail=target.as_uri() if target is not None and target.exists() else '',image=path.suffix.lower() in ['.png','.jpg','.jpeg','.webp','.avif'])
def capture_directory():
 try:return Path(json.loads((HOME/'.config/lickintosh/shell-config.json').read_text()).get('capture',{}).get('directory','~/Desktop')).expanduser()
 except (OSError,ValueError):return HOME/'Desktop'
def recent(limit=100):
 times={}
 try:
  for entry in ET.parse(HOME/'.local/share/recently-used.xbel').getroot().findall('bookmark'):
   url=urllib.parse.urlparse(entry.get('href',''))
   if url.scheme!='file' or url.netloc not in ('','localhost'):continue
   path=urllib.parse.unquote(url.path)
   try:stamp=datetime.fromisoformat(entry.get('visited',entry.get('modified','')).replace('Z','+00:00')).timestamp()
   except ValueError:stamp=0
   times[path]=max(times.get(path,0),stamp)
 except (OSError,ET.ParseError):pass
 with _recent_lock:
  for path,stamp in journal().items():times[path]=max(times.get(path,0),stamp)
 for folder in {capture_directory(),HOME/'Pictures/Screenshots'}:
  if folder.is_dir():
   for path in sorted(folder.glob('Screenshot*'),key=lambda p:p.stat().st_mtime if p.exists() else 0,reverse=True)[:100]:
    if path.is_file():times[str(path)]=max(times.get(str(path),0),path.stat().st_mtime)
 policy=recent_policy();items=[]
 for path,stamp in sorted(times.items(),key=lambda x:x[1],reverse=True):
  if stamp<=max(policy.get('clearBefore',0),policy.get('paths',{}).get(path,0)):continue
  try:items.append(fileitem(Path(path)))
  except OSError:continue
  if len(items)>=limit:break
 return items

class Watcher:
 def __init__(self):
  self.libc=ctypes.CDLL(None,use_errno=True);self.fd=self.libc.inotify_init1(os.O_CLOEXEC);self.paths={};self.stop=False
  if self.fd>=0:threading.Thread(target=self.watch,daemon=True).start()
 def add(self,folder):
  path=Path(folder).expanduser()
  if path.is_dir() and str(path) not in self.paths.values():
   wd=self.libc.inotify_add_watch(self.fd,os.fsencode(path),0x8|0x80|0x100|0x200|0x40)
   if wd>=0:self.paths[wd]=str(path)
 def watch(self):
  while not self.stop:
   try:data=os.read(self.fd,65536)
   except OSError:return
   offset=0;changed=set()
   while offset+16<=len(data):
    wd,mask,cookie,length=struct.unpack_from('iIII',data,offset);name=os.fsdecode(data[offset+16:offset+16+length].split(bytes([0]),1)[0]);offset+=16+length
    folder=self.paths.get(wd)
    if not folder or name.startswith('.'):continue
    path=Path(folder)/name
    if mask & (0x8|0x80) and Path(folder)!=HOME/'.local/share' and trash_root() not in Path(folder).parents and path.is_file() and not name.endswith('.xbel'):record_recent(path)
    changed.add(folder)
   for folder in changed:emit('changed',folder=folder)

def listfiles(folder,sort,limit=100):
 if folder=='recent':return recent(limit)
 if folder=='trash':return trashfiles(sort,limit)
 p=Path(folder).expanduser()
 if not p.is_dir():raise ValueError('Folder is unavailable')
 items=[]
 for f in p.iterdir():
  if f.name.startswith('.'):continue
  try:
   stat=f.stat();items.append((f,stat))
  except OSError:pass
 key={'name':lambda x:x[0].name.casefold(),'kind':lambda x:(not x[0].is_dir(),x[0].suffix,x[0].name.casefold()),'modified':lambda x:x[1].st_mtime,'size':lambda x:x[1].st_size,'added':lambda x:x[1].st_ctime,'created':lambda x:getattr(x[1],'st_birthtime',x[1].st_ctime)}.get(sort,lambda x:x[1].st_mtime)
 return [fileitem(f) for f,_ in sorted(items,key=key,reverse=sort in ['modified','size','added','created'])[:limit]]
def trash_root():
 return Path(os.environ.get('XDG_DATA_HOME',str(HOME/'.local/share')))/'Trash'
def trashfiles(sort='modified',limit=100):
 root=trash_root();items=[]
 if not (root/'files').is_dir():return []
 for path in (root/'files').iterdir():
  try:
   item=fileitem(path);meta=configparser.ConfigParser(interpolation=None);meta.read(root/'info'/(path.name+'.trashinfo'))
   original=urllib.parse.unquote(meta.get('Trash Info','Path',fallback=str(path)))
   item['name']=Path(original).name;item['original']=original;item['trash']=True;item['trashUri']='trash:///'+urllib.parse.quote(path.name,safe='')
   try:item['added']=datetime.fromisoformat(meta.get('Trash Info','DeletionDate',fallback='')).timestamp()
   except ValueError:pass
   items.append(item)
  except (OSError,configparser.Error):continue
 key={'name':lambda i:i['name'].casefold(),'kind':lambda i:(not i['directory'],Path(i['name']).suffix,i['name'].casefold()),'size':lambda i:i['size'],'added':lambda i:i['added']}.get(sort,lambda i:i['modified'])
 return sorted(items,key=key,reverse=sort in ['modified','size','added','created'])[:limit]
def trashcount():
 try:return sum(1 for _ in (trash_root()/'files').iterdir())
 except OSError:return 0

def focus_window(address):
 if not isinstance(address,str) or not address.startswith('0x') or any(c not in '0123456789abcdefABCDEF' for c in address[2:]):raise ValueError('Invalid window address')
 clients=json.loads(subprocess.check_output(['hyprctl','clients','-j'],text=True,timeout=3));client=next((c for c in clients if c.get('address','').lower()==address.lower()),None)
 if not client:raise ValueError('The window has closed')
 workspace=client.get('workspace',{});name=workspace.get('name','');wid=workspace.get('id',0)
 def dispatch(expression):subprocess.run(['hyprctl','dispatch',expression],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=4)
 if name.startswith('special:'):
  monitors=json.loads(subprocess.check_output(['hyprctl','monitors','-j'],text=True,timeout=3));shown=any(m.get('specialWorkspace',{}).get('name')==name for m in monitors)
  if not shown:
   short=name.split(':',1)[1];script=HOME/'scripts/special-toggle.sh'
   if short in ['special','public','left','right'] and script.is_file():subprocess.run([str(script),short],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=5)
   else:dispatch('hl.dsp.workspace.toggle_special('+json.dumps(short,ensure_ascii=False)+')')
 elif wid>0:dispatch('hl.dsp.focus({workspace='+str(int(wid))+'})')
 dispatch('hl.dsp.focus({window='+json.dumps('address:'+address)+'})')
 emit('focused',address=address,workspace=wid)

def main():
 signal.signal(signal.SIGTERM,lambda *_:sys.exit(0));ctypes.CDLL(None).prctl(1,signal.SIGTERM,0,0,0)
 if os.getppid()==1:return
 watcher=Watcher()
 for folder in [HOME/'Downloads',HOME/'Desktop',capture_directory(),HOME/'.local/share',trash_root()/'files',trash_root()/'info']:watcher.add(folder)
 history=STATE/'recent-apps.json'
 try:apps=json.loads(history.read_text())
 except (OSError,ValueError):apps=[]
 catalog=AppCatalog();identities=ProcessIdentities();clean=catalog.sanitize(apps)
 if clean!=apps:
  tmp=history.with_suffix('.tmp');tmp.write_text(json.dumps(clean));tmp.replace(history)
 apps=clean
 emit('ready',apps=apps,trash=trashcount())
 for line in sys.stdin:
  try:
   r=json.loads(line);action=r.get('action')
   if action=='list':
    if r['folder']!='recent':watcher.add(r['folder'])
    emit('files',folder=r['folder'],items=listfiles(r['folder'],r.get('sort','modified')))
   elif action=='previews':
    for folder in r['folders']:
     if folder!='recent':watcher.add(folder)
     try:emit('preview',folder=folder,items=listfiles(folder,r.get('sort','modified'),limit=3))
     except (OSError,ValueError):emit('preview',folder=folder,items=[])
   elif action=='recentDrop':
    for value in r['urls']:
     parsed=urllib.parse.urlsplit(str(value))
     if parsed.scheme=='trash':
      token=urllib.parse.unquote(parsed.path).lstrip('/')
      if '/' in token or token in ['.','..']:raise ValueError('Invalid Trash location')
      meta=configparser.ConfigParser(interpolation=None);meta.read(trash_root()/'info'/(token+'.trashinfo'))
      path=Path(urllib.parse.unquote(meta.get('Trash Info','Path')))
      subprocess.run(['gio','trash','--restore','--',value],check=True,timeout=20)
     elif parsed.scheme=='file' and parsed.netloc in ('','localhost'):path=Path(urllib.parse.unquote(parsed.path))
     else:continue
     record_recent(path)
    emit('changed',folder='recent');emit('trash',count=trashcount())
   elif action=='removeRecentFiles':
    remove_recent(r.get('paths',[]),r.get('clear',False));emit('changed',folder='recent')
   elif action=='renameRecentFiles':
    rename_recent(r.get('changes',[]));emit('changed',folder='recent')
   elif action=='recent':
    record_recent(r['path']);emit('changed',folder='recent')
   elif action=='forget':
    apps=[app for app in apps if app['key'].casefold()!=str(r['key']).casefold()];tmp=history.with_suffix('.tmp');tmp.write_text(json.dumps(apps));tmp.replace(history);emit('apps',apps=apps)
   elif action=='identities':emit('identities',clients=identities.identify(r.get('clients',[]),catalog))
   elif action=='remember':
    previous=apps
    apps=catalog.sanitize(apps)
    for app in catalog.sanitize(r['apps']):
     if any(x.get('desktopId')==app['desktopId'] for x in apps):continue
     apps.insert(0,app)
    apps=apps[:24]
    if apps!=previous:
     tmp=history.with_suffix('.tmp');tmp.write_text(json.dumps(apps));tmp.replace(history);emit('apps',apps=apps)
   elif action=='focusWindow':focus_window(r['address'])
   elif action=='focus':
    match=next((x for x in apps if x['key']==r['key']),None)
    if match and apps[0]!=match:
     apps=[match]+[x for x in apps if x['key']!=r['key']];tmp=history.with_suffix('.tmp');tmp.write_text(json.dumps(apps));tmp.replace(history);emit('apps',apps=apps)
   elif action=='trash':
    paths=[]
    for url in r['urls']:
     parsed=urllib.parse.urlparse(url)
     if parsed.scheme!='file' or parsed.netloc not in ('','localhost'):continue
     p=Path(urllib.parse.unquote(parsed.path))
     if (p.exists() or p.is_symlink()) and p not in [HOME,Path('/'),trash_root(),trash_root()/'files',trash_root()/'info']:paths.append(str(p))
    if paths:subprocess.run(['gio','trash','--',*paths],check=True,timeout=20)
    emit('trash',count=trashcount())
   elif action=='restore':
    uris=r.get('uris') or [r['uri']]
    if not all(str(uri).startswith('trash:///') for uri in uris):raise ValueError('Not a trashed item')
    subprocess.run(['gio','trash','--restore','--',*uris],check=True,timeout=30);emit('trash',count=trashcount())
   elif action=='empty':
    subprocess.run(['gio','trash','--empty'],check=True,timeout=30);emit('trash',count=trashcount())
   elif action=='refresh':emit('trash',count=trashcount())
  except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:emit('error',message=str(e)[:200])
if __name__=='__main__':main()
