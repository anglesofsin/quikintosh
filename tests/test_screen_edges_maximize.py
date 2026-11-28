"""Screen corners hide only for actual fullscreen, never decorated maximize."""
from pathlib import Path
import tempfile,unittest
import test_qml_interface as qml
@unittest.skipUnless(qml.QS,'Quickshell required')
class ScreenEdges(unittest.TestCase):
 def test_fullscreen_vs_maximize(self):
  s=(Path(__file__).parents[1]/'modules/lickintosh/corners/ScreenEdges.qml').read_text()
  fn=s[s.index(' function fullscreen('):s.index(' component Cutout:')].replace('Hyprland.monitorFor(screen)','root.monitor').replace('GlassTracker.clientsSnapshot','root.clients')
  with tempfile.TemporaryDirectory() as tmp:
   output=qml.Interface.run_qml(self,tmp,'''import QtQuick
import Quickshell
Scope{id:root;property var monitor:({id:0,activeWorkspace:{id:1}});property var clients:[]
'''+fn+'''
Timer{interval:1;running:true;onTriggered:{
 root.clients=[{monitor:0,workspace:{id:1},fullscreen:1}];if(root.fullscreen(null)){Qt.exit(2);return}
 root.clients=[{monitor:0,workspace:{id:1},fullscreen:2}];if(!root.fullscreen(null)){Qt.exit(3);return}
 root.clients=[{monitor:0,workspace:{id:2},fullscreen:2}];if(root.fullscreen(null)){Qt.exit(4);return}
 console.log('SCREEN_CORNERS_MAXIMIZE_PRESERVED');Qt.quit()
}}
}''');self.assertIn('SCREEN_CORNERS_MAXIMIZE_PRESERVED',output)
if __name__=='__main__':unittest.main()
