"""Exercise the production geometry refresh policy without the host compositor."""
from pathlib import Path
import os,tempfile,unittest
import test_qml_interface as qml
ROOT=Path(__file__).resolve().parents[1]
@unittest.skipUnless(qml.QS,'Quickshell required')
class WorkspaceRefresh(unittest.TestCase):
 def test_resume_and_consecutive_transitions_request_fresh_geometry(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory)
   def module(folder,name,body):
    path=root/folder;path.mkdir(parents=True,exist_ok=True)
    (path/(name+'.qml')).write_text('pragma Singleton\nimport QtQuick\nQtObject{'+body+'}')
    with (path/'qmldir').open('a') as f:f.write('singleton '+name+' '+name+'.qml\n')
   module('nativefake','FramePacer',"property int maximumFps:0;property bool measuring:false;property var geometry:({});property bool geometryAvailable:true;property int requests:0;function requestGeometry(){requests++}function setGeometryMotion(active,fps){}function prepareWindows(keep){}function label(window,role){}function statistics(){return []}")
   module('components/glass','GlassTracker','property int captureUsers:0;property int precisionUsers:0;property bool fast:false;property int transitionEpoch:0')
   module('services','ShellConfig',"property var options:({performance:{maximumFps:0,glassFps:0,geometryFps:0,textureScale:.5,blurScale:.5,motionScale:1,prewarm:true,shadows:true,glassEnabled:true,blurEnabled:true,ambientAnimations:true,measureFrames:false}})")
   module('services','SettingsPreferences','property var accessibility:({reduceMotion:false,reduceTransparency:false})')
   module('services','GameMode','property bool enabled:false')
   source=(ROOT/'modules/lickintosh/rendering/RenderingState.qml').read_text().replace('import Quickintosh.Render as Native','import qs.nativefake as Native')
   (root/'services/RenderingState.qml').write_text(source)
   with (root/'services/qmldir').open('a') as f:f.write('singleton RenderingState RenderingState.qml\n')
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
import qs.components.glass
import qs.nativefake
Scope{
 property var policy:RenderingState
 property int step:0
 property int before:0
 Timer{interval:40;running:true;repeat:true;onTriggered:{
  before=FramePacer.requests
  if(step===0){GlassTracker.captureUsers=1;if(FramePacer.requests<=before){Qt.exit(2);return}}
  if(step===1){GlassTracker.fast=true;GlassTracker.transitionEpoch++;if(FramePacer.requests<=before){Qt.exit(3);return}}
  if(step===2){GlassTracker.transitionEpoch++;if(FramePacer.requests<=before){Qt.exit(4);return}}
  if(step===3){GlassTracker.fast=false;GlassTracker.captureUsers=0}
  if(step===4){GlassTracker.transitionEpoch++;if(FramePacer.requests!==before){Qt.exit(5);return}console.log('RESUME_AND_CONSECUTIVE_WORKSPACES_REFRESH_OK');Qt.quit()}
  step++
 }}
}''')
   self.assertIn('RESUME_AND_CONSECUTIVE_WORKSPACES_REFRESH_OK',output)
   self.assertNotIn('ReferenceError',output)
if __name__=='__main__':unittest.main()
