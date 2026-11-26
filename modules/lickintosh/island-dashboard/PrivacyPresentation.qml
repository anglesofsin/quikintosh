pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Wayland
import qs.services
Singleton {
 id:root
 property var focused:({})
 property int epoch:0
 property bool again:false
 property bool initialized:false
 function refresh(){if(query.running){again=true;return}query.running=true}
 function fullscreen(name){
  const mon=Hyprland.monitors.values.find(m=>m.name===name)
  const active=Hyprland.activeToplevel
  const foreign=ToplevelManager.activeToplevel
  // The focused foreign handle is immediate. Match its workspace so a stale
  // handle during a switch can never hide the island on the next workspace.
  if(active && foreign && active.wayland===foreign && active.monitor?.name===name &&
     active.workspace?.id===mon?.activeWorkspace?.id)return foreign.fullscreen
  return !!root.focused[name]
 }
 function setCorner(screenName,show){}
 Process {
  id:query
  command:['hyprctl','-j','--batch','activewindow;monitors']
  stdout:StdioCollector{onStreamFinished:{try{
   const parts=JSON.parse('['+text.trim().replace(/}\s*\[/,'},[')+']')
   const w=parts[0],monitors=parts[1],next={}
   if(w.address && w.address!=='0x0' && Number(w.fullscreen)===2){
    const mon=monitors.find(m=>m.id===w.monitor)
    if(mon && (w.workspace?.id===mon.activeWorkspace?.id || w.workspace?.id===mon.specialWorkspace?.id))next[mon.name]=true
   }
   if(JSON.stringify(next)!==JSON.stringify(root.focused))root.focused=next
   root.initialized=true;root.epoch++
  }catch(error){console.warn('Fullscreen focus:',error)}}}
  onExited:if(root.again){root.again=false;Qt.callLater(root.refresh)}
 }
 Connections{target:Hyprland
  function onRawEvent(event){
   if(['fullscreen','activewindowv2','workspace','workspacev2','focusedmon','activespecial','activespecialv2','openwindow','closewindow'].includes(event.name))root.refresh()
  }
  function onActiveToplevelChanged(){root.refresh()}
 }
 Connections{target:SettingsPreferences;function onLockedChanged(){root.refresh()}}
 Timer{interval:1000;running:true;repeat:true;triggeredOnStart:true;onTriggered:root.refresh()}
}
