import importlib.util,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('widget_media',Path(__file__).with_name('media.py'));media=importlib.util.module_from_spec(spec);spec.loader.exec_module(media)
class LibraryTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def test_mixed_media_unicode_hidden_and_recursion(self):
  for name in ['é foto.jpg','movie.MP4','animated.gif','notes.txt','.private.jpg']:(self.root/name).touch()
  (self.root/'nested').mkdir();(self.root/'nested/other.webp').touch()
  self.assertEqual(len(media.scan(str(self.root))['files']),3)
  self.assertEqual(len(media.scan(str(self.root),True)['files']),4)
 def test_file_url_and_path_with_spaces(self):
  p=self.root/'my photo.jpg';p.touch();self.assertEqual(media.local(p.as_uri()),p)
 def test_remote_locations_are_rejected(self):
  for path in ['https://example.com/image.jpg','file://example.com/private.jpg']:
   with self.assertRaises(ValueError):media.local(path)
 def test_missing_folder_is_reported(self):self.assertEqual(media.scan(str(self.root/'missing'))['files'],[])
 def test_symlink_directories_are_not_followed(self):
  (self.root/'pictures').mkdir();(self.root/'pictures/p.png').touch();(self.root/'pictures/loop').symlink_to(self.root,target_is_directory=True)
  self.assertEqual(len(media.scan(str(self.root),True)['files']),1)
 @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'ffmpeg required')
 def test_video_poster_is_cached_and_metadata_read(self):
  media.FFMPEG=shutil.which('ffmpeg');media.FFPROBE=shutil.which('ffprobe')
  p=self.root/'clip.mp4'
  subprocess.run([media.FFMPEG,'-v','error','-f','lavfi','-i','color=c=blue:s=160x90:d=1','-metadata','title=Fixture','-c:v','mpeg4',str(p)],check=True)
  with patch.dict(os.environ,{'XDG_CACHE_HOME':str(self.root/'cache')}):
   first=media.poster(str(p));self.assertTrue(media.local(first['poster']).is_file())
   with patch.object(media.subprocess,'run',side_effect=AssertionError('cache miss')):self.assertEqual(first,media.poster(str(p)))
  self.assertEqual(media.metadata(str(p))['title'],'Fixture')
if __name__=='__main__':unittest.main()
