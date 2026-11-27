import base64,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'modules/lickintosh/island-shelf'))
from mcp_server import Server
class McpTests(unittest.TestCase):
 def test_defaults_read_only(self):
  server=Server(runner=lambda *args:'ready')
  self.assertEqual([t['name'] for t in server.tools()],['quickintosh_status'])
  self.assertTrue(server.dispatch(dict(id=2,method='tools/call',params=dict(name='shelf_open',arguments={'page':0})))['result']['isError'])
 def test_initialise(self):
  result=Server().dispatch(dict(id=1,method='initialize'))
  self.assertEqual(result['result']['protocolVersion'],'2025-03-26')
  self.assertIsNone(Server().dispatch(dict(method='notifications/initialized')))
 def test_bounded_open(self):
  calls=[];server=Server(['ui'],runner=lambda *args:calls.append(args) or 'opened')
  self.assertEqual(server.call('shelf_open',{'page':6}),'opened')
  self.assertEqual(calls,[('shelf','open','6')])
  for value in [-1,15,True,'0']:
   with self.assertRaises(ValueError):server.call('shelf_open',{'page':value})
 def test_paths_preserve_unicode(self):
  calls=[];server=Server(['files'],runner=lambda *args:calls.append(args) or 'queued')
  with tempfile.TemporaryDirectory() as tmp:
   file=Path(tmp)/'Olá.txt';file.write_text('test')
   server.call('shelf_add_files',{'paths':[str(file)]})
   self.assertEqual(json.loads(base64.b64decode(calls[0][-1])),[str(file)])
  with self.assertRaises(ValueError):server.call('shelf_add_files',{'paths':['relative']})
 def test_activity_validation(self):
  server=Server(['activities'],runner=lambda *args:'queued')
  self.assertEqual(server.call('shelf_activity',dict(id='build',title='Build',progress=.5,ttl=60)),'queued')
  for args in [dict(id='a',title='b',progress=9),dict(id='a',title='b',command='rm'),dict(id='a',title='b',ttl=99999)]:
   with self.assertRaises(ValueError):server.call('shelf_activity',args)
 def test_rate_limit(self):
  server=Server(runner=lambda *args:'ready')
  for _ in range(60):server.call('quickintosh_status',{})
  with self.assertRaises(ValueError):server.call('quickintosh_status',{})
if __name__=='__main__':unittest.main()
