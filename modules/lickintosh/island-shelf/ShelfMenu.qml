import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import qs.services
import qs.components.glass
Menu {
 id:root
 implicitWidth:264
 width:264
 popupType:Popup.Item
 closePolicy:Popup.CloseOnEscape | Popup.CloseOnPressOutside
 readonly property var materialState:background?.materialState || ({})
 readonly property bool glassReady:background?.captureReady || false
 property bool prewarm:false
 property bool held:false
 onVisibleChanged:{if(held!==visible){held=visible;ShelfState.interaction(held);ShelfState.menuCount=Math.max(0,ShelfState.menuCount+(held ? 1:-1))}}
 Component.onDestruction:if(held){ShelfState.interaction(false);ShelfState.menuCount=Math.max(0,ShelfState.menuCount-1)}
 padding:6
 font.family:ShelfStyle.textFamily;font.pixelSize:13
 background:Item{
  id:material
  readonly property bool captureReady:backdrop.captureSettled
  readonly property var materialState:({wallpaper:backdrop.wallpaperPath,tint:String(backdrop.tint),dim:ShellConfig.options.wallpaper.dim,host:!!host,ready:backdrop.ready,warm:backdrop.warm,settled:backdrop.captureSettled,region:backdrop.captureRegion,quads:backdrop.quads.length,screen:backdrop.screenSize,position:backdrop.windowPosition})
  readonly property var host:root.parent?.QsWindow.window || null
  function syncPosition(){
   if(!host || !root.parent)return
   const screen=host.screen;let origin=Qt.point(0,0)
   if(host.anchors){const a=host.anchors,m=host.margins;origin=Qt.point(a.left ? m.left:a.right ? screen.width-host.width-m.right:(screen.width-host.width)/2,a.top ? m.top:a.bottom ? screen.height-host.height-m.bottom:(screen.height-host.height)/2)}
   else{const window=GlassTracker.clientsSnapshot.find(c=>c.title===host.title);if(window)origin=Qt.point(window.at[0]-(screen?.x || 0),window.at[1]-(screen?.y || 0))}
   const position=origin
   if(position.x!==backdrop.windowPosition.x || position.y!==backdrop.windowPosition.y)backdrop.windowPosition=position
  }
  FrameAnimation{running:root.visible;onTriggered:material.syncPosition()}

  LiquidGlassBackdrop{
   id:backdrop;element:'menus';ready:!!material.host && (root.visible || (root.prewarm && root.parent?.visible));instantReveal:true
   wallpaperPath:GlassWallpaper.path
   screenSize:material.host?.screen ? Qt.size(material.host.screen.width,material.host.screen.height):Qt.size(1920,1080)
   monitorName:material.host?.screen?.name || ''
   windowPosition:Qt.point(0,0)
   captureWindows:ShellConfig.options.glass.captureWindows;captureInterval:ShellConfig.options.glass.captureIntervalMs
   blurRadius:32
  }
  Rectangle{anchors.fill:parent;radius:12;color:'#d92b2b32';visible:!backdrop.captureSettled}
  TahoeGlass{anchors.fill:parent;backdrop:backdrop.ready ? backdrop:null;cornerRadius:12;autoDarken:false;refractionWidth:4;materialOpacity:1;centerOpacity:1}
  Rectangle{anchors.fill:parent;radius:12;color:'#9c24242d';border.width:1;border.color:'#45ffffff'}
 }
 delegate:ShelfMenuItem{}
}
