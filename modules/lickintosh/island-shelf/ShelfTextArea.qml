import QtQuick
import QtQuick.Controls.Basic

TextArea {
 id:root
 color:ShelfStyle.primary
 placeholderTextColor:'#a1a1aa'
 selectionColor:'#526b9cda'
 selectedTextColor:'#ffffff'
 font.family:ShelfStyle.textFamily
 font.pixelSize:14
 padding:14
 topPadding:12
 bottomPadding:12
 selectByMouse:true
 wrapMode:TextEdit.Wrap
 hoverEnabled:true
 background:Rectangle {
  radius:12
  gradient:Gradient {
   GradientStop{position:0;color:root.readOnly ? '#0affffff':'#12ffffff'}
   GradientStop{position:1;color:root.readOnly ? '#06ffffff':'#09ffffff'}
  }
  border.width:1
  border.color:root.activeFocus && !root.readOnly ? '#809cbce7':root.hovered ? '#36ffffff':'#20ffffff'
  Behavior on border.color{ColorAnimation{duration:100}}
 }
}
