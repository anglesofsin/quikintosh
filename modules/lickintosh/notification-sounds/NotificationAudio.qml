pragma Singleton
import QtQuick
import QtMultimedia
import Quickshell
import Quickshell.Io
import qs.services
import "../notification-sounds/policy.js" as Policy
Singleton {
 id:root
 readonly property var preferences:SettingsPreferences.notifications
 readonly property bool dnd:ShellConfig.options.session.focus
 readonly property var names:['Rebound','Glass','Ping','Custom File']
 readonly property var keys:['rebound','glass','ping','custom']
 property double lastAt:0
 property string lastEvent:''
 property string pending:''
 property int played:0
 readonly property url selectedSource:preferences.sound==='custom' ? preferences.soundFile:Quickshell.shellDir+'/notification-sounds/assets/'+(keys.includes(preferences.sound) ? preferences.sound:'rebound')+'.wav'
 onSelectedSourceChanged:stop()
 function stop(){pending='';effect.stop();player.stop()}
 onDndChanged:if(dnd)stop()
 Connections{target:SettingsPreferences.notifications;function onSoundsChanged(){if(!root.preferences.sounds)root.stop()}}
 function play(preview,notification,rule){
  const hints=notification?.hints || {}
  if(!Policy.permitted({dnd:root.dnd,ready:ShellConfig.ready===true && SettingsPreferences.ready===true,replayed:!!notification?.lastGeneration,preview:preview,enabled:root.preferences.sounds,
      allowed:ShellConfig.options.notifications.enable && rule?.allowed!==false,
      appSound:rule?.sounds!==false,suppress:!preview && (hints['suppress-sound']===true || hints['suppress-sound']===1),
      volume:root.preferences.soundVolume}))return false
  const stamp=notification ? String(notification.id)+':'+notification.summary+':'+notification.body:''
  if(!preview && (Date.now()-lastAt<700 || stamp===lastEvent))return false
  if(!String(selectedSource))return false
  if(preferences.sound==='custom' && !/^(file:|\/)/.test(String(selectedSource)))return false
  stop()
  if(!preview){lastAt=Date.now();lastEvent=stamp}
  pending=String(selectedSource)
  if(preferences.sound==='custom'){
   player.source=selectedSource
   if(player.mediaStatus===MediaPlayer.LoadedMedia || player.mediaStatus===MediaPlayer.BufferedMedia)startCustom()
   else player.play()
  }else if(effect.status===SoundEffect.Ready){effect.play();played++;pending=''}
  return true
 }
 function startCustom(){if(!pending || dnd)return;player.play();played++;pending=''}
 SoundEffect{
  id:effect;source:root.preferences.sound==='custom' ? '':root.selectedSource
  volume:Math.max(0,Math.min(1,root.preferences.soundVolume))
  onStatusChanged:if(status===SoundEffect.Error){root.pending='';console.warn('Notification sound could not be loaded')}else if(status===SoundEffect.Ready && root.pending && !root.dnd){play();root.played++;root.pending=''}
 }
 AudioOutput{id:output;volume:Math.max(0,Math.min(1,root.preferences.soundVolume))}
 MediaPlayer{
  id:player;audioOutput:output
  onMediaStatusChanged:if(mediaStatus===MediaPlayer.LoadedMedia || mediaStatus===MediaPlayer.BufferedMedia)root.startCustom()
  onErrorOccurred:(error,message)=>{root.pending='';console.warn('Notification sound:',message)}
 }
 IpcHandler{
  target:'notificationAudio'
  function state():string{return JSON.stringify({enabled:root.preferences.sounds,dnd:root.dnd,sound:root.preferences.sound,volume:root.preferences.soundVolume,played:root.played})}
  function preview():bool{return root.play(true,null,null)}
 }
}
