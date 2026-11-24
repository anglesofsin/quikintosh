import QtQuick
import QtQuick.Controls
import Quickshell
import qs.services
import qs.components.glass
Slider {
 id:control
 property color fillColor:Theme.isGlass ? '#f5f5f7':Theme.accent
 property bool autoHideHandle:false
 property Item glassBackdrop:GlassRegistry.lookup(QsWindow.window)
 property bool recentlyChanged:false
 readonly property bool handleShown:!autoHideHandle || pressed || hovered || activeFocus || recentlyChanged
 implicitWidth:190;implicitHeight:32
 leftPadding:0;rightPadding:0;topPadding:4;bottomPadding:4
 hoverEnabled:true;from:0;to:1;stepSize:.01
 onValueChanged:if(autoHideHandle){recentlyChanged=true;settle.restart()}
 Component.onCompleted:{recentlyChanged=false;settle.stop()}
 Timer{id:settle;interval:1100;onTriggered:control.recentlyChanged=false}
 background:Item {
  x:control.leftPadding;y:control.topPadding+(control.availableHeight-height)/2;width:control.availableWidth;height:6
  Rectangle{anchors.fill:parent;radius:3;color:Theme.isLight ? '#26000000':'#3bffffff';border.width:1;border.color:Theme.isLight ? '#13000000':'#12ffffff'}
  Rectangle{width:Math.max(0,Math.min(parent.width,control.visualPosition*parent.width));height:parent.height;radius:3;color:control.fillColor
   Rectangle{anchors{left:parent.left;right:parent.right;top:parent.top;leftMargin:2;rightMargin:2}height:1;radius:1;color:'#42ffffff'}
  }
 }
 handle:Item {
  x:control.leftPadding+control.visualPosition*(control.availableWidth-width)
  y:control.topPadding+(control.availableHeight-height)/2
  width:control.pressed ? 31:26;height:control.pressed ? 21:18
  opacity:control.handleShown ? 1:0
  Rectangle{x:-1;y:2;width:parent.width+2;height:parent.height;radius:height/2;color:Theme.isLight ? '#26000000':'#44000000'}
  BoxGlass{anchors.fill:parent;radius:height/2;backdrop:control.glassBackdrop;color:control.pressed ? '#75ffffff':Theme.isLight ? '#ddffffff':'#c5e5ebef';light:'#e6ffffff';rimStrength:control.pressed ? 1:.8}
  Rectangle{anchors.fill:parent;radius:height/2;color:control.pressed ? '#25ffffff':'#cfffffff'}
  Rectangle{anchors{left:parent.left;right:parent.right;top:parent.top;leftMargin:4;rightMargin:4;topMargin:1}height:1;radius:1;color:'#e0ffffff'}
  Rectangle{anchors.fill:parent;radius:height/2;color:'transparent';border.width:control.activeFocus ? 2:1;border.color:control.activeFocus ? Theme.accent:Theme.isLight ? '#38ffffff':'#50ffffff'}
  Behavior on width{NumberAnimation{duration:ShellMotion.fade(.35);easing.type:Easing.OutCubic}}
  Behavior on height{NumberAnimation{duration:ShellMotion.fade(.35);easing.type:Easing.OutCubic}}
  Behavior on opacity{NumberAnimation{duration:ShellMotion.fade(.35)}}
 }
}
