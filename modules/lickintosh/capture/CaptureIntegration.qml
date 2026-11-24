import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.services
import qs.capture
import qs.rosa.services as Rosa
Scope {
 id:root
 property bool enabled:false
 property bool locked:false
 signal captured()
 Binding {target:CaptureState;property:"enabled";value:root.enabled && !root.locked}
 Connections {target:LauncherState;function onRequested(){if(CaptureState.opened)CaptureState.cancel()}}
 Connections {target:CaptureState;function onScreenshotSaved(path){
   if(Rosa.IslandConfig.s('enabled') && Rosa.IslandConfig.on('shot'))Rosa.IslandBus.screenshotSaved(path)
   else Quickshell.execDetached(['notify-send','-a','Lickintosh Capture','Screenshot saved',path])
  } function onCaptured(){root.captured()} function onError(message){console.warn("Capture:",message);Quickshell.execDetached(['notify-send','-a','Lickintosh Capture','Screenshot',message])}}
 CameraMirror {}
 PanelWindow {
  visible:CaptureState.recording
  anchors{bottom:true}
  margins.bottom:30;implicitWidth:260;implicitHeight:46;exclusiveZone:-1;color:'transparent'
  WlrLayershell.namespace:'lickintosh:recording-control';WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
  Rectangle {anchors.fill:parent;radius:14;color:'#f01c1c1f';border.color:'#444449';border.width:1
   Text {anchors.left:parent.left;anchors.leftMargin:15;anchors.verticalCenter:parent.verticalCenter;text:'●  '+CaptureState.recordTime;color:'#ff6b35';font.pixelSize:15}
   Rectangle {anchors.right:parent.right;anchors.rightMargin:8;anchors.verticalCenter:parent.verticalCenter;width:105;height:32;radius:9;color:'#ff6b35';Text{anchors.centerIn:parent;text:'Stop recording';color:'white';font.pixelSize:12}MouseArea{anchors.fill:parent;onClicked:CaptureState.send({action:'stopRecord'})}}
  }
 }
 CaptureWindow {id:editor;visible:CaptureState.opened && editor.frameReady}
 Variants {model:CaptureState.pins;PinWindow {required property var modelData;shot:modelData}}
 PanelWindow {
  visible:CaptureState.flash
  screen:Quickshell.screens.find(s=>s.name===CaptureState.flashMonitor) || Quickshell.screens[0]
  anchors{top:true;bottom:true;left:true;right:true}
  color:'#22ffffff';exclusiveZone:-1
  mask:Region{}
  WlrLayershell.namespace:'lickintosh:capture-flash';WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
 }
 IpcHandler {
  target:'capture'
  function hub():void {CaptureState.open('region')}
  function colorPicker():void {CaptureState.launch('color')}
  function palette():void {CaptureState.launch('palette')}
  function qr():void {CaptureState.launch('qr')}
  function lens():void {CaptureState.launch('lens')}
  function measure():void {CaptureState.launch('measure')}
  function record():void {if(CaptureState.recording)CaptureState.send({action:'stopRecord'});else CaptureState.launch('record')}
  function recordAudio():void {if(CaptureState.recording)CaptureState.send({action:'stopRecord'});else {CaptureState.options.recordSystemAudio=true;CaptureState.launch('record')}}
  function region():void {CaptureState.open('region')}
  function fullscreen():void {CaptureState.open('fullscreen')}
  function annotate():void {CaptureState.open('annotate')}
  function ocr():void {CaptureState.open('ocr')}
  function cancel():void {CaptureState.cancel()}
  function status():string {return JSON.stringify({opened:CaptureState.opened,busy:CaptureState.busy,ready:CaptureState.workerReady,pins:CaptureState.pins.length,monitor:CaptureState.frame.monitor || ''})}
 }
}
