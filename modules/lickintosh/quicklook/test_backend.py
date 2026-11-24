import importlib.util,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('quicklook_backend',Path(__file__).with_name('backend.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class QuickLookBackendTests(unittest.TestCase):
 def test_local_uri_and_text_limits(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'space # á.txt';p.write_text('Hello preview')
   self.assertEqual(b.local_path(p.as_uri()),p)
   self.assertEqual(b.describe(p.as_uri())['text'],'Hello preview')
   p.write_text('a'*(b.MAX_TEXT+8));self.assertIn('truncated',b.describe(str(p))['text'])
  for uri in ['https://example.org/a','file://remote/tmp/a','relative.txt']:
   with self.assertRaises(ValueError):b.local_path(uri)
 def test_copy_move_collision_and_link(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);src=root/'source';dst=root/'target';src.mkdir();dst.mkdir();p=src/'sample.txt';p.write_text('preserve me');(dst/p.name).write_text('existing')
   outputs=b.transfer([p.as_uri()],str(dst));self.assertEqual((dst/'sample.txt').read_text(),'existing');self.assertEqual(Path(outputs[0]).read_text(),'preserve me');self.assertTrue(p.exists())
   outputs=b.transfer([str(p)],str(dst),'move');self.assertFalse(p.exists());self.assertEqual(Path(outputs[0]).read_text(),'preserve me')
   f=src/'folder';f.mkdir();(f/'inside').write_text('contents')
   output=b.transfer([str(f)],str(dst),'link')[0];self.assertTrue(Path(output).is_symlink())
   with self.assertRaises(ValueError):b.transfer([str(src)],str(f))
 def test_same_folder_copy_duplicates_but_move_preserves_path(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'existing.txt';p.write_text('original')
   copied=b.transfer([str(p)],folder,'copy');self.assertNotEqual(copied,[str(p)]);self.assertEqual(p.read_text(),'original')
   self.assertEqual(b.transfer([str(p)],folder,'move'),[str(p)])
 def test_rotate_saves_copy_without_overwrite(self):
  from PIL import Image
  with tempfile.TemporaryDirectory() as folder:
   original=Path(folder)/'photo.png';Image.new('RGB',(60,40),'red').save(original);before=original.read_bytes()
   a=b.rotate_copy(str(original),-90);c=b.rotate_copy(str(original),-90)
   self.assertNotEqual(a,c);self.assertEqual(original.read_bytes(),before)
   with Image.open(a) as image:self.assertEqual(image.size,(40,60))
 def test_file_menu_rename_and_duplicate_do_not_overwrite(self):
  from gi.repository import GLib
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);source=root/'before.txt';source.write_text('original');other=root/'occupied.txt';other.write_text('preserve')
   with self.assertRaises(GLib.Error):b.file_operation('rename',[str(source)],'occupied.txt')
   self.assertEqual(source.read_text(),'original');self.assertEqual(other.read_text(),'preserve')
   for name in ['../escape','.','', 'a/b']:
    with self.assertRaises(ValueError):b.file_operation('rename',[str(source)],name)
   result=b.file_operation('rename',[str(source)],'after # á.txt');target=Path(result['paths'][0]);self.assertFalse(source.exists());self.assertEqual(target.read_text(),'original');self.assertEqual(result['changes'],[{'old':str(source),'new':str(target)}])
   duplicated=b.file_operation('duplicate',[str(target)]);self.assertNotEqual(duplicated['paths'],[str(target)]);self.assertEqual(Path(duplicated['paths'][0]).read_text(),'original')
 def test_permanent_delete_rejects_files_outside_trash(self):
  with tempfile.TemporaryDirectory() as folder:
   file=Path(folder)/'keep.txt';file.write_text('preserved')
   for value in [str(file),file.as_uri(),'trash:///../keep.txt','trash:///']:
    with self.assertRaises(ValueError):b.file_operation('delete',[value])
   self.assertEqual(file.read_text(),'preserved')
 def test_paste_uses_file_clipboard_and_preserves_existing_targets(self):
  import types
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);dest=root/'destination';dest.mkdir();source=root/'one # á.txt';source.write_text('copy');(dest/source.name).write_text('existing')
   content=('copy\n'+source.as_uri()+'\n').encode()
   with patch.object(b.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout=content)):
    result=b.file_operation('paste',[],destination=str(dest))
   self.assertEqual(source.read_text(),'copy');self.assertEqual((dest/source.name).read_text(),'existing');self.assertEqual(Path(result['paths'][0]).read_text(),'copy')
 def test_archive_preview_never_extracts(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'archive.zip'
   with zipfile.ZipFile(p,'w') as archive:archive.writestr('../outside','content')
   result=b.describe(str(p));self.assertEqual(result['kind'],'archive');self.assertEqual(result['entries'][0]['name'],'../outside');self.assertFalse((Path(folder)/'outside').exists())
 def test_docx_text_and_binary(self):
  with tempfile.TemporaryDirectory() as folder:
   p=Path(folder)/'document.docx'
   with zipfile.ZipFile(p,'w') as archive:archive.writestr('word/document.xml','<document><p>Quick Look document</p></document>')
   self.assertIn('Quick Look document',b.describe(str(p))['text'])
   p=Path(folder)/'binary';p.write_bytes(b'\0\xff\0');self.assertEqual(b.describe(str(p))['kind'],'binary')
class QuickLookAssociationTests(unittest.TestCase):
 def test_external_app_never_returns_quicklook_default(self):
  import sys,json,types
  from mime_types import external_app,DESKTOP_ID
  class App:
   def __init__(self,key):self.key=key
   def get_id(self):return self.key
  quicklook=App(DESKTOP_ID);editor=App('editor.desktop')
  fake=types.SimpleNamespace(AppInfo=types.SimpleNamespace(get_default_for_type=lambda *_:quicklook,get_all_for_type=lambda *_:[quicklook,editor]),DesktopAppInfo=types.SimpleNamespace(new=lambda key:editor if key=='editor.desktop' else None))
  with tempfile.TemporaryDirectory() as folder,patch.dict(sys.modules,{'gi.repository':types.SimpleNamespace(Gio=fake)}),patch.object(Path,'home',return_value=Path(folder)):
   self.assertIs(external_app('text/plain'),editor)
 def test_default_opener_encodes_selection_for_quickshell_cli(self):
  import sys,types,json,base64
  spec=importlib.util.spec_from_file_location('quicklook_opener',Path(__file__).with_name('open.py'));opener=importlib.util.module_from_spec(spec);spec.loader.exec_module(opener)
  fake=types.SimpleNamespace(content_type_guess=lambda *_:('text/plain',False))
  with tempfile.TemporaryDirectory() as folder,patch.dict(sys.modules,{'gi.repository':types.SimpleNamespace(Gio=fake)}):
   paths=[Path(folder)/'file [one] # á.txt',Path(folder)/'file two.txt']
   for path in paths:path.write_text('test')
   with patch.object(opener.subprocess,'run',return_value=types.SimpleNamespace(returncode=0,stdout='opened\n')) as call:
    self.assertEqual(opener.main([str(path) for path in paths]),0)
    command=call.call_args.args[0];self.assertEqual(command[1:5],['ipc','call','quicklook','openFiles'])
    self.assertEqual(json.loads(base64.b64decode(command[-1])),[str(path) for path in paths])
 def test_supported_types_exclude_programs_and_directories(self):
  from mime_types import compatible_mime
  for mime in ['image/png','video/mp4','application/pdf','text/x-python','application/zip']:
   self.assertTrue(compatible_mime(mime))
  for mime in ['application/x-executable','application/x-desktop','inode/directory']:
   self.assertFalse(compatible_mime(mime))

if __name__=='__main__' :unittest.main()
