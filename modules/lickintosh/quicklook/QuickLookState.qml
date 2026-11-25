pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import qs.components.glass
import qs.services
Singleton {
 id:root
 property bool active:false
 property bool enabled:false
 property int ownerPid:0
 property bool focusPending:false
 property bool focusSent:false
 property double focusDeadline:0
 property var thumbnailMap:({})
 property var thumbnailRequests:({})
 signal activated()
 property bool opened:false
 property bool restartReady:true
 property bool returnToDesktop:false
 property bool mediaPlaying:false
 property bool ready:false
 property bool bridgeReady:false
 property var pending:[]
 property bool saving:false
 property string notice:''
 property bool loading:false
 property var paths:[]
 property int index:0
 property int requestId:0
 property string context:''
 property var data:({})
 property string error:''
 property int openedSnapshot:0
 function addressOf(value){return String(value || '').replace(/^0x/i,'').toLowerCase()}
 readonly property var previewClient:opened && GlassTracker.snapshotSerial>=openedSnapshot ? GlassTracker.clientsSnapshot.find(c=>c.pid===root.ownerPid && c.mapped!==false && !c.hidden && String(c.title || '').startsWith('Lickintosh Quick Look')) || null:null
 // Closed Quickshell toplevels can retain their last IPC object. Match the
 // current compositor client first, so reopening never selects the old surface.
 readonly property var previewToplevel:previewClient ? Hyprland.toplevels.values.find(t=>root.addressOf(t.address)===root.addressOf(previewClient.address)) || null:null
 readonly property var previewIpc:previewToplevel && previewToplevel.lastIpcObject ? previewToplevel.lastIpcObject:previewClient
 readonly property var geometry:{
  const w=previewIpc;if(!opened || !w || !w.at)return ({})
  const m=GlassTracker.monitorSnapshots.find(m=>m.id===w.monitor);if(!m)return ({})
  return {address:w.address,x:w.at[0]-m.x,y:w.at[1]-m.y,width:w.size ? w.size[0]:0,height:w.size ? w.size[1]:0,monitor:m.name}
 }
 property int transferSerial:0
 signal transferred(var paths,int token)
 signal transferFailed(int token)
 signal filesChanged(var paths,var changes,string operation)
 function urlFor(path){return String(path).startsWith('file:') ? String(path):'file://'+String(path).split('/').map(encodeURIComponent).join('/')}
 function send(value){if(ready)worker.write(JSON.stringify(value)+'\n');else if(enabled)pending=pending.concat([value])}
 function requestFocus(){if(!opened || !focusPending || focusSent)return;if(Date.now()>focusDeadline){focusPending=false;return}if(geometry.address){focusSent=true;send({action:'focus',address:geometry.address})}}
 onGeometryChanged: requestFocus()
 function thumbnail(path,version){
  if(enabled)Qt.callLater(()=>root.requestThumbnail(path,version))
  return thumbnailMap[path] || ''
 }
 function requestThumbnail(path,version){
  if(!enabled)return
  const token=version===undefined ? '':String(version)
  if(thumbnailRequests[path]===undefined || (token!=='' && thumbnailRequests[path]!==token)){
   const next=Object.assign({},thumbnailRequests);next[path]=token;thumbnailRequests=next;send({action:'thumbnail',path:path,version:token})
  }
 }
 function show(files,position,source){if(!enabled || !files.length)return;paths=files.slice();index=Math.max(0,Math.min(paths.length-1,position));context=source;if(!opened){openedSnapshot=GlassTracker.snapshotSerial+1;GlassTracker.captureSnapshot();focusPending=true;focusSent=false;focusDeadline=Date.now()+1800}opened=true;GlassTracker.refreshWindows();send({action:'visible',value:true});inspect(1);requestFocus()}
 function inspect(page){loading=true;error='';notice='';send({action:'inspect',path:paths[index],page:page || 1,id:++requestId})}
 function close(){if(opened && enabled && context==='desktop'){returnToDesktop=true;desktopReturn.restart()}opened=false;focusPending=false;focusSent=false;data=({});loading=false;send({action:'visible',value:false})}
 function navigate(direction){if(context==='finder'){send({action:'navigate',direction:direction});return}const step=direction===2 || direction===4 ? -1:1;index=Math.max(0,Math.min(paths.length-1,index+step));inspect(1)}
 function fileAction(operation,paths,name,destination){send({action:'fileOperation',operation:operation,paths:paths || [],name:name || '',destination:destination || ''})}
 function transfer(urls,destination,operation){const token=++transferSerial;send({action:'transfer',id:token,paths:urls.map(String),destination:destination,operation:operation});return token}
 function openDefault(){if(data.path){send({action:'openExternal',path:data.path});close()}}
 Process {
  id:worker;running:root.active && root.restartReady;stdinEnabled:true
  command:['@PYTHON@',Quickshell.shellDir+'/quicklook/backend.py']
  stdout:SplitParser{onRead:line=>{try{
   const e=JSON.parse(line)
   if(e.type==='ready'){root.ownerPid=e.ownerPid || 0;root.ready=true;const queued=root.pending;root.pending=[];for(const value of queued)root.send(value)}
   else if(e.type==='focused'){root.focusPending=false;root.focusSent=false;root.activated()}
   else if(e.type==='thumbnail'){if(root.thumbnailRequests[e.path]===String(e.version || '')){const next=Object.assign({},root.thumbnailMap);next[e.path]=e.url;root.thumbnailMap=next}}
   else if(e.type==='bridge')root.bridgeReady=e.ready
   else if(e.type==='request'){
    const current=root.data.url || root.paths[root.index]
    if(e.toggle && root.opened && current===e.uri)root.close();else root.show([e.uri],0,'finder')
   }else if(e.type==='close')root.close()
   else if(e.type==='preview' && e.id===root.requestId){root.data=e.data;root.loading=false}
   else if(e.type==='fileOperation')root.filesChanged(e.paths,e.changes,e.operation)
   else if(e.type==='transferred')root.transferred(e.paths,e.id)
   else if(e.type==='saved'){root.saving=false;root.notice='Saved '+e.path.split('/').pop();Quickshell.execDetached(['notify-send','-a','Quick Look','Saved copy',e.path])}
   else if(e.type==='error'){if(e.operation==='focus'){root.focusSent=false}else if(e.operation==='thumbnail'){}else if(e.operation==='transfer'){root.transferFailed(e.id);Quickshell.execDetached(['notify-send','-a','Quick Look','File transfer failed',e.message])}if(e.operation==='fileOperation')Quickshell.execDetached(['notify-send','-a','Files','Unable to complete file operation',e.message]);if(['trim','rotate'].includes(e.operation)){root.saving=false;root.notice=e.message}else if(e.operation==='inspect' && e.id===root.requestId){root.error=e.message;root.loading=false}else if(!['focus','thumbnail'].includes(e.operation))console.warn('Quick Look:',e.message)}
  }catch(e){console.warn('Quick Look protocol:',e)}}}
  onExited:{root.ready=false;root.bridgeReady=false;root.opened=false;if(root.active){root.restartReady=false;retry.restart()}}
 }
 Timer{interval:120;running:root.opened && root.focusPending;repeat:true;onTriggered:{GlassTracker.refreshWindows();root.requestFocus()}}
 Timer{id:retry;interval:1000;onTriggered:root.restartReady=true}
 Timer{id:desktopReturn;interval:180;onTriggered:root.returnToDesktop=false}
 Timer{interval:120;running:root.opened && (!root.geometry.address || root.focusPending);repeat:true;triggeredOnStart:true;onTriggered:{GlassTracker.captureSnapshot();GlassTracker.refreshWindows()}}
 onEnabledChanged:if(!enabled){pending=[];returnToDesktop=false;close()}
}
