"""Dock capture must outlive its real slide, including custom animation speed."""
from pathlib import Path
import os,re,tempfile,unittest
import test_qml_interface as qml
SOURCE=os.environ.get('QUICKINTOSH_TEST_SOURCE','')
@unittest.skipUnless(SOURCE and qml.QS,'Built shell and Quickshell required')
class DockGlassExit(unittest.TestCase):
 def test_capture_follows_slide_until_last_frame(self):
  source=(Path(SOURCE)/'tahoedock/TahoeDockSurface.qml').read_text()
  presence=re.search(r'Presence\{id:dockGlassPresence;[^}]+\}',source)[0]
  transform=re.search(r'transform:Translate\{id:dockSlide;.*',source)[0].strip()
  transform=transform.replace('RenderPolicy.ShellMotion.duration(160)','root.duration')
  with tempfile.TemporaryDirectory() as directory:
   p=Path(directory);original=(Path(SOURCE)/'components/Presence.qml').read_text()
   (p/'Presence.qml').write_text(original.replace('import qs.services','').replace('ShellMotion.fade()','0'))
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
Scope{
 id:root
 property bool displayShown:true
 property bool vertical:false
 property int duration:480
 property var options:({position:'bottom'})
 QtObject{id:dock;property bool shown:true}
 '''+presence+'''
 FloatingWindow{visible:true;implicitWidth:200;implicitHeight:200
  Item{id:plate;width:150;height:50;'''+transform+'''}
 }
 property int phase:0
 property int samples:0
 property real previous:0
 property double start:0
 Timer{interval:15;running:true;repeat:true;onTriggered:{
  if(phase===0){root.start=Date.now();dock.shown=false;root.displayShown=false;phase=1;return}
  const elapsed=Date.now()-root.start
  if(elapsed>200 && elapsed<400){if(!dockGlassPresence.present || !dockSlideY.running){Qt.exit(2);return}if(dockSlide.y>previous)samples++}
  previous=dockSlide.y
  if(elapsed>650){if(dockGlassPresence.present || dockSlideY.running || samples<3){console.error('EXIT_CAPTURE_FAILED',samples,dockGlassPresence.present);Qt.exit(3);return}console.log('GLASS_ALIVE_THROUGH_SCALED_EXIT_OK');Qt.quit()}
 }}
}''')
   self.assertIn('GLASS_ALIVE_THROUGH_SCALED_EXIT_OK',output)
if __name__=='__main__':unittest.main()
