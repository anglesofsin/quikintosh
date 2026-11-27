import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.rosa.services
Item {
 id:root
 property var hub:null
 signal openPage(int page)
 readonly property var activities:{
  const rows=[]
  if(MprisState.hasPlayer)rows.push({title:MprisState.trackTitle || qsTr('Media'),subtitle:MprisState.trackArtist,icon:'notch/music.svg',page:3})
  if(hub && hub.kind==='voice')rows.push({title:qsTr('Call in progress'),subtitle:hub.label || '',icon:'notch/phone.svg',page:-1})
  if(hub && hub.downloadPhase)rows.push({title:qsTr('Downloads'),subtitle:hub.downloadName || '',icon:'notch/download.svg',page:6})
  if(ShelfState.items.length)rows.push({title:qsTr('File tray'),subtitle:qsTr('%1 files').arg(ShelfState.items.length),icon:'notch/inbox.svg',page:6})
  if(PomodoroState.running)rows.push({title:qsTr('Focus session'),subtitle:Math.ceil(PomodoroState.remainingMs/60000)+' min',icon:'notch/clock.svg',page:0})
  for(const activity of ShelfState.activities)rows.push({title:activity.title,subtitle:activity.subtitle,icon:"notch/zap.svg",page:-1,progress:activity.progress})
  if(ShelfState.awakeUntil>0)rows.push({title:qsTr('Stay Awake'),subtitle:Math.ceil((ShelfState.awakeUntil-ShelfState.now)/60000)+' min',icon:'notch/coffee.svg',page:12})
  return rows
 }
 ColumnLayout{anchors.fill:parent;spacing:12
  Text{text:qsTr('Live Activities');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold}
  ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;spacing:8;clip:true;model:root.activities
   delegate:Rectangle{required property var modelData;width:list.width;height:modelData.progress!==undefined && modelData.progress!==null ? 70:60;radius:20;color:ShelfStyle.surface
    RowLayout{anchors.fill:parent;anchors.margins:14
     ShelfButton{icon:modelData.icon;onClicked:if(modelData.page>=0)root.openPage(modelData.page)}
     ColumnLayout{Layout.fillWidth:true;spacing:3
      Text{Layout.fillWidth:true;elide:Text.ElideRight;textFormat:Text.PlainText;text:modelData.title;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:13;font.weight:Font.DemiBold}
      Text{Layout.fillWidth:true;elide:Text.ElideRight;textFormat:Text.PlainText;text:modelData.subtitle || '';color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
      Rectangle{visible:modelData.progress!==undefined && modelData.progress!==null;Layout.fillWidth:true;implicitHeight:3;radius:1.5;color:'#38383d';Rectangle{width:parent.width*(modelData.progress || 0);height:parent.height;radius:parent.radius;color:'white'}}
     }
     ShelfButton{text:qsTr('Open');visible:modelData.page>=0;onClicked:root.openPage(modelData.page)}
    }
   }
   Text{visible:list.count===0;anchors.centerIn:parent;text:qsTr('No active activities');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:14}
  }
 }
}
