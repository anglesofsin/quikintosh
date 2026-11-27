import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell
import qs.services
import Quickshell.Io
Item {
 id:root
 property var paths:[]
 property var devices:[]
 property bool loading:false
 property string error:''
 signal finished()
 function refresh(){devices=[];error='';loading=true;discover.running=true}
 Process{id:discover;command:['kdeconnect-cli','--list-available','--id-name-only'];stdout:StdioCollector{onStreamFinished:{root.devices=text.split('\n').map(line=>{const parts=line.trim().split(/\s+/);return {id:parts.shift(),name:parts.join(' ')}}).filter(d=>/^[A-Za-z0-9_-]+$/.test(d.id) && d.name)}} onExited:(code,status)=>{root.loading=false;if(code!==0)root.error=qsTr('KDE Connect is unavailable. Open its settings to pair a device.')}}
 ColumnLayout{anchors.fill:parent;spacing:8
  RowLayout{Layout.fillWidth:true
   ShelfIcon{icon:'notch/send.svg';size:28;color:'#64b7b4'}
   Text{Layout.fillWidth:true;text:qsTr('Send with KDE Connect');font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold;color:ShelfStyle.primary}
   ShelfButton{icon:'notch/x.svg';accessibleLabel:qsTr('Close');flat:true;onClicked:root.finished()}
  }
  Text{Layout.fillWidth:true;text:root.paths.length===1 ? qsTr('1 file ready to send'):qsTr('%1 files ready to send').arg(root.paths.length);wrapMode:Text.Wrap;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:13}
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Nearby devices');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:13;font.weight:Font.Medium}
   ShelfButton{flat:true;icon:'notch/refresh-cw.svg';accessibleLabel:qsTr('Refresh');enabled:!root.loading;onClicked:root.refresh()}
  }
  ListView{Layout.fillWidth:true;Layout.fillHeight:true;spacing:6;clip:true;model:root.devices;ScrollBar.vertical:ScrollBar{policy:ScrollBar.AsNeeded}
   delegate:ItemDelegate{required property var modelData;width:ListView.view.width;height:54;text:modelData.name
    contentItem:RowLayout{spacing:12
     ShelfIcon{Layout.preferredWidth:22;Layout.preferredHeight:22;icon:'notch/smartphone.svg';size:22;color:'#64b7b4'}
     ColumnLayout{Layout.fillWidth:true;spacing:2
      Text{text:modelData.name;color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:14;font.weight:Font.Medium}
      Text{text:qsTr('KDE Connect · Paired');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:12}
     }
     ShelfIcon{icon:'notch/send.svg';size:16;color:ShelfStyle.secondary}
    }
    background:Rectangle{radius:12;color:parent.hovered ? '#28ffffff':'#12ffffff';border.width:1;border.color:'#18ffffff'}
    onClicked:{ShelfState.send({action:'share',provider:'kdeconnect',device:modelData.id,paths:root.paths});root.finished()}
   }
  }
  Text{Layout.fillWidth:true;visible:!root.devices.length;text:root.loading ? qsTr('Finding devices…'):root.error || qsTr('No paired devices nearby. Pair your phone in KDE Connect.');wrapMode:Text.Wrap;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:13}
  RowLayout{Layout.fillWidth:true
   ShelfButton{text:qsTr('KDE Connect settings');onClicked:Quickshell.execDetached(['kdeconnect-app'])}
   Item{Layout.fillWidth:true}
   ShelfButton{text:qsTr('LocalSend');onClicked:{ShelfState.send({action:'share',provider:'localsend',paths:root.paths});root.finished()}}
  }
 }
}
