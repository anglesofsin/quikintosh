import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.rosa.services
PanelWindow {
 id:root
 visible:ShelfState.basketOpen && !IslandBus.locked
 WlrLayershell.namespace:'quickintosh-drag-basket'
 WlrLayershell.layer:WlrLayer.Overlay
 mask:Region{item:basketBody;radius:28}
 exclusionMode:ExclusionMode.Ignore
 anchors{left:true;top:true}
 implicitWidth:260;implicitHeight:230;color:'transparent'
 margins.left:Math.max(4,Math.min(screen.width-width-4,ShelfState.basketPosition.x-screen.x-width/2))
 margins.top:Math.max(4,Math.min(screen.height-height-4,ShelfState.basketPosition.y-screen.y-height/2))
 Rectangle{id:basketBody;anchors.fill:parent;radius:28;color:'#f508080a';border.color:'#35ffffff'
  Grid{anchors.fill:parent;anchors.margins:12;columns:2;spacing:8
   Repeater{model:[{label:qsTr('Drop'),icon:'inbox',action:'drop'},{label:qsTr('Transform'),icon:'refresh-cw',action:'transform'},{label:qsTr('Files'),icon:'folder',action:'files'},{label:ShelfState.capabilities.share ? qsTr('LocalSend'):qsTr('Copy'),icon:ShelfState.capabilities.share ? 'send':'copy',action:ShelfState.capabilities.share ? 'share':'copy'}]
    Rectangle{required property var modelData;width:114;height:99;radius:16;color:target.containsDrag ? '#403a3a40':'#141416'
     Column{anchors.centerIn:parent;spacing:12
      ShelfIcon{anchors.horizontalCenter:parent.horizontalCenter;size:26;icon:'notch/'+modelData.icon+'.svg'}
      Text{anchors.horizontalCenter:parent.horizontalCenter;text:modelData.label;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:12}
     }
     DropArea{id:target;objectName:'basket-target-'+modelData.action;anchors.fill:parent;onEntered:drag=>{drag.accepted=drag.hasUrls};onDropped:drop=>{const paths=Array.from(drop.urls).map(String);ShelfState.add(paths);if(modelData.action==='transform'){ShelfState.transformPaths=paths.map(u=>decodeURIComponent(u.replace(/^file:\/\//,'')));ShelfState.transformOpen=true}else if(modelData.action==='share'){ShelfState.send({action:'share',paths:paths.map(u=>decodeURIComponent(u.replace(/^file:\/\//,'')))})}else if(modelData.action==='copy')ShelfState.send({action:'copy',paths:paths.map(u=>decodeURIComponent(u.replace(/^file:\/\//,'')))});else if(modelData.action==='files')ShelfState.reveal(6);ShelfState.basketOpen=false;drop.acceptProposedAction()}}
    }
   }
  }
 }
 Timer{interval:60000;running:root.visible;onTriggered:ShelfState.basketOpen=false}
 Shortcut{sequence:'Escape';onActivated:ShelfState.basketOpen=false}
}
