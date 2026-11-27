import QtQuick
import QtQuick.Controls.Basic
import qs.services
Menu {
 id:root
 implicitWidth:240
 width:240
 popupType:Popup.Window
 closePolicy:Popup.CloseOnEscape | Popup.CloseOnPressOutside
 property bool held:false
 onVisibleChanged:{if(held!==visible){held=visible;ShelfState.interaction(held)}}
 Component.onDestruction:if(held)ShelfState.interaction(false)
 padding:6
 font.family:ShelfStyle.textFamily;font.pixelSize:13
 background:Rectangle{radius:14;color:'#f0222226';border.width:1;border.color:'#38ffffff'}
 delegate:MenuItem{
  id:entry
  implicitWidth:220;implicitHeight:30
  contentItem:Text{text:entry.text;font:root.font;color:entry.enabled ? '#f5f5f7':'#737378';verticalAlignment:Text.AlignVCenter;leftPadding:8}
  background:Rectangle{radius:7;color:entry.highlighted ? '#0a84ff':'transparent'}
 }
}
