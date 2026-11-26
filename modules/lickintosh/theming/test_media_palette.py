import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from media_palette import palette_image
class MediaPaletteTest(unittest.TestCase):
 def test_still_does_not_decode(self):
  with patch('media_palette.subprocess.run') as run:
   self.assertEqual(palette_image('/tmp/photo.jpg','/unused'),Path('/tmp/photo.jpg'));run.assert_not_called()
 def test_cache_and_first_frame(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);video=root/'clip.mp4';video.write_bytes(b'video')
   def decode(command,**kwargs):
    self.assertEqual(command[command.index('-frames:v')+1],'1');self.assertNotIn('-ss',command);Path(command[-1]).write_bytes(b'frame')
   with patch('media_palette.subprocess.run',side_effect=decode) as run:
    frame=palette_image(video,root/'cache');self.assertEqual(frame.read_bytes(),b'frame');self.assertEqual(palette_image(video,root/'cache'),frame);self.assertEqual(run.call_count,1)
    video.write_bytes(b'changed-video');self.assertNotEqual(palette_image(video,root/'cache'),frame)
 def test_decode_failure_cleans_temporary_file(self):
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);video=root/'clip.webm';video.write_bytes(b'bad')
   with patch('media_palette.subprocess.run',side_effect=RuntimeError('bad media')):
    with self.assertRaises(RuntimeError):palette_image(video,root/'cache')
   self.assertEqual(list((root/'cache').iterdir()),[])
if __name__=='__main__':unittest.main()
