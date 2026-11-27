pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import qs.rosa.services
Singleton {
 id:root
 readonly property string pythonExecutable:'@PYTHON@'
 property double awakeUntil:0
 property string awakeError:''
 property int nextAwakeMinutes:0
 function startAwake(){const minutes=nextAwakeMinutes;nextAwakeMinutes=0;awakeUntil=minutes>0 ? Date.now()+minutes*60000:0;if(minutes>0){awake.command=['systemd-inhibit','--what=idle','--mode=block','--who=Quickintosh','--why=User requested Stay Awake','sleep',String(minutes*60)];awake.running=true}}
 function keepAwake(minutes){awakeError='';nextAwakeMinutes=minutes;if(awake.running)awake.running=false;else startAwake()}
 Process{id:awake;onExited:code=>{if(root.nextAwakeMinutes>0){Qt.callLater(root.startAwake);return}root.awakeUntil=0;if(code!==0 && code!==15)root.awakeError=qsTr('Idle inhibition is unavailable on this system')}}
 property point basketPosition:Qt.point(0,0)
 property bool basketOpen:false
 readonly property bool trayShakeEnabled:IslandConfig.s('trayShakeEnabled')!==false
 Connections{target:Hyprland;function onRawEvent(event){if(event.name==="quickintosh-drag-end"){basketDismiss.restart();return}if(event.name!=="quickintosh-drag-shake" || !root.trayShakeEnabled || IslandBus.locked)return;const point=event.data.split(",");root.basketPosition=Qt.point(Number(point[0]),Number(point[1]));root.basketOpen=true}}
 Timer{id:basketDismiss;interval:300;onTriggered:root.basketOpen=false}
 property bool transformOpen:false
 property var transformPaths:[]
 property string transformOperation:'compress'
 property var vaultInfo:({})
 signal vaultNote(string name,string text,string modified)
 property var breakDue:({})
 Timer{interval:15000;repeat:true;running:root.utilityPreferences.breaksEnabled===true && !IslandBus.locked;onTriggered:{
  const now=Date.now(),next=Object.assign({},root.breakDue)
  if(VoiceCalls.active || NotifService.dndEnabled){root.breakDue=({});return}
  const labels={eyes:qsTr('Look away from the screen for 20 seconds'),stretch:qsTr('Time for a gentle stretch'),water:qsTr('Time for a glass of water')}
  for(const key of ['eyes','stretch','water']){
   if(!next[key])next[key]=now+(root.utilityPreferences[key+'Minutes'] || ({eyes:20,stretch:60,water:90})[key])*60000
   if(now>=next[key]){Quickshell.execDetached(['notify-send','--app-name=Quickintosh','--expire-time=10000',qsTr('Take a break'),labels[key]]);next[key]=now+(root.utilityPreferences[key+'Minutes'] || 60)*60000}
  }
  root.breakDue=next
 }}
 property var utilityPreferences:({})
 property var capabilities:({})
 property var installedApps:[]
 property var storageInfo:({total:0,used:0,free:0,cache:0})
 property bool fileBusy:false
 readonly property bool busy:fileBusy || transformJob.running
 property var transformPresets:[]
 property var jobEvent:({})
 property bool jobCancelled:false
 property var lastTransform:({})
 property bool trayOpen:false
 property bool editing:false
 property var editorOwners:({})
 property int interactionCount:0
 property int menuCount:0
 readonly property bool holdOpen:editing || Object.keys(editorOwners).length>0 || interactionCount>0
 function setEditor(owner,on){const next=Object.assign({},editorOwners);if(on)next[owner]=true;else delete next[owner];editorOwners=next}
 function interaction(on){interactionCount=Math.max(0,interactionCount+(on ? 1:-1))}
 property bool playerOpen:false
 property var filePreviews:({})
 property var items:[]
 property var clips:[]
 property var activities:[]
 property double now:Date.now()
 property bool noticeError:false
 property string notice:''
 property bool ready:false
 property var pending:[]
 property int openPage:0
 Connections{target:IslandBus;function onLockedChanged(){if(IslandBus.locked){root.playerOpen=false;root.trayOpen=false;root.basketOpen=false;root.editing=false;root.editorOwners=({});root.interactionCount=0;root.menuCount=0}}}
 signal developerResult(string text,string error)
 signal closeRequested()
 signal reveal(int page)
 function send(event){if(event.action==='archive' || event.action==='unzip')event=Object.assign({},event,{action:'transform',operation:event.action==='archive' ? 'zip':'unzip'});if(event.action==='transform'){if(transformJob.running)return;jobEvent=event;jobCancelled=false;notice='';noticeError=false;transformJob.running=true;return}if(ready)worker.write(JSON.stringify(event)+'\n');else pending=pending.concat([event])}
 function add(urls){send({action:'add',paths:Array.from(urls).map(String)})}
 Process {
  id:worker;command:['@PYTHON@',Quickshell.shellPath('island-shelf/backend.py')];running:IslandConfig.s('enabled');stdinEnabled:true
  stdout:SplitParser {onRead:data=>{try{
   const e=JSON.parse(data)
   if(e.type==='ready'){root.ready=true;root.capabilities=e.capabilities || ({});root.items=e.items;for(const p of root.pending)worker.write(JSON.stringify(p)+'\n');root.pending=[];root.send({action:'utilityPreferences'})}
   else if(e.type==='tray'){if(JSON.stringify(root.items)!==JSON.stringify(e.items))root.items=e.items}
   else if(e.type==='clipboard'){if(JSON.stringify(root.clips)!==JSON.stringify(e.items))root.clips=e.items}
   else if(e.type==='preview'){const next=Object.assign({},root.filePreviews);next[e.path]=e.preview;root.filePreviews=next}
   else if(e.type==='renamed'){root.items=e.items;root.transformPaths=root.transformPaths.map(p=>{const i=e.before.indexOf(p);return i>=0 ? e.after[i]:p})}
   else if(e.type==='vault')root.vaultInfo=e
   else if(e.type==='vaultNote')root.vaultNote(e.name,e.text,e.modified)
   else if(e.type==='utilityPreferences')root.utilityPreferences=e.values
   else if(e.type==='developerResult')root.developerResult(e.text,e.error)
   else if(e.type==='activities')root.activities=e.items
   else if(e.type==='storage')root.storageInfo=e
   else if(e.type==='applications')root.installedApps=e.items
   else if(e.type==='busy')root.fileBusy=e.value
   else if(e.type==='presets')root.transformPresets=e.items
   else if(e.type==='error'){root.noticeError=true;root.notice=e.message}
  }catch(_) {}}}
  onExited:{root.ready=false;if(IslandConfig.s('enabled'))retry.restart()}
 }
 function cancelTransform(){if(transformJob.running){jobCancelled=true;transformJob.running=false;notice=qsTr('Transformation cancelled')}}
 Process{
  id:transformJob;command:['@PYTHON@',Quickshell.shellPath('island-shelf/backend.py'),'--transform-job'];stdinEnabled:true
  onStarted:write(JSON.stringify(root.jobEvent)+'\n')
  stdout:SplitParser{onRead:data=>{try{const e=JSON.parse(data);if(e.type==='transformDone'){root.lastTransform=e;root.noticeError=false;root.send({action:'add',paths:e.paths});root.notice=qsTr('%1 files ready').arg(e.paths.length)}else if(e.type==='error' && !root.jobCancelled){root.noticeError=true;root.notice=e.message}}catch(_){}}}
  onExited:code=>{if(code!==0 && !root.jobCancelled && !root.notice)root.notice=qsTr('Transformation could not finish')}
 }
 IpcHandler{target:'shelf'
  function addFiles(encoded:string):string{try{root.add(JSON.parse(Qt.atob(encoded)));root.reveal(6);return 'queued'}catch(_){return 'invalid'}}
  function addFloatingFiles(encoded:string):string{try{root.add(JSON.parse(Qt.atob(encoded)));root.trayOpen=true;return 'queued'}catch(_){return 'invalid'}}
  function close():void{root.closeRequested()}
  function open(page:int):void{if(IslandBus.locked)return;root.reveal(Math.max(0,Math.min(14,page)))}
  function activity(encoded:string):string{try{root.send({action:'activity',activity:JSON.parse(encoded)});return 'queued'}catch(_){return 'invalid'}}
  function status():string{return JSON.stringify({ready:root.ready,files:root.items.length,activities:root.activities.length})}
 }
 Timer{interval:1000;running:root.activities.length>0 || root.awakeUntil>0;repeat:true;onTriggered:{root.now=Date.now();root.activities=root.activities.filter(a=>a.expires*1000>root.now)}}
 Timer{interval:3000;repeat:true;running:root.items.some(item=>item.tracked);onTriggered:root.send({action:'scanTracked'})}
 Timer{id:retry;interval:1500;onTriggered:worker.running=true}
 Timer {interval:5000;running:root.notice!=='';onTriggered:root.notice=''}
}
