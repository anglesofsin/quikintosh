import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.components.glass
PanelWindow {
 id:window
 property bool opened:false
 property int count:0
 property string iconSource:'file://'+Quickshell.shellDir+'/assets/icons_desktop/MacTahoe-light/places/scalable/user-trash-full.svg'
 property string heading:'Empty Trash?'
 property string message:count+' item'+(count===1 ? '':'s')+' will be permanently deleted.\nYou can’t undo this action.'
 property string confirmText:'Empty Trash'
 signal cancelled()
 signal confirmed()
 onOpenedChanged:if(opened)Qt.callLater(()=>keys.forceActiveFocus())
 visible:opened
 anchors{left:true;right:true;top:true;bottom:true}
 color:'transparent';exclusiveZone:-1
 WlrLayershell.namespace:'lickintosh:dock-confirm';WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.keyboardFocus:WlrKeyboardFocus.Exclusive
 GlassBackdrop{element:'menus'}
 readonly property color foreground:Theme.isLight ? '#202127':'#f7f7fa'
 MouseArea{anchors.fill:parent;onClicked:window.cancelled()}
 FocusScope{id:keys;anchors.fill:parent;focus:true;Keys.onEscapePressed:window.cancelled()
  BoxGlass{id:card;anchors.centerIn:parent;width:390;height:258;radius:24;color:'#a025252c'
   MouseArea{anchors.fill:parent}
   ColumnLayout{anchors.fill:parent;anchors.margins:22;spacing:12
    Image{Layout.alignment:Qt.AlignHCenter;Layout.preferredWidth:58;Layout.preferredHeight:58;source:window.iconSource;sourceSize:Qt.size(116,116)}
    Text{Layout.fillWidth:true;text:window.heading;color:window.foreground;font.family:'SF Pro Display';font.pixelSize:19;font.weight:Font.DemiBold;horizontalAlignment:Text.AlignHCenter}
    Text{Layout.fillWidth:true;Layout.fillHeight:true;text:window.message;color:Theme.isLight ? '#555761':'#c4c6cf';font.family:'SF Pro Text';font.pixelSize:13;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.WordWrap}
    RowLayout{Layout.fillWidth:true;spacing:10
     Choice{label:'Cancel';onTriggered:window.cancelled()}
     Choice{label:window.confirmText;destructive:true;onTriggered:window.confirmed()}
    }
   }
  }
 }
 component Choice:Rectangle{
  property string label:''
  property bool destructive:false
  signal triggered()
  Layout.fillWidth:true;implicitHeight:34;radius:10
  color:destructive ? (mouse.containsMouse ? '#f05252':'#d83d45'):(mouse.containsMouse ? '#50ffffff':'#28ffffff')
  border.width:1;border.color:'#24ffffff'
  Text{anchors.centerIn:parent;text:parent.label;color:parent.destructive ? 'white':window.foreground;font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.Medium}
  MouseArea{id:mouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:parent.triggered()}
 }
}
