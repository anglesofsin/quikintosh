import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
Item{
 id:root;objectName:'shelf-terminal'
 property string output:''
 property string request:''
 property int exitCode:0
 property bool held:false
 function run(){if(job.running || !command.text.trim())return;request=JSON.stringify({command:command.text});output='';exitCode=0;job.running=true}
 Process{id:job;command:[ShelfState.pythonExecutable,Quickshell.shellPath('island-shelf/terminal_backend.py')];stdinEnabled:true
  onStarted:write(root.request+'\n')
  stdout:SplitParser{onRead:line=>{try{const event=JSON.parse(line);if(event.type==='output' || event.type==='error')root.output=(root.output+event.text).slice(-262144);else if(event.type==='exit')root.exitCode=event.code}catch(_){}}}
  onRunningChanged:{if(root.held!==running){root.held=running;ShelfState.interaction(running)}}
 }
 Component.onDestruction:if(held)ShelfState.interaction(false)
 ColumnLayout{anchors.fill:parent;spacing:8
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Quick Terminal');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold}
   ShelfButton{flat:true;text:qsTr('Open Terminal');onClicked:Quickshell.execDetached(['kitty'])}
   ShelfButton{text:job.running ? qsTr('Stop'):qsTr('Run');selected:true;enabled:job.running || command.text.trim().length>0;onClicked:{if(job.running)job.running=false;else root.run()}}
  }
  ScrollView{Layout.fillWidth:true;Layout.preferredHeight:52
   TextArea{id:command;objectName:'terminal-command';placeholderText:qsTr('Enter a shell command · Ctrl+Enter to run');color:'white';placeholderTextColor:'#9999a3';font.family:'SF Mono';font.pixelSize:12;selectByMouse:true;wrapMode:TextEdit.Wrap;background:Rectangle{radius:12;color:'#18181c'} Keys.onPressed:event=>{if(event.key===Qt.Key_Return && event.modifiers&Qt.ControlModifier){root.run();event.accepted=true}}}
  }
  ScrollView{Layout.fillWidth:true;Layout.fillHeight:true
   TextArea{objectName:'terminal-output';text:root.output;readOnly:true;selectByMouse:true;wrapMode:TextEdit.Wrap;color:'#eeeeef';font.family:'SF Mono';font.pixelSize:11;background:Rectangle{radius:12;color:'#111114'}}
  }
  Text{text:job.running ? qsTr('Running…'):root.output ? qsTr('Exit code %1').arg(root.exitCode):qsTr('Runs in your home folder. Interactive commands open in Terminal.');color:'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
 }
}
