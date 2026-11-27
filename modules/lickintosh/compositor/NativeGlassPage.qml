import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import qs.components
import qs.services
import qs.settingsapp
ScrollView {
 id:root
 clip:true;contentWidth:availableWidth;contentHeight:body.implicitHeight
 ScrollBar.horizontal.policy:ScrollBar.AlwaysOff
 leftPadding:16;rightPadding:16;topPadding:8;bottomPadding:20
 readonly property string prefix:'native-glass:'
 readonly property var data:SettingsState.data['native-glass'] || ({})
 property string target:'windows'
 property string tab:'Material'
 readonly property var targets:data.targets || [{id:'windows',label:'Application windows'}]
 readonly property var selected:targets.find(t=>t.id===target) || targets[0]
 readonly property var presets:['Tahoe','Clear','Subtle','Glass','High Contrast','Default']
 readonly property var presetKeys:['pomme','clear','subtle','glass','high_contrast','default']
 function key(field){return prefix+target+':'+field}
 function value(field,fallback){const v=SettingsPreferences.inputOverrides[key(field)];return v!==undefined ? v:fallback}
 function has(field){return SettingsPreferences.inputOverrides[key(field)]!==undefined}
 function set(field,value){SettingsPreferences.input(key(field),value)}
 function global(key,value){SettingsPreferences.input(key,value)}
 function current(key,fallback){return SettingsPreferences.inputOverrides[key] ?? data.values?.[key] ?? fallback}
 function refresh(){SettingsState.query('native-glass',true)}
 function reset(all){const next=Object.assign({},SettingsPreferences.inputOverrides);for(const k of Object.keys(next)){if(k.startsWith(all ? prefix:prefix+target+':') || (all && k.startsWith('plugin:hyprglass:')))delete next[k]}if(all){Object.assign(next,{'plugin:hyprglass:windows:background_cache':false,'plugin:hyprglass:windows:live_resample':true,'plugin:hyprglass:windows:live_resample_fps':0,'plugin:hyprglass:layers:enabled':true,'plugin:hyprglass:layers:live_resample_fps':0,'plugin:hyprglass:enabled':true})}SettingsPreferences.inputOverrides=next;if(all){RenderingState.applyPreset('native');ShellConfig.options.performance.glassEnabled=true}refreshDelay.restart()}
 function rgba(value){const n=Number(value);return Qt.rgba(Math.floor(n/16777216)%256/255,Math.floor(n/65536)%256/255,Math.floor(n/256)%256/255,n%256/255)}
 readonly property bool customized:Object.keys(SettingsPreferences.inputOverrides).some(k=>k.startsWith(prefix+target+':'))
 Component.onCompleted:refresh()
 Connections{target:SettingsState;function onReadyChanged(){if(SettingsState.ready)root.refresh()}}
 Timer{id:refreshDelay;interval:650;onTriggered:root.refresh()}
 ColorDialog {
  id:tint;title:I18n.tr('Glass tint');options:ColorDialog.ShowAlphaChannel
  selectedColor:root.rgba(root.value('tint_color',Theme.isLight ? 0xffffff6a:0x1a1a1a4a))
  onAccepted:root.set('tint_color',Math.round(selectedColor.r*255)*16777216+Math.round(selectedColor.g*255)*65536+Math.round(selectedColor.b*255)*256+Math.round(selectedColor.a*255))
 }
 ColumnLayout {
  id:body;width:root.availableWidth;spacing:18
  SettingsCard {
   SettingsRow{label:I18n.tr('Liquid Glass');kind:'switch';checked:RenderingState.options.glassEnabled;onToggled:value=>{ShellConfig.options.performance.glassEnabled=value;SettingsPreferences.input(root.prefix+'windows:enabled',value);root.global('plugin:hyprglass:enabled',value);root.global('plugin:hyprglass:layers:enabled',value)}}
   SettingsRow{label:I18n.tr('Surface');kind:'choice';choices:root.targets.map(t=>I18n.tr(t.label));selection:Math.max(0,root.targets.findIndex(t=>t.id===root.target));onPicked:index=>root.target=root.targets[index].id;separator:false}
  }
  RowLayout {
   Text{Layout.fillWidth:true;text:I18n.tr(root.selected.label);font.family:'SF Pro Display';font.pixelSize:19;font.weight:Font.DemiBold;color:Theme.textPrimary}
   TahoeButton{text:'↶';implicitWidth:32;enabled:root.customized;onClicked:root.reset(false);Accessible.name:I18n.tr('Restore this surface')}
  }
  SettingsCard {
   SettingsRow{label:I18n.tr('Glass effect');kind:'switch';checked:root.value('enabled',true);onToggled:value=>root.set('enabled',value)}
   SettingsRow{label:I18n.tr('Material');kind:'choice';choices:root.presets.map(p=>I18n.tr(p));selection:Math.max(0,root.presetKeys.indexOf(root.value('preset','pomme')));onPicked:index=>root.set('preset',root.presetKeys[index]);separator:false}
  }
  Rectangle {
   Layout.fillWidth:true;implicitHeight:36;radius:10;color:Theme.isLight ? '#10000000':'#12ffffff'
   RowLayout{anchors.fill:parent;anchors.margins:3;spacing:3
    Repeater{model:['Material','Edges','Color','Performance']
     AbstractButton{id:tabButton;required property string modelData;Layout.fillWidth:true;Layout.fillHeight:true
      contentItem:Text{text:I18n.tr(modelData);font.family:'SF Pro Text';font.pixelSize:12;font.weight:root.tab===modelData ? Font.DemiBold:Font.Normal;color:Theme.textPrimary;horizontalAlignment:Text.AlignHCenter;verticalAlignment:Text.AlignVCenter}
      background:Rectangle{radius:8;color:root.tab===tabButton.modelData ? (Theme.isLight ? '#ffffff':'#505054'):'transparent'}
      onClicked:root.tab=modelData
     }
    }
   }
  }
  SettingsCard {
   visible:root.tab!=='Performance'
   Repeater {model:(root.data.fields || []).filter(f=>f.group===root.tab)
    SettingsRow{required property var modelData;readonly property var field:modelData
     label:I18n.tr(field.label);kind:'slider';minimum:field.min;maximum:field.max;step:field.step
     number:Number(root.value(field.key,field.key==='blur_strength' && root.target==='dock' ? .65:field.default))
     value:root.has(field.key) ? number.toFixed(step<1 ? 2:0):I18n.tr('Preset')
     onCommitted:value=>root.set(field.key,value)
    }
   }
   SettingsRow{visible:root.tab==='Color';label:I18n.tr('Tint color');kind:'button';buttonText:root.has('tint_color') ? '#'+Number(root.value('tint_color',0)).toString(16).padStart(8,'0').toUpperCase():I18n.tr('Preset');onActivated:tint.open();separator:false}
  }
  SettingsCard {
   visible:root.tab==='Performance'
   title:I18n.tr('Live background')
   SettingsRow{label:I18n.tr('Update background in real time');kind:'switch';checked:root.value('live_resample',true);onToggled:value=>{root.set('live_resample',value);if(root.target==='windows')root.global('plugin:hyprglass:windows:background_cache',!value)}}
   SettingsRow{label:I18n.tr('Cache static window backgrounds');visible:root.target==='windows';kind:'switch';checked:root.current('plugin:hyprglass:windows:background_cache',false);onToggled:value=>root.global('plugin:hyprglass:windows:background_cache',value)}
   SettingsRow{label:I18n.tr(root.target==='windows' ? 'Window background frame limit':'Panel background frame limit (shared)');kind:'choice';choices:[I18n.tr('Unlimited'),'15 FPS','30 FPS','60 FPS','120 FPS','144 FPS','240 FPS','360 FPS'];selection:Math.max(0,[0,15,30,60,120,144,240,360].indexOf(root.current(root.target==='windows' ? 'plugin:hyprglass:windows:live_resample_fps':'plugin:hyprglass:layers:live_resample_fps',0)));onPicked:index=>root.global(root.target==='windows' ? 'plugin:hyprglass:windows:live_resample_fps':'plugin:hyprglass:layers:live_resample_fps',[0,15,30,60,120,144,240,360][index]);separator:false}
  }
  SettingsCard {
   visible:root.tab==='Performance'
   title:I18n.tr('Shell rendering')
   SettingsRow{label:I18n.tr('Interface frame limit');kind:'choice';choices:[I18n.tr('Unlimited'),'30 FPS','60 FPS','120 FPS','144 FPS','240 FPS'];selection:Math.max(0,[0,30,60,120,144,240].indexOf(RenderingState.maximumFps));onPicked:index=>RenderingState.set('maximumFps',[0,30,60,120,144,240][index])}
   SettingsRow{label:I18n.tr('Client glass frame limit');kind:'choice';choices:[I18n.tr('Unlimited'),'15 FPS','30 FPS','60 FPS','120 FPS','144 FPS','240 FPS'];selection:Math.max(0,[0,15,30,60,120,144,240].indexOf(RenderingState.glassFps));onPicked:index=>RenderingState.set('glassFps',[0,15,30,60,120,144,240][index])}
   SettingsRow{label:I18n.tr('Prepare panels before opening');kind:'switch';checked:RenderingState.prewarm;onToggled:value=>RenderingState.set('prewarm',value)}
   SettingsRow{label:I18n.tr('Blur');kind:'switch';checked:RenderingState.blurEnabled;onToggled:value=>RenderingState.set('blurEnabled',value)}
   SettingsRow{label:I18n.tr('Shadows');kind:'switch';checked:RenderingState.shadows;onToggled:value=>RenderingState.set('shadows',value);separator:false}
  }
  SettingsCard {
   SettingsRow{label:I18n.tr('Application-specific rules');kind:'navigate';onActivated:SettingsLauncher.open('compositor')}
   SettingsRow{label:I18n.tr('Restore Liquid Glass defaults');kind:'button';buttonText:'↶ '+I18n.tr('Restore');onActivated:root.reset(true);separator:false}
  }
 }
}
