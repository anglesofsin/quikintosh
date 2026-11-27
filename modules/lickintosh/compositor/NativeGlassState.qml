pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
Singleton {
 id:root
 property var targets:[]
 function applied(target){return targets.includes(target)}
 Timer{id:reload;interval:20;onTriggered:file.reload()}
 FileView {
  id:file;watchChanges:true
  path:(Quickshell.env('XDG_STATE_HOME') || Quickshell.env('HOME')+'/.local/state')+'/lickintosh/settings/native-glass-runtime.json'
  onFileChanged:reload.restart()
  onLoaded:{try{const data=JSON.parse(text());root.targets=data.instance===Quickshell.env('HYPRLAND_INSTANCE_SIGNATURE') ? data.targets || []:[]}catch(_){root.targets=[]}}
  onLoadFailed:root.targets=[]
 }
}
