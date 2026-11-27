import QtQuick
import QtQuick.Effects
import Quickshell
import qs.components
Item {
 id:root
 property string icon:''
 property real size:ShelfStyle.icon
 property color color:ShelfStyle.primary
 readonly property string basename:icon.replace(/^.*\//,'').replace(/\.(svg|png)$/,'')
 readonly property var generated:({'mic':'microphone','package':'archive','folder-plus':'folder-plus','shopping-basket':'basket','background':'background','paperclip':'paperclip','send':'send','home':'home','inbox':'tray','grid':'widgets','play':'play','pause':'pause','backward':'backward','forward':'forward','music':'music','calendar':'calendar','calender':'calendar','cloud':'cloud','camera':'camera','clipboard':'clipboard','bell':'bell','laptop':'laptop'})
 readonly property bool needsTint:Math.abs(color.r-color.g)>.001 || Math.abs(color.g-color.b)>.001
 readonly property string asset:generated[basename] || ''
 readonly property var opticalBounds:{"microphone":[1254, 1254, 330, 183, 593, 907],"archive":[512,512,103,143,333,270],"folder-plus":[512,512,92,135,328,277],"basket":[512,512,73,123,345,298],"background":[512,512,113,106,313,309],"paperclip":[512,512,114,109,283,310],"send":[512,512,88,112,320,303],"widgets":[1254,1254,260,284,734,692],"forward":[1254,1254,282,464,690,373],"camera":[1254,1254,199,287,851,726],"music":[1254,1254,240,273,713,771],"laptop":[1451, 1084, 324, 306, 797, 471],"backward":[1262,1246,259,449,761,418],"bell":[1254,1254,252,200,745,839],"home":[1254,1254,267,312,720,668],"cloud":[1254,1254,148,403,955,486],"calendar":[1254,1254,240,221,773,830],"pause":[1536,1024,536,243,464,537],"play":[1254,1254,399,295,559,668],"clipboard":[1254,1254,270,186,710,906],"tray":[1536, 1024, 524, 368, 488, 288]}
 readonly property var bounds:opticalBounds[asset] || [1,1,0,0,1,1]
 readonly property real opticalScale:size/Math.max(bounds[4],bounds[5])
 implicitWidth:size;implicitHeight:size
 Accessible.ignored:true
 Image {
  width:root.bounds[0]*root.opticalScale; height:root.bounds[1]*root.opticalScale
  x:(root.width-root.bounds[4]*root.opticalScale)/2-root.bounds[2]*root.opticalScale
  y:(root.height-root.bounds[5]*root.opticalScale)/2-root.bounds[3]*root.opticalScale
  visible:root.asset!==''
  source:root.asset!=='' ? Qt.resolvedUrl('icons/ai/'+root.asset+'.png'):''
  sourceSize:Qt.size(Math.ceil(width*Screen.devicePixelRatio),Math.ceil(height*Screen.devicePixelRatio))
  fillMode:Image.PreserveAspectFit
  opacity:(root.needsTint ? 1:root.color.r)*root.color.a
  layer.enabled:root.needsTint
  layer.effect:MultiEffect{colorization:1;colorizationColor:root.color}
  mipmap:true;smooth:true;cache:true
 }
 CFVI {
  anchors.centerIn:parent
  visible:root.asset===''
  icon:root.asset==='' ? root.icon:''
  size:root.size;color:root.color
 }
}
