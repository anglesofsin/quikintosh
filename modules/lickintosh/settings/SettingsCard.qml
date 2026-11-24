import QtQuick
import QtQuick.Layouts
import qs.services
ColumnLayout{
 id:root
 property string title:''
 property string footer:''
 default property alias rows:column.data
 Layout.fillWidth:true;spacing:7
 Text{Layout.fillWidth:true;Layout.leftMargin:4;text:root.title;visible:!!text;font.family:'SF Pro Text';font.pixelSize:12;font.weight:Font.DemiBold;color:Theme.textSecondary}
 Rectangle{
  Layout.fillWidth:true;implicitHeight:column.implicitHeight+12;radius:12
  color:Theme.isLight ? '#f3f3f6':'#252529';border.width:SettingsPreferences.accessibility.increaseContrast ? 2:1;border.color:SettingsPreferences.accessibility.increaseContrast ? Theme.textSecondary:Theme.isLight ? '#15000000':'#20ffffff'
  ColumnLayout{id:column;anchors{left:parent.left;right:parent.right;top:parent.top;topMargin:6;leftMargin:16;rightMargin:16}spacing:0}
 }
}
