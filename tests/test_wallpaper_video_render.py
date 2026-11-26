import importlib.util,json,shutil,subprocess,tempfile,unittest,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render',ROOT/'modules/lickintosh/live-backdrop/video-render.py');render=importlib.util.module_from_spec(spec);spec.loader.exec_module(render)
@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg required')
class Rendering(unittest.TestCase):
 def test_cache_resolution_fps_and_original_integrity(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);source=root/'test video.mp4'
   subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','testsrc2=size=1920x1080:rate=60:duration=0.3','-c:v','libx264','-preset','ultrafast','-threads','2',str(source)],check=True)
   original=source.read_bytes()
   self.assertEqual(render.prepare({'source':str(source),'height':0,'fps':0},root),str(source))
   request={'source':str(source),'height':720,'fps':30}
   output=Path(render.prepare(request,root));mtime=output.stat().st_mtime_ns
   info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate','-of','json',str(output)],text=True))['streams'][0]
   self.assertEqual((info['width'],info['height'],info['avg_frame_rate']),(1280,720,'30/1'))
   self.assertEqual(render.prepare(request,root),str(output));self.assertEqual(mtime,output.stat().st_mtime_ns)
   self.assertEqual(original,source.read_bytes())
   stamp=source.stat().st_mtime_ns
   os.utime(source,ns=(stamp+1000000,stamp+1000000))
   self.assertNotEqual(render.prepare(request,root),str(output))
   # A larger requested cap must preserve aspect and never upscale.
   output=render.prepare({'source':str(source),'height':2160,'fps':120},root)
   info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate','-of','json',output],text=True))['streams'][0]
   self.assertEqual((info['width'],info['height'],info['avg_frame_rate']),(1920,1080,'60/1'))
 def test_invalid_values_rejected(self):
  with self.assertRaises(ValueError):render.prepare({'source':__file__,'height':99999,'fps':0})
if __name__=='__main__':unittest.main()
