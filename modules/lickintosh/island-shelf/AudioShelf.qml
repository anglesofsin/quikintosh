import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell.Widgets
import Quickshell.Services.Pipewire
import qs.services
Item{
 id:root
 property bool inputs:false
 readonly property var streams:Pipewire.nodes.values.filter(n=>n.isStream && n.audio && n.isSink===inputs)
 PwObjectTracker{objects:root.visible ? root.streams:[]}
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true;spacing:6
   ShelfButton{implicitWidth:30;implicitHeight:30;icon:'notch/volume-2.svg';selected:!root.inputs;accessibleLabel:qsTr('Application output');onClicked:root.inputs=false}
   ShelfButton{implicitWidth:30;implicitHeight:30;icon:'notch/mic.svg';selected:root.inputs;accessibleLabel:qsTr('Application input');onClicked:root.inputs=true}
   Item{Layout.fillWidth:true}
   ShelfButton{implicitWidth:30;implicitHeight:30;icon:'notch/rotate-ccw.svg';accessibleLabel:qsTr('Reset application volumes');enabled:root.streams.length>0;onClicked:root.streams.forEach(n=>{n.audio.volume=1;n.audio.muted=false})}
  }
  ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;spacing:6;clip:true;model:root.streams
   ScrollBar.vertical:ScrollBar{policy:ScrollBar.AsNeeded}
   delegate:Item{id:row;required property var modelData;width:list.width;height:40
    Slider{id:volume;anchors.fill:parent;padding:0;from:0;to:1;value:row.modelData.audio.volume;onMoved:row.modelData.audio.volume=value;Accessible.name:qsTr('%1 volume').arg(row.modelData.description || row.modelData.name)
     property bool held:false
     onPressedChanged:{if(held!==pressed){held=pressed;ShelfState.interaction(held)}}
     Component.onDestruction:if(held)ShelfState.interaction(false)
     background:ClippingRectangle{x:0;y:0;width:volume.width;height:volume.height;radius:20;color:'#101012'
      Rectangle{width:parent.width*volume.visualPosition;height:parent.height;color:row.modelData.audio.muted ? '#1a19191c':'#38ffffff'}
     }
     handle:Item{}
    }
    RowLayout{anchors.fill:parent;anchors.leftMargin:14;anchors.rightMargin:14;spacing:10
     Image{Layout.preferredWidth:18;Layout.preferredHeight:18;source:IconResolver.forAppId(row.modelData.properties?.['application.icon-name'] || row.modelData.name);sourceSize:Qt.size(36,36);fillMode:Image.PreserveAspectFit;asynchronous:true}
     Text{Layout.fillWidth:true;text:row.modelData.properties?.['application.name'] || row.modelData.description || row.modelData.name;elide:Text.ElideRight;color:row.modelData.audio.muted ? '#78787d':ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:13;font.weight:Font.DemiBold;textFormat:Text.PlainText}
     Text{text:Math.round(row.modelData.audio.volume*100)+'%';color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
    }
    TapHandler{acceptedButtons:Qt.RightButton;onTapped:row.modelData.audio.muted=!row.modelData.audio.muted}
   }
   Text{anchors.centerIn:parent;visible:list.count===0;text:root.inputs ? qsTr('No microphone streams'):qsTr('No active audio streams');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:13}
  }
 }
}
