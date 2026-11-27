import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import Quickshell
import qs.services
import qs.rosa.services
Item {
 id:root
 objectName:'shelf-home-editor'
 property alias contextMenu:menu
 signal openPage(int page)
 property var savedSlots:[]
 readonly property var catalog:[{key:'weather',label:qsTr('Weather'),icon:'cloud'},{key:'media',label:qsTr('Now Playing'),icon:'music'},{key:'focus',label:qsTr('Pomodoro'),icon:'clock'},{key:'calendar',label:qsTr('Calendar'),icon:'calendar'},{key:'notes',label:qsTr('Notes'),icon:'edit-3'},{key:'performance',label:qsTr('System Stats'),icon:'cpu'},{key:'files',label:qsTr('Files'),icon:'inbox'}]
 function snapshot(){savedSlots=[1,2,3,4].map(i=>IslandConfig.s('shelfSlot'+i))}
 function choose(key){const slots=[1,2,3,4].map(i=>IslandConfig.s('shelfSlot'+i));const existing=slots.indexOf(key);if(existing>=0)IslandConfig.setStyle('shelfSlot'+(existing+1),'none');else {const empty=slots.indexOf('none');IslandConfig.setStyle('shelfSlot'+(empty>=0 ? empty+1:4),key)}}
 onVisibleChanged:if(visible && ShelfState.editing)snapshot()
 Connections{target:ShelfState;function onEditingChanged(){if(ShelfState.editing)root.snapshot()}}
 ColumnLayout{anchors.fill:parent;spacing:14
  ShelfHome{Layout.fillWidth:true;Layout.fillHeight:true;onOpenPage:page=>root.openPage(page)}
  RowLayout{visible:ShelfState.editing;Layout.fillWidth:true;spacing:8
   Flickable{Layout.fillWidth:true;Layout.preferredHeight:72;contentWidth:catalogRow.implicitWidth;clip:true;boundsBehavior:Flickable.StopAtBounds
    RowLayout{id:catalogRow;spacing:6
     Repeater{model:root.catalog
      delegate:ColumnLayout{required property var modelData;spacing:5
       ShelfButton{Layout.alignment:Qt.AlignHCenter;implicitWidth:48;implicitHeight:40;icon:'notch/'+modelData.icon+'.svg';iconSize:25;selected:[1,2,3,4].some(i=>IslandConfig.s('shelfSlot'+i)===modelData.key);onClicked:root.choose(modelData.key)
        DragHandler{id:catalogDrag;target:dragProxy;onActiveChanged:if(active)ShelfState.interaction(true);else ShelfState.interaction(false)}
        Item{id:dragProxy;Drag.active:catalogDrag.active;Drag.dragType:Drag.Automatic;Drag.supportedActions:Qt.CopyAction;Drag.mimeData:({'application/x-quickintosh-widget':modelData.key});Drag.onDragFinished:{x=0;y=0}}
       }
       Text{Layout.preferredWidth:68;text:modelData.label;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:10;elide:Text.ElideRight;horizontalAlignment:Text.AlignHCenter}
      }
     }
    }
   }
   ShelfButton{icon:'notch/x.svg';accessibleLabel:qsTr('Cancel customization');onClicked:{root.savedSlots.forEach((key,i)=>IslandConfig.setStyle('shelfSlot'+(i+1),key));ShelfState.editing=false}}
   ShelfButton{icon:'notch/check.svg';selected:true;accessibleLabel:qsTr('Finish customization');onClicked:ShelfState.editing=false}
  }
 }
 ShelfButton{id:optionsButton;objectName:'home-options';visible:!ShelfState.editing;anchors.right:parent.right;anchors.top:parent.top;implicitWidth:26;implicitHeight:26;opacity:.65;icon:'notch/more-horizontal.svg';accessibleLabel:qsTr('Home options');onClicked:menu.popup(optionsButton,optionsButton.width-menu.width,optionsButton.height+4)}
 ShelfMenu{id:menu
  ShelfMenuItem{text:qsTr('Customize Home');onTriggered:ShelfState.editing=true}
  ShelfMenuItem{text:qsTr('Audio sources');onTriggered:root.openPage(10)}
  ShelfMenuItem{text:qsTr('Widgets');onTriggered:root.openPage(8)}
  ShelfMenuItem{text:qsTr('Settings');onTriggered:SettingsLauncher.open('')}
 }
}
