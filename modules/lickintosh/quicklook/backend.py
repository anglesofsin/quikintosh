"""Local Quick Look data, native Nautilus preview protocol and file transfers."""
import tempfile,time,functools,importlib.util
import concurrent.futures, hashlib, json, mimetypes, os, shutil, subprocess, sys, tarfile, threading, urllib.parse, zipfile
from pathlib import Path
from xml.etree import ElementTree
MAX_TEXT=2*1024*1024
TITLE='Lickintosh Quick Look'
CACHE=Path.home()/'.cache/lickintosh/quicklook'
_output=threading.Lock()
def emit(kind,**values):
 with _output:print(json.dumps({'type':kind,**values}),flush=True)
def local_path(value):
 u=urllib.parse.urlsplit(str(value))
 if u.scheme:
  if u.scheme!='file' or u.netloc not in ('','localhost'):raise ValueError('Only local files can be previewed')
  p=Path(urllib.parse.unquote(u.path))
 else:p=Path(value).expanduser()
 if not p.is_absolute():raise ValueError('An absolute local path is required')
 return p

@functools.lru_cache(maxsize=128)
def application_name(mime):
 try:
  from mime_types import external_app
  app=external_app(mime)
  return app.get_display_name() if app else ''
 except (ImportError,ValueError):return ''

def describe(value,page=1):
 p=local_path(value);stat=p.stat();mime=mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
 result={'path':str(p),'url':p.as_uri(),'name':p.name,'size':stat.st_size,'mime':mime,'kind':'info','page':page,'pages':1,'text':'','preview':''}
 result['application']=application_name(mime)
 if p.is_dir():
  result['kind']='directory';result['entries']=[{'name':f.name,'directory':f.is_dir(),'path':str(f)} for f in sorted(p.iterdir(),key=lambda f:(not f.is_dir(),f.name.casefold())) if not f.name.startswith('.')][:500]
 elif mime.startswith('image/') or p.suffix.lower() in ['.svg','.avif','.heic','.heif']:
  result['kind']='image';result['preview']=p.as_uri()
  try:
   from PIL import Image
   with Image.open(p) as image:result.update(pixelWidth=image.width,pixelHeight=image.height)
  except (OSError,ValueError):pass
 elif mime.startswith(('video/','audio/')):
  result['kind']='video' if mime.startswith('video/') else 'audio'
 elif mime=='application/pdf':
  info=subprocess.run(['pdfinfo',str(p)],capture_output=True,text=True,check=True,timeout=10)
  result['pages']=int(next((line.split(':',1)[1].strip() for line in info.stdout.splitlines() if line.startswith('Pages:')),'1'))
  page=max(1,min(int(page),result['pages']));result['page']=page
  CACHE.mkdir(parents=True,exist_ok=True)
  key=hashlib.sha256((str(p)+str(stat.st_mtime_ns)+str(stat.st_size)+str(page)).encode()).hexdigest();target=CACHE/(key+'.png')
  if not target.exists():subprocess.run(['pdftoppm','-f',str(page),'-singlefile','-scale-to','1600','-png',str(p),str(target.with_suffix(''))],capture_output=True,check=True,timeout=20)
  result.update(kind='pdf',preview=target.as_uri())
 elif zipfile.is_zipfile(p):
  with zipfile.ZipFile(p) as archive:
   ext=p.suffix.lower();names=archive.namelist()
   if ext in ['.docx','.xlsx','.pptx','.odt','.ods','.odp','.epub']:
    selected=[n for n in names if n in ['word/document.xml','content.xml','xl/sharedStrings.xml'] or n.startswith('ppt/slides/slide') and n.endswith('.xml') or ext=='.epub' and n.endswith(('.html','.xhtml'))][:100]
    text=[];total=0
    for name in selected:
     member=archive.getinfo(name)
     if member.file_size>MAX_TEXT or total+member.file_size>MAX_TEXT:continue
     data=archive.read(member);total+=len(data)
     try:text.append(' '.join(ElementTree.fromstring(data).itertext()))
     except ElementTree.ParseError:continue
    result.update(kind='text',text='\n\n'.join(text) or 'No readable text in this document.')
   else:result.update(kind='archive',entries=[{'name':m.filename,'size':m.file_size,'directory':m.is_dir()} for m in archive.infolist()[:1000]])
 elif p.suffix.lower() in ['.tar','.tgz','.gz','.bz2','.xz'] and tarfile.is_tarfile(p):
  with tarfile.open(p) as archive:
   entries=[]
   for m in archive:
    entries.append({'name':m.name,'size':m.size,'directory':m.isdir()})
    if len(entries)>=1000:break
   result.update(kind='archive',entries=entries)
 elif p.suffix.lower() in ['.ttf','.otf','.woff','.woff2']:result['kind']='font'
 else:
  with p.open('rb') as f:data=f.read(MAX_TEXT+1)
  try:
   text=data[:MAX_TEXT].decode('utf-8-sig')
   if '\0' in text:raise UnicodeError()
   result.update(kind='text',text=text+('\n… Preview truncated at 2 MiB.' if len(data)>MAX_TEXT else ''))
  except UnicodeError:result.update(kind='binary',text='\n'.join(f'{i:08x}  '+data[i:i+16].hex(' ') for i in range(0,min(4096,len(data)),16)))
 return result

