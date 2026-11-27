"""Single continuous alpha contour, shared by notch and detached surfaces."""
from pathlib import Path
import runpy
edit=runpy.run_path(str(Path(__file__).with_name('media_polish.py')))['edit']
def integrate(root):
 root=Path(root)
 p=root/'island-shelf/qmldir';p.write_text(p.read_text()+'\nShelfRoundedSurface ShelfRoundedSurface.qml\n')
 def dashboard(s):
  return s.replace('ClippingRectangle {\n        id: body','ShelfRoundedSurface {\n        id: body',1).replace('        layer.enabled:true\n        layer.smooth:true\n        layer.samples:4\n','',1)
 edit(root,'rosa/overlays/IslandDashboard.qml',dashboard)
 def window(s):
  s=s.replace('visible: !pill.newEvent && IslandConfig.s("goo")', 'visible: !(win.attachedNotch && win.wideKind==="media") && !pill.newEvent && IslandConfig.s("goo")',1)
  s=s.replace('visible: pill.newEvent || !IslandConfig.s("goo")', 'visible: (win.attachedNotch && win.wideKind==="media") || pill.newEvent || !IslandConfig.s("goo")',1)
  s=s.replace('                Rectangle{visible:win.attachedNotch;anchors.top:parent.top;width:parent.width;height:Math.min(parent.height/2,18);color:parent.color}', '                topLeftRadius:win.attachedNotch ? 0:radius\n                topRightRadius:win.attachedNotch ? 0:radius',1)
  s=s.replace('            ClippingRectangle {\n                anchors.fill: parent\n                radius: surface.corner', '            ShelfVisual.ShelfRoundedSurface {\n                id:activityClip\n                anchors.fill: parent\n                radius: surface.corner\n                topLeftRadius:win.attachedNotch ? 0:radius\n                topRightRadius:win.attachedNotch ? 0:radius',1)
  s=s.replace('import qs.services as NativeSettings','import "../../island-shelf" as ShelfVisual\nimport qs.services as NativeSettings',1)
  return s
 edit(root,'rosa/overlays/IslandWindow.qml',window)
