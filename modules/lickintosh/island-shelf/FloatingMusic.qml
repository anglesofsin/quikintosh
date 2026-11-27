import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import qs.services
import qs.rosa.services
FloatingWindow {
 id:root;title:'Quickintosh Floating Player';visible:ShelfState.playerOpen && !IslandBus.locked;color:'transparent'
 readonly property string mode:IslandConfig.s('floatingPlayerSize')
 implicitWidth:mode==='mini' ? 340:mode==='player' ? 360:760
 implicitHeight:mode==='mini' ? 254:540
 minimumSize:Qt.size(300,240)
 onModeChanged:resizeSoon.restart()
 onVisibleChanged:{if(!visible)ShelfState.playerOpen=false;else resizeSoon.restart()}
 Timer{id:resizeSoon;interval:60;onTriggered:if(root.visible)Quickshell.execDetached(['hyprctl','eval','for _,w in ipairs(hl.get_windows()) do if w.title=="Quickintosh Floating Player" then if not w.floating then hl.dispatch(hl.dsp.window.float({action="enable",window="address:"..w.address})) end;hl.dispatch(hl.dsp.window.resize({x='+root.implicitWidth+',y='+root.implicitHeight+',window="address:"..w.address})) end end'])}
 Rectangle{anchors.fill:parent;radius:24;color:IslandConfig.s('shelfMaterial')==='black' || !RenderingState.glassEnabled ? '#ff000000':'#18000000';border.color:ShelfStyle.outline
  ColumnLayout{anchors.fill:parent;anchors.margins:18;spacing:12
   RowLayout{Layout.fillWidth:true;spacing:8
    Text{Layout.fillWidth:true;text:qsTr('Now Playing');font.family:ShelfStyle.textFamily;font.pixelSize:12;font.weight:Font.DemiBold;color:ShelfStyle.secondary}
    RowLayout{spacing:2
     Repeater{model:[qsTr('Mini'),qsTr('Player'),qsTr('Lyrics')]
      delegate:ShelfButton{required property int index;required property string modelData;text:modelData;implicitWidth:52;implicitHeight:28;selected:['mini','player','expanded'].indexOf(root.mode)===index;onClicked:IslandConfig.setStyle('floatingPlayerSize',['mini','player','expanded'][index])}
     }
    }
    ShelfButton{icon:'notch/x.svg';onClicked:ShelfState.playerOpen=false}
   }
   RowLayout{Layout.fillWidth:true;Layout.fillHeight:true;spacing:20
    ShelfMedia{Layout.fillWidth:true;Layout.fillHeight:true;Layout.preferredWidth:root.mode==='expanded' ? 320:-1;Layout.maximumWidth:root.mode==='expanded' ? 340:Infinity;portrait:root.mode!=='mini';showPopout:false}
    Loader{Layout.fillWidth:true;Layout.fillHeight:true;Layout.preferredWidth:320;Layout.minimumWidth:root.mode==='expanded' ? 280:0;active:root.mode==='expanded';visible:active;sourceComponent:Component{LyricsShelf{}}}
   }
  }
  MouseArea{anchors.left:parent.left;anchors.top:parent.top;width:Math.max(40,parent.width-220);height:36;onPressed:root.startSystemMove()}
 }
 Shortcut{sequence:'Escape';onActivated:ShelfState.playerOpen=false}
}
