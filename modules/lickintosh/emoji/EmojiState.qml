pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
 id:root
 property bool opened:false
 property bool pending:false
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
   filtered=list.map(emoji=>items.find(item=>item.emoji===emoji)).filter(Boolean)
  }else filtered=items.filter(item=>item.group===category)
 }
 onQueryChanged:filterDelay.restart()
 onCategoryChanged:refresh()
 Timer{id:filterDelay;interval:25;onTriggered:root.refresh()}
 function toggle(){if(opened || pending){close();return}pending=true;placement.running=true}
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
  id:placement
  command:['hyprctl','-j','--batch','activewindow;cursorpos;monitors']
  stdout:StdioCollector{onStreamFinished:{
   if(!root.pending)return
   try{
    const data=JSON.parse('['+text.trim().replace(/}\s*{/g,'},{').replace(/}\s*\[/g,'},[')+']')
    const active=data[0],point=data[1],mon=data[2].find(m=>m.id===active.monitor) || data[2].find(m=>m.focused) || data[2][0]
    root.target=active.address || '';root.screenName=mon?.name || ''
    root.pointer=Qt.point(point.x-(mon?.x || 0),point.y-(mon?.y || 0))
   }catch(_){root.target='';root.screenName='';root.pointer=Qt.point(200,100)}
   root.query='';root.category=-1;root.refresh();root.pending=false;root.opened=true
  }}
  onExited:if(root.pending){root.pending=false;root.opened=true}
 }
 Connections{target:SettingsPreferences;function onLockedChanged(){if(SettingsPreferences.locked)root.close()}}
}
