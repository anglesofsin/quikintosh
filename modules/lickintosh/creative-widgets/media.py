"""Local-only widget libraries, bounded metadata and cached video posters."""
import hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
MEDIA={'.png','.jpg','.jpeg','.webp','.avif','.gif','.bmp','.tif','.tiff','.mp4','.mkv','.webm','.mov','.m4v','.avi','.ogv'}
VIDEO={'.mp4','.mkv','.webm','.mov','.m4v','.avi','.ogv'}
FFMPEG='@FFMPEG@';FFPROBE='@FFPROBE@'
def local(value):
 from urllib.parse import urlsplit,unquote
 if value.startswith('file:'):
  parsed=urlsplit(value)
  if parsed.netloc not in ('','localhost'):raise ValueError('Local files only')
  value=unquote(parsed.path)
 if '://' in value:raise ValueError('Local files only')
 return Path(value).expanduser().absolute()
def scan(value,recursive=False,sort='name'):
 directory=local(value)
 if not directory.is_dir():return {'files':[],'error':'Folder not found'}
 files=[]
 for base,dirs,names in os.walk(directory,followlinks=False):
  dirs[:]=sorted(d for d in dirs if not d.startswith('.')) if recursive else []
  for name in sorted(names):
   p=Path(base)/name
   if not name.startswith('.') and p.suffix.lower() in MEDIA and p.is_file():files.append(p)
   if len(files)>=3000:break
  if len(files)>=3000:break
 if sort=='modified':files.sort(key=lambda p:(-p.stat().st_mtime,str(p).casefold()))
 else:files.sort(key=lambda p:str(p.relative_to(directory)).casefold())
 return {'files':[str(p) for p in files],'limited':len(files)>=3000,'error':''}
def metadata(value):
 p=local(value)
 if not p.is_file():return {}
 r=subprocess.run([FFPROBE,'-v','error','-show_entries','format=duration:format_tags=title,artist,album','-of','json',str(p)],capture_output=True,timeout=6,check=True)
 data=json.loads(r.stdout[:128000]);fmt=data.get('format',{});tags=fmt.get('tags',{})
 return {key:str(tags.get(key,'')).strip()[:500] for key in ['title','artist','album']} | {'duration':float(fmt.get('duration',0))}
def poster(value):
 p=local(value)
 if p.suffix.lower() not in VIDEO or not p.is_file():return {'poster':''}
 stat=p.stat();key=hashlib.sha256((str(p)+str(stat.st_size)+str(stat.st_mtime_ns)).encode()).hexdigest()
 cache=Path(os.environ.get('XDG_CACHE_HOME',str(Path.home()/'.cache')))/'quickintosh/widget-posters';cache.mkdir(mode=0o700,parents=True,exist_ok=True)
 dest=cache/(key+'.jpg')
 if not dest.exists():
  fd,name=tempfile.mkstemp(suffix='.jpg',dir=cache);os.close(fd)
  try:
   subprocess.run([FFMPEG,'-v','error','-nostdin','-y','-i',str(p),'-frames:v','1','-vf','scale=640:640:force_original_aspect_ratio=decrease','-q:v','3',name],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=12,check=True)
   Path(name).replace(dest)
  finally:Path(name).unlink(missing_ok=True)
  files=sorted(cache.glob('*.jpg'),key=lambda f:f.stat().st_mtime,reverse=True)
  for old in files[160:]:old.unlink(missing_ok=True)
 return {'poster':dest.as_uri()}
def main():
 try:
  action,value=sys.argv[1:3]
  result=scan(value,len(sys.argv)>3 and sys.argv[3]=='true',sys.argv[4] if len(sys.argv)>4 else 'name') if action=='scan' else metadata(value) if action=='metadata' else poster(value) if action=='poster' else {}
 except (OSError,ValueError,subprocess.SubprocessError) as error:result={'error':type(error).__name__,'files':[],'poster':''}
 print(json.dumps(result,ensure_ascii=True))
if __name__=='__main__':main()
