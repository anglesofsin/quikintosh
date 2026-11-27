import QtQuick
import qs.services
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Quickshell
Item {
 id:root
 objectName:'shelf-developer-tools'
 property string result:''
 property string error:''
 readonly property var tools:[qsTr('Format JSON'),qsTr('Minify JSON'),qsTr('Encode Base64'),qsTr('Decode Base64'),qsTr('Encode URL'),qsTr('Decode URL'),qsTr('Inspect JWT'),qsTr('Generate UUID'),qsTr('SHA-256'),qsTr('SHA-512')]
 readonly property var operations:['json','minify','base64','unbase64','url','unurl','jwt','uuid','sha256','sha512']
 function run(){error='';ShelfState.send({action:'developerTool',operation:operations[choice.currentIndex],text:input.text})}
 Connections{target:ShelfState;function onDeveloperResult(text,error){root.result=text;root.error=error}}
 ColumnLayout{anchors.fill:parent;spacing:8
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Developer Tools');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold}
   ShelfChoice{id:choice;Layout.preferredWidth:190;model:root.tools}
   ShelfButton{text:qsTr('Run');selected:true;onClicked:root.run()}
  }
  ScrollView{Layout.fillWidth:true;Layout.fillHeight:true
   TextArea{id:input;objectName:'developer-input';placeholderText:qsTr('Paste text here. Processing stays on this computer.');wrapMode:TextEdit.Wrap;color:'white';font.family:'SF Mono';font.pixelSize:12;selectByMouse:true;background:Rectangle{color:'#151518';radius:12} Keys.onPressed:event=>{if(event.key===Qt.Key_Return && event.modifiers&Qt.ControlModifier){root.run();event.accepted=true}}}
  }
  ScrollView{Layout.fillWidth:true;Layout.fillHeight:true
   TextArea{objectName:'developer-result';text:root.result;readOnly:true;selectByMouse:true;wrapMode:TextEdit.Wrap;color:'#e5e5eb';font.family:'SF Mono';font.pixelSize:12;background:Rectangle{color:'#111114';radius:12}}
  }
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:root.error || (choice.currentIndex===6 ? qsTr('Decoded only. The signature is not verified.'):qsTr('Local processing'));color:root.error ? '#ff827b':'#9999a3';font.family:ShelfStyle.textFamily;font.pixelSize:11;elide:Text.ElideRight}
   ShelfButton{flat:true;text:qsTr('Copy');enabled:root.result.length>0;onClicked:ShelfState.send({action:'copyText',text:root.result})}
  }
 }
}
