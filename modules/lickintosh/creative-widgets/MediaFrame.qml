import QtQuick
import QtMultimedia
import Quickshell
import Quickshell.Io
import qs.services
Item{
 id:root
 property string path:''
 property bool desktopWidget:false
 property bool isSnapshot:false
 property bool playing:false
 property bool sound:false
 property real volume:.35
 property bool loop:true
 property string fit:'crop'
 signal finished()
 readonly property bool video:/\.(mp4|mkv|webm|mov|m4v|avi|ogv)(?:[?#].*)?$/i.test(path)
 readonly property bool gif:/\.gif(?:[?#].*)?$/i.test(path)
 readonly property url url:{const p=path.startsWith('~/') ? Quickshell.env('HOME')+path.slice(1):path;return p.startsWith('file:') ? p:p ? 'file://'+p.split('/').map(encodeURIComponent).join('/'):''}
 property string poster:''
 property string posterError:''
 readonly property string error:video ? player.item?.error || (!posterUrl ? posterError:''):gif ? animation.status===Image.Error ? 'Unable to load GIF':'':image.status===Image.Error ? 'Unable to load image':''
 readonly property string posterUrl:poster || CreativeMedia.posters[path] || ''
 onPosterChanged:if(!isSnapshot)CreativeMedia.poster(path,poster)
 readonly property bool playbackActive:player.item?.playbackState===MediaPlayer.PlayingState
 readonly property bool renderingVideo:!!player.item?.hasFrame
 readonly property bool ready:video ? !!posterUrl || !!player.item?.ready:gif ? animation.status===Image.Ready:image.status===Image.Ready
 onPathChanged:{poster='';posterError='';if(video && !isSnapshot && !CreativeMedia.posters[path] && !posterProcess.running)posterProcess.running=true}
 Process{
  id:posterProcess
  property string requested:''
  command:['@MEDIA_PYTHON@',Quickshell.shellDir+'/tools/widget-media.py','poster',root.path]
  onStarted:requested=root.path
  stdout:StdioCollector{onStreamFinished:{if(posterProcess.requested!==root.path){if(root.video)Qt.callLater(()=>posterProcess.running=true);return}try{const result=JSON.parse(text);root.poster=result.poster || '';root.posterError=result.error ? 'Unable to read video':''}catch(error){}}}
 }
 Image{id:image;anchors.fill:parent;source:root.video ? root.posterUrl:!root.gif ? root.url:'';fillMode:root.fit==='fit' ? Image.PreserveAspectFit:root.fit==='stretch' ? Image.Stretch:Image.PreserveAspectCrop;asynchronous:true;smooth:true;mipmap:true;sourceSize:Qt.size(Math.ceil(width*2),Math.ceil(height*2));visible:status===Image.Ready && (!root.video || !player.item?.hasFrame)}
 AnimatedImage{id:animation;anchors.fill:parent;source:root.gif ? root.url:'';fillMode:root.fit==='fit' ? Image.PreserveAspectFit:root.fit==='stretch' ? Image.Stretch:Image.PreserveAspectCrop;asynchronous:true;smooth:true;cache:false;playing:root.playing && !root.isSnapshot;visible:root.gif}
 Loader{
  id:player;anchors.fill:parent;active:root.video && root.desktopWidget && !root.isSnapshot
  sourceComponent:Item{
   id:videoHost
   property bool hasFrame:false
   property alias playbackState:movie.playbackState
   readonly property string error:movie.errorString
   readonly property bool ready:movie.mediaStatus===MediaPlayer.LoadedMedia || movie.mediaStatus===MediaPlayer.BufferedMedia || hasFrame
   function sync(){if(root.playing)movie.play();else movie.pause()}
   Connections{target:root;function onPlayingChanged(){videoHost.sync()}function onPathChanged(){videoHost.hasFrame=false}}
   Component.onCompleted:sync()
   MediaPlayer{
    id:movie;source:root.url;videoOutput:output
    audioOutput:AudioOutput{muted:!root.sound || !root.playing;volume:Math.max(0,Math.min(1,root.volume))}
    loops:root.loop ? MediaPlayer.Infinite:1
    onMediaStatusChanged:{if(mediaStatus===MediaPlayer.LoadedMedia)videoHost.sync();if(mediaStatus===MediaPlayer.EndOfMedia)root.finished()}
   }
   VideoOutput{id:output;anchors.fill:parent;visible:videoHost.hasFrame;fillMode:root.fit==='fit' ? VideoOutput.PreserveAspectFit:root.fit==='stretch' ? VideoOutput.Stretch:VideoOutput.PreserveAspectCrop}
   Connections{target:output.videoSink;function onVideoFrameChanged(){videoHost.hasFrame=true}}
  }
 }
}
