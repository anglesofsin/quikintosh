import unittest,tempfile,os
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import backend
class DockFilesTests(unittest.TestCase):
 def test_listing_is_bounded_and_hides_dotfiles(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   for i in range(110):(root/(str(i)+'.txt')).write_text('test')
   (root/'.secret').write_text('private')
   files=backend.listfiles(d,'name');self.assertEqual(len(files),100);self.assertFalse(any(x['name'].startswith('.') for x in files))
 def test_recent_handles_encoded_local_paths_and_ignores_network_urls(self):
  with tempfile.TemporaryDirectory() as d:
   home=Path(d);(home/'.local/share').mkdir(parents=True);file=home/'my file.txt';file.write_text('ok')
   (home/'.local/share/recently-used.xbel').write_text('<xbel><bookmark href="'+file.as_uri()+'" visited="2026-11-22"/><bookmark href="https://example.com/file"/></xbel>')
   with patch.object(backend,'HOME',home),patch.object(backend,'_recent_file',home/'recent.json'):result=backend.recent()
   self.assertEqual([x['path'] for x in result],[str(file)])
 def test_saved_capture_is_in_recent_without_xbel_and_duplicates_are_merged(self):
  with tempfile.TemporaryDirectory() as d:
   home=Path(d);(home/'Desktop').mkdir();file=home/'Desktop/Screenshot_2026-11-22_1.png';file.write_bytes(b'png')
   with patch.object(backend,'HOME',home),patch.object(backend,'_recent_file',home/'recent.json'),patch.object(backend,'_pool'):
    backend.record_recent(file);files=backend.recent();self.assertEqual([x['path'] for x in files],[str(file)])
    file.unlink();self.assertEqual(backend.recent(),[])
 def test_preview_listing_only_queues_three_files(self):
  with tempfile.TemporaryDirectory() as d:
   home=Path(d)
   for i in range(25):(home/(str(i)+'.png')).write_bytes(b'png')
   with patch.object(backend,'HOME',home),patch.object(backend,'_pool') as pool:
    files=backend.listfiles(str(home),'name',limit=3);self.assertEqual(len(files),3);self.assertEqual(pool.submit.call_count,3)
 def test_trash_lists_original_names_including_hidden_items(self):
  with tempfile.TemporaryDirectory() as d:
   data=Path(d);root=data/'Trash';(root/'files').mkdir(parents=True);(root/'info').mkdir()
   (root/'files'/'renamed.2.txt').write_text('preserved')
   (root/'files'/'.hidden').write_text('hidden')
   (root/'info'/'renamed.2.txt.trashinfo').write_text('[Trash Info]\nPath=/home/test/My%20file.txt\nDeletionDate=2026-11-23T01:00:00\n')
   with patch.dict(os.environ,{'XDG_DATA_HOME':d}):
    files=backend.listfiles('trash','name');self.assertEqual(backend.trashcount(),2)
    item=next(i for i in files if i['name']=='My file.txt');self.assertEqual(item['trashUri'],'trash:///renamed.2.txt');self.assertTrue(item['trash'])
    self.assertEqual((root/'files'/'renamed.2.txt').read_text(),'preserved');self.assertEqual(len(backend.listfiles('trash','name',limit=1)),1)
 def test_removing_recent_files_never_removes_the_original(self):
  with tempfile.TemporaryDirectory() as d:
   home=Path(d);state=home/'state';state.mkdir();file=home/'one.txt';file.write_text('original')
   with patch.object(backend,'HOME',home),patch.object(backend,'STATE',state),patch.object(backend,'_recent_file',state/'recent.json'):
    backend.record_recent(file);self.assertEqual([i['path'] for i in backend.recent()],[str(file)])
    backend.remove_recent([str(file)]);self.assertEqual(backend.recent(),[]);self.assertEqual(file.read_text(),'original')
    backend.record_recent(file);self.assertEqual([i['path'] for i in backend.recent()],[str(file)])
    backend.remove_recent([],clear=True);self.assertEqual(backend.recent(),[]);self.assertTrue(file.exists())
 def test_recent_rename_tracks_the_original_file_at_its_new_path(self):
  with tempfile.TemporaryDirectory() as d:
   home=Path(d);state=home/'state';state.mkdir();file=home/'one.txt';file.write_text('original');target=home/'renamed.txt'
   with patch.object(backend,'HOME',home),patch.object(backend,'STATE',state),patch.object(backend,'_recent_file',state/'recent.json'):
    backend.record_recent(file);file.rename(target);backend.rename_recent([{'old':str(file),'new':str(target)}]);self.assertEqual([i['path'] for i in backend.recent()],[str(target)])
 def test_thumbnail_handles_spaces_and_hashes(self):
  with tempfile.TemporaryDirectory() as d:
   home=Path(d);file=home/'image #1.png';Image.new('RGB',(640,480),'red').save(file)
   with patch.object(backend,'HOME',home),patch.object(backend,'emit'):
    backend.make_thumbnail(file);target=backend.thumbnail_path(file);self.assertTrue(target.is_file())
    with Image.open(target) as image:self.assertEqual(image.size,(256,192))
if __name__=='__main__':unittest.main()
