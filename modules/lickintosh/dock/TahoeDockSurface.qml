import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.services
import qs.components.glass
Scope {
 id:root
 function hiddenApp(value){return /kde.?connect/i.test(String(value || ''))}
 function blocked(key){return options.recentAppBlacklist.some(item=>String(item.key || item).toLowerCase()===String(key).toLowerCase())}
 function removeRecent(key,name,permanent){if(permanent && !blocked(key))options.recentAppBlacklist=options.recentAppBlacklist.concat([{key:key,name:name || key}]);recentApps=recentApps.filter(app=>app.key!==key);send({action:'forget',key:key})}
 function focusWindow(address){send({action:'focusWindow',address:address})}
 function requestEmptyTrash(){if(options.confirmEmptyTrash)trashConfirm=true;else send({action:'empty'})}
 Connections{target:DockDrag;function onStackDraggingChanged(){if(DockDrag.stackDragging){root.revealed=true;hideDelay.stop()}else if(root.options.hoverToReveal)hideDelay.restart()}function onDesktopDraggingChanged(){if(DockDrag.desktopDragging){root.revealed=true;hideDelay.stop()}else if(root.options.hoverToReveal)hideDelay.restart()}}
 required property var controller
 readonly property var options:ShellConfig.options.dockAppearance
 readonly property bool vertical:options.position!=='bottom'
 readonly property int size:Math.round(options.iconSize*options.iconScale)
 property real lensPointer:0
 property bool lensHovered:false
 property real lensStrength:options.magnificationEnabled && lensHovered && !dockDragging && !DockDrag.desktopDragging && !DockDrag.stackDragging && !stackOpen && !stackPending && !controller.menuVisible ? 1:0
 Behavior on lensStrength{NumberAnimation{duration:140;easing.type:Easing.OutCubic}}
 readonly property var lensLayout:{
  const base=[];let cursor=0
  for(const entry of root.entries){const span=entry.kind==='separator' ? 12:root.actualSize+(root.vertical ? 12:8);base.push({center:cursor+span/2,span:span,separator:entry.kind==='separator'});cursor+=span+5}
  const length=Math.max(0,cursor-5),origin=((root.vertical ? dock.height:dock.width)-length)/2
  const zooms=[];let total=0
  for(const cell of base){const distance=Math.abs((root.lensPointer-origin)-cell.center)/(root.actualSize+13);const weight=distance<2.6 ? (1+Math.cos(Math.PI*distance/2.6))/2:0;const zoom=cell.separator ? 1:1+Math.max(0,root.options.magnification-1)*weight*root.lensStrength;zooms.push(zoom);total+=root.actualSize*(zoom-1)}
  const allowed=Math.max(0,root.available-length-24)
  if(total>allowed && total>0){const factor=allowed/total;for(let i=0;i<zooms.length;i++)zooms[i]=1+(zooms[i]-1)*factor;total=allowed}
  const offsets=[];let extra=0
  for(let i=0;i<base.length;i++){const width=root.actualSize*(zooms[i]-1);offsets.push(extra+width/2-total/2);extra+=width}
  return {zooms:zooms,offsets:offsets,extra:total}
 }
 property bool dockDragging:false
 property string draggedKey:''
 property real dragPointerOrigin:0
 property int dragOriginIndex:0
 function dragItem(entry,tile,delta,outside){
  if(!entry.pinned)return
  if(!dockDragging){dockDragging=true;draggedKey=entry.key;dragOriginIndex=entry.index}
  const target=Math.max(0,Math.min(controller.pinnedApps.length-1,dragOriginIndex+Math.round(delta/(root.actualSize+13))))
  const current=controller.pinnedApps.findIndex(a=>controller.pinnedKey(a)===draggedKey)
  if(current>=0 && current!==target)controller.reorderPinnedApps(current,target)
 }
 // Keep the existing shared geometry inventory updating even while hidden.
 // This subscription creates no screencopy surfaces or additional IPC process.
 Loader {
  id:windowWatcher
  active:root.options.hoverToReveal
  sourceComponent:DockOcclusion {
   property bool subscribed:false
   Component.onCompleted:{subscribed=true;GlassTracker.captureUsers++;GlassTracker.refreshMonitorSnapshot();GlassTracker.refreshWindows()}
   Component.onDestruction:if(subscribed)GlassTracker.captureUsers--
   clients:Hyprland.toplevels.values.map(client=>client.lastIpcObject)
   monitors:GlassTracker.monitorSnapshots.map(m=>{
    const live=Hyprland.monitors.values.find(item=>item.name===m.name)
    return Object.assign({},m,{activeWorkspace:{id:live?.activeWorkspace?.id ?? m.activeWorkspace?.id}})
   })
   monitorName:dock.screen?.name || ''
   shellScale:Number(Quickshell.env('QT_SCALE_FACTOR') || 1)
   // Use resting bounds: hover magnification and the hide animation must not
   // change collision detection and cause the dock to oscillate in/out.
   dockRect:Qt.rect(root.origin.x+(root.vertical ? (options.position==='right' ? dock.width-root.thickness-8:0):(dock.width-tiles.implicitWidth-24)/2),
                    root.origin.y+(root.vertical ? (dock.height-tiles.implicitHeight-24)/2:dock.height-root.thickness-8),
                    root.vertical ? root.thickness+8:tiles.implicitWidth+24,
                    root.vertical ? tiles.implicitHeight+24:root.thickness+8)
  }
 }
 IpcHandler {
  target:'dock'
  function state():string {
   const r=windowWatcher.item?.dockRect
   return JSON.stringify({automatic:options.hoverToReveal,visible:dock.shown,
    obstructed:!!windowWatcher.item?.blocked,monitor:dock.screen?.name,
    rectangle:r ? [r.x,r.y,r.width,r.height]:null,
    scale:windowWatcher.item?.shellScale || 1})
  }
 }
 property bool revealed:false
 property int hoveredIndex:-1
 property string hoverLabel:''
 property var recentApps:[]
 property int trashCount:0
 property var files:[]
 property string folder:''
 property string stackTitle:''
 property bool stackOpen:false
 property bool stackPending:false
 property bool stackMenuOnly:false
 property bool stackDropMode:false
 property string dragHoveredPath:''
 property var folderPreviews:({})
 property var thumbnails:({})
 property real frozenZoomIndex:-1
 property bool trashConfirm:false
 property bool clearRecentConfirm:false
 property bool workerReady:false
 property var stackPoint:Qt.point(0,0)
 readonly property var pinnedKeys:controller.pinnedApps.map(e=>controller.pinnedKey(e))
 function same(a,b){return a && b && (a.indexOf(b)>=0 || b.indexOf(a)>=0)}
 function appIcon(name){return controller.resolveIcon(name)}
 function themeIcon(name){return 'file://'+Quickshell.shellDir+'/assets/icons_desktop/MacTahoe-light/places/scalable/'+name+'.svg'}
 function send(data){if(workerReady)worker.write(JSON.stringify(data)+'\n')}
 function preference(path,key){const setting=options.stackPreferences.find(p=>p.path===path);return setting && setting[key]!==undefined ? setting[key] : options[key==='display' ? 'stackDisplay' : key==='view' ? 'stackView' : 'stackSort']}
 function setPreference(path,key,value){let prefs=options.stackPreferences.slice();let i=prefs.findIndex(p=>p.path===path);const entry=i>=0 ? Object.assign({},prefs[i]) : {path:path};entry[key]=value;if(i>=0)prefs[i]=entry;else prefs.push(entry);options.stackPreferences=prefs;refreshPreviews();if(stackOpen && !stackMenuOnly && path===folder)send({action:'list',folder:path,sort:preference(path,'sort')})}
 function openStack(path,title,point,dropMode){stackDropMode=!!dropMode;stackMenuOnly=false;folder=path;stackTitle=title;stackPoint=point;frozenZoomIndex=hoveredIndex;stackPending=true;send({action:'list',folder:path,sort:preference(path,'sort')})}
 function dropFiles(urls,operation,destination){
  if(destination==='trash')send({action:'trash',urls:urls})
  else if(destination==='recent')send({action:'recentDrop',urls:urls})
  else QuickLookState.transfer(urls,destination,operation)
 }
 function operationFor(drop){const fmt='application/x-lickintosh-file-action';const value=drop.formats.indexOf(fmt)!==-1 ? drop.getDataAsString(fmt):'';return ['copy','move','link'].includes(value) ? value:drop.proposedAction===Qt.MoveAction ? 'move':drop.proposedAction===Qt.LinkAction ? 'link':'copy'}
 function fileAction(operation,entries,name,destination){
  const paths=entries.map(e=>e.trashUri || e.path)
  if(operation==='open'){Quickshell.execDetached(['lickintosh-quicklook'].concat(entries.map(e=>e.path)));root.stackOpen=false}
  else if(operation==='preview'){QuickLookState.show(entries.map(e=>e.path),0,'stack')}
  else if(operation==='chooseApp' && entries.length){QuickLookState.send({action:'chooseApp',path:entries[0].path});root.stackOpen=false}
  else if(operation==='reveal'){Quickshell.execDetached(['lickintosh-finder','--select'].concat(paths));root.stackOpen=false}
  else if(operation==='removeRecent'){send({action:'removeRecentFiles',paths:entries.map(e=>e.path)});stackRefresh.restart();previewsDelay.restart()}
  else QuickLookState.fileAction(operation,paths,name,destination)
 }
 function refreshPreviews(){if(!workerReady)return;const folders=['recent',Quickshell.env('HOME')+'/Downloads'].concat(controller.pinnedFiles.filter(f=>f.isDir).map(f=>f.path));for(const path of folders)send({action:'previews',folders:[path],sort:preference(path,'sort')})}
 function updateThumbnail(path,url){const map=Object.assign({},thumbnails);map[path]=url;thumbnails=map}

 function activate(entry,modifiers,tile){
  if(entry.kind==='pin'){options.hoverToReveal=!options.hoverToReveal;return}
  if(entry.kind==='trash'){const p=tile.mapToItem(dock.contentItem,tile.width/2,tile.height/2);openStack('trash','Trash',Qt.point(p.x+root.origin.x,p.y+root.origin.y));return}
  if(entry.kind==='stack'){const p=tile.mapToItem(dock.contentItem,tile.width/2,tile.height/2);openStack(entry.path,entry.name,Qt.point(p.x+root.origin.x,p.y+root.origin.y));return}
  if(entry.kind==='file'){send({action:'recent',path:entry.path});Quickshell.execDetached(['xdg-open',entry.path]);return}
  if((modifiers & Qt.ShiftModifier) && entry.cmd){controller.launchDetached(entry.cmd);return}
  if(entry.instances && entry.instances.length){controller.cycleWindow(entry.key,entry.instances);return}
  if(entry.cmd==='__launchpad__'){LauncherState.openApplications();return}
  if(entry.cmd==='__settings-app__' || (!entry.cmd && entry.name==='Settings')){SettingsLauncher.open('');return}
  const app=DesktopEntries.heuristicLookup(entry.key || entry.cmd)
  if(!entry.pinned && app)app.execute();else controller.launchDetached(entry.cmd || entry.key)
 }
 function menu(entry,tile){
  if(entry.kind==='stack'){const p=tile.mapToItem(dock.contentItem,tile.width/2,tile.height/2);folder=entry.path;stackTitle=entry.name;stackPoint=Qt.point(p.x+root.origin.x,p.y+root.origin.y);frozenZoomIndex=hoveredIndex;stackMenuOnly=true;stackOpen=true;return}
  const p=tile.mapToItem(dock.contentItem,tile.width/2,0)
  controller.openContextMenu(p.x+root.origin.x,Math.max(100,p.y+root.origin.y+35),entry.name,entry.key || entry.path || '',!!entry.pinned,entry.instances || [],entry.icon,entry.kind==='trash' ? 'trash' : entry.kind==='file' || entry.kind==='stack' ? 'file' : 'app')
  controller.menuRecentKey=entry.recent ? entry.key : ''
 }
 readonly property var entries:{
  let list=[];const groups=controller.groupedClients.filter(group=>!hiddenApp(group.key) && !hiddenApp(group.displayName))
  for(let i=0;i<controller.pinnedApps.length;i++){
   const a=controller.pinnedApps[i];if(hiddenApp(a.cmd) || hiddenApp(a.name))continue;const instances=controller.pinnedGroupInstances(a)
   list.push({kind:'app',name:a.name,cmd:a.cmd,key:controller.pinnedKey(a),icon:controller.pinnedIconFor(a),pinned:true,index:i,running:instances.length>0,instances:instances})
  }
  for(const g of groups){if(pinnedKeys.some(k=>same(k,g.key)))continue;list.push({kind:'app',name:g.displayName,key:g.key,cmd:g.key,icon:g.iconPath,running:true,instances:g.instances})}
  const recent=options.showRecentApps ? recentApps.filter(a=>!hiddenApp(a.key) && !hiddenApp(a.name) && !blocked(a.key) && !pinnedKeys.some(k=>same(k,a.key)) && !groups.some(g=>same(g.key,a.key))).slice(0,options.recentAppCount) : []
  if(recent.length){list.push({kind:'separator'});for(const a of recent)list.push({kind:'app',name:a.name,key:a.key,cmd:a.key,icon:appIcon(a.key) || a.icon,running:false,instances:[],recent:true})}
  if(!options.minimizeToAppIcon){
   const minimized=[]
   for(const g of groups)for(const c of g.instances)if(c.wsName && c.wsName.indexOf('special:hidden_')===0)minimized.push({kind:'app',name:c.title || g.displayName,key:g.key,icon:g.iconPath,running:false,instances:[c]})
   if(minimized.length){list.push({kind:'separator'});list=list.concat(minimized)}
  }
  if(controller.pinnedFiles.length || options.showDownloads || options.showRecentFiles || options.showTrash)list.push({kind:'separator'})
  for(const f of controller.pinnedFiles)list.push({kind:f.isDir ? 'stack':'file',name:f.path.split('/').pop(),path:f.path,icon:controller.fileIconPath(f),stack:!!f.isDir})
  if(options.showRecentFiles)list.push({kind:'stack',name:'Recent Files',path:'recent',stack:true,icon:themeIcon('folder')})
  if(options.showDownloads)list.push({kind:'stack',name:'Downloads',path:Quickshell.env('HOME')+'/Downloads',stack:true,icon:themeIcon('folder-download')})
  if(options.showTrash)list.push({kind:'trash',name:trashCount ? 'Trash · '+trashCount+' items' : 'Trash',icon:themeIcon(trashCount ? 'user-trash-full':'user-trash')})
  if(options.showPinButton)list.push({kind:'pin',name:options.hoverToReveal ? 'Keep Dock visible':'Hide Dock automatically',icon:IconResolver.byName('view-pin') || IconResolver.byName('view-restore')})
  for(const entry of list)if(entry.kind==='stack'){entry.previews=folderPreviews[entry.path] || [];entry.display=preference(entry.path,'display')}
  return list
 }
 readonly property real available:vertical ? dock.screen.height-100 : dock.screen.width-24
 readonly property real actualSize:Math.min(size,Math.max(24,(available-entries.length*7-24)/Math.max(1,entries.length)))
 readonly property real thickness:actualSize+34
 readonly property point origin:Qt.point(options.position==='right' ? dock.screen.width-dock.width : 0,vertical ? 0 : dock.screen.height-dock.height)
 Process {
  id:worker;running:true;stdinEnabled:true
  command:['@PYTHON@',Quickshell.shellDir+'/tahoedock/backend.py']
  stdout:SplitParser {onRead:line=>{
   try{
    const e=JSON.parse(line)
    if(e.type==='ready'){root.workerReady=true;root.recentApps=e.apps;root.trashCount=e.trash;root.remember();root.refreshPreviews()}
    else if(e.type==='apps')root.recentApps=e.apps
    else if(e.type==='files' && e.folder===root.folder && (root.stackPending || root.stackOpen)){root.files=e.items;root.stackPending=false;root.stackOpen=true}
    else if(e.type==='preview'){const next=Object.assign({},root.folderPreviews);next[e.folder]=e.items;root.folderPreviews=next}
    else if(e.type==='thumbnail')root.updateThumbnail(e.path,e.thumbnail)
    else if(e.type==='changed'){previewsDelay.restart();if(root.stackOpen && !root.stackMenuOnly && (e.folder===root.folder || root.folder==='recent' || root.folder==='trash'))stackRefresh.restart()}
    else if(e.type==='trash'){root.trashCount=e.count;previewsDelay.restart();if(root.stackOpen && root.folder==='trash')stackRefresh.restart()}
    else if(e.type==='error'){root.stackPending=false;console.warn('Dock:',e.message);Quickshell.execDetached(['notify-send','-a','Dock','Operation failed',e.message])}
   }catch(err){console.warn(err)}
  }}

 }
 function remember(){send({action:'remember',apps:controller.groupedClients.filter(g=>!root.blocked(g.key)).map(g=>({key:g.key,name:g.displayName,icon:g.iconPath}))})}
 Connections {target:controller;function onGroupedClientsChanged(){root.remember()}function onPinnedFilesChanged(){root.refreshPreviews()}function onActiveAppIdChanged(){if(!root.blocked(root.controller.activeAppId))root.send({action:'focus',key:root.controller.activeAppId})}function onFullscreenActiveChanged(){if(root.controller.fullscreenActive)root.revealed=false}}
 Connections{target:QuickLookState;function onFilesChanged(paths,changes,operation){
  if(changes.length)root.send({action:'renameRecentFiles',changes:changes})
  if(['duplicate','paste'].includes(operation))for(const path of paths)root.send({action:'recent',path:path})
  if(operation==='rename' && root.stackOpen)sourceStack.selection=paths.slice()
  stackRefresh.restart();previewsDelay.restart();root.send({action:'refresh'})
 }}
 Connections{target:CaptureState;function onScreenshotSaved(path){root.send({action:'recent',path:path});previewsDelay.restart()}}
 Timer{id:previewsDelay;interval:120;onTriggered:root.refreshPreviews()}
 Timer{id:springDismiss;interval:1000;running:root.stackOpen && root.stackDropMode && root.dragHoveredPath==='' && !receiverStack.dropInside;onTriggered:{root.stackOpen=false;root.stackPending=false;root.stackDropMode=false}}
 Timer{id:stackRefresh;interval:120;onTriggered:root.send({action:'list',folder:root.folder,sort:root.preference(root.folder,'sort')})}
 Timer {interval:2500;running:root.options.showTrash;repeat:true;onTriggered:root.send({action:'refresh'})}
 Timer {id:hideDelay;interval:root.options.hideDelay;onTriggered:if(!root.lensHovered && !edgeHover.hovered && !root.stackOpen && !root.stackPending && !root.controller.menuVisible)root.revealed=false}
 onStackOpenChanged:if(stackOpen){hideDelay.stop();revealed=true}else{root.hoveredIndex=-1;root.frozenZoomIndex=-1;if(options.hoverToReveal || controller.fullscreenActive)hideDelay.restart()}
 Connections {target:root.options;function onHoverToRevealChanged(){root.revealed=!root.options.hoverToReveal}function onPositionChanged(){root.controller.closeContextMenu();root.stackOpen=false;root.stackPending=false}function onStackSortChanged(){root.refreshPreviews()}function onStackDisplayChanged(){root.refreshPreviews()}}
 PanelWindow {
  id:dock
  screen:{const m=Hyprland.focusedMonitor;return Quickshell.screens.find(s=>m && s.name===m.name) || Quickshell.screens[0]}
  anchors{bottom:!root.vertical;top:root.vertical;left:options.position==='left' || !root.vertical;right:options.position==='right' || !root.vertical}
  implicitHeight:root.vertical ? screen.height : root.thickness+Math.max(72,root.actualSize*options.magnification)
  implicitWidth:root.vertical ? root.thickness+Math.max(72,root.actualSize*options.magnification) : screen.width
  exclusiveZone:options.hoverToReveal || controller.fullscreenActive ? 0 : root.thickness+8
  color:'transparent'
  WlrLayershell.namespace:'quickshell:dock';WlrLayershell.layer:WlrLayer.Top;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
  readonly property bool shown:DockDrag.desktopDragging || DockDrag.stackDragging || root.stackOpen || root.stackPending || controller.menuVisible || root.revealed || (!options.hoverToReveal && !controller.fullscreenActive) || (options.hoverToReveal && !windowWatcher.item?.blocked)
  mask:Region{Region{item:dock.shown ? inputRegion:edge;radius:dock.shown ? 24:0}Region{item:edge}}
  Item{id:inputRegion;x:plate.x;y:plate.y;width:plate.width;height:plate.height
   HoverHandler{id:lensHover;parent:plate
    onHoveredChanged:{root.lensHovered=hovered;controller.hoverActive=hovered;if(hovered){root.revealed=true;hideDelay.stop()}else{if(!root.stackOpen && !root.stackPending)root.hoveredIndex=-1;root.hoverLabel='';if(options.hoverToReveal || controller.fullscreenActive)hideDelay.restart()}}
    onPointChanged:{const p=plate.mapToItem(dock.contentItem,point.position.x,point.position.y);root.lensPointer=root.vertical ? p.y:p.x}
   }
  }
  Item {
   id:edge
   width:root.vertical ? 4 : plate.width;height:root.vertical ? plate.height : 4
   x:root.vertical ? (options.position==='right' ? dock.width-4 : 0) : plate.x
   y:root.vertical ? plate.y : dock.height-4
   HoverHandler{id:edgeHover;onHoveredChanged:{if(hovered){root.revealed=true;hideDelay.stop()}else if(options.hoverToReveal || controller.fullscreenActive)hideDelay.restart()}}
   DropArea{anchors.fill:parent;onEntered:drag=>{if(drag.hasUrls){root.revealed=true;hideDelay.stop()}}}
  }
  LiquidGlassBackdrop {
   id:dockGlass;wallpaperPath:GlassWallpaper.path;screenSize:Qt.size(dock.screen.width,dock.screen.height);windowPosition:root.origin
   monitorName:dock.screen.name;element:'dock';captureWindows:ShellConfig.options.glass.captureWindows
   ready:!Theme.plainSurfaces && dock.shown;windowOpacity:ShellConfig.options.glass.windowOpacity;windowOpacityByClass:ShellConfig.options.glass.windowOpacityByClass
  }
  Item {
   id:plate
   width:root.vertical ? root.thickness : tiles.implicitWidth+24+root.lensLayout.extra
   height:root.vertical ? tiles.implicitHeight+24+root.lensLayout.extra : root.thickness
   x:root.vertical ? (options.position==='right' ? dock.width-width-8 : 8) : (dock.width-width)/2
   y:root.vertical ? (dock.height-height)/2 : dock.height-height-8
   transform:Translate{x:!dock.shown && root.vertical ? (options.position==='right' ? plate.width+12 : -plate.width-12) : 0;y:!dock.shown && !root.vertical ? plate.height+12 : 0;Behavior on x{NumberAnimation{duration:160;easing.type:Easing.OutCubic}}Behavior on y{NumberAnimation{duration:160;easing.type:Easing.OutCubic}}}
   TahoeGlass{anchors.fill:parent;backdrop:Theme.plainSurfaces ? null : dockGlass;cornerRadius:24}
   Rectangle{anchors.fill:parent;radius:24;color:Theme.plainSurfaces ? Theme.surfaceFor('dock') : '#10ffffff';border.width:1;border.color:'#38ffffff'}

   DropArea{anchors.fill:parent;onDropped:drop=>{if(drop.hasUrls){for(const url of drop.urls)controller.pinDroppedPath(decodeURIComponent(url.toString().replace(/^file:\/\//,'')));drop.acceptProposedAction()}}}
   ListModel{id:entryModel;dynamicRoles:true}
   Connections{target:root;function onEntriesChanged(){plate.syncEntries()}}
   Component.onCompleted:syncEntries()
   function syncEntries(){
    const values=root.entries
    for(let i=0;i<values.length;i++){const e=values[i];const id=e.kind+':'+(e.key || e.path || '')+':'+(e.kind==='separator' ? String(i) : e.instances && e.instances.length && !e.running ? e.instances[0].address : '')
     let found=-1;for(let j=i;j<entryModel.count;j++)if(entryModel.get(j).identity===id){found=j;break}
     if(found<0)entryModel.insert(i,{identity:id,payload:e});else{if(found!==i)entryModel.move(found,i,1);entryModel.setProperty(i,'payload',e)}
    }
    while(entryModel.count>values.length)entryModel.remove(entryModel.count-1)
   }
   Grid {
    id:tiles;anchors.centerIn:parent;move:Transition{NumberAnimation{properties:'x,y';duration:180;easing.type:Easing.OutCubic}}
    columns:root.vertical ? 1 : root.entries.length;spacing:5
    Repeater {model:entryModel
     Item {
      id:slot;z:tile.dragging ? 100:root.hoveredIndex===slot.index ? 50:0;required property var payload;required property int index;property var modelData:payload
      width:tile.visible ? tile.width : root.vertical ? root.actualSize+16 : 12
      height:tile.visible ? tile.height : root.vertical ? 12 : root.actualSize+16
      transform:Translate{x:root.vertical ? 0:root.lensLayout.offsets[slot.index] || 0;y:root.vertical ? root.lensLayout.offsets[slot.index] || 0:0}
      Rectangle{visible:slot.modelData.kind==='separator';anchors.centerIn:parent;width:root.vertical ? root.actualSize*.7 : 1;height:root.vertical ? 1 : root.actualSize*.7;color:'#50ffffff';radius:1}
      DockTile {
       id:tile;entry:slot.modelData;visible:entry.kind!=='separator';iconSize:root.actualSize;vertical:root.vertical;indicators:options.showIndicators;animateLaunch:options.animateOpening
       thumbnailMap:root.thumbnails;dropTarget:stackDrop.containsDrag || trashDrop.containsDrag
       zoom:root.lensLayout.zooms[slot.index] || 1
       onHovered:on=>{if(root.dockDragging || root.stackOpen || root.stackPending)return;if(on){root.hoveredIndex=slot.index;root.hoverLabel=entry.name}else if(root.hoveredIndex===slot.index)root.hoverLabel=''}
       onActivated:modifiers=>root.activate(entry,modifiers,tile)
       onContextRequested:root.menu(entry,tile)
       onDragMoved:(delta,outside)=>root.dragItem(entry,tile,delta,outside)
       onDragFinished:(delta,outside)=>{root.dockDragging=false;root.draggedKey='';if(!entry.pinned)return;if(outside>root.actualSize){controller.pinnedApps=controller.pinnedApps.filter((a,i)=>i!==entry.index)}}
      }
DropArea{id:stackDrop;anchors.fill:parent;enabled:slot.modelData.kind==='stack'
       onEntered:drag=>{drag.accepted=drag.hasUrls;if(drag.accepted){root.dragHoveredPath=slot.modelData.path;springOpen.restart();root.revealed=true;hideDelay.stop()}}
       onExited:if(root.dragHoveredPath===slot.modelData.path){root.dragHoveredPath='';springOpen.stop()}
       onDropped:drop=>{springOpen.stop();const operation=slot.modelData.path==='recent' ? 'copy':root.operationFor(drop);if(operation==='copy' && !(drop.supportedActions & Qt.CopyAction)){drop.accepted=false;return}root.dropFiles(drop.urls.map(String),operation,slot.modelData.path);drop.accept(operation==='copy' ? Qt.CopyAction:operation==='link' ? Qt.LinkAction:Qt.MoveAction);root.stackPending=false;root.stackOpen=false;root.stackDropMode=false}
       Timer{id:springOpen;interval:500;onTriggered:if(root.dragHoveredPath===slot.modelData.path){const p=tile.mapToItem(dock.contentItem,tile.width/2,tile.height/2);root.openStack(slot.modelData.path,slot.modelData.name,Qt.point(p.x+root.origin.x,p.y+root.origin.y),true)}}
      }
      Rectangle{anchors.centerIn:tile;width:root.actualSize+10;height:width;radius:12;color:'#26ffffff';border.color:'#28ffffff';border.width:1;visible:stackDrop.containsDrag}
      DropArea{id:trashDrop;anchors.fill:parent;enabled:slot.modelData.kind==='trash'
       onEntered:drag=>{drag.accepted=drag.hasUrls && drag.urls.every(u=>String(u).startsWith('file://')) && (drag.supportedActions & Qt.MoveAction)!==0;if(drag.accepted){root.revealed=true;hideDelay.stop()}}
       onDropped:drop=>{if(drop.hasUrls && drop.urls.every(u=>String(u).startsWith('file://')) && (drop.supportedActions & Qt.MoveAction)!==0){root.send({action:'trash',urls:drop.urls.map(u=>u.toString())});if(drop.formats.indexOf('application/x-lickintosh-desktop')!==-1)DesktopFiles.clearSelection();drop.accept(Qt.MoveAction)}else drop.accepted=false}
      }
      Rectangle{anchors.centerIn:tile;width:root.actualSize+10;height:width;radius:12;color:'#26ffffff';border.color:'#28ffffff';border.width:1;visible:slot.modelData.kind==='trash' && trashDrop.containsDrag}
      DockTooltip{visible:root.hoverLabel!=='' && root.hoveredIndex===slot.index && !root.dockDragging && !trashDrop.containsDrag;text:slot.modelData.name || '';position:root.options.position
       x:root.vertical ? (root.options.position==='right' ? -width-10:tile.width+10):(tile.width-width)/2
       y:root.vertical ? (tile.height-height)/2:tile.height-8-root.actualSize*tile.zoom-height-12
      }
     }
    }
   }

  }
 }
 TrashConfirm{opened:root.clearRecentConfirm;iconSource:IconResolver.byName('document-open-recent') || root.themeIcon('folder');heading:'Clear Recent Files?';message:'Remove the recent file history?\nYour files will stay in their folders.';confirmText:'Clear History';onCancelled:root.clearRecentConfirm=false;onConfirmed:{root.send({action:'removeRecentFiles',clear:true});root.clearRecentConfirm=false;previewsDelay.restart()}}
 TrashConfirm{opened:root.trashConfirm;count:root.trashCount;onCancelled:root.trashConfirm=false;onConfirmed:{root.trashConfirm=false;root.send({action:'empty'})}}

 DockStack {id:sourceStack;opened:root.stackOpen && !root.stackDropMode;dropMode:false;settingsOnly:root.stackMenuOnly;title:root.stackTitle;files:root.files;folder:root.folder;point:root.stackPoint;dockPosition:options.position;view:root.preference(root.folder,'view');sort:root.preference(root.folder,'sort');display:root.preference(root.folder,'display');thumbnailMap:root.thumbnails
  onCloseRequested:{root.stackOpen=false;root.stackPending=false;root.stackDropMode=false;root.dragHoveredPath=''}
  onRemoveRequested:{const path=root.folder;root.stackOpen=false;if(path==='trash')options.showTrash=false;else if(path==='recent')options.showRecentFiles=false;else if(path===Quickshell.env('HOME')+'/Downloads')options.showDownloads=false;else controller.unpinFile(path)}
  onPreferenceRequested:(key,value)=>root.setPreference(root.folder,key,value)
  onFileActionRequested:(operation,entries,name,destination)=>root.fileAction(operation,entries,name,destination)
  onClearRecentRequested:{root.stackOpen=false;root.clearRecentConfirm=true}
  onRestoreRequested:uris=>root.send({action:'restore',uris:uris})
  onFilesDropped:(urls,operation,destination)=>root.dropFiles(urls,operation,destination)
  onEmptyRequested:{root.stackOpen=false;root.requestEmptyTrash()}
  onOpenRequested:paths=>{for(const path of paths)if(root.folder!=='trash')root.send({action:'recent',path:path});Quickshell.execDetached(['lickintosh-quicklook'].concat(paths));root.stackOpen=false}
  onFileRequested:path=>{if(root.folder!=='trash')root.send({action:'recent',path:path});Quickshell.execDetached(['xdg-open',path]);root.stackOpen=false}
  onFolderRequested:path=>root.openStack(path,path.split('/').pop(),root.stackPoint,root.stackDropMode || DockDrag.stackDragging)
 }
 DockStack {id:receiverStack;opened:root.stackOpen && root.stackDropMode;dropMode:true;title:root.stackTitle;files:root.files;folder:root.folder;point:root.stackPoint;dockPosition:options.position;view:root.preference(root.folder,'view');sort:root.preference(root.folder,'sort');display:root.preference(root.folder,'display');thumbnailMap:root.thumbnails
  onCloseRequested:if(!DockDrag.stackDragging && !DockDrag.desktopDragging){root.stackOpen=false;root.stackPending=false;root.stackDropMode=false}
  onFilesDropped:(urls,operation,destination)=>{root.dropFiles(urls,operation,destination);root.stackOpen=false;root.stackPending=false;root.stackDropMode=false}
  onFolderRequested:path=>root.openStack(path,path.split('/').pop(),root.stackPoint,true)
  onPreferenceRequested:(key,value)=>root.setPreference(root.folder,key,value)
 }

}