def trash_file(value):
 from gi.repository import Gio
 parsed=urllib.parse.urlsplit(str(value))
 if parsed.scheme!='trash' or parsed.netloc:raise ValueError('Invalid Trash location')
 return Gio.File.new_for_uri(str(value))
def transfer_trash(value,dest,action):
 from gi.repository import Gio
 source=trash_file(value);info=source.query_info('standard::name,standard::display-name,standard::type',Gio.FileQueryInfoFlags.NONE,None)
 name=info.get_display_name() or info.get_name();target=dest/name;index=2
 while target.exists() or target.is_symlink():target=dest/(Path(name).stem+' '+str(index)+Path(name).suffix);index+=1
 if action=='link':raise ValueError('Move or copy items out of Trash instead of linking them')
 if action=='move':source.move(Gio.File.new_for_path(str(target)),Gio.FileCopyFlags.NONE,None,None,None)
 elif info.get_file_type()==Gio.FileType.DIRECTORY:
  # GIO copy is not recursive. The physical home-trash directory is safe to
  # copy while retaining its trash metadata; moves use GIO to clean metadata.
  name=urllib.parse.unquote(urllib.parse.urlsplit(str(value)).path).lstrip('/')
  if '/' in name or name in ['.','..']:raise ValueError('Unsupported Trash directory')
  physical=Path(os.environ.get('XDG_DATA_HOME',str(Path.home()/'.local/share')))/'Trash/files'/name
  if not physical.is_dir():raise ValueError('This Trash directory must be restored in Finder')
  shutil.copytree(physical,target,symlinks=True)
 else:source.copy(Gio.File.new_for_path(str(target)),Gio.FileCopyFlags.NOFOLLOW_SYMLINKS,None,None,None)
 return str(target)

def transfer(values,destination,action='copy'):
 if action not in ['copy','move','link']:raise ValueError('Unsupported transfer action')
 dest=local_path(destination)
 if not dest.is_dir():raise ValueError('Destination folder is unavailable')
 outputs=[]
 for value in values:
  if urllib.parse.urlsplit(str(value)).scheme=='trash':outputs.append(transfer_trash(value,dest,action));continue
  source=local_path(value)
  if not source.exists() and not source.is_symlink():raise FileNotFoundError(source)
  if source.parent.resolve()==dest.resolve() and action!='copy':outputs.append(str(source));continue
  if source.is_dir() and dest.resolve().is_relative_to(source.resolve()):raise ValueError('A folder cannot be dropped into itself')
  target=dest/source.name;n=2
  while target.exists() or target.is_symlink():target=dest/(source.stem+' '+str(n)+source.suffix);n+=1
  if action=='move':shutil.move(str(source),str(target))
  elif action=='link':target.symlink_to(source,target_is_directory=source.is_dir())
  elif source.is_dir():shutil.copytree(source,target,symlinks=True)
  else:
   # Exclusive creation prevents a race from overwriting an existing file.
   with source.open('rb') as inp,target.open('xb') as out:shutil.copyfileobj(inp,out)
   shutil.copystat(source,target,follow_symlinks=False)
  outputs.append(str(target))
 return outputs

