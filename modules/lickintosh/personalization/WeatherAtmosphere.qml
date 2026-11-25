import QtQuick

// Compatibility surface for saved weather preferences. Weather artwork is
// supplied as image assets; this item intentionally draws no atmosphere.
Item {
    property string kind: ""
    property bool active: true
    property real intensity: 1
    property real speed: 1
    property bool lightning: true
    property color dropColor: "#9cd9ff"
    property int seed: 0
}
