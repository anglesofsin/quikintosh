pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
 id:root
 readonly property int height:ShellConfig.options.wallpaper.videoHeight
 readonly property int fps:ShellConfig.options.wallpaper.videoFps
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
