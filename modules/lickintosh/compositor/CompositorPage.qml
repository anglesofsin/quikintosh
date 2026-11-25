import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs
import qs.components
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
 function isPageOption(key) {
  return key.startsWith('window-animation:') || key.startsWith('workspace-animation:') || key.startsWith('plugin:hyprimate:') ||
         Object.prototype.hasOwnProperty.call(root.data.options || {},key)
 }
 readonly property bool canReset: Object.keys(SettingsPreferences.inputOverrides).some(root.isPageOption)
 function restoreDefaults() {
  const next=Object.assign({},SettingsPreferences.inputOverrides)
  for (const key of Object.keys(next))
   if (root.isPageOption(key)) delete next[key]
  SettingsPreferences.inputOverrides=next
  refreshTimer.restart()
 }
 Timer { id: refreshTimer; interval: 950; onTriggered: root.refresh() }
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
 property string manifestKey: ''
 property bool depthPicker: false
 FileDialog {
  id: manifestPicker
  title: root.depthPicker ? 'Choose a depth image' : 'Choose a Hyprimate shader manifest'
  nameFilters: root.depthPicker ? ['Depth images (*.png)'] : ['Shader manifests (*.json)']
  onAccepted: {
   const url=String(selectedFile)
   if (url.startsWith('file://')) root.set(root.manifestKey,decodeURIComponent(url.slice(7)))
  }
 }
 function animationLabel(path) {
  return path.split('.').pop().replace(/_/g,' ').replace(/^./, letter=>letter.toUpperCase())
 }
 function customEffectField(field) {
  return /\.effect(_parameters|_duration)?$/.test(field.path)
 }
 function hasManifest(field) {
  return !!root.value(field.key.replace(/:effect_(parameters|duration)$/,':effect'),'')
 }
 component AnimationOption: SettingsRow {
     id: animationRow
     property bool explain: false
     required property var modelData
     readonly property var field: modelData
     readonly property var currentValue: root.value(field.key, field.default)
     readonly property bool numeric: field.type === 'float' || field.type === 'int'
     readonly property bool curve: field.path.endsWith('.curve')
     readonly property bool depthImage: field.path.endsWith('.depth_source')
     readonly property bool manifest: field.path.endsWith('.effect')
     readonly property bool fileOption: manifest || depthImage
     readonly property bool sideSet: field.type==='set'
     readonly property var sideChoices: ['all'].concat(field.choices || [])
     readonly property bool parameters: field.path.endsWith('.effect_parameters')
     readonly property bool sprite: field.path.endsWith('.swarm.sprite')
     readonly property bool listed: sprite || curve || (field.type === 'string' && !!field.choices)
     label: depthImage ? 'Depth image' : manifest ? 'Shader manifest' : parameters ? 'Shader parameters (JSON)' :
         field.path.endsWith('.effect_duration') ? 'Shader duration' : root.animationLabel(field.path)
     visible: !root.customEffectField(field) || manifest || root.hasManifest(field)
     buttonText: fileOption ? 'Choose file…' : ''
     onActivated: if (fileOption) { root.manifestKey=field.key; root.depthPicker=depthImage; manifestPicker.open() }
     description: fileOption && currentValue ? String(currentValue).split('/').pop() : explain ? field.description : ''
     available: root.data.values?.[field.key] != null
     kind: fileOption ? 'button' : field.type === 'boolean' ? 'switch' : (listed || sideSet) ? 'choice' : numeric ? 'slider' : 'field'
     checked: currentValue === true
     choices: sprite ? Array.from(new Set(['spider','cat','bird',String(currentValue)])) : sideSet ? (sideChoices.includes(currentValue) ? sideChoices : [String(currentValue)].concat(sideChoices)) : curve ? Array.from(new Set([String(currentValue || 'default')].concat(root.data.workspaceNative?.curves || []))) : listed ? field.choices : []
     selection: Math.max(0, choices.indexOf(currentValue))
     minimum: field.min ?? (numeric ? Math.min(0,Number(currentValue),Number(field.default)*2) : 0)
     maximum: field.path.endsWith('duration') ? Math.max(3000,Number(currentValue),Number(field.default)) : field.max ?? (numeric ? Math.max(10,Number(currentValue),Number(field.default)*4) : 1)
     step: field.type === 'int' || maximum > 100 ? 1 : 0.01
     number: numeric ? Number(currentValue) : 0
     value: numeric && isFinite(number) ? number.toFixed(step < 1 ? 2 : 0) + (field.path.endsWith('duration') ? ' ms' : '') : field.type === 'color' && typeof currentValue === 'number' ? '0x' + currentValue.toString(16).padStart(8, '0') : String(currentValue ?? '')
     onToggled: enabled => root.set(field.key, enabled)
     onPicked: index => root.set(field.key, choices[index])
     onCommitted: amount => root.set(field.key, amount)
     onEdited: text => {
      if (!parameters) { root.set(field.key,text); return }
      try {
       const object=JSON.parse(text)
       if (object && typeof object==='object' && !Array.isArray(object)) root.set(field.key,JSON.stringify(object))
      } catch (_) {}
     }
    }
 ColumnLayout{id:body;width:root.availableWidth;spacing:20
  TahoeButton {
   Layout.alignment: Qt.AlignRight
   enabled: root.canReset
   text: '↶  Restore defaults'
   Accessible.name: 'Restore window and animation defaults'
   onClicked: root.restoreDefaults()
  }
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
  SettingsCard {
   title: 'Glass rendering'
   visible: root.data.values?.['plugin:hyprglass:windows:background_cache'] != null

   Toggle { label: 'Reuse unchanged window backgrounds'; option: 'plugin:hyprglass:windows:background_cache' }
   Toggle { label: 'Update when the background moves'; option: 'plugin:hyprglass:windows:live_resample' }
   Slider {
    label: 'Maximum background updates per second'
    option: 'plugin:hyprglass:windows:live_resample_fps'
    minimum: 0; maximum: 360; step: 1
    value: number === 0 ? 'Unlimited' : number.toFixed(0)
   }
  }
  SettingsCard {
   id: workspaceAnimations
   title: 'Workspace animations'
   readonly property string pluginPrefix: 'plugin:hyprimate:workspace:'
   readonly property string nativePrefix: 'workspace-animation:'
   readonly property var pluginStyles: root.data.hyprimate ? ['rotation','planet_hop','cube','lava','shader'] : []
   readonly property var pluginLabels: root.data.hyprimate ? ['Rotation','Planet Hop','Cube','Lava','Custom Shader'] : []
   readonly property var nativeStyles: ['slide','slidevert','fade','slidefade','slidefadevert','off']
   readonly property var nativeLabels: ['Slide','Vertical Slide','Fade','Slide and Fade','Vertical Slide and Fade','Off']
   readonly property bool pluginActive: root.data.hyprimate === true && !!root.value(pluginPrefix+'enabled',false)
   readonly property string pluginStyle: root.value(pluginPrefix+'effect','') ? 'shader' : root.value(pluginPrefix+'style','rotation')
   readonly property string nativeStyle: nativeValue('enabled',true) ? nativeValue('style','slide') : 'off'
   readonly property var pluginFields: (root.data.animationFields || []).filter(field => {
    if (!field.path.startsWith('workspace.') || ['workspace.enabled','workspace.style'].includes(field.path)) return false
    if (pluginStyle === 'shader') return field.path.startsWith('workspace.effect')
    return !field.path.startsWith('workspace.effect') &&
        (!field.path.startsWith('workspace.options.') || field.path.startsWith('workspace.options.'+pluginStyle+'.'))
   })
   function nativeValue(key,fallback) {
    return root.value(nativePrefix+key,root.data.workspaceNative?.[key] ?? fallback)
   }
   function select(index) {
    const next=Object.assign({},SettingsPreferences.inputOverrides)
    if (index<pluginStyles.length) {
     const style=pluginStyles[index]
     next[pluginPrefix+'enabled']=true
     if (style==='shader') {
      next[pluginPrefix+'effect']=root.value(pluginPrefix+'effect','')
     } else {
      next[pluginPrefix+'style']=style
      next[pluginPrefix+'effect']=''
     }
    } else {
     const style=nativeStyles[index-pluginStyles.length]
     if (root.data.hyprimate) next[pluginPrefix+'enabled']=false
     next[nativePrefix+'enabled']=style!=='off'
     if (style!=='off') next[nativePrefix+'style']=style
    }
    SettingsPreferences.inputOverrides=next
   }
   // An empty manifest still uses the selected built-in effect. Keep the editor
   // available while a custom manifest is being entered.
   property bool editingShader: false
   SettingsRow {
    label:'Transition';kind:'choice'
    choices:workspaceAnimations.pluginLabels.map(label=>'Hyprimate · '+label)
        .concat(workspaceAnimations.nativeLabels.map(label=>'Hyprland · '+label))
    selection:workspaceAnimations.pluginActive
        ? Math.max(0,workspaceAnimations.pluginStyles.indexOf(workspaceAnimations.editingShader ? 'shader' : workspaceAnimations.pluginStyle))
        : workspaceAnimations.pluginStyles.length+Math.max(0,workspaceAnimations.nativeStyles.indexOf(workspaceAnimations.nativeStyle))
    onPicked:index=>{
     workspaceAnimations.editingShader=workspaceAnimations.pluginStyles[index]==='shader'
     workspaceAnimations.select(index)
    }
   }
   Repeater {
    model:workspaceAnimations.pluginActive
     ? (workspaceAnimations.editingShader
      ? (root.data.animationFields || []).filter(field=>field.path.startsWith('workspace.effect'))
      : workspaceAnimations.pluginFields)
     : []
    delegate: AnimationOption { explain: true }
   }
   SettingsRow {
    visible:!workspaceAnimations.pluginActive && workspaceAnimations.nativeStyle!=='off'
    label:'Duration';kind:'slider';minimum:0.1;maximum:30;step:0.1
    number:Number(workspaceAnimations.nativeValue('speed',5));value:Math.round(number*100)+' ms'
    onCommitted:amount=>root.set(workspaceAnimations.nativePrefix+'speed',amount)
   }
   SettingsRow {
    visible:!workspaceAnimations.pluginActive && workspaceAnimations.nativeStyle!=='off'
    label:'Timing curve';kind:'choice'
    readonly property string selectedCurve:workspaceAnimations.nativeValue('curve','default')
    choices:Array.from(new Set([selectedCurve].concat(root.data.workspaceNative?.curves || [])))
    selection:Math.max(0,choices.indexOf(selectedCurve))
    onPicked:index=>root.set(workspaceAnimations.nativePrefix+'curve',choices[index])
   }
   SettingsRow {
    visible:!workspaceAnimations.pluginActive && !['fade','off'].includes(workspaceAnimations.nativeStyle)
    label:'Travel distance';kind:'slider';minimum:0;maximum:200;step:1
    number:Number(workspaceAnimations.nativeValue('distance',100));value:number.toFixed(0)+'%'
    onCommitted:amount=>root.set(workspaceAnimations.nativePrefix+'distance',amount)
   }
   SettingsRow {
    visible:!workspaceAnimations.pluginActive && !['fade','off'].includes(workspaceAnimations.nativeStyle)
    label:'Direction';kind:'choice';choices:['Automatic','Left','Right','Up','Down']
    readonly property var directions:['','left','right','top','bottom']
    selection:Math.max(0,directions.indexOf(workspaceAnimations.nativeValue('direction','')))
    onPicked:index=>root.set(workspaceAnimations.nativePrefix+'direction',directions[index])
   }
  }
  Repeater {
   model: ['windowsIn', 'windowsOut']
   delegate: SettingsCard {
    id: nativeWindow
    required property string modelData
    readonly property string prefix: 'window-animation:'+modelData+':'
    readonly property var current:root.data.windowNative?.[modelData] || ({})
    function read(key,fallback){return root.value(prefix+key,current[key] ?? fallback)}
    readonly property string effectKey: 'plugin:hyprimate:window:'+(modelData==='windowsIn' ? 'open' : 'close')+':enabled'
    readonly property bool useHyprimate: root.data.hyprimate===true &&
        root.value('plugin:hyprimate:window:enabled',true) && root.value(effectKey,true)
    title:modelData==='windowsIn' ? 'Window opening' : 'Window closing'
    SettingsRow {
     visible:root.data.hyprimate===true
     label:'Animation provider';kind:'choice';choices:['Hyprland','Hyprimate']
     selection:nativeWindow.useHyprimate ? 1:0
     onPicked:index=>{
      if(index===1)root.set('plugin:hyprimate:window:enabled',true)
      root.set(nativeWindow.effectKey,index===1)
     }
    }
    SettingsRow {
     visible:!nativeWindow.useHyprimate
     label:'Enabled';kind:'switch';checked:nativeWindow.read('enabled',true)
     onToggled:value=>root.set(nativeWindow.prefix+'enabled',value)
    }
    SettingsRow {
     visible:!nativeWindow.useHyprimate
     label:'Style';kind:'choice';choices:['Slide','Scale']
     selection:nativeWindow.read('style','popin')==='slide' ? 0:1
     onPicked:index=>root.set(nativeWindow.prefix+'style',['slide','popin'][index])
    }
    SettingsRow {
     label:'Scale from';kind:'slider';minimum:0;maximum:100;step:1
     visible:!nativeWindow.useHyprimate && nativeWindow.read('style','popin')==='popin'
     number:nativeWindow.read('amount',80);value:number+'%'
     onCommitted:amount=>root.set(nativeWindow.prefix+'amount',amount)
    }
    SettingsRow {
     visible:!nativeWindow.useHyprimate
     label:'Duration';kind:'slider';minimum:.1;maximum:20;step:.1
     number:nativeWindow.read('speed',5);value:Math.round(number*100)+' ms'
     onCommitted:amount=>root.set(nativeWindow.prefix+'speed',amount)
    }
    SettingsRow {
     visible:!nativeWindow.useHyprimate
     label:'Easing';kind:'choice'
     readonly property string selectedCurve:nativeWindow.read('curve','default')
     choices:Array.from(new Set([selectedCurve].concat(root.data.windowNative?.curves || [])))
     selection:choices.indexOf(selectedCurve)
     onPicked:index=>root.set(nativeWindow.prefix+'curve',choices[index])
    }
   }
  }
  SettingsCard {
   id: animations
   title: 'Hyprimate · Window and wallpaper effects'
   visible: root.data.hyprimate === true
   property string section: 'window'
   property string filter: ''
   property string phase: 'general'
   property bool customShaders: false
   readonly property var phases: ['general','open','close','movement','resize']
   readonly property string style: root.value('plugin:hyprimate:window:style','liquid')
   onPhaseChanged: page=0
   onCustomShadersChanged: page=0
   property int page: 0
   property bool explain: false
   readonly property int pageSize: 18
   readonly property int lastPage: Math.max(0, Math.ceil(fields.length / pageSize) - 1)
   onSectionChanged: page = 0
   onFilterChanged: page = 0
   readonly property var sections: ['window', 'wallpaper']
   readonly property var fields: (root.data.animationFields || []).filter(field => {
    const path = field.path.toLowerCase()
    if (!path.startsWith(section+'.') || !path.includes(filter.trim().toLowerCase())) return false
    const parts=path.split('.')
    if (root.customEffectField(field)) {
     if (!customShaders) return false
     return section==='wallpaper' || parts[1]===(phase==='movement' ? 'move' : phase)
    }
    if (section==='wallpaper') return true
    const phaseKey=['open','close','movement','resize'].includes(parts[1]) ? parts[1] : 'general'
    if (phaseKey!==phase) return false
    const options=parts.indexOf('options')
    return options<0 || parts[options+1]===style
   })

   SettingsRow {
    label: 'Animation group'; kind: 'choice'
    choices: ['Windows', 'Wallpaper']
    selection: animations.sections.indexOf(animations.section)
    onPicked: index => animations.section = animations.sections[index]
   }
   SettingsRow {
    visible: animations.section==='window'
    label: 'Window event';kind:'choice'
    choices: ['General','Opening','Closing','Moving','Resizing']
    selection: animations.phases.indexOf(animations.phase)
    onPicked:index=>animations.phase=animations.phases[index]
   }
   SettingsRow {
    label: 'Custom shaders';kind:'switch';checked:animations.customShaders
    onToggled:enabled=>animations.customShaders=enabled
   }
   Repeater {
    model: animations.customShaders ? animations.fields.filter(field=>field.path.endsWith('.effect') && root.value(field.key,'')) : []
    delegate: SettingsRow {
     required property var modelData
     label:'Custom shader';kind:'button';buttonText:'Remove'
     onActivated:root.set(modelData.key,'')
    }
   }
   SettingsRow {
    label: 'Filter animation settings'; kind: 'field'; value: animations.filter
    onEdited: text => animations.filter = text
   }
   SettingsRow {
    label: 'Show option descriptions'; kind: 'switch'; checked: animations.explain
    onToggled: enabled => animations.explain = enabled
   }
   SettingsRow {
    visible: animations.lastPage > 0
    label: 'Settings page'; kind: 'choice'; selection: animations.page
    choices: Array.from({length: animations.lastPage + 1}, (_, index) => String(index + 1))
    onPicked: index => animations.page = index
   }
   Repeater {
    model: animations.visible ? animations.fields.slice(animations.page * animations.pageSize, (animations.page + 1) * animations.pageSize) : []
    delegate: AnimationOption { explain: animations.explain }
   }
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
