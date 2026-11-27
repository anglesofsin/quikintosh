import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.components
import qs.rosa.services
Item {
 id:root
 property bool floating:false
 property var selected:[]
 function choose(path,ctrl){selected=ctrl ? (selected.includes(path) ? selected.filter(p=>p!==path):selected.concat([path])):[path]}
 function act(action){ShelfState.send({action:action,paths:selected});if(action==='remove')selected=[]}
 ColumnLayout{anchors.fill:parent;spacing:12
  RowLayout{Layout.fillWidth:true;spacing:8
   Text{Layout.fillWidth:true;text:qsTr('File tray');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold}
   ShelfButton{visible:!root.floating;icon:'notch/external-link.svg';onClicked:ShelfState.trayOpen=true}
   ShelfButton{flat:true;icon:'notch/copy.svg';accessibleLabel:qsTr('Copy files');enabled:root.selected.length>0;onClicked:root.act('copy')}
   ShelfButton{flat:true;icon:'notch/box.svg';accessibleLabel:qsTr('Create ZIP archive');enabled:root.selected.length>0;onClicked:root.act('archive')}
   ShelfButton{flat:true;icon:'notch/star.svg';accessibleLabel:qsTr('Pin files');enabled:root.selected.length>0;onClicked:root.act('pin')}
   ShelfButton{flat:true;icon:'notch/minus-circle.svg';accessibleLabel:qsTr('Remove from tray');enabled:root.selected.length>0;onClicked:root.act('remove')}
   ShelfButton{flat:true;icon:'notch/trash-2.svg';accessibleLabel:qsTr('Clear tray');onClicked:ShelfState.send({action:'clear'})}
   Item{visible:root.floating;Layout.preferredWidth:34}
  }
  GridView{id:files;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;cellWidth:Math.max(140,width/Math.max(1,Math.floor(width/170)));cellHeight:176;model:ShelfState.items;boundsBehavior:Flickable.StopAtBounds
   ScrollBar.vertical:ScrollBar{}
   delegate:Item {required property var modelData;required property int index;width:files.cellWidth;height:files.cellHeight
    Rectangle{anchors.fill:parent;anchors.margins:5;radius:15;color:root.selected.includes(modelData.path) ? ShelfStyle.selected:'transparent';border.color:root.selected.includes(modelData.path) ? '#70ffffff':'transparent'
     ColumnLayout{anchors.fill:parent;anchors.margins:12;spacing:8
      Image{Layout.fillWidth:true;Layout.fillHeight:true;source:modelData.preview || (modelData.directory ? IconResolver.forFolder():IconResolver.forFile(modelData.path));fillMode:Image.PreserveAspectFit;sourceSize:Qt.size(256,220);asynchronous:true}
      Text{Layout.fillWidth:true;text:(modelData.pinned ? '• ':'')+modelData.name;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;font.weight:Font.DemiBold;elide:Text.ElideMiddle;horizontalAlignment:Text.AlignHCenter}
      Text{Layout.fillWidth:true;text:modelData.directory ? qsTr('Folder'):(modelData.size/1024).toFixed(1)+' KB';color:'#929298';font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.caption;horizontalAlignment:Text.AlignHCenter}
     }
     MouseArea{id:mouse;anchors.fill:parent;acceptedButtons:Qt.LeftButton|Qt.RightButton;onClicked:e=>{root.choose(modelData.path,!!(e.modifiers&Qt.ControlModifier));if(e.button===Qt.RightButton)menu.popup()};onDoubleClicked:Quickshell.execDetached(['xdg-open',modelData.path]);drag.target:dragItem;drag.threshold:10}
     Item{id:dragItem;width:1;height:1;Drag.active:mouse.drag.active;Drag.dragType:Drag.Automatic;Drag.supportedActions:Qt.CopyAction;Drag.proposedAction:Qt.CopyAction;Drag.mimeData:({'text/uri-list':modelData.uri+'\r\n'});Drag.imageSource:modelData.preview || '';Drag.imageSourceSize:Qt.size(80,80);Drag.onDragFinished:{x=0;y=0}}
     Menu{id:menu;property bool holding:false;onVisibleChanged:{if(holding!==visible){holding=visible;ShelfState.interaction(holding)}}
      Component.onDestruction:if(holding)ShelfState.interaction(false)
      MenuItem{text:qsTr('Quick Look');onTriggered:QuickLookState.show([modelData.path],0,'external')}
      MenuItem{text:qsTr('Show in Finder');onTriggered:Quickshell.execDetached(['quickintosh-finder','--select',modelData.path])}
      MenuItem{text:qsTr('Convert to PNG');onTriggered:ShelfState.send({action:'convert',format:'png',paths:root.selected})}
      MenuItem{text:qsTr('Convert to JPEG');onTriggered:ShelfState.send({action:'convert',format:'jpeg',paths:root.selected})}
      MenuItem{text:qsTr('Convert to WebP');onTriggered:ShelfState.send({action:'convert',format:'webp',paths:root.selected})}
      MenuItem{text:qsTr('Copy files');onTriggered:root.act('copy')}
      MenuItem{text:qsTr('Pin / Unpin');onTriggered:root.act('pin')}
      MenuItem{text:qsTr('Remove from tray');onTriggered:root.act('remove')}
     }
    }
   }
   Text{anchors.centerIn:parent;visible:files.count===0;text:qsTr('Drop files here. Your originals stay where they are.');color:'#9a9aa3';font.family:ShelfStyle.textFamily;font.pixelSize:14}
  }
  Text{Layout.fillWidth:true;text:ShelfState.notice;color:'#ffb4aa';visible:!!text;wrapMode:Text.WordWrap;font.family:ShelfStyle.textFamily;font.pixelSize:12}
 }
 DropArea{anchors.fill:parent;keys:['text/uri-list'];onDropped:drop=>{ShelfState.add(drop.urls);drop.acceptProposedAction()}}
 Component.onCompleted:ShelfState.send({action:'list'})
}
