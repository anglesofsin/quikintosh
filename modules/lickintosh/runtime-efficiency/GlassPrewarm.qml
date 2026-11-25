pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import qs.services
Singleton {
 id:root
 property var queue:[]
 property var current:null
 property int frames:0
 property bool rendering:false
 property real started:0
 property int activePanels:0
 onActivePanelsChanged:if(activePanels===0)pump.restart()
 function enqueue(item){if(!item || !item.preload || !item.preloadReady || item.presentationActive || queue.indexOf(item)>=0 || current===item)return;queue=queue.concat([item]);pump.start()}
 function remove(item){queue=queue.filter(entry=>entry!==item);if(current===item)finish()}
 function finish(){const item=current;current=null;if(item)item.prewarming=false;frames=0;rendering=false;pump.restart()}
 function requestAll(){for(const e of GlassRegistry.entries)enqueue(e.backdrop)}
 Timer{id:events;interval:250;onTriggered:root.requestAll()}
 function invalidate(){events.restart()}
 Timer{id:pump;interval:80;onTriggered:{
  if(root.current || root.queue.length===0)return
  if(root.activePanels>0 || GlassTracker.captureBlocked)return
  const item=root.queue[0];root.queue=root.queue.slice(1)
  if(!item || item.presentationActive){restart();return}
  root.current=item;root.started=Date.now();root.frames=0;item.prewarming=true
 }}
 FrameAnimation{running:root.current!==null;onTriggered:{
  const item=root.current
  if(!item || item.presentationActive || root.activePanels>0 || GlassTracker.captureBlocked){root.finish();return}
  if(item.captureSettled && !root.rendering){if(++root.frames>=3 && Date.now()-root.started>=120){root.rendering=true;item.prepareMaterial(()=>{if(root.current===item)root.finish()})}}
  if(Date.now()-root.started>900)root.finish()
 }}
 Connections{target:GlassTracker;function onTransitionEpochChanged(){root.invalidate()}function onCaptureBlockedChanged(){if(!GlassTracker.captureBlocked)root.invalidate()}}
 Connections{target:Hyprland;function onRawEvent(event){if(GlassTracker.geometryEvents.includes(event.name) || event.name==="focusedmon" || event.name.startsWith("monitor"))root.invalidate()}}
 Connections{target:ControlCatalog;function onItemsChanged(){root.invalidate()}}
 Connections{target:GlassWallpaper;function onStillPathChanged(){root.invalidate()}function onVideoActiveChanged(){root.invalidate()}}
}
