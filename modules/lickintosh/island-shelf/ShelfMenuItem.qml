import QtQuick
import QtQuick.Controls.Basic
MenuItem {
 id:entry
 property string symbol:""
 readonly property string effectiveSymbol:symbol || (subMenu ? "notch/music.svg":"")
 implicitWidth:248
 implicitHeight:32
 font.family:ShelfStyle.textFamily
 font.pixelSize:13
 contentItem:Text {
  text:entry.text
  font:entry.font
  color:entry.enabled ? '#f5f5f7':'#737378'
  verticalAlignment:Text.AlignVCenter
  leftPadding:entry.effectiveSymbol ? 32:8
  rightPadding:12
 }
 ShelfIcon{visible:!!entry.effectiveSymbol;x:8;anchors.verticalCenter:parent.verticalCenter;size:17;icon:entry.effectiveSymbol;color:entry.enabled ? "#eeeeF4":"#737378"}
 arrow:Item{visible:!!entry.subMenu;x:entry.width-width-8;y:(entry.height-height)/2;implicitWidth:12;implicitHeight:12;Text{anchors.centerIn:parent;text:"›";color:"white";font.family:ShelfStyle.textFamily;font.pixelSize:20}}
 background:Rectangle {radius:7;color:entry.highlighted ? '#0a84ff':'transparent'}
}
