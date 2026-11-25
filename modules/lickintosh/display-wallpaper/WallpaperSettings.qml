pragma Singleton
import QtQuick
import Quickshell
import qs.services
Singleton{
 id:root
 readonly property var options:ShellConfig.options.wallpaper
 readonly property var folders:options.folders
 readonly property var favorites:options.favorites
 readonly property var perDisplay:options.perDisplay
 function itemFor(name){return perDisplay[name] || {}}
 function pathFor(name){const c=itemFor(name);return (Theme.isDark ? c.pathDark:c.pathLight) || c.path || ''}
 function videoFor(name){const c=itemFor(name);return (Theme.isDark ? c.pathDark:c.pathLight) ? '' : (c.videoPath || '')}
 function set(name,key,value){if(!name){options[key]=value;return}const all=Object.assign({},perDisplay),entry=Object.assign({},all[name] || {});entry[key]=value;all[name]=entry;options.perDisplay=all}
 function apply(name,target,item){
  const key=target==='lockscreen' ? 'lockscreenPath':target==='desktopLight' ? 'pathLight':target==='desktopDark' ? 'pathDark':'path'
  if(key==='lockscreenPath'){if(!item.video)options.lockscreenPath=item.path;return}
  if(item.video){set(name,'videoPath',item.path);set(name,'pathLight','');set(name,'pathDark','')}
  else{if(key==='path')set(name,'videoPath','');set(name,key,item.path)}
 }
 function inherit(name){const all=Object.assign({},perDisplay);delete all[name];options.perDisplay=all}
 function favorite(path){options.favorites=favorites.includes(path) ? favorites.filter(p=>p!==path):favorites.concat([path])}
 function addFolder(path){if(!folders.includes(path))options.folders=folders.concat([path])}
 function removeFolder(path){options.folders=folders.filter(p=>p!==path)}
 function next(){const list=WallpaperLibrary.personal.filter(i=>!i.video && (!options.shuffleFavorites || favorites.includes(i.path)));if(!list.length)return;let index=list.findIndex(i=>i.path===options.path);index=options.shuffleRandom ? Math.floor(Math.random()*list.length):(index+1)%list.length;apply('','desktop',list[index])}
 Timer{interval:Math.max(15,root.options.shuffleSeconds)*1000;repeat:true;running:ShellConfig.ready && root.options.shuffleEnabled;onTriggered:root.next()}
}
