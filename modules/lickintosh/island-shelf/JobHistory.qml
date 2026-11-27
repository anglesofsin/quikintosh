import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import qs.services
Item{
 id:root;objectName:'shelf-job-history'
 property var history:({items:[],seconds:0,completed:0,failed:0})
 Component.onCompleted:ShelfState.send({action:'jobHistory'})
 onVisibleChanged:if(visible)ShelfState.send({action:'jobHistory'})
 Connections{target:ShelfState;function onJobHistory(data){root.history=data}}
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Tasks & Agents');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:19;font.weight:Font.DemiBold}
   ShelfButton{flat:true;icon:'notch/refresh-cw.svg';accessibleLabel:qsTr('Refresh jobs');onClicked:ShelfState.send({action:'jobHistory'})}
  }
  Text{Layout.fillWidth:true;text:qsTr('%1 completed · %2 failed · %3 minutes').arg(history.completed).arg(history.failed).arg(Math.round(history.seconds/60));color:'#aaaab3';font.family:ShelfStyle.textFamily;font.pixelSize:12}
  ListView{id:list;reuseItems:true;Layout.fillWidth:true;Layout.fillHeight:true;spacing:6;clip:true;model:root.history.items
   ScrollBar.vertical:ScrollBar{}
   delegate:Rectangle{required property var modelData;width:list.width;height:44;radius:12;color:'#13ffffff'
    RowLayout{anchors.fill:parent;anchors.margins:10
     ShelfIcon{size:16;icon:modelData.code===0 ? 'notch/check.svg':'notch/x.svg';color:modelData.code===0 ? '#63d58b':'#ff827b'}
     Text{Layout.fillWidth:true;text:modelData.title;textFormat:Text.PlainText;elide:Text.ElideRight;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:12}
     Text{text:Math.round(modelData.seconds)+'s';color:'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
    }
   }
  }
  Text{Layout.fillWidth:true;text:qsTr('Run a task with quickintosh-run --title "Build" -- your-command. Only title, duration and exit status are saved.');wrapMode:Text.Wrap;color:'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
 }
}
