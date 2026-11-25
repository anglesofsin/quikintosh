import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import Quickshell
import Quickshell.Wayland
import Quickshell.Widgets
import qs.services
import qs.rosa.services
import qs.ui.topbar.notch.dashboard
import qs.ui.topbar.statusarea.notifcenter
import qs.ui.widgets.types

PanelWindow {
    id: panel
    required property var output
    screen: output
    anchors.top: true
    margins.top: Math.max(0, capsuleTop)
    implicitWidth: Math.min(output.width - 24, 1120)
    implicitHeight: 306
    exclusiveZone: -1
    color: 'transparent'
    WlrLayershell.namespace: 'quickintosh-island-dashboard'
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand

    property real capsuleTop: 3
    property real capsuleWidth: 92
    property real capsuleHeight: 26
    readonly property bool expandedBody: expanded && entered
    property bool expanded: false
    property bool entered: false
    Component.onCompleted: Qt.callLater(() => entered = true)
    signal pointerChanged(bool inside)
    property int page: 0
    readonly property int bodyHeight: page === 1 ? 306 : 244
    readonly property var notices: NotifService.appGroupsList.concat(NotifService.systemGroupsList)
        .flatMap(group => group.items)
    function selectPage(index) {
        if (page === index) return
        page = index
        pageArrival.restart()
    }
    property var selectedHour: null
    readonly property int displayedCode: selectedHour?.code ?? WeatherState.weatherCode
    readonly property bool displayedDay: selectedHour?.isDay ?? WeatherState.isDay
    signal dismissed()
    Shortcut { sequence: 'Escape'; onActivated: panel.dismissed() }

    function condition(code) {
        if (code >= 95) return qsTr('Thunderstorm')
        if ((code >= 71 && code <= 77) || code === 85 || code === 86) return qsTr('Snow')
        if (code >= 51 && code <= 57) return qsTr('Drizzle')
        if (code === 61 || code === 80) return qsTr('Light rain')
        if (code === 65 || code === 82) return qsTr('Heavy rain')
        if (code >= 61 && code <= 82) return qsTr('Rain')
        if (code === 45 || code === 48) return qsTr('Fog')
        if (code === 3) return qsTr('Cloudy')
        if (code === 2) return qsTr('Partly cloudy')
        return qsTr('Clear')
    }

    mask: Region { item: body; radius: 30 }
    ClippingRectangle {
        id: body
        anchors.horizontalCenter: parent.horizontalCenter
        width: panel.expandedBody ? parent.width : Math.min(parent.width, panel.capsuleWidth)
        height: panel.expandedBody ? panel.bodyHeight : panel.capsuleHeight
        radius: Math.min(30, height / 2)
        color: "#f9000000"
        border.width: 1
        border.color: "#32ffffff"
        Behavior on width { NumberAnimation { duration: ShellMotion.fade(); easing.type: Easing.OutCubic } }
        Behavior on height { NumberAnimation { duration: ShellMotion.fade(); easing.type: Easing.OutCubic } }
        HoverHandler { onHoveredChanged: panel.pointerChanged(hovered) }

        WeatherAtmosphere {
            anchors.fill: parent
            kind: panel.page === 1 && WeatherState.available && IslandConfig.s('dashboardWeatherArt')
                ? WeatherState._kindFor(panel.displayedCode, panel.displayedDay) : ""
            active: panel.expandedBody
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 18
            opacity: panel.expandedBody && body.height > 160 ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: ShellMotion.fade() } }
            spacing: 12

            Flickable {
                Layout.fillWidth: true
                Layout.preferredHeight: tabs.implicitHeight
                contentWidth: tabs.implicitWidth
                clip: true
                boundsBehavior: Flickable.StopAtBounds
                RowLayout {
                    id: tabs
                    Repeater {
                        model: [qsTr('Dashboard'), qsTr('Weather'), qsTr('Performance'), qsTr('Media'), qsTr('Notifications'), qsTr('Settings')]
                        delegate: Button {
                            required property string modelData
                            required property int index
                            text: modelData
                            checkable: true
                            checked: panel.page === index
                            onClicked: panel.selectPage(index)
                            padding: 7
                            background: Rectangle {
                                radius: height / 2
                                color: parent.checked ? "#30ffffff" : parent.hovered ? "#26ffffff" : "transparent"
                                border.color: parent.checked ? "#36ffffff" : "transparent"
                            }
                            contentItem: Text {
                                text: modelData
                                color: "#f1f5ff"
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                                font.pixelSize: 13
                                font.weight: parent.checked ? Font.DemiBold : Font.Medium
                            }
                        }
                    }
                }
            }

            Loader {
                Layout.fillWidth: true
                Layout.fillHeight: true
                id: pageContent
                sourceComponent: [overview, forecast, performance, media, notifications, preferences][panel.page]
                NumberAnimation on opacity {
                    id: pageArrival
                    from: .35; to: 1
                    duration: ShellMotion.fade()
                    easing.type: Easing.OutCubic
                }
            }
        }
    }

    Component {
        id: overview
        Item {
            id: overviewFrame
            DashboardPage {
                width: Math.max(1180, overviewFrame.width)
                height: overviewFrame.height / scale
                scale: Math.min(1, overviewFrame.width / width)
                transformOrigin: Item.TopLeft
                profileModule: IslandConfig.s('dashboardCamera') ? cameraPage : null
            }
        }
    }

    Component { id: performance; PerformancePage {} }

    Component {
        id: media
        RowLayout {
            spacing: 20
            MediaModule { Layout.fillWidth: true }
            ColumnLayout {
                Layout.fillWidth: true
                Label { text: MprisState.trackTitle || qsTr("Nothing playing"); color: "white"; font.pixelSize: 17 }
                Slider {
                    Layout.fillWidth: true
                    enabled: MprisState.canSeek
                    from: 0; to: Math.max(1, MprisState.length)
                    value: MprisState.position
                    onMoved: MprisState.seek(value)
                    Accessible.name: qsTr("Playback position")
                }
                Component.onCompleted: MprisState.watchPosition(true)
                Component.onDestruction: MprisState.watchPosition(false)
            }
        }
    }

    Component {
        id: notifications
        ColumnLayout {
            RowLayout {
                Label { text: qsTr("Recent notifications"); color: "white"; Layout.fillWidth: true }
                Switch {
                    text: qsTr("Do Not Disturb"); checked: NotifService.dndEnabled
                    onToggled: NotifService.dndEnabled = checked
                }
            }
            ListView {
                id: notificationList
                Layout.fillWidth: true; Layout.fillHeight: true
                clip: true
                spacing: 5
                model: panel.notices
                delegate: Rectangle {
                    required property var modelData
                    width: ListView.view.width; height: 38; radius: 9; color: "#1dffffff"
                    RowLayout {
                        anchors.fill: parent; anchors.margins: 6
                        Label {
                            Layout.fillWidth: true
                            text: (modelData.appName || "") + "  ·  " + (modelData.summary || "")
                            textFormat: Text.PlainText
                            elide: Text.ElideRight; color: "white"
                        }
                        Button {
                            text: qsTr("Dismiss")
                            onClicked: NotifService.removeFromCenter(modelData)
                        }
                    }
                }
                Label { anchors.centerIn: parent; visible: notificationList.count === 0; text: qsTr("No notifications"); color: "#c0ffffff" }
            }
        }
    }

    Component {
        id: preferences
        ColumnLayout {
            Repeater {
                model: [
                    ["dashboardCamera", qsTr("Camera in profile tile")],
                    ["dashboardWeatherArt", qsTr("Weather effects")],
                    ["dashboardWeatherLocation", qsTr("Show weather location")]
                ]
                delegate: Switch {
                    required property var modelData
                    text: modelData[1]
                    checked: IslandConfig.s(modelData[0])
                    onToggled: IslandConfig.setStyle(modelData[0], checked)
                }
            }
            Item { Layout.fillHeight: true }
        }
    }

    Component {
        id: forecast
        ColumnLayout {
            spacing: 12

            RowLayout {
                Layout.fillWidth: true
                ColumnLayout {
                    Text {
                        visible: WeatherState.available && IslandConfig.s('dashboardWeatherLocation')
                        text: WeatherState.city
                        color: '#e8f2ff'
                        font.pixelSize: 16
                        font.weight: Font.DemiBold
                    }
                    Text {
                        text: WeatherState.available ? Math.round(panel.selectedHour?.temp ?? WeatherState.tempC) + '°' : qsTr('Weather unavailable')
                        color: 'white'
                        font.pixelSize: WeatherState.available ? 56 : 22
                    }
                }
                Text {
                    Layout.alignment: Qt.AlignBottom
                    visible: WeatherState.available
                    text: panel.condition(panel.displayedCode)
                    color: '#ecf3ff'
                    font.pixelSize: 18
                }
                Item { Layout.fillWidth: true }
            }
            Flickable {
                Layout.fillWidth: true
                Layout.preferredHeight: 68
                contentWidth: hours.implicitWidth
                clip: true
                Row {
                    id: hours
                    spacing: 8
                    Repeater {
                        model: WeatherState.hourly
                        delegate: Rectangle {
                            required property var modelData
                            width: 112; height: 66; radius: 13
                            color: panel.selectedHour === modelData ? '#644c79b6' : '#3d12233c'
                            TapHandler {
                                onTapped: panel.selectedHour = panel.selectedHour === modelData ? null : modelData
                            }
                            Column {
                                anchors.centerIn: parent
                                spacing: 3
                                Text { text: modelData.time.split('T')[1]; color: '#dbe8ff'; font.pixelSize: 12 }
                                Text { text: modelData.temp + '°  ' + panel.condition(modelData.code); color: 'white'; font.pixelSize: 12 }
                            }
                        }
                    }
                }
            }
            Flickable {
                Layout.fillWidth: true
                Layout.preferredHeight: 68
                contentWidth: days.implicitWidth
                clip: true
                Row {
                    id: days
                    spacing: 8
                    Repeater {
                        model: WeatherState.forecast
                        delegate: Rectangle {
                            required property var modelData
                            width: 126; height: 66; radius: 13; color: '#3d12233c'
                            Column {
                                anchors.centerIn: parent
                                spacing: 3
                                Text { text: Qt.formatDate(new Date(modelData.date + 'T12:00:00'), 'ddd'); color: '#dbe8ff'; font.pixelSize: 12 }
                                Text { text: panel.condition(modelData.code); color: 'white'; font.pixelSize: 12 }
                                Text { text: modelData.tempMin + '° / ' + modelData.tempMax + '°'; color: 'white'; font.pixelSize: 12 }
                            }
                        }
                    }
                }
            }
            Item { Layout.fillHeight: true }
        }
    }

    Component {
        id: cameraPage
        Item {
            id: cameraTile
            property bool requested: false
            Button {
                anchors.centerIn: parent
                visible: !cameraTile.requested
                text: qsTr('Camera')
                onClicked: cameraTile.requested = true
            }
            Loader {
                anchors.centerIn: parent
                width: 94; height: 110
                active: cameraTile.requested
                sourceComponent: ColumnLayout {
                    MediaDevices { id: devices }
                    Camera {
                        id: camera
                        cameraDevice: devices.defaultVideoInput
                        active: devices.videoInputs.length > 0 && panel.visible
                    }
                    CaptureSession { camera: camera; videoOutput: cameraPreview }
                    VideoOutput {
                        id: cameraPreview
                        Layout.fillWidth: true; Layout.fillHeight: true
                        visible: devices.videoInputs.length > 0
                        fillMode: VideoOutput.PreserveAspectCrop
                    }
                    Text {
                        Layout.fillWidth: true
                        visible: devices.videoInputs.length === 0 || camera.error !== Camera.NoError
                        text: devices.videoInputs.length ? camera.errorString : qsTr('No camera found')
                        wrapMode: Text.WordWrap
                        color: Theme.textPrimary
                    }
                    Button {
                        Layout.fillWidth: true
                        text: qsTr('Turn off')
                        onClicked: cameraTile.requested = false
                    }
                }
            }
        }
    }
}
