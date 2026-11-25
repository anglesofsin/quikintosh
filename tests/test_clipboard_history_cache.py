import importlib.util,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
s=importlib.util.spec_from_file_location('history',Path(__file__).resolve().parents[1]/'modules/lickintosh/runtime-efficiency/clipboard_history.py');h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
class History(unittest.TestCase):
 def test_hashes_are_reused_and_edits_invalidate_them(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);files=root/'files';files.mkdir();cache=root/'cache/index.json'
   (files/'one.txt').write_text('Hello\nworld');(files/'two.png').write_bytes(b'image bytes')
   with patch.object(h,'digest',wraps=h.digest) as digest:
    first=h.history(files,10,cache);self.assertEqual(digest.call_count,2);self.assertEqual(len(first),2)
    self.assertIn('Hello world',[row[2] for row in first]);mtime=cache.stat().st_mtime_ns
    self.assertEqual(h.history(files,10,cache),first);self.assertEqual(digest.call_count,2);self.assertEqual(cache.stat().st_mtime_ns,mtime)
    (files/'one.txt').write_text('Changed');h.history(files,10,cache);self.assertEqual(digest.call_count,3)
   self.assertEqual(cache.stat().st_mode & 0o777,0o600)
   self.assertNotIn('Changed',cache.read_text())
 def test_duplicates_bounds_and_removed_entries(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);files=root/'files';files.mkdir();cache=root/'index.json'
   for n in range(3):(files/(str(n)+'.txt')).write_text('same')
   self.assertEqual(len(h.history(files,2,cache)),1)
   for path in files.iterdir():path.unlink()
   self.assertEqual(h.history(files,2,cache),[])
if __name__=='__main__':unittest.main()
