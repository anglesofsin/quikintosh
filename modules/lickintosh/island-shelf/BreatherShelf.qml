import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import qs.services
Item{
 id:root;objectName:'shelf-breather'
 readonly property var prefs:ShelfState.utilityPreferences
 ColumnLayout{anchors.fill:parent;spacing:12
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Take a breath');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:20;font.weight:Font.DemiBold}
   ShelfButton{text:root.prefs.breaksEnabled===true ? qsTr('On'):qsTr('Off');selected:root.prefs.breaksEnabled===true;onClicked:ShelfState.send({action:'utilityPreferences',values:{breaksEnabled:root.prefs.breaksEnabled!==true}})}
  }
  Text{Layout.fillWidth:true;text:qsTr('Gentle reminders for your eyes, a stretch and a glass of water.');wrapMode:Text.Wrap;color:'#aaaab3';font.family:ShelfStyle.textFamily;font.pixelSize:13}
  RowLayout{Layout.fillWidth:true
   Repeater{model:[{key:'eyes',label:qsTr('Rest your eyes'),minutes:20},{key:'stretch',label:qsTr('Stretch'),minutes:60},{key:'water',label:qsTr('Drink water'),minutes:90}]
    delegate:Rectangle{required property var modelData;Layout.fillWidth:true;Layout.fillHeight:true;radius:18;color:'#15ffffff'
     ColumnLayout{anchors.centerIn:parent;spacing:8
      Text{Layout.alignment:Qt.AlignHCenter;text:modelData.label;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:12;font.weight:Font.DemiBold}
      ShelfChoice{Layout.alignment:Qt.AlignHCenter;Layout.preferredWidth:120;readonly property var minutes:[5,10,15,20,30,45,60,90,120,180,240];model:minutes.map(String);currentIndex:Math.max(0,minutes.indexOf(root.prefs[modelData.key+'Minutes'] || modelData.minutes));onActivated:{const values={};values[modelData.key+'Minutes']=minutes[currentIndex];ShelfState.send({action:'utilityPreferences',values:values})}}
      Text{Layout.alignment:Qt.AlignHCenter;text:qsTr('minutes');color:'#aaaab3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
     }
    }
   }
  }
 }
}
