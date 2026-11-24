import QtQuick
import Quickshell
import qs.services
Item{
 id:root
 property var look:null
 property string size:'m'
 property var widgetData:null
 readonly property bool fullBleed:true
 readonly property var style:LockClockStyle.styleAt(widgetData?.clockStyle || 0)
 SystemClock{id:clock;precision:widgetData?.clockSeconds ? SystemClock.Seconds:SystemClock.Minutes}
 Column{
  anchors.centerIn:parent;width:parent.width-24;spacing:6
  Text{width:parent.width;visible:root.widgetData?.clockDate!==false;text:Qt.formatDateTime(clock.date,'dddd, d MMMM');horizontalAlignment:Text.AlignHCenter;color:root.look?.primary || Theme.textPrimary;font.family:root.style.family;font.pixelSize:14;elide:Text.ElideRight}
  Text{width:parent.width;text:Qt.formatDateTime(clock.date,root.widgetData?.clockSeconds ? 'HH:mm:ss':'HH:mm');horizontalAlignment:Text.AlignHCenter;color:root.widgetData?.clockColor || root.look?.primary || Theme.textPrimary;font.family:root.widgetData?.clockFont || root.style.family;font.italic:root.style.italic;font.weight:LockClockStyle.weightFor(root.widgetData?.clockWeight ?? .6);font.letterSpacing:root.style.spacing;font.pixelSize:root.widgetData?.clockSize || (root.size==='s' ? 48:76);minimumPixelSize:20;fontSizeMode:Text.Fit;renderType:Text.NativeRendering}
 }
}
