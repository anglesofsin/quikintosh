import QtQuick
import qs.services
Item {
 id:root
 property string text:''
 property string position:'bottom'
 readonly property color fill:Theme.isLight ? '#e8dce4e9':'#ed343439'
 readonly property color edge:Theme.isLight ? '#40000000':'#55ffffff'
 width:Math.min(280,label.implicitWidth+24);height:30
 opacity:visible ? 1:0
 Rectangle{width:11;height:11;radius:2;color:root.fill;border.width:1;border.color:root.edge;rotation:45
  x:root.position==='left' ? -4:root.position==='right' ? root.width-7:(root.width-width)/2
  y:root.position==='bottom' ? root.height-7:(root.height-height)/2
 }
 Rectangle{anchors.fill:parent;radius:8;color:root.fill;border.width:1;border.color:root.edge}
 Text{id:label;anchors.centerIn:parent;width:Math.min(256,implicitWidth);textFormat:Text.PlainText;text:root.text;color:Theme.isLight ? '#17181b':'#f7f7fa';font.family:'SF Pro Text';font.pixelSize:13;elide:Text.ElideRight;horizontalAlignment:Text.AlignHCenter}
}
