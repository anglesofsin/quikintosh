import QtQuick
import QtQuick.Effects
Item {
 id:root
 property url source:''
 Image {
  anchors.fill:parent;source:root.source;fillMode:Image.PreserveAspectCrop
  sourceSize:Qt.size(Math.ceil(root.width*2),Math.ceil(root.height*2));asynchronous:true;cache:true
  layer.enabled:true
  layer.effect:MultiEffect{maskEnabled:true;maskSource:avatarMask}
 }
 Rectangle{id:avatarMask;anchors.fill:parent;radius:Math.min(width,height)/2;color:'white';visible:false;layer.enabled:true}
}
