import QtQuick
import QtQuick.Layouts
import qs.components
import qs.services
import qs.rosa.services
ColumnLayout {
 id:root
 property bool settingsPage:false
 property color ink:settingsPage ? Theme.textPrimary:'white'
 property color muted:settingsPage ? Theme.textSecondary:'#9999a3'
 spacing:16
 Text{text:qsTr('Choose your island');color:root.ink;font.family:'SF Pro Display';font.pixelSize:20;font.weight:Font.DemiBold}
 Text{Layout.fillWidth:true;text:qsTr('Choose a floating pill or a notch attached to the top edge. Changes apply immediately.');color:root.muted;font.family:'SF Pro Text';font.pixelSize:12;wrapMode:Text.WordWrap}
 RowLayout{Layout.fillWidth:true;spacing:12
  Repeater{model:[{key:'island',title:qsTr('Dynamic Island'),subtitle:qsTr('Floating pill')},{key:'notch',title:qsTr('Notch'),subtitle:qsTr('Attached to the top')}]
   delegate:Rectangle{required property var modelData;Layout.fillWidth:true;implicitHeight:142;radius:18;color:root.settingsPage ? Theme.card:'#17171b';border.width:IslandConfig.s('surfaceMode')===modelData.key ? 2:1;border.color:IslandConfig.s('surfaceMode')===modelData.key ? Theme.accent:'#333339'
    ColumnLayout{anchors.fill:parent;anchors.margins:14;spacing:8
     Rectangle{Layout.fillWidth:true;Layout.preferredHeight:66;radius:10;color:'#26262d';clip:true
      Rectangle{anchors.horizontalCenter:parent.horizontalCenter;y:modelData.key==='notch' ? -12:12;width:modelData.key==='notch' ? 112:106;height:32;radius:modelData.key==='notch' ? 12:16;color:'black'
       Rectangle{anchors.left:parent.left;anchors.leftMargin:7;anchors.verticalCenter:parent.verticalCenter;width:19;height:19;radius:10;color:'#6366dd';visible:modelData.key==='island'}
       CFVI{anchors.right:parent.right;anchors.rightMargin:9;anchors.verticalCenter:parent.verticalCenter;size:16;icon:'notch/bar-chart2.svg';color:'#9d9dff';visible:modelData.key==='island'}
      }
     }
     Text{text:modelData.title;color:root.ink;font.family:'SF Pro Text';font.pixelSize:14;font.weight:Font.DemiBold}
     Text{text:modelData.subtitle;color:root.muted;font.family:'SF Pro Text';font.pixelSize:11}
    }
    TapHandler{onTapped:IslandConfig.setStyle('surfaceMode',modelData.key)}
    Behavior on border.color{ColorAnimation{duration:SettingsPreferences.accessibility.reduceMotion ? 0:140}}
   }
  }
 }
 RowLayout{Layout.fillWidth:true
  Text{Layout.fillWidth:true;text:qsTr('Other displays');color:root.ink;font.family:'SF Pro Text';font.pixelSize:13}
  ShelfChoice{manageHold:!root.settingsPage;Layout.preferredWidth:170;model:[qsTr('Dynamic Island'),qsTr('Notch')];currentIndex:IslandConfig.s('externalSurfaceMode')==='notch' ? 1:0;onActivated:i=>IslandConfig.setStyle('externalSurfaceMode',i ? 'notch':'island')}
 }
 Text{text:qsTr('Shelf material');color:root.ink;font.family:'SF Pro Text';font.pixelSize:14;font.weight:Font.DemiBold}
 RowLayout{Layout.fillWidth:true;spacing:8
  Repeater{model:[{key:'black',title:qsTr('Black'),icon:'notch/moon.svg'},{key:'glass',title:qsTr('Liquid Glass'),icon:'notch/droplet.svg'},{key:'dynamic',title:qsTr('Gradient'),icon:'notch/layers.svg'}]
   delegate:ShelfButton{required property var modelData;Layout.fillWidth:true;text:modelData.title;icon:modelData.icon;selected:IslandConfig.s('shelfMaterial')===modelData.key;onClicked:IslandConfig.setStyle('shelfMaterial',modelData.key)}
  }
 }
 RowLayout{Layout.fillWidth:true
  Text{Layout.fillWidth:true;text:qsTr('Width');color:root.ink;font.family:'SF Pro Text';font.pixelSize:13}
  ShelfSlider{manageHold:!root.settingsPage;Layout.preferredWidth:180;from:600;to:1400;stepSize:20;value:IslandConfig.s('shelfWidth');onMoved:IslandConfig.setStyle('shelfWidth',value)}
  Text{Layout.preferredWidth:42;text:IslandConfig.s('shelfWidth')+' px';color:root.muted;font.family:'SF Pro Text';font.pixelSize:11}
 }
 RowLayout{Layout.fillWidth:true
  Text{Layout.fillWidth:true;text:qsTr('Height');color:root.ink;font.family:'SF Pro Text';font.pixelSize:13}
  ShelfSlider{manageHold:!root.settingsPage;Layout.preferredWidth:180;from:240;to:520;stepSize:10;value:IslandConfig.s('shelfHeight');onMoved:IslandConfig.setStyle('shelfHeight',value)}
  Text{Layout.preferredWidth:42;text:IslandConfig.s('shelfHeight')+' px';color:root.muted;font.family:'SF Pro Text';font.pixelSize:11}
 }
}
