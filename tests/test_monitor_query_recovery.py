"""Overlapping monitor events retain a final query, even with no glass capture."""
from pathlib import Path
import tempfile,unittest
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Quickshell required')
class MonitorRecovery(unittest.TestCase):
 def test_monitor_updates_during_inflight_query(self):
  # Read the actual integration's generated handler strings, without executing
  # the integrator against the user's installed shell.
  import ast
  tree=ast.parse((ROOT/'modules/lickintosh/live-backdrop/integrate.py').read_text())
  texts=[node.value for node in ast.walk(tree) if isinstance(node,ast.Constant) and isinstance(node.value,str)]
  replacement=next(s for s in texts if 'onExited:if(root.monitorQueryAgain)' in s)
  exited=replacement.split('onExited:',1)[1].strip()
  refresh=next(s for s in texts if 'else root.monitorQueryAgain=true' in s)
  with tempfile.TemporaryDirectory() as directory:
   result=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
Scope {id:root;property bool monitorQueryAgain:false
 QtObject{id:monitorQuery;property bool running:false}
 function refresh(){'''+refresh+'''}
 function exited(){'''+exited+'''}
 Timer{interval:1;running:true;onTriggered:{
  refresh();if(!monitorQuery.running){Qt.exit(2);return}
  refresh();refresh();if(!monitorQueryAgain){Qt.exit(3);return}
  monitorQuery.running=false;exited()
  Qt.callLater(function(){if(!monitorQuery.running || monitorQueryAgain){Qt.exit(4);return}
   monitorQuery.running=false;exited()
   Qt.callLater(function(){if(monitorQuery.running){Qt.exit(5);return}console.log('MONITOR_QUERY_RECOVERY_OK');Qt.quit()})
  })
 }}
}''')
   self.assertIn('MONITOR_QUERY_RECOVERY_OK',result)
if __name__=='__main__':unittest.main()
