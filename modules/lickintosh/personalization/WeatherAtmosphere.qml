import QtQuick
import Quickshell
import Quickshell.Widgets
import qs.services

ClippingRectangle {
    id: root

    property string kind: ""
    property bool active: true
    property real intensity: 1
    property real speed: 1
    property bool lightning: true
    property color dropColor: "#9cd9ff"
    property int seed: 0

    readonly property bool storm: kind === "storm"
    readonly property bool wet: storm || kind === "rain" || kind === "drizzle"
    readonly property bool running: visible && active && wet
        && RenderingState.ambientAnimations && !SettingsPreferences.locked
    readonly property string artwork: storm && lightning ? "storm" : wet ? "rain"
        : kind === "sun" || kind === "partly" ? "clear" : "clouds"
    property real phase: 0

    visible: kind !== ""
    radius: Math.min(22, height / 6)
    color: "transparent"

    Image {
        anchors.fill: parent
        source: root.visible ? Quickshell.shellPath("rosa/overlays/assets/" + root.artwork + ".webp") : ""
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        opacity: .88
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0; color: "#48213250" }
            GradientStop { position: 1; color: "#9c0a1424" }
        }
    }

    FrameAnimation {
        running: root.running
        onTriggered: root.phase = (root.phase + Math.min(frameTime, .05) * root.speed) % 120
    }

    Rectangle {
        anchors.fill: parent
        color: "#9ab1ff"
        opacity: root.running && root.storm && root.lightning
            ? .14 * Math.pow(Math.max(0, Math.cos(root.phase * .52 + .9)), 65) : 0
    }

    Repeater {
        model: root.wet && root.active ? Math.min(20, Math.max(4, Math.round(10 * root.intensity))) : 0
        delegate: Rectangle {
            required property int index
            readonly property real noise: ((index * 73 + root.seed * 31) % 101) / 101
            readonly property real pulse: root.running ? (1 + Math.sin(root.phase * 1.15 + index * 2.17)) / 2 : .7
            width: 3 + noise * 7
            height: width * (1 + noise * .45)
            radius: width / 2
            scale: .65 + pulse * .35
            opacity: .22 + .48 * pulse
            x: 4 + (index * .618034 % 1) * Math.max(0, root.width - width - 8)
            y: 4 + (index * .381966 % 1) * Math.max(0, root.height - height - 8)
            color: Qt.alpha(root.dropColor, .30)
            border.width: 1
            border.color: Qt.alpha(root.dropColor, .62)

            Rectangle {
                x: parent.width * .24; y: parent.height * .17
                width: Math.max(1, parent.width * .25); height: width
                radius: width / 2
                color: "#dfffffff"
            }
        }
    }
}
