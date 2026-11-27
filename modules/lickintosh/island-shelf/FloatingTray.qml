import QtQuick
import QtQuick.Controls.Basic
import Quickshell.Io
import Quickshell
import qs.services
import qs.rosa.services
FloatingWindow {
 id:root;visible:ShelfState.trayOpen && !IslandBus.locked;title:'Quickintosh File Tray';color:'transparent';implicitWidth:760;implicitHeight:400;minimumSize:Qt.size(540,300)
 property int placementAttempts:0
 onVisibleChanged:{if(!visible){ShelfState.trayOpen=false;placementTimer.stop()}else{placementAttempts=0;placementTimer.start()}}
 Timer{id:placementTimer;interval:100;repeat:true;onTriggered:{if(!root.visible || ++root.placementAttempts>20){stop();return}if(!placement.running)placement.running=true}}
 Process{id:placement;command:['hyprctl','eval','for _,w in ipairs(hl.get_windows()) do if w.title=="Quickintosh File Tray" then if not w.floating then hl.dispatch(hl.dsp.window.float({action="enable",window="address:"..w.address})) end;hl.dispatch(hl.dsp.window.resize({x=760,y=400,window="address:"..w.address}));print("qi-tray-placed") end end'];stdout:SplitParser{onRead:data=>{if(data.includes('qi-tray-placed'))placementTimer.stop()}}}

 Rectangle{anchors.fill:parent;radius:24;color:IslandConfig.s('shelfMaterial')==='black' || !RenderingState.glassEnabled ? '#ff000000':'#18000000';border.color:ShelfStyle.outline
  FileTray{anchors.fill:parent;anchors.margins:18;floating:true}
  ShelfButton{anchors.top:parent.top;anchors.right:parent.right;anchors.margins:8;icon:'notch/x.svg';onClicked:ShelfState.trayOpen=false}
  MouseArea{anchors.left:parent.left;anchors.top:parent.top;width:160;height:30;onPressed:root.startSystemMove()}
 }
 Shortcut{sequence:'Escape';onActivated:ShelfState.trayOpen=false}
}
