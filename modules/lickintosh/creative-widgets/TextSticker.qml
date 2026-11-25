import QtQuick
import qs.services
Item{
 id:root
 property var look:null
 property string size:'m'
 property var widgetData:null
 property bool isSnapshot:false
 property bool desktopWidget:false
 readonly property bool fullBleed:true
 readonly property color ink:widgetData?.textColorMode==='custom' ? widgetData.textColor || '#fff':widgetData?.textColorMode==='accent' ? Theme.accent:look?.primary || Theme.textPrimary
 CreativeText{
  anchors.fill:parent;anchors.margins:8
  value:root.widgetData?.textContent || 'Make this space yours.'
  options:Object.assign({textStyle:root.widgetData?.variant || 'modern'},root.widgetData || {})
  ink:root.ink;isSnapshot:root.isSnapshot
  animationEnabled:root.desktopWidget && !root.isSnapshot && DesktopFiles.desktopFocused
 }
}
