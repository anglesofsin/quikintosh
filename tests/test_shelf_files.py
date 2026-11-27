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
 def test_rename_folder_updates_child_reference(self):
  folder=self.home/'folder';folder.mkdir();child=folder/'child.txt';child.write_text('child');self.s.add([str(folder),str(child)]);self.s.rename([str(folder)],'renamed-folder');self.assertTrue((self.home/'renamed-folder/child.txt').exists());self.assertIn(str(self.home/'renamed-folder/child.txt'),[x['path'] for x in self.s.items])
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
 def test_saved_preset_roundtrip(self):
  self.s.presets({'action':'savePreset','name':'Web ready','settings':{'quality':65,'format':'webp','unsafe':'ignored'}})
  rows=self.s.presets({})['items'];self.assertEqual(rows[0]['settings'],{'quality':65,'format':'webp'})
  self.s.presets({'action':'removePreset','name':'Web ready'});self.assertEqual(self.s.presets({})['items'],[])
 def test_pdf_merge_rotate_extract_and_render(self):
  import pymupdf as fitz
  p=self.home/'one.pdf'
  with fitz.open() as doc:doc.new_page().insert_text((30,30),'Original text');doc.new_page();doc.save(p)
  self.s.add([str(p)]);original=p.read_bytes()
  rotated=self.s.transform({'operation':'rotate','paths':[str(p)]})[0]
  with fitz.open(rotated) as doc:self.assertEqual(doc[0].rotation,90)
  extracted=self.s.transform({'operation':'split','paths':[str(p)],'pages':'2'})
  with fitz.open(extracted[0]) as doc:self.assertEqual(doc.page_count,1)
  rendered=self.s.transform({'operation':'convert','paths':[str(p)],'pages':'1','format':'png'})
  from PIL import Image
  with Image.open(rendered[0]) as im:self.assertGreater(im.width,0)
  merged=self.s.transform({'operation':'pdf','paths':[str(p),rotated]})[0]
  with fitz.open(merged) as doc:self.assertEqual(doc.page_count,4)
  self.assertEqual(p.read_bytes(),original)
 def test_video_resize_and_frame_rate(self):
  import subprocess
  p=self.home/'video.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=160x96:r=12:d=0.5','-threads','1','-c:v','libx264',str(p)],check=True)
  original=p.read_bytes();self.s.add([str(p)]);out=self.s.transform({'operation':'resize','paths':[str(p)],'side':80,'fps':6,'format':'mp4'})[0]
  probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',out]));self.assertEqual(probe['streams'][0]['width'],80);self.assertEqual(probe['streams'][0]['r_frame_rate'],'6/1');self.assertEqual(p.read_bytes(),original)
 def test_uninstall_requires_current_app_and_confirmation(self):
  with self.assertRaises(ValueError):self.s.uninstall({'id':'unknown','confirmed':True})
 def test_transform_job_does_not_write_tray(self):
  import subprocess,os
  from PIL import Image
  p=self.home/'picture.png';Image.new('RGB',(20,20),'red').save(p)
  env=dict(os.environ,HOME=str(self.home));state=self.home/'.local/state/quickintosh/island-shelf';worker=module.Shelf(state);worker.add([str(p)])
  result=subprocess.run([sys.executable,str(ROOT/'backend.py'),'--transform-job'],input=json.dumps({'paths':[str(p)],'operation':'resize','side':10})+'\n',env=env,capture_output=True,text=True,check=True)
  data=json.loads(result.stdout);self.assertEqual(data['type'],'transformDone');self.assertEqual(len(json.loads((state/'tray.json').read_text())),1);self.assertTrue(Path(data['paths'][0]).exists())
 def test_batch_rename_pattern_and_collision(self):
  second=self.home/'second.txt';second.write_text('Second');self.s.add([str(second)])
  result=self.s.rename_many({'paths':[str(self.a),str(second)],'pattern':'Document-{index}{ext}'})
  self.assertEqual([Path(p).name for p in result],['Document-1.txt','Document-2.txt']);self.assertEqual(Path(result[0]).read_text(),'Keep the original')
  with self.assertRaises(ValueError):self.s.rename_many({'paths':result,'pattern':'duplicate.txt'})
 def test_size_based_image_compression(self):
  from PIL import Image
  p=self.home/'image.png';Image.effect_noise((512,512),80).convert('RGB').save(p);self.s.add([str(p)])
  result=self.s.transform({'paths':[str(p)],'operation':'compress','format':'jpeg','targetBytes':25000,'quality':90})
  self.assertLessEqual(Path(result[0]).stat().st_size,25000);self.assertTrue(p.exists())
 def test_storage_not_recursive_scan(self):
  data=self.s.storage();self.assertGreater(data['total'],data['free']);self.assertGreaterEqual(data['cache'],0)
if __name__=='__main__':unittest.main()
