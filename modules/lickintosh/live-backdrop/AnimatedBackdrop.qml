import QtQuick
import QtMultimedia
import qs.services
import qs.components.glass
Item {
 id:root
 property string path:''
 property bool playing:false
 readonly property bool hasFrame:movie.hasVideo && movie.position>=0 && movie.playbackState!==MediaPlayer.StoppedState
 function sync(){if(playing)movie.play();else movie.pause()}
 onPlayingChanged:sync()
 MediaPlayer {
  id:movie
  source:root.path ? 'file://'+root.path:''
  loops:MediaPlayer.Infinite
  videoOutput:video
  audioOutput:null
  onMediaStatusChanged:if(mediaStatus===MediaPlayer.LoadedMedia){if(root.path===ShellConfig.options.wallpaper.videoPath)movie.position=GlassWallpaper.videoPosition;root.sync()}
 }
 VideoOutput{ id:video;anchors.fill:parent;fillMode:ShellConfig.options.wallpaper.fit==='fit' ? VideoOutput.PreserveAspectFit:ShellConfig.options.wallpaper.fit==='stretch' ? VideoOutput.Stretch:VideoOutput.PreserveAspectCrop }
}
