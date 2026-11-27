import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.services
RowLayout {
 id:root
 spacing:18
 Item{Layout.preferredWidth:Math.min(72,Math.max(0,root.width-270))}
 Repeater {
  model:[{name:'backward',label:qsTr('Previous track'),available:MprisState.canGoPrevious},{name:MprisState.isPlaying ? 'pause':'play',label:MprisState.isPlaying ? qsTr('Pause'):qsTr('Play'),available:MprisState.canTogglePlaying},{name:'forward',label:qsTr('Next track'),available:MprisState.canGoNext},{name:'laptop',label:qsTr('Floating player'),available:true}]
  delegate:Item {
   required property var modelData
   required property int index
   Layout.fillWidth:true
   Layout.preferredWidth:32
   Layout.preferredHeight:40
   opacity:modelData.available ? 1:.3
   activeFocusOnTab:true
   Keys.onReturnPressed:activate()
   Keys.onSpacePressed:activate()
   Accessible.role:Accessible.Button
   Accessible.name:modelData.label
   Accessible.onPressAction:activate()
   function activate(){if(!modelData.available)return;if(index===0)MprisState.previous();else if(index===1)MprisState.togglePlaying();else if(index===2)MprisState.next();else ShelfState.playerOpen=true}
   ShelfIcon{anchors.centerIn:parent;size:index===1 ? 36:index===3 ? 28:38;icon:modelData.name+'.png'}
   MouseArea{anchors.fill:parent;enabled:parent.modelData.available;cursorShape:Qt.PointingHandCursor;onClicked:parent.activate()}
   Rectangle{anchors.fill:parent;radius:10;color:'transparent';border.width:parent.activeFocus ? 1:0;border.color:'#80ffffff'}
  }
 }
}
