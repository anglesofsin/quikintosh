import QtQuick
import QtQuick.Layouts
import qs.services
Item {
 id:root
 property string kind:'files'
 signal activated()
 readonly property string heading:kind==='storage' ? qsTr('Storage'):kind==='clipboard' ? qsTr('Clipboard'):qsTr('Files')
 ColumnLayout{anchors.fill:parent;spacing:12
  RowLayout{Layout.fillWidth:true
   ShelfIcon{size:20;icon:root.kind==='storage' ? 'notch/hard-drive.svg':root.kind==='clipboard' ? 'notch/clipboard.svg':'notch/inbox.svg'}
   Text{Layout.fillWidth:true;text:root.heading;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:15;font.weight:Font.DemiBold}
   ShelfButton{flat:true;icon:'notch/arrow.svg';accessibleLabel:qsTr('Open %1').arg(root.heading);onClicked:root.activated()}
  }
  Loader{Layout.fillWidth:true;Layout.fillHeight:true;sourceComponent:root.kind==='storage' ? storage:root.kind==='clipboard' ? clipboard:files}
 }
 Component{id:files
  RowLayout{spacing:12
   Repeater{model:ShelfState.items.slice(0,3)
    ColumnLayout{required property var modelData;Layout.fillWidth:true;Layout.minimumWidth:0;spacing:6
     Image{Layout.alignment:Qt.AlignHCenter;Layout.preferredWidth:58;Layout.preferredHeight:58;source:ShelfState.filePreviews[modelData.path] || modelData.preview || (modelData.directory ? IconResolver.forFolder():IconResolver.forFile(modelData.path));sourceSize:Qt.size(116,116);fillMode:Image.PreserveAspectFit;asynchronous:true}
     Text{Layout.fillWidth:true;text:modelData.name;elide:Text.ElideMiddle;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11;horizontalAlignment:Text.AlignHCenter}
    }
   }
   Text{visible:ShelfState.items.length===0;Layout.fillWidth:true;text:qsTr('Drop files to keep them nearby');wrapMode:Text.WordWrap;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:13}
  }
 }
 Component{id:clipboard
  ColumnLayout{spacing:8
   Text{Layout.fillWidth:true;Layout.fillHeight:true;text:ShelfState.clips[0]?.kind==='image' ? qsTr('Image copied'):ShelfState.clips[0]?.text || qsTr('Your clipboard history appears here');wrapMode:Text.WordWrap;maximumLineCount:4;elide:Text.ElideRight;textFormat:Text.PlainText;color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:14}
   RowLayout{Layout.fillWidth:true
    Text{Layout.fillWidth:true;text:qsTr('%1 items').arg(ShelfState.clips.length);color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
    ShelfButton{flat:true;icon:'notch/copy.svg';enabled:ShelfState.clips.length>0;accessibleLabel:qsTr('Copy latest item');onClicked:ShelfState.send({action:'copyClip',path:ShelfState.clips[0].path})}
   }
  }
 }
 Component{id:storage
  ColumnLayout{spacing:10
   Text{text:(Number(ShelfState.storageInfo.used || 0)/1073741824).toFixed(1)+' GB';color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:25;font.weight:Font.DemiBold}
   Rectangle{Layout.fillWidth:true;Layout.preferredHeight:9;radius:4.5;color:'#24ffffff';Rectangle{width:parent.width*(ShelfState.storageInfo.used/Math.max(1,ShelfState.storageInfo.total));height:parent.height;radius:4.5;color:'#aaa6ff'}}
   Text{text:qsTr('%1 GB available').arg((Number(ShelfState.storageInfo.free || 0)/1073741824).toFixed(1));color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:12}
  }
 }
 DropArea{anchors.fill:parent;keys:['text/uri-list'];enabled:root.kind==='files';onDropped:drop=>{ShelfState.add(drop.urls);drop.acceptProposedAction()}}
 Component.onCompleted:if(kind==='storage')ShelfState.send({action:'storage'});else if(kind==='clipboard')ShelfState.send({action:'clipboard'})
}
