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
 readonly property string composition:widgetData?.variant || 'classic'
 readonly property bool stacked:composition==='stacked'
 readonly property real weight:widgetData?.clockWeight ?? (composition==='minimal' ? .25:stacked ? .4:.6)
 readonly property bool showDate:widgetData?.clockDate ?? (composition!=='minimal')
 readonly property bool dateBelow:(widgetData?.clockDatePosition || (stacked ? 'below':'above'))==='below'
 readonly property var style:LockClockStyle.styleAt(widgetData?.clockStyle ?? (composition==='minimal' ? 3:stacked ? 1:0))
 readonly property bool automatic:widgetData?.clockAutoSize ?? (widgetData?.clockSize===undefined)
 readonly property real basePixelSize:automatic ? Math.max(24,Math.min((width-32)*(stacked ? .60:.34),(height-24)*(stacked ? .30:.56))):widgetData?.clockSize || 76
 readonly property string timeFormat:widgetData?.clockFormat || (widgetData?.clock12Hour ? (widgetData?.clockSeconds ? 'h:mm:ss AP':'h:mm AP'):(widgetData?.clockSeconds ? 'HH:mm:ss':'HH:mm'))
 readonly property string timeText:stacked ? Qt.formatDateTime(clock.date,widgetData?.clock12Hour ? 'hh':'HH')+'\n'+Qt.formatDateTime(clock.date,widgetData?.clockSeconds ? 'mm:ss':'mm'):Qt.formatDateTime(clock.date,timeFormat)
 readonly property string family:widgetData?.clockFont || style.family
 readonly property color ink:widgetData?.clockColorMode==='accent' ? Theme.accent:widgetData?.clockColor || look?.primary || Theme.textPrimary
 readonly property string effect:widgetData?.clockEffect || 'solid'
 readonly property int alignment:widgetData?.clockAlign==='left' ? Text.AlignLeft:widgetData?.clockAlign==='right' ? Text.AlignRight:Text.AlignHCenter
 // Reserve the widest time for this format, independent of the live digits.
 // Custom fonts without tabular figures still receive a stable fitting size.
 readonly property real reservedTextWidth:{
  let widest='0',digitWidth=0,result=1
  for(let n=0;n<10;n++){
   const digit=String(n),w=Math.max(measure.advanceWidth(digit),measure.boundingRect(digit).width)
   if(w>digitWidth){digitWidth=w;widest=digit}
  }
  for(let h=0;h<24;h++){
   const date=new Date(2000,10,28,h,58,58)
   const value=stacked ? Qt.formatDateTime(date,widgetData?.clock12Hour ? 'hh':'HH')+'\n'+Qt.formatDateTime(date,widgetData?.clockSeconds ? 'mm:ss':'mm'):Qt.formatDateTime(date,timeFormat)
   for(const line of value.replace(/[0-9]/g,widest).split('\n'))result=Math.max(result,measure.advanceWidth(line),measure.boundingRect(line).width)
  }
  return result
 }
 readonly property real fittedSize:Math.min(basePixelSize,basePixelSize*Math.max(1,width-40)/reservedTextWidth)
 readonly property var hostBackdrop:GlassRegistry.lookup(QsWindow.window)
 readonly property var backdrop:{
  const shared=WidgetState.desktopBackdrop
  if(shared && (!QsWindow.window?.screen || shared.monitorName===QsWindow.window.screen.name))return shared
  return root.isSnapshot ? null:root.hostBackdrop
 }
 readonly property bool glassReady:effect==='glass' && !!backdrop?.captureSettled
 SystemClock{id:clock;precision:widgetData?.clockSeconds ? SystemClock.Seconds:SystemClock.Minutes}
 FontMetrics{id:measure;font:Qt.font({family:root.family,pixelSize:root.basePixelSize,weight:LockClockStyle.weightFor(root.weight),italic:root.widgetData?.clockItalic ?? root.style.italic,letterSpacing:root.widgetData?.clockSpacing ?? root.style.spacing,features:{tnum:1}})}
 Column {
  id:stack;anchors.centerIn:parent;width:parent.width-24;spacing:root.widgetData?.clockDateGap ?? 6
  component DateLine:Text{
   width:stack.width;horizontalAlignment:root.alignment;color:root.ink
   text:Qt.formatDateTime(clock.date,root.widgetData?.clockDateFormat || 'dddd, d MMMM')
   layer.enabled:root.effect==='glass';layer.effect:MultiEffect{shadowEnabled:true;shadowColor:'#80000000';shadowBlur:.4;shadowVerticalOffset:1;autoPaddingEnabled:true}
   font.family:root.widgetData?.clockDateFont || root.family;font.pixelSize:root.widgetData?.clockDateSize || Math.max(11,Math.min(28,root.fittedSize*.17));elide:Text.ElideRight
  }
  DateLine{visible:root.showDate && !root.dateBelow}
  Item{
   width:parent.width;height:digits.implicitHeight
   LockMac.MorphText{
    id:digits;anchors.fill:parent;text:root.timeText;horizontalAlignment:root.alignment;color:root.ink
    font:Qt.font({family:root.family,pixelSize:root.fittedSize,weight:LockClockStyle.weightFor(root.weight),italic:root.widgetData?.clockItalic ?? root.style.italic,letterSpacing:root.widgetData?.clockSpacing ?? root.style.spacing,features:{tnum:1}})
    duration:root.widgetData?.clockAnimate && !SettingsPreferences.accessibility.reduceMotion ? 420:0
    useBlur:duration>0;animateWidth:false;stretch:false;scaleIn:1;scaleOut:1;layer.enabled:true
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
    property variant backTex:root.backdrop?.glyphSource || root.backdrop?.blurSource || null
    property vector2d size:Qt.vector2d(width,height)
    property vector2d screenOrigin:Qt.vector2d(0,0)
    property vector2d backgroundSize:root.backdrop ? Qt.vector2d(root.backdrop.screenSize.width,root.backdrop.screenSize.height):Qt.vector2d(1,1)
    property real ringRadius:Math.max(.75,Math.min(4,root.fittedSize*.025))
    property real thickness:Math.max(.5,Math.min(6,root.fittedSize*(root.widgetData?.clockGlassDepth ?? .028)))
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
  DateLine{visible:root.showDate && root.dateBelow}
 }
}
