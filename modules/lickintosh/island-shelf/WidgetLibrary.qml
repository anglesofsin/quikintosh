import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import qs.components
import qs.services
import qs.rosa.services
Item {
 id:root
 signal openPage(int page)
 signal openWidget(string key)
 property int selectedSlot:0
 property string search:''
 property bool favoritesOnly:false
 readonly property var favoriteKeys:ShelfState.utilityPreferences.commandFavorites || []
 readonly property int columns:ShelfState.utilityPreferences.commandColumns || 7
 function favorite(key){const next=favoriteKeys.slice();const index=next.indexOf(key);if(index<0)next.push(key);else next.splice(index,1);ShelfState.send({action:'utilityPreferences',values:{commandFavorites:next}})}
 readonly property var launchers:[
  {key:'calculator',title:qsTr('Calculator'),icon:'grid',command:['quickintosh-calculator']},
  {key:'emoji',title:qsTr('Emoji Picker'),icon:'type',command:['quickintosh','ipc','call','rice','emoji']},
  {key:'spotlight',title:qsTr('Spotlight'),icon:'search',command:['quickintosh','ipc','call','rice','spotlight']},
  {key:'applications',title:qsTr('Applications'),icon:'grid',command:['quickintosh','ipc','call','rice','launchpad']},
  {key:'settings',title:qsTr('Settings'),icon:'settings',command:['quickintosh','ipc','call','rice','settings']}]
 readonly property var visibleWidgets:(ShelfState.editing ? widgets.filter(w=>homeKeys.includes(w.key)):widgets.concat(launchers)).filter(w=>(!favoritesOnly || ShelfState.editing || favoriteKeys.includes(w.key)) && (!search || w.title.toLocaleLowerCase().includes(search.toLocaleLowerCase())))
 readonly property var widgets:[
  {key:'breather',title:qsTr('Break Reminders'),icon:'coffee',page:13},
  {key:'vault',title:qsTr('Obsidian Vault'),icon:'edit-3',page:13},
  {key:'developer',title:qsTr('Developer Tools'),icon:'clipboard',page:13},
  {key:'teleprompter',title:qsTr('Teleprompter'),icon:'type',page:13},
  {key:'media',title:qsTr('Now Playing'),icon:'music',page:3},
  {key:'calendar',title:qsTr('Calendar'),icon:'calender',page:13},
  {key:'weather',title:qsTr('Weather'),icon:'cloud',page:1},
  {key:'focus',title:qsTr('Focus'),icon:'clock',page:13},
  {key:'notes',title:qsTr('Notes'),icon:'edit-3',page:13},
  {key:'performance',title:qsTr('System Stats'),icon:'cpu',page:2},
  {key:'files',title:qsTr('Files'),icon:'inbox',page:6},
  {key:'clipboard',title:qsTr('Clipboard'),icon:'clipboard',page:7},
  {key:'lyrics',title:qsTr('Lyrics'),icon:'type',page:9},
  {key:'audio',title:qsTr('Audio Control'),icon:'volume-2',page:10},
  {key:'notifications',title:qsTr('Notifications'),icon:'bell',page:4},
  {key:'camera',title:qsTr('Camera'),icon:'camera',page:5},
  {key:'awake',title:qsTr('Stay Awake'),icon:'coffee',page:12},
  {key:'storage',title:qsTr('Storage'),icon:'hard-drive',page:14},
  {key:'activities',title:qsTr('Live Activities'),icon:'zap',page:11}]
 readonly property var homeKeys:['media','calendar','weather','focus','notes','performance','files','clipboard','audio','awake','storage','camera','notifications']
 function widget(key){return widgets.find(w=>w.key===key) || {title:qsTr('Add widget'),icon:'plus'}}
 function choose(item){if(item.command){ShelfState.closeRequested();Quickshell.execDetached(item.command);return}if(ShelfState.editing)IslandConfig.setStyle('shelfSlot'+(selectedSlot+1),item.key);else if(item.page===13)openWidget(item.key);else openPage(item.page)}
 function swap(direction){const other=selectedSlot+direction;if(other<0 || other>3)return;const a=IslandConfig.s('shelfSlot'+(selectedSlot+1));IslandConfig.setStyle('shelfSlot'+(selectedSlot+1),IslandConfig.s('shelfSlot'+(other+1)));IslandConfig.setStyle('shelfSlot'+(other+1),a);selectedSlot=other}
 ColumnLayout{anchors.fill:parent;spacing:16
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:ShelfState.editing ? qsTr('Edit Home'):qsTr('Command Center');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:19;font.weight:Font.DemiBold}
   ShelfButton{visible:!ShelfState.editing;flat:true;icon:'notch/edit-3.svg';accessibleLabel:qsTr('Edit Home');onClicked:ShelfState.editing=true}
   ShelfButton{visible:ShelfState.editing;text:qsTr('Done');selected:true;onClicked:{ShelfState.editing=false;root.openPage(0)}}
  }
  RowLayout{visible:!ShelfState.editing;Layout.fillWidth:true;spacing:8
   TextField{Layout.fillWidth:true;placeholderText:qsTr('Find a control or widget');text:root.search;onTextEdited:root.search=text;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:13;leftPadding:12;background:Rectangle{radius:12;color:'#14ffffff';border.color:'#20ffffff'}}
   ShelfButton{flat:true;text:qsTr('Favorites');selected:root.favoritesOnly;onClicked:root.favoritesOnly=!root.favoritesOnly}
   ShelfChoice{Layout.preferredWidth:124;model:[qsTr('Compact'),qsTr('Comfortable'),qsTr('Spacious')];currentIndex:root.columns===7 ? 0:root.columns===5 ? 1:2;onActivated:ShelfState.send({action:'utilityPreferences',values:{commandColumns:[7,5,4][currentIndex]}})}
  }
  RowLayout{visible:ShelfState.editing;Layout.fillWidth:true;spacing:10
   Repeater{model:4
    delegate:Rectangle{required property int index;readonly property var info:root.widget(IslandConfig.s('shelfSlot'+(index+1)));Layout.fillWidth:true;implicitHeight:76;radius:16;color:root.selectedSlot===index ? '#29ffffff':'#0dffffff';border.width:1;border.color:root.selectedSlot===index ? '#a0ffffff':'#1cffffff'
     ColumnLayout{anchors.centerIn:parent;spacing:7
      ShelfIcon{Layout.alignment:Qt.AlignHCenter;size:25;Layout.preferredWidth:25;Layout.preferredHeight:25;icon:'notch/'+info.icon+'.svg';color:'white'}
      Text{text:info.title;font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'white'}
     }
     TapHandler{onTapped:root.selectedSlot=index}
    }
   }
  }
  RowLayout{visible:ShelfState.editing;Layout.fillWidth:true;spacing:7
   ShelfButton{flat:true;icon:Quickshell.shellPath('quicklook/icons/chevron-left.svg');accessibleLabel:qsTr('Move left');enabled:root.selectedSlot>0;onClicked:root.swap(-1)}
   ShelfButton{flat:true;icon:Quickshell.shellPath('quicklook/icons/chevron-right.svg');accessibleLabel:qsTr('Move right');enabled:root.selectedSlot<3;onClicked:root.swap(1)}
   Item{Layout.fillWidth:true}
   Repeater{model:[qsTr('Small'),qsTr('Medium'),qsTr('Large')]
    delegate:ShelfButton{required property string modelData;required property int index;text:modelData;flat:true;selected:IslandConfig.s('shelfWeight'+(root.selectedSlot+1))===index+1;onClicked:IslandConfig.setStyle('shelfWeight'+(root.selectedSlot+1),index+1)}
   }
   Item{Layout.fillWidth:true}
   ShelfButton{flat:true;icon:'notch/trash-2.svg';accessibleLabel:qsTr('Remove widget');onClicked:IslandConfig.setStyle('shelfSlot'+(root.selectedSlot+1),'none')}
  }
  GridView{id:grid;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;boundsBehavior:Flickable.StopAtBounds;reuseItems:true;cellWidth:Math.floor(width/Math.max(1,Math.min(root.columns,Math.floor(width/126))));cellHeight:100
   model:root.visibleWidgets
   ScrollBar.vertical:ScrollBar{policy:ScrollBar.AsNeeded}
   delegate:Item{required property var modelData;width:grid.cellWidth;height:grid.cellHeight
    Rectangle{anchors.horizontalCenter:parent.horizontalCenter;y:3;width:54;height:54;radius:17;color:tileMouse.pressed ? '#42ffffff':tileMouse.containsMouse ? '#24ffffff':'#0dffffff';border.width:1;border.color:'#1cffffff'
     ShelfIcon{anchors.centerIn:parent;size:29;Layout.preferredWidth:29;Layout.preferredHeight:29;icon:'notch/'+modelData.icon+'.svg';color:'white'}
    }
    Text{anchors.left:parent.left;anchors.right:parent.right;y:68;text:modelData.title;horizontalAlignment:Text.AlignHCenter;font.family:ShelfStyle.textFamily;font.pixelSize:12;color:'#d7d7dc';elide:Text.ElideRight}
    MouseArea{id:tileMouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;acceptedButtons:Qt.LeftButton | Qt.RightButton;onClicked:mouse=>{if(mouse.button===Qt.RightButton)root.favorite(modelData.key);else root.choose(modelData)}}
    Text{visible:root.favoriteKeys.includes(modelData.key);anchors.right:parent.right;anchors.rightMargin:12;y:4;text:'★';color:'#ffd166';font.pixelSize:11}
    Accessible.role:Accessible.Button;Accessible.name:modelData.title;Accessible.onPressAction:root.choose(modelData)
   }
  }
 }
}
