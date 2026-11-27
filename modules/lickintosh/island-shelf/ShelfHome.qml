import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import Quickshell.Widgets
import qs.services
import qs.components
import qs.rosa.services
import qs.ui.topbar.notch.dashboard
Flickable {
 id:root;clip:true;contentWidth:Math.max(width,slots.filter(x=>x!=="none").length*220);contentHeight:height;boundsBehavior:Flickable.StopAtBounds
 signal openPage(int page)
 property var slots:[IslandConfig.s('shelfSlot1'),IslandConfig.s('shelfSlot2'),IslandConfig.s('shelfSlot3'),IslandConfig.s('shelfSlot4')]
 RowLayout {
  width:root.contentWidth;height:root.height;spacing:24
  Repeater {
   model:root.slots
   delegate:Item {
    id:slot;objectName:'home-slot-'+index;required property string modelData;required property int index
    visible:modelData!=='none'
    Layout.fillWidth:true;Layout.fillHeight:true
    Layout.horizontalStretchFactor:IslandConfig.s('shelfWeight'+(index+1))*(modelData==='media' ? 105:modelData==='weather' ? 95:100)
    Layout.minimumWidth:140
    Rectangle{anchors.fill:parent;radius:20;color:IslandConfig.s('shelfWidgetCards') ? '#151518':'transparent';border.color:IslandConfig.s('shelfWidgetCards') ? '#25252b':'transparent'}
    Rectangle{anchors.fill:parent;anchors.margins:-1;radius:20;color:'transparent';border.width:1;border.color:'#70ffffff';visible:ShelfState.editing}
    Loader {anchors.fill:parent;anchors.margins:IslandConfig.s('shelfWidgetCards') ? 14:0;sourceComponent:({media:music,calendar:calendar,weather:weather,focus:focusComponent,notes:notes,performance:stats,files:files,clipboard:clipboardWidget,audio:audioWidget,awake:awakeWidget,storage:storageWidget,camera:cameraWidget,transcribe:transcribeWidget,terminal:terminalWidget,breather:breatherWidget,vault:vaultWidget,developer:developerWidget,teleprompter:teleprompterWidget,notifications:notificationsWidget})[slot.modelData] || music}
    DropArea{anchors.fill:parent;keys:['application/x-quickintosh-shelf-slot','application/x-quickintosh-widget'];onDropped:drop=>{
     const key=drop.source?.widgetKey || drop.getDataAsString('application/x-quickintosh-widget');if(key){IslandConfig.setStyle('shelfSlot'+(slot.index+1),key);drop.acceptProposedAction();return}
     const from=drop.source?.slotIndex!==undefined ? drop.source.slotIndex:Number(drop.getDataAsString('application/x-quickintosh-shelf-slot'));const to=slot.index
     if(Number.isInteger(from) && from>=0 && from<4 && from!==to){const old=IslandConfig.s('shelfSlot'+(to+1));IslandConfig.setStyle('shelfSlot'+(to+1),IslandConfig.s('shelfSlot'+(from+1)));IslandConfig.setStyle('shelfSlot'+(from+1),old)}drop.acceptProposedAction()
    }}
    ShelfButton{visible:ShelfState.editing;anchors.right:parent.right;anchors.top:parent.top;implicitWidth:24;implicitHeight:24;icon:'notch/minus.svg';onClicked:IslandConfig.setStyle('shelfSlot'+(slot.index+1),'none')}
    Rectangle{visible:ShelfState.editing;anchors.horizontalCenter:parent.horizontalCenter;anchors.top:parent.top;width:52;height:18;radius:9;color:'#44444b';z:20
     Text{anchors.centerIn:parent;text:'•••';color:'white';font.pixelSize:14}
     MouseArea{id:reorderMouse;objectName:'reorder-'+slot.index;anchors.fill:parent;drag.target:reorderProxy;onReleased:reorderProxy.Drag.drop();cursorShape:Qt.OpenHandCursor}
     Item{id:reorderProxy;property int slotIndex:slot.index;width:1;height:1;Drag.source:reorderProxy;Drag.keys:['application/x-quickintosh-shelf-slot'];Drag.active:reorderMouse.drag.active;Drag.dragType:Drag.Internal;Drag.supportedActions:Qt.MoveAction;Drag.proposedAction:Qt.MoveAction;Drag.mimeData:({'application/x-quickintosh-shelf-slot':String(slot.index)});Drag.onDragFinished:{x=0;y=0}}
    }
    Rectangle{visible:ShelfState.editing;anchors.right:parent.right;anchors.bottom:parent.bottom;width:16;height:48;radius:8;color:'#44444b';z:20
     property real startX:0;property int original:1
     MouseArea{anchors.fill:parent;cursorShape:Qt.SizeHorCursor;onPressed:e=>{parent.startX=mapToGlobal(e.x,e.y).x;parent.original=IslandConfig.s('shelfWeight'+(slot.index+1))}
onPositionChanged:e=>{if(pressed){const change=Math.round((mapToGlobal(e.x,e.y).x-parent.startX)/100);IslandConfig.setStyle('shelfWeight'+(slot.index+1),Math.max(1,Math.min(3,parent.original+change)))}}}
    }
    Rectangle {visible:slot.index>0 && !IslandConfig.s('shelfWidgetCards');anchors.left:parent.left;anchors.leftMargin:-12;width:1;height:parent.height;color:'#242426'}
   }
  }
 }
 Component{id:transcribeWidget;TranscribeShelf{}}
 Component{id:terminalWidget;TerminalShelf{}}
 Component{id:breatherWidget;BreatherShelf{}}
 Component{id:vaultWidget;VaultShelf{}}
 Component{id:developerWidget;DeveloperTools{}}
 Component{id:teleprompterWidget;Teleprompter{}}
 Component{id:music;ShelfMedia{onOpenLyrics:root.openPage(9);onOpenSources:root.openPage(10)}}
 Component{id:calendar;ShelfCalendar{}}
 Component{id:focusComponent;ShelfFocus{}}
 Component{id:notes;ShelfNotes{}}
 Component{id:stats;ShelfStats{}}
 Component{id:files;HomeUtility{kind:'files';onActivated:root.openPage(6)}}
 Component{id:clipboardWidget;HomeUtility{kind:'clipboard';onActivated:root.openPage(7)}}
 Component{id:audioWidget;AudioShelf{}}
 Component{id:awakeWidget;StayAwakeShelf{}}
 Component{id:storageWidget;HomeUtility{kind:'storage';onActivated:root.openPage(14)}}
 Component{id:cameraWidget;ShelfCamera{}}
 Component{id:notificationsWidget;ColumnLayout{ShelfIcon{size:28;icon:'notch/bell.svg'}Text{text:qsTr('Notifications');color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:15}ShelfButton{text:qsTr('Open notifications');onClicked:root.openPage(4)}}}
 Component{id:weather;ShelfWeather{onActivated:root.openPage(1)}}
 ColumnLayout{anchors.centerIn:parent;visible:root.slots.every(key=>key==='none');spacing:10
  Text{Layout.alignment:Qt.AlignHCenter;text:qsTr('Make this space yours');font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold;color:'white'}
  ShelfButton{Layout.alignment:Qt.AlignHCenter;text:qsTr('Add widgets');icon:'notch/plus.svg';onClicked:root.openPage(8)}
 }
 property bool held:false
 readonly property bool watching:slots.includes("media") && visible && !!QsWindow.window && QsWindow.window.visible
 function syncWatch(){if(held!==watching){held=watching;MprisState.watchPosition(held)}}
 onWatchingChanged:syncWatch()
 Component.onCompleted:syncWatch()
 Component.onDestruction:if(held)MprisState.watchPosition(false)
}
