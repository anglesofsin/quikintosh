import QtQuick
import QtQuick.Controls.Basic
MenuItem {
 id:entry
 implicitWidth:220
 implicitHeight:30
 font.family:ShelfStyle.textFamily
 font.pixelSize:13
 contentItem:Text {
  text:entry.text
  font:entry.font
  color:entry.enabled ? '#f5f5f7':'#737378'
  verticalAlignment:Text.AlignVCenter
  leftPadding:8
 }
 background:Rectangle {radius:7;color:entry.highlighted ? '#0a84ff':'transparent'}
}
