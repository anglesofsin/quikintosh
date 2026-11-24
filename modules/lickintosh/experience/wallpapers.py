"""Wallpaper inventory and demand-driven thumbnails; never touch originals."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import subprocess
import sys
import threading

IMAGES = {'.jpg', '.jpeg', '.png', '.webp', '.avif', '.bmp', '.gif', '.tif', '.tiff'}
VIDEOS = {'.mp4', '.webm', '.mkv', '.mov', '.m4v'}
OUTPUT = threading.Lock()


def inventory(directory):
    directory = Path(directory).expanduser()
    result = []
    for folder, dirs, files in os.walk(directory, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not d.startswith('.'))
        for name in files:
            p = Path(folder) / name
            if p.suffix.lower() not in IMAGES | VIDEOS:
                continue
            try:
                info = p.stat()
                result.append({'path': str(p), 'name': name, 'video': p.suffix.lower() in VIDEOS,
                               'version': f'{info.st_mtime_ns}:{info.st_size}'})
            except OSError:
                continue
    return sorted(result, key=lambda item: item['name'].casefold())


def thumbnail_path(item, cache):
    key = hashlib.sha256((item['path'] + '\0' + item['version']).encode()).hexdigest()
    return Path(cache) / (key + '.jpg')


def make_thumbnail(item, cache):
    from PIL import Image, ImageOps
    target = thumbnail_path(item, cache)
    if target.is_file():
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(f'.{os.getpid()}.{threading.get_ident()}.tmp')
    try:
        if item['video']:
            subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-i', item['path'], '-frames:v', '1',
                            '-vf', 'scale=320:180:force_original_aspect_ratio=decrease',
                            '-threads', '1', '-f', 'image2', '-vcodec', 'mjpeg', '-y', str(temporary)],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=12)
        else:
            with Image.open(item['path']) as image:
                image.draft('RGB', (640, 360))
                image.thumbnail((480, 320))
                image = ImageOps.exif_transpose(image).convert('RGB')
                image.save(temporary, format='JPEG', quality=82)
        temporary.replace(target)
        return target
    finally:
        temporary.unlink(missing_ok=True)


def emit(value):
    with OUTPUT:
        print(json.dumps(value, ensure_ascii=True), flush=True)


def worker(cache):
    items = {}
    pending = set()
    lock = threading.Lock()
    pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='wallpaper-thumb')

    def finish(item):
        try:
            path = make_thumbnail(item, cache)
            emit({'type': 'thumbnail', 'path': item['path'], 'version': item['version'], 'url': path.as_uri()})
        except Exception:
            emit({'type': 'thumbnail', 'path': item['path'], 'version': item['version'], 'url': '', 'failed': True})
        finally:
            with lock:
                pending.discard(item['path'])

    emit({'type': 'ready'})
    try:
        for line in sys.stdin:
            try:
                request = json.loads(line)
                if request['action'] == 'scan':
                    entries = inventory(request['directory'])
                    for item in entries:
                        items[item['path']] = item
                        thumb = thumbnail_path(item, cache)
                        item['thumb'] = thumb.as_uri() if thumb.is_file() else ''
                    emit({'type': 'inventory', 'group': request['group'], 'items': entries})
                elif request['action'] == 'thumbnails':
                    # Bound the queue to a viewport, so rapidly scrolling cannot
                    # enqueue the entire library and contend with shell rendering.
                    with lock:
                        for path in request.get('paths', []):
                            if path in items and path not in pending and len(pending) < 64:
                                pending.add(path)
                                pool.submit(finish, items[path].copy())
                            elif path in items and path not in pending:
                                emit({'type':'deferred','path':path,'version':items[path]['version']})
            except Exception as error:
                emit({'type': 'error', 'message': str(error)})
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def main():
    if sys.argv[1] == '--worker':
        worker(sys.argv[2])
        return
    directory, cache = sys.argv[1:3]
    generate = '--generate' in sys.argv[3:]
    for item in inventory(directory):
        if generate and not item['video']:
            try:
                make_thumbnail(item, cache)
            except Exception:
                pass
        elif not generate:
            target = thumbnail_path(item, cache)
            print(item['path'] + '\t' + (str(target) if target.is_file() else ''))


if __name__ == '__main__':
    main()
