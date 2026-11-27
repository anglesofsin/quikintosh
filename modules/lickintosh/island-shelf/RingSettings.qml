import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import qs.services
Item{
 id:root;objectName:'shelf-ring-settings'
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Action Ring');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold}
   ShelfChoice{Layout.preferredWidth:128;model:[qsTr('Single ring'),qsTr('Double ring'),qsTr('Triple ring')];currentIndex:(ShelfState.utilityPreferences.ringCount || 1)-1;onActivated:ShelfState.send({action:'utilityPreferences',values:{ringCount:currentIndex+1}})}
   ShelfButton{text:qsTr('Open ring');selected:true;onClicked:{ShelfState.closeRequested();ShelfState.showRing()}}
  }
  Text{Layout.fillWidth:true;text:qsTr('Hold Super+Alt+R, move to an action and release. Change this shortcut in Keyboard settings.');wrapMode:Text.Wrap;color:'#aaaab3';font.family:ShelfStyle.textFamily;font.pixelSize:12}
  GridView{id:grid;Layout.fillWidth:true;Layout.fillHeight:true;cellWidth:width/3;cellHeight:48;clip:true;model:(ShelfState.utilityPreferences.ringCount || 1)*6
   delegate:RowLayout{required property int index;width:grid.cellWidth-10;height:40;spacing:6
    Text{text:index+1;color:'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
    ShelfChoice{Layout.fillWidth:true;model:ShelfState.ringCatalogue.map(a=>a.title);currentIndex:Math.max(0,ShelfState.ringCatalogue.findIndex(a=>a.key===ShelfState.ringKeys[index]));onActivated:{const keys=ShelfState.ringKeys.slice();keys[index]=ShelfState.ringCatalogue[currentIndex].key;ShelfState.send({action:'utilityPreferences',values:{ringActions:keys}})}}
   }
   ScrollBar.vertical:ScrollBar{}
  }
 }
}
