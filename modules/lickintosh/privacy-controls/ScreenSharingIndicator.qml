import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import qs.services

Item {
    id: root

    required property var hostWindow
    readonly property var sessions: {
        const apps = new Set(MediaCaptureState.visibleDetails.filter(entry => entry.kind === "screen")
                             .map(entry => entry.app))
        if (CaptureState.recording) apps.add("Quickshot")
        return Array.from(apps)
    }
    property bool opened: false

    implicitWidth: 28
    implicitHeight: 24
    visible: sessions.length > 0

    function windowFor(app) {
        const wanted = app.toLowerCase().replace(/[^a-z0-9]/g, "")
        return Hyprland.toplevels.values.find(toplevel => {
            const info = toplevel.lastIpcObject
            return [info?.class, info?.initialClass].some(value =>
                String(value || "").split(".").pop().toLowerCase().replace(/[^a-z0-9]/g, "") === wanted)
        }) || null
    }

    onVisibleChanged: if (!visible) opened = false

    component ShareIcon: Image {
        source: Quickshell.shellPath("assets/icons/screenshare.svg")
        sourceSize: Qt.size(48, 48)
        fillMode: Image.PreserveAspectFit
    }

    Button {
        id: indicator
        anchors.centerIn: parent
        width: parent.width
        height: 19
        Accessible.name: qsTr("Screen sharing")
        checkable: true
        checked: root.opened
        onClicked: root.opened = !root.opened

        background: Rectangle {
            radius: 5
            color: indicator.hovered || indicator.checked ? "#685acf" : "#5849ba"
            border.color: "#40c8bbff"
        }
        contentItem: Item {
            ShareIcon {
                anchors.centerIn: parent
                width: 17
                height: 17
            }
        }
        ToolTip.visible: hovered && !root.opened
        ToolTip.text: Accessible.name
    }

    LazyLoader {
        active: root.opened && root.visible && root.hostWindow !== null

        PanelWindow {
            id: popup
            screen: root.hostWindow.screen
            anchors { top: true; left: true; right: true }
            implicitHeight: screen.height
            exclusiveZone: -1
            color: "transparent"
            WlrLayershell.namespace: "quickintosh-sharing-panel"
            WlrLayershell.layer: WlrLayer.Overlay
            WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand
            property bool entered: false
            Component.onCompleted: Qt.callLater(() => entered = true)

            Shortcut { sequence: "Escape"; onActivated: root.opened = false }

            MouseArea {
                anchors.fill: parent
                onClicked: root.opened = false
            }

            Rectangle {
                id: card
                readonly property real buttonEdge: root.mapToItem(null, root.width, 0).x
                x: Math.max(8, Math.min(popup.width - width - 8, buttonEdge - width))
                y: Math.max(32, root.hostWindow.height) + 5
                width: Math.min(320, popup.width - 16)
                height: panel.implicitHeight + 28
                opacity: popup.entered ? 1 : 0
                scale: popup.entered ? 1 : .96
                transformOrigin: Item.TopRight
                Behavior on opacity { NumberAnimation { duration: ShellMotion.fade() } }
                Behavior on scale { NumberAnimation { duration: ShellMotion.fade(); easing.type: Easing.OutCubic } }
                radius: 19
                color: Theme.plainSurfaces ? (Theme.isLight ? "#f4f6fc" : "#1c2333")
                                          : (Theme.isLight ? "#e8edf1fc" : "#dc171f32")
                border.width: 1
                border.color: Theme.isLight ? "#25000000" : "#37ffffff"

                MouseArea { anchors.fill: parent }

                ColumnLayout {
                    id: panel
                    anchors { left: parent.left; right: parent.right; top: parent.top; margins: 14 }
                    spacing: 11

                    RowLayout {
                        ShareIcon { Layout.preferredWidth: 20; Layout.preferredHeight: 20 }
                        Text {
                            Layout.fillWidth: true
                            text: qsTr("Screen sharing")
                            font.pixelSize: 15
                            font.weight: Font.DemiBold
                            color: Theme.textPrimary
                        }

                    }

                    Text {
                        text: qsTr("Currently sharing")
                        font.pixelSize: 11
                        font.weight: Font.DemiBold
                        color: Theme.textPrimary
                        opacity: .7
                    }

                    ScrollView {
                        Layout.fillWidth: true
                        Layout.preferredHeight: Math.min(sessionsList.implicitHeight, 280)
                        contentWidth: availableWidth
                        clip: true
                        ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                        ColumnLayout {
                            id: sessionsList
                            width: parent.width
                            spacing: 6

                            Repeater {
                                model: root.sessions
                                delegate: Rectangle {
                                    id: session
                                    required property string modelData
                                    readonly property var appWindow: root.windowFor(modelData)
                                    Layout.fillWidth: true
                                    implicitHeight: sessionRow.implicitHeight + 16
                                    radius: 11
                                    color: Theme.isLight ? "#100e286e" : "#20aec5ff"

                                    RowLayout {
                                        id: sessionRow
                                        anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; margins: 8 }
                                        ShareIcon {
                                            Layout.preferredWidth: 18
                                            Layout.preferredHeight: 18
                                        }
                                        Text {
                                            Layout.fillWidth: true
                                            text: modelData
                                            textFormat: Text.PlainText
                                            color: Theme.textPrimary
                                            elide: Text.ElideRight
                                        }
                                        Button {
                                            visible: modelData === "Quickshot" && CaptureState.recording
                                            text: qsTr("Stop recording")
                                            onClicked: CaptureState.send({action: "stopRecord"})
                                        }
                                        Button {
                                            readonly property string address: session.appWindow?.address || ""
                                            visible: modelData !== "Quickshot" && /^(?:0x)?[0-9a-f]+$/i.test(address)
                                            text: qsTr("Open app")
                                            onClicked: {
                                                const target = address.startsWith("0x") ? address : "0x" + address
                                                Hyprland.dispatch('hl.dsp.focus({window="address:' + target + '"})')
                                                root.opened = false
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
