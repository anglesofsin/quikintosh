import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.rosa.services
import qs.components.glass
PanelWindow{
 id:win
 visible:ShelfState.selectionOpen && !IslandBus.locked
 screen:Quickshell.screens.find(s=>ShelfState.selectionPosition.x>=s.x && ShelfState.selectionPosition.x<s.x+s.width && ShelfState.selectionPosition.y>=s.y && ShelfState.selectionPosition.y<s.y+s.height) || Quickshell.screens[0]
 implicitWidth:180;implicitHeight:44;color:'transparent';exclusionMode:ExclusionMode.Ignore
 anchors{left:true;top:true}
 margins.left:Math.round(Math.max(4,Math.min(screen.width-width-4,ShelfState.selectionPosition.x-screen.x+8)))
 margins.top:Math.round(Math.max(4,Math.min(screen.height-height-4,ShelfState.selectionPosition.y-screen.y+16)))
 WlrLayershell.namespace:'quickintosh-selection-actions';WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
 mask:Region{item:body;radius:22}
 Item{id:body;anchors.fill:parent;opacity:backdrop.captureSettled || !RenderingState.glassEnabled ? 1:0;Behavior on opacity{NumberAnimation{duration:80}}
  LiquidGlassBackdrop{id:backdrop;element:'menus';ready:win.visible;instantReveal:true;wallpaperPath:GlassWallpaper.path;screenSize:Qt.size(win.screen.width,win.screen.height);monitorName:win.screen.name;windowPosition:Qt.point(win.margins.left,win.margins.top);captureWindows:ShellConfig.options.glass.captureWindows;captureInterval:ShellConfig.options.glass.captureIntervalMs;blurRadius:26}
  TahoeGlass{anchors.fill:parent;backdrop:backdrop.ready ? backdrop:null;cornerRadius:22;autoDarken:false;materialOpacity:1;centerOpacity:1}
  Rectangle{anchors.fill:parent;radius:22;color:'#b31b1b20';border.width:1;border.color:'#35ffffff'}
  RowLayout{anchors.fill:parent;anchors.margins:5;spacing:4
   ShelfButton{Layout.fillWidth:true;implicitHeight:34;flat:true;icon:'notch/copy.svg';text:qsTr('Copy');onClicked:{ShelfState.send({action:'copyText',text:ShelfState.selectionText});ShelfState.clearSelection()}}
   ShelfButton{Layout.fillWidth:true;implicitHeight:34;flat:true;icon:'notch/search.svg';text:qsTr('Search');onClicked:{Quickshell.execDetached(['xdg-open','https://duckduckgo.com/?q='+encodeURIComponent(ShelfState.selectionText)]);ShelfState.clearSelection()}}
  }
  HoverHandler{onHoveredChanged:ShelfState.selectionHovered=hovered}
 }
 Timer{interval:8000;running:win.visible && !ShelfState.selectionHovered;onTriggered:ShelfState.clearSelection()}
}
