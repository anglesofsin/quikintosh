import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs
import Quickshell
import Quickshell.Widgets
import qs.services
Item{
 id:root;objectName:'shelf-queue'
 readonly property string player:MprisState.activePlayer?.dbusName || ''
 readonly property bool watching:visible && !!QsWindow.window && QsWindow.window.visible
 readonly property var queue:ShelfState.queueData.player===player ? ShelfState.queueData:({supported:false,items:[]})
 function refresh(){ShelfState.send({action:'queueWatch',player:player,enabled:watching && !!player})}
 onPlayerChanged:if(watching)refresh()
 onWatchingChanged:refresh()
 Component.onCompleted:refresh()
 Component.onDestruction:ShelfState.send({action:'queueWatch',enabled:false})
 Connections{target:MprisState;function onActivePlayerChanged(){if(root.watching)root.refresh()}}
 Connections{target:MprisState.activePlayer;function onTrackChanged(){if(root.watching)root.refresh()}}
 FileDialog{id:audio;title:qsTr('Add to Playing Next');nameFilters:[qsTr('Media (*.mp3 *.wav *.flac *.ogg *.opus *.m4a *.aac *.mp4 *.mkv)')];onAccepted:ShelfState.send({action:'queueAction',player:root.player,operation:'add',path:String(selectedFile)})}
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true
   ColumnLayout{Layout.fillWidth:true;spacing:3
    Text{text:qsTr('Playing Next');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:19;font.weight:Font.DemiBold}
    Text{text:MprisState.identity || qsTr('No media player');color:'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:12}
   }
   Item{Layout.fillWidth:true}
   ShelfButton{flat:true;icon:'notch/refresh-cw.svg';accessibleLabel:qsTr('Refresh queue');onClicked:root.refresh()}
   ShelfButton{visible:root.queue.editable===true;flat:true;icon:'notch/plus.svg';accessibleLabel:qsTr('Add media');onClicked:audio.open()}
  }
  ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:6;model:root.queue.items || []
   ScrollBar.vertical:ScrollBar{}
   delegate:Rectangle{required property var modelData;width:list.width;height:52;radius:14;color:root.queue.current===modelData.id ? '#260a84ff':'#10ffffff'
    MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:ShelfState.send({action:'queueAction',player:root.player,operation:'jump',id:parent.modelData.id})}
    RowLayout{anchors.fill:parent;anchors.margins:7;spacing:10
     ClippingRectangle{Layout.preferredWidth:38;Layout.preferredHeight:38;radius:8;color:'#242429';Image{anchors.fill:parent;source:modelData.art;sourceSize:Qt.size(76,76);fillMode:Image.PreserveAspectCrop;asynchronous:true}ShelfIcon{anchors.centerIn:parent;visible:!modelData.art;size:21;icon:'notch/music.svg'}}
     ColumnLayout{Layout.fillWidth:true;spacing:2
      Text{Layout.fillWidth:true;text:modelData.title;textFormat:Text.PlainText;elide:Text.ElideRight;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:13;font.weight:Font.DemiBold}
      Text{Layout.fillWidth:true;text:modelData.artist;textFormat:Text.PlainText;elide:Text.ElideRight;color:'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
     }
     Text{text:Math.floor(modelData.length/60)+':'+String(Math.floor(modelData.length%60)).padStart(2,'0');color:'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
     ShelfButton{visible:root.queue.editable===true;flat:true;icon:'notch/minus.svg';accessibleLabel:qsTr('Remove from queue');onClicked:ShelfState.send({action:'queueAction',player:root.player,operation:'remove',id:modelData.id})}
    }
   }
   Text{visible:list.count===0 && (root.queue.fetched || !root.player);anchors.centerIn:parent;width:parent.width;text:!root.player ? qsTr('Play music to see Playing Next.'):root.queue.supported ? qsTr('This queue is empty.'):qsTr('Queue unavailable for this player.');wrapMode:Text.Wrap;horizontalAlignment:Text.AlignHCenter;color:'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:13}
  }
 }
 DropArea{anchors.fill:parent;z:-1;onDropped:drop=>{if(root.queue.editable && drop.urls.length){ShelfState.send({action:'queueAction',player:root.player,operation:'add',path:String(drop.urls[0])});drop.acceptProposedAction()}}}
}
