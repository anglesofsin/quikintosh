import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import qs.services
import qs.components
import qs.rosa.services
import qs.ui.topbar.notch.dashboard
Flickable {
 id:root;clip:true;contentWidth:Math.max(width,slots.filter(x=>x!=="none").length*220);contentHeight:height;boundsBehavior:Flickable.StopAtBounds
 signal openPage(int page)
 property var slots:[IslandConfig.s('shelfSlot1'),IslandConfig.s('shelfSlot2'),IslandConfig.s('shelfSlot3'),IslandConfig.s('shelfSlot4')]
 RowLayout {
  width:root.contentWidth;height:root.height;spacing:18
  Repeater {
   model:root.slots
   delegate:Item {
    id:slot;required property string modelData;required property int index
    visible:modelData!=='none'
    Layout.fillWidth:true;Layout.fillHeight:true
    Layout.horizontalStretchFactor:IslandConfig.s('shelfWeight'+(index+1))
    Layout.minimumWidth:140
    Rectangle{anchors.fill:parent;anchors.margins:-4;radius:16;color:'transparent';border.width:1;border.color:Theme.accent;visible:ShelfState.editing}
    Loader {anchors.fill:parent;sourceComponent:({media:music,calendar:calendar,weather:weather,focus:focus,notes:notes,performance:stats,files:files})[slot.modelData] || music}
    DropArea{anchors.fill:parent;keys:['application/x-quickintosh-shelf-slot'];onDropped:drop=>{
     const from=Number(drop.getDataAsString('application/x-quickintosh-shelf-slot'));const to=slot.index
     if(Number.isInteger(from) && from>=0 && from<4 && from!==to){const old=IslandConfig.s('shelfSlot'+(to+1));IslandConfig.setStyle('shelfSlot'+(to+1),IslandConfig.s('shelfSlot'+(from+1)));IslandConfig.setStyle('shelfSlot'+(from+1),old)}drop.acceptProposedAction()
    }}
    Rectangle{visible:ShelfState.editing;anchors.horizontalCenter:parent.horizontalCenter;anchors.top:parent.top;width:52;height:18;radius:9;color:'#44444b';z:20
     Text{anchors.centerIn:parent;text:'•••';color:'white';font.pixelSize:13}
     MouseArea{id:reorderMouse;anchors.fill:parent;drag.target:reorderProxy;cursorShape:Qt.OpenHandCursor}
     Item{id:reorderProxy;width:1;height:1;Drag.active:reorderMouse.drag.active;Drag.dragType:Drag.Automatic;Drag.supportedActions:Qt.MoveAction;Drag.proposedAction:Qt.MoveAction;Drag.mimeData:({'application/x-quickintosh-shelf-slot':String(slot.index)});Drag.onDragFinished:{x=0;y=0}}
    }
    Rectangle{visible:ShelfState.editing;anchors.right:parent.right;anchors.bottom:parent.bottom;width:16;height:48;radius:8;color:'#44444b';z:20
     property real startX:0;property int original:1
     MouseArea{anchors.fill:parent;cursorShape:Qt.SizeHorCursor;onPressed:e=>{parent.startX=mapToGlobal(e.x,e.y).x;parent.original=IslandConfig.s('shelfWeight'+(slot.index+1))};onPositionChanged:e=>{if(pressed){const change=Math.round((mapToGlobal(e.x,e.y).x-parent.startX)/100);IslandConfig.setStyle('shelfWeight'+(slot.index+1),Math.max(1,Math.min(3,parent.original+change)))}}}
    }
    Rectangle {visible:slot.index>0;anchors.left:parent.left;anchors.leftMargin:-9;width:1;height:parent.height;color:'#242426'}
   }
  }
 }
 Component {id:music
  ColumnLayout {spacing:12
   RowLayout {spacing:12;Layout.fillWidth:true
    Rectangle {Layout.preferredWidth:64;Layout.preferredHeight:64;radius:13;color:'#222225';clip:true
     Image{anchors.fill:parent;source:MprisState.artUrl;fillMode:Image.PreserveAspectCrop;asynchronous:true}
     TintedIcon{anchors.centerIn:parent;size:28;visible:!MprisState.artUrl;source:Quickshell.shellPath('assets/icons_desktop/MacTahoe/actions/symbolic/music-note-symbolic.svg');tint:'#cfcfd3'}
    }
    ColumnLayout {Layout.fillWidth:true;spacing:4
     Text{Layout.fillWidth:true;text:MprisState.trackTitle || qsTr('Nothing playing');font.family:'SF Pro Display';font.pixelSize:15;font.weight:Font.DemiBold;color:'white';elide:Text.ElideRight}
     Text{Layout.fillWidth:true;text:MprisState.trackArtist || MprisState.identity;font.family:'SF Pro Text';font.pixelSize:12;color:'#99999e';elide:Text.ElideRight}
    }
   }
   Slider {id:seek;Layout.fillWidth:true;implicitHeight:16;from:0;to:Math.max(1,MprisState.length);value:MprisState.position;enabled:MprisState.canSeek;onMoved:MprisState.seek(value)
    background:Rectangle{y:seek.height/2-2;width:seek.width;height:4;radius:2;color:'#333336';Rectangle{height:4;radius:2;width:parent.width*seek.visualPosition;color:'#d9d9de'}}
    handle:Item{}
   }
   RowLayout {Layout.alignment:Qt.AlignHCenter;spacing:14
    CtrlButton{icon:'music/backward.svg';size:20;active:MprisState.canGoPrevious;onClicked:MprisState.previous()}
    CtrlButton{icon:MprisState.isPlaying ? 'music/pause.svg':'music/play.svg';size:25;active:MprisState.canTogglePlaying;onClicked:MprisState.togglePlaying()}
    CtrlButton{icon:'music/forward.svg';size:20;active:MprisState.canGoNext;onClicked:MprisState.next()}
    ShelfButton{text:qsTr('Lyrics');onClicked:root.openPage(9)}
    ShelfButton{icon:'notch/external-link.svg';onClicked:ShelfState.playerOpen=true}
   }
  }
 }
 Component{id:calendar;CalendarModule{}}
 Component{id:focus;FocusModule{}}
 Component{id:notes;NotesModule{}}
 Component{id:stats;ColumnLayout{spacing:12
  Text{text:qsTr('System');font.family:'SF Pro Display';font.pixelSize:17;font.weight:Font.DemiBold;color:'white'}
  PerformancePage{Layout.fillWidth:true;Layout.fillHeight:true}
 }}
 Component{id:files;ColumnLayout{spacing:12
  CFVI{Layout.alignment:Qt.AlignHCenter;size:36;icon:'notch/inbox.svg';color:'#c5c5cd'}
  Text{Layout.alignment:Qt.AlignHCenter;text:qsTr('%1 files in tray').arg(ShelfState.items.length);font.family:'SF Pro Text';font.pixelSize:14;color:'white'}
  ShelfButton{Layout.alignment:Qt.AlignHCenter;text:qsTr('Open tray');onClicked:root.openPage(6)}
 }}
 Component {id:weather
  Rectangle {radius:20;color:'#15171c'
   ColumnLayout {anchors.fill:parent;anchors.margins:16;spacing:7
    RowLayout{Layout.fillWidth:true
     ColumnLayout{Layout.fillWidth:true;spacing:3
      Text{Layout.fillWidth:true;text:IslandConfig.s('dashboardWeatherLocation') ? WeatherState.city:qsTr('Weather');font.family:'SF Pro Text';font.pixelSize:12;color:'#c4c4cc';elide:Text.ElideRight}
      Text{text:WeatherState.available ? Math.round(WeatherState.tempC)+'°':'—°';font.family:'SF Pro Display';font.pixelSize:36;font.weight:Font.Light;color:'white'}
     }
     Image{Layout.preferredWidth:52;Layout.preferredHeight:52;source:Quickshell.shellPath('rosa/overlays/assets/weather-'+(WeatherState.weatherCode>=95 ? 'storm':WeatherState.weatherCode>=51 ? 'rain':WeatherState.weatherCode>=3 ? 'clouds':WeatherState.weatherCode===2 ? 'partly':WeatherState.isDay ? 'sun':'night')+'.png');fillMode:Image.PreserveAspectFit;sourceSize:Qt.size(128,128)}
    }
    RowLayout {Layout.fillWidth:true
     Repeater {model:WeatherState.hourly.slice(0,4)
      delegate:ColumnLayout {required property var modelData;Layout.fillWidth:true;spacing:8
       Text{Layout.alignment:Qt.AlignHCenter;text:modelData.time ? String(modelData.time).slice(-5):'';font.family:'SF Pro Text';font.pixelSize:10;color:'#9999a0'}
       Text{Layout.alignment:Qt.AlignHCenter;text:Math.round(modelData.temp)+'°';font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold;color:'white'}
      }
     }
    }
    TapHandler{onTapped:root.openPage(1)}
   }
  }
 }
 property bool held:false
 readonly property bool watching:visible && !!QsWindow.window && QsWindow.window.visible
 function syncWatch(){if(held!==watching){held=watching;MprisState.watchPosition(held)}}
 onWatchingChanged:syncWatch()
 Component.onCompleted:syncWatch()
 Component.onDestruction:if(held)MprisState.watchPosition(false)
}
