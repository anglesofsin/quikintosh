"""The indexed search worker must never deliver old results over a newer query."""
from pathlib import Path
import tempfile,unittest,shutil
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Quickshell is required')
class SpotlightWorker(unittest.TestCase):
 def test_large_index_and_serialized_results_without_gui_blocking(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   # This is the exact shared search implementation installed before the worker.
   source=ROOT/'modules/lickintosh/spotlight-search/Search.js'
   if not source.is_file():
    source=ROOT/'modules/lickintosh/runtime-efficiency/Search.js'
   self.assertTrue(source.is_file(),source)
   (root/'SearchWorker.js').write_text(source.read_text()+'\n'+(ROOT/'modules/lickintosh/island-dashboard/SearchWorker.js').read_text())
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import QtQml.WorkerScript
import Quickshell
Scope {
 id:root
 property int ticks:0
 property int serial:0
 property bool done:false
 property double started:Date.now()
 Timer { interval:10;running:true;repeat:true;onTriggered:root.ticks++ }
 Timer { interval:7000;running:true;onTriggered:Qt.exit(20) }
 WorkerScript {
  id:worker;source:"SearchWorker.js"
  onMessage:message=>{
   if(message.type==='indexed') {
    worker.sendMessage({type:'search',query:'file-12',serial:1})
    worker.sendMessage({type:'search',query:'file-59999',serial:2})
   } else if(message.serial===2) {
    if(message.paths[0]!=='/home/test/file-59999.txt' || root.ticks===0){Qt.exit(21);return}
    console.log('WORKER_ASYNC_OK',root.ticks,Date.now()-root.started);Qt.quit()
   }
  }
 }
 Component.onCompleted:{
  const paths=[]
  for(let i=0;i<60000;i++)paths.push('/home/test/file-'+i+'.txt')
  worker.sendMessage({type:'index',paths:paths})
 }
}''')
   self.assertIn('WORKER_ASYNC_OK',output)
if __name__=='__main__':unittest.main()
