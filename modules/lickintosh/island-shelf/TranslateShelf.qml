import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
Item {
 id:root;objectName:'shelf-translate'
 property string result:''
 property string error:''
 property string request:''
 property string initialText:ShelfState.translationText
 readonly property var codes:['pt','en','es','fr','de','it','ja','ko','zh','ru']
 function run(){if(job.running || !input.text.trim())return;result='';error='';request=JSON.stringify({text:input.text,source:'auto',target:codes[target.currentIndex]});job.running=true}
 Process{id:job;command:[ShelfState.pythonExecutable,Quickshell.shellPath('island-shelf/translate_backend.py')];stdinEnabled:true
  onStarted:{write(root.request+'\n')}
  stdout:StdioCollector{onStreamFinished:{try{const response=JSON.parse(text);root.result=response.text || '';root.error=response.error || ''}catch(_){root.error=qsTr('Translation unavailable')}}}
 }
 onVisibleChanged:if(!visible)job.running=false
 ColumnLayout{anchors.fill:parent;spacing:12
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:root.result ? qsTr('Automatic → %1').arg(target.currentText):qsTr('Quick Translate');font.family:ShelfStyle.displayFamily;font.pixelSize:20;font.weight:Font.DemiBold;color:ShelfStyle.primary}
   ShelfChoice{id:target;enabled:!job.running;Layout.preferredWidth:130;model:['Português','English','Español','Français','Deutsch','Italiano','日本語','한국어','中文','Русский'];onActivated:{root.result='';root.error=''}}
  }
  ScrollView{Layout.fillWidth:true;Layout.fillHeight:true;clip:true;visible:!root.result
   ShelfTextArea{id:input;objectName:'translate-input';readOnly:job.running;text:root.initialText;onTextChanged:{root.result='';root.error=''}placeholderText:qsTr('Enter text to translate…');font.pixelSize:16}
  }
  ScrollView{Layout.fillWidth:true;Layout.fillHeight:true;clip:true;visible:!!root.result
   ShelfTextArea{objectName:'translate-result';text:root.result;readOnly:true;background:null;padding:0;font.family:ShelfStyle.displayFamily;font.pixelSize:22}
  }
  Text{Layout.fillWidth:true;text:root.error || qsTr('Google Translate · Online. Text is sent only when you press Translate.');wrapMode:Text.Wrap;font.family:ShelfStyle.textFamily;font.pixelSize:12;color:root.error ? '#ff827b':ShelfStyle.secondary}
  RowLayout{Layout.fillWidth:true
   ShelfButton{text:root.result ? qsTr('Edit'):qsTr('Clear');flat:true;onClicked:{if(!root.result)input.clear();root.result='';root.error=''}}
   Item{Layout.fillWidth:true}
   ShelfButton{text:qsTr('Copy');enabled:!!root.result;onClicked:ShelfState.send({action:'copyText',text:root.result})}
   ShelfButton{visible:!root.result;text:job.running ? qsTr('Cancel'):qsTr('Translate');selected:true;enabled:job.running || !!input.text.trim();onClicked:job.running ? job.running=false:root.run()}
  }
 }
}
