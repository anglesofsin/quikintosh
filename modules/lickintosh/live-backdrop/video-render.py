"""Prepare optional wallpaper playback copies; never rewrite source media."""
import fcntl, hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path

HEIGHTS = (0, 720, 1080, 1440, 2160)
RATES = (0, 15, 24, 30, 60, 120)

def prepare(request, cache=None):
    source = Path(request['source']).expanduser().resolve(strict=True)
    height, fps = int(request.get('height', 0)), int(request.get('fps', 0))
    if height not in HEIGHTS or fps not in RATES:
        raise ValueError('Unsupported wallpaper resolution or frame rate')
    if not height and not fps:
        return str(source)
    stat = source.stat()
    identity = f'v1|{source}|{stat.st_mtime_ns}|{stat.st_size}|{height}|{fps}'
    key = hashlib.sha256(identity.encode()).hexdigest()
    directory = Path(cache or os.environ.get('XDG_CACHE_HOME', str(Path.home()/'.cache'))) / 'quickintosh/wallpaper-render'
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (key+'.mp4')
    with (directory/(key+'.lock')).open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if target.exists() and target.stat().st_size:
            return str(target)
        probe = subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate','-of','json',str(source)],capture_output=True,text=True,check=True,timeout=30)
        streams = json.loads(probe.stdout)['streams']
        if not streams:
            raise ValueError('No video stream found')
        stream = streams[0]
        # Resolution is a maximum frame box; never stretch or enlarge the source.
        filters = []
        if height and (int(stream["width"]) > height*16//9 or int(stream["height"]) > height):
            width = height*16//9
            filters.append(f'scale=w=min(iw\\,{width}):h=min(ih\\,{height}):force_original_aspect_ratio=decrease:force_divisible_by=2')
        if fps:
            numerator, denominator = stream.get('avg_frame_rate','0/1').split('/')
            original_rate = float(numerator)/max(1,float(denominator))
            if original_rate > fps:
                filters.append(f'fps={fps}')
        if not filters:
            return str(source)
        fd, temporary = tempfile.mkstemp(prefix=key+'-',suffix='.mp4',dir=directory)
        os.close(fd)
        try:
            args = ['ffmpeg','-nostdin','-v','error','-y','-filter_threads','1','-i',str(source),'-map','0:v:0','-an','-vf',','.join(filters),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','2','-movflags','+faststart',temporary]
            result = subprocess.run(args,capture_output=True,text=True)
            if result.returncode:
                raise RuntimeError(result.stderr.strip()[-500:] or 'Video conversion failed')
            os.replace(temporary,target)
        finally:
            Path(temporary).unlink(missing_ok=True)
    return str(target)

def main():
    try:
        os.nice(10)
    except OSError:
        pass
    for line in sys.stdin:
        request = {}
        try:
            request = json.loads(line)
            response = dict(request, path=prepare(request), error='')
        except Exception as error:
            response = dict(request, path='', error=str(error))
        print(json.dumps(response),flush=True)

if __name__ == '__main__':
    main()
