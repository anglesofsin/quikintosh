import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Widgets
import qs.services
import qs.rosa.reusables as MediaVisual
import qs.rosa.services
FloatingWindow {
 id:root;title:'Quickintosh Floating Player';visible:ShelfState.playerOpen && !IslandBus.locked;color:'transparent'
 readonly property string mode:IslandConfig.s('floatingPlayerSize')
 property string content:'player'
 readonly property bool mini:mode==='mini'
 implicitWidth:mini ? 320:360
 implicitHeight:mini ? 244:content==='queue' ? 620:content==='lyrics' ? 600:mode==='expanded' ? 660:554
 MediaVisual.ArtTint{id:playerTint;source:MprisState.artUrl;fallback:'#2c276d'}
 minimumSize:Qt.size(300,230)
 onModeChanged:resizeSoon.restart()
 onContentChanged:resizeSoon.restart()
 onVisibleChanged:{if(!visible)ShelfState.playerOpen=false;else resizeSoon.restart()}
 Timer{id:resizeSoon;interval:60;onTriggered:if(root.visible)Quickshell.execDetached(['hyprctl','eval','for _,w in ipairs(hl.get_windows()) do if w.title=="Quickintosh Floating Player" then if not w.floating then hl.dispatch(hl.dsp.window.float({action="enable",window="address:"..w.address})) end;hl.dispatch(hl.dsp.window.resize({x='+root.implicitWidth+',y='+root.implicitHeight+',window="address:"..w.address})) end end'])}
 ClippingRectangle{anchors.fill:parent;radius:28;antialiasing:true;color:'#ee0b0b0d';layer.enabled:true;layer.samples:4
  Rectangle{anchors.fill:parent;gradient:Gradient{GradientStop{position:0;color:'transparent'}GradientStop{position:.42;color:'transparent'}GradientStop{position:1;color:Qt.rgba(playerTint.color.r*.45,playerTint.color.g*.45,playerTint.color.b*.45,.85)}}}
  ColumnLayout{anchors.fill:parent;anchors.margins:18;spacing:12
   RowLayout{Layout.fillWidth:true;spacing:6
    Item{Layout.fillWidth:true;implicitHeight:24;MouseArea{anchors.fill:parent;onPressed:root.startSystemMove()}}
    ShelfButton{id:sizeButton;flat:true;icon:'notch/more-horizontal.svg';accessibleLabel:qsTr('Player size');onClicked:sizeMenu.toggleAt(sizeButton,0,sizeButton.height)}
    ShelfMenu{id:sizeMenu
     ShelfMenuItem{text:qsTr('Mini');onTriggered:IslandConfig.setStyle('floatingPlayerSize','mini')}
     ShelfMenuItem{text:qsTr('Player');onTriggered:IslandConfig.setStyle('floatingPlayerSize','player')}
     ShelfMenuItem{text:qsTr('Expanded');onTriggered:IslandConfig.setStyle('floatingPlayerSize','expanded')}
    }
    ShelfButton{flat:true;icon:'notch/x.svg';accessibleLabel:qsTr('Close player');onClicked:ShelfState.playerOpen=false}
   }
   ShelfMedia{id:player;visible:root.content==='player';Layout.fillWidth:true;Layout.fillHeight:true;portrait:!root.mini;showPopout:false;inlineActions:true
    onOpenQueue:root.content='queue'
    onOpenLyrics:root.content='lyrics'
    onOpenOutput:root.content='outputs'
   }
   QueueShelf{inlineActions:true;onRequestLyrics:root.content='lyrics';onRequestOutput:root.content='outputs';visible:root.content==='queue';Layout.fillWidth:true;Layout.fillHeight:true;onCloseQueue:root.content='player'}
   ColumnLayout{visible:root.content==='lyrics';Layout.fillWidth:true;Layout.fillHeight:true;spacing:12
    ShelfButton{flat:true;icon:'notch/music.svg';text:qsTr('Now Playing');onClicked:root.content='player'}
    LyricsShelf{Layout.fillWidth:true;Layout.fillHeight:true}
   }
   ColumnLayout{visible:root.content==='outputs';Layout.fillWidth:true;Layout.fillHeight:true;spacing:12
    ShelfButton{flat:true;icon:'notch/music.svg';text:qsTr('Now Playing');onClicked:root.content='player'}
    AudioShelf{Layout.fillWidth:true;Layout.fillHeight:true}
   }
   RowLayout{visible:root.content==='player';Layout.fillWidth:true;spacing:12
    ShelfButton{objectName:'floating-lyrics-button';flat:true;icon:'notch/type.svg';accessibleLabel:qsTr('Lyrics');onClicked:root.content='lyrics'}
    Item{Layout.fillWidth:true}
    Text{Layout.fillWidth:true;horizontalAlignment:Text.AlignHCenter;text:MprisState.identity;elide:Text.ElideRight;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
    Item{Layout.fillWidth:true}
    ShelfButton{flat:true;icon:'notch/more-horizontal.svg';accessibleLabel:qsTr('Playback options');onClicked:options.toggleAt(this,0,height)}
    ShelfMenu{id:options
     ShelfMenuItem{text:qsTr('Shuffle');checkable:true;checked:MprisState.shuffle;enabled:MprisState.shuffleSupported;onTriggered:MprisState.toggleShuffle()}
     ShelfMenuItem{text:qsTr('Repeat');checkable:true;checked:MprisState.loopActive;enabled:MprisState.loopSupported;onTriggered:MprisState.cycleLoop()}
     ShelfMenuItem{text:qsTr('Playing Next');onTriggered:root.content='queue'}
     ShelfMenuItem{text:qsTr('Lyrics');onTriggered:root.content='lyrics'}
    }
   }
  }
 }
 Shortcut{sequence:'Escape';onActivated:{if(root.content!=='player')root.content='player';else ShelfState.playerOpen=false}}
}
