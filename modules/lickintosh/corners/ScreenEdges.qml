import QtQuick
import QtQuick.Shapes
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.services
import qs.components.glass
Scope {
 id:root
 property bool enabled:true
 readonly property var cfg:ShellConfig.options.edges
 readonly property bool watching:enabled && cfg.roundedCorners
 property bool subscribed:false
 function syncInventory(){if(subscribed===watching)return;subscribed=watching;GlassTracker.inventoryUsers+=watching ? 1:-1;if(watching){GlassTracker.refreshWindows();GlassTracker.refreshMonitorSnapshot()}}
 onWatchingChanged:syncInventory()
 Component.onCompleted:syncInventory()
 Component.onDestruction:if(subscribed)GlassTracker.inventoryUsers--
 function fullscreen(screen){
  const monitor=Hyprland.monitorFor(screen)
  if(!monitor)return false
  const ws=monitor.activeWorkspace?.id
  return GlassTracker.clientsSnapshot.some(w=>(w.monitor===monitor.id || w.monitor?.id===monitor.id) && w.workspace?.id===ws && !w.hidden && w.mapped!==false && w.fullscreen===2)
 }
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
