import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell.Services.Pipewire
import qs.services
Item{
 id:root
 readonly property var streams:Pipewire.nodes.values.filter(n=>n.isStream && n.audio && !n.isSink)
 PwObjectTracker{objects:root.streams}
 ColumnLayout{anchors.fill:parent;spacing:12
  Text{text:qsTr('Audio Control');color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.title;font.weight:Font.DemiBold}
  ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;spacing:8;clip:true;model:root.streams
   ScrollBar.vertical:ScrollBar{policy:ScrollBar.AsNeeded}
   delegate:Item{id:row;required property var modelData;width:list.width;height:38
    Slider{id:volume;anchors.fill:parent;from:0;to:1;value:row.modelData.audio.volume;onMoved:row.modelData.audio.volume=value;Accessible.name:qsTr('%1 volume').arg(row.modelData.description || row.modelData.name)
     property bool held:false
     onPressedChanged:{if(held!==pressed){held=pressed;ShelfState.interaction(held)}}
     Component.onDestruction:if(held)ShelfState.interaction(false)
     background:Rectangle{radius:10;color:ShelfStyle.surface;clip:true
      Rectangle{width:parent.width*volume.visualPosition;height:parent.height;color:row.modelData.audio.muted ? '#12ffffff':'#38ffffff';radius:10}
     }
     handle:Item{}
    }
    RowLayout{anchors.fill:parent;anchors.margins:9;spacing:9
     ShelfIcon{Layout.preferredWidth:18;Layout.preferredHeight:18;size:18;icon:'notch/music.svg';color:ShelfStyle.primary}
     Text{Layout.fillWidth:true;text:row.modelData.description || row.modelData.name;elide:Text.ElideRight;color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;textFormat:Text.PlainText}
     Text{text:Math.round(row.modelData.audio.volume*100)+'%';color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.caption}
     ShelfButton{implicitWidth:24;implicitHeight:24;flat:true;icon:row.modelData.audio.muted ? 'notch/volume-x.svg':'notch/volume-2.svg';accessibleLabel:row.modelData.audio.muted ? qsTr('Unmute'):qsTr('Mute');onClicked:row.modelData.audio.muted=!row.modelData.audio.muted}
    }
   }
   Text{anchors.centerIn:parent;visible:list.count===0;text:qsTr('No active audio streams');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body}
  }
 }
}
