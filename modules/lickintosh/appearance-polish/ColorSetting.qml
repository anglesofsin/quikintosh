import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.components
RowLayout {
 id:root
 property string label:'Color'
 property color value:'#0088ff'
 signal picked(color value)
 Layout.fillWidth:true;implicitHeight:48;spacing:12
 Text{Layout.fillWidth:true;text:root.label;color:Theme.textPrimary;font.pixelSize:13}
 TahoeButton{
  text:String(root.value).toUpperCase();implicitWidth:145
  onClicked:{chooser.chosen=root.value;chooser.open()}
  Rectangle{width:16;height:16;radius:8;color:root.value;anchors.left:parent.left;anchors.leftMargin:10;anchors.verticalCenter:parent.verticalCenter;border.width:1;border.color:'#40ffffff'}
 }
 Dialog {
  id:chooser;property color chosen:root.value
  parent:Overlay.overlay;anchors.centerIn:parent;modal:true;focus:true;width:360;padding:22;header:null
  background:Rectangle{radius:18;color:Theme.isLight ? '#f5f5f7':'#29292e';border.width:1;border.color:Theme.cardRim}
  contentItem:ColumnLayout{spacing:16
   Text{text:root.label;color:Theme.textPrimary;font.pixelSize:18;font.bold:true}
   Rectangle{Layout.fillWidth:true;Layout.preferredHeight:56;radius:12;color:chooser.chosen;border.width:1;border.color:'#30ffffff'}
   GridLayout{columns:8;rowSpacing:10;columnSpacing:10
    Repeater{model:['#ff453a','#ff9f0a','#ffd60a','#30d158','#64d2ff','#0a84ff','#5e5ce6','#bf5af2','#ff375f','#a2845e','#ffffff','#b8b8bf','#676770','#303038','#121216','#000000']
     delegate:Rectangle{required property string modelData;Layout.preferredWidth:30;Layout.preferredHeight:30;radius:15;color:modelData;border.width:chooser.chosen.toString()===modelData ? 3:1;border.color:Theme.textSecondary;MouseArea{anchors.fill:parent;onClicked:chooser.chosen=parent.modelData}}
    }
   }
   Repeater{model:[{name:'Hue',max:1},{name:'Saturation',max:1},{name:'Brightness',max:1}]
    delegate:RowLayout{required property var modelData;required property int index;Layout.fillWidth:true;spacing:12
     Text{Layout.preferredWidth:76;text:modelData.name;color:Theme.textSecondary;font.pixelSize:12}
     TahoeSlider{Layout.fillWidth:true;from:0;to:1;value:parent.index===0 ? Math.max(0,chooser.chosen.hsvHue):parent.index===1 ? chooser.chosen.hsvSaturation:chooser.chosen.hsvValue
      onMoved:chooser.chosen=Qt.hsva(parent.index===0 ? value:Math.max(0,chooser.chosen.hsvHue),parent.index===1 ? value:chooser.chosen.hsvSaturation,parent.index===2 ? value:chooser.chosen.hsvValue,1)
     }
    }
   }
   TahoeField{Layout.fillWidth:true;text:String(chooser.chosen);selectByMouse:true;validator:RegularExpressionValidator{regularExpression:/#[0-9a-fA-F]{6}/} onEditingFinished:if(acceptableInput)chooser.chosen=text}
   RowLayout{Layout.alignment:Qt.AlignRight;TahoeButton{text:'Cancel';onClicked:chooser.close()}TahoeButton{text:'Done';highlighted:true;onClicked:{root.picked(chooser.chosen);chooser.close()}}}
  }
 }
}
