import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import subprocess
spec=importlib.util.spec_from_file_location('desktop_operations',Path(__file__).with_name('operations.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class DesktopOperationsTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
  self.root=Path(self.temp.name);self.desktop=self.root/'Desktop';self.desktop.mkdir();self.other=self.root/'Other';self.other.mkdir();self.ops=m.Operations(self.root/'data')
 def file(self,name='space # á.txt'):
  path=self.other/name;path.write_text('original');return path
 def perform(self,op,paths=(),**kw):return self.ops.perform(dict(operation=op,paths=list(map(str,paths)),destination=str(self.desktop),**kw))
 def test_copy_collision_and_undo_redo(self):
  src=self.file();(self.desktop/src.name).write_text('existing')
  target=Path(self.perform('transfer',[src])[0]);self.assertNotEqual(target.name,src.name)
  self.perform('undo');self.assertFalse(target.exists());self.assertTrue(src.exists());self.assertEqual((self.desktop/src.name).read_text(),'existing')
  self.perform('redo');self.assertEqual(target.read_text(),'original')
 def test_move_undo_redo(self):
  src=self.file();target=Path(self.perform('transfer',[src],mode='move')[0]);self.assertFalse(src.exists())
  self.perform('undo');self.assertTrue(src.exists());self.assertFalse(target.exists())
  self.perform('redo');self.assertTrue(target.exists());self.assertFalse(src.exists())
 def test_trash_restore_metadata(self):
  src=self.file();self.perform('trash',[src]);self.assertFalse(src.exists())
  info=next((self.ops.trash/'info').iterdir()).read_text();self.assertIn('%23',info);self.assertIn('%C3%A1',info)
  self.perform('undo');self.assertEqual(src.read_text(),'original');self.assertFalse(list((self.ops.trash/'info').iterdir()))
  self.perform('redo');self.assertFalse(src.exists())
 def test_undo_refuses_overwrite_retains_history(self):
  src=self.file();target=Path(self.perform('transfer',[src],mode='move')[0]);src.write_text('new occupant')
  with self.assertRaises(FileExistsError):self.perform('undo')
  self.assertEqual(src.read_text(),'new occupant');self.assertTrue(target.exists());self.assertEqual(len(self.ops.undo_stack),1)
  src.unlink();self.perform('undo');self.assertEqual(src.read_text(),'original')
 def test_directory_and_symlink_trash(self):
  folder=self.other/'folder';folder.mkdir();(folder/'child').write_text('safe');link=self.other/'link';link.symlink_to(folder)
  self.perform('trash',[folder,link]);self.perform('undo');self.assertTrue(link.is_symlink());self.assertEqual((folder/'child').read_text(),'safe')
 def test_partial_transfer_has_undo(self):
  src=self.file()
  with self.assertRaises(FileNotFoundError):self.perform('transfer',[src,self.other/'missing'])
  self.assertTrue((self.desktop/src.name).exists());self.perform('undo');self.assertFalse((self.desktop/src.name).exists());self.assertTrue(src.exists())
 def test_rename_and_create_undo(self):
  src=self.file();target=Path(self.perform('rename',[src],name='renamed')[0]);self.assertTrue(target.exists());self.perform('undo');self.assertTrue(src.exists())
  created=Path(self.perform('new-folder')[0]);self.assertTrue(created.is_dir());self.perform('undo');self.assertFalse(created.exists());self.perform('redo');self.assertTrue(created.exists())
 def test_new_action_clears_redo(self):
  self.perform('transfer',[self.file()]);self.perform('undo');self.perform('new-file');self.assertFalse(self.ops.redo_stack)
 def test_cut_paste_and_external_uri_clipboard(self):
  src=self.file();payload=('cut\n'+src.as_uri()).encode()
  with patch.object(m.subprocess,'run',side_effect=[subprocess.CompletedProcess([],0,payload),subprocess.CompletedProcess([],0,payload),subprocess.CompletedProcess([],0)]) as run:
   target=Path(self.perform('paste')[0]);self.assertFalse(src.exists());self.assertEqual(run.call_args.args[0],['wl-copy','--clear'])
  self.perform('undo');self.assertTrue(src.exists());self.assertFalse(target.exists())
  with patch.object(m.subprocess,'run',side_effect=[subprocess.CompletedProcess([],1,b''),subprocess.CompletedProcess([],0,('# files\n'+src.as_uri()).encode())]):
   self.perform('paste');self.assertTrue(src.exists())
 def test_copy_clipboard_uses_encoded_urls(self):
  src=self.file()
  with patch.object(m.subprocess,'run',return_value=subprocess.CompletedProcess([],0)) as run:
   self.perform('copy',[src]);self.assertEqual(run.call_args.kwargs['input'],'copy\n'+src.as_uri())
if __name__=='__main__':unittest.main()
