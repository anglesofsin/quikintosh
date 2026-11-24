import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.services
Scope{
 id:root
 property bool enabled:true
 readonly property var cfg:ShellConfig.options.edges
 signal actionRequested(string action)
 Variants{
  model:root.enabled && root.cfg.hotCorners ? Quickshell.screens:[]
  Scope{
   id:perScreen
   required property var modelData
   property var monitor:modelData
   Variants{
    model:['topLeft','topRight','bottomLeft','bottomRight']
    PanelWindow{
     id:zone
     required property string modelData
     screen:perScreen.monitor
     readonly property var cfg:root.cfg
     readonly property bool full:!!Hyprland.monitorFor(screen)?.activeWorkspace?.hasFullscreen
     readonly property bool right:modelData.endsWith('Right')
     readonly property bool bottom:modelData.startsWith('bottom')
     anchors{top:!zone.bottom;bottom:zone.bottom;left:!zone.right;right:zone.right}
     implicitWidth:2;implicitHeight:2;color:'transparent';exclusiveZone:-1
     exclusionMode:ExclusionMode.Ignore
     WlrLayershell.namespace:'lickintosh-hot-corner-'+modelData
     WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
     visible:root.enabled && root.cfg.hotCorners && cfg[modelData+'Action']!=='none' && !(cfg.hideHotCornersFullscreen && full)
     CornerTrigger{
      id:trigger;enabled:zone.visible;delay:cfg.hotCornerDelay
      action:cfg[zone.modelData+'Action'];requiredModifiers:cfg[zone.modelData+'Modifiers']
      onTriggered:action=>root.actionRequested(action)
     }
     MouseArea{
      anchors.fill:parent;hoverEnabled:true;acceptedButtons:Qt.NoButton
      onEntered:{trigger.inside=true;trigger.update()}
      onPositionChanged:event=>{trigger.modifiers=event.modifiers;trigger.inside=true}
      onExited:{trigger.inside=false;checkLeave.running=true}
     }
     // A popup stealing pointer focus must not count as leaving the corner.
     Process{
      id:checkLeave;command:['hyprctl','cursorpos','-j']
      stdout:StdioCollector{onStreamFinished:{try{const p=JSON.parse(text),s=zone.screen,m=Hyprland.monitorFor(s),mx=m?.x || 0,my=m?.y || 0;const x=mx+(zone.right ? s.width-2:0),y=my+(zone.bottom ? s.height-2:0);if(p.x<x || p.x>=x+2 || p.y<y || p.y>=y+2)trigger.leave();else if(trigger.fired)leavePoll.restart()}catch(error){trigger.leave()}}}
     }
     Timer{id:leavePoll;interval:160;onTriggered:if(trigger.fired && !checkLeave.running)checkLeave.running=true}
    }
   }
  }
 }
}
