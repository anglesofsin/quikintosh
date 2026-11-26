import QtQuick
import QtQuick.Controls
ComboBox {
 id:control;implicitHeight:32;leftPadding:10;rightPadding:26;font.family:'SF Pro Text';font.pixelSize:12
 contentItem:Text{text:control.displayText;color:'#eeeeF2';font:control.font;verticalAlignment:Text.AlignVCenter;elide:Text.ElideRight}
 indicator:Text{anchors.right:parent.right;anchors.rightMargin:10;anchors.verticalCenter:parent.verticalCenter;text:'⌄';color:'#aaaab3';font.pixelSize:15}
 background:Rectangle{radius:10;color:control.down ? '#38383e':'#25252a';border.color:control.activeFocus ? '#777780':'#393940'}
 popup:Popup{y:control.height+5;width:control.width;padding:5;implicitHeight:Math.min(260,list.contentHeight+10)
  background:Rectangle{radius:12;color:'#27272c';border.color:'#55555d'}
  contentItem:ListView{id:list;clip:true;model:control.popup.visible ? control.delegateModel:null;currentIndex:control.highlightedIndex;ScrollBar.vertical:ScrollBar{}}
 }
 delegate:ItemDelegate{required property int index;required property var modelData;width:control.width-10;height:30
  contentItem:Text{text:parent.modelData;color:'white';font:control.font;verticalAlignment:Text.AlignVCenter}
  background:Rectangle{radius:7;color:parent.highlighted ? '#4b4b52':'transparent'}
  highlighted:control.highlightedIndex===index
 }
}
