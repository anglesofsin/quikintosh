"""Shared expanded-surface antialiasing and media presentation integration."""
from pathlib import Path

def edit(root,name,fn):
 p=root/name;s=p.read_text()
 if p.is_symlink():p.unlink()
 else:p.chmod(0o644)
 p.write_text(fn(s))

def dashboard(s):
 s=s.replace('        id: body\n','        id: body\n        antialiasing:true\n        layer.enabled:true\n        layer.smooth:true\n        layer.samples:4\n',1)
 s=s.replace('queue:360','queue:540').replace('"selection","queue","jobs"','"selection","jobs"')
 s=s.replace('import QtQuick\n','import QtQuick\nimport qs.rosa.reusables as MediaVisual\n',1)
 s=s.replace('        HoverHandler { id: dashboardHover;', '''        MediaVisual.ArtTint{id:queueTint;source:MprisState.artUrl;fallback:'#26216a'}
        Rectangle{anchors.fill:parent;radius:body.radius;visible:panel.page===13 && panel.detailWidget==='queue';gradient:Gradient{GradientStop{position:0;color:'transparent'}GradientStop{position:.35;color:'transparent'}GradientStop{position:1;color:Qt.rgba(queueTint.color.r*.45,queueTint.color.g*.45,queueTint.color.b*.45,.85)}}}
        HoverHandler { id: dashboardHover;''',1)
 return s

def integrate(root):
 root=Path(root)
 edit(root,'rosa/overlays/IslandDashboard.qml',dashboard)
 # A screenshot always opens its transient expanded card, even with other
 # activities configured not to auto-expand. No compact screenshot pill.
 edit(root,'rosa/overlays/IslandWindow.qml',lambda s:s.replace('(win.hub.flashKind !== "" && win.bigEvent && IslandConfig.s("autoWide"))','(win.hub.kind === "shot" || (win.hub.flashKind !== "" && win.bigEvent && IslandConfig.s("autoWide")))'))
