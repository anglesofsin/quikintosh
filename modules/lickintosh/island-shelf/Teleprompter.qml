import QtQuick
import QtQuick.Dialogs
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import qs.services
import QtQuick.Controls.Basic
import QtQuick.Layouts
Item {
 id:root
 objectName:'shelf-teleprompter'
 IdleInhibitor{window:root.QsWindow.window;enabled:root.visible && root.reading && root.playing}
 property bool reading:false
 property bool playing:false
 property bool mirrored:ShelfState.utilityPreferences.teleprompterMirrored===true
 property real wordsPerMinute:ShelfState.utilityPreferences.teleprompterWpm || 140
 readonly property real pixelsPerSecond:Math.max(1,(script.paintedHeight/Math.max(1,editor.text.trim().split(/\s+/).length))*wordsPerMinute/60)
 property string importError:""
 property real fontSize:ShelfState.utilityPreferences.teleprompterFontSize || 24
 property bool held:false
 onPlayingChanged:{if(held!==playing){held=playing;ShelfState.interaction(held)}}
 onVisibleChanged:if(!visible)playing=false
 FrameAnimation{running:root.visible && root.reading && root.playing;onTriggered:{scroller.contentY=Math.min(Math.max(0,scroller.contentHeight-scroller.height),scroller.contentY+root.pixelsPerSecond*Math.min(frameTime,.1));if(scroller.contentY>=scroller.contentHeight-scroller.height)root.playing=false}}
 FileDialog{id:importDialog;title:qsTr('Import script');nameFilters:[qsTr('Documents (*.txt *.md *.pdf *.docx)')];onAccepted:{importJob.command=[ShelfState.pythonExecutable,Quickshell.shellPath('island-shelf/script_import.py'),decodeURIComponent(String(selectedFile).replace('file://',''))];importJob.running=true}}
 Process{id:importJob;stdout:StdioCollector{onStreamFinished:{try{const data=JSON.parse(text);root.importError=data.error || '';if(data.text)editor.text=data.text}catch(_){root.importError=qsTr('Could not read document')}}}}
 ColumnLayout{anchors.fill:parent;spacing:9
  RowLayout{Layout.fillWidth:true
   Text{Layout.fillWidth:true;text:qsTr('Teleprompter');color:'white';font.family:ShelfStyle.displayFamily;font.pixelSize:18;font.weight:Font.DemiBold}
   ShelfButton{flat:true;text:qsTr('Import');visible:!root.reading;enabled:!importJob.running;onClicked:importDialog.open()}
   ShelfButton{flat:true;icon:'notch/edit-3.svg';accessibleLabel:qsTr('Edit script');visible:root.reading;onClicked:{root.playing=false;root.reading=false}}
   ShelfButton{text:root.reading ? root.playing ? qsTr('Pause'):qsTr('Play'):qsTr('Read');selected:true;enabled:editor.text.trim().length>0;onClicked:{if(!root.reading){root.reading=true;scroller.contentY=0}root.playing=!root.playing}}
  }
  Text{visible:!!root.importError;Layout.fillWidth:true;text:root.importError;color:'#ff827b';wrapMode:Text.Wrap;font.family:ShelfStyle.textFamily;font.pixelSize:12}
  ScrollView{clip:true;visible:!root.reading;Layout.fillWidth:true;Layout.fillHeight:true
   ShelfTextArea{id:editor;objectName:'teleprompter-script';text:ShelfState.utilityPreferences.teleprompterText || '';placeholderText:qsTr('Paste your script…');wrapMode:TextEdit.Wrap;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:16;selectByMouse:true; onTextChanged:save.restart()}
  }
  Flickable{id:scroller;visible:root.reading;Layout.fillWidth:true;Layout.fillHeight:true;clip:true;contentWidth:width;contentHeight:script.height+height;boundsBehavior:Flickable.StopAtBounds
   Text{id:script;width:scroller.width;text:editor.text;textFormat:Text.PlainText;wrapMode:Text.Wrap;horizontalAlignment:Text.AlignHCenter;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:root.fontSize;lineHeight:1.45;topPadding:16;transform:Scale{origin.x:script.width/2;xScale:root.mirrored ? -1:1}}
  }
  RowLayout{Layout.fillWidth:true
   Text{text:qsTr('%1 WPM').arg(Math.round(root.wordsPerMinute));color:'#aaaab3';font.family:ShelfStyle.textFamily;font.pixelSize:11}
   ShelfSlider{Layout.fillWidth:true;from:60;to:300;stepSize:5;value:root.wordsPerMinute;onMoved:{root.wordsPerMinute=value;save.restart()}}
   ShelfButton{flat:true;text:'A−';accessibleLabel:qsTr('Smaller text');onClicked:{root.fontSize=Math.max(14,root.fontSize-2);save.restart()}}
   ShelfButton{flat:true;text:'A+';accessibleLabel:qsTr('Larger text');onClicked:{root.fontSize=Math.min(48,root.fontSize+2);save.restart()}}
   ShelfButton{flat:true;text:qsTr('Mirror');selected:root.mirrored;onClicked:{root.mirrored=!root.mirrored;save.restart()}}
  }
 }
 Timer{id:save;interval:600;onTriggered:ShelfState.send({action:'utilityPreferences',values:{teleprompterText:editor.text,teleprompterWpm:root.wordsPerMinute,teleprompterFontSize:root.fontSize,teleprompterMirrored:root.mirrored}})}
 Component.onDestruction:{if(held)ShelfState.interaction(false);if(save.running)ShelfState.send({action:'utilityPreferences',values:{teleprompterText:editor.text,teleprompterWpm:root.wordsPerMinute,teleprompterFontSize:root.fontSize,teleprompterMirrored:root.mirrored}})}
}
