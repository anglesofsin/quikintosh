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
 property string selectionText:''
 property string selectionError:''
 property point selectionPosition:Qt.point(0,0)
 property bool selectionOpen:false
 property bool selectionHovered:false
 function clearSelection(){selectionOpen=false;selectionText=''}
 Process{id:selectionWatch;onStarted:root.selectionError='';command:['wl-paste','--primary','--type','text','--watch',root.pythonExecutable,Quickshell.shellPath('island-shelf/selection_bridge.py')];running:root.utilityPreferences.selectionActionsEnabled===true && !IslandBus.locked
  stdout:SplitParser{onRead:line=>{try{const e=JSON.parse(line);root.selectionText=e.text;if(!e.text.trim())root.clearSelection();else selectionQuiet.restart()}catch(_){}}}
  onExited:code=>{if(code!==0 && root.utilityPreferences.selectionActionsEnabled)root.selectionError=qsTr('Primary selection is unavailable on this session.')}
 }
 Timer{id:selectionQuiet;interval:160;onTriggered:{if(root.selectionText && !selectionLocate.running)selectionLocate.running=true}}
 Process{id:selectionLocate;command:['hyprctl','cursorpos','-j'];stdout:StdioCollector{onStreamFinished:{try{const p=JSON.parse(text);root.selectionPosition=Qt.point(p.x,p.y);root.selectionOpen=!!root.selectionText && !IslandBus.locked}catch(_){}}}}
 property bool ringArmed:false
 property bool ringRequested:false
 property bool ringOpen:false
 property point ringPosition:Qt.point(960,540)
 property int ringSelected:-1
 readonly property var ringCatalogue:[
  {key:'spotlight',title:qsTr('Spotlight'),icon:'search',ipc:'spotlight'},
  {key:'files',title:qsTr('Files'),icon:'inbox',page:6},
  {key:'clipboard',title:qsTr('Clipboard'),icon:'clipboard',page:7},
  {key:'media',title:qsTr('Now Playing'),icon:'music',page:3},
  {key:'transcribe',title:qsTr('Voice Transcription'),icon:'mic',widget:'transcribe'},
  {key:'calculator',title:qsTr('Calculator'),icon:'grid',command:'quickintosh-calculator'},
  {key:'emoji',title:qsTr('Emoji Picker'),icon:'type',ipc:'emoji'},
  {key:'settings',title:qsTr('Settings'),icon:'settings',ipc:'settings'},
  {key:'terminal',title:qsTr('Terminal'),icon:'type',widget:'terminal'},
  {key:'focus',title:qsTr('Focus'),icon:'clock',widget:'focus'},
  {key:'notes',title:qsTr('Notes'),icon:'edit-3',widget:'notes'},
  {key:'weather',title:qsTr('Weather'),icon:'cloud',page:1},
  {key:'audio',title:qsTr('Audio Control'),icon:'volume-2',page:10},
  {key:'storage',title:qsTr('Storage'),icon:'hard-drive',page:14},
  {key:'calendar',title:qsTr('Calendar'),icon:'calender',widget:'calendar'},
  {key:'notifications',title:qsTr('Notifications'),icon:'bell',page:4},
  {key:'awake',title:qsTr('Stay Awake'),icon:'coffee',page:12},
  {key:'camera',title:qsTr('Camera'),icon:'camera',page:5},
  {key:'queue',title:qsTr('Playing Next'),icon:'list',widget:'queue'},
  {key:'selection',title:qsTr('Selection Actions'),icon:'copy',widget:'selection'},
  {key:'developer',title:qsTr('Developer Tools'),icon:'clipboard',widget:'developer'},
  {key:'teleprompter',title:qsTr('Teleprompter'),icon:'type',widget:'teleprompter'},
  {key:'vault',title:qsTr('Obsidian Vault'),icon:'edit-3',widget:'vault'},
  {key:'breather',title:qsTr('Break Reminders'),icon:'coffee',widget:'breather'}]
 readonly property var ringKeys:{const saved=utilityPreferences.ringActions || [];return ringCatalogue.map((a,i)=>saved[i] || a.key)}
 signal detailRequested(string key)
 function openDetail(key){detailRequested(key);reveal(13)}
 function showRing(){if(IslandBus.locked)return;ringRequested=true;ringArmed=false;ringSelected=-1;if(!ringLocate.running)ringLocate.running=true}
 function activateRing(index){const action=ringCatalogue.find(a=>a.key===ringKeys[index]);ringRequested=false;ringOpen=false;ringSelected=-1;if(!action)return;if(action.ipc)Quickshell.execDetached(['quickintosh','ipc','call','rice',action.ipc]);else if(action.command)Quickshell.execDetached([action.command]);else if(action.widget)openDetail(action.widget);else reveal(action.page)}
 Process{id:ringLocate;command:['hyprctl','cursorpos','-j'];stdout:StdioCollector{onStreamFinished:{try{const p=JSON.parse(text);root.ringPosition=Qt.point(p.x,p.y)}catch(_){root.ringPosition=Qt.point(960,540)}root.ringOpen=root.ringRequested}}}
 IpcHandler{target:'actionRing';function show():void{root.showRing()}function release():void{root.activateRing(root.ringSelected)}function close():void{root.ringRequested=false;root.ringOpen=false}function settings():void{root.openDetail('ring')}function status():string{return JSON.stringify({open:root.ringOpen,rings:root.utilityPreferences.ringCount || 1,selected:root.ringSelected})}}
 property point basketPosition:Qt.point(0,0)
 property bool basketOpen:false
 readonly property bool trayShakeEnabled:IslandConfig.s('trayShakeEnabled')!==false
 Connections{target:Hyprland;function onRawEvent(event){if(event.name==='configreloaded'){Quickshell.execDetached([root.pythonExecutable,Quickshell.shellPath('island-shelf/ensure_ring_shortcut.py')]);return}if(event.name==="quickintosh-drag-end"){basketDismiss.restart();return}if(event.name!=="quickintosh-drag-shake" || !root.trayShakeEnabled || IslandBus.locked)return;const point=event.data.split(",");root.basketPosition=Qt.point(Number(point[0]),Number(point[1]));root.basketOpen=true}}
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
 readonly property var widgetPriority:['media','weather','calendar','focus','notes','files','clipboard','audio','notifications','performance','queue','camera','storage','awake','calculator','emoji','spotlight','applications','transcribe','terminal','vault','developer','breather','teleprompter','ring','selection','jobs','activities','settings']
 function orderWidgets(items){const recent=utilityPreferences.widgetRecent || [];return items.slice().sort((a,b)=>{const x=recent.indexOf(a.key),y=recent.indexOf(b.key);if(x>=0 || y>=0)return x<0 ? 1:y<0 ? -1:x-y;return widgetPriority.indexOf(a.key)-widgetPriority.indexOf(b.key)})}
 function useWidget(key){const recent=[key].concat((utilityPreferences.widgetRecent || []).filter(k=>k!==key)).slice(0,40);utilityPreferences=Object.assign({},utilityPreferences,{widgetRecent:recent});send({action:'utilityPreferences',values:{widgetRecent:recent}})}
 function beginEditing(){reveal(0);editing=true}
 property var utilityPreferences:({})
 property var capabilities:({})
 property var installedApps:[]
 property var queueData:({player:'',items:[],supported:false})
 property var appJobEvent:({})
 property var appPendingEvent:null
 readonly property bool appBusy:(appJob.running && appJobEvent.action==='uninstall') || appPendingEvent?.action==='uninstall'
 property var appDataReview:({})
 signal applicationSuggested(string id)
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
 Connections{target:IslandBus;function onLockedChanged(){if(IslandBus.locked){root.clearSelection();root.playerOpen=false;root.ringRequested=false;root.ringOpen=false;root.trayOpen=false;root.basketOpen=false;root.editing=false;root.editorOwners=({});root.interactionCount=0;root.menuCount=0}}}
 signal jobHistory(var data)
 signal developerResult(string text,string error)
 signal closeRequested()
 signal reveal(int page)
 function send(event){if(['applicationData','uninstall'].includes(event.action)){if(appJob.running){if(appPendingEvent?.action!=='uninstall')appPendingEvent=event}else{appJobEvent=event;appJob.running=true}return}if(event.action==='archive' || event.action==='unzip')event=Object.assign({},event,{action:'transform',operation:event.action==='archive' ? 'zip':'unzip'});if(event.action==='transform'){if(transformJob.running)return;jobEvent=event;jobCancelled=false;notice='';noticeError=false;transformJob.running=true;return}if(ready)worker.write(JSON.stringify(event)+'\n');else pending=pending.concat([event])}
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
   else if(e.type==='utilityPreferences'){root.utilityPreferences=e.values;if(!e.values.selectionActionsEnabled)root.clearSelection()}
   else if(e.type==='developerResult')root.developerResult(e.text,e.error)
   else if(e.type==='activities')root.activities=e.items
   else if(e.type==='storage')root.storageInfo=e
   else if(e.type==='applications'){root.installedApps=e.items;if(e.suggested)root.applicationSuggested(e.suggested)}
   else if(e.type==='jobHistory')root.jobHistory(e)
   else if(e.type==='queue')root.queueData=e
   else if(e.type==='applicationData')root.appDataReview=e
   else if(e.type==='busy')root.fileBusy=e.value
   else if(e.type==='presets')root.transformPresets=e.items
   else if(e.type==='error'){root.noticeError=true;root.notice=e.message}
  }catch(_) {}}}
  onExited:{root.ready=false;if(IslandConfig.s('enabled'))retry.restart()}
 }
 function cancelTransform(){if(transformJob.running){jobCancelled=true;transformJob.running=false;notice=qsTr('Transformation cancelled')}}
 Process{id:appJob;command:[root.pythonExecutable,Quickshell.shellPath('island-shelf/backend.py'),'--application-job'];stdinEnabled:true
  onStarted:write(JSON.stringify(root.appJobEvent)+'\n')
  stdout:SplitParser{onRead:line=>{try{const e=JSON.parse(line);if(e.type==='applications'){root.installedApps=e.items;root.noticeError=false;root.notice=qsTr('Application removed')}else if(e.type==='applicationData')root.appDataReview=e;else if(e.type==='error'){root.noticeError=true;root.notice=e.message}}catch(_){}}}
  onExited:{if(root.appPendingEvent){root.appJobEvent=root.appPendingEvent;root.appPendingEvent=null;Qt.callLater(()=>appJob.running=true)}}
 }
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
