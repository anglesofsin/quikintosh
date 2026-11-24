import QtQuick
import QtQuick.Controls
import qs.services
ComboBox{
 id:control
 implicitHeight:30;implicitWidth:Math.max(140,display.implicitWidth+44)
 leftPadding:11;rightPadding:30;font.family:'SF Pro Text';font.pixelSize:12
 background:Rectangle{radius:9;color:control.down ? '#40687282':Theme.isLight ? '#c8ffffff':'#304b4e58';border.width:1;border.color:Theme.isLight ? '#20000000':'#28ffffff'}
 contentItem:Text{id:display;text:control.displayText;font:control.font;color:Theme.textPrimary;verticalAlignment:Text.AlignVCenter;elide:Text.ElideRight}
 indicator:Text{x:control.width-width-10;anchors.verticalCenter:parent.verticalCenter;text:'⌄';color:Theme.textSecondary;font.pixelSize:17}
 delegate:ItemDelegate{
  required property int index;width:control.width;text:control.textAt(index);highlighted:control.highlightedIndex===index
  contentItem:Text{text:control.textAt(parent.index);font:control.font;color:Theme.textPrimary;verticalAlignment:Text.AlignVCenter}
  background:Rectangle{radius:6;color:parent.highlighted ? '#506b98ca':'transparent'}
 }
 popup:Popup{
  y:control.height+5;width:Math.max(control.width,160);padding:5;implicitHeight:Math.min(300,contentItem.implicitHeight+10)
  background:Rectangle{radius:11;color:Theme.isLight ? '#f0f0f4':'#282a32';border.width:1;border.color:Theme.isLight ? '#24000000':'#38ffffff'}
  contentItem:ListView{clip:true;implicitHeight:contentHeight;model:control.popup.visible ? control.delegateModel:null;currentIndex:control.highlightedIndex;ScrollIndicator.vertical:ScrollIndicator{}}
 }
}
