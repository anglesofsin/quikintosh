import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.components
import qs.rosa.services
Item {
 id:root
 property bool floating:false
 property var selected:[]
 property bool selectionMode:false
 property string renamePath:''
 readonly property var chosen:ShelfState.items.filter(item=>selected.includes(item.path))
 function choose(path,ctrl){selected=ctrl || selectionMode ? (selected.includes(path) ? selected.filter(p=>p!==path):selected.concat([path])):[path]}
 function act(action){ShelfState.send({action:action,paths:selected});if(action==='remove')selected=[]}
 function sizeText(n){if(n<1024)return n+' bytes';if(n<1048576)return Math.round(n/1024)+' KB';if(n<1073741824)return (n/1048576).toFixed(1)+' MB';return (n/1073741824).toFixed(1)+' GB'}
 function transform(operation){ShelfState.transformPaths=selected;ShelfState.transformOperation=operation || 'compress';ShelfState.closeRequested();ShelfState.transformOpen=true}
 ColumnLayout{anchors.fill:parent;spacing:12
  RowLayout{Layout.fillWidth:true;spacing:8
   ShelfButton{implicitWidth:36;implicitHeight:36;icon:'notch/package.svg';iconSize:19;accessibleLabel:qsTr('Create ZIP');enabled:root.selected.length>0;onClicked:root.act('archive')}
   ShelfButton{implicitWidth:36;implicitHeight:36;icon:'notch/folder-plus.svg';iconSize:19;accessibleLabel:qsTr('Copy selection into a new folder');enabled:root.selected.length>0;onClicked:root.act('folder')}
   ShelfButton{implicitWidth:36;implicitHeight:36;icon:'notch/check-circle.svg';iconSize:19;selected:root.selectionMode;accessibleLabel:qsTr('Select multiple files');onClicked:root.selectionMode=!root.selectionMode}
   Item{Layout.fillWidth:true}
   ShelfButton{visible:!root.floating;implicitWidth:36;implicitHeight:36;icon:'notch/shopping-basket.svg';iconSize:19;accessibleLabel:qsTr('Floating file tray');onClicked:ShelfState.trayOpen=true}
   ShelfButton{implicitWidth:36;implicitHeight:36;icon:'notch/trash-2.svg';iconSize:19;accessibleLabel:root.selected.length ? qsTr('Remove selection from tray'):qsTr('Clear unpinned files');onClicked:root.selected.length ? root.act('remove'):ShelfState.send({action:'clear'})}
   Item{visible:root.floating;Layout.preferredWidth:30}
  }
  GridView{
   id:files;Layout.fillWidth:true;Layout.fillHeight:true;clip:true
   cellWidth:Math.floor(width/Math.max(1,Math.floor(width/156)));cellHeight:162
   model:ShelfState.items;boundsBehavior:Flickable.StopAtBounds;reuseItems:true
   ScrollBar.vertical:ScrollBar{policy:ScrollBar.AsNeeded}
   delegate:Item{
    id:tile;required property var modelData;required property int index
    width:files.cellWidth;height:files.cellHeight
    readonly property bool picked:root.selected.includes(modelData.path)
    readonly property string thumbnail:ShelfState.filePreviews[modelData.path] || modelData.preview || (modelData.directory ? IconResolver.forFolder():IconResolver.forFile(modelData.path))
    Rectangle{anchors.fill:parent;anchors.margins:4;radius:18;color:tile.picked ? '#0a84ff':folderDrop.containsDrag ? '#26ffd60a':'transparent';border.width:folderDrop.containsDrag ? 3:0;border.color:'#ffd60a'
     Image{id:art;anchors.horizontalCenter:parent.horizontalCenter;y:14;width:88;height:88;source:tile.thumbnail;sourceSize:Qt.size(176,176);fillMode:Image.PreserveAspectFit;asynchronous:true;retainWhileLoading:true;mipmap:true}
     Rectangle{visible:!!tile.modelData.textPreview;anchors.horizontalCenter:parent.horizontalCenter;y:14;width:76;height:88;radius:4;color:'white'
      Text{anchors.fill:parent;anchors.margins:5;text:tile.modelData.textPreview || '';color:'#202024';font.family:'SF Mono';font.pixelSize:4;wrapMode:Text.Wrap;clip:true;textFormat:Text.PlainText}
     }
     Rectangle{visible:!!tile.modelData.tracked;anchors.horizontalCenter:parent.horizontalCenter;y:2;width:52;height:18;radius:9;color:'#0a84ff';Text{anchors.centerIn:parent;text:qsTr('tracked');font.family:ShelfStyle.textFamily;font.pixelSize:10;font.weight:Font.DemiBold;color:'white'}}
     Rectangle{visible:!!tile.modelData.pinned;x:parent.width/2+26;y:77;width:20;height:20;radius:10;color:'#ff9f0a';ShelfIcon{anchors.centerIn:parent;size:12;icon:'notch/map-pin.svg'}}
     Text{anchors.left:parent.left;anchors.right:parent.right;anchors.margins:5;y:107;text:tile.modelData.name;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:14;font.weight:Font.DemiBold;elide:Text.ElideMiddle;horizontalAlignment:Text.AlignHCenter;textFormat:Text.PlainText}
     Text{anchors.left:parent.left;anchors.right:parent.right;anchors.margins:4;y:128;text:(tile.modelData.pinned ? qsTr('Pinned · '):'')+(tile.modelData.directory ? qsTr('%1 items').arg(tile.modelData.count || 0):root.sizeText(tile.modelData.size)+(tile.modelData.dimensions ? ' · '+tile.modelData.dimensions:''));color:tile.picked ? '#d9eeff':'#a1a1a6';font.family:ShelfStyle.textFamily;font.pixelSize:12;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight}
     MouseArea{id:mouse;objectName:'tray-item-'+tile.index;anchors.fill:parent;acceptedButtons:Qt.LeftButton|Qt.RightButton;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;drag.target:dragProxy;drag.threshold:8
      onPressed:e=>{if(e.button===Qt.RightButton){if(!tile.picked)root.selected=[tile.modelData.path]}else root.choose(tile.modelData.path,!!(e.modifiers&Qt.ControlModifier))}
      onClicked:e=>{if(e.button===Qt.RightButton)fileMenu.popup(mouse,e.x,e.y)}
      onDoubleClicked:Quickshell.execDetached(['xdg-open',tile.modelData.path])
      onPositionChanged:e=>{if(drag.active){const dir=e.x>dragProxy.lastX ? 1:-1;if(dir!==dragProxy.direction && Math.abs(e.x-dragProxy.lastX)>6){dragProxy.reversals++;dragProxy.direction=dir;if(dragProxy.reversals>=6){ShelfState.trayOpen=true;dragProxy.reversals=0}}dragProxy.lastX=e.x}}
      onReleased:{dragProxy.reversals=0}
     }
     Item{id:dragProxy;width:1;height:1;property real lastX:0;property int direction:0;property int reversals:0
      Drag.active:mouse.drag.active;Drag.dragType:Drag.Automatic;Drag.supportedActions:Qt.CopyAction;Drag.proposedAction:Qt.CopyAction
      Drag.mimeData:({'text/uri-list':root.chosen.map(item=>item.uri).join('\r\n')+'\r\n'})
      Drag.imageSource:tile.thumbnail;Drag.imageSourceSize:Qt.size(80,80);Drag.hotSpot:Qt.point(40,40)
      Drag.onDragFinished:{x=0;y=0;reversals=0}
     }
     DropArea{id:folderDrop;anchors.fill:parent;enabled:tile.modelData.directory;keys:['text/uri-list']
      onDropped:drop=>{const paths=Array.from(drop.urls).map(String);ShelfState.add(drop.urls);ShelfState.send({action:'folder',paths:paths,target:tile.modelData.path});drop.acceptProposedAction()}
     }
     ShelfMenu{id:fileMenu
      ShelfMenuItem{symbol:'notch/eye.svg';text:qsTr('Quick Look');onTriggered:QuickLookState.show([tile.modelData.path],0,'external')}
      ShelfMenuItem{symbol:'notch/refresh-cw.svg';text:qsTr('Transform…');onTriggered:root.transform('compress')}
      ShelfMenuItem{symbol:'notch/package.svg';text:qsTr('Create ZIP');onTriggered:root.act('archive')}
      ShelfMenuItem{visible:String(tile.modelData.name).toLowerCase().endsWith('.zip');height:visible ? implicitHeight:0;text:qsTr('Unzip');onTriggered:root.act('unzip')}
      ShelfMenuItem{symbol:'notch/edit-3.svg';text:qsTr('Rename…');onTriggered:{root.renamePath=tile.modelData.path;renameInput.text=tile.modelData.name;renameDialog.open()}}
      ShelfMenuSeparator{}
      ShelfMenuItem{text:tile.modelData.pinned ? qsTr('Unpin'):qsTr('Pin');onTriggered:root.act('pin')}
      ShelfMenuItem{visible:tile.modelData.directory;height:visible ? implicitHeight:0;text:tile.modelData.tracked ? qsTr('Stop tracking folder'):qsTr('Track folder');onTriggered:root.act('track')}
      ShelfMenuItem{symbol:'notch/copy.svg';text:qsTr('Copy');onTriggered:root.act('copy')}
      ShelfMenuItem{symbol:'notch/send.svg';text:qsTr('Share with LocalSend');visible:!!ShelfState.capabilities.share;height:visible ? implicitHeight:0;onTriggered:root.act('share')}
      ShelfMenuItem{symbol:'notch/folder.svg';text:qsTr('Show in Finder');onTriggered:Quickshell.execDetached(['quickintosh-finder','--select',tile.modelData.path])}
      ShelfMenuItem{symbol:'notch/trash-2.svg';text:qsTr('Remove from tray');onTriggered:root.act('remove')}
     }
    }
   }
   Text{anchors.centerIn:parent;visible:files.count===0;text:qsTr('Drop files here');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:16}
  }
  Text{Layout.fillWidth:true;text:ShelfState.notice;color:ShelfState.noticeError ? '#ffb4aa':ShelfStyle.secondary;visible:!!text;elide:Text.ElideRight;font.family:ShelfStyle.textFamily;font.pixelSize:12}
 }
 Popup{id:renameDialog;anchors.centerIn:parent;width:Math.min(root.width,330);padding:16;modal:true
  background:Rectangle{radius:20;color:'#ee242426';border.color:ShelfStyle.outline}
  contentItem:ColumnLayout{spacing:12
   Text{text:qsTr('Rename');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:17;font.weight:Font.DemiBold}
   TextField{id:renameInput;Layout.fillWidth:true;selectByMouse:true;color:'white';font.family:ShelfStyle.textFamily;background:Rectangle{radius:10;color:'#25ffffff'}
onAccepted:renameConfirm.clicked()}
   ShelfButton{id:renameConfirm;Layout.alignment:Qt.AlignRight;text:qsTr('Rename');selected:true;onClicked:{ShelfState.send({action:'rename',paths:[root.renamePath],name:renameInput.text});renameDialog.close()}}
  }
 }
 DropArea{z:-1;anchors.fill:parent;keys:['text/uri-list'];onDropped:drop=>{ShelfState.add(drop.urls);drop.acceptProposedAction()}}
 Connections{target:ShelfState;function onItemsChanged(){root.selected=root.selected.filter(p=>ShelfState.items.some(i=>i.path===p))}}
 Component.onCompleted:ShelfState.send({action:'list'})
}
