"""Stale hover clears only for an obstructed dock, outside its hit region."""
import json,tempfile,unittest,re,subprocess
from pathlib import Path
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Quickshell required')
class Recovery(unittest.TestCase):
 def test_pointer_recovery_and_unobstructed_idle_gate(self):
  source=(ROOT/'modules/lickintosh/dock/TahoeDockSurface.qml').read_text()
  body=re.search(r'onStreamFinished:\{(try\{const p=JSON.parse\(text\),r=windowWatcher.item\?\.dockRect.*?catch\(_\)\{\})\}\}\}',source)[1].replace('GlassTracker.monitorSnapshots','tracker.monitorSnapshots')
  with tempfile.TemporaryDirectory() as directory:
   result=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
Scope{id:root;property bool lensHovered:true;property int hoveredIndex:3;property string hoverLabel:'App';property bool revealed:true
property var controller:({hoverActive:true})
QtObject{id:windowWatcher;property var item:({dockRect:{x:300,y:950,width:700,height:100}})}
QtObject{id:tracker;property var monitorSnapshots:[{name:'test',x:0,y:0}]}
QtObject{id:dock;property var screen:({name:'test'})}
function receive(text){'''+body+'''}
Timer{interval:1;running:true;onTriggered:{
 receive(JSON.stringify({x:500,y:1000}));if(!revealed){Qt.exit(2);return}
 receive(JSON.stringify({x:100,y:100}));if(revealed || lensHovered || controller.hoverActive || hoveredIndex!==-1 || hoverLabel!==''){Qt.exit(3);return}
 console.log('STALE_DOCK_HOVER_RECOVERY_PASSED');Qt.quit()
}}
}''')
   self.assertIn('STALE_DOCK_HOVER_RECOVERY_PASSED',result)
if __name__=='__main__':unittest.main()