def file_operation(operation,values,name='',destination=''):
 from gi.repository import Gio
 paths=[];changes=[]
 if operation=='paste':
  clipboard=subprocess.run(['wl-paste','--no-newline','--type','x-special/gnome-copied-files'],capture_output=True,timeout=5)
  if clipboard.returncode==0:
   lines=clipboard.stdout.decode().splitlines();action=lines.pop(0) if lines else 'copy';action='move' if action=='cut' else 'copy'
  else:
   clipboard=subprocess.run(['wl-paste','--no-newline','--type','text/uri-list'],capture_output=True,check=True,timeout=5);lines=clipboard.stdout.decode().splitlines();action='copy'
  urls=[line.strip() for line in lines if line.strip() and not line.startswith('#')]
  if not urls or len(urls)>1000:raise ValueError('The clipboard does not contain a file selection')
  paths=transfer(urls,destination,action)
  if action=='move':
   latest=subprocess.run(['wl-paste','--no-newline','--type','x-special/gnome-copied-files'],capture_output=True,timeout=5)
   if latest.returncode==0 and latest.stdout==clipboard.stdout:subprocess.run(['wl-copy','--clear'],check=True,timeout=5)
  return {'paths':paths,'changes':changes}
 if not values:raise ValueError('No files selected')
 if operation=='rename':
  if len(values)!=1 or not name or name in ['.','..'] or '/' in name or '\0' in name:raise ValueError('Enter a valid file name')
  source=local_path(values[0]);target=source.with_name(name)
  if source!=target:Gio.File.new_for_path(str(source)).move(Gio.File.new_for_path(str(target)),Gio.FileCopyFlags.NONE,None,None,None)
  return {'paths':[str(target)],'changes':[{'old':str(source),'new':str(target)}]}
 for value in values:
  if operation=='delete':
   parsed=urllib.parse.urlsplit(str(value));token=urllib.parse.unquote(parsed.path).strip('/')
   if parsed.scheme!='trash' or parsed.netloc or not token or '/' in token or token in ['.','..']:raise ValueError('Only items already in Trash can be deleted permanently')
   delete_trash_entry(trash_file(value));paths.append(str(value))
  elif operation=='trash':
   path=local_path(value);home=Path.home();trash=Path(os.environ.get('XDG_DATA_HOME',str(home/'.local/share')))/'Trash'
   if path in [home,Path('/'),trash,trash/'files',trash/'info']:raise ValueError('This location cannot be moved to Trash')
   Gio.File.new_for_path(str(path)).trash(None);paths.append(str(path))
  elif operation=='duplicate':
   source=local_path(value);paths.extend(transfer([str(source)],str(source.parent),'copy'))
  else:raise ValueError('Unsupported file operation')
 return {'paths':paths,'changes':changes}

def delete_trash_entry(file):
 # GVfs handles a top-level trashed folder recursively and removes its metadata.
 # Its children are deliberately read-only through trash:///, so let the backend
 # perform the operation rather than trying to mutate them one by one.
 file.delete(None)

_focus_module=None

def focus_preview(address):
 global _focus_module
 if _focus_module is None:
  path=Path(__file__).parent.parent/'tahoedock/backend.py'
  spec=importlib.util.spec_from_file_location('_lickintosh_focus',path);_focus_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(_focus_module);_focus_module.emit=emit
 _focus_module.focus_window(address)

