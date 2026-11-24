import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.ui.widgets
Scope {
 Variants {
  model:Quickshell.screens
  delegate:PanelWindow {
   id:win
   required property var modelData
   screen:modelData
   visible:GameMode.enabled || modelData!==Quickshell.screens[0]
   anchors{left:true;right:true;top:true;bottom:true}
   exclusionMode:ExclusionMode.Ignore;color:'transparent'
   WlrLayershell.layer:WlrLayer.Bottom
   WlrLayershell.namespace:'quickintosh:desktop-input'
   MouseArea {
    anchors.fill:parent;acceptedButtons:Qt.RightButton
    onPressed:mouse=>menu.openAt(mouse.x,mouse.y,DesktopFiles.desktopMenu())
   }
   WidgetContextMenu {
    id:menu
    onChosen:action=>DesktopFiles.handle(action,{kind:"desktop"})
   }
  }
 }
}
