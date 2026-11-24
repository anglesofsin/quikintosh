"""Formats Quick Look can actually preview, plus non-recursive external openers."""
import json,mimetypes,os
from pathlib import Path
DESKTOP_ID='lickintosh-quicklook.desktop'
BASE_TYPES={
 'image/png','image/jpeg','image/gif','image/webp','image/avif','image/svg+xml','image/bmp','image/tiff','image/x-icon','image/vnd.microsoft.icon','image/x-icns','image/x-tga',
 'audio/mpeg','audio/flac','audio/ogg','audio/wav','audio/x-wav','audio/mp4','audio/aac','audio/opus','audio/x-aiff',
 'video/mp4','video/webm','video/x-matroska','video/quicktime','video/x-msvideo','video/mpeg','video/ogg',
 'application/pdf','application/json','application/ld+json','application/xml','application/javascript','application/x-yaml','application/toml',
 'application/zip','application/x-tar','application/gzip','application/x-gzip','application/x-bzip2','application/x-xz',
 'application/vnd.openxmlformats-officedocument.wordprocessingml.document','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','application/vnd.openxmlformats-officedocument.presentationml.presentation',
 'application/vnd.oasis.opendocument.text','application/vnd.oasis.opendocument.spreadsheet','application/vnd.oasis.opendocument.presentation','application/epub+zip',
 'font/ttf','font/otf','font/woff','font/woff2','application/x-font-ttf','application/x-font-opentype',
 'text/plain','text/html','text/css','text/csv','text/markdown','text/x-python','text/x-shellscript','text/x-log',
}
def supported_mimes():
 types=set(BASE_TYPES)
 candidates=set(mimetypes.types_map.values())
 for folder in os.environ.get('XDG_DATA_DIRS','/run/current-system/sw/share:/usr/share').split(':'):
  try:candidates.update((Path(folder)/'mime/types').read_text().splitlines())
  except OSError:pass
 types.update(t for t in candidates if t.startswith(('text/','audio/','video/')))
 return sorted(types)
def compatible_mime(mime):return mime in BASE_TYPES or mime.startswith(('text/','audio/','video/'))
def external_app(mime):
 from gi.repository import Gio
 current=Gio.AppInfo.get_default_for_type(mime,False)
 if current and current.get_id()!=DESKTOP_ID:return current
 try:
  previous=json.loads((Path.home()/'.local/state/lickintosh/desktop-profile/previous-openers.json').read_text()).get(mime,'')
  if previous and previous!=DESKTOP_ID:
   app=Gio.DesktopAppInfo.new(previous)
   if app:return app
 except (OSError,ValueError):pass
 return next((app for app in Gio.AppInfo.get_all_for_type(mime) if app.get_id()!=DESKTOP_ID),None)
