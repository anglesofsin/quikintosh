import QtQuick
import QtQuick.Effects
import Quickshell
import qs.components
Item {
 id:root
 property bool forceTint:false
 property string icon:''
 property real size:ShelfStyle.icon
 property color color:ShelfStyle.primary
 // The artwork is pre-cropped to its alpha bounds. Keep the source texture
 // inside the logical box so tint shaders never clip translated pixels.
 readonly property string basename:icon.replace(/^.*\//,'').replace(/\.(svg|png)$/,'')
 readonly property var generated:({'battery-status':'battery-status','vpn':'vpn','zap':'bolt','headphones':'headphones','x':'close','refresh-cw':'refresh','rotate-ccw':'refresh','smartphone':'phone','mic':'microphone','package':'archive','folder-plus':'folder-plus','shopping-basket':'basket','background':'background','paperclip':'paperclip','send':'send','home':'home-bold','inbox':'tray-user','grid':'widgets-bold','play':'play','pause':'pause','backward':'backward','forward':'forward','music':'music','calendar':'calendar','calender':'calendar','cloud':'cloud','camera':'camera','clipboard':'clipboard','bell':'bell','laptop':'laptop-user'})
 readonly property bool needsTint:forceTint || Math.abs(color.r-color.g)>.001 || Math.abs(color.g-color.b)>.001
 readonly property string asset:generated[basename] || ''
 readonly property var opticalBounds:{"widgets-bold":[797,798,0,0,797,798],"home-bold":[956,832,0,0,956,832],"tray-bold":[1282,617,0,0,1282,617],"laptop-bold":[1488,743,0,0,1488,743],"battery-status":[1165,523,0,0,1165,523],"vpn":[786,798,0,0,786,798],"bolt":[380,897,0,0,380,897],"headphones":[805,843,0,0,805,843],"close":[339,340,0,0,339,340],"refresh":[675,691,0,0,675,691],"phone":[590,1068,0,0,590,1068],"microphone":[593,907,0,0,593,907],"archive":[333,270,0,0,333,270],"folder-plus":[328,277,0,0,328,277],"basket":[345,298,0,0,345,298],"background":[313,309,0,0,313,309],"paperclip":[283,310,0,0,283,310],"send":[839,828,0,0,839,828],"widgets":[734,692,0,0,734,692],"forward":[690,373,0,0,690,373],"camera":[851,726,0,0,851,726],"music":[713,771,0,0,713,771],"laptop":[797,471,0,0,797,471],"backward":[761,418,0,0,761,418],"bell":[745,839,0,0,745,839],"home":[720,668,0,0,720,668],"cloud":[955,486,0,0,955,486],"calendar":[773,830,0,0,773,830],"pause":[464,537,0,0,464,537],"play":[559,668,0,0,559,668],"clipboard":[710,906,0,0,710,906],"tray":[488,288,0,0,488,288],"laptop-user":[965, 593, 0, 0, 965, 593],"tray-user":[854,614,0,0,854,614]}
 readonly property var bounds:opticalBounds[asset] || [1,1,0,0,1,1]
 readonly property real opticalScale:size/Math.max(bounds[4],bounds[5])
 implicitWidth:size;implicitHeight:size
 Accessible.ignored:true
 Image {
  id:generatedImage
  objectName:"generated-icon-image"
  width:root.bounds[0]*root.opticalScale; height:root.bounds[1]*root.opticalScale
  x:(root.width-root.bounds[4]*root.opticalScale)/2-root.bounds[2]*root.opticalScale
  y:(root.height-root.bounds[5]*root.opticalScale)/2-root.bounds[3]*root.opticalScale
  visible:root.asset!=='' && generatedImage.status!==Image.Error
  source:root.asset!=='' ? Qt.resolvedUrl('icons/ai/'+root.asset+'-bounded.png'):''
  sourceSize:Qt.size(Math.ceil(width*Screen.devicePixelRatio),Math.ceil(height*Screen.devicePixelRatio))
  fillMode:Image.PreserveAspectFit
  opacity:(root.needsTint ? 1:root.color.r)*root.color.a
  layer.enabled:root.needsTint
  layer.effect:MultiEffect{colorization:1;colorizationColor:root.color}
  mipmap:true;smooth:true;cache:true
 }
 CFVI {
  objectName:"generated-icon-fallback"
  anchors.centerIn:parent
  visible:root.asset==='' || generatedImage.status===Image.Error
  icon:(root.asset==='' || generatedImage.status===Image.Error) ? (root.basename==='vpn' ? 'notch/shield.svg':root.basename==='battery-status' ? 'notch/battery.svg':root.icon):''
  size:root.size;color:root.color
 }
}
