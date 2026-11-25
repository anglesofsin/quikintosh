import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.components
import qs.ui.settings.widgets
ColumnLayout{
 id:root
 property var entry:({})
 function set(key,value){const changes={}
changes[key]=value;WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,changes)}
 spacing:12
 Text{text:'Typography';color:Theme.textSecondary;font.pixelSize:12;font.weight:Font.DemiBold}
 RowLayout{Layout.fillWidth:true
  Text{text:'Text style';color:Theme.textPrimary;Layout.fillWidth:true}
  TahoeCombo{model:['Modern','Classic','Rounded','Typewriter','Serif','Handwriting','Neon'];currentIndex:Math.max(0,['modern','classic','rounded','typewriter','serif','handwriting','neon'].indexOf(root.entry.textStyle || (root.entry.type==='textsticker' ? root.entry.variant:'modern')));onActivated:i=>root.set('textStyle',['modern','classic','rounded','typewriter','serif','handwriting','neon'][i])}
 }
 TahoeField{Layout.fillWidth:true;placeholderText:'Custom font family';text:root.entry.textFont || '';onEditingFinished:root.set('textFont',text.trim())}
 ConfigSlider{text:'Font size';from:12;to:240;decimals:0;value:root.entry.textSize || (root.entry.type==='lyricssticker' ? 28:32);onMoved:v=>root.set('textSize',Math.round(v))}
 ConfigSwitch{text:'Fit text to widget';checked:root.entry.textAutoSize!==false;onToggled:v=>root.set('textAutoSize',v)}
 ConfigSlider{text:'Weight';from:100;to:900;decimals:0;value:root.entry.textWeight || 700;onMoved:v=>root.set('textWeight',Math.round(v/100)*100)}
 ConfigSwitch{text:'Italic';checked:!!root.entry.textItalic;onToggled:v=>root.set('textItalic',v)}
 ConfigSlider{text:'Letter spacing';from:-3;to:20;decimals:1;value:root.entry.textSpacing || 0;onMoved:v=>root.set('textSpacing',v)}
 ConfigSlider{text:'Line spacing';from:.8;to:2;decimals:1;value:root.entry.textLineHeight || 1.1;onMoved:v=>root.set('textLineHeight',v)}
 RowLayout{Layout.fillWidth:true
  Text{text:'Alignment';color:Theme.textPrimary;Layout.fillWidth:true}
  TahoeCombo{model:['Left','Center','Right'];currentIndex:Math.max(0,['left','center','right'].indexOf(root.entry.textAlign || 'center'));onActivated:i=>root.set('textAlign',['left','center','right'][i])}
 }
 RowLayout{Layout.fillWidth:true
  Text{text:'Vertical alignment';color:Theme.textPrimary;Layout.fillWidth:true}
  TahoeCombo{model:['Top','Center','Bottom'];currentIndex:Math.max(0,['top','center','bottom'].indexOf(root.entry.textVertical || 'center'));onActivated:i=>root.set('textVertical',['top','center','bottom'][i])}
 }
 ConfigSlider{text:'Text padding';from:0;to:48;decimals:0;value:root.entry.textPadding ?? 12;onMoved:v=>root.set('textPadding',Math.round(v))}
 RowLayout{Layout.fillWidth:true
  Text{text:'Letter case';color:Theme.textPrimary;Layout.fillWidth:true}
  TahoeCombo{model:['Original','UPPERCASE','lowercase'];currentIndex:Math.max(0,['original','upper','lower'].indexOf(root.entry.textCase || 'original'));onActivated:i=>root.set('textCase',['original','upper','lower'][i])}
 }
 RowLayout{Layout.fillWidth:true
  Text{text:'Text effect';color:Theme.textPrimary;Layout.fillWidth:true}
  TahoeCombo{model:['Solid','Liquid Glass','Gradient','Shadow','Outline','Neon'];currentIndex:Math.max(0,['solid','glass','gradient','shadow','outline','neon'].indexOf(root.entry.textEffect || (root.entry.textStyle==='neon' ? 'neon':'solid')));onActivated:i=>root.set('textEffect',['solid','glass','gradient','shadow','outline','neon'][i])}
 }
 RowLayout{Layout.fillWidth:true
  Text{text:'Color';color:Theme.textPrimary;Layout.fillWidth:true}
  TahoeCombo{model:['Follow appearance','Wallpaper accent','Custom'];currentIndex:Math.max(0,['auto','accent','custom'].indexOf(root.entry.textColorMode || 'auto'));onActivated:i=>root.set('textColorMode',['auto','accent','custom'][i])}
 }
 ColorSetting{visible:root.entry.textColorMode==='custom';label:'Text color';value:root.entry.textColor || Theme.textPrimary;onPicked:v=>root.set('textColor',String(v))}
 ColorSetting{visible:root.entry.textEffect==='outline';label:'Outline color';value:root.entry.textOutlineColor || Theme.accent;onPicked:v=>root.set('textOutlineColor',String(v))}
 ColorSetting{visible:root.entry.textEffect==='gradient';label:'Gradient color';value:root.entry.textGradientColor || Theme.accent;onPicked:v=>root.set('textGradientColor',String(v))}
 ConfigSwitch{text:'Highlight behind text';checked:!!root.entry.textDecorated;onToggled:v=>root.set('textDecorated',v)}
 ColorSetting{visible:!!root.entry.textDecorated;label:'Highlight color';value:root.entry.textBackground || Theme.accent;onPicked:v=>root.set('textBackground',String(v))}
 ConfigSlider{visible:!!root.entry.textDecorated;text:'Highlight opacity';from:0;to:1;decimals:2;value:root.entry.textBackgroundOpacity ?? .25;onMoved:v=>root.set('textBackgroundOpacity',v)}
 ConfigSlider{text:'Rotation';from:-25;to:25;decimals:0;value:root.entry.textRotation || 0;onMoved:v=>root.set('textRotation',Math.round(v))}
 RowLayout{Layout.fillWidth:true
  Text{text:'Text entrance';color:Theme.textPrimary;Layout.fillWidth:true}
  TahoeCombo{model:['None','Fade','Slide'];currentIndex:Math.max(0,['none','fade','slide'].indexOf(root.entry.textAnimation || (root.entry.type==='lyricssticker' ? 'fade':'none')));onActivated:i=>root.set('textAnimation',['none','fade','slide'][i])}
 }
 ConfigSlider{visible:!!root.entry.textAnimation && root.entry.textAnimation!=='none';text:'Animation duration (ms)';from:150;to:2000;decimals:0;value:root.entry.textAnimationMs || 700;onMoved:v=>root.set('textAnimationMs',Math.round(v))}
}
