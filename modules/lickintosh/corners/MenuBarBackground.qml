import QtQuick
import QtQuick.Shapes
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
