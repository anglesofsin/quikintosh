"""Exercise automation ownership without touching user DND or applications."""
from pathlib import Path
import tempfile,unittest
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Quickshell required')
class FocusRuntime(unittest.TestCase):
 def test_sharing_restores_only_the_state_owned_by_automation(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);services=root/'services';services.mkdir()
   files={
    'SettingsPreferences':'''property bool ready:true
property bool locked:false
property QtObject focus:QtObject{property int profileVersion:0;property bool allowCritical:true;property bool schedule:false;property string start:'22:00';property string end:'07:00';property var days:[0,1,2,3,4,5,6];property bool autoDndSharing:false;property string activeId:'dnd';property var profiles:[{id:'dnd',name:'DND',appMode:'allow',apps:''}]}''',
    'ShellConfig':'''property QtObject options:QtObject{property QtObject session:QtObject{property bool focus:false}}''',
    'MediaCaptureState':'''property var visibleDetails:[]''',
    'CaptureState':'''property bool recording:false'''
   }
   for name,body in files.items():(services/(name+'.qml')).write_text('pragma Singleton\nimport QtQuick\nimport Quickshell\nSingleton{'+body+'}\n')
   source=(ROOT/'modules/lickintosh/focus/FocusState.qml').read_text().replace('import Quickshell.Hyprland','').replace("Hyprland.activeToplevel?.wayland?.appId || ''","''")
   (services/'FocusState.qml').write_text(source)
   (services/'FocusPolicy.js').write_text((ROOT/'modules/lickintosh/focus/FocusPolicy.js').read_text())
   (services/'qmldir').write_text('module qs.services\n'+''.join('singleton '+name+' '+name+'.qml\n' for name in [*files,'FocusState']))
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
Scope {
 Timer{interval:20;running:true;onTriggered:{
  const prefs=SettingsPreferences.focus,session=ShellConfig.options.session
  MediaCaptureState.visibleDetails=[{kind:'screen'}];FocusState.tick()
  if(session.focus || prefs.profileVersion!==1){Qt.exit(30);return}
  prefs.autoDndSharing=true;FocusState.tick()
  if(!session.focus || !FocusState.owned){Qt.exit(31);return}
  MediaCaptureState.visibleDetails=[];FocusState.tick()
  if(session.focus){Qt.exit(32);return}
  session.focus=true;MediaCaptureState.visibleDetails=[{kind:'screen'}];FocusState.tick()
  MediaCaptureState.visibleDetails=[];FocusState.tick()
  if(!session.focus){Qt.exit(33);return}
  session.focus=false;MediaCaptureState.visibleDetails=[{kind:'screen'}];FocusState.tick()
  session.focus=false;FocusState.tick()
  if(session.focus){Qt.exit(34);return}
  MediaCaptureState.visibleDetails=[];FocusState.tick()
  if(session.focus){Qt.exit(35);return}
  console.log('OWNERSHIP_OK');Qt.quit()
 }}
}''')
   self.assertIn('OWNERSHIP_OK',output)
if __name__=='__main__':unittest.main()
