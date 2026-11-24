import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Scope {
 id:root
 property bool enabled:false
 property bool locked:false
 Binding{target:QuickLookState;property:'active';value:root.enabled}
 Binding{target:QuickLookState;property:'enabled';value:root.enabled && !root.locked}
 QuickLookWindow{id:viewer}
 QuickLookModal{}
 IpcHandler {
  target:'quicklook'
  function preview(path:string):void{QuickLookState.show([path],0,'external')}
  function openFiles(encoded:string):string{const paths=JSON.parse(Qt.atob(encoded));if(!QuickLookState.enabled || !Array.isArray(paths) || !paths.length)return 'unavailable';QuickLookState.show(paths,0,'external');return 'opened'}
  function close():void{QuickLookState.close()}
  function status():string{return JSON.stringify({opened:QuickLookState.opened,ready:QuickLookState.ready,bridge:QuickLookState.bridgeReady,loading:QuickLookState.loading,mediaPlaying:QuickLookState.mediaPlaying,path:QuickLookState.data.path || '',kind:QuickLookState.data.kind || '',geometry:QuickLookState.geometry,focusPending:QuickLookState.focusPending,glassReady:viewer.glassReady,glassRegion:viewer.glassRegion,videoFrames:viewer.videoFrames,error:QuickLookState.error})}
 }
}
