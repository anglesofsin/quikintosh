"""Expanded transient events return straight to the normal compact island."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(name,old,new):
 p=root/name;s=p.read_text()
 if s.count(old)!=1:raise ValueError(f'Transient notification anchor {name}: {old[:70]} ({s.count(old)})')
 p.write_text(s.replace(old,new,1))

window='rosa/overlays/IslandWindow.qml'
edit(window,'if(win.previousKind === "shot" && win.hub.kind !== "shot")', 'if(["shot","notif","clip","cmd","weather","bt","peri","power","net","vpn","done","fail","desk","keys"].includes(win.previousKind) && win.hub.kind !== win.previousKind)')
edit(window,'(win.hub.kind === "shot" && IslandConfig.s("autoWide"))', '(win.hub.flashKind !== "" && win.bigEvent && IslandConfig.s("autoWide"))')
hub='rosa/overlays/Island.qml'
p=root/hub;s=p.read_text();old='if(root.flashKind === "shot") {root.flashText="";root.flashGlyph="";root.flashFraction=-1;}'
assert s.count(old)==2;s=s.replace(old,'root.flashText="";root.flashGlyph="";root.flashFraction=-1;');p.write_text(s)
body='rosa/overlays/IslandBody.qml'
edit(body,'    onKindChanged:if(body.kind === "shot")body.shotPresented=true','''    function transient(kind){return ["shot","notif","clip","cmd","weather","bt","peri","power","net","vpn","done","fail","desk","keys"].includes(kind)}
    onKindChanged:if(body.transient(body.kind))body.shotPresented=true''')
edit(body,'if(body.kind !== "shot")body.shotPresented=false;', 'if(!body.transient(body.kind))body.shotPresented=false;')
# Observability for actual lifecycle verification, no additional test-only IPC.
edit('RosaIntegration.qml','kind:islandLoader.item ? islandLoader.item.kind : "",','kind:islandLoader.item ? islandLoader.item.kind : "",flashKind:islandLoader.item ? islandLoader.item.flashKind : "",')
