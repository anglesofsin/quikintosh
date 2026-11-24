pragma Singleton
import QtQuick
import QtMultimedia
import Quickshell
import qs.services
import qs.rosa.services
Singleton{
 id:root
 readonly property var preferences:SettingsPreferences.notifications
 readonly property bool ringing:VoiceCalls.enabled && VoiceCalls.showIncoming && preferences.callRingtoneEnabled
 readonly property url source:preferences.callRingtone==='custom' ? preferences.callRingtoneFile:Quickshell.shellDir+'/rosa/ringtones/'+(preferences.callRingtone==='reflection' ? 'reflection':'opening')+'.m4r'
 onRingingChanged:{if(ringing && preferences.callRingtoneVolume>0 && /^(file:|\/)/.test(String(source)))player.play();else player.stop()}
 onSourceChanged:player.stop()
 AudioOutput{id:audio;volume:Math.max(0,Math.min(1,root.preferences.callRingtoneVolume))}
 MediaPlayer{id:player;source:root.source;audioOutput:audio;loops:MediaPlayer.Infinite;onErrorOccurred:(error,message)=>console.warn('Call ringtone:',message)}
 function silence(){player.stop()}
}
