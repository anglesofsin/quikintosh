import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
ShellRoot{id:root
 property bool animateBackground:false
 PanelWindow{anchors{top:true;bottom:true;left:true;right:true}
 color:'transparent';exclusiveZone:-1;WlrLayershell.namespace:'qa-background';WlrLayershell.layer:WlrLayer.Background;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
 Rectangle{anchors.fill:parent;color:Qt.rgba(.5+.5*Math.sin(t),.05,.5-.5*Math.sin(t),1);property real t:0;NumberAnimation on t{running:root.animateBackground;from:0;to:6.283;duration:1000;loops:Animation.Infinite}}
 }
 FloatingWindow{visible:true;title:'QI Glass Target';implicitWidth:700;implicitHeight:400;color:'#08000000';Text{text:'Glass';anchors.top:parent.top;color:'white'}}
 PanelWindow{anchors{top:true;left:true}
 margins.left:400;margins.top:300;implicitWidth:40;implicitHeight:40;exclusiveZone:-1;color:'transparent';WlrLayershell.namespace:'qa-top';WlrLayershell.layer:WlrLayer.Top;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
 Rectangle{anchors.fill:parent;color:Qt.rgba(t,.3,.8,1);property real t:0;NumberAnimation on t{from:0;to:1;duration:300;loops:Animation.Infinite}}
 }
 IpcHandler{target:'qa';function animate(value:bool):void{root.animateBackground=value}}
}