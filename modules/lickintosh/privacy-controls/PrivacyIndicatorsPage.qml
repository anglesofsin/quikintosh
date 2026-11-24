import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.components
import qs.settingsapp
import qs.ui.settings.widgets
ScrollView{
 id:root
 property string selectedKind:'all'
 property string appName:''
 readonly property var kinds:['all'].concat(PrivacyPreferences.kinds)
 readonly property var knownApps:Array.from(new Set(MediaCaptureState.detected.map(e=>e.app).concat(PrivacyPreferences.exceptions.map(e=>e.app)))).sort()
 contentWidth:availableWidth;contentHeight:content.implicitHeight+36;clip:true
 ScrollBar.horizontal.policy:ScrollBar.AlwaysOff
 ColumnLayout{
  id:content;x:24;y:12;width:root.availableWidth-48;spacing:22
  SettingsCard{title:'Privacy Indicators'
   SettingsRow{label:'Show privacy indicators';kind:'switch';checked:PrivacyPreferences.enabled;onToggled:value=>PrivacyPreferences.enabled=value}
   SettingsRow{label:'Dynamic Island';kind:'switch';checked:PrivacyPreferences.island;onToggled:value=>PrivacyPreferences.island=value}
   SettingsRow{label:'Control Center';kind:'switch';checked:PrivacyPreferences.controlCenter;onToggled:value=>PrivacyPreferences.controlCenter=value}
   SettingsRow{label:'Hide indicator in full screen';kind:'switch';checked:PrivacyPreferences.hideFullscreen;onToggled:value=>PrivacyPreferences.hideFullscreen=value}
   SettingsRow{label:'Show while Dynamic Island is expanded';kind:'switch';checked:PrivacyPreferences.showExpanded;separator:false;onToggled:value=>PrivacyPreferences.showExpanded=value}
  }
  Repeater{model:PrivacyPreferences.kinds
   delegate:SettingsCard{
    id:category;required property string modelData
    readonly property var options:PrivacyPreferences.category(modelData)
    title:PrivacyPreferences.titles[modelData]
    SettingsRow{label:'Show indicator';kind:'switch';checked:category.options.enabled;onToggled:value=>PrivacyPreferences.setCategory(category.modelData,'enabled',value)}
    ColorSetting{label:'Indicator color';value:category.options.color;onPicked:value=>PrivacyPreferences.setCategory(category.modelData,'color',String(value))}
    SettingsRow{label:'Priority';kind:'choice';choices:['1 — Highest','2','3','4 — Lowest'];selection:category.options.priority;separator:false;onPicked:index=>PrivacyPreferences.setCategory(category.modelData,'priority',index)}
   }
  }
  SettingsCard{title:'Current Access';visible:MediaCaptureState.detected.length>0
   Repeater{model:MediaCaptureState.detected;delegate:SettingsRow{
    required property var modelData;required property int index
    label:modelData.app;value:PrivacyPreferences.titles[modelData.kind];kind:'info';separator:index<MediaCaptureState.detected.length-1
   }}
  }
  SettingsCard{title:'Application Exceptions'
   ColumnLayout{Layout.fillWidth:true;spacing:12;Layout.topMargin:8;Layout.bottomMargin:12
    TahoeCombo{Layout.fillWidth:true;visible:root.knownApps.length>0;model:['Choose an application…'].concat(root.knownApps);onActivated:index=>{if(index>0){root.appName=root.knownApps[index-1];application.text=root.appName}}}
    TahoeField{id:application;Layout.fillWidth:true;placeholderText:'Application name or process';selectByMouse:true;onTextEdited:root.appName=text}
    RowLayout{Layout.fillWidth:true;spacing:12
     TahoeCombo{Layout.fillWidth:true;model:['All access types'].concat(PrivacyPreferences.kinds.map(kind=>PrivacyPreferences.titles[kind]));onActivated:index=>root.selectedKind=root.kinds[index]}
     TahoeButton{text:'Add Exception';enabled:!!root.appName.trim();onClicked:{const name=root.appName.trim();PrivacyPreferences.setRule(name.toLowerCase(),name,root.selectedKind,'hide');application.text='';root.appName=''}}
    }
   }
   Repeater{model:PrivacyPreferences.exceptions;delegate:SettingsRow{
    required property var modelData;required property int index
    label:modelData.app;description:modelData.kind==='all' ? 'All access types':PrivacyPreferences.titles[modelData.kind]
    kind:'choice';choices:['Follow category','Always show','Hide'];selection:modelData.mode==='show' ? 1:2;separator:index<PrivacyPreferences.exceptions.length-1
    onPicked:index=>PrivacyPreferences.setRule(modelData.id,modelData.app,modelData.kind,['default','show','hide'][index])
   }}
  }
 }
}
