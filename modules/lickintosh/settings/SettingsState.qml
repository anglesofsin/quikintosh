pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton{
 id:root
 property bool ready:false
 property int ownerPid:0
 property var data:({})
 property var loading:({})
 property var updated:({})
 property string error:''
 property bool changing:false
 property int serial:0
 property var requests:({})
 signal completed(string name,var result)
 function send(kind,name,args){
  if(!ready)return 0
  const token=++serial;requests[token]={kind:kind,name:name};worker.write(JSON.stringify({kind:kind,name:name,args:args || {},token:token})+'\n');return token
 }
 function query(name,force,args){if(args)force=true;if(!ready || loading[name] || (!force && updated[name] && Date.now()-updated[name]<15000))return;const next=Object.assign({},loading);next[name]=true;loading=next;send('query',name,args)}
 function change(name,args){error='';changing=true;send('action',name,args)}
 function refresh(){for(const name of Object.keys(data))root.query(name,true)}
 function bytes(value){if(value===null || value===undefined)return 'Not available';const units=['B','KB','MB','GB','TB'];let number=Number(value),index=0;while(number>=1024 && index<4){number/=1024;index++}return number.toFixed(index>1 ? 1:0)+' '+units[index]}
 function open(command){Quickshell.execDetached(command)}
 FileView{
  id:runtimeStatus;path:Quickshell.env('HOME')+'/.local/state/lickintosh/settings/runtime-status.json';watchChanges:true
  onFileChanged:reload()
  onLoaded:{try{const status=JSON.parse(text());if(status.error)root.error=status.error}catch(error){}}
 }
 Process{
  id:worker;running:true;stdinEnabled:true;command:['@PYTHON@',Quickshell.shellDir+'/settingsapp/backend.py','--worker']
  stdout:SplitParser{onRead:line=>{try{
   const event=JSON.parse(line)
   if(event.type==='ready'){root.ownerPid=event.ownerPid || 0;root.ready=true;root.query('system',true);return}
   const request=root.requests[event.token];delete root.requests[event.token]
   if(request?.kind==='query'){const flags=Object.assign({},root.loading);delete flags[request.name];root.loading=flags}
   if(request?.kind==='action')root.changing=false
   if(event.type==='error'){root.error=event.message;return}
   if(event.kind==='query'){const next=Object.assign({},root.data);next[event.name]=event.data;root.data=next;root.updated[event.name]=Date.now()}
   else root.completed(event.name,event.data)
  }catch(error){console.warn('Settings response:',error)}}}
  onExited:code=>{root.ready=false;root.loading=({});root.changing=false;if(code!==0)root.error='The settings service stopped. Reopen Settings to reconnect.'}
 }
}
