from pathlib import Path
import sys
base=Path(sys.argv[1])/'rosa'
def edit(name,old,new):
 p=base/name;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Incoming UI anchor '+name+': '+str(s.count(old)))
 p.write_text(s.replace(old,new,1))
edit('overlays/IslandWindow.qml','    readonly property bool wide:\n','    readonly property bool wide:\n        !(VoiceCalls.incoming && !VoiceCalls.showIncoming) &&\n')
edit('overlays/IslandWindow.qml','|| win.hub.voicePeek || win.replying','|| win.hub.voicePeek || VoiceCalls.showIncoming || win.replying')
edit('overlays/IslandWindow.qml','                onTapped: {\n                    if (win.hub.kind === "call"', '                onTapped: {\n                    if(VoiceCalls.incoming){VoiceCalls.dismissIncoming();win.hub.voicePeek=false;win.forced=false;win.hub.pinned=false;win.hushed=true;return}\n                    if (win.hub.kind === "call"')

import shutil
here=Path(__file__).parent
shutil.copytree(here/'ringtones',base/'ringtones')
(base/'services/IncomingRingtone.qml').write_text((here/'IncomingRingtone.qml').read_text())
p=base/'services/qmldir';p.write_text(p.read_text()+'\nsingleton IncomingRingtone IncomingRingtone.qml\n')
p=base/'services/VoiceCalls.qml';s=p.read_text().replace('    id: root','    id: root\n    readonly property var ringtone:IncomingRingtone',1).replace('        if(incoming && call.client', '        if(incoming)IncomingRingtone.silence()\n        if(incoming && call.client',1);p.write_text(s)
p=base.parent/'services/SettingsPreferences.qml';s=p.read_text().replace('   property JsonObject notifications:JsonObject{',"""   property JsonObject notifications:JsonObject{
    property bool callRingtoneEnabled:true
    property string callRingtone:'opening'
    property string callRingtoneFile:''
    property real callRingtoneVolume:0.6""",1);p.write_text(s)
p=base.parent/'settingsapp/SettingsContent.qml';s=p.read_text().replace('import QtQuick.Controls','import qs.rosa.services as Calls\nimport QtQuick.Dialogs as CallDialogs\nimport QtQuick.Controls',1)
s=s.replace(' signal navigate(string page)',""" signal navigate(string page)
 CallDialogs.FileDialog{
  id:callRingtonePicker;title:'Choose Call Ringtone';nameFilters:['Audio (*.wav *.ogg *.mp3 *.m4r *.m4a *.flac *.aiff *.caf)']
  onAccepted:{SettingsPreferences.notifications.callRingtoneFile=selectedFile.toString();SettingsPreferences.notifications.callRingtone='custom'}
 }
""",1)
s=s.replace("   result.push(card('Output',[", """   result.push(card('Incoming Calls',[
    pref('Play Call Ringtone','notifications','callRingtoneEnabled','switch'),
    choice('Ringtone',['Opening (FaceTime)','Reflection','Custom File'],['opening','reflection','custom'].indexOf(SettingsPreferences.notifications.callRingtone),'call-ringtone'),
    pref('Ringtone Volume','notifications','callRingtoneVolume','slider',{minimum:0,maximum:1,step:0.01,value:Math.round(SettingsPreferences.notifications.callRingtoneVolume*100)+'%'}),
    button('Custom Ringtone','Choose File…','call-ringtone-file')
   ]))
   result.push(card('Output',[""",1)
s=s.replace("  if(name==='notification-app')", "  if(name==='call-ringtone'){SettingsPreferences.notifications.callRingtone=['opening','reflection','custom'][value];return}\n  if(name==='call-ringtone-file'){callRingtonePicker.open();return}\n  if(name==='notification-app')",1);p.write_text(s)
