"""Offscreen policy checks against the built geometry tracker, without host IPC."""
from pathlib import Path
import os,tempfile,unittest
from unittest.mock import patch
import test_qml_interface as qml
SOURCE=os.environ.get('QUICKINTOSH_TEST_SOURCE','')
@unittest.skipUnless(SOURCE and qml.QS,'Set QUICKINTOSH_TEST_SOURCE/QUICKINTOSH_TEST_QS')
class Efficiency(unittest.TestCase):
 def test_stationary_inventory_does_not_republish_or_refresh_native_models(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);services=root/'services';services.mkdir();bin=root/'bin';bin.mkdir()
   fake=bin/'hyprctl';fake.write_text('#!/bin/sh\nprintf "[]"\n');fake.chmod(0o700)
   (services/'qmldir').write_text('module qs.services\nsingleton Hyprland Hyprland.qml\n')
   (services/'Hyprland.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject{property int calls:0;property var toplevels:({values:[]});property var monitors:({values:[]});function refreshToplevels(){calls++}function refreshMonitors(){}signal rawEvent(var event)}')
   source=(Path(SOURCE)/'components/glass/GlassTracker.qml').read_text().replace('pragma Singleton','',1).replace('Singleton {','Scope {',1).replace('import Quickshell.Hyprland','import qs.services')
   (root/'Tracker.qml').write_text(source)
   with patch.dict(os.environ,{'PATH':str(bin)+':'+os.environ['PATH']}):
    output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
Scope{
 Tracker{id:tracker}
 property int stage:0
 property int publications:0
 Connections{target:tracker;function onClientsSnapshotChanged(){publications++}}
 Timer{interval:180;running:true;repeat:true;onTriggered:{
  if(stage<3){tracker.clientsUpdated=0;tracker.refreshWindows();stage++;return}
  if(Hyprland.calls!==1 || publications!==1){console.error('IDLE_REFRESH_FAILED',Hyprland.calls,publications);Qt.exit(2);return}
  tracker.precisionUsers=1;tracker.refreshWindows();if(Hyprland.calls!==2){Qt.exit(3);return}
  tracker.precisionUsers=0;tracker.fast=true;tracker.refreshWindows();if(Hyprland.calls!==3){Qt.exit(4);return}
  const base={address:'0x1',pid:1,at:[0,0],size:[100,100],workspace:{id:1},monitor:0,fullscreen:0}
  const moved=Object.assign({},base,{at:[10,0]}),full=Object.assign({},base,{fullscreen:2})
  if(tracker.geometrySignature([base])===tracker.geometrySignature([moved]) || tracker.geometrySignature([base])===tracker.geometrySignature([full])){Qt.exit(5);return}
  console.log('IDLE_NATIVE_COALESCING_AND_FAST_PATH_OK');Qt.quit()
 }}
}''')
   self.assertIn('IDLE_NATIVE_COALESCING_AND_FAST_PATH_OK',output)
 def test_closed_capture_source_is_detached_and_never_restarted(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);services=root/'services';services.mkdir();testing=root/'testing';testing.mkdir()
   stubs={
    'Hyprland':'property var toplevels:[];property var monitors:({values:[]})',
    'GlassTracker':"property var monitorSnapshots:[{name:'TEST',id:0,x:0,y:0,width:1280,height:720,scale:1,activeWorkspace:{id:1},specialWorkspace:{id:0}}];property var clientsSnapshot:[];property int captureMargin:200;property int snapshotSerial:0;property int transitionEpoch:0;property bool captureBlocked:false;property int captureUsers:0;property bool closing:false;property string closingAddress:'';function captureSnapshot(){return 0}",
    'ShellMotion':'property var effectsCurve:[.2,0,0,1,1,1]',
   }
   for name,body in stubs.items():(services/(name+'.qml')).write_text('pragma Singleton\nimport QtQuick\nQtObject{'+body+'}')
   (services/'qmldir').write_text('module qs.services\n'+''.join('singleton '+name+' '+name+'.qml\n' for name in stubs))
   (testing/'qmldir').write_text('module qs.testing\nsingleton Registry Registry.qml\nScreencopyView ScreencopyView.qml\n')
   (testing/'Registry.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject{property var viewer:null}')
   (testing/'ScreencopyView.qml').write_text('import QtQuick\nimport qs.testing\nItem{property var captureSource:null;property bool live:false;readonly property bool hasContent:captureSource!==null;signal stopped();function captureFrame(){}Component.onCompleted:Registry.viewer=this}')
   (root/'GlassWindows.qml').write_text((Path(SOURCE)/'components/glass/GlassWindows.qml').read_text().replace('import Quickshell.Wayland','import qs.testing').replace('import Quickshell.Hyprland','import qs.services'))
   (root/'CaptureGate.qml').write_text((Path(SOURCE)/'components/glass/CaptureGate.qml').read_text())
   output=qml.Interface.run_qml(self,directory,'''import QtQuick
import Quickshell
import qs.services
import qs.testing as Testing
Scope{
 QtObject{id:source;signal closed()}
 FloatingWindow{implicitWidth:220;implicitHeight:220;GlassWindows{id:glass;monitorName:'TEST';region:Qt.rect(0,0,200,200)}}
 property int step:0
 Timer{interval:100;running:true;repeat:true;onTriggered:{
  if(step===0){Hyprland.toplevels=[{wayland:source,address:'0x1',workspace:{id:1},lastIpcObject:{address:'0x1',pid:1,monitor:0,workspace:{id:1},at:[0,0],size:[100,100],mapped:true}}];step++;return}
  const view=Testing.Registry.viewer
  if(!view){console.error('NO_VIEW',Hyprland.toplevels.length,glass.children.length);Qt.exit(5);return}
  if(step===1){if(view.captureSource!==source || !view.live){console.error('CAPTURE_NOT_STARTED');Qt.exit(6);return}glass.capturing=false;step++;return}
  if(step===2){if(view.live || view.captureSource!==source){console.error('PAUSED_CAPTURE_DISCARDED');Qt.exit(8);return}glass.capturing=true;step++;return}
  if(step===3){if(!view.live || view.captureSource!==source){Qt.exit(9);return}source.closed();step++;return}
  for(let n=0;n<10;n++){view.stopped();view.restart()}
  if(view.captureSource!==null || view.live || view.restartFailures!==0){console.error('CLOSED_CAPTURE_RESTARTED');Qt.exit(7);return}
  console.log('CLOSED_CAPTURE_DETACHED_OK');Qt.quit()
 }}
}''')
   self.assertIn('CLOSED_CAPTURE_DETACHED_OK',output)
   self.assertNotIn('Binding loop',output)

if __name__=='__main__':unittest.main()
