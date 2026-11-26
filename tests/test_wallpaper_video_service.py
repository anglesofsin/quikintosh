import tempfile,unittest,subprocess,os,shutil,sys
from pathlib import Path
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS and shutil.which('ffmpeg'),'Quickshell and FFmpeg required')
class VideoService(unittest.TestCase):
 def test_default_bypass_async_completion_and_live_source_binding(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);services=root/'services';services.mkdir();(root/'tools').mkdir()
   path=root/'source.mp4'
   subprocess.run(['ffmpeg','-nostdin','-v','error','-f','lavfi','-i','color=blue:size=320x180:rate=30:duration=0.3','-c:v','libx264','-threads','1',str(path)],check=True)
   (services/'qmldir').write_text('module qs.services\nsingleton ShellConfig ShellConfig.qml\nsingleton WallpaperVideo WallpaperVideo.qml\n')
   (services/'ShellConfig.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject{property QtObject options:QtObject{property QtObject wallpaper:QtObject{property int videoHeight:0;property int videoFps:0}}}')
   (services/'WallpaperVideo.qml').write_text((ROOT/'modules/lickintosh/live-backdrop/WallpaperVideo.qml').read_text().replace('@PYTHON@',sys.executable))
   shutil.copyfile(ROOT/'modules/lickintosh/live-backdrop/video-render.py',root/'tools/wallpaper-video-render.py')
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
Scope{id:root
 readonly property string source:"'''+str(path)+'''"
 readonly property string effective:WallpaperVideo.resolve(source)
 property int step:0
 Timer{interval:30;repeat:true;running:true;onTriggered:{
  if(step===0){if(effective!==source || WallpaperVideo.busy){Qt.exit(2);return}ShellConfig.options.wallpaper.videoFps=15;step=1;return}
  if(step===1 && effective!==source){if(!effective.endsWith('.mp4') || WallpaperVideo.busy || WallpaperVideo.error){Qt.exit(3);return}ShellConfig.options.wallpaper.videoFps=0;step=2;return}
  if(step===2){if(effective!==source){Qt.exit(4);return}console.log('WALLPAPER_ASYNC_SOURCE_RESET_OK');Qt.quit()}
  if(WallpaperVideo.error){console.error(WallpaperVideo.error);Qt.exit(5)}
 }}
 Timer{interval:8000;running:true;onTriggered:Qt.exit(6)}
}''')
   self.assertIn('WALLPAPER_ASYNC_SOURCE_RESET_OK',output)
if __name__=='__main__':unittest.main()
