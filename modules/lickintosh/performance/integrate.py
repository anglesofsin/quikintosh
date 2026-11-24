"""Avoid publishing unchanged state and repeated storage work on hot paths."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(name,old,new):
 p=root/name;s=p.read_text()
 if old not in s:raise ValueError('Performance anchor: '+name+' '+old[:60])
 p.chmod(p.stat().st_mode|0o200);p.write_text(s.replace(old,new))
edit('services/MediaCaptureState.qml',' function _parse(text){',' property string captureSignature:""\n function _parse(text){')
edit('services/MediaCaptureState.qml','  detected=result.details;cameraApps=result.camera;micApps=result.mic;screenApps=result.screen;audioApps=result.audio','  const signature=JSON.stringify(result)\n  if(signature===root.captureSignature)return\n  root.captureSignature=signature\n  detected=result.details;cameraApps=result.camera;micApps=result.mic;screenApps=result.screen;audioApps=result.audio')
edit('tahoedock/TahoeDockSurface.qml'," function remember(){send({action:'remember',apps:controller.groupedClients.filter(g=>!root.blocked(g.key)).map(g=>({key:g.key,name:g.displayName,icon:g.iconPath}))})}"," property string recentSignature:''\n function remember(){const apps=controller.groupedClients.filter(g=>!root.blocked(g.key)).map(g=>({key:g.key,name:g.displayName,icon:g.iconPath}));const signature=JSON.stringify(apps);if(signature===root.recentSignature)return;root.recentSignature=signature;send({action:'remember',apps:apps})}")
# Thumbnail completion and app-history replies must not trigger identical models.
edit('services/WallpaperLibrary.qml'," property var incoming:({})", " property var incoming:({})\n property double refreshed:0\n property string refreshedDirectory:''")
edit('services/WallpaperLibrary.qml',"function refresh(){if(!ready || !ShellConfig.ready)return;", "function refresh(){if(!ready || !ShellConfig.ready)return;if(root.loaded && root.refreshedDirectory===root.userDir && Date.now()-root.refreshed<1500)return;root.refreshed=Date.now();root.refreshedDirectory=root.userDir;")
# Screen/monitor fallback does not need to publish identical objects every second.
edit('rosa/overlays/IslandWindow.qml','    property var fallbackMonitors:[]','    property var fallbackMonitors:[]\n    property string fallbackMonitorSignature:""')
edit('rosa/overlays/IslandWindow.qml','win.fallbackMonitors=monitors.map(', 'const next=monitors.map(')
edit('rosa/overlays/IslandWindow.qml','m.specialWorkspace.id))}))}catch(e)', 'm.specialWorkspace.id))}));const signature=JSON.stringify(next);if(signature!==win.fallbackMonitorSignature){win.fallbackMonitorSignature=signature;win.fallbackMonitors=next}}catch(e)')
# A silent/unchanged spectrum does not need to allocate two arrays and notify
# every equalizer delegate again. Changed frames retain the original 60 Hz path.
edit('rosa/services/Cava.qml','    property var levels: root.zeros()','    property string lastFrame:""\n    property var levels: root.zeros()')
edit('rosa/services/Cava.qml','            onRead: data => {','            onRead: data => {\n                if(data===root.lastFrame)return;root.lastFrame=data')
edit('rosa/services/Cava.qml','        root.levels = root.zeros();','        root.lastFrame="";\n        root.levels = root.zeros();')
