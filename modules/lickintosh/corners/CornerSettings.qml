import QtQuick
import QtQuick.Layouts
import qs.services
import qs.components
import qs.settingsapp
import qs.ui.settings.widgets
SettingsCard{
 title:'Screen Corners'
 readonly property var cfg:ShellConfig.options.edges
 SettingsRow{label:'Rounded screen corners';kind:'switch';checked:cfg.roundedCorners;onToggled:value=>cfg.roundedCorners=value}
 ConfigSlider{visible:cfg.roundedCorners;text:'Radius';from:0;to:80;decimals:0;value:cfg.cornerRadius;onMoved:value=>cfg.cornerRadius=Math.round(value)}
 SettingsRow{label:'Hide corners in full screen';kind:'switch';checked:cfg.hideCornersFullscreen;separator:false;onToggled:value=>cfg.hideCornersFullscreen=value}
}
