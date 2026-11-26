pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
 id:root
 property bool opened:false
 property bool pending:false
 property bool workerReady:false
 property int requestSerial:0
 property double requestedAt:0
 property real placementMs:0
 IpcHandler{target:"emoji";function status():string{return JSON.stringify({opened:root.opened,pending:root.pending,items:root.items.length,caret:root.caretAnchor,placementMs:root.placementMs})}}
 property bool caretAnchor:false
 property string screenName:''
 property point pointer:Qt.point(0,0)
 property string target:''
 property var pendingPaste:null
 property var pasteCommand:[]
 Process{id:pasteProcess;command:root.pasteCommand;stderr:StdioCollector{onStreamFinished:if(text.trim())console.warn('Emoji insertion:',text.trim())}}
 function finishPaste(){if(!pendingPaste)return;const data=pendingPaste;pendingPaste=null;pasteCommand=['@PYTHON@',Quickshell.shellDir+'/emoji/paste.py',data.value,data.target];pasteProcess.running=true}
 property string query:''
 property int category:-1
 property int tone:0
 property var items:[]
 property var filtered:[]
 property var recent:[]
 readonly property var groups:['Smileys & People','Animals & Nature','Food & Drink','Activities','Travel & Places','Objects','Symbols','Flags']
 readonly property var categories:[
  {name:'Frequently used',icon:'󰥔',group:-1},
  {name:'Smileys & Emotion',icon:'󰞅',group:0},{name:'People & Body',icon:'󰀄',group:1},
  {name:'Animals & Nature',icon:'󰄛',group:2},{name:'Food & Drink',icon:'󰉛',group:3},
  {name:'Travel & Places',icon:'󰄋',group:4},{name:'Activities',icon:'󰒸',group:5},
  {name:'Objects',icon:'󰌵',group:6},{name:'Symbols',icon:'󰣐',group:7},{name:'Flags',icon:'󰈿',group:8}]
 function normalize(value){return String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()}
 function label(item){return I18n.lang.startsWith('pt') ? item.pt:item.name}
 function glyph(item){return item.tones[String(root.tone)] || item.emoji}
 function refresh(){
  const words=normalize(query).trim().split(/\s+/).filter(Boolean)
  if(words.length)filtered=items.filter(item=>words.every(word=>item.search.includes(word) || item.emoji===word))
  else if(category<0){
   const defaults=['✅','❤️‍🔥','💻','❤️','😂','😍','😒','👌','☺️','😊','😘','😭','😩','💕','😔','😄','😁','😳','👍','✌️','😉','😌','🤷','🙈','😎','🎶','👀','😑','😴','😀']
   const list=recent.length ? recent:defaults
   const preferred=list.map(emoji=>items.find(item=>item.emoji===emoji)).filter(Boolean)
   filtered=preferred.concat(items.filter(item=>item.group===0 && !list.includes(item.emoji)))
  }else filtered=items.filter(item=>item.group===category)
 }
 onQueryChanged:filterDelay.restart()
 onCategoryChanged:refresh()
 Timer{id:filterDelay;interval:25;onTriggered:root.refresh()}
 function toggle(){if(opened || pending){close();return}pending=true;requestedAt=Date.now();requestSerial++;if(workerReady)placement.write(JSON.stringify({serial:requestSerial})+'\n')}
 function present(data){if(!pending || data.serial!==requestSerial)return;placementMs=Date.now()-requestedAt;target=data.target;screenName=data.screen;pointer=Qt.point(data.x,data.y);caretAnchor=data.caret;query='';category=-1;refresh();pending=false;opened=true}
 function close(){pending=false;opened=false}
 function choose(item){
  const value=glyph(item),destination=target
  recent=[item.emoji].concat(recent.filter(e=>e!==item.emoji)).slice(0,80)
  save.restart();pendingPaste={value:value,target:destination};close()
 }
 FileView {path:Quickshell.shellDir+'/emoji/catalog.json';onLoaded:{try{root.items=JSON.parse(text()).items;root.refresh()}catch(e){console.warn('Emoji catalog:',e)}}}
 FileView {id:history;path:Quickshell.env('HOME')+'/.local/state/lickintosh/emoji/recent.json'
  onLoaded:{try{const data=JSON.parse(text());root.recent=Array.isArray(data.recent) ? data.recent.filter(e=>typeof e==='string').slice(0,80):[];root.tone=Math.max(0,Math.min(5,Number(data.tone)||0));root.refresh()}catch(_){}}
 }
 Timer{id:save;interval:100;onTriggered:history.setText(JSON.stringify({recent:root.recent,tone:root.tone}))}
 onToneChanged:save.restart()
 Process {
  id:placement;running:true;stdinEnabled:true
  command:['@PYTHON@',Quickshell.shellDir+'/emoji/placement.py']
  stdout:SplitParser{onRead:line=>{try{const data=JSON.parse(line);if(data.type==='ready'){root.workerReady=true;if(root.pending)placement.write(JSON.stringify({serial:root.requestSerial})+'\n')}else root.present(data)}catch(error){console.warn('Emoji placement:',error)}}}
  onExited:{root.workerReady=false;if(root.pending)root.present({serial:root.requestSerial,target:'',screen:'',x:200,y:100,caret:false});workerRestart.restart()}
 }
 Timer{id:workerRestart;interval:1000;onTriggered:placement.running=true}
 Connections{target:SettingsPreferences;function onLockedChanged(){if(SettingsPreferences.locked)root.close()}}
}
