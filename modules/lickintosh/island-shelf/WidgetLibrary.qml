import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.rosa.services
Flickable {
 id:root;clip:true;contentWidth:width;contentHeight:contents.implicitHeight;boundsBehavior:Flickable.StopAtBounds;signal openPage(int page)
 readonly property var widgets:[{key:'media',title:qsTr('Now Playing'),page:3},{key:'calendar',title:qsTr('Calendar'),page:0},{key:'weather',title:qsTr('Weather'),page:1},{key:'focus',title:qsTr('Focus'),page:0},{key:'notes',title:qsTr('Notes'),page:0},{key:'performance',title:qsTr('System'),page:2},{key:'files',title:qsTr('File tray'),page:6}]
 ColumnLayout{id:contents;width:root.width;spacing:14
  Text{text:qsTr('Your shelf');color:'white';font.family:'SF Pro Display';font.pixelSize:19;font.weight:Font.DemiBold}
  RowLayout{Layout.fillWidth:true;spacing:12
   Repeater{model:4
    delegate:Rectangle{required property int index;Layout.fillWidth:true;implicitHeight:126;radius:18;color:'#17171a';border.color:'#2b2b30'
     ColumnLayout{anchors.fill:parent;anchors.margins:12;spacing:8
      Text{text:qsTr('Position %1').arg(index+1);color:'#9898a0';font.family:'SF Pro Text';font.pixelSize:11}
      ShelfChoice{Layout.fillWidth:true;model:[qsTr('None')].concat(root.widgets.map(w=>w.title));currentIndex:root.widgets.findIndex(w=>w.key===IslandConfig.s('shelfSlot'+(index+1)))+1;onActivated:i=>IslandConfig.setStyle('shelfSlot'+(index+1),i ? root.widgets[i-1].key:'none')}
      RowLayout{Layout.fillWidth:true
       Text{text:qsTr('Width');color:'#b0b0b8';font.family:'SF Pro Text';font.pixelSize:11}
       ShelfSlider{Layout.fillWidth:true;from:1;to:3;stepSize:1;value:IslandConfig.s('shelfWeight'+(index+1));onMoved:IslandConfig.setStyle('shelfWeight'+(index+1),value)}
      }
     }
    }
   }
  }
  Flow{Layout.fillWidth:true;spacing:8
   Repeater{model:[{title:qsTr('Weather'),page:1},{title:qsTr('System'),page:2},{title:qsTr('Notifications'),page:4},{title:qsTr('Camera'),page:5},{title:qsTr('Clipboard'),page:7},{title:qsTr('Lyrics'),page:9},{title:qsTr('App volume'),page:10},{title:qsTr('Activities'),page:11},{title:qsTr('Stay Awake'),page:12}]
    delegate:ShelfButton{required property var modelData;text:modelData.title;onClicked:root.openPage(modelData.page)}
   }
  }
  Flow{Layout.fillWidth:true;spacing:8
   Repeater{model:[{title:qsTr('Quickshot'),method:'region'},{title:qsTr('Text Capture'),method:'ocr'},{title:qsTr('Pick color'),method:'colorPicker'}]
    delegate:ShelfButton{required property var modelData;text:modelData.title;onClicked:Quickshell.execDetached(['quickintosh','ipc','call','capture',modelData.method])}
   }
   ShelfButton{text:qsTr('Settings');onClicked:SettingsLauncher.open('RosaPage')}
  }
  RowLayout{spacing:10
   ShelfButton{text:qsTr('Arrange on shelf');onClicked:{ShelfState.editing=true;root.openPage(0)}}
   ShelfButton{text:qsTr('Music · Calendar · Weather');onClicked:{for(const [i,key] of ['media','calendar','weather','none'].entries())IslandConfig.setStyle('shelfSlot'+(i+1),key)}}
   ShelfButton{text:qsTr('Focus · Notes · Files');onClicked:{for(const [i,key] of ['focus','notes','files','none'].entries())IslandConfig.setStyle('shelfSlot'+(i+1),key)}}
   Item{Layout.fillWidth:true}
  }
 }
}
