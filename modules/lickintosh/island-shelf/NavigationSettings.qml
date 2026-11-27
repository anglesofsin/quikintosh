import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import qs.services
import qs.components
ColumnLayout{
 id:root;objectName:'shelf-navigation-settings'
 property bool settingsPage:false
 readonly property color ink:settingsPage ? Theme.textPrimary:ShelfStyle.primary
 Text{text:qsTr('Navigation');font.family:ShelfStyle.textFamily;font.pixelSize:15;font.weight:Font.DemiBold;color:root.ink}
 Rectangle{Layout.fillWidth:true;implicitHeight:options.implicitHeight+8;radius:12;color:root.settingsPage ? Theme.card:'#0dffffff';border.width:1;border.color:'#20ffffff'
  ColumnLayout{id:options;anchors.left:parent.left;anchors.right:parent.right;anchors.margins:12;y:4;spacing:0
   Repeater{model:[{key:'navigationShown',label:qsTr('Show navigation'),value:ShelfNavigation.shown},{key:'navigationWidgets',label:qsTr('Show widgets page'),value:ShelfNavigation.widgetsShown},{key:'navigationTrayOnlyWithFiles',label:qsTr('Show Tray only when it contains files'),value:ShelfNavigation.trayOnlyWithFiles},{key:'navigationGestures',label:qsTr('Swipe between pages'),value:ShelfNavigation.gestures}]
    RowLayout{required property var modelData;Layout.fillWidth:true;Layout.preferredHeight:42
     Text{Layout.fillWidth:true;text:modelData.label;color:root.ink;font.family:ShelfStyle.textFamily;font.pixelSize:13}
     Switch{id:toggle;checked:modelData.value;onToggled:ShelfNavigation.set(modelData.key,checked);padding:0;implicitWidth:40;implicitHeight:24
      indicator:Rectangle{width:40;height:24;radius:12;color:toggle.checked ? '#30d158':'#55555b';Rectangle{x:toggle.checked ? 18:2;y:2;width:20;height:20;radius:10;color:'white';Behavior on x{NumberAnimation{duration:120}}}}
      contentItem:Item{}
     }
    }
   }
  }
 }
 Text{text:qsTr('Favorites');font.family:ShelfStyle.textFamily;font.pixelSize:15;font.weight:Font.DemiBold;color:root.ink}
 Rectangle{Layout.fillWidth:true;implicitHeight:slots.implicitHeight+16;radius:12;color:root.settingsPage ? Theme.card:'#0dffffff';border.width:1;border.color:'#20ffffff'
  ColumnLayout{id:slots;anchors.left:parent.left;anchors.right:parent.right;anchors.margins:12;y:8;spacing:8
   Repeater{model:4
    RowLayout{required property int index;Layout.fillWidth:true
     Text{Layout.fillWidth:true;text:qsTr('Favorite %1').arg(index+1);font.family:ShelfStyle.textFamily;font.pixelSize:13;color:root.ink}
     ShelfChoice{objectName:'navigation-favorite-'+index;manageHold:!root.settingsPage;Layout.preferredWidth:220;model:ShelfNavigation.choices.map(item=>item.title);currentIndex:Math.max(0,ShelfNavigation.choices.findIndex(item=>item.key===(ShelfState.utilityPreferences.navigationFavorites || [])[index]));onActivated:i=>ShelfNavigation.pin(index,ShelfNavigation.choices[i].key)}
    }
   }
  }
 }
}
