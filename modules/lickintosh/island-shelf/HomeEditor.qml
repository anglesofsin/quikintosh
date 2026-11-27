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
 property var savedWeights:[]
 readonly property var catalog:ShelfState.orderWidgets([{key:'weather',label:qsTr('Weather'),icon:'cloud'},{key:'media',label:qsTr('Now Playing'),icon:'music'},{key:'focus',label:qsTr('Pomodoro'),icon:'clock'},{key:'calendar',label:qsTr('Calendar'),icon:'calendar'},{key:'notes',label:qsTr('Notes'),icon:'edit-3'},{key:'performance',label:qsTr('System Stats'),icon:'cpu'},{key:'files',label:qsTr('Files'),icon:'inbox'},{key:'clipboard',label:qsTr('Clipboard'),icon:'clipboard'},{key:'audio',label:qsTr('Audio'),icon:'volume-2'},{key:'awake',label:qsTr('Stay Awake'),icon:'coffee'},{key:'storage',label:qsTr('Storage'),icon:'hard-drive'},{key:'camera',label:qsTr('Camera'),icon:'camera'},{key:'notifications',label:qsTr('Notifications'),icon:'bell'}])
 function snapshot(){savedSlots=[1,2,3,4].map(i=>IslandConfig.s('shelfSlot'+i));savedWeights=[1,2,3,4].map(i=>IslandConfig.s('shelfWeight'+i))}
 function choose(key){ShelfState.useWidget(key);const slots=[1,2,3,4].map(i=>IslandConfig.s('shelfSlot'+i));const existing=slots.indexOf(key);if(existing>=0)IslandConfig.setStyle('shelfSlot'+(existing+1),'none');else {const empty=slots.indexOf('none');IslandConfig.setStyle('shelfSlot'+(empty>=0 ? empty+1:4),key)}}
 Component.onCompleted:if(ShelfState.editing)snapshot()
 Connections{target:ShelfState;function onEditingChanged(){if(ShelfState.editing)root.snapshot()}}
 ColumnLayout{anchors.fill:parent;spacing:14
  ShelfHome{Layout.fillWidth:true;Layout.fillHeight:true;onOpenPage:page=>root.openPage(page)}
  RowLayout{visible:ShelfState.editing;Layout.fillWidth:true;spacing:8
   Flickable{Layout.fillWidth:true;Layout.preferredHeight:72;contentWidth:catalogRow.implicitWidth;clip:true;boundsBehavior:Flickable.StopAtBounds
    RowLayout{id:catalogRow;spacing:6
     Repeater{model:root.catalog
      delegate:ColumnLayout{required property var modelData;spacing:5
       ShelfButton{Layout.alignment:Qt.AlignHCenter;implicitWidth:46;implicitHeight:46;icon:'notch/'+modelData.icon+'.svg';iconSize:25;selected:[1,2,3,4].some(i=>IslandConfig.s('shelfSlot'+i)===modelData.key);onClicked:root.choose(modelData.key)
        DragHandler{id:catalogDrag;target:dragProxy;onActiveChanged:if(active)ShelfState.interaction(true);else{dragProxy.Drag.drop();ShelfState.interaction(false)}}
        Item{id:dragProxy;property string widgetKey:modelData.key;Drag.source:dragProxy;Drag.keys:['application/x-quickintosh-widget'];Drag.active:catalogDrag.active;Drag.dragType:Drag.Internal;Drag.supportedActions:Qt.CopyAction;Drag.mimeData:({'application/x-quickintosh-widget':modelData.key});Drag.onDragFinished:{x=0;y=0}}
       }
       Text{Layout.preferredWidth:62;text:modelData.label;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:10;elide:Text.ElideRight;horizontalAlignment:Text.AlignHCenter}
      }
     }
    }
   }
   ShelfButton{implicitWidth:38;implicitHeight:38;icon:'notch/x.svg';accessibleLabel:qsTr('Cancel customization');onClicked:{root.savedSlots.forEach((key,i)=>IslandConfig.setStyle('shelfSlot'+(i+1),key));root.savedWeights.forEach((value,i)=>IslandConfig.setStyle('shelfWeight'+(i+1),value));ShelfState.editing=false}}
   ShelfButton{implicitWidth:38;implicitHeight:38;icon:'notch/check.svg';selected:true;selectedColor:'#0a84ff';accessibleLabel:qsTr('Finish customization');onClicked:ShelfState.editing=false}
  }
 }
 ShelfButton{id:optionsButton;objectName:'home-options';visible:!ShelfState.editing;anchors.right:parent.right;anchors.top:parent.top;implicitWidth:26;implicitHeight:26;opacity:.65;icon:'notch/more-horizontal.svg';accessibleLabel:qsTr('Home options');onClicked:menu.toggleAt(optionsButton,optionsButton.width-menu.width,optionsButton.height+4)}
 ShelfMenu{id:menu;prewarm:true
  ShelfMenuItem{symbol:'notch/layout.svg';text:qsTr('Customize Home');onTriggered:ShelfState.editing=true}
  ShelfMenu{id:sourcesMenu;title:qsTr('Source')
   Instantiator{model:MprisState.players
    delegate:ShelfMenuItem{required property var modelData;symbol:'notch/music.svg';text:(MprisState.activePlayer===modelData ? '✓ ':'')+(modelData.identity || qsTr('Media player'));onTriggered:MprisState.selectPlayer(modelData)}
    onObjectAdded:(index,object)=>sourcesMenu.insertItem(index,object)
    onObjectRemoved:(index,object)=>sourcesMenu.removeItem(object)
   }
   ShelfMenuSeparator{}
   ShelfMenuItem{symbol:'notch/sliders.svg';text:qsTr('App volumes');onTriggered:ShelfState.reveal(10)}
  }
  ShelfMenuSeparator{}
  ShelfMenuItem{symbol:'notch/grid.svg';text:qsTr('Open Command Center');onTriggered:ShelfState.reveal(8)}
  ShelfMenuItem{symbol:'notch/settings.svg';text:qsTr('Open Settings');onTriggered:SettingsLauncher.open('')}
 }
}
