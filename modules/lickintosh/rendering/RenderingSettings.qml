import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.components
import qs.services
import qs.settingsapp
import qs.ui.settings.widgets
ColumnLayout {
 id:root
 Layout.fillWidth:true;spacing:20
 component FpsSetting:ColumnLayout{
  id:row
  property string label:''
  property int limit:0
  property bool custom:false
  readonly property var presets:[0,15,30,60,90,120,144,165,240,360]
  signal committed(int value)
  Layout.fillWidth:true;spacing:0
  SettingsRow{label:row.label;kind:'choice';choices:['Automatic','15','30','60','90','120','144','165','240','360','Custom'];selection:row.custom || row.presets.indexOf(row.limit)<0 ? 10:row.presets.indexOf(row.limit);onPicked:index=>{row.custom=index===10;if(!row.custom)row.committed(row.presets[index])}}
  SettingsRow{visible:row.custom || row.presets.indexOf(row.limit)<0;label:'Custom FPS';kind:'field';value:String(row.limit);onEdited:text=>{const n=Number(text);if(Number.isFinite(n) && n>=0 && n<=1000)row.committed(Math.round(n))}}
 }
 TahoeButton {
  Layout.alignment: Qt.AlignRight
  text: '↶  Restore defaults'
  Accessible.name: 'Restore rendering and motion defaults'
  onClicked: {
   RenderingState.applyPreset('native')
   RenderingState.set('renderer','auto')
   RenderingState.set('measureFrames',false)
  }
 }
 SettingsCard{title:I18n.tr('Rendering & Performance')
  SettingsRow{label:'Profile';kind:'choice';choices:['Custom','Native refresh rate','Balanced','Power saving'];selection:['custom','native','balanced','saving'].indexOf(RenderingState.profile);onPicked:index=>{if(index>0)RenderingState.applyPreset(['custom','native','balanced','saving'][index])}}
  FpsSetting{label:'Interface FPS';limit:RenderingState.maximumFps;onCommitted:value=>RenderingState.set('maximumFps',value)}
  FpsSetting{label:'Liquid Glass FPS';limit:RenderingState.glassFps;onCommitted:value=>RenderingState.set('glassFps',value)}
  FpsSetting{label:'Window motion FPS';limit:RenderingState.geometryFps;onCommitted:value=>RenderingState.set('geometryFps',value)}
  SettingsRow{label:'Keep panels prepared';kind:'switch';checked:RenderingState.prewarm;onToggled:value=>RenderingState.set('prewarm',value)}
  SettingsRow{label:'Renderer';kind:'choice';choices:['Automatic','Threaded','Basic'];selection:['auto','threaded','basic'].indexOf(RenderingState.options.renderer);onPicked:index=>RenderingState.set('renderer',['auto','threaded','basic'][index])}
  SettingsRow{visible:RenderingState.options.renderer!==(Quickshell.env('QUICKINTOSH_RENDERER') || 'auto');label:'Apply renderer';kind:'button';buttonText:'Restart shell';onActivated:Quickshell.execDetached(['rice-shell','restart'])}
 }
 SettingsCard{title:I18n.tr('Motion')
  SettingsRow{label:'Animations';kind:'switch';checked:!SettingsPreferences.accessibility.reduceMotion;onToggled:value=>SettingsPreferences.accessibility.reduceMotion=!value}
  SettingsRow{label:'Animation duration';kind:'slider';number:RenderingState.motionScale;minimum:.1;maximum:3;step:.1;value:RenderingState.motionScale.toFixed(1)+'×';onCommitted:value=>RenderingState.set('motionScale',value)}
  SettingsRow{label:'Looping effects';kind:'switch';checked:RenderingState.options.ambientAnimations;onToggled:value=>RenderingState.set('ambientAnimations',value)}
  SettingsRow{label:'Widget drag preview';kind:'choice';choices:['Live','Cached'];selection:RenderingState.options.cacheWidgetDrag ? 1:0;onPicked:index=>RenderingState.set('cacheWidgetDrag',index===1)}
  SettingsRow{label:'Dock magnification';kind:'switch';checked:ShellConfig.options.dockAppearance.magnificationEnabled;separator:false;onToggled:value=>ShellConfig.options.dockAppearance.magnificationEnabled=value}
 }
 SettingsCard{title:I18n.tr('Effects')
  SettingsRow{label:'Liquid Glass';kind:'switch';checked:RenderingState.options.glassEnabled;onToggled:value=>RenderingState.set('glassEnabled',value)}
  SettingsRow{label:'Reflect windows';kind:'switch';checked:ShellConfig.options.glass.captureWindows;available:RenderingState.glassEnabled;onToggled:value=>ShellConfig.options.glass.captureWindows=value}
  SettingsRow{label:'Glass resolution';kind:'slider';number:RenderingState.textureScale;minimum:.25;maximum:1;step:.05;value:Math.round(RenderingState.textureScale*100)+'%';available:RenderingState.glassEnabled;onCommitted:value=>RenderingState.set('textureScale',value)}
  SettingsRow{label:'Blur';kind:'switch';checked:RenderingState.blurEnabled;available:RenderingState.glassEnabled;onToggled:value=>RenderingState.set('blurEnabled',value)}
  SettingsRow{label:'Blur resolution';kind:'slider';number:RenderingState.blurScale;minimum:.25;maximum:1;step:.05;value:Math.round(RenderingState.blurScale*100)+'%';available:RenderingState.glassEnabled && RenderingState.blurEnabled;onCommitted:value=>RenderingState.set('blurScale',value)}
  SettingsRow{label:'Shadows';kind:'switch';checked:RenderingState.shadows;separator:false;onToggled:value=>RenderingState.set('shadows',value)}
 }
 SettingsCard{title:I18n.tr('Frame diagnostics')
  SettingsRow{label:'Measure rendered frames';kind:'switch';checked:RenderingState.options.measureFrames;separator:false;onToggled:value=>RenderingState.set('measureFrames',value)}
  ColumnLayout{id:metricsColumn;visible:RenderingState.options.measureFrames;Layout.fillWidth:true;spacing:4
   property var samples:[]
   Timer{interval:1000;running:metricsColumn.visible;repeat:true;triggeredOnStart:true;onTriggered:metricsColumn.samples=RenderingState.statistics().filter(row=>row.active && row.samples>5)}
   Repeater{model:metricsColumn.samples;delegate:SettingsRow{required property var modelData;label:modelData.role;value:modelData.fps.toFixed(1)+' FPS · '+modelData.p95Ms.toFixed(1)+' ms';separator:false}}
  }
 }
}
