"""Persistent material compositor: prepared mask fields + palette, no browser.

Light/dark are immutable downloaded art. Tinted/Clear use reusable geometric,
relief and specular fields. Original source content hashes invalidate schemas.
"""
import os,sys,json,hashlib,time,threading,collections,subprocess,io
from pathlib import Path
from urllib.parse import unquote,urlparse
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageFilter
CACHE=Path.home()/'.cache/lickintosh/icon-materials-v2';CACHE.mkdir(parents=True,exist_ok=True)
RSVG=sys.argv[1];SIZE=192;VERSION='material-schema-7'
lock=threading.Condition();output_lock=threading.Lock();queue=collections.deque();epoch=None;stopping=False;prepared=collections.OrderedDict()
try:index=json.loads((CACHE/'index.json').read_text())
except (ValueError,OSError):index={}
def emit(o):
 with output_lock:print(json.dumps(o,separators=(',',':')),flush=True)
icon_catalog=None
def find_icon(name):
 global icon_catalog
 decoded=unquote(name)
 absolute=Path(urlparse(decoded).path if decoded.startswith('file:') else decoded)
 if absolute.is_absolute() and absolute.is_file():return absolute
 name=decoded.strip('/').lower()
 if icon_catalog is None:
  icon_catalog={};visited=set()
  bases=[Path.home()/'.local/share',Path.home()/'.nix-profile/share',Path('/run/current-system/sw/share'),Path('/var/lib/flatpak/exports/share'),Path.home()/'.local/share/flatpak/exports/share']
  bases += [Path(p) for p in os.environ.get('XDG_DATA_DIRS','').split(':') if p]
  for base in bases:
   for folder in [base/'icons/hicolor',base/'pixmaps',base/'icons']:
    if not folder.is_dir():continue
    for current,dirs,files in os.walk(folder,followlinks=True):
     real=os.path.realpath(current)
     if real in visited:dirs[:]=[];continue
     visited.add(real)
     for filename in files:
      p=Path(current)/filename
      if p.suffix.lower() in ['.svg','.svgz','.png','.webp','.ico','.icns','.xpm','.jpg','.jpeg','.bmp','.gif']:
       icon_catalog.setdefault(p.stem.lower(),p)
 for key in [name,Path(name).stem,name.removesuffix('.desktop')]:
  if key in icon_catalog:return icon_catalog[key]
 raise FileNotFoundError('No installed artwork for icon provider: '+name)
def path(s):
 if s.startswith('image://icon/'):return find_icon(urlparse(s).path)
 return Path(unquote(urlparse(s).path) if s.startswith('file:') else s)
