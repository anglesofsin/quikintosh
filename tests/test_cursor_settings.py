import importlib.util,struct,tempfile,unittest,zipfile
from pathlib import Path
spec=importlib.util.spec_from_file_location('cursor_settings',Path(__file__).resolve().parents[1]/'modules/lickintosh/cursor/cursor_settings.py');cursor=importlib.util.module_from_spec(spec);spec.loader.exec_module(cursor)
class CursorTint(unittest.TestCase):
 def test_recolors_fill_preserves_outline_alpha_and_frames(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);source=root/'src';source.mkdir();target=root/'dst'
   pixels=[0xff000000,0xffffffff,0x80000000,0]
   data=struct.pack('<4I',0x72756358,16,0x10000,1)+struct.pack('<3I',0xfffd0002,24,28)+struct.pack('<9I',36,0xfffd0002,24,1,2,2,0,0,50)+struct.pack('<4I',*pixels)
   (source/'left_ptr').write_bytes(data);(source/'default').symlink_to('left_ptr')
   cursor.tint(source,target,'#007aff')
   result=struct.unpack_from('<4I',(target/'left_ptr').read_bytes(),64)
   self.assertEqual(result[1],0xffffffff);self.assertEqual(result[2]>>24,128);self.assertEqual(result[3],0)
   self.assertNotEqual(result[0],pixels[0]);self.assertEqual((target/'default').read_bytes(),(target/'left_ptr').read_bytes())
 def test_vector_tint_retains_frames_and_metadata(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);source=root/'source';dest=root/'dest';(source/'hyprcursors').mkdir(parents=True)
   (source/'manifest.hl').write_text('name = Original\ncursors_directory = hyprcursors\n')
   metadata=b'hotspot_x = 0.125\ndefine_override = left_ptr\ndefine_size = 0, image.svg, 30\n'
   with zipfile.ZipFile(source/'hyprcursors/default.hlc','w') as archive:
    archive.writestr('meta.hl',metadata)
    archive.writestr('image.svg','<svg><path style="fill:#000"/><path fill="#fff"/></svg>')
   cursor.tint_hd(source,dest,'#007aff')
   with zipfile.ZipFile(dest/'hyprcursors/default.hlc') as archive:
    self.assertEqual(archive.read('meta.hl'),metadata)
    image=archive.read('image.svg').decode()
    self.assertNotIn('fill:#000',image)
    self.assertIn('fill="#fff"',image)
    self.assertIn('fill:#004fa6',image)
   self.assertTrue((dest/'.vector-cache-v1').exists())
if __name__=='__main__':unittest.main()
