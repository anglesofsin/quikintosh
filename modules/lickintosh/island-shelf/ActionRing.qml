import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.rosa.services
import qs.components.glass
PanelWindow{
 id:win
 visible:ShelfState.ringOpen && !IslandBus.locked
 screen:Quickshell.screens.find(s=>ShelfState.ringPosition.x>=s.x && ShelfState.ringPosition.x<s.x+s.width && ShelfState.ringPosition.y>=s.y && ShelfState.ringPosition.y<s.y+s.height) || Quickshell.screens[0]
 readonly property int count:ShelfState.utilityPreferences.ringCount || 1
 implicitWidth:count===1 ? 220:count===2 ? 320:412
 implicitHeight:implicitWidth
 color:'transparent';exclusionMode:ExclusionMode.Ignore
 anchors{left:true;top:true}
 margins.left:Math.round(Math.max(4,Math.min(screen.width-width-4,ShelfState.ringPosition.x-screen.x-width/2)))
 margins.top:Math.round(Math.max(4,Math.min(screen.height-height-4,ShelfState.ringPosition.y-screen.y-height/2)))
 WlrLayershell.namespace:'quickintosh-action-ring';WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.keyboardFocus:WlrKeyboardFocus.Exclusive
 mask:Region{item:disc;radius:disc.width/2}
 Item{id:disc;anchors.fill:parent;focus:true;opacity:backdrop.captureSettled || !RenderingState.glassEnabled ? 1:0;Behavior on opacity{NumberAnimation{duration:90}} Keys.onEscapePressed:{ShelfState.ringRequested=false;ShelfState.ringOpen=false}
  LiquidGlassBackdrop{id:backdrop;element:'menus';ready:win.visible;instantReveal:true;wallpaperPath:GlassWallpaper.path;screenSize:Qt.size(win.screen.width,win.screen.height);monitorName:win.screen.name;windowPosition:Qt.point(win.margins.left,win.margins.top);captureWindows:ShellConfig.options.glass.captureWindows;captureInterval:ShellConfig.options.glass.captureIntervalMs;blurRadius:32}
  TahoeGlass{anchors.fill:parent;backdrop:backdrop.ready ? backdrop:null;cornerRadius:width/2;autoDarken:false;materialOpacity:1;centerOpacity:1}
  Rectangle{anchors.fill:parent;radius:width/2;color:'#bb16161b';border.width:1;border.color:'#35ffffff'}
  Repeater{model:win.count*6
   delegate:Rectangle{
    id:tile;required property int index
    readonly property var action:ShelfState.ringCatalogue.find(a=>a.key===ShelfState.ringKeys[index]) || ShelfState.ringCatalogue[index]
    readonly property real angle:-Math.PI/2+(index%6)*Math.PI/3
    readonly property real orbit:win.count===1 ? 72:52+Math.floor(index/6)*54
    width:42;height:42;radius:14
    x:disc.width/2+Math.cos(angle)*orbit-width/2;y:disc.height/2+Math.sin(angle)*orbit-height/2
    color:area.containsMouse ? '#0a84ff':'#20ffffff';border.width:1;border.color:area.containsMouse ? '#6fb6ff':'#18ffffff'
    scale:area.containsMouse ? 1.1:1
    Behavior on scale{NumberAnimation{duration:90;easing.type:Easing.OutCubic}}
    ShelfIcon{anchors.centerIn:parent;size:21;icon:'notch/'+tile.action.icon+'.svg';color:'white'}
    MouseArea{id:area;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onEntered:if(ShelfState.ringArmed)ShelfState.ringSelected=tile.index;onPositionChanged:mouse=>{const dx=win.screen.x+win.margins.left+tile.x+mouse.x-ShelfState.ringPosition.x;const dy=win.screen.y+win.margins.top+tile.y+mouse.y-ShelfState.ringPosition.y;if(dx*dx+dy*dy>36)ShelfState.ringArmed=true;if(ShelfState.ringArmed)ShelfState.ringSelected=tile.index};onExited:if(ShelfState.ringSelected===tile.index)ShelfState.ringSelected=-1;onClicked:ShelfState.activateRing(tile.index)}
    Accessible.role:Accessible.Button;Accessible.name:tile.action.title;Accessible.onPressAction:ShelfState.activateRing(tile.index)
   }
  }
  Text{anchors.centerIn:parent;width:win.count===1 ? 78:60;text:ShelfState.ringSelected>=0 ? (ShelfState.ringCatalogue.find(a=>a.key===ShelfState.ringKeys[ShelfState.ringSelected])?.title || ''):qsTr('Choose an action');wrapMode:Text.Wrap;horizontalAlignment:Text.AlignHCenter;color:'#dddde3';font.family:ShelfStyle.textFamily;font.pixelSize:10;MouseArea{anchors.fill:parent;onClicked:{ShelfState.ringRequested=false;ShelfState.ringOpen=false}}}
 }
 Timer{interval:60000;running:win.visible;onTriggered:{ShelfState.ringRequested=false;ShelfState.ringOpen=false}}
}
