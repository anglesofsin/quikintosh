import QtQuick
import QtQuick.Shapes
import Quickshell.Io
import Quickshell.Hyprland
import qs.services

// The bar stays rectangular. Inverse quarter-circles extend below its edges,
// masking the desktop around the rounded top corners of a maximized window.
Item {
 id:root
 property bool fullscreen:false
 readonly property var cfg:ShellConfig.options.topbar
 readonly property real cornerRadius:ShellConfig.options.edges.roundMenuBackground && !(fullscreen && ShellConfig.options.edges.hideCornersFullscreen) ? ShellConfig.options.edges.menuCornerRadius:0
 readonly property color paint:cfg.backgroundEnabled ? cfg.backgroundColor:'#000000'
 readonly property real paintOpacity:cfg.backgroundEnabled ? cfg.backgroundOpacity:(cfg.blurEnabled ? 0.02:0)
 visible:(cfg.backgroundEnabled || cfg.blurEnabled) && root.y+root.height>0
 opacity:paintOpacity
 // Match only edge-maximized clients to the cutout radius. A named rule restores
 // their normal decoration automatically when the maximize tag is removed.
 readonly property bool matchCorners:ShellConfig.options.edges.roundMenuBackground && (cfg.backgroundEnabled || cfg.blurEnabled)
 readonly property int matchingRadius:ShellConfig.options.edges.menuCornerRadius
 property bool initialized:false
 property bool pendingRule:false
 function scheduleRule(){if(initialized)cornerRuleDelay.restart()}
 onMatchCornersChanged:scheduleRule()
 onMatchingRadiusChanged:scheduleRule()
 Component.onCompleted:{initialized=true;scheduleRule()}
 Connections{target:Hyprland;function onRawEvent(event){if(event.name==='configreloaded')root.scheduleRule()}}
 Timer{id:cornerRuleDelay;interval:120;onTriggered:{if(cornerRule.running)root.pendingRule=true;else cornerRule.running=true}}
 Process{
  id:cornerRule
  command:['hyprctl','eval',"hl.window_rule({name='quickintosh-menubar-corners',enabled="+(root.matchCorners ? 'true':'false')+",match={tag='quickintosh-maximized'},rounding="+root.matchingRadius+"}); for _,w in ipairs(hl.get_windows()) do local m=w.monitor; if m and w.fullscreen==0 then local a=m.reserved; if math.abs(w.at.x-(m.x+a.left))<1 and math.abs(w.at.y-(m.y+a.top))<1 and math.abs(w.size.x-(m.mode.width-a.left-a.right))<1 and math.abs(w.size.y-(m.mode.height-a.top-a.bottom))<1 then local tagged=false;for _,t in ipairs(w.tags or {}) do if t=='quickintosh-maximized' then tagged=true end end;if not tagged then hl.dispatch(hl.dsp.window.tag({tag='+quickintosh-maximized',window='address:'..w.address})) end end end end"]
  onExited:if(root.pendingRule){root.pendingRule=false;cornerRuleDelay.restart()}
 }

 Rectangle{anchors.fill:parent;color:root.paint}
 component OuterCorner:Shape {
  width:root.cornerRadius;height:root.cornerRadius
  ShapePath{strokeWidth:0;fillColor:root.paint
   PathSvg{path:'M0,0 L'+root.cornerRadius+',0 A'+root.cornerRadius+','+root.cornerRadius+' 0 0 0 0,'+root.cornerRadius+' Z'}
  }
 }
 OuterCorner{x:0;y:root.height;visible:root.cornerRadius>0}
 OuterCorner{x:root.width-width;y:root.height;visible:root.cornerRadius>0;transform:Scale{xScale:-1;origin.x:root.cornerRadius/2}}
}
