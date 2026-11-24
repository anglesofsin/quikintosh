import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
import qs.components.glass
Scope {
 id:root
 property bool enabled:false
 property var entries:[]
 property string folder:''
 property Item host:null
 property Item backdrop:null
 property real menuX:0
 property real menuY:0
 property bool clipboardFiles:false
 property bool deleting:false
 readonly property bool popupActive:menu.visible || renameDialog.visible || deleting
 readonly property bool trash:folder==='trash'
 readonly property color foreground:Theme.isLight ? '#202127':'#f6f7fb'
 signal requested(string operation,var entries,string name,string destination)
 signal restoreRequested(var uris)
 function show(values,x,y){if(!enabled)return;entries=values.slice();menuX=x;menuY=y;clipboardFiles=false;clipboardCheck.running=true;menu.open()}
 function perform(operation){if(entries.length)requested(operation,entries,'',folder)}
 function rename(){if(!enabled || trash || entries.length!==1)return;renameInput.text=entries[0].name;renameDialog.open()}
 function submitRename(){if(renameInput.text.trim()==='' || entries.length!==1)return;requested('rename',entries,renameInput.text,folder);renameDialog.close()}
 function erase(){if(!entries.length)return;if(trash){deleting=true}else perform('trash')}
 function copy(cut){if(!entries.length)return;const urls=entries.map(e=>e.trashUri || QuickLookState.urlFor(e.path));Quickshell.execDetached(['wl-copy','--type','x-special/gnome-copied-files','--',(cut ? 'cut':'copy')+'\n'+urls.join('\n')+'\n'])}
 onEnabledChanged:if(!enabled){menu.close();renameDialog.close();deleting=false}
 Process{id:clipboardCheck;command:['wl-paste','--list-types'];stdout:StdioCollector{onStreamFinished:root.clipboardFiles=/^(x-special\/gnome-copied-files|text\/uri-list)$/m.test(text)}}
 Menu{
  id:menu;parent:root.host;popupType:Popup.Item;modal:false
  x:Math.max(8,Math.min(root.host ? root.host.width-width-8:root.menuX,root.menuX));y:Math.max(8,Math.min(root.host ? root.host.height-height-8:root.menuY,root.menuY))
  padding:6;width:258
  background:BoxGlass{radius:13;color:'#c0282a32';backdrop:root.backdrop;Rectangle{anchors.fill:parent;radius:13;z:-1;color:Theme.isLight ? '#eff0f1f4':'#ef282a32';visible:!root.backdrop || !root.backdrop.captureSettled}}
  Entry{text:'Open';enabled:root.entries.length>0;hint:'Enter';onTriggered:root.perform('open')}
  Entry{text:'Quick Look';enabled:root.entries.length>0;hint:'Space';onTriggered:root.perform('preview')}
  Entry{text:'Open With…';enabled:root.entries.length===1 && !root.entries[0].directory;onTriggered:root.perform('chooseApp')}
  Divider{}
  Entry{text:'Show in Finder';enabled:root.entries.length>0;onTriggered:root.perform('reveal')}
  Entry{text:'Rename…';enabled:!root.trash && root.entries.length===1;hint:'F2';onTriggered:root.rename()}
  Entry{text:'Duplicate';enabled:!root.trash && root.entries.length>0;onTriggered:root.perform('duplicate')}
  Divider{}
  Entry{text:'Copy';enabled:root.entries.length>0;hint:'Ctrl+C';onTriggered:root.copy(false)}
  Entry{text:'Cut';enabled:root.entries.length>0;hint:'Ctrl+X';onTriggered:root.copy(true)}
  Entry{text:'Paste';enabled:root.folder.startsWith('/') && root.clipboardFiles;hint:'Ctrl+V';onTriggered:root.requested('paste',[],'',root.folder)}
  Entry{text:'Copy File Location';enabled:root.entries.length>0;onTriggered:Quickshell.execDetached(['wl-copy','--',root.entries.map(e=>e.trashUri || e.path).join('\n')])}
  Divider{}
  Entry{text:'Put Back';available:root.trash;enabled:root.entries.length>0;onTriggered:root.restoreRequested(root.entries.map(e=>e.trashUri))}
  Entry{text:root.trash ? 'Delete Immediately…':'Move to Trash';enabled:root.entries.length>0;destructive:root.trash;hint:'Delete';onTriggered:root.erase()}
  Entry{text:'Remove from Recent Files';available:root.folder==='recent';enabled:root.entries.length>0;onTriggered:root.perform('removeRecent')}
 }
 Popup{
  id:renameDialog;parent:root.host;popupType:Popup.Item;width:370;height:166;modal:true;focus:true;padding:20
  x:root.host ? (root.host.width-width)/2:0;y:root.host ? (root.host.height-height)/2:0
  onOpened:Qt.callLater(()=>{renameInput.forceActiveFocus();const name=renameInput.text;const dot=name.lastIndexOf('.');renameInput.select(0,root.entries[0].directory || dot<=0 ? name.length:dot)})
  background:BoxGlass{radius:20;color:'#c0282a32';backdrop:root.backdrop;Rectangle{anchors.fill:parent;radius:20;z:-1;color:Theme.isLight ? '#eff0f1f4':'#ef282a32';visible:!root.backdrop || !root.backdrop.captureSettled}}
  ColumnLayout{anchors.fill:parent;spacing:12
   Text{Layout.fillWidth:true;text:'Rename';color:root.foreground;font.family:'SF Pro Display';font.pixelSize:17;font.weight:Font.DemiBold}
   TextField{id:renameInput;Layout.fillWidth:true;font.family:'SF Pro Text';font.pixelSize:13;color:root.foreground;selectByMouse:true;selectionColor:AppearanceState.highlight;selectedTextColor:Theme.luma(AppearanceState.highlight)>.5 ? '#17171a':'white';padding:9
    background:Rectangle{radius:8;color:Theme.isLight ? '#18ffffff':'#38000000';border.width:1;border.color:renameInput.activeFocus ? Theme.accent:Theme.cardRim}
    onAccepted:root.submitRename();Keys.onEscapePressed:renameDialog.close()
   }
   RowLayout{Layout.alignment:Qt.AlignRight;spacing:8
    Choice{label:'Cancel';onTriggered:renameDialog.close()}
    Choice{label:'Rename';primary:true;enabled:renameInput.text.trim()!=='';onTriggered:root.submitRename()}
   }
  }
 }
 TrashConfirm{
  opened:root.deleting;count:root.entries.length
  heading:'Delete Immediately?'
  message:root.entries.length+' item'+(root.entries.length===1 ? '':'s')+' will be permanently deleted.\nYou can’t undo this action.'
  confirmText:'Delete' 
  onCancelled:{root.deleting=false}
  onConfirmed:{root.perform('delete');root.deleting=false}
 }
 component Entry:MenuItem{
  id:control
  property string hint:''
  property bool available:true
  property bool destructive:false
  visible:available;implicitHeight:available ? 30:0;implicitWidth:246;leftPadding:11;rightPadding:11
  contentItem:Item{
   implicitWidth:224;implicitHeight:22
   Text{anchors.left:parent.left;anchors.verticalCenter:parent.verticalCenter;width:parent.width-hintText.width-12;textFormat:Text.PlainText;text:control.text;elide:Text.ElideRight;color:control.destructive ? '#ff797f':root.foreground;font.family:'SF Pro Text';font.pixelSize:12;opacity:control.enabled ? 1:.35}
   Text{id:hintText;anchors.right:parent.right;anchors.verticalCenter:parent.verticalCenter;text:control.hint;color:root.foreground;opacity:control.enabled ? .48:.2;font.family:'SF Pro Text';font.pixelSize:11}
  }
  background:Rectangle{radius:7;color:control.highlighted || control.hovered ? (Theme.isLight ? '#20000000':'#28ffffff'):'transparent'}
 }
 component Divider:MenuSeparator{padding:4;contentItem:Rectangle{implicitWidth:238;implicitHeight:1;color:Theme.isLight ? '#18000000':'#20ffffff'}}
 component Choice:Rectangle{
  property string label:''
  property bool primary:false
  signal triggered()
  implicitWidth:86;implicitHeight:30;radius:8;opacity:enabled ? 1:.4
  color:primary ? (mouse.containsMouse ? '#6b8caf':'#55799e'):(mouse.containsMouse ? '#40ffffff':'#20ffffff')
  Text{anchors.centerIn:parent;text:parent.label;color:parent.primary ? 'white':root.foreground;font.family:'SF Pro Text';font.pixelSize:12}
  MouseArea{id:mouse;anchors.fill:parent;hoverEnabled:true;onClicked:parent.triggered()}
 }
}
