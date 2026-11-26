"""Renderer bursts publish one reactive map, retaining all generated icons."""
import os,tempfile,unittest
from pathlib import Path
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Quickshell required')
class Batch(unittest.TestCase):
 def test_burst_retains_results_and_publishes_once(self):
  source=(ROOT/'modules/lickintosh/live-backdrop/integrate.py').read_text()
  # Exercise the production function from the assembly fixture, not a copy.
  namespace={'__name__':'not_main'}
  import ast
  tree=ast.parse(source)
  fn=next(n for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str) and 'function flushCompleted' in n.value).value
  with tempfile.TemporaryDirectory() as directory:
   out=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
Scope{id:root;property var files:({});property int pending:1000;property int lastRenderMs:0;property int publications:0
onFilesChanged:publications++
'''+fn+'''
Component.onCompleted:{publications=0;for(let i=0;i<1000;i++){completed.push({key:'icon'+i+'|signature',path:'/tmp/icon'+i+'.png',ms:i});Qt.callLater(root.flushCompleted)}}
Timer{interval:80;running:true;onTriggered:{if(Object.keys(files).length!==1000 || Object.keys(origins).length!==1000 || publications!==1 || pending!==0){console.error('BATCH_FAILED',publications,pending);Qt.exit(2);return}console.log('ICON_BURST_ONE_PUBLICATION',publications);Qt.quit()}}
}''')
   self.assertIn('ICON_BURST_ONE_PUBLICATION',out)
if __name__=='__main__':unittest.main()
