import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects
import Quickshell
import qs.services
import qs.components
import qs.settingsapp
import qs.ui.settings.widgets
ColumnLayout {
 id:root
 Layout.fillWidth:true
 spacing:22
 property bool advanced:false
 readonly property var options:ShellConfig.options.appearance
 readonly property var accentColors:['#007aff','#af52de','#ff2d82','#ff3b30','#ff9500','#ffcc00','#34c759','#8e8e93']
 ColorSetting{id:accentPicker;visible:false;label:I18n.tr('Custom color');value:Theme.accent;onPicked:value=>root.chooseAccent(value)}
 function chooseMode(mode){SettingsPreferences.profile.autoAppearance=mode==='auto';if(mode!=='auto')Theme.setMode(mode)}
 function chooseAccent(color){options.accentMode='manual';Theme.setAccent(String(color))}
 function chooseStyle(style){WidgetState.widgetStyle=style;if(style==='auto')options.iconAppearance='auto'}
 component Card:Rectangle {
  default property alias contents:body.data
  Layout.fillWidth:true
  implicitHeight:body.implicitHeight+28
  radius:14
  color:Theme.isLight ? '#f1f1f3':'#25272a'
  border.width:SettingsPreferences.accessibility.increaseContrast ? 1:0
  border.color:Theme.textSecondary
  ColumnLayout{id:body;anchors{left:parent.left;right:parent.right;top:parent.top;margins:14}spacing:12}
 }
 component Rule:Rectangle{Layout.fillWidth:true;implicitHeight:1;color:Theme.isLight ? '#14000000':'#12ffffff'}
 component Label:Text{color:Theme.textPrimary;font.family:'SF Pro Text';font.pixelSize:13;Layout.fillWidth:true}
 component Tile:Item {
  id:tile
  required property string caption
  required property bool selected
  property bool icon:false
  property string mode:'light'
  property color tint:Theme.accent
  signal picked()
  implicitWidth:icon ? 62:106
  implicitHeight:icon ? 84:92
  activeFocusOnTab:true
  Accessible.role:Accessible.RadioButton
  Accessible.name:caption
  Accessible.checked:selected
  Keys.onSpacePressed:picked()
  Keys.onReturnPressed:picked()
  Rectangle{
   id:frame
   anchors.horizontalCenter:parent.horizontalCenter
   y:4;width:tile.icon ? 49:98;height:tile.icon ? 49:64
   radius:tile.icon ? 12:8
   color:tile.icon ? (tile.mode==='dark' ? '#121315':tile.mode==='clear' ? '#c5c7ca':tile.mode==='tinted' ? tile.tint:'#2486e7'):'#2163c8'
   clip:true
   border.width:1;border.color:Theme.isLight ? '#20000000':'#30ffffff'
   Image{anchors.fill:parent;visible:!tile.icon;source:QuickLookState.urlFor(ShellConfig.options.wallpaper.path);sourceSize:Qt.size(196,128);fillMode:Image.PreserveAspectCrop;asynchronous:true}
   Rectangle{visible:!tile.icon;x:0;y:0;width:tile.mode==='auto' ? parent.width/2:parent.width;height:parent.height;color:tile.mode==='light' || tile.mode==='auto' ? '#40ffffff':'#45000000'}
   Repeater{
    model:tile.icon ? 0:2
    delegate:Rectangle {
     required property int index
     readonly property bool dark:tile.mode==='dark' || (tile.mode==='auto' && index===1)
     x:index===0 ? -5:37;y:index===0 ? 10:32;width:78;height:53;radius:5
     color:dark ? '#292a30':'#ececf0';border.width:1;border.color:'#40000000'
     Rectangle{x:0;y:0;width:parent.width;height:12;radius:4;color:parent.dark ? '#383a42':'#d9d9df'}
     Rectangle{x:7;y:4;width:56;height:4;radius:1;color:'#3985f6'}
     Row{x:9;y:23;spacing:5;Repeater{model:['#ff6059','#ffbe2e','#2aca45'];delegate:Rectangle{required property string modelData;width:8;height:8;radius:4;color:modelData}}}
    }
   }
   Image {
    id:weatherArt;visible:tile.icon
    anchors.fill:parent;anchors.margins:4
    source:Quickshell.shellDir+'/rosa/overlays/assets/weather-partly.png'
    sourceSize:Qt.size(100,100);fillMode:Image.PreserveAspectFit
    layer.enabled:tile.mode==='clear' || tile.mode==='tinted'
    layer.effect:MultiEffect{colorization:1;colorizationColor:tile.mode==='clear' ? '#f9f9fa':Qt.lighter(tile.tint,2.5);saturation:-1}
   }
  }
  Rectangle{anchors.fill:frame;anchors.margins:-4;radius:frame.radius+4;color:'transparent';border.width:tile.selected ? 3:tile.activeFocus ? 1:0;border.color:Theme.accent}
  Text{anchors{top:frame.bottom;topMargin:10;horizontalCenter:parent.horizontalCenter}text:I18n.tr(tile.caption);font.family:'SF Pro Text';font.pixelSize:12;font.weight:tile.selected ? Font.DemiBold:Font.Normal;color:tile.selected ? Theme.textPrimary:Theme.textSecondary}
  MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:tile.picked()}
 }
 Card{
  RowLayout{
   Layout.fillWidth:true;spacing:10
   Label{text:I18n.tr('Appearance');Layout.alignment:Qt.AlignTop;Layout.topMargin:6;font.weight:Font.Medium}
   Repeater{
    model:[{key:'auto',title:'Auto'},{key:'light',title:'Light'},{key:'dark',title:'Dark'}]
    delegate:Tile{
     required property var modelData
     caption:modelData.title;mode:modelData.key
     selected:modelData.key==='auto' ? SettingsPreferences.profile.autoAppearance:!SettingsPreferences.profile.autoAppearance && (Theme.isLight ? modelData.key==='light':modelData.key==='dark')
     onPicked:root.chooseMode(modelData.key)
    }
   }
  }
 }
 Text{text:I18n.tr('Theme');Layout.topMargin:4;Layout.leftMargin:14;font.family:'SF Pro Text';font.pixelSize:15;font.weight:Font.DemiBold;color:Theme.textPrimary}
 Card{
  RowLayout{
   Layout.fillWidth:true;spacing:8
   Label{text:I18n.tr('Color');Layout.minimumWidth:70}
   Item{
    implicitWidth:34;implicitHeight:42
    Rectangle{anchors.centerIn:parent;width:27;height:27;radius:14;gradient:Gradient{orientation:Gradient.Horizontal;GradientStop{position:0;color:'#ff527d'}GradientStop{position:.25;color:'#ffdc51'}GradientStop{position:.5;color:'#4bc866'}GradientStop{position:.75;color:'#36aff7'}GradientStop{position:1;color:'#a05ce6'}}}
    Rectangle{anchors.centerIn:parent;width:35;height:35;radius:18;color:'transparent';border.width:root.options.accentMode==='auto' ? 2:0;border.color:Theme.accent}
    Accessible.name:I18n.tr('Wallpaper');Accessible.role:Accessible.Button
    MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:root.options.accentMode='auto'}
   }
   Repeater{model:root.accentColors
    delegate:Item{
     required property string modelData
     implicitWidth:32;implicitHeight:42
     Rectangle{anchors.centerIn:parent;width:27;height:27;radius:14;color:parent.modelData}
     Rectangle{anchors.centerIn:parent;width:35;height:35;radius:18;color:'transparent';border.width:root.options.accentMode==='manual' && String(Theme.accent).toLowerCase()===parent.modelData ? 2:0;border.color:Theme.accent}
     Accessible.name:modelData;Accessible.role:Accessible.Button
     MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:root.chooseAccent(parent.modelData)}
    }
   }
   Item{
    implicitWidth:32;implicitHeight:42
    Rectangle{anchors.centerIn:parent;width:27;height:27;radius:14;color:Theme.isLight ? '#18000000':'#20ffffff';border.width:1;border.color:Theme.textSecondary
     Text{anchors.centerIn:parent;text:'+';font.pixelSize:20;color:Theme.textPrimary}
    }
    Accessible.name:I18n.tr('Custom color');Accessible.role:Accessible.Button
    MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:accentPicker.open()}
   }
  }
  Rule{}
  SettingsRow{label:'Text highlight color';kind:'choice';choices:['Automatic','Custom'];selection:root.options.highlightMode==='custom' ? 1:0;separator:false;onPicked:index=>root.options.highlightMode=index ? 'custom':'accent'}
  ColorSetting{visible:root.options.highlightMode==='custom';label:I18n.tr('Highlight color');value:root.options.highlightColor;onPicked:value=>root.options.highlightColor=String(value)}
 }
 Card{
  RowLayout{
   Layout.fillWidth:true;spacing:4
   Label{text:I18n.tr('Icon & widget style');Layout.alignment:Qt.AlignTop;Layout.topMargin:6;Layout.minimumWidth:125}
   Repeater{
    model:[{key:'auto',title:'Default'},{key:'dark',title:'Dark'},{key:'clear',title:'Clear'},{key:'tinted',title:'Tinted'}]
    delegate:Tile{
     required property var modelData
     caption:modelData.title;mode:modelData.key;icon:true
     selected:modelData.key==='auto' ? ['auto','color'].includes(WidgetState.widgetStyle):WidgetState.widgetStyle===modelData.key
     tint:AppearanceState.iconColor
     onPicked:root.chooseStyle(modelData.key)
    }
   }
  }
  Rule{}
  SettingsRow{label:'Icon appearance';kind:'choice';choices:['Automatic','Light','Dark'];selection:['auto','light','dark'].indexOf(root.options.iconAppearance);separator:false;onPicked:index=>root.options.iconAppearance=['auto','light','dark'][index]}
  SettingsRow{visible:AppearanceState.tinted;label:'Tint color';kind:'choice';choices:['Matugen palette','Custom'];selection:root.options.iconTintMode==='auto' ? 0:1;onPicked:index=>root.options.iconTintMode=index===0 ? 'auto':'manual'}
  SettingsRow{visible:AppearanceState.tinted && root.options.iconTintMode==='auto';label:'Palette color';kind:'choice';choices:['Primary','Secondary','Tertiary'];selection:['primary','secondary','tertiary'].indexOf(root.options.iconPaletteRole);onPicked:index=>root.options.iconPaletteRole=['primary','secondary','tertiary'][index]}
  ColorSetting{visible:AppearanceState.tinted && root.options.iconTintMode==='manual';label:'Light tint';value:root.options.iconLightColor;onPicked:value=>root.options.iconLightColor=String(value)}
  ColorSetting{visible:AppearanceState.tinted && root.options.iconTintMode==='manual';label:'Dark tint';value:root.options.iconDarkColor;onPicked:value=>root.options.iconDarkColor=String(value)}
 }
 Card{
  SettingsRow{label:'Liquid Glass';kind:'choice';choices:['Clear','Tinted'];selection:Theme.glassValue('*','tintAlpha')>.45 ? 1:0;separator:false;onPicked:index=>Theme.setGlassParam('*','tintAlpha',index===1 ? .62:.12)}
 }
 TahoeButton{text:I18n.tr(root.advanced ? 'Hide advanced settings':'Advanced settings…');onClicked:root.advanced=!root.advanced}
 ColumnLayout{
  Layout.fillWidth:true;visible:root.advanced;spacing:20
  SettingsCard{title:I18n.tr('Icons & Widgets')
   SettingsRow{label:'Transparent widgets';kind:'switch';checked:WidgetState.widgetStyle==='transparent';onToggled:value=>WidgetState.widgetStyle=value ? 'transparent':'auto'}
   SettingsRow{label:'Layer material intensity';kind:'slider';number:root.options.iconTreatmentStrength;minimum:0;maximum:1;step:.05;value:Math.round(root.options.iconTreatmentStrength*100)+'%';separator:false;onCommitted:value=>root.options.iconTreatmentStrength=value}
  }
  RenderingSettings{}
  CornerSettings{}
  SettingsCard{title:I18n.tr('Interface')
   SettingsRow{label:'Sidebar size';kind:'choice';choices:['Small','Medium','Large'];selection:['small','medium','large'].indexOf(root.options.sidebarSize);onPicked:index=>root.options.sidebarSize=['small','medium','large'][index]}
   SettingsRow{label:'Show scroll bars';kind:'choice';choices:['Automatically','When scrolling','Always'];selection:['automatic','scrolling','always'].indexOf(root.options.scrollbarVisibility);separator:false;onPicked:index=>root.options.scrollbarVisibility=['automatic','scrolling','always'][index]}
  }
 }
}
