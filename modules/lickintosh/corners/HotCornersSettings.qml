import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.components
import qs.ui.settings.widgets
Item{
 id:root;Layout.fillWidth:true;implicitHeight:36
 readonly property var cfg:ShellConfig.options.edges
 readonly property var ids:['none','launchpad','spotlight','controlCenter','notifications','widgets','clipboard','quickNote','focus','lock','sleep']
 readonly property var labels:['—','Applications','Spotlight','Control Center','Notification Center','Edit Widgets','Clipboard','Quick Note','Focus','Lock Screen','Put Display to Sleep']
 function open(){editor.open()}
 TahoeButton{text:'Hot Corners…';onClicked:root.open()}
 Dialog{
  id:editor;parent:Overlay.overlay;anchors.centerIn:parent;width:Math.min(760,parent.width-40);modal:true;focus:true;header:null;padding:24
  background:Rectangle{radius:18;color:Theme.isLight ? '#f6f6f8':'#252529';border.width:1;border.color:Theme.cardRim}
  contentItem:ColumnLayout{
   spacing:18
   Text{text:'Hot Corners';color:Theme.textPrimary;font.family:'SF Pro Display';font.pixelSize:22;font.weight:Font.DemiBold}
   ConfigSwitch{text:'Enable Hot Corners';checked:root.cfg.hotCorners;onToggled:value=>root.cfg.hotCorners=value}
   Item{
    Layout.fillWidth:true;Layout.preferredHeight:280
    Rectangle{
     width:210;height:130;anchors.centerIn:parent;radius:10;color:Theme.fillControl;border.width:2;border.color:Theme.textSecondary
     Rectangle{anchors.fill:parent;anchors.margins:6;radius:6;gradient:Gradient{GradientStop{position:0;color:Theme.accent}GradientStop{position:1;color:Theme.fillControl}}}
     Rectangle{width:46;height:6;radius:3;color:Theme.textSecondary;anchors{top:parent.bottom;topMargin:8;horizontalCenter:parent.horizontalCenter}}
    }
    Repeater{
     model:['topLeft','topRight','bottomLeft','bottomRight']
     ColumnLayout{
      id:corner;required property string modelData;required property int index
      width:235;x:index%2 ? parent.width-width:0;y:index<2 ? 0:188;spacing:6
      Text{text:['Top Left','Top Right','Bottom Left','Bottom Right'][corner.index];color:Theme.textSecondary;font.pixelSize:12}
      TahoeCombo{Layout.fillWidth:true;model:root.labels;currentIndex:Math.max(0,root.ids.indexOf(root.cfg[corner.modelData+'Action']));onActivated:index=>root.cfg[corner.modelData+'Action']=root.ids[index]}
      RowLayout{
       spacing:3
       Repeater{model:[{label:'⌘',bit:Qt.MetaModifier},{label:'⌥',bit:Qt.AltModifier},{label:'⌃',bit:Qt.ControlModifier},{label:'⇧',bit:Qt.ShiftModifier}]
        TahoeButton{required property var modelData;text:modelData.label;checkable:true;checked:!!(root.cfg[corner.modelData+'Modifiers'] & modelData.bit);onClicked:root.cfg[corner.modelData+'Modifiers']=root.cfg[corner.modelData+'Modifiers'] ^ modelData.bit;Layout.preferredWidth:45}
       }
      }
     }
    }
   }
   ConfigSwitch{text:'Disable Hot Corners in full screen';checked:root.cfg.hideHotCornersFullscreen;onToggled:value=>root.cfg.hideHotCornersFullscreen=value}
   ConfigSlider{text:'Activation delay';from:0;to:1500;decimals:0;value:root.cfg.hotCornerDelay;onMoved:value=>root.cfg.hotCornerDelay=Math.round(value)}
   RowLayout{Layout.alignment:Qt.AlignRight;TahoeButton{text:'Done';onClicked:editor.close()}}
  }
 }
}
