pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
 id:root
 property var bank:({})
 property var files:({})
 property var origins:({})
 property var requested:({})
 property var waiting:[]
 property bool ready:false
 property bool selectionDirty:true
 property int pending:0
 property string lastError:''
 property int lastRenderMs:0
 readonly property string style:WidgetState.widgetStyle
 readonly property string appearance:style==='clear' ? 'clear':style==='tinted' ? 'tinted':AppearanceState.iconDark ? 'dark':'light'
 readonly property var palette:AppearanceState.iconPalette
 readonly property string role:AppearanceState.paletteRole
 readonly property var colors:({container:ShellConfig.options.appearance.iconTintMode==='auto' ? (AppearanceState.iconDark ? (palette.surface_container_lowest || '#15151b'):(palette[role+'_container'] || '#eeeef2')):String(AppearanceState.iconHigh),ink:ShellConfig.options.appearance.iconTintMode==='auto' ? (AppearanceState.iconDark ? (palette[role] || '#eeeeef'):(palette['on_'+role+'_container'] || '#222228')):String(AppearanceState.iconLow)})
 readonly property string signature:JSON.stringify({renderer:25,appearance:appearance,dark:AppearanceState.iconDark,colors:colors,strength:AppearanceState.strength})
 onSignatureChanged:{root.selectionDirty=true;pump.restart()}
 FileView{path:Quickshell.shellDir+'/layered-icons/bank.json';onLoaded:{try{root.bank=JSON.parse(text())}catch(e){root.lastError=String(e)}}}
 function normalize(name){return String(name || '').toLowerCase().replace(/\.(desktop|svg|png|ico|icns)$/,'').replace(/[ _]/g,'-')}
 function lookup(mode,source,name){
  const table=bank[mode] || ({})
  const base=String(source).split('/').pop().split('?')[0]
  for(const key of [normalize(name),normalize(base)])if(table[key])return table[key]
  return ''
 }
 function resolve(source,name){
  if(!source && !name)return ''
  let path=String(source || '')
  if(path.indexOf('/icon-materials-v2/')>=0)path=root.origins[path] || path
  // System symbols/media previews must never become application tiles.
  if(/(?:-symbolic\.|\/(?:status|actions|panel|mimetypes|devices)\/)/.test(path))return source
  const mode=AppearanceState.iconDark ? 'dark':'light'
  const native=lookup(mode,path,name)
  if(appearance==='light' || appearance==='dark')return native ? 'file://'+native:source
  const original=native ? 'file://'+native:path
  if(original.indexOf('image://icon/')!==0 && !/\.(svg|svgz|png|webp|ico|icns|xpm|jpg|jpeg|bmp|gif)$/i.test(original))return source
  const matte=lookup('clear',native || path,native ? '' : name)
  const key=original+'|'+matte+'|'+signature
  if(files[key])return 'file://'+files[key]
  if(!root.requested[key]){
   const job={key:key,source:original,matte:matte,geometry:(root.bank.vectors || ({}))[native] || '',appearance:appearance,dark:AppearanceState.iconDark,palette:colors,strength:AppearanceState.strength,signature:signature}
   // Distinct closures prevent Qt.callLater from coalescing different icons.
   Qt.callLater(function(){root.request(job)})
  }
  return original
 }
 function request(job){
  if(job.signature!==root.signature || requested[job.key] || files[job.key])return
  requested[job.key]=true;pending++
  waiting=waiting.concat([job]);pump.restart()
 }
 Timer{id:pump;interval:70;onTriggered:{
  if(!root.ready)return
  if(root.selectionDirty){worker.write(JSON.stringify({action:'select',signature:root.signature})+'\n');root.selectionDirty=false}
  const jobs=root.waiting;root.waiting=[]
  for(const job of jobs){if(job.signature===root.signature)worker.write(JSON.stringify(job)+'\n');else root.pending=Math.max(0,root.pending-1)}
 }}
 Process{id:worker;running:true;command:['@PYTHON@',Quickshell.shellDir+'/layered-icons/fast-renderer.py','@RSVG@'];stdinEnabled:true
  stdout:SplitParser{onRead:line=>{try{
   const data=JSON.parse(line)
   if(data.type==='ready'){const initial=data.index || ({});const reverse={};for(const key of Object.keys(initial))reverse['file://'+initial[key]]=key.split('|')[0];root.origins=reverse;root.ready=true;root.files=initial;root.selectionDirty=true;pump.restart()}
   else if(data.type==='rendered'){const reverse=Object.assign({},root.origins);reverse['file://'+data.path]=data.key.split('|')[0];root.origins=reverse;const next=Object.assign({},root.files);next[data.key]=data.path;root.files=next;root.pending=Math.max(0,root.pending-1);root.lastRenderMs=data.ms}
   else if(data.type==='cancelled'){root.pending=Math.max(0,root.pending-1);const next=Object.assign({},root.requested);delete next[data.key];root.requested=next}
   else if(data.type==='error'){root.pending=Math.max(0,root.pending-1);root.lastError=data.message;console.warn('Icon material:',data.message)}
  }catch(error){console.warn('Icon material protocol',error)}}}
  onExited:{root.ready=false;root.pending=0;root.waiting=[]}
 }
}