def thumbnail(value):
 source=local_path(value);stat=source.stat();key=hashlib.sha256((str(source)+str(stat.st_mtime_ns)+str(stat.st_size)).encode()).hexdigest()
 cache=Path.home()/'.cache/lickintosh/dock-thumbnails';cache.mkdir(parents=True,exist_ok=True);target=cache/(key+'.png')
 if target.exists():
  try:
   from PIL import Image
   with Image.open(target) as image:image.verify()
   return target.as_uri()
  except (OSError,ValueError):pass
 fd,tmp=tempfile.mkstemp(prefix='.'+key+'-',suffix='.png',dir=cache);os.close(fd);tmp=Path(tmp)
 try:
  subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-threads','1','-ss','0.1','-i',str(source),'-frames:v','1','-vf','scale=256:256:force_original_aspect_ratio=decrease','-threads','1',str(tmp)],capture_output=True,check=True,timeout=15)
  tmp.replace(target);return target.as_uri()
 finally:tmp.unlink(missing_ok=True)

def saved_copy(source,tag,suffix,producer):
 source=local_path(source);fd,temp=tempfile.mkstemp(prefix='.'+source.stem+'-',suffix=suffix,dir=source.parent);os.close(fd);temp=Path(temp)
 try:
  producer(temp)
  target=source.with_name(source.stem+' '+tag+suffix);index=2
  while True:
   try:os.link(temp,target);break
   except FileExistsError:target=source.with_name(source.stem+' '+tag+' '+str(index)+suffix);index+=1
  return str(target)
 finally:temp.unlink(missing_ok=True)

def trim_media(value,start,end):
 source=local_path(value);start=float(start);end=float(end)
 if start<0 or end<=start:raise ValueError('Choose a valid start and end time')
 video=(mimetypes.guess_type(source.name)[0] or '').startswith('video/')
 suffix='.mp4' if video else source.suffix if source.suffix.lower() in ['.wav','.flac','.mp3','.ogg','.m4a'] else '.m4a'
 def produce(target):
  args=['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-ss',str(start),'-i',str(source),'-t',str(end-start),'-map','0:v?','-map','0:a?']
  if video:args+=['-c:v','libx264','-preset','veryfast','-crf','20','-c:a','aac','-movflags','+faststart']
  subprocess.run(args+[str(target)],capture_output=True,check=True,timeout=180)
 return saved_copy(str(source),'trimmed',suffix,produce)

def rotate_copy(value,degrees):
 from PIL import Image,ImageOps
 def produce(target):
  with Image.open(local_path(value)) as original:ImageOps.exif_transpose(original).rotate(-float(degrees),expand=True).save(target,format='PNG')
 return saved_copy(value,'rotated','.png',produce)

XML='''<node><interface name="org.gnome.NautilusPreviewer2"><method name="ShowFile"><arg type="s" direction="in"/><arg type="s" direction="in"/><arg type="b" direction="in"/><arg type="s" direction="in"/></method><method name="Close"/><signal name="SelectionEvent"><arg type="u"/></signal><property name="Visible" type="b" access="read"/></interface></node>'''

