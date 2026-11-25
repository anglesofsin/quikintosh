"""Exercise the actual edit batcher with a private HOME and offscreen Qt."""
from pathlib import Path
import os,tempfile,unittest
from unittest.mock import patch
import test_qml_interface as qml
SOURCE=os.environ.get('QUICKINTOSH_TEST_SOURCE','')
@unittest.skipUnless(SOURCE and qml.QS,'Built source and Quickshell required')
class WidgetEdits(unittest.TestCase):
 def test_edits_merge_per_frame_and_structural_actions_preserve_them(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);services=root/'services';services.mkdir();(root/'.config/lickintosh/core').mkdir(parents=True)
   (root/'.config/lickintosh/core/widgets.json').write_text('{"desktop":[],"notifCenter":[]}')
   source=(Path(SOURCE)/'services/WidgetState.qml').read_text().replace('interval: 100\n        onTriggered: widgetsFile.writeAdapter()','interval: 10000\n        onTriggered: widgetsFile.writeAdapter()')
   (services/'WidgetState.qml').write_text(source)
   stubs={'AppearanceState':"property color iconColor:'#08f'",'DesktopFiles':'property var layout:[]'}
   for name,body in stubs.items():(services/(name+'.qml')).write_text('pragma Singleton\nimport QtQuick\nQtObject{'+body+'}')
   (services/'qmldir').write_text('module qs.services\nsingleton WidgetState WidgetState.qml\n'+''.join('singleton '+n+' '+n+'.qml\n' for n in stubs))
   with patch.dict(os.environ,{'HOME':directory,'XDG_CONFIG_HOME':directory+'/.config'}):
    output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
Scope{
 property int phase:0
 property int publications:0
 Connections{target:WidgetState;function onDesktopChanged(){if(phase>0)publications++}}
 Timer{interval:150;running:true;repeat:true;onTriggered:{
  if(phase===0){WidgetState.desktop=[{id:'one',type:'personalclock',size:'s',x:0,y:0},{id:'two',type:'image',size:'s',x:600,y:0}];WidgetState.areaWidth=1200;WidgetState.areaHeight=800;phase=1;return}
  if(phase===1){publications=0;for(let n=0;n<100;n++)WidgetState.configure('desktop','one',{clockWeight:n/100,clockSize:30+n});phase=2;return}
  if(phase===2){
   const entry=WidgetState.entryOf('desktop','one')
   if(publications!==1 || entry.clockWeight!==.99 || entry.clockSize!==129){console.error('PATCH_BATCH_FAILED',publications,entry.clockWeight);Qt.exit(2);return}
   WidgetState.configure('desktop','one',{clockColor:'#123456'});WidgetState.moveWidget('one',300,200,true)
   if(WidgetState.entryOf('desktop','one').clockColor!=='#123456'){Qt.exit(3);return}
   WidgetState.configure('desktop','two',{image:'example.png'});WidgetState.removeWidget('desktop','two');phase=3;return
  }
  if(WidgetState.entryOf('desktop','two')!==null || Object.keys(WidgetState.pendingConfiguration).length){Qt.exit(4);return}
  console.log('WIDGET_EDIT_BATCH_AND_FLUSH_OK');Qt.quit()
 }}
}''')
   self.assertIn('WIDGET_EDIT_BATCH_AND_FLUSH_OK',output)
if __name__=='__main__':unittest.main()
