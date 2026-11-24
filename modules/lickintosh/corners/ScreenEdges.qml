import QtQuick
import QtQuick.Shapes
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.services
Scope {
 id:root
 property bool enabled:true
 readonly property var cfg:ShellConfig.options.edges
 function fullscreen(screen){const monitor=Hyprland.monitorFor(screen);return !!monitor?.activeWorkspace?.hasFullscreen}
 component Cutout:Shape {
  id:cutout
  property real cornerRadius:18
  width:cornerRadius;height:cornerRadius
  ShapePath{fillColor:'black';strokeWidth:0;PathSvg{path:'M0,0 L'+cutout.cornerRadius+',0 A'+cutout.cornerRadius+','+cutout.cornerRadius+' 0 0 0 0,'+cutout.cornerRadius+' Z'}}
 }
 Variants{
  model:root.enabled && root.cfg.roundedCorners ? Quickshell.screens:[]
  PanelWindow{
   id:window
   required property var modelData
   screen:modelData;anchors{top:true;bottom:true;left:true;right:true}
   exclusionMode:ExclusionMode.Ignore;exclusiveZone:-1
   WlrLayershell.namespace:'lickintosh-screen-corners';WlrLayershell.layer:WlrLayer.Overlay
   WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
   color:'transparent';mask:Region{}
   visible:root.enabled && !(root.cfg.hideCornersFullscreen && root.fullscreen(modelData))
   Cutout{cornerRadius:root.cfg.cornerRadius;anchors{top:parent.top;left:parent.left}}
   Cutout{cornerRadius:root.cfg.cornerRadius;rotation:90;anchors{top:parent.top;right:parent.right}}
   Cutout{cornerRadius:root.cfg.cornerRadius;rotation:180;anchors{bottom:parent.bottom;right:parent.right}}
   Cutout{cornerRadius:root.cfg.cornerRadius;rotation:270;anchors{bottom:parent.bottom;left:parent.left}}
  }
 }
}
