pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
 id:root
 readonly property int height:ShellConfig.options.wallpaper.videoHeight
 readonly property int fps:ShellConfig.options.wallpaper.videoFps
 property bool measuring:false
 property var probes:({})
 property real guiLast:0
 property real guiMaxGap:0
 function addProbe(path,probe){const next=Object.assign({},probes);next[path]=probe;probes=next}
 function removeProbe(path,probe){if(probes[path]!==probe)return;const next=Object.assign({},probes);delete next[path];probes=next}
 Timer{interval:20;running:root.measuring;repeat:true;onTriggered:{const now=Date.now();if(root.guiLast)root.guiMaxGap=Math.max(root.guiMaxGap,now-root.guiLast);root.guiLast=now}}
 IpcHandler{target:'wallpaperVideo';function monitor(value:bool):void{root.guiLast=0;root.guiMaxGap=0;root.measuring=value}function state():string{return JSON.stringify({measuring:root.measuring,guiMaxGapMs:root.guiMaxGap,busy:root.busy,error:root.error,streams:Object.keys(root.probes).map(path=>({path:path,frames:root.probes[path]?.statistics()}))})}}
 property var files:({})
 property var pending:({})
 property var failures:({})
 readonly property bool busy:Object.keys(pending).length>0
 readonly property string error:Object.values(failures).join('\n')
 function key(path){return JSON.stringify([path,height,fps])}
 function resolve(path){
  if(!path || (!height && !fps))return path
  const k=key(path)
  if(files[k])return files[k]
  Qt.callLater(function(){root.request(path)})
  return path
 }
 function request(path){
  if(!path || (!height && !fps))return
  const k=key(path)
  if(files[k] || pending[k] || failures[k])return
  const next=Object.assign({},pending);next[k]=true;pending=next
  if(!worker.running)worker.running=true
  worker.write(JSON.stringify({key:k,source:path,height:height,fps:fps})+'\n')
 }
 Process {
  id:worker
  command:['@PYTHON@',Quickshell.shellDir+'/tools/wallpaper-video-render.py']
  stdinEnabled:true
  stdout:SplitParser{onRead:line=>{try{
   const data=JSON.parse(line),next=Object.assign({},root.pending);delete next[data.key];root.pending=next
   if(data.error){const errors=Object.assign({},root.failures);errors[data.key]=data.error;root.failures=errors}
   else{const files=Object.assign({},root.files);files[data.key]=data.path;root.files=files}
  }catch(error){console.warn('Wallpaper video preparation:',error)}}}
  onExited:{if(root.busy){const errors=Object.assign({},root.failures);for(const k of Object.keys(root.pending))errors[k]='Video preparation stopped';root.failures=errors;root.pending=({})}}
 }
}
