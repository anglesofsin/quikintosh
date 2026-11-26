import QtQuick
import QtQuick.Controls
import Quickshell
import qs.services
import qs.rosa.services
FloatingWindow {
 id:root;visible:ShelfState.trayOpen && !IslandBus.locked;title:'Quickintosh File Tray';color:'transparent';implicitWidth:760;implicitHeight:400;minimumSize:Qt.size(540,300)
 onVisibleChanged:if(!visible)ShelfState.trayOpen=false
 Rectangle{anchors.fill:parent;radius:24;color:IslandConfig.s('shelfMaterial')==='black' || !RenderingState.glassEnabled ? '#ff000000':'#60202024';border.color:'#35ffffff'
  FileTray{anchors.fill:parent;anchors.margins:18;floating:true}
  ShelfButton{anchors.top:parent.top;anchors.right:parent.right;anchors.margins:8;icon:'notch/x.svg';onClicked:ShelfState.trayOpen=false}
  MouseArea{anchors.left:parent.left;anchors.top:parent.top;width:160;height:30;onPressed:root.startSystemMove()}
 }
 Shortcut{sequence:'Escape';onActivated:ShelfState.trayOpen=false}
}
