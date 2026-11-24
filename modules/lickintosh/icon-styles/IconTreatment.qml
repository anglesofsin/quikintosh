import QtQuick
import qs.services
ShaderEffect{
 property var source
 readonly property color lowColor:AppearanceState.iconLow
 readonly property color highColor:AppearanceState.iconHigh
 readonly property real treatment:AppearanceState.treatment
 readonly property real strength:AppearanceState.strength
 fragmentShader:Qt.resolvedUrl('icon-style.frag.qsb')
}
