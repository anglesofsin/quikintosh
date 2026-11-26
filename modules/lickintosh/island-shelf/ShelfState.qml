pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.rosa.services
Singleton {
 id:root
 property double awakeUntil:0
 property string awakeError:''
 property int nextAwakeMinutes:0
 function startAwake(){const minutes=nextAwakeMinutes;nextAwakeMinutes=0;awakeUntil=minutes>0 ? Date.now()+minutes*60000:0;if(minutes>0){awake.command=['systemd-inhibit','--what=idle','--mode=block','--who=Quickintosh','--why=User requested Stay Awake','sleep',String(minutes*60)];awake.running=true}}
 function keepAwake(minutes){awakeError='';nextAwakeMinutes=minutes;if(awake.running)awake.running=false;else startAwake()}
 Process{id:awake;onExited:code=>{if(root.nextAwakeMinutes>0){Qt.callLater(root.startAwake);return}root.awakeUntil=0;if(code!==0 && code!==15)root.awakeError=qsTr('Idle inhibition is unavailable on this system')}}
 property bool trayOpen:false
 property bool editing:false
 property var editorOwners:({})
 property int interactionCount:0
 readonly property bool holdOpen:editing || Object.keys(editorOwners).length>0 || interactionCount>0
 function setEditor(owner,on){const next=Object.assign({},editorOwners);if(on)next[owner]=true;else delete next[owner];editorOwners=next}
 function interaction(on){interactionCount=Math.max(0,interactionCount+(on ? 1:-1))}
 property bool playerOpen:false
 property var items:[]
 property var clips:[]
 property var activities:[]
 property double now:Date.now()
 property string notice:''
 property bool ready:false
 property var pending:[]
 property int openPage:0
 Connections{target:IslandBus;function onLockedChanged(){if(IslandBus.locked){root.playerOpen=false;root.trayOpen=false;root.editing=false;root.editorOwners=({});root.interactionCount=0}}}
 signal closeRequested()
 signal reveal(int page)
 function send(event){if(ready)worker.write(JSON.stringify(event)+'\n');else pending=pending.concat([event])}
 function add(urls){send({action:'add',paths:Array.from(urls).map(String)})}
 Process {
  id:worker;command:['@PYTHON@',Quickshell.shellPath('island-shelf/backend.py')];running:IslandConfig.s('enabled');stdinEnabled:true
  stdout:SplitParser {onRead:data=>{try{
   const e=JSON.parse(data)
   if(e.type==='ready'){root.ready=true;root.items=e.items;for(const p of root.pending)worker.write(JSON.stringify(p)+'\n');root.pending=[]}
   else if(e.type==='tray')root.items=e.items
   else if(e.type==='clipboard')root.clips=e.items
   else if(e.type==='activities')root.activities=e.items
   else if(e.type==='error')root.notice=e.message
  }catch(_) {}}}
  onExited:{root.ready=false;if(IslandConfig.s('enabled'))retry.restart()}
 }
 IpcHandler{target:'shelf'
  function addFiles(encoded:string):string{try{root.add(JSON.parse(Qt.atob(encoded)));root.reveal(6);return 'queued'}catch(_){return 'invalid'}}
  function close():void{root.closeRequested()}
  function open(page:int):void{if(IslandBus.locked)return;root.reveal(Math.max(0,Math.min(12,page)))}
  function activity(encoded:string):string{try{root.send({action:'activity',activity:JSON.parse(encoded)});return 'queued'}catch(_){return 'invalid'}}
  function status():string{return JSON.stringify({ready:root.ready,files:root.items.length,activities:root.activities.length})}
 }
 Timer{interval:1000;running:root.activities.length>0 || root.awakeUntil>0;repeat:true;onTriggered:{root.now=Date.now();root.activities=root.activities.filter(a=>a.expires*1000>root.now)}}
 Timer{id:retry;interval:1500;onTriggered:worker.running=true}
 Timer {interval:5000;running:root.notice!=='';onTriggered:root.notice=''}
}
