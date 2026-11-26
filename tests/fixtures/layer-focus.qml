import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
ShellRoot{
 property bool opened:false
 FloatingWindow{visible:true;title:'QI Hidden Call';implicitWidth:200;implicitHeight:150;Rectangle{anchors.fill:parent;color:'blue'}}
 PanelWindow{anchors{top:true;bottom:true;left:true;right:true}
color:'#222222';exclusiveZone:-1;WlrLayershell.namespace:'quickshell:desktop';WlrLayershell.layer:WlrLayer.Top;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None}
 PanelWindow{visible:opened;anchors{top:true;bottom:true;left:true;right:true}
color:'#404040';exclusiveZone:-1;WlrLayershell.namespace:'quickshell:qa-panel';WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.keyboardFocus:WlrKeyboardFocus.Exclusive}
 IpcHandler{target:'qa';function setPanel(value:bool):void{opened=value}}
}