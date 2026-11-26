import importlib.util,tempfile,unittest,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ipcpath',ROOT/'modules/lickintosh/icon-styles/ipc-path.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class IpcPath(unittest.TestCase):
 def test_valid_cache_reuse_and_restart(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);processes=root/'proc';processes.mkdir();cache=root/'cache';a=root/'a-lickintosh-source-test';a.mkdir();(a/'shell.qml').touch();b=root/'b-lickintosh-source-test';b.mkdir();(b/'shell.qml').touch()
   p=processes/'123';p.mkdir();(p/'cmdline').write_bytes(('quickshell\0-p\0'+str(a)+'\0').encode())
   self.assertEqual(m.resolve('fallback',processes,cache),str(a));stamp=cache.stat().st_mtime_ns
   self.assertEqual(m.resolve('fallback',processes,cache),str(a));self.assertEqual(cache.stat().st_mtime_ns,stamp)
   (p/'cmdline').write_bytes(('quickshell\0-p\0'+str(b)+'\0').encode());self.assertEqual(m.resolve('fallback',processes,cache),str(b))
 def test_stale_cache_and_other_qs_clients(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);cache=root/'cache';cache.write_text('{"pid":"999","path":"old"}');p=root/'12';p.mkdir();(p/'cmdline').write_bytes(b'qs\0-p\0/tmp/picker.qml\0')
   self.assertEqual(m.resolve('fallback',root,cache),'fallback')
if __name__=='__main__':unittest.main()
