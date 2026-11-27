import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell
import Quickshell.Widgets
import qs.services
Item {
 id:root
 signal openLyrics()
 signal openSources()
 onOpenLyrics:ShelfState.reveal(9)
 onOpenSources:ShelfState.reveal(10)
 property bool portrait:false
 property bool showPopout:true
 property var demo:({})
 readonly property var sample:demo && demo.media ? demo.media:null
 readonly property string title:sample ? sample.title:MprisState.trackTitle
 readonly property string artist:sample ? sample.artist:MprisState.trackArtist
 readonly property string artwork:sample ? (sample.art || ''):MprisState.artUrl
 readonly property real duration:sample ? sample.length:MprisState.length
 readonly property real position:sample ? sample.progress*sample.length:MprisState.position
 readonly property bool hasVolume:!sample && !!MprisState.activePlayer && MprisState.activePlayer.volumeSupported && MprisState.activePlayer.canControl
 readonly property Item hero:portrait ? cover:smallCover
 readonly property var qaLayout:({width:width,height:height,portrait:portrait,coverWidth:cover.width,titleWidth:metadata.width,seekWidth:seek.width,transportWidth:transport.width,volume:hasVolume,title:title,titleElided:trackTitle.truncated,lyricsGap:lyricsBadge.x-(trackTitle.x+trackTitle.width),lyricsCenter:lyricsBadge.y+lyricsBadge.height/2,titleCenter:trackTitle.y+trackTitle.height/2})
 property bool held:false
 readonly property bool watching:visible && !!QsWindow.window && QsWindow.window.visible
 function syncWatch(){if(held!==watching){held=watching;MprisState.watchPosition(held)}}
 function timeText(value){const n=Math.max(0,Math.floor(value || 0));return Math.floor(n/60)+':'+String(n%60).padStart(2,'0')}
 onWatchingChanged:syncWatch()
 Component.onCompleted:syncWatch()
 Component.onDestruction:if(held)MprisState.watchPosition(false)
 MouseArea{anchors.fill:parent;acceptedButtons:Qt.RightButton;onClicked:event=>contextMenu.toggleAt(root,event.x,event.y)}
 ShelfMenu{id:contextMenu
  ShelfMenuItem{symbol:'notch/list.svg';text:qsTr('Playing Next');onTriggered:ShelfState.openDetail('queue')}
  ShelfMenuItem{symbol:'notch/type.svg';text:qsTr('Lyrics');onTriggered:root.openLyrics()}
  ShelfMenuItem{symbol:'notch/layout.svg';text:qsTr('Customize Home');onTriggered:{ShelfState.reveal(0);ShelfState.editing=true}}
  ShelfMenu{id:sourcesMenu;title:qsTr('Source')
   Instantiator{model:MprisState.players
    delegate:ShelfMenuItem{required property var modelData;symbol:'notch/music.svg';text:(MprisState.activePlayer===modelData ? '✓ ':'')+(modelData.identity || qsTr('Media player'));onTriggered:MprisState.selectPlayer(modelData)}
    onObjectAdded:(index,object)=>sourcesMenu.insertItem(index,object)
    onObjectRemoved:(index,object)=>sourcesMenu.removeItem(object)
   }
   ShelfMenuSeparator{}
   ShelfMenuItem{symbol:'notch/sliders.svg';text:qsTr('App volumes');onTriggered:ShelfState.reveal(10)}
  }
  ShelfMenuItem{symbol:'notch/list.svg';text:qsTr('Lyrics');onTriggered:root.openLyrics()}
  ShelfMenuSeparator{}
  ShelfMenuItem{symbol:'notch/grid.svg';text:qsTr('Open Command Center');onTriggered:ShelfState.reveal(8)}
  ShelfMenuItem{symbol:'notch/settings.svg';text:qsTr('Open Settings');onTriggered:SettingsLauncher.open('')}
 }
 ColumnLayout {
  anchors.fill:parent
  spacing:root.portrait ? 16:root.height<170 ? 4:8
  ClippingRectangle {
   id:cover
   Layout.alignment:Qt.AlignHCenter
   Layout.fillWidth:root.portrait
   Layout.preferredHeight:root.portrait ? Math.min(root.width,Math.max(80,root.height-228)):0
   visible:root.portrait
   radius:20;color:'#151517'
   Image{anchors.fill:parent;source:root.artwork;sourceSize:Qt.size(700,700);fillMode:Image.PreserveAspectCrop;asynchronous:true;mipmap:true}
   ShelfIcon{anchors.centerIn:parent;visible:!root.artwork;size:48;icon:'notch/music.svg';color:ShelfStyle.secondary}
  }
  RowLayout {
   Layout.fillWidth:true;Layout.maximumHeight:root.portrait ? Infinity:smallCover.width;spacing:14
   ClippingRectangle {
    id:smallCover
    Layout.preferredWidth:root.height<170 ? 44:68
    Layout.preferredHeight:width
    visible:!root.portrait;radius:14;color:'#151517'
    Image{anchors.fill:parent;source:root.artwork;sourceSize:Qt.size(160,160);fillMode:Image.PreserveAspectCrop;asynchronous:true;mipmap:true}
    ShelfIcon{anchors.centerIn:parent;visible:!root.artwork;size:25;icon:'notch/music.svg';color:ShelfStyle.secondary}
   }
   ColumnLayout {
    id:metadata;Layout.fillWidth:true;spacing:4
    Item{
     Layout.fillWidth:true;implicitHeight:Math.max(trackTitle.implicitHeight,18)
     Text{id:trackTitle;width:Math.min(implicitWidth,Math.max(0,parent.width-(lyricsBadge.visible ? lyricsBadge.width+7:0)));anchors.verticalCenter:parent.verticalCenter;text:root.title || qsTr('Nothing playing');textFormat:Text.PlainText;font.family:ShelfStyle.displayFamily;font.pixelSize:root.portrait ? 23:18;font.weight:Font.DemiBold;color:ShelfStyle.primary;elide:Text.ElideRight;wrapMode:Text.NoWrap}
     Rectangle{id:lyricsBadge;visible:root.showPopout;x:trackTitle.x+trackTitle.width+7;anchors.verticalCenter:trackTitle.verticalCenter;width:16;height:18;radius:4;color:'#ededf0'
      Text{anchors.fill:parent;leftPadding:1;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;text:'L';font.family:ShelfStyle.textFamily;font.pixelSize:11;font.weight:Font.Bold;color:'#27272a'}
      Accessible.role:Accessible.Button;Accessible.name:qsTr('Lyrics')
      MouseArea{anchors.fill:parent;onClicked:root.openLyrics()}
     }
    }
    Text{Layout.fillWidth:true;text:root.artist || (root.sample ? '':MprisState.identity);textFormat:Text.PlainText;font.family:ShelfStyle.displayFamily;font.pixelSize:16;font.weight:Font.Medium;color:'#b5b5bb';elide:Text.ElideRight}
   }
   ShelfAudioMeter{visible:!root.portrait;Layout.preferredWidth:34;Layout.preferredHeight:28}
  }
  Item{visible:!root.portrait;Layout.fillHeight:true;Layout.minimumHeight:12}
  RowLayout {
   Layout.fillWidth:true;Layout.maximumHeight:20;spacing:10
   Text{text:root.timeText(root.position);font.family:ShelfStyle.textFamily;font.pixelSize:13;font.weight:Font.Medium;font.features:({tnum:1});color:'#b5b5bb'}
   Slider {
    id:seek;Layout.fillWidth:true;implicitHeight:20;from:0;to:Math.max(1,root.duration);value:root.position;enabled:!root.sample && MprisState.canSeek
    Accessible.name:qsTr('Playback position')
    property bool holding:false
    onPressedChanged:{if(holding!==pressed){holding=pressed;ShelfState.interaction(holding)}}
    Component.onDestruction:if(holding)ShelfState.interaction(false)
    onMoved:MprisState.seek(value)
    background:Rectangle{y:(seek.height-height)/2;width:seek.width;height:6;radius:3;color:'#36ffffff';Rectangle{width:parent.width*seek.visualPosition;height:parent.height;radius:parent.radius;color:'#e6ffffff'}}
    handle:Rectangle{visible:seek.pressed;width:10;height:10;radius:5;color:'white';x:seek.visualPosition*(seek.width-width);y:(seek.height-height)/2}
   }
   Text{text:root.duration>0 ? '−'+root.timeText(root.duration-root.position):'—:—';font.family:ShelfStyle.textFamily;font.pixelSize:13;font.weight:Font.Medium;font.features:({tnum:1});color:'#b5b5bb'}
  }
  RowLayout {
   id:transport;Layout.fillWidth:true;Layout.maximumHeight:Layout.preferredHeight;Layout.preferredHeight:root.portrait ? 54:root.height<170 ? 32:40;spacing:22
   ShelfButton{visible:root.showPopout;flat:true;icon:'notch/list.svg';iconSize:26;accessibleLabel:qsTr('Playing Next');onClicked:ShelfState.openDetail('queue')}
   Item{Layout.fillWidth:true}
   Repeater {
    model:[{icon:'backward',label:qsTr('Previous track'),enabled:MprisState.canGoPrevious},{icon:MprisState.isPlaying ? 'pause':'play',label:MprisState.isPlaying ? qsTr('Pause'):qsTr('Play'),enabled:MprisState.canTogglePlaying},{icon:'forward',label:qsTr('Next track'),enabled:MprisState.canGoNext}]
    delegate:Item {
     required property var modelData;required property int index
     Layout.preferredWidth:48;Layout.fillHeight:true;enabled:modelData.enabled && !root.sample;opacity:enabled ? 1:.35;activeFocusOnTab:true
     function activate(){if(index===0)MprisState.previous();else if(index===1)MprisState.togglePlaying();else MprisState.next()}
     Keys.onReturnPressed:activate();Keys.onSpacePressed:activate()
     Accessible.role:Accessible.Button;Accessible.name:modelData.label;Accessible.onPressAction:activate()
     ShelfIcon{anchors.centerIn:parent;size:index===1 ? (root.portrait ? 40:30):(root.portrait ? 36:30);icon:modelData.icon+'.png'}
     Rectangle{anchors.fill:parent;radius:12;color:mouse.pressed ? '#18ffffff':'transparent';border.width:parent.activeFocus ? 1:0;border.color:'#70ffffff'}
     MouseArea{id:mouse;anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:parent.activate()}
    }
   }
   Item{Layout.fillWidth:true}
   ShelfButton{visible:root.showPopout;flat:true;icon:'laptop.png';iconSize:28;foreground:ShelfStyle.secondary;accessibleLabel:qsTr('Floating player');onClicked:ShelfState.playerOpen=true}
  }
  RowLayout {
   visible:root.hasVolume && (root.portrait || root.height>=210);Layout.fillWidth:true;spacing:10
   ShelfIcon{size:14;Layout.preferredWidth:14;icon:'notch/volume-1.svg';color:ShelfStyle.secondary}
   ShelfSlider{Layout.fillWidth:true;from:0;to:1;value:root.hasVolume ? MprisState.activePlayer.volume:0;Accessible.name:qsTr('Player volume');onMoved:if(root.hasVolume)MprisState.activePlayer.volume=value}
   ShelfIcon{size:18;Layout.preferredWidth:18;icon:'notch/volume-2.svg';color:ShelfStyle.secondary}
  }
 }
}
