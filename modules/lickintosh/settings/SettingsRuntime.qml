import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
import Quickshell.Wayland
import qs.services
Scope{
 id:root
 required property bool enabled
 property bool locked:false
 property bool workerReady:false
 property bool scheduleWasActive:false
 property bool savedFocus:false
 property bool clockStarted:false
 property double lastUsage:Date.now()
 signal lockRequested()
 function send(name,args){if(workerReady)worker.write(JSON.stringify({kind:'action',name:name,args:args || {}})+'\n')}
 function applyInput(){if(enabled && SettingsPreferences.ready && workerReady)send('runtime',{values:SettingsPreferences.inputOverrides})}
 function minutes(value){const parts=String(value).split(':');return Number(parts[0])*60+Number(parts[1])}
 function tick(){
  if(!enabled || !SettingsPreferences.ready)return
  const now=new Date(),time=now.getHours()*60+now.getMinutes(),focus=SettingsPreferences.focus
  if(focus.endAt>0 && Date.now()>=focus.endAt){ShellConfig.options.session.focus=false;focus.endAt=0}
  const start=minutes(focus.start),end=minutes(focus.end)
  const day=start>end && time<end ? (now.getDay()+6)%7:now.getDay()
  const active=focus.schedule && focus.days.includes(day) && (start<=end ? time>=start && time<end:time>=start || time<end)
  if(active!==scheduleWasActive){if(active){savedFocus=ShellConfig.options.session.focus;ShellConfig.options.session.focus=true}else if(ShellConfig.options.session.focus)ShellConfig.options.session.focus=savedFocus;scheduleWasActive=active}
  if(SettingsPreferences.profile.autoAppearance){const mode=time>=420 && time<1140 ? 'light':'dark';if(ShellConfig.options.appearance.mode!==mode)Theme.setMode(mode)}
  if(SettingsPreferences.accessibility.reduceTransparency){
   if(!SettingsPreferences.session.savedAppearance){SettingsPreferences.session.savedAppearance=ShellConfig.options.appearance.mode;Theme.setMode(Theme.isLight ? 'light':'dark')}
  }else if(SettingsPreferences.session.savedAppearance){const mode=SettingsPreferences.session.savedAppearance;SettingsPreferences.session.savedAppearance='';Theme.setMode(mode)}
 }
 onLockedChanged:SettingsPreferences.locked=locked
 Connections{
  target:SettingsPreferences
  function onInputOverridesChanged(){applyDelay.restart()}
  function onReadyChanged(){if(SettingsPreferences.ready){applyDelay.restart();root.tick()}}
 }
 Connections{target:SettingsPreferences.focus;function onScheduleChanged(){root.tick()}function onStartChanged(){root.tick()}function onEndChanged(){root.tick()}function onDaysChanged(){root.tick()}}
 Connections{target:SettingsPreferences.profile;function onAutoAppearanceChanged(){root.tick()}}
 Connections{target:SettingsPreferences.accessibility;function onReduceTransparencyChanged(){root.tick()}}
 Connections{target:Hyprland;function onRawEvent(event){if(event.name==='configreloaded')applyDelay.restart()}}
 Timer{id:applyDelay;interval:300;onTriggered:root.applyInput()}
 Timer{interval:1000;running:root.enabled;onTriggered:root.tick()}
 Timer{interval:15000;running:root.enabled;repeat:true;onTriggered:root.tick()}
 Timer{
  interval:10000;running:root.enabled && SettingsPreferences.activity.enabled;repeat:true
  onTriggered:{const now=Date.now(),delta=Math.min(15,(now-root.lastUsage)/1000);root.lastUsage=now;if(root.locked || !root.workerReady)return;const app=Hyprland.activeToplevel?.wayland?.appId || '';if(app)root.send('usage-tick',{app:app,seconds:Math.max(1,delta)})}
  onRunningChanged:root.lastUsage=Date.now()
 }
 IdleMonitor{
  enabled:root.enabled && SettingsPreferences.ready && SettingsPreferences.session.autoLock && !root.locked && !KeepAwake.enabled
  timeout:Math.max(60,SettingsPreferences.session.lockAfter)
  respectInhibitors:true
  onIsIdleChanged:if(enabled && isIdle)root.lockRequested()
 }
 Process{
  id:worker;running:root.enabled;stdinEnabled:true;command:['@PYTHON@',Quickshell.shellDir+'/settingsapp/backend.py','--worker']
  stdout:SplitParser{onRead:line=>{try{const event=JSON.parse(line);if(event.type==='ready'){root.workerReady=true;root.applyInput()}else if(event.type==='error')console.warn('Settings runtime:',event.message)}catch(error){console.warn('Settings runtime response:',error)}}}
  onExited:root.workerReady=false
 }
}
