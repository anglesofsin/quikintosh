import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services
PanelWindow {
 id:root
 property var shot:({})
 property real zoom:1
 screen:Quickshell.screens.find(s=>s.name===shot.monitor) || Quickshell.screens[0]
 anchors {top:true;bottom:true;left:true;right:true}
 color:'transparent';exclusiveZone:-1
 mask:Region {item:picture}
 WlrLayershell.namespace:'lickintosh:pinned-capture'
 WlrLayershell.layer:WlrLayer.Overlay
 WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
 // Stable compositor surface: move only the scene-graph quad, never reconfigure
 // layer-shell margins on every pointer event (which creates motion feedback).
 Item {
  id:picture;x:32;y:64
  width:Math.max(48,Math.min(root.screen.width*.85,(root.shot.width || 300)*root.zoom))
  height:width*(root.shot.height || 200)/(root.shot.width || 300)
  Rectangle {anchors.fill:parent;color:'#262629';radius:5;border.width:1;border.color:'#8a8a90'}
  Image {anchors.fill:parent;anchors.margins:1;source:root.shot.path ? 'file://'+root.shot.path : '';fillMode:Image.PreserveAspectFit;cache:true}
  MouseArea {
   id:move;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.SizeAllCursor
   property real dragX:0
   property real dragY:0
   property real initialX:0
   property real initialY:0
   onPressed:m=>{const p=mapToItem(root.contentItem,m.x,m.y);dragX=p.x;dragY=p.y;initialX=picture.x;initialY=picture.y}
   onPositionChanged:m=>{if(pressed){const p=mapToItem(root.contentItem,m.x,m.y);picture.x=Math.max(0,Math.min(root.screen.width-picture.width,initialX+p.x-dragX));picture.y=Math.max(0,Math.min(root.screen.height-picture.height,initialY+p.y-dragY))}}
   onWheel:event=>{root.zoom=Math.max(.1,Math.min(3,root.zoom*(event.angleDelta.y>0 ? 1.1 : .9)));event.accepted=true}
  }
  Rectangle {
   width:24;height:24;radius:12;anchors.top:parent.top;anchors.right:parent.right;anchors.margins:5;color:'#dd202023';visible:move.containsMouse || closeMouse.containsMouse
   Text {anchors.centerIn:parent;text:'×';font.pixelSize:22;color:'white'}
   MouseArea {id:closeMouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:CaptureState.unpin(root.shot.id)}
  }
 }
}
