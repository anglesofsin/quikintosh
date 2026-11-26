import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell.Services.Pipewire
import qs.services
Item {
 id:root
 readonly property var streams:Pipewire.nodes.values.filter(n=>n.isStream && n.audio && !n.isSink)
 PwObjectTracker {objects:root.streams}
 ColumnLayout{anchors.fill:parent;spacing:12
  Text{text:qsTr('App volume');color:'white';font.family:'SF Pro Display';font.pixelSize:18;font.weight:Font.DemiBold}
  ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;spacing:7;clip:true;model:root.streams;ScrollBar.vertical:ScrollBar{}
   delegate:Rectangle{required property var modelData;width:list.width;height:58;radius:14;color:'#17171b'
    RowLayout{anchors.fill:parent;anchors.margins:12;spacing:12
     Text{Layout.preferredWidth:180;text:modelData.description || modelData.name;color:'white';font.family:'SF Pro Text';font.pixelSize:13;elide:Text.ElideRight}
     ShelfSlider{Layout.fillWidth:true;from:0;to:1;value:modelData.audio.volume;onMoved:modelData.audio.volume=value}
     ShelfButton{text:modelData.audio.muted ? qsTr('Unmute'):qsTr('Mute');onClicked:modelData.audio.muted=!modelData.audio.muted}
    }
   }
   Text{anchors.centerIn:parent;visible:list.count===0;text:qsTr('No active audio streams');color:'#9999a0';font.family:'SF Pro Text';font.pixelSize:14}
  }
 }
}
