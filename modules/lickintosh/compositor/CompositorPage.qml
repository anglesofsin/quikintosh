import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.settingsapp
ScrollView{
 id:root
 clip:true;contentWidth:availableWidth;contentHeight:body.implicitHeight;ScrollBar.horizontal.policy:ScrollBar.AlwaysOff;leftPadding:16;rightPadding:16;topPadding:8;bottomPadding:16
 property var data:SettingsState.data.compositor || ({})
 property var rules:[]
 property int selected:-1
 property string app:''
 readonly property var current:selected>=0 ? rules[selected] || ({}):({})
 function refresh(){SettingsState.query('compositor',true)}
 function value(key,fallback){const v=SettingsPreferences.inputOverrides[key];return v!==undefined ? v:data.values?.[key] ?? fallback}
 function set(key,value){const next=Object.assign({},SettingsPreferences.inputOverrides);next[key]=value;SettingsPreferences.inputOverrides=next}
 function save(){SettingsState.change('compositor-rules',{rules:root.rules})}
 function patch(key,value){if(selected<0)return;const list=rules.slice(),entry=Object.assign({},list[selected]);entry[key]=value;list[selected]=entry;rules=list;save()}
 Component.onCompleted:refresh()
 Connections{target:SettingsState;function onReadyChanged(){if(SettingsState.ready)root.refresh()}function onDataChanged(){if(SettingsState.data.compositor)root.rules=SettingsState.data.compositor.rules || []}function onCompleted(name,result){if(name==='compositor-rules')root.refresh()}}
 component Toggle:SettingsRow{
  property string option:''
  kind:'switch';available:root.data.values?.[option]!=null
  checked:!!root.value(option,false)
  onToggled:value=>root.set(option,value)
 }
 component Slider:SettingsRow{
  property string option:''
  kind:'slider';available:root.data.values?.[option]!=null
  number:Number(root.value(option,minimum));value:number.toFixed(step<1 ? 2:0)
  onCommitted:value=>root.set(option,value)
 }
 ColumnLayout{id:body;width:root.availableWidth;spacing:20
  SettingsCard{title:'Window appearance'
   Slider{label:'Corner radius';option:'decoration:rounding';minimum:0;maximum:50;step:1}
   Slider{label:'Corner curve';option:'decoration:rounding_power';minimum:2;maximum:10;step:.1}
   Slider{label:'Border width';option:'general:border_size';minimum:0;maximum:12;step:1}
   Slider{label:'Active opacity';option:'decoration:active_opacity';minimum:.1;maximum:1;step:.01}
   Slider{label:'Inactive opacity';option:'decoration:inactive_opacity';minimum:.1;maximum:1;step:.01}
   Slider{label:'Fullscreen opacity';option:'decoration:fullscreen_opacity';minimum:.1;maximum:1;step:.01}
   Toggle{label:'Dim inactive windows';option:'decoration:dim_inactive'}
   Slider{label:'Inactive dimming';option:'decoration:dim_strength';minimum:0;maximum:1;step:.01}
  }
  SettingsCard{title:'Window blur'
   Toggle{label:'Enable blur';option:'decoration:blur:enabled'}
   SettingsRow{label:'Blur preset';kind:'choice';choices:['Custom','Soft','Frosted','Deep'];selection:0;onPicked:i=>{if(i===0)return;const presets=[{}, {size:5,passes:2,noise:.01,contrast:.9,brightness:1.05,vibrancy:.1},{size:9,passes:3,noise:.02,contrast:.95,brightness:1,vibrancy:.2},{size:14,passes:4,noise:.02,contrast:1,brightness:.9,vibrancy:.3}];const next=Object.assign({},SettingsPreferences.inputOverrides);for(const k in presets[i])next['decoration:blur:'+k]=presets[i][k];SettingsPreferences.inputOverrides=next}}
   Slider{label:'Blur radius';option:'decoration:blur:size';minimum:1;maximum:40;step:1}
   Slider{label:'Blur passes';option:'decoration:blur:passes';minimum:1;maximum:8;step:1}
   Slider{label:'Noise';option:'decoration:blur:noise';minimum:0;maximum:1;step:.01}
   Slider{label:'Contrast';option:'decoration:blur:contrast';minimum:0;maximum:2;step:.01}
   Slider{label:'Brightness';option:'decoration:blur:brightness';minimum:0;maximum:2;step:.01}
   Slider{label:'Vibrancy';option:'decoration:blur:vibrancy';minimum:0;maximum:1;step:.01}
   Toggle{label:'Optimize blur';option:'decoration:blur:new_optimizations'}
   Toggle{label:'Ignore window opacity';option:'decoration:blur:ignore_opacity'}
   Toggle{label:'Blur wallpaper behind tiled windows';option:'decoration:blur:xray'}
  }
  SettingsCard{title:'Window Liquid Glass';visible:root.data.values?.['plugin:hyprglass:enabled']!=null
   Toggle{label:'Liquid Glass for all windows';option:'plugin:hyprglass:enabled'}
   SettingsRow{label:'Glass preset';kind:'choice';choices:['Default','Clear','Subtle','Glass','Tahoe-inspired','High contrast'];selection:Math.max(0,['default','clear','subtle','glass','pomme','high_contrast'].indexOf(root.value('plugin:hyprglass:default_preset','default')));onPicked:i=>root.set('plugin:hyprglass:default_preset',['default','clear','subtle','glass','pomme','high_contrast'][i])}
   Slider{label:'Glass blur';option:'plugin:hyprglass:blur_strength';minimum:0;maximum:8;step:.1}
   Slider{label:'Glass blur passes';option:'plugin:hyprglass:blur_iterations';minimum:1;maximum:5;step:1}
   Slider{label:'Refraction';option:'plugin:hyprglass:refraction_strength';minimum:0;maximum:8;step:.1}
   Slider{label:'Color dispersion';option:'plugin:hyprglass:chromatic_aberration';minimum:0;maximum:2;step:.05}
   Slider{label:'Glass opacity';option:'plugin:hyprglass:glass_opacity';minimum:0;maximum:1;step:.01}
   Slider{label:'Glass grain';option:'plugin:hyprglass:noise_strength';minimum:0;maximum:1;step:.01}
   Slider{label:'Specular highlights';option:'plugin:hyprglass:specular_strength';minimum:0;maximum:2;step:.05}
   Slider{label:'Edge highlights';option:'plugin:hyprglass:fresnel_strength';minimum:0;maximum:2;step:.05}
   Slider{label:'Edge width';option:'plugin:hyprglass:edge_thickness_px';minimum:0;maximum:80;step:1}
   Slider{label:'Sample window content';option:'plugin:hyprglass:self_sample';minimum:0;maximum:1;step:.01}
   Toggle{label:'Wallpaper only';option:'plugin:hyprglass:xray'}
  }
  SettingsCard{title:'Shadows'
   Toggle{label:'Window shadows';option:'decoration:shadow:enabled'}
   Slider{label:'Shadow range';option:'decoration:shadow:range';minimum:0;maximum:100;step:1}
   Slider{label:'Shadow falloff';option:'decoration:shadow:render_power';minimum:1;maximum:5;step:.1}
  }
  SettingsCard{title:'Layout & behavior'
   SettingsRow{label:'Layout';kind:'choice';choices:['Dwindle','Master','Scrolling'];selection:Math.max(0,['dwindle','master','scrolling'].indexOf(root.value('general:layout','dwindle')));onPicked:i=>root.set('general:layout',['dwindle','master','scrolling'][i])}
   Slider{label:'Inner gaps';option:'general:gaps_in';minimum:0;maximum:80;step:1}
   Slider{label:'Outer gaps';option:'general:gaps_out';minimum:0;maximum:120;step:1}
   SettingsRow{label:'Focus follows mouse';kind:'choice';choices:['Disabled','Always','Focus on click','Focus without raising'];selection:Number(root.value('input:follow_mouse',1));onPicked:i=>root.set('input:follow_mouse',i)}
   Toggle{label:'Focus on application activation';option:'misc:focus_on_activate'}
   Toggle{label:'Window animations';option:'animations:enabled'}
   Toggle{label:'Animate manual resize';option:'misc:animate_manual_resizes'}
   Toggle{label:'Animate window dragging';option:'misc:animate_mouse_windowdragging'}
   Toggle{label:'Variable frame scheduling';option:'misc:vfr'}
  }
  SettingsCard{title:'Application rules'
   SettingsRow{label:'Application';kind:'field';value:root.app;onEdited:v=>root.app=v}
   SettingsRow{label:'Open applications';kind:'choice';choices:['Choose an application'].concat(root.data.applications || []);selection:0;onPicked:i=>{if(i>0)root.app=root.data.applications[i-1]}}
   SettingsRow{label:'Add rule';kind:'button';buttonText:'Add';available:root.app.length>0;onActivated:{root.rules=root.rules.concat([{app:root.app,activeOpacity:1,inactiveOpacity:1,noBlur:false,noShadow:false,noAnimations:false,rounding:20,borderSize:1}]);root.selected=root.rules.length-1;root.save()}}
   SettingsRow{label:'Edit rule';kind:'choice';choices:['Choose a rule'].concat(root.rules.map(r=>r.app+(r.title ? ' — '+r.title:'')));selection:root.selected+1;onPicked:i=>root.selected=i-1}
   ColumnLayout{visible:root.selected>=0;Layout.fillWidth:true
    SettingsRow{label:'Window title (optional)';kind:'field';value:root.current.title || '';onEdited:v=>root.patch('title',v)}
    SettingsRow{label:'Active opacity';kind:'slider';minimum:.1;maximum:1;step:.01;number:root.current.activeOpacity ?? 1;value:number.toFixed(2);onCommitted:v=>root.patch('activeOpacity',v)}
    SettingsRow{label:'Inactive opacity';kind:'slider';minimum:.1;maximum:1;step:.01;number:root.current.inactiveOpacity ?? 1;value:number.toFixed(2);onCommitted:v=>root.patch('inactiveOpacity',v)}
    SettingsRow{label:'Window material';kind:'choice';available:root.data.values?.['plugin:hyprglass:enabled']!=null;choices:['Follow global','No glass','Clear','Subtle','Glass','Tahoe-inspired','High contrast'];selection:Math.max(0,['inherit','off','clear','subtle','glass','pomme','high_contrast'].indexOf(root.current.glass || 'inherit'));onPicked:i=>root.patch('glass',['inherit','off','clear','subtle','glass','pomme','high_contrast'][i])}
    SettingsRow{label:'Blur';kind:'switch';checked:!root.current.noBlur;onToggled:v=>root.patch('noBlur',!v)}
    SettingsRow{label:'Shadows';kind:'switch';checked:!root.current.noShadow;onToggled:v=>root.patch('noShadow',!v)}
    SettingsRow{label:'Animations';kind:'switch';checked:!root.current.noAnimations;onToggled:v=>root.patch('noAnimations',!v)}
    SettingsRow{label:'Corner radius';kind:'slider';minimum:0;maximum:50;step:1;number:root.current.rounding ?? 20;onCommitted:v=>root.patch('rounding',v)}
    SettingsRow{label:'Border width';kind:'slider';minimum:0;maximum:12;step:1;number:root.current.borderSize ?? 1;onCommitted:v=>root.patch('borderSize',v)}
    SettingsRow{label:'Remove rule';kind:'button';buttonText:'Remove';onActivated:{const list=root.rules.slice();list.splice(root.selected,1);root.selected=-1;root.rules=list;root.save()}}
   }
  }
  SettingsCard{title:'Compositor policy'
   SettingsRow{label:'Restore global overrides';kind:'button';buttonText:'Restore';onActivated:{const next=Object.assign({},SettingsPreferences.inputOverrides);for(const key of Object.keys(root.data.options || {}))delete next[key];SettingsPreferences.inputOverrides=next}}
   SettingsRow{label:'Refresh capabilities';kind:'button';buttonText:'Refresh';onActivated:root.refresh()}
  }
 }
}
