pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Hyprland
import qs.services
import "FocusPolicy.js" as Policy
Singleton {
 id:root
 readonly property var prefs:SettingsPreferences.focus
 readonly property var profiles:prefs.profiles
 readonly property var profile:profiles.find(p=>p.id===prefs.activeId) || profiles[0] || ({})
 readonly property bool sharing:MediaCaptureState.visibleDetails.some(e=>e.kind==='screen') || CaptureState.recording
 property string automation:''
 property bool owned:false
 property bool changing:false
 property bool suppressed:false
 property string lastWanted:''
 readonly property string activeApp:Hyprland.activeToplevel?.wayland?.appId || ''
 function edit(key,value){const next=profiles.map(p=>{if(p.id!==profile.id)return p;const item=Object.assign({},p);item[key]=value;return item});prefs.profiles=next}
 function select(id){prefs.activeId=id}
 function add(){const id='custom-'+Date.now();prefs.profiles=profiles.concat([{id:id,name:'Custom Focus',appMode:'allow',apps:'',peopleMode:'allow',people:'',allowCritical:true,timeSensitive:false,schedule:false,start:'09:00',end:'17:00',days:[1,2,3,4,5],triggerApps:''}]);select(id)}
 function remove(){if(profiles.length<2)return;prefs.profiles=profiles.filter(p=>p.id!==profile.id);select(profiles[0].id)}
 function permits(notification){
  const hints=notification.hints || {}
  const sender=hints['sender'] || hints['x-quickintosh-sender'] || ''
  const critical=Number(notification.urgency)===2
  return Policy.permits(profile,notification.appName,sender,critical,!!hints['x-quickintosh-time-sensitive'])
 }
 function tick(){
  if(!SettingsPreferences.ready || SettingsPreferences.locked)return
  if(prefs.profileVersion===0){
   prefs.profileVersion=1
   prefs.profiles=profiles.map((p,i)=>i===0 ? Object.assign({},p,{allowCritical:prefs.allowCritical,schedule:prefs.schedule,start:prefs.start,end:prefs.end,days:prefs.days}):p)
  }
  const now=new Date()
  const scheduled=profiles.find(p=>Policy.scheduled(p,now) || Policy.matches(p.triggerApps,activeApp))
  const wanted=prefs.autoDndSharing && sharing ? 'sharing':scheduled ? scheduled.id:''
  if(wanted!==lastWanted){suppressed=false;lastWanted=wanted}
  if(wanted && !suppressed){
   if(!automation && !ShellConfig.options.session.focus){owned=true;changing=true;ShellConfig.options.session.focus=true;changing=false}
   automation=wanted
   if(scheduled && wanted!=='sharing' && prefs.activeId!==scheduled.id)select(scheduled.id)
  }else if(!wanted){
   if(owned && ShellConfig.options.session.focus){changing=true;ShellConfig.options.session.focus=false;changing=false}
   owned=false;automation=''
  }
 }
 Connections{target:ShellConfig.options.session;function onFocusChanged(){if(!root.changing){root.owned=false;if(root.automation)root.suppressed=true}}}
 Connections{target:root.prefs;function onAutoDndSharingChanged(){root.tick()}function onProfilesChanged(){root.tick()}}
 onSharingChanged:tick()
 onActiveAppChanged:tick()
 Timer{interval:1000;running:SettingsPreferences.ready;repeat:true;triggeredOnStart:true;onTriggered:root.tick()}
}
