import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Dialogs
import Quickshell
import Quickshell.Io
import qs.services
import qs.rosa.services
Item{
 id:root;objectName:'shelf-transcribe'
 property string phase:'idle'
 readonly property var languages:['auto','pt','en','es','fr','de','it','ja','ko','zh','ru']
 readonly property string language:ShelfState.utilityPreferences.voiceLanguage || 'auto'
 property string transcript:''
 property string error:''
 property var request:({})
 property bool held:false
 function begin(event){if(job.running)return;request=Object.assign({},event,{language:language});error='';transcript='';phase='starting';job.running=true}
 onVisibleChanged:if(!visible && phase==='recording')job.running=false
 Connections{target:IslandBus;function onLockedChanged(){if(IslandBus.locked)job.running=false}}
 Process{id:job;command:[ShelfState.pythonExecutable,Quickshell.shellPath('island-shelf/transcribe_backend.py')];stdinEnabled:true
  onStarted:write(JSON.stringify(root.request)+'\n')
  stdout:SplitParser{onRead:line=>{try{const e=JSON.parse(line);if(e.type==='phase')root.phase=e.value;else if(e.type==='transcript'){root.transcript=e.text;root.phase='done'}else if(e.type==='error'){root.error=e.text;root.phase='error'}}catch(_){}}}
  onRunningChanged:{if(root.held!==running){root.held=running;ShelfState.interaction(running)}if(!running && ['starting','recording','processing'].includes(root.phase))root.phase='idle'}
 }
 Component.onDestruction:if(held)ShelfState.interaction(false)
 FileDialog{id:audio;title:qsTr('Transcribe an audio file');nameFilters:[qsTr('Audio (*.wav *.mp3 *.m4a *.ogg *.flac *.opus)'),qsTr('All files (*)')];onAccepted:root.begin({action:'file',path:decodeURIComponent(String(selectedFile).replace('file://',''))})}
 ColumnLayout{anchors.fill:parent;spacing:10
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Voice Transcription');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold}
   ShelfChoice{Layout.preferredWidth:105;model:[qsTr('Automatic'),'Português','English','Español','Français','Deutsch','Italiano','日本語','한국어','中文','Русский'];currentIndex:Math.max(0,root.languages.indexOf(root.language));enabled:!job.running;onActivated:ShelfState.send({action:'utilityPreferences',values:{voiceLanguage:root.languages[currentIndex]}})}
   ShelfButton{flat:true;text:qsTr('Audio file');enabled:!job.running;onClicked:audio.open()}
   ShelfButton{text:root.phase==='recording' ? qsTr('Stop & transcribe'):job.running ? qsTr('Cancel'):qsTr('Record');selected:true;icon:'notch/mic.svg';onClicked:{if(root.phase==='recording'){job.write('stop\n');root.phase='processing'}else if(job.running)job.running=false;else root.begin({action:'record'})}}
  }
  ScrollView{Layout.fillWidth:true;Layout.fillHeight:true
   TextArea{text:root.transcript;readOnly:true;selectByMouse:true;wrapMode:TextEdit.Wrap;color:'white';placeholderTextColor:'#9999a3';placeholderText:root.phase==='recording' ? qsTr('Listening… up to 60 seconds'):root.phase==='processing' ? qsTr('Transcribing on this computer…'):qsTr('Record your voice or choose an audio file. Audio stays on this computer.');font.family:ShelfStyle.textFamily;font.pixelSize:14;background:Rectangle{radius:14;color:'#151518'}}
  }
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:root.error || qsTr('Local multilingual model · audio files up to 5 minutes');elide:Text.ElideRight;color:root.error ? '#ff827b':'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
   ShelfButton{flat:true;text:qsTr('Copy');enabled:root.transcript.length>0;onClicked:ShelfState.send({action:'copyText',text:root.transcript})}
  }
 }
}
