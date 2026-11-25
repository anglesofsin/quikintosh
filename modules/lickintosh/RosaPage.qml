import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import Quickshell
import qs.services
import qs.components
import qs.ui.settings.widgets
import qs.rosa.services as Rosa

ContentPage {
    id: root
    pageTitle: "Dynamic Island"
    property string settingsFilter: ""
    property bool weatherLocationRevealed:false
    ContentSection {
        title: "Dashboard"
        Repeater {
            model: [
                {key:"dashboardEnabled", label:"Open dashboard with right click"},
                {key:"dashboardCamera", label:"Offer camera in profile tile"},
                {key:"dashboardWeatherArt", label:"Show weather backgrounds"},
                {key:"dashboardWeatherLocation", label:"Show weather location"}
            ]
            delegate: ConfigSwitch {
                required property var modelData
                text: modelData.label
                checked: Rosa.IslandConfig.s(modelData.key)
                onToggled: function(value) { Rosa.IslandConfig.setStyle(modelData.key, value) }
            }
        }
    }

    readonly property var settingsHost:QsWindow.window
    Connections {
        target:root.settingsHost
        function onVisibleChanged(){if(!root.settingsHost.visible)root.weatherLocationRevealed=false}
    }
    TextField {
        Layout.fillWidth: true
        placeholderText: "Find an option: downloads, clock, workspace, notifications…"
        onTextChanged: root.settingsFilter = text.trim().toLowerCase()
    }
    ContentSection {
        title: "Dynamic Island"
        ConfigSwitch {
            text: "Use enhanced Dynamic Island"
            checked: ShellConfig.options.topbar.islandProvider === "rosa"
            onToggled: function(v) { ShellConfig.options.topbar.islandProvider = v ? "rosa" : "classic" }
        }
        ConfigSwitch {
            text: "Show the island"
            checked: ShellConfig.options.topbar.notchVisible && Rosa.IslandConfig.s("enabled")
            onToggled: function(v) { ShellConfig.options.topbar.notchVisible=v; Rosa.IslandConfig.setStyle("enabled",v) }
        }
        ConfigSwitch {
            text: "Island sound effects"
            checked: Rosa.Prefs.sfxEnabled
            onToggled: function(v) { Rosa.Prefs.set("sfxEnabled",v) }
        }
        ConfigSwitch {
            text: "Weather alerts"
            checked: Rosa.Prefs.weatherEnabled
            onToggled: function(v) { Rosa.Prefs.set("weatherEnabled",v) }
        }
        RowLayout {
            Layout.fillWidth:true
            CFText{Layout.fillWidth:true;text:"Weather location";color:Theme.textPrimary;font.pixelSize:13}
            TahoeButton {
                text:root.weatherLocationRevealed ? "Hide location":"Show location…"
                onClicked:root.weatherLocationRevealed=!root.weatherLocationRevealed
            }
        }
        TextField {
            Layout.fillWidth:true
            visible:root.weatherLocationRevealed
            placeholderText:"City or city,country"
            text:root.weatherLocationRevealed ? Rosa.Prefs.weatherPlace:""
            onEditingFinished:if(root.weatherLocationRevealed)Rosa.Prefs.set("weatherPlace",text.trim())
        }
        RowLayout {
            Button {
                text: "Restore defaults"
                onClicked: Rosa.IslandConfig.reset()
            }
            Button {
                text: "Test animations"
                onClicked: Quickshell.execDetached(["lickintosh","ipc","call","island","play","media"])
            }
            Button {
                text: "Stop preview"
                onClicked: Quickshell.execDetached(["lickintosh","ipc","call","island","play","stop"])
            }
        }
    }
    ContentSection {
        title: "Voice integration"
        CFText {
            Layout.fillWidth: true
            text: "Discord priority: Canary → PTB → Stable → Equibop. Restart each client once after installation. Other apps need to publish a PipeWire Communication role; microphone use alone is not treated as a call."
            color: Theme.textPrimary
            font.pixelSize: 12
            wrapMode: Text.WordWrap
        }
    }
    Repeater {
        model: Rosa.IslandConfig.groups
        ContentSection {
            id: group
            required property var modelData
            title: Rosa.IslandConfig.groupTitle(group.modelData.key)
            Repeater {
                model: group.modelData.names.filter(function(name){return !root.settingsFilter || Rosa.IslandConfig.optTitle(name).toLowerCase().indexOf(root.settingsFilter)>=0})
                Loader {
                    id: option
                    required property string modelData
                    readonly property var spec: Rosa.IslandConfig.spec[modelData]
                    Layout.fillWidth: true
                    Layout.preferredHeight: item ? item.implicitHeight : 0
                    sourceComponent: spec.type === "bool" ? boolControl : spec.type === "int" ? intControl : pickControl
                    Component {
                        id: boolControl
                        ConfigSwitch {
                            text: Rosa.IslandConfig.optTitle(option.modelData)
                            checked: Rosa.IslandConfig.s(option.modelData)
                            onToggled: function(v) { Rosa.IslandConfig.setStyle(option.modelData,v) }
                        }
                    }
                    Component {
                        id: intControl
                        ConfigSlider {
                            text: Rosa.IslandConfig.optTitle(option.modelData)
                            from: option.spec.min
                            to: option.spec.max
                            value: Rosa.IslandConfig.s(option.modelData)
                            onMoved: function(v) { Rosa.IslandConfig.setStyle(option.modelData,v) }
                        }
                    }
                    Component {
                        id: pickControl
                        RowLayout {
                            CFText {
                                text: Rosa.IslandConfig.optTitle(option.modelData)
                                color: Theme.textPrimary
                                font.pixelSize: 14
                                Layout.fillWidth: true
                            }
                            ComboBox {
                                model: option.spec.values.map(function(v){return option.modelData === "voiceLayout" && v === "auto" ? "Automatic (minimize beside media)" : Rosa.IslandConfig.valueTitle(v)})
                                currentIndex: option.spec.values.indexOf(Rosa.IslandConfig.s(option.modelData))
                                onActivated: function(i) { Rosa.IslandConfig.setStyle(option.modelData,option.spec.values[i]) }
                            }
                        }
                    }
                }
            }
        }
    }
}
