import QtQuick
import Quickshell.Hyprland
import qs.services
import qs.components.glass
LiquidGlassBackdrop{
 id:root
 required property var host
 readonly property var own:Hyprland.toplevels.values.map(item=>item.lastIpcObject).find(item=>item && item.pid===SettingsState.ownerPid && item['class']==='org.lickintosh.Settings') || ({})
 readonly property var monitor:GlassTracker.monitorSnapshots.find(item=>item.id===root.own.monitor) || ({x:0,y:0})
 property bool precision:false
 property bool firstPosition:true
 ready:!!host?.visible && !!own.address && !SettingsPreferences.accessibility.reduceTransparency
 wallpaperPath:GlassWallpaper.path
 screenSize:host?.screen ? Qt.size(host.screen.width,host.screen.height):Qt.size(1,1)
 windowPosition:Qt.point((own.at?.[0] || 0)-(monitor.x || 0),(own.at?.[1] || 0)-(monitor.y || 0))
 monitorName:host?.screen?.name || ''
 excludedAddress:own.address || ''
 excludedPid:SettingsState.ownerPid
 captureRegion:Qt.rect(windowPosition.x,windowPosition.y,host?.width || 1,host?.height || 1)
 captureWindows:ready && ShellConfig.options.glass.captureWindows
 windowOpacity:ShellConfig.options.glass.windowOpacity
 windowOpacityByClass:ShellConfig.options.glass.windowOpacityByClass
 instantReveal:true;element:'menus'
 onPrecisionChanged:GlassTracker.precisionUsers=Math.max(0,GlassTracker.precisionUsers+(precision ? 1:-1))
 onWindowPositionChanged:{if(firstPosition){firstPosition=false;return}if(ready){precision=true;settle.restart()}}
 Timer{id:settle;interval:250;onTriggered:root.precision=false}
 Connections{target:SettingsState;function onOwnerPidChanged(){Hyprland.refreshToplevels()}}
 onCaptureSettledChanged:{if(captureSettled)GlassRegistry.register(host,root);else GlassRegistry.unregister(root)}
 Component.onCompleted:{if(captureSettled)GlassRegistry.register(host,root);GlassTracker.captureIdleInterval=100;Hyprland.refreshToplevels()}
 Component.onDestruction:{if(precision)GlassTracker.precisionUsers=Math.max(0,GlassTracker.precisionUsers-1);GlassRegistry.unregister(root)}
}
