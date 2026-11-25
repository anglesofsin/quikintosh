import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import Quickshell
import qs.services
import Quickshell.Io
FloatingWindow {
 id:window
 visible:QuickLookState.opened
 title:'Lickintosh Quick Look — '+(QuickLookState.data.name || '')
 onVisibleChanged:if(!visible && QuickLookState.opened)QuickLookState.close()
 color:'transparent';implicitWidth:880;implicitHeight:650;minimumSize:Qt.size(460,320)
 property bool glassReady: true
 readonly property rect glassRegion: Qt.rect(QuickLookState.geometry.x || 0, QuickLookState.geometry.y || 0, window.width, window.height)
 readonly property bool videoFrames:window.kind==='video' && video.contentRect.width>0 && video.contentRect.height>0
 property real zoom:1
 property real angle:0
 property bool indexSheet:false
 property bool imageDragging:false
 readonly property color foreground:Theme.isLight ? '#202127':'#f6f7fb'
 readonly property color secondary:Theme.isLight ? '#535761':'#b9bbc5'
 property var retainedInfo: ({})
 property bool presented: false
 readonly property var info:QuickLookState.opened ? QuickLookState.data : retainedInfo
 readonly property int motionDuration: ShellMotion.fade()
 Timer { id:closeMotion; interval:Math.max(1,window.motionDuration); onTriggered:window.retainedInfo=({}) }
 Connections {
  target: QuickLookState
  function onDataChanged() { if (QuickLookState.opened) window.retainedInfo=QuickLookState.data }
  function onOpenedChanged() {
   if (QuickLookState.opened) {
    closeMotion.stop()
    Qt.callLater(()=>{ if (QuickLookState.opened) window.presented=true })
   } else {
    window.presented=false
    if (window.motionDuration>0) closeMotion.restart()
   }
  }
 }
 readonly property string kind:info.kind || ''
 readonly property bool raster:['image','pdf'].includes(kind)
 Shortcut{sequences:['Escape','Space'];enabled:QuickLookState.opened;context:Qt.ApplicationShortcut;onActivated:window.closePreview()}
 function closePreview(){QuickLookState.close()}
 function timeText(ms){const s=Math.floor(ms/1000);return (s>=3600 ? Math.floor(s/3600)+':':'')+String(Math.floor(s/60)%60).padStart(2,'0')+':'+String(s%60).padStart(2,'0')}
 function sizeText(n){return n>1048576 ? (n/1048576).toFixed(1)+' MB':n>1024 ? (n/1024).toFixed(1)+' KB':n+' B'}
 Connections{target:QuickLookState;function onActivated(){Qt.callLater(()=>keys.forceActiveFocus())}function onDataChanged(){window.zoom=1;window.angle=0}function onOpenedChanged(){if(QuickLookState.opened){window.indexSheet=false;Qt.callLater(()=>keys.forceActiveFocus())}else{player.stop();trimPopup.close();shareMenu.close();window.fullscreen=false}}}
 Process {
  command: ['hyprctl', '-j', 'hyprglass', 'status']
  running: true
  stdout: StdioCollector {
   onStreamFinished: {
    try { window.glassReady = JSON.parse(text).versionCheck === 'match' }
    catch (_) { window.glassReady = false }
   }
  }
 }
 FocusScope{
  id:keys;anchors.fill:parent;focus:true
  enabled:QuickLookState.opened
  opacity:1
  scale:1
  transformOrigin:Item.Center
  Keys.onPressed:event=>{
   if(event.key===Qt.Key_Escape){window.closePreview();event.accepted=true}
   else if(event.key===Qt.Key_Space && !(event.modifiers & Qt.ControlModifier)){window.closePreview();event.accepted=true}
   else if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter){QuickLookState.openDefault();event.accepted=true}
   else if(event.key===Qt.Key_Left || event.key===Qt.Key_Up || event.key===Qt.Key_Right || event.key===Qt.Key_Down){QuickLookState.navigate(event.key===Qt.Key_Up ? 2:event.key===Qt.Key_Down ? 3:event.key===Qt.Key_Left ? 4:5);event.accepted=true}
   else if(event.key===Qt.Key_Plus || event.key===Qt.Key_Equal){window.zoom=Math.min(5,window.zoom+.25);event.accepted=true}
   else if(event.key===Qt.Key_Minus){window.zoom=Math.max(.25,window.zoom-.25);event.accepted=true}
  }
  Rectangle{
   id:surface;anchors.fill:parent;anchors.margins:1;radius:20
   color:window.glassReady && !Theme.plainSurfaces ? (Theme.isLight ? '#70ffffff' : '#58202027') : (Theme.isLight ? '#fafafa' : '#22232b')
   opacity:window.imageDragging ? .4 : 1
   Rectangle{anchors.fill:parent;anchors.margins:1;radius:19;color:Theme.isLight ? '#10ffffff':'#35000000'}
   Item{
    id:header;height:54;anchors{left:parent.left;right:parent.right;top:parent.top}
    MouseArea{anchors.fill:parent;onPressed:window.startSystemMove()
onDoubleClicked:window.fullscreen=!window.fullscreen}
    Row{id:leftActions;anchors.left:parent.left;anchors.leftMargin:14;anchors.verticalCenter:parent.verticalCenter;spacing:7
     Action{label:'×';tip:'Close';onTriggered:window.closePreview()}
     Action{label:'⛶';tip:'Full Screen';onTriggered:window.fullscreen=!window.fullscreen}
     Action{label:'‹';tip:'Previous file';enabled:QuickLookState.context==='finder' || QuickLookState.index>0;onTriggered:QuickLookState.navigate(4)}
     Action{label:'›';tip:'Next file';enabled:QuickLookState.context==='finder' || QuickLookState.index<QuickLookState.paths.length-1;onTriggered:QuickLookState.navigate(5)}
    }
    Text{textFormat:Text.PlainText;id:fileTitle;anchors.verticalCenter:parent.verticalCenter;anchors.left:leftActions.right;anchors.right:rightActions.left;anchors.margins:12;text:window.info.name || 'Quick Look';elide:Text.ElideMiddle;horizontalAlignment:Text.AlignHCenter;color:window.foreground;font.family:'SF Pro Display';font.pixelSize:13;font.weight:Font.DemiBold
     Item{id:titleDrag; width:1;height:1
      Drag.dragType:Drag.Automatic;Drag.active:titleMouse.drag.active;Drag.supportedActions:Qt.CopyAction | Qt.MoveAction;Drag.proposedAction:Qt.CopyAction
      Drag.mimeData:({'text/uri-list':(window.info.url || '')+'\r\n','text/plain':window.info.path || ''});Drag.imageSource:window.raster ? window.info.preview || '':IconResolver.forFile(window.info.name || '');Drag.imageSourceSize:Qt.size(80,80)
     }
     MouseArea{id:titleMouse;anchors.fill:parent;drag.target:titleDrag;drag.threshold:8;cursorShape:Qt.OpenHandCursor}
    }
    Row{id:rightActions;anchors.right:parent.right;anchors.rightMargin:12;anchors.verticalCenter:parent.verticalCenter;spacing:7
     Action{label:'✎';tip:'Markup a copy';visible:window.raster;onTriggered:{const file=window.info.preview || window.info.url;QuickLookState.close();CaptureState.editFile(file)}}
     Action{label:'✂';tip:'Trim';visible:['audio','video'].includes(window.kind);onTriggered:trimPopup.open()}
     Action{label:'↶';tip:'Rotate preview';visible:window.raster;onTriggered:window.angle-=90}
     Action{label:'▦';tip:'Index Sheet';visible:QuickLookState.paths.length>1;onTriggered:window.indexSheet=!window.indexSheet}
     Action{label:'↗';tip:'Show in Finder';onTriggered:{if(window.info.path)Quickshell.execDetached(['lickintosh-finder','--select',window.info.path])}}
     Action{label:'⋯';tip:'More actions';onTriggered:shareMenu.open()}
     Action{label:window.info.application ? 'Open with '+window.info.application:'Open';wide:true;tip:'Open in default app';onTriggered:QuickLookState.openDefault()}
    }
   }
   Rectangle{anchors.top:header.bottom;anchors.left:parent.left;anchors.right:parent.right;height:1;color:'#18ffffff'}
   Item{
    id:content;anchors{top:header.bottom;left:parent.left;right:parent.right;bottom:footer.top}
anchors.margins:12;clip:true
    VideoOutput{id:video;anchors.fill:parent;anchors.bottomMargin:50;visible:window.kind==='video' && !window.indexSheet;fillMode:VideoOutput.PreserveAspectFit;endOfStreamPolicy:VideoOutput.KeepLastFrame}
    Loader{anchors.fill:parent;active:!QuickLookState.error && window.kind!=='' && !window.indexSheet
     sourceComponent:window.raster ? imagePreview:window.kind==='video' || window.kind==='audio' ? mediaPreview:window.kind==='text' || window.kind==='binary' ? textPreview:window.kind==='archive' ? directoryPreview:window.kind==='font' ? fontPreview:genericPreview
    }
    BusyIndicator{anchors.centerIn:parent;running:QuickLookState.loading;visible:running}
    Text{textFormat:Text.PlainText;anchors.centerIn:parent;width:parent.width-60;text:QuickLookState.error;color:'#ffb4ad';font.pixelSize:14;wrapMode:Text.Wrap;horizontalAlignment:Text.AlignHCenter;visible:QuickLookState.error!==''}
    GridView{anchors.fill:parent;visible:window.indexSheet;model:QuickLookState.paths;cellWidth:160;cellHeight:130;clip:true
     delegate:Rectangle{required property string modelData;required property int index;width:150;height:120;radius:12;color:'#24ffffff'
      Image{anchors.top:parent.top;anchors.topMargin:8;anchors.horizontalCenter:parent.horizontalCenter;width:110;height:75;fillMode:Image.PreserveAspectFit;source:/\.(png|jpe?g|webp|gif|svg|avif)$/i.test(modelData) ? QuickLookState.urlFor(modelData):IconResolver.forFile(modelData);asynchronous:true;sourceSize:Qt.size(220,150)}
      Text{textFormat:Text.PlainText;anchors.bottom:parent.bottom;anchors.bottomMargin:8;width:parent.width-12;anchors.horizontalCenter:parent.horizontalCenter;text:decodeURIComponent(modelData.split('/').pop());color:window.foreground;elide:Text.ElideMiddle;horizontalAlignment:Text.AlignHCenter;font.pixelSize:11}
      MouseArea{anchors.fill:parent;onClicked:{QuickLookState.index=index;QuickLookState.inspect(1);window.indexSheet=false}}
     }
    }
   }
   RowLayout{
    id:footer;height:40;anchors{left:parent.left;right:parent.right;bottom:parent.bottom}
anchors.margins:12;spacing:10
    Text{textFormat:Text.PlainText;Layout.fillWidth:true;text:QuickLookState.saving ? 'Saving copy…':QuickLookState.notice || (window.info.mime ? window.info.mime+' · '+window.sizeText(window.info.size || 0):'');color:window.secondary;elide:Text.ElideMiddle;font.family:'SF Pro Text';font.pixelSize:11}
    Action{label:'Save rotation';wide:true;visible:window.raster && window.angle%360!==0;tip:'Save a rotated copy';onTriggered:{QuickLookState.saving=true;QuickLookState.send({action:'rotate',path:window.kind==='pdf' ? window.info.preview:window.info.path,degrees:window.angle})}}
    Action{label:'−';visible:window.raster;tip:'Zoom out';onTriggered:window.zoom=Math.max(.25,window.zoom-.25)}
    Text{textFormat:Text.PlainText;visible:window.raster;text:Math.round(window.zoom*100)+'%';color:window.foreground;font.pixelSize:11}
    Action{label:'+';visible:window.raster;tip:'Zoom in';onTriggered:window.zoom=Math.min(5,window.zoom+.25)}
    Action{label:'‹';visible:window.kind==='pdf';enabled:(window.info.page || 1)>1;tip:'Previous page';onTriggered:QuickLookState.inspect(window.info.page-1)}
    Text{textFormat:Text.PlainText;visible:window.kind==='pdf';text:(window.info.page || 1)+' / '+(window.info.pages || 1);color:window.foreground;font.pixelSize:11}
    Action{label:'›';visible:window.kind==='pdf';enabled:window.info.page<window.info.pages;tip:'Next page';onTriggered:QuickLookState.inspect(window.info.page+1)}
   }
  }
 }
 Component{id:imagePreview
  Flickable{id:imageScroll;contentWidth:width*window.zoom;contentHeight:height*window.zoom;clip:true;boundsBehavior:Flickable.StopAtBounds
   Item{id:image;width:imageScroll.width*window.zoom;height:imageScroll.height*window.zoom;rotation:window.angle
    Image{anchors.fill:parent;visible:window.info.mime!=='image/gif';source:visible ? window.info.preview || '':'';fillMode:Image.PreserveAspectFit;asynchronous:true;cache:false;autoTransform:true;sourceSize:Qt.size(2400,2400);onStatusChanged:if(status===Image.Error)QuickLookState.error='Preview is unavailable for this image format.'}
    AnimatedImage{anchors.fill:parent;visible:window.info.mime==='image/gif';source:visible ? window.info.preview || '':'';fillMode:Image.PreserveAspectFit;asynchronous:true;playing:visible;cache:false}
    Item{width:1;height:1
     Drag.dragType:Drag.Automatic;Drag.active:imageDrag.active;Drag.mimeData:({'text/uri-list':window.info.url+'\r\n','text/plain':window.info.path});Drag.supportedActions:Qt.CopyAction | Qt.MoveAction;Drag.proposedAction:Qt.CopyAction;Drag.imageSource:window.info.preview || '';Drag.imageSourceSize:Qt.size(96,96)
     Drag.onDragStarted:window.imageDragging=true
     Drag.onDragFinished:window.imageDragging=false
     DragHandler{id:imageDrag;target:null;acceptedModifiers:Qt.AltModifier}
    }
   }
   ScrollBar.vertical:ScrollBar{}
ScrollBar.horizontal:ScrollBar{}
  }
 }
 MediaPlayer{id:player;source:window.visible && ['video','audio'].includes(window.kind) ? window.info.url || '':'';audioOutput:AudioOutput{id:audio;volume:.65}
videoOutput:video
  onErrorOccurred:(code,message)=>QuickLookState.error=message
  onPlaybackStateChanged:QuickLookState.mediaPlaying=playbackState===MediaPlayer.PlayingState
  onSourceChanged:{video.clearOutput();if(source.toString()!=='')play()}
 }
 Component{id:mediaPreview
  Item{
   Text{textFormat:Text.PlainText;visible:window.kind==='audio';anchors.centerIn:parent;text:'♫';color:'#b9cfff';font.pixelSize:120}
   RowLayout{anchors{bottom:parent.bottom;left:parent.left;right:parent.right}
height:42;spacing:10
    Action{label:player.playbackState===MediaPlayer.PlayingState ? 'Ⅱ':'▶';tip:'Play/Pause';onTriggered:player.playbackState===MediaPlayer.PlayingState ? player.pause():player.play()}
    Text{textFormat:Text.PlainText;text:window.timeText(player.position);color:window.foreground;font.pixelSize:11}
    MediaSlider{id:seek;Layout.fillWidth:true;from:0;to:Math.max(1,player.duration);onMoved:player.position=value;Binding{target:seek;property:'value';value:player.position;when:!seek.pressed}}
    Text{textFormat:Text.PlainText;text:window.timeText(player.duration);color:window.foreground;font.pixelSize:11}
    Action{label:audio.muted ? '󰖁':'󰕾';tip:'Mute audio';onTriggered:audio.muted=!audio.muted}
    MediaSlider{Layout.preferredWidth:85;from:0;to:1;value:audio.volume;onMoved:{audio.volume=value;audio.muted=false}}
   }
  }
 }
 Component{id:textPreview;ScrollView{clip:true;TextArea{Keys.forwardTo:[keys];text:window.info.text || '';readOnly:true;selectByMouse:true;textFormat:TextEdit.PlainText;wrapMode:TextEdit.Wrap;font.family:'SF Mono';font.pixelSize:13;color:'#f1f2f6';background:null}}}
 Component{id:directoryPreview
  ListView{clip:true;model:window.info.entries || [];spacing:2;ScrollBar.vertical:ScrollBar{}
   delegate:Rectangle{required property var modelData;required property int index;width:ListView.view.width;height:36;color:index%2 ? '#0affffff':'transparent';radius:6
    Text{textFormat:Text.PlainText;anchors.left:parent.left;anchors.leftMargin:12;anchors.verticalCenter:parent.verticalCenter;width:parent.width-20;text:(modelData.directory ? '▸  ':'')+modelData.name;color:window.foreground;elide:Text.ElideMiddle;font.pixelSize:12}
   }
  }
 }
 Component{id:fontPreview;ScrollView{clip:true;FontLoader{id:font;source:window.info.url || ''}TextArea{readOnly:true;text:'Aa Bb Cc\n\nThe quick brown fox jumps over the lazy dog.\n0123456789\n\nÁÀÂÃÉÊÍÓÔÕÚÇ';font.family:font.name;font.pixelSize:36;color:window.foreground;background:null;wrapMode:TextEdit.Wrap}}}
 Component{id:genericPreview;Item{Image{anchors.centerIn:parent;width:120;height:120;source:window.kind==='directory' ? IconResolver.forFolder():IconResolver.forFile(window.info.name || '');fillMode:Image.PreserveAspectFit}}}
 Menu{
  id:shareMenu;parent:keys;x:Math.max(8,window.width-width-12);y:49
  background:Rectangle{radius:15;color:'#e6282a32'}
  MenuItem{text:'Open with another app…';onTriggered:QuickLookState.send({action:'chooseApp',path:window.info.path})}
  MenuItem{text:'Show in Finder';onTriggered:Quickshell.execDetached(['lickintosh-finder','--select',window.info.path])}
  MenuItem{text:'Copy file location';onTriggered:Quickshell.execDetached(['wl-copy','--',window.info.path])}
 }
 Popup{
  id:trimPopup;parent:keys;width:Math.min(440,window.width-40);height:210;x:(window.width-width)/2;y:(window.height-height)/2;modal:true;focus:true
  onOpened:{player.pause();trimRange.first.value=0;trimRange.second.value=player.duration}
  background:Rectangle{radius:20;color:'#ec202028'}
  ColumnLayout{anchors.fill:parent;anchors.margins:18;spacing:12
   Text{textFormat:Text.PlainText;text:'Trim '+window.info.name;color:window.foreground;font.family:'SF Pro Display';font.pixelSize:16;font.weight:Font.DemiBold;Layout.fillWidth:true;elide:Text.ElideMiddle}
   RangeSlider{id:trimRange;Layout.fillWidth:true;implicitHeight:32;leftPadding:7;rightPadding:7;from:0;to:Math.max(1,player.duration);first.onMoved:player.position=first.value;second.onMoved:player.position=second.value
    background:Rectangle{x:trimRange.leftPadding;y:(trimRange.height-height)/2;width:trimRange.availableWidth;height:5;radius:3;color:'#30ffffff'
     Rectangle{x:trimRange.first.visualPosition*parent.width;width:(trimRange.second.visualPosition-trimRange.first.visualPosition)*parent.width;height:parent.height;radius:3;color:window.foreground}
    }
    first.handle:Rectangle{x:trimRange.leftPadding+trimRange.first.visualPosition*(trimRange.availableWidth-width);y:(trimRange.height-height)/2;width:12;height:20;radius:5;color:window.foreground;border.color:'#30000000'}
    second.handle:Rectangle{x:trimRange.leftPadding+trimRange.second.visualPosition*(trimRange.availableWidth-width);y:(trimRange.height-height)/2;width:12;height:20;radius:5;color:window.foreground;border.color:'#30000000'}
   }
   Text{textFormat:Text.PlainText;text:(trimRange.first.value/1000).toFixed(1)+' s  –  '+(trimRange.second.value/1000).toFixed(1)+' s';color:window.secondary;font.pixelSize:12}
   RowLayout{Layout.alignment:Qt.AlignRight;spacing:10
    Action{label:'Cancel';wide:true;onTriggered:trimPopup.close()}
    Action{label:'Save Copy';wide:true;enabled:trimRange.second.value>trimRange.first.value;onTriggered:{QuickLookState.saving=true;QuickLookState.send({action:'trim',path:window.info.path,start:trimRange.first.value/1000,end:trimRange.second.value/1000});trimPopup.close()}}
   }
  }
 }
 component MediaSlider:Slider{
  id:control;focusPolicy:Qt.NoFocus;implicitHeight:28;leftPadding:5;rightPadding:5
  background:Rectangle{x:control.leftPadding;y:(control.height-height)/2;width:control.availableWidth;height:3;radius:2;color:Theme.isLight ? '#30202127':'#40ffffff'
   Rectangle{width:control.visualPosition*parent.width;height:parent.height;radius:2;color:window.foreground}
  }
  handle:Rectangle{x:control.leftPadding+control.visualPosition*(control.availableWidth-width);y:(control.height-height)/2;width:control.pressed ? 12:10;height:width;radius:width/2;color:window.foreground;border.width:1;border.color:Theme.isLight ? '#20000000':'#30ffffff'}
 }
 component Action:Rectangle{
  property string label:'';property string tip:'';property bool wide:false
  signal triggered()
  width:wide ? Math.max(90,actionLabel.implicitWidth+22):29;height:29;radius:wide ? 14:14;color:mouse.containsMouse ? '#32ffffff':'#12ffffff';opacity:enabled ? 1:.35
  Text{textFormat:Text.PlainText;id:actionLabel;anchors.centerIn:parent;text:parent.label;color:window.foreground;font.family:parent.label==='󰖁' || parent.label==='󰕾' ? 'Symbols Nerd Font':'SF Pro Text';font.pixelSize:parent.wide ? 11:18}
  MouseArea{id:mouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:parent.triggered()}
  ToolTip.visible:mouse.containsMouse && tip!=='';ToolTip.delay:800;ToolTip.text:tip
 }
}
