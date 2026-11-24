pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
Singleton {
 id:root
 property real value:0.5
 property bool available:false
 property bool ready:false
 property real pending:-1
 property string error:''
 function set(fraction){pending=Math.max(.01,Math.min(1,fraction));value=pending;debounce.restart()}
 function change(delta){set(value+delta)}
 function refresh(){if(!request.running && pending<0){request.command=['python3',Quickshell.shellDir+'/tools/brightness.py','get'];request.running=true}}
 function flush(){if(request.running)return;const wanted=pending;pending=-1;request.command=['python3',Quickshell.shellDir+'/tools/brightness.py','set',String(Math.round(wanted*100))];request.running=true}
 Timer{id:debounce;interval:120;onTriggered:root.flush()}
 Process{id:request
  stdout:StdioCollector{onStreamFinished:{try{const data=JSON.parse(text);root.available=!!data.available;root.error=data.error || '';if(data.available && root.pending<0)root.value=data.value/100;root.ready=true}catch(error){root.error='Invalid brightness response'}}}
  onExited:if(root.pending>=0)debounce.restart()
 }
 FileView{path:Quickshell.env('XDG_RUNTIME_DIR')+'/lickintosh-brightness/value.json';watchChanges:true;onFileChanged:reload();onLoaded:{try{const data=JSON.parse(text());root.available=!!data.available;if(data.available && root.pending<0 && !request.running)root.value=data.value/100}catch(error){}}}
 Timer{interval:5000;running:true;repeat:true;triggeredOnStart:true;onTriggered:root.refresh()}
}
