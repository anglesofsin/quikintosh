import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
ShellRoot {
 id:root
 property bool shown:true
 PanelWindow {
  anchors {top:true;bottom:true;left:true;right:true}
  exclusiveZone:-1;color:'#6080a0'
  WlrLayershell.namespace:'qa-background'
  WlrLayershell.layer:WlrLayer.Background
  WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
 }
 PanelWindow {
  id:dock
  anchors {bottom:true;left:true;right:true}
  implicitHeight:180;exclusiveZone:-1;color:'transparent'
  WlrLayershell.namespace:'quickshell:dock'
  WlrLayershell.layer:WlrLayer.Top
  WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
  Rectangle {
   width:500;height:80;radius:24;color:'#08000000';border.color:'#38ffffff'
   x:(dock.width-width)/2;y:root.shown ? 80:200
   Behavior on y {NumberAnimation {duration:160;easing.type:Easing.OutCubic}}
   Row {anchors.centerIn:parent;spacing:12
    Repeater {model:6;Rectangle {width:48;height:48;radius:10;color:'#5b65c0'}}
   }
  }
 }
 IpcHandler {target:'qa';function setShown(value:bool):void {root.shown=value}}
}