def raster(p):
 if p.suffix.lower() in ['.svg','.svgz']:
  data=subprocess.run([RSVG,'-w',str(SIZE),'-h',str(SIZE),str(p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=8).stdout
  im=Image.open(io.BytesIO(data)).convert('RGBA')
 else:im=Image.open(p).convert('RGBA')
 im.thumbnail((SIZE,SIZE),Image.Resampling.LANCZOS)
 canvas=Image.new('RGBA',(SIZE,SIZE));canvas.alpha_composite(im,((SIZE-im.width)//2,(SIZE-im.height)//2));return canvas

def prepare(job):
 source=path(job.get('matte') or job.get('geometry') or job['source']);data=source.read_bytes();stamp=hashlib.sha256(data+VERSION.encode()+str(bool(job.get('matte'))).encode()).hexdigest();file=CACHE/(stamp+'.npz')
 if stamp in prepared:
  prepared.move_to_end(stamp);return prepared[stamp],stamp
 if file.exists():
  with np.load(file) as a:fields={k:a[k] for k in a.files}
  prepared[stamp]=fields
  if len(prepared)>24:prepared.popitem(last=False)
  return fields,stamp
 im=raster(source);a=np.asarray(im,dtype=np.float32)/255;rgb=a[:,:,:3];alpha=a[:,:,3]
 lum=rgb@np.array([.2126,.7152,.0722],dtype=np.float32)
 yy,xx=np.mgrid[:SIZE,:SIZE];central=(xx>SIZE*.2)&(xx<SIZE*.8)&(yy>SIZE*.2)&(yy<SIZE*.8)&(alpha>.9)
 if job.get('matte'):
  # Native monochrome rendition explicitly supplies the geometric relief.
  neutral=lum[central & (lum>.2) & (lum<.8)]
  base=float(np.median(neutral)) if len(neutral) else .58
  ink=np.clip((lum-base)/max(.15,1-base),0,1)
  shadow=np.clip((base-lum)/max(.15,base),0,1)
 else:
  # Infer the existing container from an inset ring, keeping saturated logos
  # apart from neutral tiles. This runs once, never once per color change.
  ring=(((xx<SIZE*.22)|(xx>SIZE*.78)|(yy<SIZE*.22)|(yy>SIZE*.78)) & (alpha>.95))
  sample=rgb[ring];bg=np.median(sample,axis=0) if len(sample) else np.zeros(3)
  # Fit the container gradient row by row from inset side strips. A single
  # global background color turns ordinary gradients into false foreground bands.
  strips=(((xx>SIZE*.12)&(xx<SIZE*.18))|((xx>SIZE*.82)&(xx<SIZE*.88)))&(alpha>.98)
  background=np.tile(bg,(SIZE,1));valid=[]
  for row in range(SIZE):
   samples=rgb[row][strips[row]]
   if len(samples)>=4:background[row]=np.median(samples,axis=0);valid.append(row)
  if valid:
   for channel in range(3):background[:,channel]=np.interp(np.arange(SIZE),valid,background[valid,channel])
  distance=np.sqrt(np.sum((rgb-background[:,None,:])**2,axis=2))

  ink=np.clip((distance-.08)/.55,0,1)
  # Transparent standalone logos have no container to separate.
  occupancy=float(np.mean(alpha>.9))
  if occupancy<.38:ink=alpha.copy()
  shadow=np.clip((float(bg@np.array([.2126,.7152,.0722]))-lum)*.55,0,.35)*(1-ink)
 fallback_ink=ink.copy();fallback_shadow=shadow.copy()
 if not job.get('matte') and source.suffix.lower() in ['.svg','.svgz']:
  # Prefer authored SVG geometry over color segmentation. Remove only explicit
  # full-size container rectangles and known tile shadow/rim decoration.
  try:
   root=ET.fromstring(__import__('gzip').decompress(data) if source.suffix.lower()=='.svgz' else data);vb=list(map(float,root.get('viewBox','0 0 '+root.get('width','64')+' '+root.get('height','64')).split()));w,h=vb[2:]
   removed=0
   for parent in list(root.iter()):
    for node in list(parent):
     tag=node.tag.rsplit('}',1)[-1]
     full=parent is root and tag=='rect' and not node.get('transform') and float(node.get('width','0'))*float(node.get('height','0'))>w*h*.55
     decoration=node.get('id')=='tahoeShadow' or 'tahoeRim' in node.get('filter','')
     if full or decoration:parent.remove(node);removed+=1
   if removed:
    result=subprocess.run([RSVG,'-w',str(SIZE),'-h',str(SIZE)],input=ET.tostring(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=8)
    foreground=np.asarray(Image.open(io.BytesIO(result.stdout)).convert('RGBA'),dtype=np.float32)/255
    fa=foreground[:,:,3];fl=foreground[:,:,:3]@np.array([.2126,.7152,.0722],dtype=np.float32)
    retained=float(np.count_nonzero(fa>.9))/max(1,int(np.count_nonzero(alpha>.9)))
    if retained<.90:
     ink=np.clip((fa-.06)/.94,0,1)*(.55+.45*fl)
     shadow=np.zeros_like(ink)
    # A grouped/path-based container may still be present. In that case the
    # untouched raster contrast is safer than painting the whole tile as ink.
  except (ValueError,ET.ParseError,subprocess.SubprocessError):pass
 # Reject empty or solid mattes: successful decoding does not prove that the
 # application's symbol survived extraction. Use the untouched raster's contrast
 # field if a structural/grouped SVG could not be separated reliably.
 inside=central
 if np.count_nonzero(inside)<16:inside=alpha>.5
 values=ink[inside]
 if values.size and (float(values.max())<.12 or (float(values.std())<.015 and (float(values.mean())<.08 or float(values.mean())>.92))):
  ink=fallback_ink;shadow=fallback_shadow
  values=ink[inside]
  if values.size and float(values.max())<.12:
   samples=lum[inside];lo,hi=np.quantile(samples,[.02,.98])
   if hi-lo>.025:ink=np.clip((lum-lo)/(hi-lo),0,1)
 # Preserve surface relief at each contour, rather than recolor a flat bitmap.
 blur=np.asarray(Image.fromarray(np.uint8(np.clip(ink,0,1)*255)).filter(ImageFilter.GaussianBlur(.8)),dtype=np.float32)/255
 gy,gx=np.gradient(blur);relief=np.clip(-(gx+gy)*.5,-1,1)
 opaque=Image.fromarray(np.uint8(np.clip(alpha,0,1)*255));eroded=np.asarray(opaque.filter(ImageFilter.MinFilter(3)),dtype=np.float32)/255
 rim=np.clip(alpha-eroded,0,1)
 fields={'alpha':alpha.astype('float32'),'ink':ink.astype('float32'),'shadow':shadow.astype('float32'),'relief':relief.astype('float32'),'rim':rim.astype('float32')}
 temp=file.with_suffix('.tmp')
 with temp.open('wb') as f:np.savez_compressed(f,**fields)
 temp.replace(file);prepared[stamp]=fields
 if len(prepared)>24:prepared.popitem(last=False)
 return fields,stamp

def color(s):
 s=s.lstrip('#');s=s[-6:];return np.array([int(s[i:i+2],16)/255 for i in [0,2,4]],dtype=np.float32)
def render(job):
 begin=time.monotonic();fields,stamp=prepare(job);palette=job.get('palette',{});dark=job.get('dark',False);strength=float(job.get('strength',1))
 settings={k:job.get(k) for k in ['appearance','dark','palette','strength']};hashkey=hashlib.sha256((stamp+json.dumps(settings,sort_keys=True)).encode()).hexdigest();dest=CACHE/(hashkey+'.png')
 if dest.exists():return {'path':str(dest),'cached':True,'ms':round((time.monotonic()-begin)*1000)}
 ink=fields['ink'][...,None];alpha=fields['alpha'];shadow=fields['shadow'][...,None];relief=fields['relief'][...,None]
 bg=color(palette.get('container','#25252b' if dark else '#eeeef2'));fg=color(palette.get('ink','#ededf4' if dark else '#26262b'))
 if job.get('appearance')=='clear':bg=np.full(3,.12 if dark else .92);fg=np.full(3,.96 if dark else .14)
 # Colors mix in linear light; light and dark have independent material values.
 bg=bg**2.2;fg=fg**2.2
 result=bg[None,None,:]*(1-ink)+fg[None,None,:]*ink
 yy=np.linspace(0,1,SIZE,dtype=np.float32)[:,None,None]
 result=result*(1-strength*.11*yy)*(1-shadow*strength*.25)+relief*strength*.045
 xx=np.linspace(0,1,SIZE,dtype=np.float32)[None,:,None]
 result+=fields['rim'][...,None]*strength*(.10 if dark else .16)*(1-(xx+yy)*.4)
 result=np.clip(result,0,1)**(1/2.2)
 if job.get('appearance')=='clear':alpha=alpha*(.3+.7*fields['ink'])
 result[alpha<.005]=0
 rgba=np.dstack((result,alpha));image=Image.fromarray(np.uint8(np.clip(rgba,0,1)*255));temp=dest.with_suffix('.tmp');image.save(temp,format='PNG');temp.replace(dest)
 return {'path':str(dest),'cached':False,'ms':round((time.monotonic()-begin)*1000)}

def worker():
 global stopping
 while True:
  with lock:
   lock.wait_for(lambda:queue or stopping)
   if stopping:return
   job=queue.popleft()
  try:
   result=render(job)
   with lock:current=job.get('signature')==epoch
   if not current:emit({'type':'cancelled','key':job['key']});continue
   if index.get(job['key'])!=result['path']:
    index[job['key']]=result['path'];tmp=CACHE/'index.tmp';tmp.write_text(json.dumps(index,separators=(',',':')));tmp.replace(CACHE/'index.json')
   emit({'type':'rendered','key':job['key'],**result})
  except Exception as e:emit({'type':'error','key':job.get('key',''),'message':str(e)[:500]})
def main():
 global epoch,stopping
 emit({'type':'ready','index':index});thread=threading.Thread(target=worker,daemon=True);thread.start()
 for line in sys.stdin:
  try:
   job=json.loads(line)
   with lock:
    if job.get('action')=='quit':break
    if job.get('action')=='select':
     epoch=job['signature']
     while queue:emit({'type':'cancelled','key':queue.popleft()['key']})
    else:queue.append(job)
    lock.notify()
  except (ValueError,KeyError):pass
 with lock:stopping=True;lock.notify()
 thread.join(timeout=10)

if __name__=='__main__':main()
