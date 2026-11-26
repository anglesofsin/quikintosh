import importlib.util,struct,tempfile,unittest
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
if __name__=='__main__':unittest.main()
