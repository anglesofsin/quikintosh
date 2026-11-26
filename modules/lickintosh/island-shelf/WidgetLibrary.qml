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
 property int tab:0
 property int selectedSlot:0
 readonly property var widgets:[{key:'media',title:qsTr('Now Playing'),icon:'music',detail:qsTr('Artwork and playback')},{key:'calendar',title:qsTr('Calendar'),icon:'calender',detail:qsTr('Dates and events')},{key:'weather',title:qsTr('Weather'),icon:'cloud',detail:qsTr('Current conditions')},{key:'focus',title:qsTr('Focus'),icon:'clock',detail:qsTr('Focus timer')},{key:'notes',title:qsTr('Notes'),icon:'edit-3',detail:qsTr('Your quick notes')},{key:'performance',title:qsTr('System'),icon:'cpu',detail:qsTr('CPU and memory')},{key:'files',title:qsTr('Files'),icon:'inbox',detail:qsTr('Your file tray')}]
 function widget(key){return widgets.find(w=>w.key===key) || {title:qsTr('Empty'),icon:'plus',detail:''}}
 function setWidget(key){IslandConfig.setStyle('shelfSlot'+(selectedSlot+1),key)}
 function swap(direction){const other=selectedSlot+direction;if(other<0 || other>3)return;const a=IslandConfig.s('shelfSlot'+(selectedSlot+1));const b=IslandConfig.s('shelfSlot'+(other+1));IslandConfig.setStyle('shelfSlot'+(selectedSlot+1),b);IslandConfig.setStyle('shelfSlot'+(other+1),a);selectedSlot=other}
 ColumnLayout{anchors.fill:parent;spacing:16
  RowLayout{Layout.fillWidth:true
   ColumnLayout{Layout.fillWidth:true;spacing:3
    Text{text:qsTr('Customize your island');color:'white';font.family:'SF Pro Display';font.pixelSize:21;font.weight:Font.DemiBold}
    Text{text:qsTr('Your editor stays open until you finish.');color:'#9999a3';font.family:'SF Pro Text';font.pixelSize:12}
   }
   ShelfButton{text:qsTr('Done');icon:'notch/check.svg';selected:true;onClicked:{ShelfState.editing=false;root.openPage(0)}}
  }
  RowLayout{spacing:5
   Repeater{model:[{title:qsTr('Widgets'),icon:'grid'},{title:qsTr('Appearance'),icon:'sliders'},{title:qsTr('Tools'),icon:'command'}]
    delegate:ShelfButton{required property var modelData;required property int index;text:modelData.title;icon:'notch/'+modelData.icon+'.svg';selected:root.tab===index;onClicked:root.tab=index}
   }
   Item{Layout.fillWidth:true}
   ShelfChoice{visible:root.tab===0;Layout.preferredWidth:190;model:[qsTr('Choose a layout…'),qsTr('Music · Calendar · Weather'),qsTr('Focus · Notes · Files')];onActivated:i=>{if(i>0)for(const [n,key] of (i===1 ? ['media','calendar','weather','none']:['focus','notes','files','none']).entries()){IslandConfig.setStyle('shelfSlot'+(n+1),key);IslandConfig.setStyle('shelfWeight'+(n+1),1)}currentIndex=0}}
  }
  Flickable{id:scroll;Layout.fillWidth:true;Layout.fillHeight:true;contentWidth:width;contentHeight:content.implicitHeight;clip:true;boundsBehavior:Flickable.StopAtBounds;ScrollBar.vertical:ScrollBar{}
   ColumnLayout{id:content;width:scroll.width;spacing:18
    ColumnLayout{visible:root.tab===0;Layout.fillWidth:true;spacing:14
     RowLayout{Layout.fillWidth:true;spacing:10
      Repeater{model:4
       delegate:Rectangle{required property int index;Layout.fillWidth:true;implicitHeight:108;radius:16;color:root.selectedSlot===index ? '#29292f':'#151518';border.width:root.selectedSlot===index ? 2:1;border.color:root.selectedSlot===index ? Theme.accent:'#303036'
        readonly property var info:root.widget(IslandConfig.s('shelfSlot'+(index+1)))
        ColumnLayout{anchors.fill:parent;anchors.margins:12;spacing:8
         RowLayout{Layout.fillWidth:true
          CFVI{size:22;icon:'notch/'+info.icon+'.svg';color:root.selectedSlot===index ? Theme.accent:'#a0a0aa'}
          Item{Layout.fillWidth:true}
          Text{text:String(index+1);color:'#777780';font.family:'SF Pro Text';font.pixelSize:11}
         }
         Item{Layout.fillHeight:true}
         Text{Layout.fillWidth:true;text:info.title;color:'white';font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold;elide:Text.ElideRight}
         Rectangle{Layout.fillWidth:true;implicitHeight:3;radius:2;color:'#333338';Rectangle{height:parent.height;radius:2;width:parent.width*IslandConfig.s('shelfWeight'+(index+1))/3;color:root.selectedSlot===index ? Theme.accent:'#777780'}}
        }
        TapHandler{onTapped:root.selectedSlot=index}
        Behavior on color{ColorAnimation{duration:SettingsPreferences.accessibility.reduceMotion ? 0:140}}
       }
      }
     }
     RowLayout{Layout.fillWidth:true;spacing:6
      Text{Layout.fillWidth:true;text:qsTr('Position %1').arg(root.selectedSlot+1);color:'#aaaab4';font.family:'SF Pro Text';font.pixelSize:12}
      ShelfButton{icon:'notch/skip-back.svg';enabled:root.selectedSlot>0;onClicked:root.swap(-1)}
      ShelfButton{icon:'notch/skip-forward.svg';enabled:root.selectedSlot<3;onClicked:root.swap(1)}
      Repeater{model:[qsTr('Compact'),qsTr('Balanced'),qsTr('Wide')]
       delegate:ShelfButton{required property string modelData;required property int index;text:modelData;selected:IslandConfig.s('shelfWeight'+(root.selectedSlot+1))===index+1;onClicked:IslandConfig.setStyle('shelfWeight'+(root.selectedSlot+1),index+1)}
      }
      ShelfButton{icon:'notch/trash-2.svg';enabled:IslandConfig.s('shelfSlot'+(root.selectedSlot+1))!=='none';onClicked:root.setWidget('none')}
     }
     Text{text:qsTr('Choose a widget for this position');color:'white';font.family:'SF Pro Text';font.pixelSize:14;font.weight:Font.DemiBold}
     GridLayout{Layout.fillWidth:true;columns:scroll.width<700 ? 2:3;columnSpacing:10;rowSpacing:10
      Repeater{model:root.widgets
       delegate:Rectangle{required property var modelData;Layout.fillWidth:true;implicitHeight:76;radius:16;color:cardMouse.containsMouse ? '#27272d':'#17171b';border.color:IslandConfig.s('shelfSlot'+(root.selectedSlot+1))===modelData.key ? Theme.accent:'#303036'
        RowLayout{anchors.fill:parent;anchors.margins:14;spacing:12
         Rectangle{Layout.preferredWidth:38;Layout.preferredHeight:38;radius:12;color:'#2b2b33';CFVI{anchors.centerIn:parent;size:21;icon:'notch/'+modelData.icon+'.svg';color:'#d3d3de'}}
         ColumnLayout{Layout.fillWidth:true;spacing:4
          Text{Layout.fillWidth:true;text:modelData.title;color:'white';font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold;elide:Text.ElideRight}
          Text{Layout.fillWidth:true;text:modelData.detail;color:'#9696a0';font.family:'SF Pro Text';font.pixelSize:11;elide:Text.ElideRight}
         }
         CFVI{size:16;icon:IslandConfig.s('shelfSlot'+(root.selectedSlot+1))===modelData.key ? 'notch/check.svg':'notch/plus.svg';color:'#c5c5d0'}
        }
        MouseArea{id:cardMouse;anchors.fill:parent;hoverEnabled:true;onClicked:root.setWidget(modelData.key)}
       }
      }
     }
     RowLayout{Layout.fillWidth:true
      ShelfButton{text:qsTr('Arrange directly on shelf');icon:'notch/move.svg';onClicked:{ShelfState.editing=true;root.openPage(0)}}
      Item{Layout.fillWidth:true}
      ShelfButton{text:qsTr('All settings');icon:'notch/settings.svg';onClicked:SettingsLauncher.open('RosaPage')}
     }
    }
    ShelfAppearance{visible:root.tab===1;Layout.fillWidth:true}
    GridLayout{visible:root.tab===2;Layout.fillWidth:true;columns:scroll.width<700 ? 2:3;columnSpacing:10;rowSpacing:10
     Repeater{model:[{title:qsTr('Weather'),icon:'cloud',page:1},{title:qsTr('System'),icon:'cpu',page:2},{title:qsTr('Notifications'),icon:'bell',page:4},{title:qsTr('Camera'),icon:'camera',page:5},{title:qsTr('Clipboard'),icon:'clipboard',page:7},{title:qsTr('Lyrics'),icon:'type',page:9},{title:qsTr('App volume'),icon:'volume-2',page:10},{title:qsTr('Activities'),icon:'zap',page:11},{title:qsTr('Stay Awake'),icon:'coffee',page:12}]
      delegate:ShelfButton{required property var modelData;Layout.fillWidth:true;implicitHeight:54;text:modelData.title;icon:'notch/'+modelData.icon+'.svg';onClicked:root.openPage(modelData.page)}
     }
    }
   }
  }
 }
}
