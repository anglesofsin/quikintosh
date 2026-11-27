import QtQuick
import Quickshell
import qs.components
Rectangle {
 id:root
 property string text:''
 property string icon:''
 property real iconSize:16
 readonly property real fittedIconSize:Math.max(0,Math.min(iconSize,height-12,width-(badge>0 ? badgeLabel.implicitWidth+12:12)))
 property string accessibleLabel:text
 property int badge:0
 property color selectedColor:ShelfStyle.selected
 property color foreground:ShelfStyle.primary
 property bool selected:false
 property bool flat:false
 signal clicked()
 implicitWidth:Math.max(badge>0 ? 48:32,label.implicitWidth+(icon && text ? 48:24));implicitHeight:32;radius:16
 color:selected ? selectedColor:mouse.pressed ? '#40ffffff':mouse.containsMouse ? ShelfStyle.surfaceHover:flat ? 'transparent':ShelfStyle.surface
 opacity:enabled ? 1:.35
 activeFocusOnTab:true
 Keys.onSpacePressed:clicked()
 Keys.onReturnPressed:clicked()
 border.width:activeFocus ? 1:0
 border.color:'#8fffffff'
 ShelfIcon {visible:!!root.icon;anchors.left:parent.left;anchors.leftMargin:root.text ? 10:(root.width-(root.badge>0 ? badgeLabel.implicitWidth+4:0)-size)/2;anchors.verticalCenter:parent.verticalCenter;size:root.fittedIconSize;icon:root.icon;color:root.foreground}
 Text{id:badgeLabel;visible:root.badge>0;anchors.left:parent.left;anchors.leftMargin:(root.width+root.iconSize-implicitWidth)/2+2;anchors.verticalCenter:parent.verticalCenter;text:root.badge;font.family:'SF Pro Text';font.pixelSize:10;font.weight:Font.DemiBold;color:'#c9c9ce'}
 Text {id:label;anchors.centerIn:parent;anchors.horizontalCenterOffset:root.icon ? 10:0;text:root.text;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;font.weight:Font.Medium;color:root.foreground;textFormat:Text.PlainText}
 MouseArea{id:mouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:root.clicked()}
 Accessible.role:Accessible.Button;Accessible.name:accessibleLabel;Accessible.onPressAction:clicked()
}
