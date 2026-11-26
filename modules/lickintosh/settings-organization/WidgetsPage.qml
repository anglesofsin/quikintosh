import QtQuick
import Quickshell
import QtQuick.Layouts
import qs.components
import qs.services
import qs.settingsapp
import qs.ui.settings.widgets
ContentPage {
 id:root
 SettingsCard{title:I18n.tr('Desktop Widgets')
  SettingsRow{label:I18n.tr('Show Widgets');kind:'switch';checked:WidgetState.showDesktopWidgets;onToggled:value=>WidgetState.showDesktopWidgets=value}
  SettingsRow{label:I18n.tr('Appearance');kind:'choice';choices:['Automatic','Default','Dark','Clear','Tinted','Transparent'];selection:['auto','color','dark','clear','tinted','transparent'].indexOf(WidgetState.widgetStyle);onPicked:index=>WidgetState.widgetStyle=['auto','color','dark','clear','tinted','transparent'][index]}
  SettingsRow{label:I18n.tr('Surface');kind:'choice';choices:['Liquid Glass','Solid','Transparent'];selection:['glass','solid','transparent'].indexOf(WidgetState.widgetMaterial);onPicked:index=>WidgetState.widgetMaterial=['glass','solid','transparent'][index]}
  SettingsRow{label:I18n.tr('Dim Widgets Behind Windows');kind:'switch';checked:WidgetState.dimWidgets;onToggled:value=>WidgetState.dimWidgets=value}
  SettingsRow{label:I18n.tr('Free Placement with Control');kind:'switch';checked:WidgetState.allowCtrlFreePlacement;onToggled:value=>WidgetState.allowCtrlFreePlacement=value}
  SettingsRow{label:I18n.tr('Avoid Desktop Icons');kind:'switch';checked:WidgetState.avoidDesktopIcons;onToggled:value=>WidgetState.avoidDesktopIcons=value;separator:false}
 }
 SettingsCard{title:I18n.tr('Widget Gallery')
  SettingsRow{label:I18n.tr('Desktop Widgets');kind:'button';buttonText:I18n.tr('Edit Widgets…');onActivated:Quickshell.execDetached(['quickintosh','ipc','call','rice','widgetGallery','desktop'])}
  SettingsRow{label:I18n.tr('Notification Center');kind:'button';buttonText:I18n.tr('Edit Widgets…');onActivated:Quickshell.execDetached(['quickintosh','ipc','call','rice','widgetGallery','notifCenter']);separator:false}
 }
 SettingsCard{title:I18n.tr('Personalization')
  SettingsRow{label:I18n.tr('Weather');kind:'navigate';onActivated:SettingsLauncher.open('weather')}
  SettingsRow{label:I18n.tr('Appearance');kind:'navigate';onActivated:SettingsLauncher.open('appearance');separator:false}
 }
}
