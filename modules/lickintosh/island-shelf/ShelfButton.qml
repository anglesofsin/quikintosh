import QtQuick
import Quickshell
import qs.components
Rectangle {
 id:root
 property string text:''
 property string icon:''
 property string accessibleLabel:text
 property int badge:0
 property bool selected:false
 signal clicked()
 implicitWidth:Math.max(badge>0 ? 48:32,label.implicitWidth+(icon && text ? 48:24));implicitHeight:32;radius:16
 color:selected ? '#353538':mouse.pressed ? '#454548':mouse.containsMouse ? '#29292c':'#19191b'
 opacity:enabled ? 1:.35
 CFVI {visible:!!root.icon;anchors.left:parent.left;anchors.leftMargin:root.text ? 10:(root.width-size)/2;anchors.verticalCenter:parent.verticalCenter;size:16;icon:root.icon;color:'white'}
 Text{visible:root.badge>0;anchors.right:parent.right;anchors.rightMargin:5;anchors.verticalCenter:parent.verticalCenter;text:root.badge;font.family:'SF Pro Text';font.pixelSize:10;font.weight:Font.DemiBold;color:'#c9c9ce'}
 Text {id:label;anchors.centerIn:parent;anchors.horizontalCenterOffset:root.icon ? 10:0;text:root.text;font.family:'SF Pro Text';font.pixelSize:12;font.weight:Font.Medium;color:'white';textFormat:Text.PlainText}
 MouseArea{id:mouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:root.clicked()}
 Accessible.role:Accessible.Button;Accessible.name:accessibleLabel;Accessible.onPressAction:clicked()
}
