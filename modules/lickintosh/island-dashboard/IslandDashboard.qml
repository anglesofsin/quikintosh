import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.rosa.services
import qs.ui.topbar.notch

PanelWindow {
    id: panel
    required property var output
    screen: output
    anchors.top: true
    margins.top: 38
    implicitWidth: Math.min(output.width - 24, 1120)
    implicitHeight: page === 1 ? 360 : 280
    exclusiveZone: -1
    color: 'transparent'
    WlrLayershell.namespace: 'quickintosh-island-dashboard'
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand

    property int page: 0
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

    readonly property string weatherArt: {
        const kind = WeatherState._kindFor(panel.displayedCode, panel.displayedDay)
        if (kind === 'storm') return 'storm'
        if (kind === 'rain') return 'rain'
        if (kind === 'sun' || kind === 'partly') return 'clear'
        return 'clouds'
    }

    Rectangle {
        anchors.fill: parent
        radius: 26
        color: Theme.isLight ? '#c9f1f4f8' : '#d0141822'
        border.color: '#35ffffff'
        clip: true

        Image {
            anchors.fill: parent
            visible: panel.page === 1 && WeatherState.available && IslandConfig.s('dashboardWeatherArt')
            source: visible ? Qt.resolvedUrl('assets/' + panel.weatherArt + '.webp') : ''
            fillMode: Image.PreserveAspectCrop
            asynchronous: true
            opacity: .8
        }
        Rectangle {
            anchors.fill: parent
            radius: 26
            visible: panel.page === 1
            gradient: Gradient {
                GradientStop { position: 0; color: '#40202737' }
                GradientStop { position: 1; color: '#bb0a111e' }
            }
        }

        Repeater {
            model: panel.page === 1 && IslandConfig.s('dashboardWeatherArt') && WeatherState.available
                   && (panel.weatherArt === 'rain' || panel.weatherArt === 'storm') ? 18 : 0
            delegate: Rectangle {
                required property int index
                width: 2; height: 7 + index % 6
                radius: width / 2
                color: '#53dceaff'
                x: parent.width * ((index * 37) % 101) / 101
                rotation: 14
                NumberAnimation on y {
                    from: -20
                    to: panel.height + 20
                    duration: 740 + index * 83
                    loops: Animation.Infinite
                    running: panel.visible
                }
            }
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 18
            spacing: 12

            RowLayout {
                Repeater {
                    model: [qsTr('Dashboard'), qsTr('Weather')]
                    delegate: Button {
                        required property string modelData
                        required property int index
                        text: modelData
                        checkable: true
                        checked: panel.page === index
                        onClicked: panel.page = index
                    }
                }
                Item { Layout.fillWidth: true }
                Button { text: '×'; Accessible.name: qsTr('Close dashboard'); onClicked: panel.dismissed() }
            }

            Loader {
                Layout.fillWidth: true
                Layout.fillHeight: true
                sourceComponent: panel.page === 1 ? forecast : overview
            }
        }
    }

    Component {
        id: overview
        NotchDashboard {
            profileModule: IslandConfig.s('dashboardCamera') ? cameraPage : null
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
