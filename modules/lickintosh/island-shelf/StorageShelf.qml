import QtQuick
import QtQuick.Layouts
import qs.services
Item{
 id:root
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
  Item{Layout.fillHeight:true}
  RowLayout{Layout.fillWidth:true
   ColumnLayout{Layout.fillWidth:true;spacing:4
    Text{text:qsTr('Generated previews');font.family:ShelfStyle.textFamily;font.pixelSize:13;color:'white'}
    Text{text:qsTr('%1 · originals are preserved').arg(root.gb(root.storage.cache));font.family:ShelfStyle.textFamily;font.pixelSize:11;color:ShelfStyle.secondary}
   }
   ShelfButton{icon:'notch/trash-2.svg';accessibleLabel:qsTr('Clear generated preview cache');enabled:root.storage.cache>0;onClicked:ShelfState.send({action:'cleanPreviews'})}
  }
 }
}
