from pathlib import Path
import tempfile,unittest
import test_qml_interface as qml
ROOT=Path(__file__).parents[1]
@unittest.skipUnless(qml.QS,'Quickshell required')
class Rename(unittest.TestCase):
 def test_return_and_open_are_separate(self):
  s=(ROOT/'modules/lickintosh/desktop-files/integrate.py').read_text();a=s.index('                if(event.modifiers===Qt.NoModifier');b=s.index("\n''',1)",a);body=s[a:b].replace("DesktopFiles","files")
  with tempfile.TemporaryDirectory() as tmp:
   output=qml.Interface.run_qml(self,tmp,'''import QtQuick
import Quickshell
Scope{id:root;property int opened:0
QtObject{id:files;property var selection:['/tmp/a.txt'];property string renaming:'';function open(path,name){root.opened++}function nameOfPath(path){return path}}
function handle(event){'''+body+'''}
Timer{interval:1;running:true;onTriggered:{
 let event={key:Qt.Key_Return,modifiers:Qt.NoModifier,accepted:false};root.handle(event);if(files.renaming!=='/tmp/a.txt' || root.opened!==0){Qt.exit(2);return}
 files.renaming='';event={key:Qt.Key_O,modifiers:Qt.ControlModifier};root.handle(event);if(root.opened!==1){Qt.exit(3);return}
 files.selection=['a','b'];event={key:Qt.Key_Return,modifiers:Qt.NoModifier};root.handle(event);if(files.renaming!==''){Qt.exit(4);return}
 console.log('DESKTOP_RETURN_RENAME_OK');Qt.quit()
}}
}''');self.assertIn('DESKTOP_RETURN_RENAME_OK',output)
if __name__=='__main__':unittest.main()
