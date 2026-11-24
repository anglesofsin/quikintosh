import QtQuick
import QtQuick.Layouts
import qs.services
import qs.components
import qs.settingsapp
import qs.ui.settings.widgets
ColumnLayout {
 id:root
 Layout.fillWidth:true
 spacing:20
 SettingsCard{title:'Appearance'
  SettingsRow{label:'Appearance';kind:'choice';choices:['Light','Dark','Automatic'];selection:SettingsPreferences.profile.autoAppearance ? 2:Theme.isLight ? 0:1;onPicked:index=>{SettingsPreferences.profile.autoAppearance=index===2;if(index!==2)Theme.setMode(index===0 ? 'light':'dark')}}
  SettingsRow{label:'Accent color';kind:'choice';choices:['Wallpaper','Custom'];selection:ShellConfig.options.appearance.accentMode==='auto' ? 0:1;separator:false;onPicked:index=>ShellConfig.options.appearance.accentMode=index===0 ? 'auto':'manual'}
  ColorSetting{visible:ShellConfig.options.appearance.accentMode==='manual';label:'Custom accent';value:Theme.accent;onPicked:value=>Theme.setAccent(String(value))}
 }
 SettingsCard{title:'Icons & Widgets'
  SettingsRow{label:'Style';kind:'choice';choices:['Automatic','Full Color','Clear','Tinted'];selection:['auto','color','clear','tinted'].indexOf(WidgetState.widgetStyle);onPicked:index=>{WidgetState.widgetStyle=['auto','color','clear','tinted'][index];ShellConfig.options.appearance.iconStyle=index===3 ? 'tinted':'color'}}
  SettingsRow{visible:AppearanceState.tinted;label:'Tint color';kind:'choice';choices:['Wallpaper','Custom'];selection:ShellConfig.options.appearance.iconTintMode==='auto' ? 0:1;separator:false;onPicked:index=>ShellConfig.options.appearance.iconTintMode=index===0 ? 'auto':'manual'}
  ColorSetting{visible:AppearanceState.tinted && ShellConfig.options.appearance.iconTintMode==='manual';label:'Custom tint';value:ShellConfig.options.appearance.iconTintColor;onPicked:value=>ShellConfig.options.appearance.iconTintColor=String(value)}
 }
 SettingsCard{title:'Liquid Glass'
  SettingsRow{label:'Appearance';kind:'choice';choices:['Clear','Tinted'];selection:Theme.glassValue('*','tintAlpha')>.45 ? 1:0;separator:false;onPicked:index=>{Theme.setGlassParam('*','tintAlpha',index===1 ? .62:.12)}}
 }
}
