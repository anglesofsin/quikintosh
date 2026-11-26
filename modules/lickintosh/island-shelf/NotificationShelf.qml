import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import qs.services
import qs.ui.topbar.statusarea.notifcenter
Item {
 id:root;property var notices:[]
 ColumnLayout{anchors.fill:parent;spacing:12
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Notifications');font.family:'SF Pro Display';font.pixelSize:18;font.weight:Font.DemiBold;color:'white'}
   ShelfButton{text:NotifService.dndEnabled ? qsTr('Focus on'):qsTr('Focus off');selected:NotifService.dndEnabled;onClicked:NotifService.dndEnabled=!NotifService.dndEnabled}
  }
  ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;spacing:8;clip:true;model:root.notices
   remove:Transition{ParallelAnimation{NumberAnimation{property:'opacity';to:0;duration:ShellMotion.fade()}NumberAnimation{property:'x';to:60;duration:ShellMotion.fade();easing.type:Easing.InCubic}}}
   displaced:Transition{NumberAnimation{properties:'x,y';duration:ShellMotion.fade();easing.type:Easing.OutCubic}}
   delegate:Rectangle {id:card;required property var modelData;width:list.width;height:content.implicitHeight+24;radius:18;color:'#17171b'
    ColumnLayout{id:content;anchors.left:parent.left;anchors.right:parent.right;anchors.top:parent.top;anchors.margins:12;spacing:6
     RowLayout{Layout.fillWidth:true
      Text{Layout.fillWidth:true;text:card.modelData.appName || qsTr('Notification');color:'#9999a3';font.family:'SF Pro Text';font.pixelSize:11;elide:Text.ElideRight;textFormat:Text.PlainText}
      ShelfButton{icon:'notch/x.svg';onClicked:NotifService.removeFromCenter(card.modelData)}
     }
     Text{Layout.fillWidth:true;text:card.modelData.summary || '';font.family:'SF Pro Text';font.pixelSize:14;font.weight:Font.DemiBold;color:'white';elide:Text.ElideRight;textFormat:Text.PlainText}
     Text{Layout.fillWidth:true;visible:!!text;text:card.modelData.body || '';font.family:'SF Pro Text';font.pixelSize:12;color:'#b0b0b8';wrapMode:Text.WordWrap;maximumLineCount:2;elide:Text.ElideRight;textFormat:Text.PlainText}
     Flow{Layout.fillWidth:true;spacing:6
      Repeater{model:card.modelData.actions || []
       delegate:ShelfButton{required property var modelData;text:modelData.text || qsTr('Open');onClicked:modelData.invoke()}
      }
     }
    }
   }
   Text{anchors.centerIn:parent;visible:list.count===0;text:qsTr('No notifications');color:'#9999a3';font.family:'SF Pro Text';font.pixelSize:14}
  }
 }
}
