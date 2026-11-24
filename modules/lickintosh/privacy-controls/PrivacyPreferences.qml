pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
Singleton{
 id:root
 property bool ready:false
 property alias enabled:adapter.enabled
 property alias island:adapter.island
 property alias controlCenter:adapter.controlCenter
 property alias hideFullscreen:adapter.hideFullscreen
 property alias showExpanded:adapter.showExpanded
 property alias categories:adapter.categories
 property alias exceptions:adapter.exceptions
 readonly property var kinds:['camera','screen','mic','audio']
 readonly property var titles:({camera:'Camera',mic:'Microphone',screen:'Screen Sharing',audio:'System Audio'})
 function category(kind){return Object.assign({enabled:true,color:({camera:'#30d158',mic:'#ff9f0a',screen:'#409cff',audio:'#bf5af2'})[kind],priority:kinds.indexOf(kind)},categories[kind] || {})}
 function setCategory(kind,key,value){const next=Object.assign({},categories),entry=category(kind);if(key==='priority'){for(const other of kinds){if(other!==kind && category(other).priority===value)next[other]=Object.assign({},category(other),{priority:entry.priority})}}entry[key]=value;next[kind]=entry;categories=next}
 function rule(id,kind,app){const matches=e=>e.id.toLowerCase()===id.toLowerCase() || e.id.toLowerCase()===(app || '').toLowerCase();return exceptions.find(e=>matches(e) && e.kind===kind)?.mode || exceptions.find(e=>matches(e) && e.kind==='all')?.mode || 'default'}
 function setRule(id,app,kind,mode){const next=exceptions.filter(e=>!(e.id===id && e.kind===kind));if(mode!=='default')next.push({id:id,app:app,kind:kind,mode:mode});exceptions=next}
 function allowed(entry){const mode=rule(entry.id,entry.kind,entry.app);return mode==='show' || (mode!=='hide' && category(entry.kind).enabled)}
 Timer{id:save;interval:150;onTriggered:file.writeAdapter()}
 Timer{id:reload;interval:100;onTriggered:file.reload()}
 FileView{id:file;path:Quickshell.env('HOME')+'/.config/lickintosh/core/privacy-indicators.json';watchChanges:true
  onFileChanged:reload.restart()
  onLoaded:root.ready=true
  onLoadFailed:error=>{if(error===FileViewError.FileNotFound){root.ready=true;file.writeAdapter()}}
  onAdapterUpdated:if(root.ready)save.restart()
  JsonAdapter{id:adapter
   property bool enabled:true
   property bool island:true
   property bool controlCenter:true
   property bool hideFullscreen:false
   property bool showExpanded:false
   property var categories:({})
   property list<var> exceptions:[]
  }
 }
}
