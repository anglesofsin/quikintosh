//@ pragma AppId org.quickintosh.WallpaperBenchmark
import QtQuick
import QtMultimedia
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickintosh.Render
ShellRoot {
 PanelWindow {
  id:window
  anchors{left:true;right:true;top:true;bottom:true}
  color:'black';exclusionMode:ExclusionMode.Ignore
  WlrLayershell.layer:WlrLayer.Background
  WlrLayershell.namespace:'quickintosh:wallpaper-benchmark'
  WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
  VideoOutput{id:video;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectCrop}
  MediaPlayer{id:player;source:Quickshell.env('QUICKINTOSH_BENCHMARK_VIDEO');loops:MediaPlayer.Infinite;audioOutput:null;videoOutput:video;Component.onCompleted:play()}
  VideoFrameRelay{id:probe;source:video.videoSink;measuring:true}
 }
 IpcHandler{target:'wallpaperBenchmark';function state():string{return JSON.stringify(Object.assign({error:player.errorString},probe.statistics()))}}
}
