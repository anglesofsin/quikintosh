import QtQuick
import Quickshell
import qs.services
import qs.components.glass
Item{
  id:material
  property real cornerRadius:22
  readonly property bool captureReady:backdrop.captureSettled
  readonly property var materialState:({wallpaper:backdrop.wallpaperPath,tint:String(backdrop.tint),dim:ShellConfig.options.wallpaper.dim,host:!!host,ready:backdrop.ready,warm:backdrop.warm,settled:backdrop.captureSettled,region:backdrop.captureRegion,quads:backdrop.quads.length,screen:backdrop.screenSize,position:backdrop.windowPosition})
  readonly property var host:material.parent?.QsWindow.window || null
  function syncPosition(){
   if(!host || !material.parent)return
   const screen=host.screen;let origin=Qt.point(0,0)
   if(host.anchors){const a=host.anchors,m=host.margins;origin=Qt.point(a.left ? m.left:a.right ? screen.width-host.width-m.right:(screen.width-host.width)/2,a.top ? m.top:a.bottom ? screen.height-host.height-m.bottom:(screen.height-host.height)/2)}
   else{const window=GlassTracker.clientsSnapshot.find(c=>c.title===host.title);if(window)origin=Qt.point(window.at[0]-(screen?.x || 0),window.at[1]-(screen?.y || 0))}
   const position=origin
   if(position.x!==backdrop.windowPosition.x || position.y!==backdrop.windowPosition.y)backdrop.windowPosition=position
  }
  FrameAnimation{running:material.visible;onTriggered:material.syncPosition()}

  LiquidGlassBackdrop{
   excludedPid:Quickshell.processId
   id:backdrop;element:'menus';ready:!!material.host && (material.visible || (false && material.parent?.visible));instantReveal:true
   wallpaperPath:GlassWallpaper.path
   screenSize:material.host?.screen ? Qt.size(material.host.screen.width,material.host.screen.height):Qt.size(1920,1080)
   monitorName:material.host?.screen?.name || ''
   windowPosition:Qt.point(0,0)
   captureWindows:ShellConfig.options.glass.captureWindows;captureInterval:ShellConfig.options.glass.captureIntervalMs
   aa:Math.max(1,GlassTracker.backdropScale)
   blurDownscale:Math.max(.5,RenderingState.blurScale)
   blurRadius:32
  }
  Rectangle{anchors.fill:parent;radius:material.cornerRadius;color:'#d92b2b32';visible:!backdrop.captureSettled}
  TahoeGlass{anchors.fill:parent;backdrop:backdrop.ready ? backdrop:null;cornerRadius:material.cornerRadius;autoDarken:false;refractionWidth:1.5;highlightStrength:.15;materialOpacity:1;centerOpacity:1}
  Rectangle{anchors.fill:parent;radius:material.cornerRadius;color:'#b21c1c20';border.width:1;border.color:'#27ffffff'}
 }
