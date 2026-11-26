import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.services
Item {
 Layout.fillWidth:true;implicitHeight:110
 Rectangle{anchors.fill:parent;radius:12;color:Theme.isLight ? '#e6e9ef':'#191b20'}
 Rectangle{
  anchors.centerIn:parent
  width:icons.implicitWidth+24;height:72;radius:19
  color:Theme.isLight ? '#a0ffffff':'#60434a53';border.width:1;border.color:Theme.cardRim
  Row{
   id:icons;anchors.centerIn:parent;spacing:8
   Repeater{
    model:ShellConfig.options.dock.pinnedApps.slice(0,6)
    delegate:Item{
     required property var modelData
     width:48;height:48
     Image{anchors.centerIn:parent;width:Math.min(52,ShellConfig.options.dockAppearance.iconSize*.75);height:width;source:LayeredIcons.resolve(parent.modelData.iconPath ? QuickLookState.urlFor(parent.modelData.iconPath):IconResolver.byName(parent.modelData.icon || 'applications-system'),parent.modelData.name);sourceSize:Qt.size(96,96);fillMode:Image.PreserveAspectFit;asynchronous:true}
    }
   }
  }
 }
}
