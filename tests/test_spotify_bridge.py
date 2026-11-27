import unittest,tempfile,sys,time,json,threading,urllib.request,urllib.error
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/'modules/lickintosh/island-shelf'))
from spotify_bridge import SpotifyBridge
from install_spotify_bridge import install
class SpotifyQueueTests(unittest.TestCase):
 def test_queue_scope_expiry_and_normalization(self):
  bridge=SpotifyBridge('/tmp/no-token');bus='org.mpris.MediaPlayer2.spotify'
  self.assertIsNone(bridge.queue(bus))
  events=[];bridge.on_update=lambda:events.append(True)
  bridge.accept({'items':[{'uri':'spotify:track:0123456789AB','title':'Next','artist':'Artist','art':'https://i.scdn.co/image/example','length':123},{'uri':'javascript:bad'}]})
  data=bridge.queue(bus);self.assertEqual(len(data['items']),1);self.assertEqual(data['items'][0]['title'],'Next');self.assertFalse(data['editable']);self.assertEqual(len(events),1)
  self.assertIsNone(bridge.queue('org.mpris.MediaPlayer2.vlc'));bridge.received-=16;self.assertIsNone(bridge.queue(bus))
 def test_installer_preserves_extensions_and_is_idempotent(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);config=root/'.config/spicetify/config-xpui.ini';config.parent.mkdir(parents=True);config.write_text('[AdditionalOptions]\nextensions = existing.js\n')
   install(root);install(root)
   self.assertEqual(config.read_text().count('quickintosh-queue.js'),1);self.assertIn('existing.js',config.read_text())
   token=root/'.local/state/quickintosh/island-shelf/spotify-bridge-token';self.assertEqual(token.stat().st_mode&0o777,0o600)
   extension=(config.parent/'Extensions/quickintosh-queue.js').read_text();self.assertNotIn('@LOCAL_BRIDGE_KEY@',extension)
 def test_loopback_authentication(self):
  with tempfile.TemporaryDirectory() as tmp:
   key=Path(tmp)/'spotify-bridge-token';key.write_text('local-test-key-'*4);key.chmod(0o600)
   bridge=SpotifyBridge(tmp);self.assertTrue(bridge.start(port=0));address='http://127.0.0.1:'+str(bridge.server.server_address[1])+'/queue'
   def send(origin,token):
    request=urllib.request.Request(address,data=b'{"items":[]}',headers={'Origin':origin,'X-Quickintosh-Key':token,'Content-Type':'application/json'})
    try:
     with urllib.request.urlopen(request,timeout=2) as response:return response.status
    except urllib.error.HTTPError as error:
     status=error.code;error.close();return status
   try:
    self.assertEqual(send('https://evil.example',key.read_text()),403)
    self.assertEqual(send('https://xpui.app.spotify.com','wrong'),403)
    self.assertEqual(send('https://xpui.app.spotify.com',key.read_text()),204)
    self.assertEqual(bridge.queue('org.mpris.MediaPlayer2.spotify')['items'],[])
   finally:bridge.server.shutdown();bridge.server.server_close()
 def test_bad_snapshot_rejected(self):
  bridge=SpotifyBridge('/tmp/no-token')
  with self.assertRaises(ValueError):bridge.accept({'items':'bad'})
if __name__=='__main__':unittest.main()
