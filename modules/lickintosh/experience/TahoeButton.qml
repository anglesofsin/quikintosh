import QtQuick
import QtQuick.Controls
import qs.services
Button{
 id:control
 implicitHeight:30;implicitWidth:Math.max(64,label.implicitWidth+24)
 padding:7;leftPadding:12;rightPadding:12;font.family:'SF Pro Text';font.pixelSize:12
 opacity:enabled ? 1:.4
 background:Rectangle{radius:9;color:control.highlighted ? (control.down ? Qt.darker(Theme.accent,1.15):Theme.accent):control.checked ? '#456b98ca':control.down ? '#40a0a6b0':control.hovered ? '#30a0a6b0':Theme.isLight ? '#c8ffffff':'#303f424c';border.width:1;border.color:Theme.isLight ? '#20000000':'#28ffffff'}
 contentItem:Text{id:label;text:control.text;font:control.font;color:control.highlighted || control.checked ? 'white':Theme.textPrimary;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter;elide:Text.ElideRight}
}
