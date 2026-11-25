import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import Quickshell
import Quickshell.Wayland
import Quickshell.Hyprland
import Quickshell.Io
import Quickshell.Widgets
import qs.services
import qs.components
import qs.ui.widgets
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
    implicitWidth: Math.min(output.width - 32, 1120)
    implicitHeight: 306
    exclusiveZone: -1
    color: 'transparent'
    WlrLayershell.namespace: 'quickintosh-island-dashboard'
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand

    FontLoader { id: sfText; source: Quickshell.shellPath("assets/fonts/SFPT/SF-Pro-Text-Regular.otf") }
    FontLoader { source: Quickshell.shellPath("assets/fonts/SFPT/SF-Pro-Text-Semibold.otf") }
    FontLoader { id: sfDisplay; source: Quickshell.shellPath("assets/fonts/SFPD/SF-Pro-Display-Regular.otf") }
    FontLoader { source: Quickshell.shellPath("assets/fonts/SFPD/SF-Pro-Display-Light.otf") }

    function weatherImage(code, daytime) {
        if (!daytime && code <= 1) return "night"
        if (code >= 95) return "storm"
        if ((code >= 71 && code <= 77) || code === 85 || code === 86) return "snow"
        if (code === 65 || code === 67 || code === 82) return "heavy-rain"
        if (code >= 51 && code <= 82) return "rain"
        if (code === 2) return "partly"
        if (code >= 3) return "clouds"
        return "sun"
    }
    component WeatherArt: Image {
        required property int code
        property bool daytime: true
        source: Qt.resolvedUrl("assets/weather-" + panel.weatherImage(code, daytime) + ".png")
        sourceSize: Qt.size(128,128)
        fillMode: Image.PreserveAspectFit
        asynchronous: true
    }

    component IslandButton: Button {
        id: control
        implicitHeight: 30
        implicitWidth: Math.max(30, label.implicitWidth + 24)
        padding: 8
        background: Rectangle {
            radius: height / 2
            color: control.down ? "#40ffffff" : control.hovered ? "#2bffffff" : "#19ffffff"
            border.color: "#28ffffff"
        }
        contentItem: Text {
            id: label
            text: control.text
            color: control.enabled ? "#f5f5f7" : "#77777c"
            font.family: sfText.name
            font.pixelSize: 12
            font.weight: Font.Medium
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    component IslandSwitch: Switch {
        id: control
        implicitHeight: 36
        implicitWidth: caption.implicitWidth + 54
        Layout.maximumWidth: parent ? parent.width : implicitWidth
        spacing: 16
        padding: 0
        indicator: Rectangle {
            x: control.width - width
            y: (control.height - height) / 2
            width: 38; height: 23; radius: 12
            color: control.checked ? "#4bce77" : "#4a4a50"
            Rectangle {
                x: control.checked ? 17 : 2
                y: 2; width: 19; height: 19; radius: 10
                color: "white"
                Behavior on x { NumberAnimation { duration: 140; easing.type: Easing.OutCubic } }
            }
        }
        contentItem: Text {
            id: caption
            text: control.text
            color: "#eeeeef"
            font.family: sfText.name
            font.pixelSize: 13
            verticalAlignment: Text.AlignVCenter
            rightPadding: 48
            elide: Text.ElideRight
        }
    }

    property real capsuleTop: 3
    property real capsuleWidth: 92
    property real capsuleHeight: 26
    readonly property bool expandedBody: expanded && entered
    property bool expanded: false
    property bool entered: false
    Component.onCompleted: Qt.callLater(() => entered = true)
    signal pointerChanged(bool inside)
    property int page: 0
    readonly property int bodyHeight: 236
    readonly property var notices: {
        const entries = []
        for (const list of [NotifService.appGroupsList, NotifService.systemGroupsList])
            for (const group of list)
                for (const item of group.items) entries.push(item)
        return entries
    }
    function selectPage(index) {
        if (page === index) return
        page = index
        pageArrival.restart()
    }
    property var selectedHour: null
    readonly property int displayedCode: selectedHour?.code ?? WeatherState.weatherCode
    readonly property bool displayedDay: selectedHour?.isDay ?? WeatherState.isDay
    signal dismissed()
    // Some controls retain hover state until Wayland sends a new enter event.
    // Check the actual pointer only while the panel is open.
    Timer {
        interval: 280
        running: panel.expanded && panel.entered
        repeat: true
        onTriggered: cursorCheck.running = true
    }
    Process {
        id: cursorCheck
        command: ["hyprctl", "cursorpos", "-j"]
        stdout: StdioCollector {
            onStreamFinished: {
                const monitor = Hyprland.monitorFor(panel.output)?.lastIpcObject
                if (!monitor || !panel.expanded) return
                let point
                try { point = JSON.parse(text) } catch (_) { return }
                const x = point.x - monitor.x - (panel.output.width - body.width) / 2
                const y = point.y - monitor.y - panel.capsuleTop
                if (x < 0 || x > body.width || y < -8 || y > body.height)
                    panel.dismissed()
            }
        }
    }
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
        color: "#ff000000"
        border.width: 1
        border.color: "#32ffffff"
        Behavior on width { NumberAnimation { duration: ShellMotion.fade(); easing.type: Easing.OutCubic } }
        Behavior on height { NumberAnimation { duration: ShellMotion.fade(); easing.type: Easing.OutCubic } }
        HoverHandler { id: dashboardHover; onHoveredChanged: panel.pointerChanged(hovered) }

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
                        model: [qsTr('Dashboard'), qsTr('Weather'), qsTr('Performance'), qsTr('Media'), qsTr('Notifications'), qsTr('Camera')]
                        delegate: IslandButton {
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
                            contentItem: Text { font.family: sfText.name;
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

            Item {
                id: pageFrame
                Layout.fillWidth: true
                Layout.fillHeight: true
                Loader {
                    id: pageContent
                    width: Math.max(1050,pageFrame.width)
                    scale: Math.min(1,pageFrame.width / width)
                    height: pageFrame.height / scale
                    transformOrigin: Item.TopLeft
                    sourceComponent: [overview, forecast, performance, media, notifications, cameraFull][panel.page]
                    NumberAnimation on opacity {
                        id: pageArrival
                        from: .35; to: 1
                        duration: ShellMotion.fade()
                        easing.type: Easing.OutCubic
                    }
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

    function clockText(seconds) {
        const value = Math.max(0, Math.floor(seconds))
        return Math.floor(value / 60) + ":" + String(value % 60).padStart(2, "0")
    }

    component SectionCard: Rectangle {
        radius: 14
        color: "#151515"
        border.color: "#24ffffff"
    }

    Component {
        id: media
        RowLayout {
            spacing: 22
            ClippingRectangle {
                Layout.preferredWidth: 116; Layout.preferredHeight: 116
                radius: 16; color: "#202020"
                Image {
                    anchors.fill: parent
                    source: MprisState.artUrl
                    fillMode: Image.PreserveAspectCrop
                    asynchronous: true
                }
                Text { font.family: sfText.name; anchors.centerIn: parent; visible: !MprisState.artUrl; text: "♫"; color: "#aaa"; font.pixelSize: 34 }
            }
            ColumnLayout {
                Layout.preferredWidth: 240
                Layout.alignment: Qt.AlignVCenter
                spacing: 7
                Text { font.family: sfText.name; Layout.fillWidth: true; text: MprisState.trackTitle || qsTr("Nothing playing"); color: "white"; font.pixelSize: 16; font.weight: Font.DemiBold; elide: Text.ElideRight }
                Text { font.family: sfText.name; Layout.fillWidth: true; text: MprisState.trackArtist || MprisState.identity; color: "#a6a6ac"; font.pixelSize: 12; elide: Text.ElideRight }
                Text { font.family: sfText.name; Layout.fillWidth: true; text: MprisState.trackAlbum; color: "#818188"; font.pixelSize: 11; elide: Text.ElideRight }
            }
            ColumnLayout {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: 10
                RowLayout {
                    Layout.alignment: Qt.AlignHCenter
                    spacing: 18
                    IslandButton { text: "‹"; enabled: MprisState.canGoPrevious; onClicked: MprisState.previous() }
                    IslandButton { text: MprisState.isPlaying ? "Ⅱ" : "▶"; enabled: MprisState.canTogglePlaying; onClicked: MprisState.togglePlaying() }
                    IslandButton { text: "›"; enabled: MprisState.canGoNext; onClicked: MprisState.next() }
                }
                TahoeSlider {
                    Layout.fillWidth: true
                    enabled: MprisState.canSeek
                    from: 0; to: Math.max(1, MprisState.length); value: MprisState.position
                    fillColor: "#ededf2"; onMoved: MprisState.seek(value)
                    Accessible.name: qsTr("Playback position")
                }
                RowLayout {
                    Text { font.family: sfText.name; text: panel.clockText(MprisState.position); color: "#99999f"; font.pixelSize: 11 }
                    Item { Layout.fillWidth: true }
                    Text { font.family: sfText.name; text: panel.clockText(MprisState.length); color: "#99999f"; font.pixelSize: 11 }
                }
                Component.onCompleted: MprisState.watchPosition(true)
                Component.onDestruction: MprisState.watchPosition(false)
            }
            SectionCard {
                Layout.preferredWidth: 190; Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 15
                    Text { font.family: sfText.name; text: qsTr("Now playing"); color: "#99999f"; font.pixelSize: 11 }
                    Text { font.family: sfText.name; Layout.fillWidth: true; text: MprisState.identity || qsTr("No player"); color: "white"; elide: Text.ElideRight; font.pixelSize: 14 }
                    Item { Layout.fillHeight: true }
                    IslandButton { text: qsTr("Sound settings"); onClicked: SettingsLauncher.open("sound") }
                }
            }
        }
    }

    Component {
        id: notifications
        ColumnLayout {
            RowLayout {
                Label { font.family: sfText.name; text: qsTr("Recent notifications"); color: "white"; Layout.fillWidth: true }
                IslandSwitch {
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
                        Label { font.family: sfText.name;
                            Layout.fillWidth: true
                            text: (modelData.appName || "") + "  ·  " + (modelData.summary || "")
                            textFormat: Text.PlainText
                            elide: Text.ElideRight; color: "white"
                        }
                        IslandButton {
                            text: qsTr("Dismiss")
                            onClicked: NotifService.removeFromCenter(modelData)
                        }
                    }
                }
                Label { font.family: sfText.name; anchors.centerIn: parent; visible: notificationList.count === 0; text: qsTr("No notifications"); color: "#c0ffffff" }
            }
        }
    }

    component ForecastCell: ColumnLayout {
        required property string heading
        required property int code
        required property string temperature
        property string low: ""
        property bool daytime: true
        spacing: 7
        Text { font.family: sfText.name; Layout.alignment: Qt.AlignHCenter; text: heading; color: "#b8b8c0"; font.pixelSize: 11 }
        WeatherArt {
            Layout.alignment: Qt.AlignHCenter
            Layout.preferredWidth: 38; Layout.preferredHeight: 34
            code: parent.code; daytime: parent.daytime
        }
        Text { font.family: sfText.name; Layout.alignment: Qt.AlignHCenter; text: temperature; color: "white"; font.pixelSize: 13; font.weight: Font.DemiBold }
        Text { font.family: sfText.name; Layout.alignment: Qt.AlignHCenter; text: low; visible: !!low; color: "#888890"; font.pixelSize: 11 }
    }

    Component {
        id: forecast
        RowLayout {
            spacing: 24
            ColumnLayout {
                Layout.preferredWidth: 240
                spacing: 7
                Text { font.family: sfText.name;
                    Layout.fillWidth: true
                    text: IslandConfig.s("dashboardWeatherLocation") ? WeatherState.city : qsTr("Weather")
                    color: "#d0d0d6"; font.pixelSize: 12; elide: Text.ElideRight
                }
                RowLayout {
                    WeatherArt {
                        Layout.preferredWidth: 74; Layout.preferredHeight: 78
                        code: panel.displayedCode; daytime: panel.displayedDay
                    }
                    Text { font.family: sfText.name; text: WeatherState.available ? Math.round(panel.selectedHour?.temp ?? WeatherState.tempC)+"°" : "—°"; color: "white"; font.pixelSize: 48; font.weight: Font.Light }
                }
                Text { font.family: sfText.name; text: WeatherState.available ? panel.condition(panel.displayedCode) : qsTr("Weather unavailable"); color: "#c5c5cd"; font.pixelSize: 12 }
                Text { font.family: sfText.name; text: qsTr("Feels like")+" "+Math.round(WeatherState.feelsLikeC)+"°"; visible: WeatherState.available; color: "#9d9da7"; font.pixelSize: 11 }
                Text { font.family: sfText.name; text: Math.round(WeatherState.windSpeed)+" km/h · "+WeatherState.humidity+"%"; visible: WeatherState.available; color: "#9d9da7"; font.pixelSize: 11 }
            }
            Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: "#25ffffff" }
            ColumnLayout {
                Layout.fillWidth: true
                Text { font.family: sfText.name; text: qsTr("Hourly forecast"); color: "#aaaab3"; font.pixelSize: 11 }
                RowLayout {
                    Layout.fillWidth: true
                    Repeater {
                        model: WeatherState.hourly.slice(0,6)
                        delegate: ForecastCell {
                            required property var modelData
                            Layout.fillWidth: true
                            heading: modelData.time.split("T")[1]
                            code: modelData.code; daytime: modelData.isDay
                            temperature: modelData.temp+"°"
                            TapHandler { onTapped: panel.selectedHour=panel.selectedHour===modelData ? null:modelData }
                        }
                    }
                }
            }
            Rectangle { Layout.preferredWidth: 1; Layout.fillHeight: true; color: "#25ffffff" }
            ColumnLayout {
                Layout.fillWidth: true
                Text { font.family: sfText.name; text: qsTr("This week"); color: "#aaaab3"; font.pixelSize: 11 }
                RowLayout {
                    Layout.fillWidth: true
                    Repeater {
                        model: WeatherState.forecast.slice(0,7)
                        delegate: ForecastCell {
                            required property var modelData
                            Layout.fillWidth: true
                            heading: Qt.formatDate(new Date(modelData.date+"T12:00:00"),"ddd")
                            code: modelData.code
                            temperature: modelData.tempMax+"°"
                            low: modelData.tempMin+"°"
                        }
                    }
                }
            }
        }
    }

    Component {
        id: cameraFull
        RowLayout {
            spacing: 18
            SectionCard {
                Layout.preferredWidth: 230; Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 18
                    Text { font.family: sfText.name; text: qsTr("Camera preview"); color: "white"; font.pixelSize: 17; font.weight: Font.DemiBold }
                    Text { font.family: sfText.name; Layout.fillWidth: true; text: qsTr("See yourself in the island"); color: "#a0a0aa"; wrapMode: Text.WordWrap; font.pixelSize: 12 }
                    Item { Layout.fillHeight: true }
                    IslandSwitch {
                        text: qsTr("Profile preview")
                        checked: IslandConfig.s("dashboardCamera")
                        onToggled: IslandConfig.setStyle("dashboardCamera",checked)
                    }
                }
            }
            Loader { Layout.fillWidth: true; Layout.fillHeight: true; sourceComponent: cameraPage }
            SectionCard {
                Layout.preferredWidth: 220; Layout.fillHeight: true
                ColumnLayout {
                    anchors.fill: parent; anchors.margins: 18
                    Text { font.family: sfText.name; text: qsTr("Privacy"); color: "white"; font.pixelSize: 15 }
                    Text { font.family: sfText.name; Layout.fillWidth: true; text: qsTr("Camera starts when you open the preview and stops when you leave this page."); color: "#a0a0aa"; wrapMode: Text.WordWrap; font.pixelSize: 12 }
                    Item { Layout.fillHeight: true }
                    IslandButton { text: qsTr("Privacy settings"); onClicked: SettingsLauncher.open("privacy-indicators") }
                }
            }
        }
    }

    Component {
        id: cameraPage
        Item {
            id: cameraTile
            property bool requested: false
            IslandButton {
                anchors.centerIn: parent
                visible: !cameraTile.requested
                text: qsTr('Open camera')
                onClicked: cameraTile.requested = true
            }
            Loader {
                anchors.centerIn: parent
                width: Math.min(280,parent.width); height: Math.max(90,parent.height)
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
                    Text { font.family: sfText.name;
                        Layout.fillWidth: true
                        visible: devices.videoInputs.length === 0 || camera.error !== Camera.NoError
                        text: devices.videoInputs.length ? camera.errorString : qsTr('No camera found')
                        wrapMode: Text.WordWrap
                        color: Theme.textPrimary
                    }
                    IslandButton {
                        Layout.fillWidth: true
                        text: qsTr('Turn off')
                        onClicked: cameraTile.requested = false
                    }
                }
            }
        }
    }
}
