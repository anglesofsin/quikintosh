"""Prepared panels keep their state without remaining mapped over the desktop."""
import re,tempfile,unittest
from pathlib import Path
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Quickshell required')
class PanelMapping(unittest.TestCase):
 def test_preparation_unmaps_then_reopens_through_original_binding(self):
  source=(ROOT/'modules/lickintosh/runtime-efficiency/responsiveness.py').read_text()
  binding=re.search(r'Binding\{target:root.win;property:"visible";[^\n]+',source)[0]
  with tempfile.TemporaryDirectory() as directory:
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
Scope{id:root
 property bool preload:true
 property bool prewarming:false
 property bool retained:true
 property bool opened:false
 property bool closing:false
 property var win:host
 QtObject{id:host;property bool visible:root.opened || root.closing}
 '''+binding+'''
 property int step:0
 Timer{interval:5;repeat:true;running:true;onTriggered:{
  if(step===0){if(host.visible){Qt.exit(1);return}root.prewarming=true}
  if(step===1){if(!host.visible){Qt.exit(2);return}root.prewarming=false}
  if(step===2){if(host.visible || !retained){Qt.exit(3);return}root.opened=true}
  if(step===3){if(!host.visible){Qt.exit(4);return}root.closing=true;root.opened=false}
  if(step===4){if(!host.visible){Qt.exit(5);return}root.closing=false}
  if(step===5){if(host.visible || !retained){Qt.exit(6);return}console.log('PREPARED_PANEL_UNMAP_REOPEN_OK');Qt.quit()}
  step++
 }}
}''')
   self.assertIn('PREPARED_PANEL_UNMAP_REOPEN_OK',output)
if __name__=='__main__':unittest.main()
