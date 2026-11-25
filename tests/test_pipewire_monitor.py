import importlib.util,json,unittest
from pathlib import Path
s=importlib.util.spec_from_file_location('pw_watch',Path(__file__).resolve().parents[1]/'modules/lickintosh/runtime-efficiency/pipewire_watch.py');pw=importlib.util.module_from_spec(s);s.loader.exec_module(pw)
class Monitor(unittest.TestCase):
 def test_fragmented_frames_unicode_and_multiple_messages(self):
  frames=pw.Frames();raw=(json.dumps([{'id':1,'name':'á'}],ensure_ascii=False)+json.dumps([{'id':2}])).encode();out=[]
  for byte in raw:out.extend(frames.feed(bytes([byte])))
  self.assertEqual(out,[[{'id':1,'name':'á'}],[{'id':2}]])
 def test_registry_merges_partial_updates_preserves_client_links_and_removes(self):
  r=pw.Registry();r.update([{'id':1,'type':'PipeWire:Interface:Node','info':{'state':'running','props':{'media.class':'Audio/Source','node.name':'mic'}}},{'id':2,'type':'PipeWire:Interface:Client','info':{'props':{'application.name':'Call'}}},{'id':3,'type':'PipeWire:Interface:Link','info':{'state':'active','props':{'link.output.node':1,'link.input.node':2}}},{'id':4,'type':'PipeWire:Interface:Port','info':{}}])
  self.assertEqual(len(r.values()),3)
  self.assertFalse(r.update([r.values()[0]]))
  self.assertTrue(r.update([{'id':1,'info':{'state':'idle'}}]));self.assertEqual(r.objects[1]['info']['props']['node.name'],'mic')
  r.update([{'id':1,'info':{'props':{'node.name':None}}}]);self.assertNotIn('node.name',r.objects[1]['info']['props'])
  self.assertTrue(r.update([{'id':1,'info':None}]));self.assertNotIn(1,r.objects)
 def test_broken_monitor_input_is_bounded(self):
  f=pw.Frames(limit=10)
  with self.assertRaises(ValueError):f.feed(b'['+b' '*15)
if __name__=='__main__':unittest.main()
