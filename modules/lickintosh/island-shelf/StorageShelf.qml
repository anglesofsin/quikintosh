import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import QtQuick.Layouts
import qs.services
Item{
 id:root
 objectName:'shelf-storage'
 property alias reviewPopup:confirm
 property var selectedApp:null
 property bool appList:false
 property bool removeData:false
 function review(app){selectedApp=app;removeData=false;ShelfState.appDataReview=({});ShelfState.send({action:'applicationData',id:app.id});confirm.open()}
 Connections{target:ShelfState;function onApplicationSuggested(id){const app=ShelfState.installedApps.find(a=>a.id===id);if(app?.removable)root.review(app)}}
 readonly property var storage:ShelfState.storageInfo
 function gb(value){return (Number(value || 0)/1073741824).toFixed(1)+' GB'}
 Component.onCompleted:ShelfState.send({action:'storage'})
 onVisibleChanged:if(visible)ShelfState.send({action:'storage'})
 ColumnLayout{anchors.fill:parent;spacing:18
  RowLayout{Layout.fillWidth:true;spacing:8
   ColumnLayout{Layout.fillWidth:true;spacing:4
    Text{text:root.gb(root.storage.used);font.family:ShelfStyle.displayFamily;font.pixelSize:26;font.weight:Font.DemiBold;color:'white'}
    Text{text:qsTr('%1 available').arg(root.gb(root.storage.free));font.family:ShelfStyle.textFamily;font.pixelSize:13;color:ShelfStyle.secondary}
   }
   Text{text:qsTr('of %1').arg(root.gb(root.storage.total));font.family:ShelfStyle.textFamily;font.pixelSize:13;color:ShelfStyle.secondary}
   ShelfButton{icon:'notch/refresh-cw.svg';accessibleLabel:qsTr('Refresh storage');onClicked:ShelfState.send({action:'storage'})}
  }
  Rectangle{Layout.fillWidth:true;Layout.preferredHeight:50;radius:14;color:'#101012'
   Grid{anchors.fill:parent;anchors.margins:8;columns:64;rows:6;columnSpacing:3;rowSpacing:3
    Repeater{model:384
     Rectangle{required property int index;width:Math.max(2,(parent.width-63*3)/64);height:3;radius:1;color:index<384*(root.storage.used/Math.max(1,root.storage.total)) ? '#79797f':'#303034'}
    }
   }
  }
  RowLayout{Layout.fillWidth:true
   ShelfIcon{icon:'notch/hard-drive.svg';size:18}
   Text{Layout.fillWidth:true;text:qsTr('System and files');font.family:ShelfStyle.textFamily;font.pixelSize:13;color:ShelfStyle.secondary}
   Text{text:root.gb(root.storage.used);font.family:ShelfStyle.textFamily;font.pixelSize:13;color:'white'}
  }
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:ShelfState.appBusy ? qsTr('Removing application…'):qsTr('Applications');font.family:ShelfStyle.textFamily;font.pixelSize:13;color:'white'}
   ShelfButton{text:root.appList ? qsTr('Hide'):qsTr('Manage…');onClicked:{root.appList=!root.appList;if(root.appList)ShelfState.send({action:'applications'})}}
  }
  ListView{id:apps;visible:root.appList;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;spacing:4;model:ShelfState.installedApps
   ScrollBar.vertical:ScrollBar{}
   delegate:Rectangle{required property var modelData;width:apps.width;height:44;radius:12;color:'#10ffffff'
    RowLayout{anchors.fill:parent;anchors.margins:8;spacing:10
     Image{Layout.preferredWidth:24;Layout.preferredHeight:24;source:IconResolver.forAppId(modelData.icon || modelData.id);sourceSize:Qt.size(48,48);asynchronous:true}
     Text{Layout.fillWidth:true;text:modelData.name;elide:Text.ElideRight;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:12}
     Text{text:modelData.size || modelData.kind;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:10}
     ShelfButton{icon:'notch/trash-2.svg';enabled:modelData.removable && !ShelfState.appBusy;accessibleLabel:qsTr('Uninstall %1').arg(modelData.name);onClicked:{root.review(modelData)}}
    }
   }
   Text{anchors.centerIn:parent;visible:apps.count===0;text:qsTr('No user-managed applications');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:12}
  }
  DropArea{Layout.fillWidth:true;Layout.preferredHeight:root.appList ? 0:38;visible:!root.appList;keys:['text/uri-list']
   Rectangle{anchors.fill:parent;radius:12;color:parent.containsDrag ? '#250a84ff':'transparent';border.width:parent.containsDrag ? 1:0;border.color:'#0a84ff'}
   Text{anchors.centerIn:parent;text:qsTr('Drop an app to manage it');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:12}
   onDropped:drop=>{ShelfState.send({action:'applications',path:String(drop.urls[0] || '')});root.appList=true;drop.acceptProposedAction()}
  }
  Item{Layout.fillHeight:true;visible:!root.appList}
  RowLayout{Layout.fillWidth:true
   ColumnLayout{Layout.fillWidth:true;spacing:4
    Text{text:qsTr('Generated previews');font.family:ShelfStyle.textFamily;font.pixelSize:13;color:'white'}
    Text{text:qsTr('%1 · originals are preserved').arg(root.gb(root.storage.cache));font.family:ShelfStyle.textFamily;font.pixelSize:11;color:ShelfStyle.secondary}
   }
   ShelfButton{icon:'notch/trash-2.svg';accessibleLabel:qsTr('Clear generated preview cache');enabled:root.storage.cache>0;onClicked:ShelfState.send({action:'cleanPreviews'})}
  }
 }
 Popup{id:confirm;anchors.centerIn:parent;width:Math.min(root.width,360);padding:18;modal:false
  onOpened:ShelfState.interaction(true)
  onClosed:ShelfState.interaction(false)
  background:Rectangle{radius:18;color:'#f0222226';border.color:ShelfStyle.outline}
  contentItem:ColumnLayout{spacing:12
   Text{Layout.fillWidth:true;text:qsTr('Uninstall %1?').arg(root.selectedApp?.name || '');wrapMode:Text.WordWrap;color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:17}
   Text{Layout.fillWidth:true;text:root.selectedApp?.kind==='flatpak' ? root.removeData ? qsTr('The application will be removed and its selected personal data moved to Trash.'):qsTr('The application will be removed. Its personal data is kept.'):qsTr('The local launcher and AppImage will be moved to Trash.');wrapMode:Text.WordWrap;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:12}
   ShelfButton{visible:ShelfState.appDataReview.id===root.selectedApp?.id && (ShelfState.appDataReview.items || []).length>0;Layout.fillWidth:true;flat:true;selected:root.removeData;icon:root.removeData ? 'notch/check.svg':'notch/trash-2.svg';text:qsTr('Also move personal data to Trash');onClicked:root.removeData=!root.removeData}
   Text{visible:root.removeData;Layout.fillWidth:true;text:(ShelfState.appDataReview.items || []).map(item=>item.path).join('\n');wrapMode:Text.Wrap;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:10}
   RowLayout{Layout.alignment:Qt.AlignRight
    ShelfButton{text:qsTr('Cancel');onClicked:confirm.close()}
    ShelfButton{text:qsTr('Uninstall');onClicked:{ShelfState.send({action:'uninstall',id:root.selectedApp.id,confirmed:true,removeData:root.removeData});confirm.close()}}
   }
  }
 }
}
