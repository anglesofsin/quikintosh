import QtQuick
import QtQuick.Effects
import Quickshell
import qs.services
import qs.components.glass
Item{
 id:root
 property string value:''
 property var options:({})
 property color ink:Theme.textPrimary
 property bool isSnapshot:false
 property bool animationEnabled:false
 readonly property string face:options.textStyle || 'modern'
 readonly property string family:options.textFont || (face==='typewriter' ? 'SF Mono':face==='serif' ? 'serif':face==='handwriting' ? 'cursive':face==='rounded' ? 'SF Pro Rounded':'SF Pro Display')
 readonly property string content:options.textCase==='upper' ? value.toUpperCase():options.textCase==='lower' ? value.toLowerCase():value
 readonly property int alignment:options.textAlign==='left' ? Text.AlignLeft:options.textAlign==='right' ? Text.AlignRight:Text.AlignHCenter
 readonly property string effect:options.textEffect || (face==='neon' ? 'neon':'solid')
 readonly property var hostBackdrop:GlassRegistry.lookup(QsWindow.window)
 readonly property var backdrop:{const shared=WidgetState.desktopBackdrop;if(shared && (!QsWindow.window?.screen || shared.monitorName===QsWindow.window.screen.name))return shared;return isSnapshot ? null:hostBackdrop}
 readonly property bool glassReady:effect==='glass' && !!backdrop?.captureSettled
 implicitHeight:letters.implicitHeight+24
 property real reveal:1
 function animate(){if(animationEnabled && options.textAnimation && options.textAnimation!=='none' && !SettingsPreferences.accessibility.reduceMotion)entrance.restart();else reveal=1}
 onValueChanged:animate()
 onAnimationEnabledChanged:animate()
 NumberAnimation{id:entrance;target:root;property:'reveal';from:0;to:1;duration:root.options.textAnimationMs || 700;easing.type:Easing.OutCubic}
 Item{
  id:body;anchors.fill:parent;rotation:root.options.textRotation || 0;opacity:root.reveal
  transform:Translate{y:root.options.textAnimation==='slide' ? (1-root.reveal)*16:0}
  Rectangle{
   width:Math.min(parent.width,letters.contentWidth+24);height:Math.min(parent.height,letters.contentHeight+16)
   x:root.alignment===Text.AlignLeft ? letters.x-8:root.alignment===Text.AlignRight ? letters.x+letters.width-width+8:letters.x+(letters.width-width)/2
   y:root.options.textVertical==='top' ? letters.y-8:root.options.textVertical==='bottom' ? letters.y+letters.height-height+8:letters.y+(letters.height-height)/2
   visible:!!root.options.textDecorated;radius:root.options.textBackgroundRadius ?? 10
   color:root.options.textBackground || Theme.accent;opacity:root.options.textBackgroundOpacity ?? .25
  }
  Text{
   id:letters;anchors.fill:parent;anchors.margins:root.options.textPadding ?? 12
   text:root.content.slice(0,6000);textFormat:Text.PlainText;wrapMode:Text.WordWrap
   horizontalAlignment:root.alignment;verticalAlignment:root.options.textVertical==='top' ? Text.AlignTop:root.options.textVertical==='bottom' ? Text.AlignBottom:Text.AlignVCenter
   color:root.ink
   font.family:root.family;font.pixelSize:root.options.textSize || 32;font.weight:root.options.textWeight || (root.face==='modern' ? Font.Bold:Font.Medium)
   font.italic:!!root.options.textItalic;font.letterSpacing:root.options.textSpacing || 0
   fontSizeMode:root.options.textAutoSize===false ? Text.FixedSize:Text.Fit;minimumPixelSize:10
   lineHeight:root.options.textLineHeight || 1.1
   style:root.effect==='outline' ? Text.Outline:Text.Normal;styleColor:root.options.textOutlineColor || Theme.accent
   layer.enabled:root.effect==='shadow' || root.effect==='neon'
   layer.effect:MultiEffect{shadowEnabled:true;shadowColor:root.effect==='neon' ? root.ink:'#a0000000';shadowBlur:root.effect==='neon' ? .9:.45;shadowHorizontalOffset:0;shadowVerticalOffset:root.effect==='neon' ? 0:2;autoPaddingEnabled:true}
  }
  ShaderEffectSource{id:mask;anchors.fill:letters;sourceItem:letters;hideSource:root.glassReady || root.effect==='gradient';live:true;visible:false}
  Rectangle{
   anchors.fill:letters;visible:root.effect==='gradient'
   gradient:Gradient{GradientStop{position:0;color:root.ink}GradientStop{position:1;color:root.options.textGradientColor || Theme.accent}}
   layer.enabled:visible;layer.effect:MultiEffect{maskEnabled:true;maskSource:mask;maskThresholdMin:.5;maskSpreadAtMin:1}
  }
  ShaderEffect{
   id:glyph;anchors.fill:letters;visible:root.glassReady
   property variant maskTex:mask
   property variant backTex:root.backdrop?.glyphSource || root.backdrop?.blurSource || null
   property vector2d size:Qt.vector2d(width,height)
   property vector2d screenOrigin:Qt.vector2d(0,0)
   property vector2d backgroundSize:root.backdrop ? Qt.vector2d(root.backdrop.screenSize.width,root.backdrop.screenSize.height):Qt.vector2d(1,1)
   property real ringRadius:2
   property real thickness:3
   property real highlightStrength:.55
   property real highlightWidth:2
   property real saturation:1.08
   property real lift:.02
   function sync(){const p=mapToItem(null,0,0),o=root.isSnapshot ? Qt.point(0,0):root.hostBackdrop?.windowPosition || Qt.point(0,0);const next=Qt.vector2d(p.x+o.x,p.y+o.y);if(next.x!==screenOrigin.x || next.y!==screenOrigin.y)screenOrigin=next}
   Component.onCompleted:sync()
   Connections{target:glyph.Window.window;ignoreUnknownSignals:true;function onAfterAnimating(){if(glyph.visible)glyph.sync()}}
   vertexShader:Qt.resolvedUrl(Quickshell.shellDir+'/assets/shaders/liquidglass/GlyphGlass.vert.qsb')
   fragmentShader:Qt.resolvedUrl(Quickshell.shellDir+'/assets/shaders/liquidglass/WidgetGlyphGlass.frag.qsb')
  }
 }
}
