import QtQuick
import QtQuick.Controls
Slider {
 id:control;implicitHeight:26;leftPadding:5;rightPadding:5
 background:Rectangle{x:control.leftPadding;y:(control.height-height)/2;width:control.availableWidth;height:4;radius:2;color:'#393940'
  Rectangle{height:4;radius:2;width:parent.width*control.visualPosition;color:'#d9d9df'}
 }
 handle:Rectangle{x:control.leftPadding+control.visualPosition*(control.availableWidth-width);y:(control.height-height)/2;width:12;height:12;radius:6;color:'#f0f0f5'}
}
