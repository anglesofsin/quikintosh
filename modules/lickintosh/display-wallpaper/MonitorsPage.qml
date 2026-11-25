import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.components
import qs.ui.settings.widgets
ContentPage{
 id:root
 property string selected:MonitorState.drafts[0]?.output || ''
 readonly property var chosen:MonitorState.drafts.find(s=>s.output===selected) || null
 readonly property var hardware:MonitorState.monitors.find(s=>s.name===selected) || null
 property bool advanced:false
 property bool identify:false
 function update(p){if(chosen)MonitorState.update(selected,p)}
 component Label:Text{color:Theme.textPrimary;font.pixelSize:13;verticalAlignment:Text.AlignVCenter}
 component Field:TahoeField{selectByMouse:true;implicitWidth:100;color:Theme.textPrimary}
 component Line:RowLayout{Layout.fillWidth:true;spacing:14;Layout.minimumHeight:44}
 ContentSection{
  RowLayout{Layout.fillWidth:true
   Label{text:'Displays';font.pixelSize:17;font.weight:Font.DemiBold;Layout.fillWidth:true}
   TahoeButton{text:'Refresh';enabled:!MonitorState.loading && !MonitorState.pending;onClicked:MonitorState.refresh()}
  }
  Rectangle{
   id:map;Layout.fillWidth:true;Layout.preferredHeight:210;radius:14;color:Theme.isLight ? '#09000000':'#0cffffff'
   readonly property var screens:MonitorState.drafts.filter(s=>!s.disabled && !s.mirror)
   readonly property var bounds:{let l=0,t=0,r=1920,b=1080;for(const s of screens){const p=MonitorState.position(s),d=MonitorState.dimensions(s);l=Math.min(l,p.x);t=Math.min(t,p.y);r=Math.max(r,p.x+d.w);b=Math.max(b,p.y+d.h)}return {x:l,y:t,w:r-l,h:b-t}}
   readonly property real factor:Math.min((width-48)/bounds.w,(height-40)/bounds.h)
   Repeater{model:map.screens
    delegate:Rectangle{
     id:screenCard;required property var modelData
     readonly property var pos:MonitorState.position(modelData)
     readonly property var dims:MonitorState.dimensions(modelData)
     x:(map.width-map.bounds.w*map.factor)/2+(pos.x-map.bounds.x)*map.factor
     y:(map.height-map.bounds.h*map.factor)/2+(pos.y-map.bounds.y)*map.factor
     width:dims.w*map.factor;height:dims.h*map.factor;radius:7
     color:root.selected===modelData.output ? Theme.accent:'#647580';border.width:2;border.color:root.selected===modelData.output ? '#eeffffff':'#70ffffff'
     Label{anchors.centerIn:parent;width:parent.width-12;horizontalAlignment:Text.AlignHCenter;text:screenCard.modelData.output;color:'white';elide:Text.ElideRight}
     MouseArea{anchors.fill:parent;cursorShape:Qt.SizeAllCursor;property point start;property point origin
      onPressed:mouse=>{root.selected=screenCard.modelData.output;start=mapToItem(map,mouse.x,mouse.y);origin=Qt.point(screenCard.pos.x,screenCard.pos.y)}
      onReleased:mouse=>{const p=mapToItem(map,mouse.x,mouse.y);root.update({position:Math.round((origin.x+(p.x-start.x)/map.factor)/10)*10+'x'+Math.round((origin.y+(p.y-start.y)/map.factor)/10)*10})}
     }
    }
   }
  }
  Line{Label{text:'Display';Layout.fillWidth:true}TahoeCombo{model:MonitorState.drafts.map(s=>s.output);currentIndex:Math.max(0,MonitorState.drafts.findIndex(s=>s.output===root.selected));onActivated:i=>root.selected=MonitorState.drafts[i].output}}
 }
 ContentSection{
  visible:!!root.chosen
  title:root.hardware?.description || root.selected
  ConfigSwitch{text:'Enabled';checked:!root.chosen?.disabled;enabled:!!root.chosen && (root.chosen.disabled || MonitorState.activeCount>1);onToggled:v=>root.update({disabled:!v})}
  Line{Label{text:'Use as';Layout.fillWidth:true}TahoeCombo{model:['Extended display'].concat(MonitorState.drafts.filter(s=>s.output!==root.selected && !s.disabled && !s.mirror).map(s=>'Mirror '+s.output));currentIndex:root.chosen?.mirror ? Math.max(0,model.indexOf('Mirror '+root.chosen.mirror)):0;onActivated:i=>root.update({mirror:i ? model[i].slice(7):''})}}
  Line{Label{text:'Resolution';Layout.fillWidth:true}TahoeCombo{model:['preferred'].concat([...new Set((root.hardware?.availableModes || []).map(m=>m.split('@')[0]))]);currentIndex:Math.max(0,model.indexOf((root.chosen?.mode || '').split('@')[0]));onActivated:i=>{const mode=i ? (root.hardware.availableModes.find(m=>m.startsWith(model[i]+'@')) || model[i]).replace('Hz',''):'preferred';root.update({mode:mode})}}}
  Line{visible:root.chosen?.mode!=='preferred';Label{text:'Refresh rate';Layout.fillWidth:true}TahoeCombo{model:(root.hardware?.availableModes || []).filter(m=>m.startsWith((root.chosen?.mode || '').split('@')[0]+'@')).map(m=>m.split('@')[1]);currentIndex:Math.max(0,model.findIndex(m=>Math.abs(parseFloat(m)-parseFloat((root.chosen?.mode || '').split('@')[1]))<.1));onActivated:i=>root.update({mode:root.chosen.mode.split('@')[0]+'@'+model[i].replace('Hz','')})}}
  ConfigSlider{text:'Scale';from:.5;to:3;decimals:2;value:root.chosen?.scale || 1;onMoved:v=>root.update({scale:Math.round(v*20)/20})}
  Line{Label{text:'Rotation';Layout.fillWidth:true}TahoeCombo{model:['Normal','90°','180°','270°','Flipped','Flipped 90°','Flipped 180°','Flipped 270°'];currentIndex:root.chosen?.transform || 0;onActivated:i=>root.update({transform:i})}}
  Line{Label{text:'Position';Layout.fillWidth:true}Field{placeholderText:'X';text:String(MonitorState.position(root.chosen || {}).x);validator:IntValidator{};onEditingFinished:root.update({position:Math.round(Number(text))+'x'+MonitorState.position(root.chosen).y})}Field{placeholderText:'Y';text:String(MonitorState.position(root.chosen || {}).y);validator:IntValidator{};onEditingFinished:root.update({position:MonitorState.position(root.chosen).x+'x'+Math.round(Number(text))})}}
  Line{visible:MonitorState.drafts.length>1
   TahoeCombo{id:neighbor;model:MonitorState.drafts.filter(s=>s.output!==root.selected && !s.disabled).map(s=>s.output);Layout.fillWidth:true}
   Repeater{model:['left','right','above','below'];delegate:TahoeButton{required property string modelData;text:modelData;onClicked:MonitorState.beside(root.selected,neighbor.currentText,modelData)}}
  }
  TahoeButton{text:root.advanced ? 'Hide Advanced':'Advanced…';onClicked:root.advanced=!root.advanced}
 }
 ContentSection{
  visible:root.advanced && !!root.chosen;title:'Advanced'
  ConfigSwitch{text:'Variable refresh rate';checked:!!root.chosen?.vrr;onToggled:v=>root.update({vrr:v ? 1:0})}
  ConfigSwitch{text:'10-bit color';checked:root.chosen?.bitdepth===10;onToggled:v=>root.update({bitdepth:v ? 10:8})}
  Line{Label{text:'Color profile';Layout.fillWidth:true}TahoeCombo{model:['auto','srgb','dcip3','dp3','adobe','wide','edid','hdr','hdredid'];currentIndex:Math.max(0,model.indexOf(root.chosen?.cm || 'auto'));onActivated:i=>root.update({cm:model[i]})}}
 }
 ContentSection{
  title:'Display Profiles'
  Line{TahoeCombo{id:profiles;Layout.fillWidth:true;model:Object.keys(MonitorState.profiles)}TahoeButton{text:'Load';enabled:profiles.count>0;onClicked:MonitorState.loadProfile(profiles.currentText)}TahoeButton{text:'Remove';enabled:profiles.count>0;onClicked:MonitorState.deleteProfile(profiles.currentText)}}
  Line{Field{id:profileName;Layout.fillWidth:true;placeholderText:'Profile name'}TahoeButton{text:'Save';enabled:profileName.text.trim()!=='';onClicked:MonitorState.saveProfile(profileName.text)}}
 }
 ContentSection{
  visible:MonitorState.pending!==null || MonitorState.dirty || MonitorState.error!==''
  Label{visible:MonitorState.error!=='';text:MonitorState.error;wrapMode:Text.WordWrap;Layout.fillWidth:true;color:'#ff7777'}
  Line{Label{Layout.fillWidth:true;text:MonitorState.pending ? 'Keep these display settings? '+MonitorState.secondsLeft+'s':''}
   TahoeButton{text:MonitorState.pending ? 'Revert':'Cancel';onClicked:MonitorState.pending ? MonitorState.revert():MonitorState.reset()}
   TahoeButton{text:MonitorState.pending ? 'Keep Changes':'Apply';enabled:!MonitorState.loading;onClicked:MonitorState.pending ? MonitorState.confirm():MonitorState.apply()}
  }
 }
 ContentSection{title:'Night Shift'
  ConfigSwitch{text:'Night Shift';enabled:NightShift.available;checked:NightShift.enabled;onToggled:v=>NightShift.enabled=v}
  ConfigSlider{visible:NightShift.enabled;text:'Color temperature';from:NightShift.minTemperature;to:NightShift.maxTemperature;value:NightShift.temperature;decimals:0;valueSuffix:' K';onMoved:v=>NightShift.setTemperature(v)}
 }
}
