import QtQuick
Rectangle {
 id:root
 property string glyph:""
 property string label:""
 property string iconFont:""
 property bool selected:false
 property bool primary:false
 property bool available:true
 signal clicked()
 width:40;height:40;radius:10
 color:primary ? (mouse.containsMouse ? '#ff8252' : '#ff6b35') : selected ? '#66b8542e' : mouse.containsMouse ? '#30ffffff' : 'transparent'
 opacity:available ? 1 : .35
 Text {anchors.centerIn:parent;text:root.glyph;font.family:root.iconFont;font.pixelSize:22;color:root.selected ? '#ff9a70' : '#e8e8ed';textFormat:Text.PlainText}
 MouseArea {id:mouse;anchors.fill:parent;hoverEnabled:true;enabled:root.available;cursorShape:Qt.PointingHandCursor;onClicked:root.clicked()}
 Accessible.name:label
}
