import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
Item{
 id:root
 property var look:null
 property string size:'m'
 property var widgetData:null
 property bool isSnapshot:false
 property bool desktopWidget:false
 readonly property bool fullBleed:true
 readonly property bool preview:widgetData?.id==='preview'
 readonly property bool watching:desktopWidget && !isSnapshot && visible && !CreativeMedia.locked && !preview && (widgetData?.lyricsEnabled ?? true)
 property bool held:false
 property bool heldRemote:false
 property bool heldLocal:false
 property var localLines:[]
 readonly property var lines:widgetData?.lyricsFile ? (isSnapshot ? CreativeMedia.lyrics[widgetData.lyricsFile] || []:localLines):LyricsState.lines
 readonly property bool synced:widgetData?.lyricsFile ? lines.length>0:LyricsState.synced
 readonly property real position:MprisState.position+(widgetData?.lyricsOffset ?? 0)
 readonly property int lineIndex:{let found=-1;if(synced)for(let i=0;i<lines.length;i++){if(lines[i].t<=position+.12)found=i;else break}return found}
 readonly property string layout:widgetData?.variant || 'stacked'
 readonly property color ink:widgetData?.textColorMode==='custom' ? widgetData.textColor || '#fff':widgetData?.textColorMode==='accent' ? Theme.accent:look?.primary || Theme.textPrimary
 readonly property string current:preview ? 'Your favorite songs, right here.':widgetData?.lyricsEnabled===false ? 'Lyrics paused':!MprisState.hasPlayer ? 'Play a song to see its lyrics':!synced ? (lines.length ? lines[0].text:LyricsState.status==='loading' ? 'Finding lyrics…':'No synchronized lyrics found'):lineIndex>=0 ? lines[lineIndex].text:'♪'
 function sync(){if(watching!==held){held=watching;MprisState.watchPosition(held)}const remote=watching && !widgetData?.lyricsFile;if(remote!==heldRemote){heldRemote=remote;LyricsState.watch(remote)}const local=watching && !!widgetData?.lyricsFile;if(local!==heldLocal){heldLocal=local;MprisState.fastWatchers=Math.max(0,MprisState.fastWatchers+(local ? 1:-1))}}
 onWidgetDataChanged:sync()
 onWatchingChanged:sync()
 Component.onCompleted:sync()
 Component.onDestruction:{if(heldRemote)LyricsState.watch(false);if(held)MprisState.watchPosition(false);if(heldLocal)MprisState.fastWatchers=Math.max(0,MprisState.fastWatchers-1)}
 FileView{id:lrc;path:!root.isSnapshot ? root.widgetData?.lyricsFile || '':'';onLoaded:{root.localLines=LyricsState.parseLrc(text()).slice(0,20000);CreativeMedia.lrc(root.widgetData?.lyricsFile,root.localLines)}
onLoadFailed:root.localLines=[]}
 ColumnLayout{
  anchors.fill:parent;anchors.margins:16;spacing:6
  Text{visible:root.widgetData?.lyricsTrack!==false;Layout.fillWidth:true;text:root.preview ? 'LIVE LYRICS':MprisState.trackTitle;color:root.ink;opacity:.6;font.pixelSize:11;font.weight:Font.DemiBold;elide:Text.ElideRight;horizontalAlignment:Text.AlignHCenter;textFormat:Text.PlainText}
  Text{visible:root.layout==='stacked' && (root.preview || root.synced && root.lineIndex>0);Layout.fillWidth:true;text:root.preview ? 'A moment before':root.lines[root.lineIndex-1]?.text || '';color:root.ink;opacity:.3;font.family:root.widgetData?.textFont || 'SF Pro Display';font.pixelSize:Math.max(11,(root.widgetData?.textSize || 28)*.65);horizontalAlignment:Text.AlignHCenter;wrapMode:Text.WordWrap;maximumLineCount:2;elide:Text.ElideRight;textFormat:Text.PlainText}
  CreativeText{Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumHeight:32;value:root.current;options:Object.assign({textSize:28,textAnimation:'fade'},root.widgetData || {});ink:root.ink;isSnapshot:root.isSnapshot;animationEnabled:root.watching}
  Rectangle{
   visible:root.layout==='karaoke' && (root.preview || root.synced && root.lineIndex>=0);Layout.fillWidth:true;height:3;radius:2;color:Qt.rgba(root.ink.r,root.ink.g,root.ink.b,.12)
   Rectangle{height:parent.height;radius:2;color:root.ink;width:root.preview ? parent.width*.55:parent.width*Math.max(0,Math.min(1,(root.position-(root.lines[root.lineIndex]?.t || 0))/Math.max(.1,(root.lines[root.lineIndex+1]?.t || MprisState.length)-(root.lines[root.lineIndex]?.t || 0))))}
  }
  Text{visible:root.layout==='stacked' && (root.preview || root.synced && root.lineIndex+1<root.lines.length);Layout.fillWidth:true;text:root.preview ? 'Another verse ahead':root.lines[root.lineIndex+1]?.text || '';color:root.ink;opacity:.3;font.family:root.widgetData?.textFont || 'SF Pro Display';font.pixelSize:Math.max(11,(root.widgetData?.textSize || 28)*.65);horizontalAlignment:Text.AlignHCenter;wrapMode:Text.WordWrap;maximumLineCount:2;elide:Text.ElideRight;textFormat:Text.PlainText}
  Text{visible:!root.synced && !!root.lines.length;Layout.fillWidth:true;text:'Lyrics without timestamps';color:root.ink;opacity:.45;font.pixelSize:10;horizontalAlignment:Text.AlignHCenter}
 }
}
