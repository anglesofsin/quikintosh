pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import "audio-policy.js" as Policy
Singleton{
 id:root
 property bool checked:false
 property bool externalActive:false
 property var apps:[]
 readonly property bool mprisActive:MprisState.players.some(player=>player.isPlaying)
 readonly property bool busy:mprisActive || externalActive
 readonly property bool mayPlay:checked && !busy
 function observe(data){
  checked=true;stale.restart();const next=Policy.activeOutputs(data,Quickshell.processId);apps=next
  if(next.length){quiet.stop();externalActive=true}
  else if(externalActive && !quiet.running)quiet.start()
 }
 IpcHandler{target:'widget-audio';function status():string{return JSON.stringify({checked:root.checked,busy:root.busy,mpris:root.mprisActive,apps:root.apps})}}
 Timer{id:quiet;interval:1200;onTriggered:root.externalActive=false}
 Timer{id:stale;interval:4500;onTriggered:root.checked=false}
}
