pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
 id:root
 property var fallback:({})
 property bool detected:false
 property int avatarRevision:0
 readonly property bool ready:SettingsPreferences.ready && detected
 readonly property string displayName:SettingsPreferences.profile.displayName.trim() || fallback.name || Quickshell.env('USER') || ''
 readonly property string initial:displayName.charAt(0).toUpperCase() || '?'
 readonly property string avatarPath:{const value=SettingsPreferences.profile.avatar.trim() || fallback.avatar || '';return value.startsWith('~/') ? Quickshell.env('HOME')+value.slice(1):value}
 readonly property url avatarUrl:!avatarPath ? '' : Qt.url((avatarPath.startsWith('file:') || avatarPath.startsWith('qrc:') ? avatarPath:'file://'+avatarPath.split('/').map(encodeURIComponent).join('/'))+(avatarRevision ? '#revision-'+avatarRevision:''))
 Process{running:true;command:['python3',Quickshell.shellDir+'/tools/user-profile.py'];stdout:StdioCollector{onStreamFinished:{try{root.fallback=JSON.parse(text)}catch(error){}root.detected=true}} onExited:root.detected=true}
 FileView{path:root.avatarPath.startsWith('file://') ? decodeURIComponent(root.avatarPath.slice(7)):root.avatarPath;watchChanges:true;onFileChanged:{root.avatarRevision++;reload()}}
}
