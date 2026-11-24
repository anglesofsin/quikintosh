import QtQuick
import QtQuick.Controls
import qs.services
TextField{
 id:control
 implicitHeight:32;padding:8;leftPadding:11;rightPadding:11;font.family:'SF Pro Text';font.pixelSize:12
 color:Theme.textPrimary;placeholderTextColor:Theme.textSecondary;selectionColor:Theme.accent;selectedTextColor:'white'
 background:Rectangle{radius:9;color:Theme.isLight ? '#80ffffff':'#30202028';border.width:control.activeFocus ? 2:1;border.color:control.activeFocus ? Qt.rgba(Theme.accent.r,Theme.accent.g,Theme.accent.b,.75):Theme.isLight ? '#20000000':'#26ffffff'}
}
