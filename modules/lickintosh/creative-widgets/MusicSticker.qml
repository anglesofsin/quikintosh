import QtQuick
import QtQuick.Layouts
import QtMultimedia
import Quickshell
import qs.services
import qs.components
Item{
 id:root
 property var look:null
 property string size:'m'
 property var widgetData:null
 property bool isSnapshot:false
 property bool desktopWidget:false
 readonly property bool fullBleed:true
 readonly property bool showCover:widgetData?.musicShowCover!==false
 readonly property bool disc:widgetData?.variant==='disc'
 readonly property bool preview:widgetData?.id==='preview'
 property bool userPaused:false
 property bool userStarted:false
 readonly property bool allowed:desktopWidget && !isSnapshot && !preview && CreativeMedia.desktopActive && (widgetData?.musicRespectAudio===false || CreativeMedia.canPlayAudio) && visible && !userPaused && ((widgetData?.musicAutoPlay ?? true) || userStarted)
 readonly property color ink:widgetData?.musicColorMode==='custom' ? widgetData.musicColor || '#fff':widgetData?.musicColorMode==='accent' ? Theme.accent:look?.primary || Theme.textPrimary
 readonly property string playbackError:engine.item?.error || ''
 readonly property bool actuallyPlaying:engine.item?.playbackState===MediaPlayer.PlayingState
 onAudioUrlChanged:{userPaused=false;userStarted=false}
 readonly property string title:widgetData?.musicTitle || (widgetData?.audioFile ? String(widgetData.audioFile).split('/').pop().replace(/\.[^.]+$/,''):'Your soundtrack')
 readonly property string artist:widgetData?.musicArtist || 'Choose an audio file'
 readonly property string coverPath:widgetData?.musicCover || ''
 readonly property url audioUrl:{const p=String(widgetData?.audioFile || '');return p.startsWith('file:') ? p:p ? 'file://'+p.split('/').map(encodeURIComponent).join('/'):''}
 Loader{
  id:engine;active:root.desktopWidget && !root.isSnapshot && !!root.audioUrl
  sourceComponent:Item{
   property alias duration:player.duration
   property alias position:player.position
   property alias playbackState:player.playbackState
   property alias error:player.errorString
   MediaPlayer{
   id:player;source:root.audioUrl;loops:root.widgetData?.musicLoop===false ? 1:MediaPlayer.Infinite
   audioOutput:AudioOutput{volume:Math.max(0,Math.min(1,root.widgetData?.musicVolume ?? .35));muted:!!root.widgetData?.musicMuted || !root.allowed}
   function sync(){if(root.allowed)play();else pause()}
   Component.onCompleted:sync()
   onMediaStatusChanged:{if(mediaStatus===MediaPlayer.LoadedMedia)sync();if(mediaStatus===MediaPlayer.EndOfMedia)root.userPaused=true}
   }
   Connections{target:root;function onAllowedChanged(){player.sync()}}
  }
 }
 ColumnLayout{
  anchors.fill:parent;anchors.margins:root.disc ? 12:16;spacing:8
  Item{
   id:art;visible:root.showCover;Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumHeight:40
   readonly property real diameter:Math.min(width,height)
   CFClippingRect{
    id:cover;anchors.centerIn:parent;width:art.diameter;height:width;radius:root.disc ? width/2:Math.min(16,width*.12);color:Qt.tint(Theme.accent,'#99404050')
    RotationAnimator on rotation{from:0;to:360;duration:16000;loops:Animation.Infinite;running:root.disc && root.allowed && root.actuallyPlaying && !SettingsPreferences.accessibility.reduceMotion}
    Image{anchors.fill:parent;source:root.coverPath.startsWith('file:') ? root.coverPath:root.coverPath ? 'file://'+root.coverPath.split('/').map(encodeURIComponent).join('/'):'';fillMode:Image.PreserveAspectCrop;asynchronous:true;smooth:true;mipmap:true;sourceSize:Qt.size(500,500)}
    Text{anchors.centerIn:parent;visible:!root.coverPath;text:'♫';color:root.ink;font.pixelSize:Math.max(28,parent.width*.36);font.family:'SF Pro Rounded';opacity:.85}
    Rectangle{anchors.centerIn:parent;visible:root.disc;width:parent.width*.18;height:width;radius:width/2;color:Theme.fillControl;border.width:1;border.color:root.ink;opacity:.9}
    Rectangle{anchors.centerIn:parent;visible:root.disc;width:parent.width*.035;height:width;radius:width/2;color:'#16161a'}
   }
  }
  Item{visible:!root.showCover;Layout.fillHeight:true}
  Text{Layout.fillWidth:true;text:root.title;color:root.ink;font.family:root.widgetData?.musicFont || 'SF Pro Display';font.pixelSize:root.widgetData?.musicFontSize || Math.max(14,Math.min(24,root.width*.07));font.weight:Font.Bold;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight;textFormat:Text.PlainText}
  Text{Layout.fillWidth:true;text:root.artist;color:root.ink;opacity:.7;font.pixelSize:12;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight;textFormat:Text.PlainText}
  Text{visible:root.height>=230 && !!root.widgetData?.musicDescription;Layout.fillWidth:true;text:root.widgetData?.musicDescription || '';color:root.ink;opacity:.6;font.pixelSize:11;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.WordWrap;maximumLineCount:2;elide:Text.ElideRight;textFormat:Text.PlainText}
  Text{visible:!!root.playbackError;Layout.fillWidth:true;text:'Unable to play this audio file';color:root.ink;font.pixelSize:11;wrapMode:Text.WordWrap;horizontalAlignment:Text.AlignHCenter}
  Item{visible:!root.showCover;Layout.fillHeight:true}
  RowLayout{
   visible:root.widgetData?.musicControls!==false;Layout.fillWidth:true;spacing:10
   Rectangle{Layout.fillWidth:true;height:3;radius:2;color:Qt.rgba(root.ink.r,root.ink.g,root.ink.b,.16)
    Rectangle{width:parent.width*(engine.item?.duration>0 ? engine.item.position/engine.item.duration:0);height:3;radius:2;color:root.ink}
   }
   Text{text:root.actuallyPlaying ? 'Ⅱ':'▶';color:root.ink;font.pixelSize:17;Layout.preferredWidth:24;horizontalAlignment:Text.AlignHCenter
    TapHandler{enabled:root.desktopWidget && !root.isSnapshot;onTapped:{DesktopFiles.desktopFocused=true;if(root.actuallyPlaying)root.userPaused=true;else{root.userStarted=true;root.userPaused=false}}}
   }
  }
 }
}
