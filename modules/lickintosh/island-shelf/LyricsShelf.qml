import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import qs.rosa.services
import Quickshell
import qs.services
Item {
 id:root
 readonly property int lineIndex:{let index=-1;if(LyricsState.synced)for(let i=0;i<LyricsState.lines.length;i++){if(LyricsState.lines[i].t<=MprisState.position+.1)index=i;else break}return index}
 onLineIndexChanged:if(lineIndex>=0)lines.positionViewAtIndex(lineIndex,ListView.Center)
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:MprisState.trackTitle || qsTr('Lyrics');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold;elide:Text.ElideRight}
   Text{text:MprisState.trackArtist;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:12}
  }
  ListView{id:lines;reuseItems:true;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:16;model:LyricsState.lines;boundsBehavior:Flickable.StopAtBounds
   highlightMoveDuration:220
   delegate:Text{required property var modelData;required property int index;width:lines.width;text:modelData.text;textFormat:Text.PlainText;wrapMode:Text.WordWrap;horizontalAlignment:Text.AlignLeft;font.family:ShelfStyle.displayFamily;font.pixelSize:28;font.weight:Font.DemiBold;color:!LyricsState.synced || root.lineIndex===index ? ShelfStyle.primary:'#88888e';opacity:!LyricsState.synced || root.lineIndex===index ? 1:.5
    TapHandler{enabled:LyricsState.synced && MprisState.canSeek;onTapped:MprisState.seek(modelData.t)}
   }
   Text{anchors.centerIn:parent;visible:!LyricsState.lines.length && !IslandConfig.s('shelfLyricsBlank');text:LyricsState.status==='loading' ? qsTr('Finding lyrics…'):qsTr('No lyrics available');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:14}
  }
 }
 property bool held:false
 readonly property bool watching:visible && !!QsWindow.window && QsWindow.window.visible
 function syncWatch(){if(held!==watching){held=watching;LyricsState.watch(held);MprisState.watchPosition(held)}}
 onWatchingChanged:syncWatch()
 Component.onCompleted:syncWatch()
 Component.onDestruction:if(held){LyricsState.watch(false);MprisState.watchPosition(false)}
}
