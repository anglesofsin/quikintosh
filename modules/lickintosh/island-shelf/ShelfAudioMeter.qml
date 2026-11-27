import QtQuick
import Quickshell
import qs.services
import qs.rosa.services
Item{
 id:root
 implicitWidth:34;implicitHeight:28
 property color tint:'#7873ed'
 property bool held:false
 readonly property bool watching:visible && !!QsWindow.window && QsWindow.window.visible && MprisState.isPlaying
 function sync(){if(held===watching)return;held=watching;if(held)Cava.hold();else Cava.release()}
 onWatchingChanged:sync()
 Component.onCompleted:sync()
 Component.onDestruction:if(held)Cava.release()
 Row{anchors.centerIn:parent;spacing:2
  Repeater{model:7
   Rectangle{required property int index;width:3;radius:1.5;height:Math.max(3,root.height*Math.min(1,Math.max(0,Number(Cava.smooth[Math.round(index*(Cava.bars-1)/6)] || 0))));anchors.verticalCenter:parent.verticalCenter
    gradient:Gradient{GradientStop{position:0;color:Qt.lighter(root.tint,1.5)}GradientStop{position:1;color:root.tint}}
    Behavior on height{NumberAnimation{duration:60;easing.type:Easing.OutQuad}}
   }
  }
 }
 Accessible.role:Accessible.Button;Accessible.name:qsTr('Audio sources');Accessible.onPressAction:ShelfState.reveal(10)
 MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:ShelfState.reveal(10)}
}
