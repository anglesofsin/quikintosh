import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.components
import qs.ui.widgets
import qs.ui.settings.widgets
ColumnLayout{
 id:root
 property var entry:({})
 function set(key,value){const changes={};changes[key]=value;WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,changes)}
 Layout.fillWidth:true;spacing:14
 EditorGroup{visible:root.entry.type==='worldclock';title:'Cities'
  Text{Layout.fillWidth:true;text:'City name and IANA time zone, separated by a vertical bar';color:Theme.textSecondary;font.pixelSize:12;wrapMode:Text.WordWrap}
  ScrollView{Layout.fillWidth:true;Layout.preferredHeight:180;clip:true
   TextArea{wrapMode:TextEdit.Wrap;selectByMouse:true;color:Theme.textPrimary;text:(root.entry.worldCities || [{name:'Cupertino',tz:'America/Los_Angeles'},{name:'New York',tz:'America/New_York'},{name:'London',tz:'Europe/London'},{name:'Paris',tz:'Europe/Paris'},{name:'Dubai',tz:'Asia/Dubai'},{name:'Tokyo',tz:'Asia/Tokyo'}]).map(c=>c.name+' | '+c.tz).join('\n');onActiveFocusChanged:if(!activeFocus){const cities=text.split('\n').map(line=>{const parts=line.split('|');return {name:(parts[0] || '').trim(),tz:(parts[1] || '').trim()}}).filter(c=>c.name && c.tz).slice(0,8);if(cities.length)root.set('worldCities',cities)}
    background:Rectangle{radius:10;color:Theme.fillControl}
   }
  }
  ConfigSwitch{text:'12-hour clock';checked:!!root.entry.world12Hour;onToggled:v=>root.set('world12Hour',v)}
 }
 EditorGroup{visible:root.entry.type==='calendar';title:'Calendar'
  RowLayout{Layout.fillWidth:true
   Text{text:'First day of week';color:Theme.textPrimary;Layout.fillWidth:true}
   TahoeCombo{model:['Follow language','Monday','Sunday'];currentIndex:root.entry.calendarFirstDay===1 ? 1:root.entry.calendarFirstDay===0 ? 2:0;onActivated:i=>root.set('calendarFirstDay',i===0 ? -1:i===1 ? 1:0)}
  }
  ConfigSwitch{text:'Show events';checked:root.entry.calendarEvents!==false;onToggled:v=>root.set('calendarEvents',v)}
 }
 EditorGroup{visible:root.entry.type==='tasks';title:'Tasks'
  ConfigSwitch{text:'Show completed tasks';checked:root.entry.tasksCompleted!==false;onToggled:v=>root.set('tasksCompleted',v)}
 }
 EditorGroup{visible:root.entry.type==='timer';title:'Timer presets'
  TahoeField{Layout.fillWidth:true;text:(root.entry.timerPresets || [1,5,10,25]).join(', ');placeholderText:'Minutes, separated by commas';onEditingFinished:{const list=Array.from(new Set(text.split(',').map(Number).filter(n=>Number.isFinite(n) && n>0 && n<=1440))).slice(0,6);if(list.length)root.set('timerPresets',list)}}
 }
 EditorGroup{visible:root.entry.type==='quote';title:'Quote'
  TahoeField{Layout.fillWidth:true;text:root.entry.quoteText || '';placeholderText:'Custom quote (optional)';onEditingFinished:root.set('quoteText',text)}
  TahoeField{Layout.fillWidth:true;text:root.entry.quoteAuthor || '';placeholderText:'Author';onEditingFinished:root.set('quoteAuthor',text)}
 }
 EditorGroup{visible:root.entry.type==='weather';title:'Location privacy'
  ConfigSwitch{text:'Show location name';checked:root.entry.weatherLocation!==false;onToggled:v=>root.set('weatherLocation',v)}
 }
}
