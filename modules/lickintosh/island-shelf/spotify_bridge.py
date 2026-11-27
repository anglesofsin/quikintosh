"""Authenticated loopback-only queue snapshots from the user's Spicetify extension.

Never accesses Spotify credentials. The random local bridge key is unrelated to
Spotify and is readable only by the current user. Snapshots expire after 15s.
"""
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import hmac,json,threading,time,re
PORT=43891
ORIGINS={'https://xpui.app.spotify.com','https://zlink.app.spotify.com'}
class SpotifyBridge:
 def __init__(self,root):self.root=Path(root);self.snapshot=None;self.received=0;self.server=None;self.on_update=None
 def queue(self,bus):
  if self.snapshot is None or not re.fullmatch(r'org\.mpris\.MediaPlayer2\.spotify(?:\.[A-Za-z0-9_-]+)*',bus or '') or time.monotonic()-self.received>15:return None
  return dict(type='queue',player=bus,supported=True,editable=False,provider='spicetify',fetched=True,current='',items=self.snapshot or [])
 def accept(self,value):
  if not isinstance(value,dict) or not isinstance(value.get('items'),list):raise ValueError('Expected queue items')
  rows=[]
  for index,item in enumerate(value['items'][:200]):
   if not isinstance(item,dict):continue
   uri=str(item.get('uri',''))
   if not re.fullmatch(r'spotify:(?:track|episode):[A-Za-z0-9]{10,64}',uri):continue
   art=str(item.get('art',''))
   if not art.startswith('https://'):art=''
   rows.append(dict(id=str(index)+':'+uri,uri=uri,title=str(item.get('title',''))[:300],artist=str(item.get('artist',''))[:300],art=art[:2048],length=max(0,min(86400,float(item.get('length',0) or 0)))))
  self.snapshot=rows;self.received=time.monotonic()
  if self.on_update:self.on_update()
 def start(self,port=PORT):
  key=self.root/'spotify-bridge-token'
  if not key.is_file() or key.is_symlink() or key.stat().st_mode&0o077:return False
  token=key.read_text().strip()
  if len(token)<32:return False
  bridge=self
  class Handler(BaseHTTPRequestHandler):
   def log_message(self,*args):pass
   def reply(self,status):
    self.send_response(status)
    origin=self.headers.get('Origin','')
    if origin in ORIGINS:self.send_header('Access-Control-Allow-Origin',origin)
    self.send_header('Access-Control-Allow-Private-Network','true');self.send_header('Access-Control-Allow-Headers','Content-Type, X-Quickintosh-Key');self.send_header('Access-Control-Allow-Methods','POST, OPTIONS');self.send_header('Content-Length','0');self.end_headers()
   def do_OPTIONS(self):self.reply(204 if self.headers.get('Origin') in ORIGINS else 403)
   def do_POST(self):
    self.connection.settimeout(2)
    if self.path!='/queue' or self.headers.get('Origin') not in ORIGINS or not hmac.compare_digest(self.headers.get('X-Quickintosh-Key',''),token):self.reply(403);return
    try:
     size=int(self.headers.get('Content-Length','0'))
     if not 0<size<=262144:raise ValueError('size')
     bridge.accept(json.loads(self.rfile.read(size)));self.reply(204)
    except (ValueError,TypeError,TimeoutError):self.reply(400)
  try:self.server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
  except OSError:return False
  self.server.daemon_threads=True;threading.Thread(target=self.server.serve_forever,daemon=True,name='spotify-local-queue').start();return True
