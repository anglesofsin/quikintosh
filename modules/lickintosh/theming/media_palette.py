"""Decode the first frame once per local wallpaper version, outside the UI thread."""
from pathlib import Path
import hashlib,os,subprocess,tempfile
VIDEO={'.mp4','.webm','.mkv','.mov','.m4v','.avi','.gif'}
def palette_image(source,cache):
 source=Path(source).expanduser()
 if source.suffix.lower() not in VIDEO:return source
 cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
 stat=source.stat();key=hashlib.sha256((str(source.resolve())+str(stat.st_mtime_ns)+str(stat.st_size)+'first-frame-v1').encode()).hexdigest()
 output=cache/(key+'.png')
 if output.is_file() and output.stat().st_size:return output
 fd,tmp=tempfile.mkstemp(dir=cache,suffix='.png');os.close(fd)
 try:
  subprocess.run(['ffmpeg','-nostdin','-v','error','-threads','1','-i',str(source),'-map','0:v:0','-frames:v','1','-vf','scale=1024:1024:force_original_aspect_ratio=decrease','-threads','1','-y',tmp],check=True,timeout=35,capture_output=True)
  if not Path(tmp).stat().st_size:raise ValueError('Wallpaper has no readable video frame')
  Path(tmp).replace(output)
 finally:Path(tmp).unlink(missing_ok=True)
 return output
