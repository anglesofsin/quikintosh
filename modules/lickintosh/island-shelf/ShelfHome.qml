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
    id:slot;required property string modelData;required property int index
    visible:modelData!=='none'
    Layout.fillWidth:true;Layout.fillHeight:true
    Layout.horizontalStretchFactor:IslandConfig.s('shelfWeight'+(index+1))*(modelData==='media' ? 105:modelData==='weather' ? 95:100)
    Layout.minimumWidth:140
    Rectangle{anchors.fill:parent;radius:20;color:IslandConfig.s('shelfWidgetCards') ? '#151518':'transparent';border.color:IslandConfig.s('shelfWidgetCards') ? '#25252b':'transparent'}
    Rectangle{anchors.fill:parent;anchors.margins:-1;radius:20;color:'transparent';border.width:1;border.color:Theme.accent;visible:ShelfState.editing}
    Loader {anchors.fill:parent;anchors.margins:IslandConfig.s('shelfWidgetCards') ? 14:0;sourceComponent:({media:music,calendar:calendar,weather:weather,focus:focusComponent,notes:notes,performance:stats,files:files})[slot.modelData] || music}
    DropArea{anchors.fill:parent;keys:['application/x-quickintosh-shelf-slot'];onDropped:drop=>{
     const from=Number(drop.getDataAsString('application/x-quickintosh-shelf-slot'));const to=slot.index
     if(Number.isInteger(from) && from>=0 && from<4 && from!==to){const old=IslandConfig.s('shelfSlot'+(to+1));IslandConfig.setStyle('shelfSlot'+(to+1),IslandConfig.s('shelfSlot'+(from+1)));IslandConfig.setStyle('shelfSlot'+(from+1),old)}drop.acceptProposedAction()
    }}
    Rectangle{visible:ShelfState.editing;anchors.horizontalCenter:parent.horizontalCenter;anchors.top:parent.top;width:52;height:18;radius:9;color:'#44444b';z:20
     Text{anchors.centerIn:parent;text:'•••';color:'white';font.pixelSize:14}
     MouseArea{id:reorderMouse;anchors.fill:parent;drag.target:reorderProxy;cursorShape:Qt.OpenHandCursor}
     Item{id:reorderProxy;width:1;height:1;Drag.active:reorderMouse.drag.active;Drag.dragType:Drag.Automatic;Drag.supportedActions:Qt.MoveAction;Drag.proposedAction:Qt.MoveAction;Drag.mimeData:({'application/x-quickintosh-shelf-slot':String(slot.index)});Drag.onDragFinished:{x=0;y=0}}
    }
    Rectangle{visible:ShelfState.editing;anchors.right:parent.right;anchors.bottom:parent.bottom;width:16;height:48;radius:8;color:'#44444b';z:20
     property real startX:0;property int original:1
     MouseArea{anchors.fill:parent;cursorShape:Qt.SizeHorCursor;onPressed:e=>{parent.startX=mapToGlobal(e.x,e.y).x;parent.original=IslandConfig.s('shelfWeight'+(slot.index+1))};onPositionChanged:e=>{if(pressed){const change=Math.round((mapToGlobal(e.x,e.y).x-parent.startX)/100);IslandConfig.setStyle('shelfWeight'+(slot.index+1),Math.max(1,Math.min(3,parent.original+change)))}}}
    }
    Rectangle {visible:slot.index>0 && !IslandConfig.s('shelfWidgetCards');anchors.left:parent.left;anchors.leftMargin:-12;width:1;height:parent.height;color:'#242426'}
   }
  }
 }
 Component{id:music
  ColumnLayout{id:musicCard;spacing:12
   function timeText(seconds){const n=Math.max(0,Math.floor(seconds || 0));return Math.floor(n/60)+':'+String(n%60).padStart(2,'0')}
   RowLayout{Layout.fillWidth:true;spacing:14
    ClippingRectangle{Layout.preferredWidth:76;Layout.preferredHeight:76;radius:17;color:'#1c1c1e'
     Image{anchors.fill:parent;source:MprisState.artUrl;fillMode:Image.PreserveAspectCrop;asynchronous:true}
     ShelfIcon{anchors.centerIn:parent;size:30;visible:!MprisState.artUrl;icon:'notch/music.svg';color:ShelfStyle.secondary}
    }
    ColumnLayout{Layout.fillWidth:true;spacing:5
     Text{Layout.fillWidth:true;text:MprisState.trackTitle || qsTr('Nothing playing');textFormat:Text.PlainText;font.family:ShelfStyle.displayFamily;font.pixelSize:22;font.weight:Font.DemiBold;color:'white';elide:Text.ElideRight}
     Text{Layout.fillWidth:true;text:MprisState.trackArtist || MprisState.identity;textFormat:Text.PlainText;font.family:ShelfStyle.textFamily;font.pixelSize:18;color:'#a9a9ad';elide:Text.ElideRight}
    }
   }
   RowLayout{Layout.fillWidth:true;spacing:10
    Text{Layout.preferredWidth:34;text:musicCard.timeText(MprisState.position);color:'#99999f';font.family:ShelfStyle.textFamily;font.pixelSize:14}
    Slider{id:seek;Layout.fillWidth:true;implicitHeight:22;from:0;to:Math.max(1,MprisState.length);value:MprisState.position;enabled:MprisState.canSeek;onMoved:MprisState.seek(value)
     background:Rectangle{y:seek.height/2-7;width:seek.width;height:14;radius:7;color:'#29292e';Rectangle{height:parent.height;radius:7;width:parent.width*seek.visualPosition;color:'#c1c1c5'}}
     handle:Item{}
    }
    Text{Layout.preferredWidth:42;text:MprisState.length>0 ? '−'+musicCard.timeText(Math.max(0,MprisState.length-MprisState.position)):'—:—';horizontalAlignment:Text.AlignRight;color:'#99999f';font.family:ShelfStyle.textFamily;font.pixelSize:14}
   }
   ShelfPlayback{Layout.fillWidth:true}
  }
 }
 Component{id:calendar;ShelfCalendar{}}
 Component{id:focusComponent;ShelfFocus{}}
 Component{id:notes;ShelfNotes{}}
 Component{id:stats;ShelfStats{}}
 Component{id:files;ColumnLayout{spacing:12
  ShelfIcon{Layout.alignment:Qt.AlignHCenter;size:36;icon:'notch/inbox.svg';color:'#c5c5cd'}
  Text{Layout.alignment:Qt.AlignHCenter;text:qsTr('%1 files in tray').arg(ShelfState.items.length);font.family:ShelfStyle.textFamily;font.pixelSize:14;color:'white'}
  ShelfButton{Layout.alignment:Qt.AlignHCenter;text:qsTr('Open tray');onClicked:root.openPage(6)}
 }}
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
