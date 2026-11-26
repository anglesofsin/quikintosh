import QtQuick
import qs.services
import qs.components
import qs.settingsapp
import qs.ui.settings.widgets
ContentPage {
 id:root
 readonly property var cfg:ShellConfig.options.capture
 SettingsCard{title:I18n.tr('Screenshots')
  SettingsRow{label:'Save a PNG automatically when copying';kind:'switch';checked:root.cfg.autoSave;onToggled:value=>root.cfg.autoSave=value}
  SettingsPathRow{label:'Save location';path:root.cfg.directory;onEdited:value=>root.cfg.directory=value}
  SettingsRow{label:'File name';kind:'field';value:root.cfg.filenameTemplate;onEdited:value=>root.cfg.filenameTemplate=value}
  SettingsRow{label:'Fullscreen feedback';kind:'choice';choices:['Flash and notification','Flash only','Off'];selection:['notification','flash','off'].indexOf(root.cfg.feedback);onPicked:index=>root.cfg.feedback=['notification','flash','off'][index]}
  SettingsRow{label:'Show pixel magnifier';kind:'switch';checked:root.cfg.magnifier;onToggled:value=>root.cfg.magnifier=value;separator:false}
 }
 SettingsCard{title:I18n.tr('Screen Recording')
  SettingsPathRow{label:'Recording location';path:root.cfg.videoDirectory;onEdited:value=>root.cfg.videoDirectory=value}
  SettingsRow{label:'Record system audio';kind:'switch';checked:root.cfg.recordSystemAudio;onToggled:value=>root.cfg.recordSystemAudio=value}
  SettingsRow{label:'Record microphone';kind:'switch';checked:root.cfg.recordMic;onToggled:value=>root.cfg.recordMic=value}
  SettingsRow{label:'Show cursor in recordings';kind:'switch';checked:root.cfg.recordCursor;onToggled:value=>root.cfg.recordCursor=value}
  SettingsRow{label:'Maximum duration';kind:'slider';minimum:3;maximum:3600;step:1;number:root.cfg.recordMaxSeconds;value:Math.round(root.cfg.recordMaxSeconds)+' s';onCommitted:value=>root.cfg.recordMaxSeconds=Math.round(value);separator:false}
 }
 SettingsCard{title:I18n.tr('Text Recognition & Translation')
  SettingsRow{label:'Recognition languages';kind:'field';value:root.cfg.ocrLanguages;onEdited:value=>root.cfg.ocrLanguages=value}
  SettingsRow{label:'Translation language';kind:'field';value:root.cfg.translateLanguage;onEdited:value=>root.cfg.translateLanguage=value;separator:false}
 }
}
