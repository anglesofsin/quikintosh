pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
 id:root
 property bool ready:false
 property bool loaded:false
 property var shipped:[]
 property var personal:[]
 property var thumbnails:({})
 property var versions:({})
 property var queued:({})
 property var pending:({})
 property var incoming:({})
 readonly property string userDir:ShellConfig.options.spotlight.indexing.wallpaperDir
 readonly property string cache:(Quickshell.env('XDG_CACHE_HOME') || Quickshell.env('HOME')+'/.cache')+'/lickintosh/wallpapers'
 function send(data){if(ready)worker.write(JSON.stringify(data)+'\n')}
 function refresh(){if(!ready || !ShellConfig.ready)return;send({action:'scan',group:'shipped',directory:Quickshell.shellDir+'/assets/wallpapers'});send({action:'scan',group:'personal',directory:userDir})}
 function request(path){if(!path || thumbnails[path]!==undefined || pending[path])return;pending[path]=true;queued[path]=true;queueTimer.restart()}
 function queueVisible(){const paths=Object.keys(queued);queued=({});if(paths.length)send({action:'thumbnails',paths:paths})}
 onUserDirChanged:if(loaded)refresh()
 Connections{target:ShellConfig;function onReadyChanged(){if(ShellConfig.ready)root.refresh()}}
 Timer{id:queueTimer;interval:24;onTriggered:root.queueVisible()}
 Timer{id:commit;interval:80;onTriggered:{root.thumbnails=Object.assign({},root.thumbnails,root.incoming);root.incoming=({})}}
 Process{
  id:worker;running:true;command:['@PYTHON@',Quickshell.shellDir+'/tools/wallpaper-library.py','--worker',root.cache]
  stdout:SplitParser{onRead:line=>{try{
   const event=JSON.parse(line)
   if(event.type==='ready'){root.ready=true;root.refresh()}
   else if(event.type==='inventory'){
    const map=Object.assign({},root.thumbnails)
    for(const item of event.items){
     if(root.versions[item.path]!==item.version){delete map[item.path];delete root.incoming[item.path];delete root.pending[item.path]}
     root.versions[item.path]=item.version
     if(item.thumb)map[item.path]=item.thumb
    }
    root.thumbnails=map
    if(event.group==='shipped')root.shipped=event.items;else{root.personal=event.items;root.loaded=true}
   }else if(event.type==='thumbnail' && root.versions[event.path]===event.version){delete root.pending[event.path];root.incoming[event.path]=event.url;if(!commit.running)commit.start()}
   else if(event.type==='deferred'){delete root.pending[event.path]}
   else if(event.type==='error')console.warn('Wallpapers:',event.message)
  }catch(error){console.warn('Wallpaper library:',error)}}}
 }
}
