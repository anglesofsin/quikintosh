import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.components
import qs.services
Item{
 id:root
 property string label:''
 property string description:''
 property string value:''
 property string kind:'info'
 property bool checked:false
 property bool separator:true
 property bool available:true
 property var choices:[]
 property int selection:0
 property real number:0
 property real minimum:0
 property real maximum:1
 property real step:0.01
 property string buttonText:'Open…'
 signal activated()
 signal toggled(bool value)
 signal picked(int index)
 signal edited(string value)
 signal committed(real value)
 Layout.fillWidth:true
 implicitHeight:Math.max(description ? 64:48,labels.implicitHeight+22)
 opacity:available ? 1:0.5
 Rectangle{anchors{left:parent.left;right:parent.right;bottom:parent.bottom}height:root.separator ? 1:0;color:Theme.isLight ? '#10000000':'#18ffffff'}
 RowLayout{
  anchors.fill:parent;spacing:14
  ColumnLayout{
   id:labels;Layout.fillWidth:true;spacing:4
   Text{Layout.fillWidth:true;text:root.label;color:Theme.textPrimary;font.family:'SF Pro Text';font.pixelSize:13;wrapMode:Text.WordWrap}
   Text{Layout.fillWidth:true;text:root.description;visible:!!text;color:Theme.textSecondary;font.family:'SF Pro Text';font.pixelSize:11;wrapMode:Text.WordWrap}
  }
  Loader{
   Layout.preferredWidth:root.kind==='switch' ? 38:root.kind==='slider' ? 190:root.kind==='choice' || root.kind==='field' ? 190:item ? Math.min(300,item.implicitWidth):0
   Layout.preferredHeight:item ? item.implicitHeight:30
   enabled:root.available
   sourceComponent:root.kind==='switch' ? toggle:root.kind==='choice' ? choice:root.kind==='slider' ? slider:root.kind==='field' ? field:root.kind==='button' ? button:info
  }
 }
 MouseArea{anchors.fill:parent;enabled:root.available && root.kind==='navigate';hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:root.activated()}
 Component{id:info;RowLayout{spacing:9;implicitHeight:30
  Text{Layout.maximumWidth:260;text:root.value;color:Theme.textSecondary;font.family:'SF Pro Text';font.pixelSize:12;elide:Text.ElideMiddle;horizontalAlignment:Text.AlignRight}
  Text{text:'›';visible:root.kind==='navigate';font.pixelSize:23;color:Theme.textSecondary}
 }}
 Component{id:button;TahoeButton{text:root.buttonText;onClicked:root.activated()}}
 Component{id:field;TahoeField{text:root.value;selectByMouse:true;onEditingFinished:if(text!==root.value)root.edited(text)}}
 Component{id:choice;TahoeCombo{model:root.choices;currentIndex:root.selection;onActivated:index=>root.picked(index)}}
 Component{id:toggle;Switch{
  id:control;implicitWidth:38;implicitHeight:23;padding:0;checked:root.checked
  onToggled:root.toggled(checked)
  indicator:Rectangle{implicitWidth:38;implicitHeight:23;radius:12;color:control.checked ? Theme.accent:Theme.isLight ? '#b9bbc2':'#62636a';Rectangle{x:control.checked ? 17:2;y:2;width:19;height:19;radius:10;color:'white';Behavior on x{NumberAnimation{duration:ShellMotion.fade(.35)}}}}
 }}
 Component{id:slider;Item{
  implicitHeight:32
  RowLayout{anchors.fill:parent;spacing:10
   Text{visible:!!root.value;Layout.preferredWidth:visible ? 34:0;text:root.value;color:Theme.textSecondary;font.pixelSize:11;horizontalAlignment:Text.AlignRight;elide:Text.ElideRight}
   TahoeSlider{
    id:control;Layout.fillWidth:true;fillColor:Theme.accent;from:root.minimum;to:root.maximum;stepSize:root.step;value:root.number
    onPressedChanged:if(!pressed)root.committed(value)
    Keys.onReleased:event=>{if([Qt.Key_Left,Qt.Key_Right,Qt.Key_Home,Qt.Key_End].includes(event.key))root.committed(value)}
   }
  }
 }}
}
