import QtQuick
import QtQuick.Layouts
import qs.services
Item{
 id:root;objectName:'shelf-selection-settings'
 ColumnLayout{anchors.fill:parent;spacing:14
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Selection Actions');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:19;font.weight:Font.DemiBold}
   ShelfButton{text:ShelfState.utilityPreferences.selectionActionsEnabled ? qsTr('On'):qsTr('Off');selected:ShelfState.utilityPreferences.selectionActionsEnabled===true;onClicked:ShelfState.send({action:'utilityPreferences',values:{selectionActionsEnabled:ShelfState.utilityPreferences.selectionActionsEnabled!==true}})}
  }
  Text{Layout.fillWidth:true;text:qsTr('Show Copy and Search next to selected text. Selection text stays in memory and is cleared when the actions close. Search opens only when you click it.');wrapMode:Text.Wrap;color:'#aaaab3';font.family:ShelfStyle.textFamily;font.pixelSize:13}
  Text{visible:ShelfState.selectionError!=='';Layout.fillWidth:true;text:ShelfState.selectionError;wrapMode:Text.Wrap;color:'#ff827b';font.family:ShelfStyle.textFamily;font.pixelSize:12}
  Item{Layout.fillHeight:true}
 }
}
