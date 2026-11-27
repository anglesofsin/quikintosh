"""Real non-destructive file operations in an isolated home."""
import importlib.util,sys,tempfile,unittest,zipfile,json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]/'modules/lickintosh/island-shelf'
sys.path.insert(0,str(ROOT));spec=importlib.util.spec_from_file_location('shelf_backend',ROOT/'backend.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class Files(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name);(self.home/'Downloads').mkdir();self.patch=patch.object(Path,'home',return_value=self.home);self.patch.start();self.s=module.Shelf(self.home/'state');self.a=self.home/'original.txt';self.a.write_text('Keep the original');self.s.add([str(self.a)])
 def tearDown(self):self.patch.stop();self.tmp.cleanup()
 def test_archive_extract_preserves_original(self):
  name=self.s.archive([str(self.a)]);self.s.unpack([name]);self.assertEqual(self.a.read_text(),'Keep the original');self.assertTrue(any(p.is_dir() and (p/'original.txt').exists() for p in self.home.joinpath('Downloads').iterdir()))
 def test_zip_traversal_rejected(self):
  p=self.home/'bad.zip'
  with zipfile.ZipFile(p,'w') as z:z.writestr('../escape.txt','bad')
  self.s.add([str(p)])
  with self.assertRaises(ValueError):self.s.unpack([str(p)])
  self.assertFalse((self.home/'escape.txt').exists())
 def test_folder_copy_and_no_overwrite(self):
  self.s.folder_copy([str(self.a)],{});folder=next(p for p in (self.home/'Downloads').iterdir() if p.is_dir());self.assertEqual((folder/self.a.name).read_text(),self.a.read_text())
  with self.assertRaises(ValueError):self.s.folder_copy([str(self.a)],{'target':str(folder)})
 def test_rename_collision_and_reference(self):
  with self.assertRaises(ValueError):self.s.rename([str(self.a)],'../evil')
  (self.home/'exists').touch()
  with self.assertRaises(ValueError):self.s.rename([str(self.a)],'exists')
  self.s.rename([str(self.a)],'renamed.txt');self.assertEqual(self.s.items[0]['path'],str(self.home/'renamed.txt'))
 def test_remove_reference_only(self):
  self.s.handle({'action':'remove','paths':[str(self.a)]});self.assertTrue(self.a.exists());self.assertEqual(self.s.items,[])
 def test_tracking_only_new_files(self):
  folder=self.home/'tracked';folder.mkdir();(folder/'old.txt').touch();self.s.add([str(folder)]);self.s.handle({'action':'track','paths':[str(folder)]});(folder/'new.txt').touch();self.s.handle({'action':'scanTracked'});self.assertIn(str(folder/'new.txt'),[x['path'] for x in self.s.items]);self.assertNotIn(str(folder/'old.txt'),[x['path'] for x in self.s.items])
 def test_transform_keeps_original(self):
  from PIL import Image
  p=self.home/'picture.png';Image.new('RGB',(200,100),'red').save(p);original=p.read_bytes();self.s.add([str(p)]);out=self.s.transform({'paths':[str(p)],'operation':'resize','side':64,'format':'webp'});self.assertEqual(p.read_bytes(),original)
  with Image.open(out[0]) as i:self.assertEqual(i.size,(64,32))
 def test_metadata_and_pdf(self):
  from PIL import Image
  p=self.home/'picture.png';Image.new('RGB',(20,20),'blue').save(p);self.s.add([str(p)]);outputs=self.s.transform({'paths':[str(p)],'operation':'pdf'});self.assertTrue(Path(outputs[0]).read_bytes().startswith(b'%PDF'))
 def test_storage_not_recursive_scan(self):
  data=self.s.storage();self.assertGreater(data['total'],data['free']);self.assertGreaterEqual(data['cache'],0)
if __name__=='__main__':unittest.main()