def main():
 from gi.repository import Gio,GLib
 Gio.AppInfoMonitor.get().connect('changed',lambda *_:application_name.cache_clear())
 loop=GLib.MainLoop();inspect_future=None;thumb_pool=concurrent.futures.ThreadPoolExecutor(max_workers=2);pool=concurrent.futures.ThreadPoolExecutor(max_workers=2);bus=None;sender=None;visible=False;last_geometry=None
 def acquired(connection,name):
  nonlocal bus
  bus=connection
  def call(c,sender_name,path,interface,method,args,invocation):
   nonlocal sender
   sender=sender_name
   if method=='ShowFile':
    uri,handle,toggle,token=args.unpack();emit('request',uri=uri,toggle=toggle,owner=handle)
   elif method=='Close':emit('close')
   invocation.return_value(GLib.Variant('()',()))
  connection.register_object('/org/gnome/NautilusPreviewer',Gio.DBusNodeInfo.new_for_xml(XML).interfaces[0],call,lambda *args:GLib.Variant('b',visible),None)
  emit('bridge',ready=True)
 Gio.bus_own_name(Gio.BusType.SESSION,'org.gnome.NautilusPreviewer',Gio.BusNameOwnerFlags.NONE,acquired,None,lambda *args:emit('bridge',ready=False))
 def work(req):
  try:
   if req['action']=='thumbnail':emit('thumbnail',path=str(local_path(req['path'])),version=req.get('version',''),url=thumbnail(req['path']))
   elif req['action']=='inspect':emit('preview',id=req['id'],data=describe(req['path'],req.get('page',1)))
   elif req['action']=='trim':emit('saved',path=trim_media(req['path'],req['start'],req['end']))
   elif req['action']=='rotate':emit('saved',path=rotate_copy(req['path'],req['degrees']))
   elif req['action']=='fileOperation':emit('fileOperation',id=req.get('id',0),operation=req['operation'],**file_operation(req['operation'],req.get('paths',[]),req.get('name',''),req.get('destination','')))
   elif req['action']=='transfer':emit('transferred',id=req.get('id',0),paths=transfer(req['paths'],req['destination'],req.get('operation','copy')))
   elif req['action']=='geometry':
    clients=json.loads(subprocess.check_output(['hyprctl','clients','-j'],timeout=2));window=next((c for c in clients if c.get('title','').startswith(TITLE)),None)
    if window:
     monitors=json.loads(subprocess.check_output(['hyprctl','monitors','-j'],timeout=2));monitor=next((m for m in monitors if m['id']==window['monitor']),monitors[0]);emit('geometry',address=window['address'],x=window['at'][0]-monitor['x'],y=window['at'][1]-monitor['y'],monitor=monitor['name'])
   elif req['action']=='focus':focus_preview(req['address'])
  except Exception as error:emit('error',id=req.get('id',-1),operation=req.get('action',''),message=str(error))
 def dispatch(req):
  nonlocal visible,inspect_future
  if req['action']=='visible':
   visible=bool(req['value'])
   if bus:bus.emit_signal(None,'/org/gnome/NautilusPreviewer','org.freedesktop.DBus.Properties','PropertiesChanged',GLib.Variant('(sa{sv}as)',('org.gnome.NautilusPreviewer2',{'Visible':GLib.Variant('b',visible)},[])))
  elif req['action']=='openExternal':
   from mime_types import external_app
   path=local_path(req['path']);mime=Gio.content_type_guess(str(path),None)[0];app=external_app(mime)
   if app:app.launch([Gio.File.new_for_path(str(path))],None)
  elif req['action']=='chooseApp':
   if bus:bus.call('org.freedesktop.portal.Desktop','/org/freedesktop/portal/desktop','org.freedesktop.portal.OpenURI','OpenURI',GLib.Variant('(ssa{sv})',('',local_path(req['path']).as_uri(),{'ask':GLib.Variant('b',True)})),None,Gio.DBusCallFlags.NONE,-1,None,None,None)
  elif req['action']=='navigate':
   if bus and sender:bus.emit_signal(sender,'/org/gnome/NautilusPreviewer','org.gnome.NautilusPreviewer2','SelectionEvent',GLib.Variant('(u)',(int(req['direction']),)))
  elif req['action']=='thumbnail':thumb_pool.submit(work,req)
  elif req['action']=='inspect':
   if inspect_future:inspect_future.cancel()
   inspect_future=pool.submit(work,req)
  else:pool.submit(work,req)
  return False
 def stdin():
  for line in sys.stdin:
   try:GLib.idle_add(dispatch,json.loads(line))
   except (ValueError,KeyError):pass
  GLib.idle_add(loop.quit)
 threading.Thread(target=stdin,daemon=True).start();emit('ready',ownerPid=os.getppid());loop.run();thumb_pool.shutdown(wait=False,cancel_futures=True);pool.shutdown(wait=False,cancel_futures=True)
if __name__=='__main__':main()
