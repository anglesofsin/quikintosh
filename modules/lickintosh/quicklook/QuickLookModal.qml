import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services
Scope {
 Variants {
  model:Quickshell.screens
  delegate:PanelWindow {
   id:shield
   required property var modelData
   screen:modelData
   visible:QuickLookState.opened && Boolean(QuickLookState.geometry.address)
   color:'transparent';exclusionMode:ExclusionMode.Ignore
   anchors{top:true;bottom:true;left:true;right:true}
   WlrLayershell.namespace:'lickintosh-quicklook-modal'
   WlrLayershell.layer:WlrLayer.Overlay
   WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
   readonly property var preview:QuickLookState.geometry
   readonly property bool ownsPreview:preview.monitor===modelData.name
   mask:Region {
    width:shield.width;height:shield.height
    Region {
     x:shield.ownsPreview ? shield.preview.x:0
     y:shield.ownsPreview ? shield.preview.y:0
     width:shield.ownsPreview ? shield.preview.width:0
     height:shield.ownsPreview ? shield.preview.height:0
     radius:20;intersection:Intersection.Subtract
    }
   }
   MouseArea {
    anchors.fill:parent;hoverEnabled:true
    acceptedButtons:Qt.AllButtons
    onPressed:event=>{event.accepted=true;QuickLookState.close()}
    onWheel:event=>event.accepted=true
   }
  }
 }
}
