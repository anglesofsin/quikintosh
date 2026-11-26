import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import qs.services
import qs.rosa.services
FloatingWindow {
 id:root;title:'Quickintosh Floating Player';visible:ShelfState.playerOpen && !IslandBus.locked;color:'transparent'
 readonly property string mode:IslandConfig.s('floatingPlayerSize')
 implicitWidth:mode==='mini' ? 320:mode==='player' ? 450:780
 implicitHeight:mode==='mini' ? 230:mode==='player' ? 280:360
 minimumSize:Qt.size(300,140)
 onModeChanged:resizeSoon.restart()
 onVisibleChanged:{if(!visible)ShelfState.playerOpen=false;else resizeSoon.restart()}
 Timer{id:resizeSoon;interval:180;onTriggered:if(root.visible)Quickshell.execDetached(['hyprctl','eval','for _,w in ipairs(hl.get_windows()) do if w.title=="Quickintosh Floating Player" then hl.dispatch(hl.dsp.window.resize({x='+root.implicitWidth+',y='+root.implicitHeight+',window="address:"..w.address})) end end'])}
 Rectangle{anchors.fill:parent;radius:24;color:IslandConfig.s('shelfMaterial')==='black' || !RenderingState.glassEnabled ? '#ff000000':'#60202024';border.color:'#35ffffff'
  ColumnLayout{anchors.fill:parent;anchors.margins:18;spacing:12
   RowLayout{Layout.fillWidth:true;spacing:8
    Text{Layout.fillWidth:true;text:qsTr('Now Playing');font.family:'SF Pro Text';font.pixelSize:12;font.weight:Font.DemiBold;color:'#9999a0'}
    ShelfChoice{Layout.preferredWidth:110;model:[qsTr('Mini'),qsTr('Player'),qsTr('Lyrics')];currentIndex:['mini','player','expanded'].indexOf(root.mode);onActivated:i=>IslandConfig.setStyle('floatingPlayerSize',['mini','player','expanded'][i])}
    ShelfButton{icon:'notch/x.svg';onClicked:ShelfState.playerOpen=false}
   }
   RowLayout{Layout.fillWidth:true;Layout.fillHeight:true;spacing:20
    ShelfHome{Layout.fillWidth:true;Layout.fillHeight:true;slots:['media'];onOpenPage:page=>IslandConfig.setStyle('floatingPlayerSize','expanded')}
    Loader{Layout.fillWidth:true;Layout.fillHeight:true;active:root.mode==='expanded';visible:active;sourceComponent:Component{LyricsShelf{}}}
   }
  }
  MouseArea{anchors.left:parent.left;anchors.top:parent.top;width:Math.max(40,parent.width-175);height:36;onPressed:root.startSystemMove()}
 }
 Shortcut{sequence:'Escape';onActivated:ShelfState.playerOpen=false}
}
