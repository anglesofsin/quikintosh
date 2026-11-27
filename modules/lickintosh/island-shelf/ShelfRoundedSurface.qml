import QtQuick
// One analytic alpha contour for the background, border and all child content.
// The coverage mask stays at device resolution; no full-panel supersampling.
Item {
 id:root
 property real radius:0
 property real topLeftRadius:radius
 property real topRightRadius:radius
 property real bottomRightRadius:radius
 property real bottomLeftRadius:radius
 property color color:'transparent'
 property bool antialiasing:true
 property bool contentUnderBorder:false
 property bool contentInsideBorder:!contentUnderBorder
 readonly property alias border:metrics.border
 readonly property alias contentItem:content
 default property alias data:content.data
 property alias children:content.children
 Rectangle{id:metrics;visible:false;border.width:0;border.color:'transparent'}
 Item{id:container;anchors.fill:root
  Item{id:content;anchors.fill:parent;anchors.margins:root.contentInsideBorder ? root.border.width:0}
 }
 ShaderEffectSource{id:texture;sourceItem:container;hideSource:true;smooth:true;live:true}
 ShaderEffect {
  anchors.fill:root
  property var contentTexture:texture
  property vector2d surfaceSize:Qt.vector2d(root.width,root.height)
  property vector4d cornerRadii:Qt.vector4d(root.topLeftRadius,root.topRightRadius,root.bottomRightRadius,root.bottomLeftRadius)
  property color backgroundColor:root.color
  property color borderColor:root.border.color
  property real borderWidth:root.border.width
  fragmentShader:Qt.resolvedUrl('shaders/smooth-surface.frag.qsb')
 }
}
