import QtQuick
import qs.services
Item{
 id:root
 property string kind:''
 property bool active:true
 property real intensity:1
 property real speed:1
 property bool lightning:true
 property color dropColor:'#9cd9ff'
 property int seed:0
 readonly property bool rain:['rain','drizzle','showers','thunder','storm','thunderstorm'].some(k=>kind.toLowerCase().includes(k))
 readonly property bool snow:kind.toLowerCase().includes('snow') || kind.toLowerCase().includes('sleet')
 readonly property bool storm:kind.toLowerCase().includes('thunder') || kind.toLowerCase().includes('storm')
 readonly property bool running:visible && active && RenderingState.ambientAnimations && !SettingsPreferences.locked && (rain || snow)
 clip:true
 property real phase:0
 FrameAnimation{running:root.running;onTriggered:root.phase=(root.phase+Math.min(frameTime,.05)*root.speed)%120}
 Repeater{model:root.active && (root.rain || root.snow) ? Math.min(70,Math.round((root.snow ? 24:36)*root.intensity)):0
  Rectangle{
   required property int index
   readonly property real noise:((index*73+root.seed*31)%101)/101
   width:root.snow ? 2+noise*3:1+noise*.6;height:root.snow ? width:9+noise*15
   radius:width/2;color:root.dropColor;opacity:(.16+noise*.38)*(root.snow ? 1:.8)
   x:((index*.6180339+root.phase*(root.snow ? .014:.065))%1)*root.width
   y:((index*.381966+root.phase*(root.snow ? .07:.65+noise*.45))%1)*(root.height+height)-height
   rotation:root.snow ? 0:18
  }
 }
 Rectangle{anchors.fill:parent;color:'#d9eaff';opacity:root.running && root.lightning && root.storm ? (Math.sin(root.phase*.9)> .994 ? .26:Math.sin(root.phase*.9+.06)>.998 ? .14:0):0}
}
