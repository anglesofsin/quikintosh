import QtQuick
import QtQuick.Effects
import Quickshell
import qs.services
import qs.components.glass
import "../../lockscreen/mac" as LockMac
Item {
 id:root
 property var look:null
 property string size:'m'
 property var widgetData:null
 property bool isSnapshot:false
 readonly property bool fullBleed:true
 readonly property var style:LockClockStyle.styleAt(widgetData?.clockStyle || 0)
 readonly property bool automatic:widgetData?.clockAutoSize ?? (widgetData?.clockSize===undefined)
 readonly property real basePixelSize:automatic ? Math.max(24,Math.min((width-32)*.34,(height-24)*.56)):widgetData?.clockSize || 76
 readonly property string timeFormat:widgetData?.clockFormat || (widgetData?.clock12Hour ? (widgetData?.clockSeconds ? 'h:mm:ss AP':'h:mm AP'):(widgetData?.clockSeconds ? 'HH:mm:ss':'HH:mm'))
 readonly property string timeText:Qt.formatDateTime(clock.date,timeFormat)
 readonly property string family:widgetData?.clockFont || style.family
 readonly property color ink:widgetData?.clockColorMode==='accent' ? Theme.accent:widgetData?.clockColor || look?.primary || Theme.textPrimary
 readonly property string effect:widgetData?.clockEffect || 'solid'
 readonly property int alignment:widgetData?.clockAlign==='left' ? Text.AlignLeft:widgetData?.clockAlign==='right' ? Text.AlignRight:Text.AlignHCenter
 readonly property real fittedSize:Math.min(basePixelSize,basePixelSize*Math.max(1,width-40)/Math.max(1,Math.max(measure.advanceWidth(timeText),measure.boundingRect(timeText).width)))
 readonly property var hostBackdrop:GlassRegistry.lookup(QsWindow.window)
 readonly property var backdrop:{
  const shared=WidgetState.desktopBackdrop
  if(shared && (!QsWindow.window?.screen || shared.monitorName===QsWindow.window.screen.name))return shared
  return root.isSnapshot ? null:root.hostBackdrop
 }
 readonly property bool glassReady:effect==='glass' && !!backdrop?.captureSettled
 SystemClock{id:clock;precision:widgetData?.clockSeconds ? SystemClock.Seconds:SystemClock.Minutes}
 FontMetrics{id:measure;font:Qt.font({family:root.family,pixelSize:root.basePixelSize,weight:LockClockStyle.weightFor(root.widgetData?.clockWeight ?? .6),italic:root.widgetData?.clockItalic ?? root.style.italic,letterSpacing:root.widgetData?.clockSpacing ?? root.style.spacing})}
 Column {
  id:stack;anchors.centerIn:parent;width:parent.width-24;spacing:root.widgetData?.clockDateGap ?? 6
  component DateLine:Text{
   width:stack.width;horizontalAlignment:root.alignment;color:root.ink
   text:Qt.formatDateTime(clock.date,root.widgetData?.clockDateFormat || 'dddd, d MMMM')
   layer.enabled:root.effect==='glass';layer.effect:MultiEffect{shadowEnabled:true;shadowColor:'#80000000';shadowBlur:.4;shadowVerticalOffset:1;autoPaddingEnabled:true}
   font.family:root.widgetData?.clockDateFont || root.family;font.pixelSize:root.widgetData?.clockDateSize || Math.max(11,Math.min(28,root.fittedSize*.17));elide:Text.ElideRight
  }
  DateLine{visible:root.widgetData?.clockDate!==false && root.widgetData?.clockDatePosition!=='below'}
  Item{
   width:parent.width;height:digits.implicitHeight
   LockMac.MorphText{
    id:digits;anchors.fill:parent;text:root.timeText;horizontalAlignment:root.alignment;color:root.ink
    font:Qt.font({family:root.family,pixelSize:root.fittedSize,weight:LockClockStyle.weightFor(root.widgetData?.clockWeight ?? .6),italic:root.widgetData?.clockItalic ?? root.style.italic,letterSpacing:root.widgetData?.clockSpacing ?? root.style.spacing})
    duration:root.widgetData?.clockAnimate && !SettingsPreferences.accessibility.reduceMotion ? 420:0
    useBlur:duration>0;animateWidth:false;layer.enabled:true
    layer.effect:MultiEffect{shadowEnabled:root.effect==='shadow';shadowColor:'#90000000';shadowBlur:.65;shadowVerticalOffset:2;autoPaddingEnabled:true}
   }
   ShaderEffectSource{id:mask;anchors.fill:parent;sourceItem:digits;hideSource:root.glassReady || root.effect==='gradient';live:true;visible:false}
   Rectangle{
    anchors.fill:parent;visible:root.effect==='gradient'
    gradient:Gradient{GradientStop{position:0;color:root.ink}GradientStop{position:1;color:root.widgetData?.clockGradientColor || Theme.accent}}
    layer.enabled:visible;layer.effect:MultiEffect{maskEnabled:true;maskSource:mask;maskThresholdMin:.5;maskSpreadAtMin:1.0}
   }
   ShaderEffect{
    id:glyphGlass;anchors.fill:parent;visible:root.glassReady;blending:true
    property variant maskTex:mask
    property variant backTex:root.backdrop?.blurSource || null
    property vector2d size:Qt.vector2d(width,height)
    property vector2d screenOrigin:Qt.vector2d(0,0)
    property vector2d backgroundSize:root.backdrop ? Qt.vector2d(root.backdrop.screenSize.width,root.backdrop.screenSize.height):Qt.vector2d(1,1)
    property real ringRadius:Math.max(.75,Math.min(2.5,root.fittedSize*.018))
    property real thickness:Math.max(.5,Math.min(3,root.fittedSize*(root.widgetData?.clockGlassDepth ?? .016)))
    property real highlightStrength:root.widgetData?.clockGlassHighlight ?? .55
    property real highlightWidth:Math.max(1.5,root.fittedSize*.033)
    property real saturation:1.08
    property real lift:.02
    function syncOrigin(){const p=mapToItem(null,0,0),o=root.isSnapshot ? Qt.point(0,0):root.hostBackdrop?.windowPosition || Qt.point(0,0);const next=Qt.vector2d(p.x+o.x,p.y+o.y);if(next.x!==screenOrigin.x || next.y!==screenOrigin.y)screenOrigin=next}
    Component.onCompleted:syncOrigin()
    Connections{target:glyphGlass.Window.window;ignoreUnknownSignals:true;function onAfterAnimating(){if(glyphGlass.visible)glyphGlass.syncOrigin()}}
    vertexShader:Qt.resolvedUrl(Quickshell.shellDir+'/assets/shaders/liquidglass/GlyphGlass.vert.qsb')
    fragmentShader:Qt.resolvedUrl(Quickshell.shellDir+'/assets/shaders/liquidglass/WidgetGlyphGlass.frag.qsb')
   }
  }
  DateLine{visible:root.widgetData?.clockDate!==false && root.widgetData?.clockDatePosition==='below'}
 }
}
