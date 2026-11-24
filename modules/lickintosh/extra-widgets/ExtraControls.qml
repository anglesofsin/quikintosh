pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Services.Pipewire
import qs.services
Singleton{
 id:root
 readonly property var microphone:Pipewire.defaultAudioSource
 readonly property bool microphoneMuted:!!microphone?.audio?.muted
 PwObjectTracker{objects:root.microphone ? [root.microphone]:[]}
 readonly property var entries:[
  {id:'extra_clipboard',title:'Clipboard',icon:'notch/clipboard.svg',category:'utilities',w:1,h:1,subtitle:''},
  {id:'extra_notifications',title:'Notifications',icon:'notch/bell.svg',category:'utilities',w:1,h:1,subtitle:''},
  {id:'extra_microphone',title:'Microphone',icon:'notch/mic.svg',category:'media',w:1,h:1,subtitle:''},
  {id:'extra_ocr',title:'Copy Text from Screen',icon:'search.svg',category:'screen',w:1,h:1,subtitle:''},
  {id:'extra_color',title:'Color Picker',icon:'settings/appearance.svg',category:'screen',w:1,h:1,subtitle:''},
  {id:'extra_wallpaper',title:'Wallpaper',icon:'notch/image.svg',category:'display',w:1,h:1,subtitle:''},
  {id:'extra_settings',title:'Settings',icon:'settings/general.svg',category:'utilities',w:1,h:1,subtitle:''},
  {id:'extra_quicknote',title:'Quick Note',icon:'notch/book.svg',category:'utilities',w:1,h:1,subtitle:''}
 ]
 function available(id){return id!=='extra_microphone' || !!microphone?.audio}
 function active(id){return id==='extra_microphone' && microphoneMuted}
 function run(id){
  if(id==='extra_microphone'){if(microphone?.audio)microphone.audio.muted=!microphone.audio.muted;return}
  const actions={extra_clipboard:['rice','clipboard'],extra_notifications:['rice','notifications'],extra_ocr:['capture','ocr'],extra_color:['capture','colorPicker'],extra_wallpaper:['rice','wallpaper'],extra_settings:['rice','settings'],extra_quicknote:['rice','quickNote']}
  const command=actions[id];if(command)Quickshell.execDetached(['lickintosh','ipc','call'].concat(command))
 }
}
