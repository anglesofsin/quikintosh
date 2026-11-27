import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs
import Quickshell
import Quickshell.Widgets
import qs.services
Item{
 id:root;objectName:'shelf-queue'
 property bool showPlayer:true
 property bool inlineActions:false
 signal requestLyrics()
 signal requestOutput()
 onRequestLyrics:if(!inlineActions)ShelfState.reveal(9)
 onRequestOutput:if(!inlineActions)ShelfState.playerOpen=true
 property var reviewQueue:null
 readonly property string watchId:String(Date.now())+String(Math.random())
 signal closeQueue()
 readonly property string player:MprisState.activePlayer?.dbusName || ''
 readonly property bool watching:visible && !!QsWindow.window && QsWindow.window.visible
 readonly property var queue:reviewQueue || (ShelfState.queueData.player===player ? ShelfState.queueData:({supported:false,items:[]}))
 readonly property var nextItems:{const rows=queue.items || [];const index=rows.findIndex(row=>row.id===queue.current);return index>=0 ? rows.slice(index+1):rows}
 function refresh(){if(!reviewQueue)ShelfState.watchQueue(watchId,player,watching && !!player)}
 Timer{interval:4000;repeat:true;running:root.watching && !!root.player && !root.reviewQueue;onTriggered:root.refresh()}
 onPlayerChanged:if(watching)refresh()
 onWatchingChanged:refresh()
 Component.onCompleted:refresh()
 Component.onDestruction:ShelfState.watchQueue(watchId,player,false)
 Connections{target:MprisState;function onActivePlayerChanged(){if(root.watching)root.refresh()}}
 Connections{target:MprisState.activePlayer;function onTrackChanged(){if(root.watching)root.refresh()}}
 FileDialog{id:audio;title:qsTr('Add to Playing Next');nameFilters:[qsTr('Media (*.mp3 *.wav *.flac *.ogg *.opus *.m4a *.aac *.mp4 *.mkv)')];onAccepted:ShelfState.send({action:'queueAction',player:root.player,operation:'add',path:String(selectedFile)})}
 ColumnLayout{anchors.fill:parent;spacing:10
  ShelfMedia{visible:root.showPlayer;Layout.fillWidth:true;Layout.preferredHeight:176;inlineActions:true;showPopout:true;queueSelected:true;onOpenQueue:root.closeQueue();onOpenLyrics:root.requestLyrics();onOpenOutput:root.requestOutput()}
  Rectangle{Layout.alignment:Qt.AlignHCenter;Layout.preferredWidth:96;Layout.preferredHeight:1;color:'#18ffffff';visible:root.showPlayer}
  RowLayout{Layout.fillWidth:true;Layout.topMargin:8
   Text{Layout.fillWidth:true;text:qsTr('Playing Next');color:'#a5a5aa';font.family:ShelfStyle.textFamily;font.pixelSize:14;font.weight:Font.DemiBold}
   ShelfButton{visible:root.queue.editable===true;flat:true;icon:'notch/plus.svg';accessibleLabel:qsTr('Add media');onClicked:audio.open()}
  }
  ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:6;model:root.nextItems
   ScrollBar.vertical:ScrollBar{}
   delegate:Rectangle{required property var modelData;width:list.width;height:62;radius:12;color:rowHover.containsMouse ? '#16ffffff':'transparent'
    MouseArea{id:rowHover;hoverEnabled:true;anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:ShelfState.send({action:'queueAction',player:root.player,operation:'jump',id:parent.modelData.id})}
    RowLayout{anchors.fill:parent;anchors.margins:7;spacing:10
     ClippingRectangle{Layout.preferredWidth:44;Layout.preferredHeight:44;radius:8;color:'#242429';Image{anchors.fill:parent;source:modelData.art;sourceSize:Qt.size(76,76);fillMode:Image.PreserveAspectCrop;asynchronous:true}ShelfIcon{anchors.centerIn:parent;visible:!modelData.art;size:21;icon:'notch/music.svg'}}
     ColumnLayout{Layout.fillWidth:true;spacing:2
      Text{Layout.fillWidth:true;text:modelData.title;textFormat:Text.PlainText;elide:Text.ElideRight;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:16;font.weight:Font.DemiBold}
      Text{Layout.fillWidth:true;text:modelData.artist;textFormat:Text.PlainText;elide:Text.ElideRight;color:'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:14}
     }
     ShelfIcon{size:21;icon:'notch/list.svg';color:'#8e8e93'}
     ShelfButton{visible:root.queue.editable===true;flat:true;icon:'notch/minus.svg';accessibleLabel:qsTr('Remove from queue');onClicked:ShelfState.send({action:'queueAction',player:root.player,operation:'remove',id:modelData.id})}
    }
   }
   Text{visible:list.count===0 && (root.queue.fetched || !root.player);anchors.centerIn:parent;width:parent.width;text:!root.player ? qsTr('Play music to see Playing Next.'):root.queue.supported ? qsTr('This queue is empty.'):qsTr('Queue unavailable for this player.');wrapMode:Text.Wrap;horizontalAlignment:Text.AlignHCenter;color:'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:13}
  }
 }
 DropArea{anchors.fill:parent;z:-1;onDropped:drop=>{if(root.queue.editable && drop.urls.length){ShelfState.send({action:'queueAction',player:root.player,operation:'add',path:String(drop.urls[0])});drop.acceptProposedAction()}}}
}
