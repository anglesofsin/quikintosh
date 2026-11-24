import QtQuick
import Quickshell
import qs.services
import qs.components
Item{
 id:root
 property var look:null
 property string size:'m'
 property var widgetData:null
 readonly property bool fullBleed:true
 readonly property string path:String(widgetData?.image || '').trim()
 readonly property url imageUrl:{
  const value=root.path.startsWith('~/') ? Quickshell.env('HOME')+root.path.slice(1):root.path
  return value.startsWith('file:') ? value:value ? 'file://'+value.split('/').map(encodeURIComponent).join('/'):''
 }
 readonly property bool animated:/\.gif(?:[?#].*)?$/i.test(path)
 readonly property int imageStatus:animated ? animation.status:still.status
 CFClippingRect{anchors.fill:parent;radius:22;color:'transparent'
  Image{id:still;anchors.fill:parent;source:!root.animated ? root.imageUrl:'';fillMode:Image.PreserveAspectCrop;asynchronous:true;smooth:true;mipmap:true;sourceSize:Qt.size(Math.ceil(root.width*2),Math.ceil(root.height*2));visible:status===Image.Ready}
  AnimatedImage{id:animation;anchors.fill:parent;source:root.animated ? root.imageUrl:'';fillMode:Image.PreserveAspectCrop;asynchronous:true;smooth:true;cache:false;playing:root.visible && root.animated;visible:status===Image.Ready}
 }
 Column{anchors.centerIn:parent;width:parent.width-28;spacing:8;visible:root.imageStatus!==Image.Ready
  Text{width:parent.width;text:!root.path ? 'Choose an image or GIF':root.imageStatus===Image.Loading ? 'Loading…':'Unable to load image';color:root.look?.secondary || Theme.textSecondary;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.WordWrap;font.family:'SF Pro Text';font.pixelSize:14}
  Text{width:parent.width;visible:!root.path;text:'Right-click → Choose Photo…';color:root.look?.secondary || Theme.textSecondary;horizontalAlignment:Text.AlignHCenter;wrapMode:Text.WordWrap;font.pixelSize:11}
 }
}
