import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.rosa.services
PanelWindow {
 id:root
 visible:root.reveal>0.001 && !IslandBus.locked
 WlrLayershell.namespace:'quickintosh-drag-basket'
 WlrLayershell.layer:WlrLayer.Overlay
 WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
 mask:Region{item:basketBody;radius:28}
 exclusionMode:ExclusionMode.Ignore
 anchors{left:true;top:true}
 implicitWidth:260;implicitHeight:230;color:'transparent'
 margins.left:Math.max(4,Math.min(screen.width-width-4,ShelfState.basketPosition.x-screen.x-width/2))
 margins.top:Math.max(4,Math.min(screen.height-height-4,ShelfState.basketPosition.y-screen.y-height/2))
 property real reveal:ShelfState.basketOpen && !IslandBus.locked ? 1:0
 Behavior on reveal{NumberAnimation{duration:180;easing.type:Easing.OutCubic}}
 ShelfRoundedSurface{id:basketBody;anchors.fill:parent;radius:28;color:'transparent';border.width:1;border.color:'#28ffffff';opacity:root.reveal;scale:.94+.06*root.reveal
  ShelfPanelMaterial{anchors.fill:parent;cornerRadius:28}
  Grid{anchors.fill:parent;anchors.margins:12;columns:2;spacing:8
   Repeater{model:[{label:qsTr('Drop'),icon:'inbox',action:'drop'},{label:qsTr('Transform'),icon:'refresh-cw',action:'transform'},{label:qsTr('Files'),icon:'folder',action:'files'},{label:ShelfState.capabilities.share ? (ShelfState.capabilities.kdeconnect ? qsTr('KDE Connect'):qsTr('LocalSend')):qsTr('Copy'),icon:ShelfState.capabilities.share ? 'send':'copy',action:ShelfState.capabilities.share ? 'share':'copy'}]
    Rectangle{required property var modelData;width:114;height:99;radius:16;property bool highlighted:target.containsDrag || pointer.hovered;color:highlighted ? '#32ffffff':'#0cffffff';border.width:highlighted ? 1:0;border.color:'#38ffffff';scale:target.containsDrag ? 1.035:pointer.hovered ? 1.015:1
     Behavior on color{ColorAnimation{duration:140}}
     Behavior on scale{NumberAnimation{duration:170;easing.type:Easing.OutCubic}}
     HoverHandler{id:pointer}
     Column{anchors.centerIn:parent;spacing:12
      ShelfIcon{anchors.horizontalCenter:parent.horizontalCenter;size:26;icon:'notch/'+modelData.icon+'.svg'}
      Text{anchors.horizontalCenter:parent.horizontalCenter;text:modelData.label;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:12}
     }
     DropArea{id:target;objectName:'basket-target-'+modelData.action;anchors.fill:parent;onEntered:drag=>{drag.accepted=drag.hasUrls;drag.accept(Qt.CopyAction)};onDropped:drop=>{const paths=Array.from(drop.urls).map(String);ShelfState.add(paths);if(modelData.action==='transform'){ShelfState.transformPaths=paths.map(u=>decodeURIComponent(u.replace(/^file:\/\//,'')));ShelfState.transformOpen=true}else if(modelData.action==='share'){ShelfState.send({action:'share',provider:ShelfState.capabilities.kdeconnect ? 'kdeconnect':'localsend',paths:paths.map(u=>decodeURIComponent(u.replace(/^file:\/\//,'')))})}else if(modelData.action==='copy')ShelfState.send({action:'copy',paths:paths.map(u=>decodeURIComponent(u.replace(/^file:\/\//,'')))});else if(modelData.action==='files')ShelfState.reveal(6);ShelfState.basketOpen=false;drop.accept(Qt.CopyAction)}}
    }
   }
  }
 }
 Timer{interval:60000;running:root.visible;onTriggered:ShelfState.basketOpen=false}
 Shortcut{sequence:'Escape';onActivated:ShelfState.basketOpen=false}
}
