import QtQuick
import QtQuick.Layouts
import qs.services
Item {
 ColumnLayout{anchors.centerIn:parent;spacing:18
  Text{Layout.alignment:Qt.AlignHCenter;text:qsTr('Stay Awake');color:'white';font.family:'SF Pro Display';font.pixelSize:23;font.weight:Font.DemiBold}
  Text{Layout.alignment:Qt.AlignHCenter;text:ShelfState.awakeUntil>Date.now() ? qsTr('%1 minutes remaining').arg(Math.ceil((ShelfState.awakeUntil-ShelfState.now)/60000)):qsTr('Keep automatic idle sleep paused');color:'#aaaab2';font.family:'SF Pro Text';font.pixelSize:13}
  RowLayout{spacing:10
   Repeater{model:[15,30,60,120]
    delegate:ShelfButton{required property int modelData;text:modelData+' min';onClicked:ShelfState.keepAwake(modelData)}
   }
   ShelfButton{text:qsTr('Stop');enabled:ShelfState.awakeUntil>0;onClicked:ShelfState.keepAwake(0)}
  }
  Text{Layout.alignment:Qt.AlignHCenter;visible:!!ShelfState.awakeError;text:ShelfState.awakeError;color:'#ffb4aa';font.family:'SF Pro Text';font.pixelSize:12}
 }
}
