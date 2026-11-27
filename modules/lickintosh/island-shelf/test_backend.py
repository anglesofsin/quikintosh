import importlib.util,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('shelf',Path(__file__).with_name('backend.py'));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ShelfTest(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.home=Path(self.temp.name);self.s=module.Shelf(self.home/'state');self.a=self.home/'a file.txt';self.a.write_text('original')
 def tearDown(self):self.temp.cleanup()
 def test_navigation_preferences_persist_and_limit_favorites(self):
  flags={'navigationShown':False,'navigationWidgets':False,'navigationTrayOnlyWithFiles':True,'navigationGestures':True,'navigationFavorites':['media','clipboard','batteries','storage','weather']}
  self.s.handle({'action':'utilityPreferences','values':flags})
  restored=module.Shelf(self.s.root).handle({'action':'utilityPreferences'})['values']
  self.assertFalse(restored['navigationShown']);self.assertTrue(restored['navigationTrayOnlyWithFiles']);self.assertEqual(restored['navigationFavorites'],flags['navigationFavorites'][:4])
 def test_navigation_invalid_favorites_rejected(self):
  with self.assertRaises(ValueError):self.s.handle({'action':'utilityPreferences','values':{'navigationFavorites':'media'}})
 def test_add_uri_and_dedupe(self):
  self.s.add([self.a.as_uri(),str(self.a)]);self.assertEqual(len(self.s.entries()),1);self.assertEqual(self.a.read_text(),'original')
 def test_remove_retains_original(self):
  self.s.add([str(self.a)]);self.s.handle({'action':'remove','paths':[str(self.a)]});self.assertTrue(self.a.exists());self.assertEqual(self.s.entries(),[])
 def test_pin_survives_clear_and_reload(self):
  self.s.add([str(self.a)]);self.s.handle({'action':'pin','paths':[str(self.a)]});self.s.handle({'action':'clear'});self.assertTrue(module.Shelf(self.s.root).entries()[0]['pinned'])
 def test_unknown_archive_rejected(self):
  with self.assertRaises(ValueError):self.s.archive([str(self.a)])
 def test_archive_returns_zip_with_original(self):
  self.s.add([str(self.a)])
  with patch.object(Path,'home',return_value=self.home):output=self.s.archive([str(self.a)])
  with zipfile.ZipFile(output) as z:self.assertEqual(z.read(self.a.name),b'original')
  self.assertEqual(self.a.read_text(),'original')
 def test_remote_uri_rejected(self):
  with self.assertRaises(ValueError):self.s.add(['file://remote/file'])
 def test_symlinks_not_archived(self):
  link=self.home/'link';link.symlink_to(self.a);self.s.add([str(link)])
  with self.assertRaises(ValueError):self.s.archive([str(link)])
 def test_activity_bounds_and_remove(self):
  result=self.s.handle({'action':'activity','activity':{'id':'build','title':'Compiling','progress':2,'ttl':99999}})
  self.assertEqual(result['items'][0]['progress'],1)
  self.assertLessEqual(result['items'][0]['expires']-module.time.time(),3600)
  self.assertEqual(self.s.handle({'action':'activity','activity':{'id':'build','remove':True}})['items'],[])
 def test_empty_activity_rejected(self):
  with self.assertRaises(ValueError):self.s.handle({'action':'activity','activity':{'id':'build','title':''}})
 def test_clipboard_reads_existing_store(self):
  folder=self.home/'.cache/quickshell/spotlight_clip';folder.mkdir(parents=True);(folder/'one.txt').write_text('hello')
  with patch.object(Path,'home',return_value=self.home):rows=self.s.clipboard()
  self.assertEqual(rows[0]['text'],'hello')
if __name__=='__main__':unittest.main()
