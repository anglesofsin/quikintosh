import QtQuick
import QtQuick.Controls
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.services
import qs.components.glass
Scope {
 id:root
 property bool dragging:false
 readonly property bool previewing:QuickLookState.opened && QuickLookState.context==='stack'
 property bool opened:false
 property bool settingsOnly:false
 property string title:''
 property string folder:''
 readonly property bool trashStack:folder==='trash'
 property bool dropMode:false
 property var selection:[]
 property int anchorIndex:0
 property bool nativeRequested:false
 property var dragPayload:[]
 property string dragOrigin:''
 property string dragImage:''
 property int dragActions:Qt.MoveAction | Qt.CopyAction | Qt.LinkAction
 property int dragAction:Qt.MoveAction
 readonly property bool dropInside:cardDrop.containsDrag
 readonly property bool receiving:dropMode || (dragging && folder!==dragOrigin)
 signal openRequested(var paths)
 signal filesDropped(var urls,string operation,string destination)
 signal restoreRequested(var uris)
 signal emptyRequested()
 signal clearRecentRequested()
 signal fileActionRequested(string operation,var entries,string name,string destination)
 property var files:[]
 property var thumbnailMap:({})
 property point point:Qt.point(0,0)
 property string dockPosition:'bottom'
 property string view:'automatic'
 property string sort:'modified'
 property string display:'stack'
 property bool present:false
 property real progress:0
 property int selectedIndex:0
 readonly property string effectiveView:view==='automatic' ? (dockPosition==='bottom' && files.length<=9 ? 'fan':'grid') : view
 readonly property bool fan:effectiveView==='fan' && dockPosition==='bottom'
 signal closeRequested()
 signal folderRequested(string path)
 signal fileRequested(string path)
 signal removeRequested()
 signal preferenceRequested(string key,string value)
 Behavior on progress{NumberAnimation{duration:root.opened ? 240 : 170;easing.type:Easing.OutCubic}}
 onOpenedChanged:{if(opened){closeDelay.stop();present=true;selectedIndex=0;selection=[];anchorIndex=0;Qt.callLater(()=>{root.progress=1;keys.forceActiveFocus();if(root.settingsOnly)preferences.open()})}else{progress=0;closeDelay.restart()}}
 Timer{id:closeDelay;interval:180;onTriggered:root.present=false}
 ListModel{id:fileModel;dynamicRoles:true}
 function syncFiles(){
  for(let i=0;i<files.length;i++){
   let found=-1;for(let j=i;j<fileModel.count;j++)if(fileModel.get(j).path===files[i].path){found=j;break}
   if(found<0)fileModel.insert(i,{path:files[i].path,payload:files[i]});else{if(found!==i)fileModel.move(found,i,1);fileModel.setProperty(i,'payload',files[i])}
  }
  while(fileModel.count>files.length)fileModel.remove(fileModel.count-1)
  selection=selection.filter(path=>files.some(f=>f.path===path));selectedIndex=Math.min(selectedIndex,Math.max(0,fileModel.count-1))
 }
 onFilesChanged:syncFiles()
 onPreviewingChanged:if(!previewing && opened)Qt.callLater(()=>keys.forceActiveFocus())
 Connections{target:QuickLookState;function onIndexChanged(){if(root.previewing)root.selectedIndex=QuickLookState.index}}
 function actionSelection(){const entries=picked();fileActions.entries=entries;return entries}
 function showFileMenu(index,x,y){
  if(index>=0){if(selection.indexOf(files[index].path)===-1)selectOnly(index);selectedIndex=index;fileActions.show(picked(),x,y)}else fileActions.show([],x,y)
 }
 function picked(){return files.filter(f=>selection.indexOf(f.path)!==-1)}
 function selectOnly(index){if(index<0 || index>=files.length)return;selectedIndex=index;anchorIndex=index;selection=[files[index].path]}
 function selectRange(index,add){const range=files.slice(Math.min(anchorIndex,index),Math.max(anchorIndex,index)+1).map(f=>f.path);selection=add ? Array.from(new Set(selection.concat(range))):range;selectedIndex=index}
 function pressItem(index,modifiers){
  const present=selection.indexOf(files[index].path)!==-1;selectedIndex=index
  if(modifiers & Qt.ShiftModifier)selectRange(index,!!(modifiers & Qt.ControlModifier))
  else if(modifiers & Qt.ControlModifier){if(!present)selection=selection.concat([files[index].path]);anchorIndex=index}
  else if(!present)selectOnly(index)
  return present
 }
 function clickItem(index,modifiers,wasSelected){
  if(modifiers & Qt.ShiftModifier)return
  if(modifiers & Qt.ControlModifier){if(wasSelected)selection=selection.filter(p=>p!==files[index].path)}else selectOnly(index)
 }
 function activate(item){if(item.directory)folderRequested(item.path);else openRequested(selection.length ? selection.slice():[item.path])}
 function beginDrag(item,modifiers,image){
  if(nativeRequested || dragging)return
  if(selection.indexOf(item.path)===-1)selectOnly(files.findIndex(f=>f.path===item.path))
  dragPayload=picked().map(f=>f.trashUri || QuickLookState.urlFor(f.path));dragOrigin=folder;dragImage=image
  dragActions=(modifiers & Qt.ControlModifier) ? Qt.CopyAction:(modifiers & Qt.AltModifier) ? Qt.LinkAction:Qt.CopyAction | Qt.MoveAction | Qt.LinkAction
  dragAction=(modifiers & Qt.ControlModifier) ? Qt.CopyAction:(modifiers & Qt.AltModifier) ? Qt.LinkAction:Qt.MoveAction
  nativeRequested=true
 }
 function acceptDrop(drop,destination){
  if(!drop.hasUrls || !drop.urls.every(u=>/^(file|trash):\/\//.test(String(u)))){drop.accepted=false;return}
  if(destination==='trash' && (!(drop.supportedActions & Qt.MoveAction) || !drop.urls.every(u=>String(u).startsWith('file://')))){drop.accepted=false;return}
  const format='application/x-lickintosh-file-action'
  const mode=drop.formats.indexOf(format)!==-1 ? drop.getDataAsString(format):''
  const operation=destination==='trash' ? 'move':destination==='recent' ? 'copy':['copy','move','link'].indexOf(mode)!==-1 ? mode:drop.proposedAction===Qt.MoveAction ? 'move':drop.proposedAction===Qt.LinkAction ? 'link':'copy'
  if(destination==='recent' && !(drop.supportedActions & Qt.CopyAction)){drop.accepted=false;return}
  filesDropped(drop.urls.map(String),operation,destination)
  drop.accept(operation==='move' ? Qt.MoveAction:operation==='link' ? Qt.LinkAction:Qt.CopyAction)
 }
 onFolderChanged:{selection=[];selectedIndex=0;anchorIndex=0}

 PanelWindow {
  id:window;visible:root.present || root.dragging;color:'transparent';exclusiveZone:-1
  screen:{const m=Hyprland.focusedMonitor;return Quickshell.screens.find(s=>m && s.name===m.name) || Quickshell.screens[0]}
  anchors{left:true;right:true;top:true;bottom:true}
  WlrLayershell.namespace:'lickintosh:dock-stack';WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.keyboardFocus:root.opened && !root.dragging && !root.dropMode && !root.previewing ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None
  mask:Region{item:root.opened && !root.previewing ? (root.receiving ? card:root.dragging ? null:window.contentItem):null}
  GlassBackdrop{element:'menus';gateEnabled:(!root.fan && !root.settingsOnly) || fileActions.popupActive || preferences.visible}
  MouseArea{anchors.fill:parent;onClicked:root.closeRequested()}
  Item{id:nativeSource;width:1;height:1
   Drag.dragType:Drag.Automatic;Drag.active:root.nativeRequested
   Drag.supportedActions:root.dragActions;Drag.proposedAction:root.dragAction
   Drag.mimeData:({'text/uri-list':root.dragPayload.join('\r\n')+'\r\n','application/x-lickintosh-file-action':root.dragAction===Qt.CopyAction ? 'copy':root.dragAction===Qt.LinkAction ? 'link':'move'})
   Drag.imageSource:root.dragImage;Drag.imageSourceSize:Qt.size(80,80);Drag.hotSpot:Qt.point(40,40)
   Drag.onDragStarted:{root.dragging=true;DockDrag.stackDragging=true}
   Drag.onDragFinished:{root.nativeRequested=false;root.dragging=false;DockDrag.stackDragging=false;root.closeRequested()}
  }
  FocusScope{
   id:keys;anchors.fill:parent;focus:true
   Keys.onPressed:event=>{
    if(event.key===Qt.Key_F2 && root.selection.length===1){root.actionSelection();fileActions.rename();event.accepted=true;return}
    if(event.key===Qt.Key_Delete && root.selection.length){root.actionSelection();fileActions.erase();event.accepted=true;return}
    if(event.modifiers & Qt.ControlModifier){
     if(event.key===Qt.Key_C && root.selection.length){root.actionSelection();fileActions.copy(false);event.accepted=true;return}
     if(event.key===Qt.Key_X && root.selection.length){root.actionSelection();fileActions.copy(true);event.accepted=true;return}
     if(event.key===Qt.Key_V && root.folder.startsWith('/')){root.fileActionRequested('paste',[],'',root.folder);event.accepted=true;return}
    }

    if(event.key===Qt.Key_A && (event.modifiers & Qt.ControlModifier)){root.selection=root.files.map(f=>f.path);event.accepted=true;return}
    if(event.key===Qt.Key_Space && fileModel.count){const paths=root.selection.length>1 ? root.selection.slice():root.files.map(f=>f.path);QuickLookState.show(paths,root.selection.length>1 ? 0:root.selectedIndex,'stack');event.accepted=true;return}
    if(event.key===Qt.Key_Escape){root.closeRequested();event.accepted=true}
    else if(event.key===Qt.Key_Return || event.key===Qt.Key_Enter){if(fileModel.count)root.activate(fileModel.get(root.selectedIndex).payload);event.accepted=true}
    else if([Qt.Key_Down,Qt.Key_Up,Qt.Key_Left,Qt.Key_Right].includes(event.key)){
     const step=event.key===Qt.Key_Up ? (root.effectiveView==='grid' ? -5:-1) : event.key===Qt.Key_Down ? (root.effectiveView==='grid' ? 5:1) : event.key===Qt.Key_Left ? -1:1
     const next=root.selection.length ? Math.max(0,Math.min(fileModel.count-1,root.selectedIndex+step)):0;if(event.modifiers & Qt.ShiftModifier)root.selectRange(next,!!(event.modifiers & Qt.ControlModifier));else root.selectOnly(next);event.accepted=true
    }
   }
  }
  BoxGlass{
   id:card;visible:root.present && (root.opened || !root.dragging) && !root.settingsOnly && !root.previewing && (!root.dragging || root.receiving)
   width:root.fan ? 430 : root.effectiveView==='list' ? 390 : 570
   height:Math.min(window.height-100,root.fan ? 88+Math.min(9,fileModel.count)*60 : root.effectiveView==='list' ? 100+Math.min(11,fileModel.count)*42 : 104+Math.max(1,Math.ceil(Math.min(20,fileModel.count)/5))*106)
   radius:22;color:root.fan ? 'transparent':'#501a1a20';transparent:root.fan;highlightEnabled:!root.fan;backdrop:root.fan ? null:card.registered
   readonly property real finalX:root.dockPosition==='left' ? Math.min(window.width-width-12,root.point.x+48) : root.dockPosition==='right' ? Math.max(12,root.point.x-width-48) : Math.max(12,Math.min(window.width-width-12,root.point.x-width+76))
   readonly property real finalY:root.dockPosition==='bottom' ? Math.max(42,root.point.y-height-46) : Math.max(42,Math.min(window.height-height-20,root.point.y-height/2))
   x:finalX;y:finalY
   opacity:root.dragging && !root.receiving ? 0:root.progress
   transformOrigin:root.dockPosition==='bottom' ? Item.BottomRight:root.dockPosition==='left' ? Item.Left:Item.Right
   scale:.84+.16*root.progress
   transform:Translate{x:root.dockPosition==='left' ? -30*(1-root.progress) : root.dockPosition==='right' ? 30*(1-root.progress):0;y:root.dockPosition==='bottom' ? 42*(1-root.progress):0}
   MouseArea{anchors.fill:parent;acceptedButtons:Qt.LeftButton | Qt.RightButton;onClicked:mouse=>{if(mouse.button===Qt.RightButton){const p=card.mapToItem(window.contentItem,mouse.x,mouse.y);root.showFileMenu(-1,p.x,p.y)}else root.selection=[]}}
   DropArea{id:cardDrop;anchors.fill:parent
    onEntered:drag=>{drag.accepted=drag.hasUrls;if(drag.hasUrls)leaveTarget.stop()}
    onExited:if(root.receiving)leaveTarget.restart()
    onDropped:drop=>{leaveTarget.stop();root.acceptDrop(drop,root.folder);root.closeRequested()}
   }
   Timer{id:leaveTarget;interval:1000;onTriggered:if(root.receiving)root.closeRequested()}
   Rectangle{anchors.fill:parent;radius:22;color:'#08ffffff';visible:cardDrop.containsDrag}
   Text{x:18;y:16;text:root.title+(root.selection.length>1 ? ' · '+root.selection.length+' selected':'');color:'white';font.family:'SF Pro Display';font.pixelSize:17;font.weight:Font.DemiBold;visible:!root.fan}
   Rectangle{
    anchors.right:parent.right;anchors.rightMargin:14;y:11;width:30;height:30;radius:9;color:menuMouse.containsMouse ? '#36ffffff':'transparent'
    Text{anchors.centerIn:parent;text:'•••';color:'white';font.pixelSize:12}
    MouseArea{id:menuMouse;anchors.fill:parent;hoverEnabled:true;onClicked:preferences.open()}
   }
   Menu{
    id:preferences;parent:window.contentItem
    x:root.settingsOnly ? Math.max(8,Math.min(window.width-width-8,root.point.x-width/2)) : card.x+card.width-width-14
    y:root.settingsOnly ? Math.max(38,Math.min(window.height-height-8,root.point.y-height-40)) : card.y+45
    onClosed:if(root.settingsOnly)root.closeRequested()
    MenuItem{text:'Display as Stack';checkable:true;checked:root.display==='stack';onTriggered:root.preferenceRequested('display','stack')}
    MenuItem{text:'Display as Folder';checkable:true;checked:root.display==='folder';onTriggered:root.preferenceRequested('display','folder')}
    MenuSeparator{}
    MenuItem{text:'Fan';checkable:true;checked:root.effectiveView==='fan';enabled:root.dockPosition==='bottom';onTriggered:root.preferenceRequested('view','fan')}
    MenuItem{text:'Grid';checkable:true;checked:root.effectiveView==='grid';onTriggered:root.preferenceRequested('view','grid')}
    MenuItem{text:'List';checkable:true;checked:root.effectiveView==='list';onTriggered:root.preferenceRequested('view','list')}
    MenuItem{text:'Automatic';checkable:true;checked:root.view==='automatic';onTriggered:root.preferenceRequested('view','automatic')}
    MenuSeparator{}
    MenuItem{text:'Sort by Name';onTriggered:root.preferenceRequested('sort','name')}
    MenuItem{text:'Sort by Date Added';onTriggered:root.preferenceRequested('sort','added')}
    MenuItem{text:'Sort by Date Modified';onTriggered:root.preferenceRequested('sort','modified')}
    MenuItem{text:'Sort by Kind';onTriggered:root.preferenceRequested('sort','kind')}
    MenuSeparator{}
    MenuItem{text:'Open in File Manager';onTriggered:{Quickshell.execDetached(['xdg-open',root.folder==='trash' ? 'trash:///':root.folder==='recent' ? Quickshell.env('HOME'):root.folder]);root.closeRequested()}}
    MenuItem{text:'Put Back';visible:root.trashStack;enabled:fileModel.count>0;onTriggered:root.restoreRequested((root.picked().length ? root.picked():[fileModel.get(root.selectedIndex).payload]).map(f=>f.trashUri))}
    MenuItem{text:'Empty Trash…';visible:root.trashStack;enabled:fileModel.count>0;onTriggered:root.emptyRequested()}
    MenuItem{text:'Clear Recent Files…';visible:root.folder==='recent';onTriggered:root.clearRecentRequested()}
    MenuItem{text:'Remove from Dock';visible:!root.trashStack;onTriggered:root.removeRequested()}
   }
   Text{visible:!fileModel.count;anchors.centerIn:parent;text:'No items yet';color:'#cbd0dd';font.pixelSize:14}
   Loader{
    id:content;active:!root.settingsOnly;x:14;y:root.fan ? 26:52;width:parent.width-28;height:parent.height-y-43
    sourceComponent:root.fan ? fanView : root.effectiveView==='grid' ? gridView:listView
   }
   Component{
    id:gridView
    GridView{clip:true;model:fileModel;cellWidth:width/5;cellHeight:106;cacheBuffer:106;boundsBehavior:Flickable.StopAtBounds;ScrollBar.vertical:ScrollBar{}
     delegate:FileTile{required property var payload;required property int index;item:payload;itemIndex:index;width:GridView.view.cellWidth;height:GridView.view.cellHeight;square:true}
    }
   }
   Component{
    id:listView
    ListView{clip:true;model:fileModel;reuseItems:true;cacheBuffer:84;boundsBehavior:Flickable.StopAtBounds;ScrollBar.vertical:ScrollBar{}
     delegate:FileTile{required property var payload;required property int index;item:payload;itemIndex:index;width:ListView.view.width;height:42}
    }
   }
   Component{
    id:fanView
    Item{
     Repeater{model:Math.min(9,fileModel.count)
      FileTile{required property int index;item:fileModel.get(index).payload;itemIndex:index;width:parent.width-25;height:56;y:(Math.min(9,fileModel.count)-index-1)*60;x:Math.pow(index,1.3)*2.2;fan:true}
     }
    }
   }
   Rectangle{
    anchors.bottom:parent.bottom;anchors.bottomMargin:9;anchors.horizontalCenter:parent.horizontalCenter;width:parent.width-28;height:29;radius:9;color:folderMouse.containsMouse ? '#40ffffff':root.fan ? '#e025252d':'#16ffffff'
    Text{anchors.centerIn:parent;text:root.fan && fileModel.count>9 ? 'Show all '+fileModel.count+' items  ↗':'Open in File Manager  ↗';color:'white';font.pixelSize:12}
    MouseArea{id:folderMouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:{if(root.fan && fileModel.count>9)root.preferenceRequested('view','grid');else{Quickshell.execDetached(['xdg-open',root.folder==='trash' ? 'trash:///':root.folder==='recent' ? Quickshell.env('HOME'):root.folder]);root.closeRequested()}}}
   }
  }
 }
 FileActions{id:fileActions;enabled:root.opened && !root.settingsOnly && !root.dragging && !root.dropMode;folder:root.folder;host:window.contentItem;backdrop:card.registered
  onRequested:(operation,entries,name,destination)=>root.fileActionRequested(operation,entries,name,destination)
  onRestoreRequested:uris=>root.restoreRequested(uris)
 }
 component FileTile:Item{
  id:entry
  property var item:({})
  property int itemIndex:0
  property bool square:false
  property bool fan:false
  readonly property bool nativeThreshold:fileMouse.drag.active
  onNativeThresholdChanged:if(nativeThreshold){fileMouse.moved=true;root.beginDrag(entry.item,fileMouse.pressModifiers,entry.source)}
  readonly property string thumbnail:root.thumbnailMap[item.path] || item.thumbnail || ''
  readonly property string source:thumbnail || (item.directory ? IconResolver.forFolder():IconResolver.forFile(item.name || ''))
  Rectangle{anchors.fill:parent;anchors.margins:2;radius:9;color:root.selection.indexOf(entry.item.path)!==-1 ? '#3dffffff':fileMouse.containsMouse ? '#16ffffff':'transparent';visible:!entry.fan}
  Rectangle{visible:entry.fan;anchors.right:icon.left;anchors.rightMargin:10;anchors.verticalCenter:parent.verticalCenter;width:Math.min(label.implicitWidth+22,parent.width-85);height:28;radius:7;color:root.selection.indexOf(entry.item.path)!==-1 ? '#ee4778aa':fileMouse.containsMouse ? '#e640404b':'#e626262e'}
  Image{
   id:icon;width:entry.square ? 60:entry.fan ? 54:30;height:width
   x:entry.square ? (parent.width-width)/2 : entry.fan ? parent.width-width:8;y:entry.square ? 3:(parent.height-height)/2
   source:entry.source;sourceSize:Qt.size(128,128);fillMode:Image.PreserveAspectFit;asynchronous:true;smooth:true;mipmap:true
   rotation:entry.fan ? -entry.itemIndex*2.2:0
  }
  Text{
   id:label;textFormat:Text.PlainText;x:entry.square ? 3:entry.fan ? 0:48;y:entry.square ? 67:0;width:entry.square ? parent.width-6:entry.fan ? parent.width-76:parent.width-58;height:entry.square ? 34:parent.height
   text:entry.item.name || '';color:'white';font.family:'SF Pro Text';font.pixelSize:entry.fan ? 12:11;elide:Text.ElideMiddle;wrapMode:entry.square ? Text.WrapAnywhere:Text.NoWrap;maximumLineCount:2
   horizontalAlignment:entry.square ? Text.AlignHCenter:entry.fan ? Text.AlignRight:Text.AlignLeft;verticalAlignment:Text.AlignVCenter
  }
  DropArea{anchors.fill:parent;enabled:!!entry.item.directory
   onEntered:drag=>{drag.accepted=drag.hasUrls;if(drag.accepted){leaveTarget.stop();openFolder.start()}}
   onExited:openFolder.stop()
   onDropped:drop=>{openFolder.stop();root.acceptDrop(drop,entry.item.path);root.closeRequested()}
   Timer{id:openFolder;interval:650;onTriggered:root.folderRequested(entry.item.path)}
  }
  Item{id:dragProxy;width:1;height:1}
  MouseArea{id:fileMouse;anchors.fill:parent;acceptedButtons:Qt.LeftButton | Qt.RightButton;preventStealing:true;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;drag.target:pressedButtons===Qt.LeftButton ? dragProxy:null;drag.threshold:8
   property bool moved:false
   property bool wasSelected:false
   property int pressModifiers:0
   onPressed:mouse=>{pressModifiers=mouse.modifiers;moved=false;if(mouse.button===Qt.RightButton){if(root.selection.indexOf(entry.item.path)===-1)root.selectOnly(entry.itemIndex);root.selectedIndex=entry.itemIndex;return}wasSelected=root.pressItem(entry.itemIndex,mouse.modifiers)}
   onPositionChanged:if(drag.active){moved=true;root.beginDrag(entry.item,pressModifiers,entry.source)}
   onClicked:mouse=>{if(moved || root.dragging)return;if(mouse.button===Qt.RightButton){const p=entry.mapToItem(window.contentItem,mouse.x,mouse.y);root.showFileMenu(entry.itemIndex,p.x,p.y)}else root.clickItem(entry.itemIndex,pressModifiers,wasSelected)}
   onDoubleClicked:mouse=>{if(mouse.button===Qt.LeftButton && !moved && !root.dragging)root.activate(entry.item)}
  }
 }
}
